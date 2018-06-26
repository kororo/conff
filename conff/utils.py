import posixpath
import os
import json
from munch import Munch
from collections import (
    OrderedDict as odict,
    MutableMapping,
)
import yaml
try:
    from yaml import (
        CLoader as Loader,
        CDumper as Dumper,
        CSafeLoader as SafeLoader,
        CSafeDumper as SafeDumper,
    )
except ImportError:
    from yaml import (
        Loader,
        Dumper,
        SafeLoader,
        SafeDumper,
    )
_YAML_MAP_TAG = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG


class FancyDict(MutableMapping):
    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)

    def __getitem__(self, k):
        """
        This override allows us to get a nested value in a dict using a forward
        slash separated string
        """

        parts = self._get_parts(k)
        return self.getfromseq(parts)

    def __setitem__(self, k, v):
        """
        This setup allows setting a value inside a nested dictionary using
        either a slash separated string or a list/tuple with the usual []
        operator.
        """

        parts = self._get_parts(k)
        self.setfromseq(parts, v)

    def __delitem__(self, k):
        parts = self._get_parts(k)
        self.delfromseq(parts)

    def _get_parts(self, k):
        if isinstance(k, str):
            parts = splitall(k)

        elif isinstance(k, (tuple, list)):
            parts = k
        else:
            raise ValueError('Key must be a slash separated string, list, '
                             'or tuple')
        return parts

    def getfromseq(self, keyset):
        """
        A convenience method to get the section of the config file located
        at the end of the sequence of keys
        """

        try:
            ret = self._d
            for key in keyset:
                ret = ret[key]
        except KeyError as ex:
            key = ex.args[0]
            msg = 'Key {} missing from path {}'.format(key, keyset)
            ex.args = (msg,)
            raise
        return ret

    def setfromseq(self, keyset, value):
        """
        A convenience method to set the a value in the config given a sequence
        of keys
        """
        sect = self._d
        for key in keyset[:-1]:
            if key in sect:
                sect = sect[key]
            else:
                sect[key] = {}
                sect = sect[key]
        sect[keyset[-1]] = value

    def delfromseq(self, keyset):
        """
        Deletes the section of the config located at the end of a sequence
        of keys
        """
        del self.getfromseq(keyset[:-1])[keyset[-1]]

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __str__(self):
        return str(self._d)

    def __repr__(self):
        return repr(self._d)

    def flatten(self, skip_branch=None, sep='/'):
        """
        Returned a flattened copy of the nested data structure.

        The keys will be the full path to the item's location in the nested
        data structure separated using the optional sep kwarg, and the value
        will be the value at that location

        Parameters
        ----------
        sep : str, default '/'
            The separating character used for all paths
        skip_branch : list, optional
            A list of `sep` separated paths to branches in the config that you
            would like to skip when flattening. This can be leaves in the
            Config or entire branches

        Returns
        -------
        dict
            A dict whose keys are `sep` separated strings representing the full
            path to the value in the originally nested dictionary. The values
            are the same as those from the original dictionary.

        Examples
        --------
        >>> c = Config({'a': {'b': 1, 'c': 2})
        >>> c.flatten()
        {'a/b': 1, 'a/c': 2}
        >>> c.flatten(sep='_')
        {'a_b': 1, 'a_c': 2}
        >>> c.flatten(sep='_', skip_branch='a_c')
        {'a_b': 1}
        """
        return self._flatten(skip_branch=skip_branch, sep=sep)

    def _flatten(self, branch=None, flattened=None, keypath='',
                 skip_branch=None, sep='/'):
        """
        Internal, recursive flattening implementation
        """
        flattened = flattened if flattened is not None else {}
        skip_branch = skip_branch if skip_branch is not None else []
        if keypath:
            branch = branch if branch is not None else self._d[keypath]
        else:
            branch = branch if branch is not None else self._d
        if isinstance(branch, dict):
            for key, val in branch.items():
                newpath = sep.join([keypath, key]).strip(sep)
                if keypath in skip_branch:
                    continue
                if isinstance(val, dict):
                    self._flatten(branch=val, flattened=flattened,
                                  keypath=newpath, skip_branch=skip_branch,
                                  sep=sep)
                else:
                    flattened[newpath] = val
        return flattened

    @classmethod
    def _to_yaml(cls, dumper, conf):
        return dumper.represent_dict({'ID': conf.ID,
                                      'skip_keys': conf.skip_keys,
                                      '_d': conf._d})

    @classmethod
    def fromYAML(cls, *args, skip_keys=None, **kwargs):
        """
        Return an instance of a Config object given a raw YAML string or a
        file-like object containing valid YAML syntax. Handles arbitrary YAML
        and YAML dumped by another Config object
        """
        data = yaml.load(*args, **kwargs)
        skip_keys = skip_keys if skip_keys is not None else []
        if 'skip_keys' in data:
            for item in data['skip_keys']:
                if isinstance(item, list):
                    skip_keys.append(tuple(item))
                else:
                    skip_keys.append(item)
            del data['skip_keys']
        if 'ID' in data and '_d' in data:
            return cls(data['_d'], skip_keys=skip_keys)
        else:
            return cls(data, skip_keys=skip_keys)

    @staticmethod
    def fromJSON(stream, **kwargs):
        """
        Load config from a JSON stream (either string or file-like object)
        """
        return json.loads(stream)

    @classmethod
    def fromFile(cls, path, syntax='yaml', **kwargs):
        """
        Load config from a file given a path. File must be in YAML or JSON
        syntax
        """
        syntax = syntax.lower()
        if syntax not in ('yaml', 'json'):
            raise ValueError('Can only load from yaml or JSON files')
        path = os.path.expandvars(path)
        if not os.path.isfile(path):
            raise ValueError("Path {} is not a regular file".format(path))
        d = {'yaml': cls.fromYAML, 'json': cls.fromJSON}
        with open(path, 'r') as stream:
            inst = d[syntax](stream, **kwargs)
        return inst

    def write(self, f):
        """
        Dumps this config object to its YAML representation given a path to a
        file
        """
        if isinstance(f, str):
            f = os.path.expandvars(f)
            f = open(f, 'w')
        yaml.dump(self, stream=f, default_flow_style=False)

    def dump(self):
        """
        Returns YAML representation of this particular config
        """
        return yaml.dump(self, default_flow_style=False)


