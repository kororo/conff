import posixpath
from munch import Munch
from collections import OrderedDict as odict

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

        # try:
        head, tail = posixpath.split(k)
        if head:
            ret = self[head]
        else:
            ret = self
        super(Munch2, ret).__setitem__(tail, v)

    def __delitem__(self, key):
        head, tail = posixpath.split(key)
        if head:
            ret = self[head]
        else:
            ret = self
        super(Munch2, ret).__delitem__(tail)


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


def yaml_safe_load(stream):
    import yaml
    from yaml.resolver import BaseResolver

    def ordered_load(stream, loader_cls):
        class OrderedLoader(loader_cls):
            pass

        def construct_mapping(loader, node):
            loader.flatten_mapping(node)
            return odict(loader.construct_pairs(node))

        OrderedLoader.add_constructor(BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
        return yaml.load(stream, OrderedLoader)

    return ordered_load(stream, yaml.SafeLoader)


def filter_value(value):
    if isinstance(value, str):
        if value == '[empty]':
            value = ''
    if isinstance(value, str):
        value = value.strip()
    return value
