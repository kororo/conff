# TODO: for now, let user use these function, eventually, before version 1.0, we should mark this as deprecated


def parse(root, names: dict = None, fns: dict = None, errors: list = None):
    from conff import Parser
    parser = Parser(names=names, fns=fns)
    if isinstance(root, str):
        result = parser.parse_expr(root)
    else:
        result = parser.parse_dict(root)
    return result


def load(fs_path: str, fs_root: str = '', params: dict = None, errors: list = None):
    from conff import Parser
    parser = Parser(params=params)
    result = parser.parse_file(fs_path=fs_path, fs_root=fs_root)
    return result


def encrypt(names: dict):
    def fn_encrypt(data):
        from conff import Parser
        parser = Parser(names=names, params=names.get('R', {}).get('_', {}))
        result = parser.fn_encrypt(data)
        return result

    return fn_encrypt


def decrypt(names: dict):
    def fn_decrypt(data):
        from conff import Parser
        parser = Parser(names=names, params=names.get('R', {}).get('_', {}))
        result = parser.fn_decrypt(data)
        return result

    return fn_decrypt


def generate_key(names: dict):
    def fn_generate_key():
        from conff import Parser
        parser = Parser(names=names, params=names.get('R', {}).get('_', {}))
        result = parser.generate_crypto_key()
        return result

    return fn_generate_key
