# conff
Simple config parser with evaluator library.

### Why Another Config Parser Module?
This project started because of the complexity of project config. It needs:
- import mechanism from other file or object
- ability to encrypt/decrypt values with ease
- expression on the config to have flexibility to the environments

One can argue, it is better to put into PY file, however,
having config in python script may give too much power than what it requires. 

### Install
```bash
[sudo] pip install conff
```

### Basic Usage
To get very basic parsing: 
```python
import conff

# parse object
conff.parse({'math': '1 + 3'})
# {'math': '4'}

# load YAML file
data = conff.load('path_of_file.yaml')

# import files
## y1.yml
# shared_conf: 1

## y2.yml
# conf: F.inc('y1.yml')

data = conff.load('y2.yml')
# {'conf': {'shared_conf': 1}}
```

### Examples
```python
import conff

### parse with simple expression
conff.parse('1 + 2')
# 3


### parse object
conff.parse({"math": "1 + 2"})
# {'math': 3}


### ignore expression (declare it as string)
conff.parse('"1 + 2"')
# '1 + 2'


### any errors will be stored as string and the string of expression will be retained
errors = []
conff.parse({"math": "1 / 0"}, errors=errors)
# {'math': '1 / 0'}
# errors = [['1 / 0', ZeroDivisionError('division by zero',)]]


### parse with functions
def fn_add(a, b):
    return a + b
conff.parse('F.add(1, 2)', fns={'add': fn_add})
# 3


### parse with names
conff.parse('a + b', names={'a': 1, 'b': 2})
# 3


### parse with extends
data = {
    't1': {'a': 'a'},
    't2': {
        'F.extend': 'R.t1',
        'b': 'b'
    }
}
conff.parse(data)
# {'t1': {'a': 'a'}, 't2': {'a': 'a', 'b': 'b'}}


### parse with updates
data = {
    't1': {'a': 'a'},
    't2': {
        'b': 'b',
        'F.update': {
            'c': 'c'
        },
    }
}
conff.parse(data)
# {'t1': {'a': 'a'}, 't2': {'b': 'b', 'c': 'c'}}


### parse with extends and updates
data = {
    't1': {'a': 'a'},
    't2': {
        'F.extend': 'R.t1',
        'b': 'b',
        'F.update': {
            'a': 'A',
            'c': 'c'
        },
    }
}
conff.parse(data)
# {'t1': {'a': 'a'}, 't2': {'a': 'A', 'b': 'b', 'c': 'c'}}
```

### Test
To test this project:
```bash
nose2 --with-coverage
```

### Other Open Source
This opensource project uses other awesome projects:
+   [`Munch`](https://github.com/Infinidat/munch)
+   [`simpleeval`](https://github.com/danthedeckie/simpleeval)
+   [`cryptography`](https://github.com/pyca/cryptography)
