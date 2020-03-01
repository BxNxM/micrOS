import sys
try:
    from ConfigHandler import console_write
except Exception as e:
    print("Failed to import ConfigHandler: {}".format(e))
    console_write = None

def DynamicExec(*args, **kwargs):
    # Dynamic Parameter Handling
    module = varResolver(key='module', fallback_index=0, args_tuple=args, kwargs_dict=kwargs)
    kwargs.pop('module')
    function = varResolver(key='function', fallback_index=1, args_tuple=args, kwargs_dict=kwargs)
    kwargs.pop('function')
    # Dynamic runtime execution
    try:
        exec('from {} import {}'.format(module, function), {})     # Instead of globals, use empty dict, so we don't get a reference to the module
    except Exception as e:
        console_write("[DynamicExec] from {} import {} error: {}".format(module, function, e))
        raise Exception("[DynamicExec] from {} import {} error: {}".format(module, function, e))
    try:
        if len(args) == 0 and len(kwargs) == 0:
            result = getattr(sys.modules[module], function)(**dict(__varResolveFunc=varResolver))
        else:
            result = getattr(sys.modules[module], function)(*args, **dict(kwargs, __varResolveFunc=varResolver))
    except Exception as e:
            console_write("[DynamicExec] getattr(sys.modules[{}], {})({}, {}) error: {}".format(module, function, args, kwargs, e))
            raise Exception("[DynamicExec] getattr(sys.modules[{}], {})({}, {}) error: {}".format(module, function, args, kwargs, e))
    finally:
        del sys.modules[module]                                     # Remove reference
    return result

def varResolver(key=None, fallback_index=None, args_tuple=(), kwargs_dict={}, fallback_value=None):
    try:
        if key is not None:
            return kwargs_dict.get(key) if kwargs_dict.get(key) else args_tuple[fallback_index]
        if fallback_index is not None:
            return args_tuple[fallback_index]
    except IndexError:
        console_write("Variable [key:{}|index:{}] is required! Fallback: {}".format(key, fallback_index, fallback_value))
        return fallback_value

def parseRawFuncArgs(raw_args='(1, 2, a=3, b=4)'):
    args = []
    kwargs = {}
    arglist = [ k.strip().replace('(', '').replace(')', '') for k in raw_args.split(',') ]
    for arg in arglist:
        if '=' in arg:
            kwargs[arg.split('=')[0]] = arg.split('=')[1]
        elif arg != '':
            args.append(arg)
    console_write("[parseRawFuncArgs] args: {}, kwargs: {}".format(args, kwargs))
    return tuple(args), dict(kwargs)

if __name__ == "__main__":
    a = varResolver(fallback_index=0, args_tuple=(55, 22, 11), kwargs_dict={})
    console_write(a)

    # Simple function call - without arguments
    DynamicExec(module='modtest', function='some_func')
    #  OR
    args, kwargs = parseRawFuncArgs('()')
    DynamicExec(*args, **kwargs, module='modtest', function='some_func')
    # Function call with arguments
    args, kwargs = parseRawFuncArgs('(20, a=5, b=3)')
    DynamicExec(*args, **kwargs, module='modtest', function='some_func_args')
