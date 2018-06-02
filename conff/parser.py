import os
import collections
import yaml
import hashlib
import six
import copy
import simpleeval
import pprint
from simpleeval import EvalWithCompoundTypes
from collections import Iterable, MutableMapping, OrderedDict
from collections import OrderedDict as odict
from cryptography.fernet import Fernet

from .ee import yaml_safe_load, Munch2, filter_value, update_recursive


class Parser:
    opts = {
        'max_power': simpleeval.MAX_POWER,
        'max_string_length': simpleeval.MAX_STRING_LENGTH,
        'disallow_prefixes': simpleeval.DISALLOW_PREFIXES
    }

    def __init__(self, params=None, names=None, fns=None, operators=None,
                 opts=None):
        """
        :param params: A dictionary containing some parameters that will modify
        how the builtin functions run. For example, the type of encryption to
        use and the encrpyption key to use
        """

        self._params = params if params is not None else {}
        self._params.update({'etype': 'fernet'})
        self._operators = operators if operators is not None else simpleeval.DEFAULT_OPERATORS
        opts = opts if opts is not None else {}
        self.opts.update(opts)
        self._names = Munch2(names) if names is not None else {}
        fns = fns if fns is not None else {}
        self._fns = {'F': update_recursive(fns, {fn[3:]: getattr(self, fn)
                                                 for fn in dir(self) if
                                                 'fn_' in fn})}
        # Update simpleeval safety options
        for k, v in opts.items():
            setattr(simpleeval, k.upper(), v)
        self._eval = EvalWithCompoundTypes()
        # self._evals_functions should mirror self._fns
        # TODO: Make a test to ensure proper mirroring
        self._eval.functions = self._fns
        self._eval.names = self._names
        if operators:
            self._operators = operators
            self._eval.operators = self._operators
        self.errors = []

    def parse_file(self, fs_path: str, fs_root: str = '',
                   include_dirs: list = [], syntax='yaml'):
        """
        Parse configuration file on disk.

        :param fs_path: The path to the file on disk. If fs_root is specified,
        this will be interpreted as a path relative to fs_root
        :type fs_path: str
        :param fs_root: Root directory to use when parsing. Defaults to the
        directory of the input file.
        :type fs_root: str
        :param include_dirs: A list of additional directories in which to
        search for included files. Always contains the directory of the input
        file, and will also contain fs_root if specified.
        :type include_dirs: list
        :param syntax: The syntax of the file on disk. Defaults to YAML
        :type syntax: str
        """
        fs_file_path = os.path.join(fs_root, fs_path)
        fs_root = fs_root if fs_root is None else os.path.dirname(fs_file_path)
        self._params.update({'fs_path': fs_path, 'fs_root': fs_root})
        with open(fs_file_path) as stream:
            # load_yaml initial structure
            data = yaml_safe_load(stream, ordered=True)
            names = {'R': data}
            self._names.update(names)
            data = self._parse(data)
        # Delete anything specific to this file so we can reuse the parser
        for k in ('fs_path', 'fs_root', 'R'):
            if k in self._params:
                del self._params[k]
        return data

    def parse_dict(self, in_data):
        """
        Parse a dictionary containing conff syntax
        """
        names = {'R': in_data}
        self._names.update(names)
        data = self._parse(in_data)
        return data

    def parse_expr(self, expr: str):
        """
        Parse a string
        """
        try:
            v = self._eval.eval(expr=expr)
        except SyntaxError as ex:
            v = expr
            # print("Raised simpleeval exception {} for expression {}".format(type(ex), v))
            self.errors.append([expr, ex])
        except simpleeval.InvalidExpression as ex:
            v = expr
            # print("Raised simpleeval exception {} for expression {}".format(type(ex), v))
            # print("Raised simpleeval exception {} for expression {}".format(type(ex), v))
            # print("Message: {}".format(ex))
            self.errors.append(ex)
        except Exception as ex:
            print('Exception on expression: {}'.format(expr))
            raise
        v = filter_value(v)
        return v

    def _parse(self, root):
        """
        The main parsing function
        """
        root_type = type(root)
        if root_type == dict or root_type == odict:
            root_keys = list(root.keys())
            for k, v in root.items():
                root[k] = self._parse(v)
            if 'F.extend' in root_keys:
                root = self.fn_extend(root['F.extend'], root)
                if isinstance(root, dict):
                    del root['F.extend']
            if 'F.update' in root_keys:
                self.fn_update(root['F.update'], root)
                del root['F.update']
            if 'F.foreach' in root_keys:
                for k in ('values', 'template'):
                    if k not in root['F.foreach']:
                        raise ValueError('F.foreach missing key: {}'.format(k))
                self.fn_foreach(root['F.foreach'], root)
                del root['F.foreach']
        elif root_type == list:
            for i, v in enumerate(root):
                root[i] = self._parse(root=v)
        elif root_type == str:
            value = root
            if type(value) == str:
                value = self.parse_expr(root)
            return value
        return root

    def add_functions(self, funcs: dict):
        """
        Add functions to the list of available parsing function. Funcs should
        be a dict whose keys are the name you would like the function to have,
        and whose value is a callable that maps to that name. The functions
        will be callable via F.name_of_func(args_go_here)
        """

    def add_names(self, names: dict):
        """
        Add names to the dictionary of names available when parsing. These
        names are accessible via the syntax R.path.to.name
        """

    def generate_crypto_key(self):
        """
        Generate a cryptographic key for encrypting data. Stores the key in
        self._params['ekey'] so it is accessible to encrypt parsing functions.
        Also returns the key
        """

        try:
            etype = self._params['etype']
        except KeyError:
            etype = 'fernet'
        if etype == 'fernet':
            key = Fernet.generate_key()
        else:
            key = None
        self._params['ekey'] = key
        return key

    def fn_str(self, val):
        return str(val)

    def fn_float(self, val):
        return float(val)

    def fn_int(self, val):
        return int(val)

    def fn_has(self, val, name):
        if isinstance(val, collections.Mapping):
            return val.get(name, False) is not False
        else:
            return name in val

    def fn_next(self, vals, default=None):
        vals = [vals] if type(vals) != list else vals
        val = next(iter(vals), default)
        return val

    def fn_join(self, vals, sep=' '):
        vals = [val for val in vals if val]
        return sep.join(vals)

    def fn_trim(self, val: str, cs: list = None):
        cs = cs if cs else ['/', ' ']
        for c in cs:
            val = val.strip(c)
        return val

    def fn_linspace(self, start, end, steps):
        delta = (end-start)/(steps-1)
        return [start + delta*i for i in range(steps)]

    def fn_arange(self, start, end, delta):
        vals = [start]
        while vals[-1] + delta <= end:
            vals.append(vals[-1] + delta)
        return vals

    def fn_extend(self, val, val2):
        val = copy.deepcopy(val)
        type_val = type(val)
        type_val2 = type(val2)
        if type_val == list and type_val2 == list:
            val.extend(val2)
        elif type_val in [dict, odict, Munch2] and type_val2 in [dict, odict, Munch2]:
            for k, v in val2.items():
                val[k] = v
        return val

    def fn_update(self, update, parent):
        def walk(u, p):
            tu, tp = type(u), type(p)
            if tu in [dict, odict, Munch2] and tp in [dict, odict, Munch2]:
                for k, v in u.items():
                    p[k] = walk(v, p.get(k, v))
                return p
            else:
                return u
        walk(update, parent)

    def fn_encrypt(self, data):
        etype = self._params.get('etype', None)
        ekey = self._params.get('ekey', None)
        token = None
        if etype == 'fernet':
            f = Fernet(ekey)
            token = f.encrypt(data=str(data).encode()).decode()
        return token

    def fn_decrypt(self, data):
        etype = self._params.get('etype', None)
        ekey = self._params.get('ekey', None)
        message = None
        if etype == 'fernet':
            f = Fernet(ekey)
            message = f.decrypt(token=str(data).encode()).decode()
        return message

    def fn_inc(self, fs_path, syntax: str = 'yaml', fs_root: str = None):
        fs_root = fs_root if fs_root else self._params['fs_root']
        # Make sure to pass on any modified options to the sub parser
        sub_parser = Parser(opts=self.opts)
        data = sub_parser.parse_file(fs_path=fs_path, fs_root=fs_root,
                                     syntax=syntax)
        return data

    def fn_foreach(self, foreach, parent):
        template = foreach['template']
        if not isinstance(template, dict):
            raise ValueError('template item of F.foreach must be a dict')
        for i, v in enumerate(foreach['values']):
            self._names.update({'loop': {'index': i, 'value': v,
                                'length': len(foreach['values'])}})
            result = {}
            for key, val in template.items():
                pkey = self.parse_expr(key)
                pval = self._parse(copy.copy(val))
                result[pkey] = pval
            parent.update(result)
        # remove this specific foreach loop info from names dict so we don't
        # break any subsequent foreach loops
        del self._names['loop']
