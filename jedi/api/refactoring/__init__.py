import difflib
import re
from pathlib import Path
from typing import Dict, Iterable, Tuple

from parso import split_lines

from jedi.api.exceptions import RefactoringError
from jedi.inference.value.namespace import ImplicitNSName

EXPRESSION_PARTS = (
    'or_test and_test not_test comparison '
    'expr xor_expr and_expr shift_expr arith_expr term factor power atom_expr'
).split()

# Precedence levels for Python expression node types (higher = binds tighter).
# Atoms (number, string, name, keyword, fstring, atom) have the highest
# precedence and are represented by a sentinel value above all entries here.
_PRECEDENCE = {
    'or_test': 1,
    'and_test': 2,
    'not_test': 3,
    'comparison': 4,
    'expr': 5,        # bitwise |
    'xor_expr': 6,    # bitwise ^
    'and_expr': 7,    # bitwise &
    'shift_expr': 8,  # << >>
    'arith_expr': 9,  # + -
    'term': 10,       # * / // % @
    'factor': 11,     # unary +, -, ~
    'power': 12,      # **
    'atom_expr': 13,  # attribute access, subscript, call
}
_ATOM_PRECEDENCE = 14  # number, string, name, keyword, fstring, atom


class ChangedFile:
    def __init__(self, inference_state, from_path, to_path,
                 module_node, node_to_str_map):
        self._inference_state = inference_state
        self._from_path = from_path
        self._to_path = to_path
        self._module_node = module_node
        self._node_to_str_map = node_to_str_map

    def get_diff(self):
        old_lines = split_lines(self._module_node.get_code(), keepends=True)
        new_lines = split_lines(self.get_new_code(), keepends=True)

        # Add a newline at the end if it's missing. Otherwise the diff will be
        # very weird. A `diff -u file1 file2` would show the string:
        #
        #     \ No newline at end of file
        #
        # This is not necessary IMO, because Jedi does not really play with
        # newlines and the ending newline does not really matter in Python
        # files. ~dave
        if old_lines[-1] != '':
            old_lines[-1] += '\n'
        if new_lines[-1] != '':
            new_lines[-1] += '\n'

        project_path = self._inference_state.project.path
        if self._from_path is None:
            from_p = ''
        else:
            try:
                from_p = self._from_path.relative_to(project_path)
            except ValueError:  # Happens it the path is not on th project_path
                from_p = self._from_path
        if self._to_path is None:
            to_p = ''
        else:
            try:
                to_p = self._to_path.relative_to(project_path)
            except ValueError:
                to_p = self._to_path
        diff = difflib.unified_diff(
            old_lines, new_lines,
            fromfile=str(from_p),
            tofile=str(to_p),
        )
        # Apparently there's a space at the end of the diff - for whatever
        # reason.
        return ''.join(diff).rstrip(' ')

    def get_new_code(self):
        return self._inference_state.grammar.refactor(self._module_node, self._node_to_str_map)

    def apply(self):
        if self._from_path is None:
            raise RefactoringError(
                'Cannot apply a refactoring on a Script with path=None'
            )

        with open(self._from_path, 'w', newline='') as f:
            f.write(self.get_new_code())

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self._from_path)


