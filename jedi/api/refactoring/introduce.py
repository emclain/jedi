from jedi.api.exceptions import RefactoringError
from jedi.api.refactoring import Refactoring, _remove_indent_of_prefix


def introduce_parameter(inference_state, path, module_node, name, pos):
    """
    Introduces a parameter for a variable assignment inside a function.

    The variable's assignment is removed and the variable is added as a new
    parameter to the enclosing function, with the original RHS as the default
    value.
    """
    leaf = module_node.get_leaf_for_position(pos, include_prefixes=True)

    # Navigate to the actual name node
    if leaf.type != 'name':
        raise RefactoringError("No name found at the given position")

    if not leaf.is_definition():
        raise RefactoringError("The name is not a variable definition")

    expr_stmt = leaf.get_definition()
    if expr_stmt.type != 'expr_stmt':
        type_ = dict(
            funcdef='function',
            classdef='class',
        ).get(expr_stmt.type, expr_stmt.type)
        raise RefactoringError("Cannot introduce a %s as a parameter" % type_)

    if len(expr_stmt.get_defined_names(include_setitem=True)) > 1:
        raise RefactoringError(
            "Cannot introduce a parameter from a statement with multiple definitions"
        )

    # Check there's a simple `=` assignment (not augmented assignment or annotation-only)
    first_child = expr_stmt.children[1]
    if first_child.type == 'annassign' and len(first_child.children) == 4:
        first_child = first_child.children[2]
    if first_child != '=':
        if first_child.type == 'annassign':
            raise RefactoringError(
                "Cannot introduce a parameter from an annotation without a value"
            )
        else:
            raise RefactoringError(
                'Cannot introduce a parameter from a statement with "%s"'
                % first_child.get_code(include_prefix=False)
            )

    rhs = expr_stmt.get_rhs()
    if _is_call_expr(rhs):
        raise RefactoringError(
            "Cannot use a call expression as a default value: "
            "it would be evaluated once at definition time, not on each call"
        )

    # Reject mutable literal defaults (lists and dicts/sets) because they would
    # share the same object across all calls, unlike a fresh local variable.
    if rhs.type == 'atom' and rhs.children[0].value in ('[', '{'):
        raise RefactoringError(
            "Cannot use a mutable literal as a parameter default"
        )

    default_value = rhs.get_code(include_prefix=False)

    # Find the enclosing function
    funcdef = _find_enclosing_funcdef(expr_stmt)
    if funcdef is None:
        raise RefactoringError(
            "Cannot introduce a parameter: the variable is not inside a function"
        )

    # Build the new parameter text: `name=default_value`
    var_name = leaf.value
    if name != var_name:
        # The user can optionally rename the parameter
        param_name = name
    else:
        param_name = var_name

    new_param = param_name + '=' + default_value

    # Modify the function's parameter list
    node_changes = {}
    parameters = funcdef.get_params()
    if parameters:
        # Appending after **kwargs would produce a SyntaxError
        last_param = parameters[-1]
        if last_param.children and last_param.children[0].value == '**':
            raise RefactoringError(
                "Cannot introduce a parameter after **kwargs"
            )
        last_param_code = last_param.get_code(include_prefix=True)
        node_changes[last_param] = last_param_code + ', ' + new_param
    else:
        # No parameters exist - need to add inside the parens
        # funcdef.children: ['def', name, parameters, ':', suite]
        # parameters.children: ['(', ')']
        params_node = funcdef.children[2]  # The 'parameters' node
        close_paren = params_node.children[-1]  # The ')' operator
        node_changes[close_paren] = new_param + ')'

    # Remove the assignment statement
    node_changes[expr_stmt] = _remove_indent_of_prefix(
        expr_stmt.get_first_leaf().prefix
    )
    next_leaf = expr_stmt.get_next_leaf()
    if next_leaf.prefix.strip(' \t') == '' \
            and (next_leaf.type == 'newline' or next_leaf == ';'):
        node_changes[next_leaf] = ''

    # If the parameter was renamed, also update all references in the function body
    if name != var_name:
        _rename_in_scope(funcdef, var_name, name, node_changes)

    file_to_node_changes = {path: node_changes}
    return Refactoring(inference_state, file_to_node_changes)


