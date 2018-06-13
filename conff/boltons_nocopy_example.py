from boltons.iterutils import remap, default_enter, default_exit, default_visit
from collections import Mapping, Sequence, Set, ItemsView

# def enter(p, k, v):
#     print('enter path: {}'.format(p))
#     print('enter key: {}'.format(k))
#     print('enter value: {}'.format(v))
#     return v, v 
def enter(path, key, value):
    if isinstance(value, dict):
        return value, ItemsView(value)
    else:
        return default_enter(path, key, value)


def visit(p, k, v):
    print('visit path: {}'.format(p))
    print('visit key: {}'.format(k))
    print('visit value: {}'.format(v))
    return k, v

orig = {'a1': {'b1': 1, 'b2': 2}}

new = remap(orig, visit=visit, enter=enter)
print('ORIG ID: {}'.format(id(orig)))
print('NEW: {}'.format(new))
print('NEW ID: {}'.format(id(new)))