def construct_odict(loader, node):
    loader.flatten_mapping(node)
    return odict(loader.construct_pairs(node))


def represent_odict(dumper, data):
    return dumper.represent_dict(data.iteritems())


class OrderedLoader(SafeLoader):
    """
    We subclass the SafeLoader so we don't globally mess up any YAML loaders
    that the client application might be using elsewhere. The modifications we
    make invasively convert all mappings to OrderedDicts, which might not be
    desired in any client applications
    """
    pass


# I think it is safe to globally add this representer, because worst case
# scenario OrderedDicts get dumped as a normal dict would without throwing any
# exceptions
yaml.add_representer(odict, represent_odict)
# Means all mapping tags will be loaded and returned as OrderedDicts
OrderedLoader.add_constructor(_YAML_MAP_TAG, construct_odict)


def yaml_safe_load(stream):
    return yaml.load(stream)


def splitall(path):
    """
    Get each individual component in a path separated by forward slashes.
    Relative paths are normalized first.

    :param path: A slash separated path /like/this/../here
    :type path: str

    :return: A list of all the parts in the path
    :rtype: list
    """

    path = posixpath.normpath(path.strip('/'))
    allparts = []
    while True:
        parts = posixpath.split(path)
        if parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


def update_recursive(d, u):
    """
    Update dictionary recursively. It traverse any object implements
    "collections.Mapping", anything else, it overwrites the original value.
    :param d: Original dictionary to be updated
    :param u: Value dictionary
    :return: Updated dictionary after merged
    """
    for k, v in u.items():
        if isinstance(d, MutableMapping):
            d2 = d.get(k, {})
        else:
            d2 = getattr(d, k, object())

        if isinstance(v, MutableMapping):
            r = update_recursive(d2, v)
            u2 = r
        else:
            u2 = u[k]

        if isinstance(d, MutableMapping):
            d[k] = u2
        else:
            setattr(d, k, u2)
    return d


def filter_value(value):
    if isinstance(value, str):
        if value == '[empty]':
            value = ''
    if isinstance(value, str):
        value = value.strip()
    return value
