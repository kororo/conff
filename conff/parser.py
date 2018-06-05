import json
import logging
import os
import collections
import copy
import sys

import simpleeval
import warnings
from jinja2 import Template
from simpleeval import EvalWithCompoundTypes
from cryptography.fernet import Fernet
from conff import utils
from conff.utils import Munch2, update_recursive, yaml_safe_load, filter_value, odict


class Parser:
    # default params
    default_params = {
        'etype': 'fernet',
        # list of simpleeval library parameters
        'simpleeval': {
            # by default operators = simpleeval.DEFAULT_OPERATORS,
            'operators': {},
            'options': {
                'max_power': simpleeval.MAX_POWER,
                'max_string_length': simpleeval.MAX_STRING_LENGTH,
                'disallow_prefixes': simpleeval.DISALLOW_PREFIXES
            }
        }
    }

    def __init__(self, names=None, fns=None, params=None):
        """
        :param params: A dictionary containing some parameters that will modify
        how the builtin functions run. For example, the type of encryption to
        use and the encrpyption key to use or simpleeval library parameters
        """
        self.errors = []
        self.logger = self.prepare_logger()
        self.params = self.prepare_params(params=params)
        self.fns = self.prepare_functions(fns=fns)
        self.names = self.prepare_names(names=names)
        self._evaluator = self.prepare_evaluator()

    def prepare_logger(self):
        logger = logging.getLogger('conff')
        return logger

    def prepare_params(self, params: dict = None):
        """
        Setup parameters for the library

        :param params: A dictionary containing some parameters that will modify
        how the builtin functions run. For example, the type of encryption to
        use and the encrpyption key to use or simpleeval library parameters

        :return: Prepared parameters
        """
        # ensure not to update mutable params
        params = copy.deepcopy(params or {})
        # inject with default params with exception for simpleeval.operators
        params = utils.update_recursive(params, self.default_params)
        return params

    def prepare_functions(self, fns: dict = None):
        fns = fns or {}
        cls_fns = {fn[3:]: getattr(self, fn) for fn in dir(self) if 'fn_' in fn}
        result = {'F': update_recursive(fns, cls_fns)}
        return result

    def prepare_names(self, names: dict = None):
        names = names or {}
        names = names if isinstance(names, Munch2) else Munch2(names)
        return names

    def prepare_evaluator(self):
        """
        Setup evaluator engine

        :return: Prepare evaluator engine
        """
        simpleeval_params = self.params.get('simpleeval', {})
        # update simpleeval safety options
        for k, v in simpleeval_params.get('options', {}).items():
            setattr(simpleeval, k.upper(), v)
        evaluator = EvalWithCompoundTypes()
        # self._evals_functions should mirror self.fns
        # TODO: Make a test to ensure proper mirroring
        evaluator.functions = self.fns
        evaluator.names = self.names
        # set the operators
        if simpleeval_params.get('operators'):
            evaluator.operators = simpleeval_params.get('operators')

        return evaluator

    def load(self, fs_path: str, fs_root: str = '', fs_include: list = None):
        """
        Parse configuration file on disk.

        :param fs_path: The path to the file on disk. If fs_root is specified,
        this will be interpreted as a path relative to fs_root
        :type fs_path: str
        :param fs_root: Root directory to use when parsing. Defaults to the
        directory of the input file.
        :type fs_root: str
        :param fs_include: A list of additional directories in which to
        search for included files. Always contains the directory of the input
        file, and will also contain fs_root if specified.
        :type fs_include: list
        """
        fs_file_path = os.path.join(fs_root, fs_path)
        _, fs_file_ext = os.path.splitext(fs_file_path)
        fs_root = fs_root if fs_root is None else os.path.dirname(fs_file_path)
        self.params.update({'fs_path': fs_path, 'fs_root': fs_root})
        with open(fs_file_path) as stream:
            if 'yml' in fs_file_ext:
                # load_yaml initial structure
                data = yaml_safe_load(stream)
                names = {'R': data}
                self.names.update(names)
                data = self._process(data)
            elif 'json' in fs_file_ext:
                data = json.loads(stream.read())
                names = {'R': data}
                self.names.update(names)
                data = self._process(data)
            else:
                data = '\n'.join(stream.readlines())
        # Delete anything specific to this file so we can reuse the parser
        for k in ('fs_path', 'fs_root', 'R'):
            if k in self.params:
                del self.params[k]
        return data

    def parse(self, data):
        """
        Main entry point to parse arbitary data type
        :param data: Input can be any data type such as dict, list, string, int
        :return: Parsed data
        """
        if isinstance(data, dict):
            if type(data) == dict:
                warnings.warn('argument type is in dict, please use collections.OrderedDict for guaranteed order.')
            self.names.update(data)
            result = self._process(data)
        else:
            result = self.parse_expr(data)
        return result

    def parse_expr(self, expr: str):
        """
        Parse an expression in string
        """
        try:
            v = self._evaluator.eval(expr=expr)
        except SyntaxError as ex:
            v = expr
            # TODO: feature T2
            # print("Raised simpleeval exception {} for expression {}".format(type(ex), v))
            self.errors.append([expr, ex])
        except simpleeval.InvalidExpression as ex:
            v = expr
            # TODO: feature T2
            # print("Raised simpleeval exception {} for expression {}".format(type(ex), v))
            # print("Raised simpleeval exception {} for expression {}".format(type(ex), v))
            # print("Message: {}".format(ex))
            self.errors.append(ex)
        except Exception as ex:
            v = expr
            # TODO: feature T2
            # print('Exception on expression: {}'.format(expr))
            self.errors.append(ex)
            raise
        # TODO: feature T4: include this part of the classes so user could override
        v = filter_value(v)
        return v

    def _process(self, root):
        """
        The main parsing function
        """
        root_type = type(root)
        if root_type == dict or root_type == odict:
            root_keys = list(root.keys())
            for k, v in root.items():
                root[k] = self._process(v)
            if 'F.extend' in root_keys:
                root = self.fn_extend(root['F.extend'], root)
                if isinstance(root, dict):
                    del root['F.extend']
            if 'F.template' in root_keys:
                root = self.fn_template(root['F.template'], root)
                if isinstance(root, dict):
                    del root['F.template']
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
                root[i] = self._process(root=v)
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
        self.params['ekey'] so it is accessible to encrypt parsing functions.
        Also returns the key
        """
        etype = self.params.get('etype')
        if etype == 'fernet':
            key = Fernet.generate_key()
        else:
            key = None
        self.params['ekey'] = key
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
        delta = (end - start) / (steps - 1)
        return [start + delta * i for i in range(steps)]

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
        etype = self.params.get('etype', None)
        ekey = self.params.get('ekey', None)
        token = None
        if etype == 'fernet':
            f = Fernet(ekey)
            token = f.encrypt(data=str(data).encode()).decode()
        return token

    def fn_decrypt(self, data):
        etype = self.params.get('etype', None)
        ekey = self.params.get('ekey', None)
        message = None
        if etype == 'fernet':
            f = Fernet(ekey)
            message = f.decrypt(token=str(data).encode()).decode()
        return message

    def fn_inc(self, fs_path, fs_root: str = None):
        fs_root = fs_root if fs_root else self.params['fs_root']
        # Make sure to pass on any modified options to the sub parser
        sub_parser = Parser(params=self.params)
        data = sub_parser.load(fs_path=fs_path, fs_root=fs_root)
        return data

    def fn_foreach(self, foreach, parent):
        template = foreach['template']
        if not isinstance(template, dict):
            raise ValueError('template item of F.foreach must be a dict')
        for i, v in enumerate(foreach['values']):
            self.names.update({'loop': {'index': i, 'value': v,
                                        'length': len(foreach['values'])}})
            result = {}
            for key, val in template.items():
                pkey = self.parse_expr(key)
                pval = self._process(copy.copy(val))
                result[pkey] = pval
            parent.update(result)
        # remove this specific foreach loop info from names dict so we don't
        # break any subsequent foreach loops
        del self.names['loop']

    def fn_template(self, template: str, root=None):
        engine = Template(template)
        obj_str = engine.render(**self.names)
        result = obj_str

        # TODO: feature T2
        obj = utils.yaml_safe_load(obj_str)
        if root and isinstance(obj, dict):
            result = self.fn_extend(root, obj)
        return result


class ParserPlugin(object):
    pass
