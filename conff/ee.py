import collections
import copy
import os
import simpleeval
import yaml
from munch import Munch
from simpleeval import EvalWithCompoundTypes
from collections import OrderedDict as odict
from cryptography.fernet import Fernet


class Munch2(Munch):
    """
    Provide easy way to access item in object by dot-notation.
    Example:
        obj = {'item': 'value'}
        # old way
        value = obj.get('item')
        # with munch
        value = obj.item
    """
    pass


def update_recursive(d, u):
    """
    Update dictionary recursively. It traverse any object implements "collections.Mapping", anything else,
    it overwrites the original value.
    :param d: Original dictionary to be updated
    :param u: Value dictionary
    :return: Updated dictionary after merged
    """
    for k, v in u.items():
        if isinstance(d, dict):
            d2 = d.get(k, {})
        else:
            d2 = getattr(d, k, object())

        if isinstance(v, dict):
            r = update_recursive(d2, v)
            u2 = r
        else:
            u2 = u[k]

        if isinstance(d, dict):
            d[k] = u2
        else:
            setattr(d, k, u2)
    return d


def filter_value(value):
    if type(value) == str:
        if value == '[empty]':
            value = ''
    elif type(value) == Munch2:
        value = value.toDict()
    if type(value) == str:
        value = value.strip()
    return value


def fn_str(val):
    return str(val)


def fn_has(val, name):
    if isinstance(val, collections.Mapping):
        return val.get(name, False) is not False
    else:
        return name in val


def fn_list_next(vals, default=None):
    vals = [vals] if type(vals) != list else vals
    val = next(iter(vals), default)
    return val


def fn_list_join(vals, sep=' '):
    vals = [val for val in vals if val]
    return sep.join(vals)


def fn_str_trim(val: str, cs: list = None):
    cs = cs if cs else ['/', ' ']
    for c in cs:
        val = val.strip(c)
    return val


def fn_extend(val, val2):
    val = copy.deepcopy(val)
    type_val = type(val)
    type_val2 = type(val2)
    if type_val == list and type_val2 == list:
        val.extend(val2)
    elif type_val in [dict, odict, Munch2] and type_val2 in [dict, odict, Munch2]:
        for k, v in val2.items():
            val[k] = v
    return val


def fn_update(update, parent):
    def walk(u, p):
        tu, tp = type(u), type(p)
        if tu in [dict, odict, Munch2] and tp in [dict, odict, Munch2]:
            for k, v in u.items():
                p[k] = walk(v, p.get(k, v))
            return p
        else:
            return u

    walk(update, parent)


def fn_encrypt_names(names: dict):
    def fn_encrypt(data, etype=None, ekey=None):
        r = (names if names else {}).get('R', {}).get('_', {})
        etype = etype if etype else r.get('etype')
        ekey = ekey if ekey else r.get('ekey')
        token = None
        if etype == 'fernet':
            f = Fernet(ekey)
            token = f.encrypt(data=str(data).encode()).decode()
        return token

    return fn_encrypt


def fn_crypt_generate_key_names(names: dict = None):
    def fn_crypt_generate_key(etype=None):
        r = (names if names else {}).get('R', {}).get('_', {})
        etype = etype if etype else r.get('etype')
        if etype == 'fernet':
            key = Fernet.generate_key()
            return key

    return fn_crypt_generate_key


def fn_decrypt_names(names: dict):
    def fn_decrypt(data, etype=None, ekey=None):
        r = (names if names else {}).get('R', {}).get('_', {})
        etype = etype if etype else r.get('etype')
        ekey = ekey if ekey else r.get('ekey')
        message = None
        if etype == 'fernet':
            f = Fernet(ekey)
            message = f.decrypt(token=str(data).encode()).decode()
        return message

    return fn_decrypt


def fn_inc_names(names: dict):
    def fn_inc(fs_path, itype: str = 'yaml', fs_root: str = None, errors=None):
        fs_root = fs_root if fs_root else (names if names else {}).get('R', {}).get('_', {}).get('fs_root')
        data = None
        if itype == 'yaml':
            data = load(fs_path=fs_path, fs_root=fs_root, errors=errors)
        return data

    return fn_inc


def parse_expr(expr: str, names: dict, fns: dict, errors: list = None):
    errors = errors if type(errors) == list else []
    names2 = Munch2.fromDict({**names, **{

    }})
    fns = {'F': update_recursive(fns, {
        'list': {
            'next': fn_list_next,
            'join': fn_list_join
        },
        'str': fn_str,
        'has': fn_has,
        'next': fn_list_next,
        'join': fn_list_join,
        'trim': fn_str_trim,
        'extend': fn_extend,
        'update': fn_update,
        'encrypt': fn_encrypt_names(names2),
        'decrypt': fn_decrypt_names(names2),
        'inc': fn_inc_names(names2)
    })}
    s = EvalWithCompoundTypes(names=names2, functions=fns)
    try:
        v = s.eval(expr=expr)
    except Exception as ex:
        v = expr
        errors.append([expr, ex])
    v = filter_value(v)
    return v


def parse(root, names: dict = None, fns: dict = None, parent=None, errors: list = None):
    names = names if names else {'R': root}
    fns = fns if fns else {}
    errors = errors if type(errors) == list else []
    root_type = type(root)
    if root_type == dict or root_type == collections.OrderedDict:
        root_keys = list(root.keys())
        for k, v in root.items():
            root[k] = parse(root=v, names=names, fns=fns, parent=root, errors=errors)
        if 'F.extend' in root_keys:
            root = fn_extend(root['F.extend'], root)
            if isinstance(root, dict):
                del root['F.extend']
        if 'F.update' in root_keys:
            fn_update(root['F.update'], root)
            del root['F.update']
    elif root_type == list:
        for i, v in enumerate(root):
            root[i] = parse(root=v, names=names, fns=fns, parent=root, errors=errors)
    elif root_type == str:
        value = root
        if type(value) == str:
            value = parse_expr(root, names=names, fns=fns, errors=errors)
        return value
    return root


def load(fs_path: str, fs_root: str = '', errors: list = None, params: dict = None, opts: dict = None):
    errors = errors if type(errors) == list else []
    fs_file_path = os.path.join(fs_root, fs_path)
    fs_root = fs_root if fs_root is None else os.path.dirname(fs_file_path)
    params = params if params else {}
    opts = opts if opts else {
        'max_power': simpleeval.MAX_POWER,
        'max_string_length': simpleeval.MAX_STRING_LENGTH,
        'disallow_prefixes': simpleeval.DISALLOW_PREFIXES
    }
    try:
        with open(fs_file_path) as stream:
            # load_yaml initial structure
            data = yaml.safe_load(stream)
            data['_'] = data['_'] if data.get('_') else {}
            data_internal = {'fs_path': fs_path, 'fs_root': fs_root}
            data_internal = {**{'etype': 'fernet'}, **data_internal, **params}
            data['_'] = {**data['_'], **data_internal}
            names = {'R': data}
            fns = {}
            data = parse(data, names=names, fns=fns)
            # data cleanup to ensure no data_internal
            all(map(data['_'].pop, data_internal))
            # remove when empty
            if len(data['_']) == 0:
                del data['_']
            return data
    except Exception as ex:
        errors.append([fs_file_path, ex])
    return None
