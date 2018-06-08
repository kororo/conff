import posixpath
from munch import Munch
from collections import OrderedDict as odict
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


class Munch2(Munch):
    """
    Provide easy way to access item in object by dot-notation or with a slash
    separatred string representing a path.
    Example:
        obj = {'outer': {'inner': 'value'}}
        # old way
        value = obj.get('outer').get('inner')
        # with munch2
        value = obj.outer.inner
        # or
        value = obj['outer/inner']
    """

    def __getitem__(self, k):
        """
        This override allows us to get a nested value in a dict using a forward
        slash separated string
        """

        try:
            parts = splitall(k)
            ret = super().__getitem__(parts[0])
            for part in parts[1:]:
                ret = super(Munch2, ret).__getitem__(part)
            return ret
        except KeyError as ex:
            key = ex.args[0]
            msg = 'Key {} missing from path {}'.format(key, parts)
            ex.args = (msg,)
            raise

    def __setitem__(self, k, v):
        """
        This setup allows setting a value inside a nested dictionary using a
        slash separated string with the usual [] operator.
        """

        parts = splitall(k)
        ret = self
        for part in parts[:-1]:
            if part not in ret:
                super(Munch2, ret).__setitem__(part, Munch2())
            ret = ret[part]
        super(Munch2, ret).__setitem__(parts[-1], v)

    def __delitem__(self, key):
        head, tail = posixpath.split(key)
        if head:
            ret = self[head]
        else:
            ret = self
        super(Munch2, ret).__delitem__(tail)


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
    return yaml.load(stream, Loader=OrderedLoader)


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
    if isinstance(value, str):
        if value == '[empty]':
            value = ''
    if isinstance(value, str):
        value = value.strip()
    return value