def introduce_field(inference_state, path, module_node, pos):
    """
    Introduces a field for a variable assignment inside a method.

    The local variable assignment `x = expr` becomes `self.x = expr`, and all
    references to `x` within the method are replaced with `self.x`.
    """
    leaf = module_node.get_leaf_for_position(pos, include_prefixes=True)

    if leaf.type != 'name':
        raise RefactoringError("No name found at the given position")

    if not leaf.is_definition():
        raise RefactoringError("The name is not a variable definition")

    expr_stmt = leaf.get_definition()
    if expr_stmt.type != 'expr_stmt':
        type_ = dict(
            funcdef='function',
            classdef='class',
        ).get(expr_stmt.type, expr_stmt.type)
        raise RefactoringError("Cannot introduce a %s as a field" % type_)

    # Check there's a simple `=` assignment
    first_child = expr_stmt.children[1]
    if first_child.type == 'annassign' and len(first_child.children) == 4:
        first_child = first_child.children[2]
    if first_child != '=':
        if first_child.type == 'annassign':
            raise RefactoringError(
                "Cannot introduce a field from an annotation without a value"
            )
        else:
            raise RefactoringError(
                'Cannot introduce a field from a statement with "%s"'
                % first_child.get_code(include_prefix=False)
            )

    # Find the enclosing function (method)
    funcdef = _find_enclosing_funcdef(expr_stmt)
    if funcdef is None:
        raise RefactoringError(
            "Cannot introduce a field: the variable is not inside a function"
        )

    # Check that the function is a method (inside a class)
    classdef = _find_enclosing_classdef(funcdef)
    if classdef is None:
        raise RefactoringError(
            "Cannot introduce a field: the function is not inside a class"
        )

    # Get the self parameter name
    params = funcdef.get_params()
    if not params or params[0].star_count != 0:
        raise RefactoringError(
            "Cannot introduce a field: the method has no self parameter"
        )
    self_name = params[0].name.value

    var_name = leaf.value
    field_ref = self_name + '.' + var_name

    # Check that self.var_name doesn't already exist in the method body
    suite = _get_funcdef_suite(funcdef)
    if suite is not None and _has_field_reference(suite, self_name, var_name):
        raise RefactoringError(
            "Cannot introduce a field: %s already exists in the method" % field_ref
        )

    # Check that the variable is not referenced inside a nested function.
    # Such references are closures over the local variable; after the refactor
    # the local no longer exists, but self.x cannot be substituted safely
    # without knowing whether self is shadowed in the nested scope.
    if suite is not None and _has_reference_in_nested_func(suite, var_name):
        raise RefactoringError(
            "Cannot introduce a field: '%s' is referenced inside a nested function"
            % var_name
        )

    # Build node changes:
    # 1. Replace the definition `x = expr` with `self.x = expr`
    # 2. Replace all references to `x` within the function with `self.x`
    node_changes = {}

    # Replace definition: change the name node to self.name
    node_changes[leaf] = leaf.prefix + field_ref

    # Find and replace all references in the function body
    suite = _get_funcdef_suite(funcdef)
    _replace_references_with_field(suite, var_name, field_ref, leaf, node_changes)

    file_to_node_changes = {path: node_changes}
    return Refactoring(inference_state, file_to_node_changes)


def _find_enclosing_funcdef(node):
    """Find the nearest enclosing funcdef or async_funcdef, not crossing classdef boundaries."""
    parent = node.parent
    while parent is not None:
        if parent.type in ('funcdef', 'async_funcdef'):
            return parent
        if parent.type == 'classdef':
            return None
        parent = parent.parent
    return None


def _find_enclosing_classdef(node):
    """Find the nearest enclosing classdef for a funcdef."""
    parent = node.parent
    while parent is not None:
        if parent.type == 'classdef':
            return parent
        parent = parent.parent
    return None


def _get_funcdef_suite(funcdef):
    """Get the suite (body) node of a funcdef."""
    # funcdef children: 'def' name parameters ':' suite
    # async_funcdef children: 'async' funcdef
    if funcdef.type == 'async_funcdef':
        funcdef = funcdef.children[1]
    for child in funcdef.children:
        if child.type == 'suite':
            return child
    return None