class Refactoring:
    def __init__(self, inference_state, file_to_node_changes, renames=()):
        self._inference_state = inference_state
        self._renames = renames
        self._file_to_node_changes = file_to_node_changes

    def get_changed_files(self) -> Dict[Path, ChangedFile]:
        def calculate_to_path(p):
            if p is None:
                return p
            p = str(p)
            for from_, to in renames:
                if p.startswith(str(from_)):
                    p = str(to) + p[len(str(from_)):]
            return Path(p)

        renames = self.get_renames()
        return {
            path: ChangedFile(
                self._inference_state,
                from_path=path,
                to_path=calculate_to_path(path),
                module_node=next(iter(map_)).get_root_node(),
                node_to_str_map=map_
            )
            # We need to use `or`, because the path can be None
            for path, map_ in sorted(
                self._file_to_node_changes.items(),
                key=lambda x: x[0] or Path("")
            )
        }

    def get_renames(self) -> Iterable[Tuple[Path, Path]]:
        """
        Files can be renamed in a refactoring.
        """
        return sorted(self._renames)

    def get_diff(self):
        text = ''
        project_path = self._inference_state.project.path
        for from_, to in self.get_renames():
            text += 'rename from %s\nrename to %s\n' \
                % (_try_relative_to(from_, project_path), _try_relative_to(to, project_path))

        return text + ''.join(f.get_diff() for f in self.get_changed_files().values())

    def apply(self):
        """
        Applies the whole refactoring to the files, which includes renames.
        """
        for f in self.get_changed_files().values():
            f.apply()

        for old, new in self.get_renames():
            old.rename(new)


def _calculate_rename(path, new_name):
    dir_ = path.parent
    if path.name in ('__init__.py', '__init__.pyi'):
        return dir_, dir_.parent.joinpath(new_name)
    return path, dir_.joinpath(new_name + path.suffix)


def _iter_string_annotations(module_node):
    """Yield String leaf nodes that appear in annotation positions."""
    for node in _walk_tree(module_node):
        if node.type == 'funcdef':
            ann = node.annotation
            if ann is not None and ann.type == 'string':
                yield ann
            for param in node.get_params():
                if param.annotation is not None and param.annotation.type == 'string':
                    yield param.annotation
        elif node.type == 'expr_stmt' and len(node.children) >= 2:
            annassign = node.children[1]
            if getattr(annassign, 'type', None) == 'annassign':
                ann = annassign.children[1]
                if ann.type == 'string':
                    yield ann


def _iter_dunder_all_strings(module_node):
    """Yield String leaf nodes that appear as elements in a module-level
    ``__all__ = [...]`` (or ``__all__ = (...)``) assignment."""
    for stmt in module_node.children:
        if stmt.type == 'simple_stmt':
            for child in stmt.children:
                if child.type == 'expr_stmt':
                    yield from _iter_dunder_all_string_elements(child)
        elif stmt.type == 'expr_stmt':
            yield from _iter_dunder_all_string_elements(stmt)


def _iter_dunder_all_string_elements(expr_stmt):
    """Yield String nodes inside a ``__all__ = [...]`` expr_stmt."""
    children = expr_stmt.children
    if (len(children) < 3
            or getattr(children[0], 'value', None) != '__all__'
            or getattr(children[1], 'value', None) != '='):
        return
    rhs = children[2]
    if not hasattr(rhs, 'children'):
        return
    for item in rhs.children:
        if getattr(item, 'type', None) == 'string':
            yield item
        elif getattr(item, 'type', None) == 'testlist_comp':
            for element in item.children:
                if getattr(element, 'type', None) == 'string':
                    yield element


def _get_enclosing_classdef(node):
    """Walk up the tree to find the nearest enclosing classdef, or None."""
    current = getattr(node, 'parent', None)
    while current is not None:
        if getattr(current, 'type', None) == 'classdef':
            return current
        current = getattr(current, 'parent', None)
    return None


def _iter_classdef_slots_strings(classdef_node):
    """Yield String leaf nodes in ``__slots__ = [...]`` within a classdef body."""
    suite = None
    for child in classdef_node.children:
        if getattr(child, 'type', None) == 'suite':
            suite = child
            break
    if suite is None:
        return
    for stmt in suite.children:
        if getattr(stmt, 'type', None) == 'simple_stmt':
            for child in stmt.children:
                if getattr(child, 'type', None) == 'expr_stmt':
                    yield from _iter_dunder_slots_string_elements(child)
        elif getattr(stmt, 'type', None) == 'expr_stmt':
            yield from _iter_dunder_slots_string_elements(stmt)


