import ast
import types
import inspect


def code_to_node(code):
    result = None
    try:
        src = inspect.getsource(code)
        file = inspect.getfile(code)
        result = ast.parse(src, file, 'exec')
    except IOError:
        pass
    return result


def func_to_node(func):
    result = None
    if func and hasattr(func, '__code__'):
        result = code_to_node(func.__code__)
    return result


def node_to_code(node, old_code):
    result = old_code
    if node and isinstance(node, ast.Module):
        file = inspect.getfile(old_code) if old_code else None
        module = compile(node, file or '<file>', 'exec')
        node = node.body[0]
        for code in module.co_consts:
            if not isinstance(code, types.CodeType):
                continue
            if code.co_name == node.name and code.co_firstlineno == node.lineno:
                result = code
                break
    return result


def node_to_func(node, old_func):
    result = old_func
    if node and old_func:
        old_code = getattr(old_func, '__code__', None)
        result.__code__ = node_to_code(node, old_code)
    return result


class ReturnIncrement(ast.NodeTransformer):
    def visit_Return(self, node):
        node.value = (ast.BinOp(
            left=node.value,
            op=ast.Add(),
            right=ast.Num(n=1)
        ))
        return node


def transform_with(transformer):
    def transform_decorator(func):
        node = func_to_node(func)
        node = transformer().visit(node)
        node = ast.fix_missing_locations(node)
        func = node_to_func(node, func)
        return func

    return transform_decorator


@transform_with(ReturnIncrement)
def f(a, b, c):
    return a + b + c


if __name__ == "__main__":
    print(f(1, 2, 3))  # 7