def _has_field_reference(node, self_name, var_name):
    """
    Return True if the node tree contains a reference to self_name.var_name
    (i.e., an attribute access like `self.x`).
    """
    try:
        children = node.children
    except AttributeError:
        # Leaf node: check if it is `var_name` preceded by `self_name.`
        if node.type == 'name' and node.value == var_name:
            parent = node.parent
            # The pattern for `self.x` is: expr -> trailer -> ['.', 'x']
            # parent of 'x' is a trailer node, parent of that has self_name before it
            if (parent is not None and parent.type == 'trailer'
                    and len(parent.children) == 2
                    and parent.children[0] == '.'):
                # The trailer's parent should have self_name as an adjacent child
                grandparent = parent.parent
                if grandparent is not None:
                    siblings = grandparent.children
                    trailer_idx = siblings.index(parent)
                    if trailer_idx > 0:
                        prev = siblings[trailer_idx - 1]
                        if prev.type == 'name' and prev.value == self_name:
                            return True
        return False

    if node.type in ('funcdef', 'async_funcdef', 'classdef'):
        return False

    return any(_has_field_reference(child, self_name, var_name) for child in children)


def _has_reference_in_nested_func(node, name):
    """
    Return True if *name* is referenced as a free variable inside any nested
    funcdef or async_funcdef within *node*.  Does not recurse past classdef
    boundaries (a nested class creates its own scope).
    """
    try:
        children = node.children
    except AttributeError:
        return False

    if node.type == 'classdef':
        return False

    for child in children:
        if child.type in ('funcdef', 'async_funcdef'):
            if _name_used_in_func(child, name):
                return True
        else:
            if _has_reference_in_nested_func(child, name):
                return True
    return False


def _name_used_in_func(funcdef_node, name):
    """Return True if *name* appears as a name leaf anywhere inside funcdef_node."""
    try:
        children = funcdef_node.children
    except AttributeError:
        return (funcdef_node.type == 'name'
                and funcdef_node.value == name
                and not (funcdef_node.parent.type == 'trailer'
                         and funcdef_node.parent.children[0] == '.'))

    for child in children:
        if _name_used_in_func(child, name):
            return True
    return False


def _walk_name_references(node, name, callback):
    """
    Walk the node tree, calling callback(leaf) for every name leaf whose
    value equals *name*, subject to the standard guards:
    - do not descend into nested funcdef/async_funcdef/classdef nodes
    - skip trailer nodes that begin with '.' (attribute access)
    - skip leaf nodes that are themselves the RHS of a dot (i.e., the leaf's
      parent is a trailer whose first child is '.')
    """
    try:
        children = node.children
    except AttributeError:
        # Leaf node
        if node.type == 'name' and node.value == name:
            if node.parent.type == 'trailer' and node.parent.children[0] == '.':
                return
            callback(node)
        return

    if node.type in ('funcdef', 'async_funcdef', 'classdef'):
        return

    for child in children:
        if child.type == 'trailer' and child.children[0] == '.':
            continue
        _walk_name_references(child, name, callback)


def _replace_references_with_field(node, var_name, field_ref, definition_leaf, node_changes):
    """
    Recursively find references to var_name in node and replace them
    with field_ref (e.g., self.var_name). Skip the definition itself
    and names that are part of attribute access (x.something is already handled).
    """
    def _apply(leaf):
        if leaf is definition_leaf:
            return
        # Don't replace parameter names
        if leaf.parent.type in ('param', 'typedargslist'):
            return
        node_changes[leaf] = leaf.prefix + field_ref

    _walk_name_references(node, var_name, _apply)


def _rename_in_scope(funcdef, old_name, new_name, node_changes):
    """Rename all references to old_name within funcdef's body to new_name."""
    suite = _get_funcdef_suite(funcdef)
    if suite is None:
        return
    _rename_references(suite, old_name, new_name, node_changes)


def _rename_references(node, old_name, new_name, node_changes):
    def _apply(leaf):
        if leaf not in node_changes:
            node_changes[leaf] = leaf.prefix + new_name

    _walk_name_references(node, old_name, _apply)


def _is_call_expr(node):
    """Return True if node is a call expression (e.g., foo(), obj.method())."""
    if node.type in ('atom_expr', 'power'):
        for child in node.children:
            if child.type == 'trailer' and child.children[0].value == '(':
                return True
    return False