def _iter_dunder_slots_string_elements(expr_stmt):
    """Yield String nodes inside a ``__slots__ = [...]`` expr_stmt."""
    children = expr_stmt.children
    if (len(children) < 3
            or getattr(children[0], 'value', None) != '__slots__'
            or getattr(children[1], 'value', None) != '='):
        return
    rhs = children[2]
    if not hasattr(rhs, 'children'):
        return
    for item in rhs.children:
        if getattr(item, 'type', None) == 'string':
            yield item
        elif getattr(item, 'type', None) == 'testlist_comp':
            for element in item.children:
                if getattr(element, 'type', None) == 'string':
                    yield element


def _walk_tree(node):
    yield node
    if hasattr(node, 'children'):
        for child in node.children:
            yield from _walk_tree(child)


def rename(inference_state, definitions, new_name):
    file_renames = set()
    file_tree_name_map = {}

    if not definitions:
        raise RefactoringError("There is no name under the cursor")

    project_path = inference_state.project.path
    internal_def_paths = set()
    external_def_paths = set()
    for d in definitions:
        if d.is_definition() and d.module_path is not None \
                and not isinstance(d._name, ImplicitNSName) \
                and d.type != 'module':
            try:
                Path(d.module_path).relative_to(project_path)
                internal_def_paths.add(d.module_path)
            except ValueError:
                external_def_paths.add(d.module_path)
    if internal_def_paths and external_def_paths:
        raise RefactoringError(
            "Cannot rename: symbol is defined in an external package"
        )

    old_name = None
    for d in definitions:
        # This private access is ok in a way. It's not public to
        # protect Jedi users from seeing it.
        tree_name = d._name.tree_name
        if old_name is None and tree_name is not None:
            old_name = tree_name.value
        if d.type == 'module' and tree_name is None and d.module_path is not None:
            p = Path(d.module_path)
            file_renames.add(_calculate_rename(p, new_name))
        elif isinstance(d._name, ImplicitNSName):
            for p in d._name._value.py__path__():
                file_renames.add(_calculate_rename(Path(p), new_name))
        else:
            if tree_name is not None:
                fmap = file_tree_name_map.setdefault(d.module_path, {})
                fmap[tree_name] = tree_name.prefix + new_name

    if old_name is not None:
        pattern = re.compile(r'\b' + re.escape(old_name) + r'\b')
        for fmap in file_tree_name_map.values():
            module_node = next(iter(fmap)).get_root_node()
            for string_node in _iter_string_annotations(module_node):
                new_val = pattern.sub(new_name, string_node.value)
                if new_val != string_node.value:
                    fmap[string_node] = string_node.prefix + new_val
            for string_node in _iter_dunder_all_strings(module_node):
                new_val = pattern.sub(new_name, string_node.value)
                if new_val != string_node.value:
                    fmap[string_node] = string_node.prefix + new_val
            seen_classdefs = set()
            for tree_name_node in list(fmap.keys()):
                classdef = _get_enclosing_classdef(tree_name_node)
                if classdef is not None and id(classdef) not in seen_classdefs:
                    seen_classdefs.add(id(classdef))
                    for string_node in _iter_classdef_slots_strings(classdef):
                        new_val = pattern.sub(new_name, string_node.value)
                        if new_val != string_node.value:
                            fmap[string_node] = string_node.prefix + new_val

    return Refactoring(inference_state, file_tree_name_map, file_renames)


