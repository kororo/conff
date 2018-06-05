from munch import Munch
from collections import OrderedDict as odict


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