def inline(inference_state, names):
    if not names:
        raise RefactoringError("There is no name under the cursor")
    if any(n.api_type in ('module', 'namespace') for n in names):
        raise RefactoringError("Cannot inline imports, modules or namespaces")
    if any(n.tree_name is None for n in names):
        raise RefactoringError("Cannot inline builtins/extensions")

    definitions = [n for n in names if n.tree_name.is_definition()]
    if len(definitions) == 0:
        raise RefactoringError("No definition found to inline")
    if len(definitions) > 1:
        raise RefactoringError("Cannot inline a name with multiple definitions")
    if len(names) == 1:
        raise RefactoringError("There are no references to this name")

    tree_name = definitions[0].tree_name

    expr_stmt = tree_name.get_definition()
    if expr_stmt.type != 'expr_stmt':
        type_ = {'funcdef': 'function', 'classdef': 'class'}.get(expr_stmt.type, expr_stmt.type)
        raise RefactoringError("Cannot inline a %s" % type_)

    if len(expr_stmt.get_defined_names(include_setitem=True)) > 1:
        raise RefactoringError("Cannot inline a statement with multiple definitions")
    first_child = expr_stmt.children[1]
    if first_child.type == 'annassign':
        if len(first_child.children) != 4:
            raise RefactoringError('Cannot inline a statement that is defined by an annotation')
        first_child = first_child.children[2]
    if first_child != '=':
        raise RefactoringError(
            'Cannot inline a statement with "%s"' % first_child.get_code(include_prefix=False)
        )

    rhs = expr_stmt.get_rhs()
    replace_code = rhs.get_code(include_prefix=False)

    references = [n for n in names if not n.tree_name.is_definition()]
    file_to_node_changes = {}
    for name in references:
        tree_name = name.tree_name
        path = name.get_root_context().py__file__()
        s = replace_code
        context_type = tree_name.parent.type
        if (rhs.type == 'testlist_star_expr'
                or context_type in EXPRESSION_PARTS
                or context_type == 'trailer'
                and tree_name.parent.get_next_sibling() is not None):
            if not _is_safe_without_parens(rhs, context_type):
                s = '(' + replace_code + ')'

        of_path = file_to_node_changes.setdefault(path, {})

        node = tree_name
        prefix = tree_name.prefix
        par = tree_name.parent
        if par.type == 'trailer' and par.children[0] == '.':
            prefix = par.parent.children[0].prefix
            node = par
            for sibling in par.parent.children[:par.parent.children.index(par)]:
                of_path[sibling] = ''
        of_path[node] = prefix + s

    path = definitions[0].get_root_context().py__file__()
    changes = file_to_node_changes.setdefault(path, {})
    changes[expr_stmt] = _remove_indent_of_prefix(expr_stmt.get_first_leaf().prefix)
    next_leaf = expr_stmt.get_next_leaf()

    # Remove the newline (and any inline comment) at the end of the statement.
    # Inline comments on the definition line belong to that line and are
    # removed along with the definition.
    if next_leaf.type == 'newline' or next_leaf == ';':
        changes[next_leaf] = ''
    return Refactoring(inference_state, file_to_node_changes)


def _is_safe_without_parens(rhs, context_type):
    """
    Returns True if *rhs* binds strictly tighter than *context_type*, so no
    wrapping parentheses are needed.  Equal precedence is NOT safe because
    Python's binary operators are not all associative (e.g. ``a-(b-c)`` ≠
    ``a-b-c``).  Tuples (testlist_star_expr) always need parens — handled at
    call site.
    """
    if rhs.type in ('number', 'string', 'keyword', 'fstring', 'name'):
        rhs_prec = _ATOM_PRECEDENCE
    elif rhs.type == 'atom':
        # parenthesised/list/dict/set — delimiters make them self-contained
        if rhs.children[0].value in ('(', '[', '{'):
            rhs_prec = _ATOM_PRECEDENCE
        else:
            return False  # e.g. ellipsis literal — treat conservatively
    else:
        rhs_prec = _PRECEDENCE.get(rhs.type)
        if rhs_prec is None:
            return False  # unknown node type — add parens to be safe

    context_prec = _PRECEDENCE.get(context_type, _ATOM_PRECEDENCE)
    return rhs_prec > context_prec


def _remove_indent_of_prefix(prefix):
    r"""
    Removes the last indentation of a prefix, e.g. " \n \n " becomes " \n \n".
    """
    return ''.join(split_lines(prefix, keepends=True)[:-1])


def _try_relative_to(path: Path, base: Path) -> Path:
    try:
        return path.relative_to(base)
    except ValueError:
        return path
