conff
=====

Simple config parser with evaluator library.

.. image:: https://badge.fury.io/py/conff.svg
    :target: https://badge.fury.io/py/conff

.. image:: https://travis-ci.com/kororo/conff.svg?branch=master
    :target: https://travis-ci.com/kororo/conff

.. image:: https://coveralls.io/repos/github/kororo/conff/badge.svg?branch=master
    :target: https://coveralls.io/github/kororo/conff?branch=master

.. image:: https://api.codeclimate.com/v1/badges/c476e9c6bfe505bc4b4d/maintainability
    :target: https://codeclimate.com/github/kororo/conff/maintainability
    :alt: Maintainability

.. image:: https://badges.gitter.im/kororo-conff.png
    :target: https://gitter.im/kororo-conff
    :alt: Gitter


Why Another Config Parser Module?
---------------------------------

This project inspired of the necessity complex config in a project. By means complex:

- Reusability

  - Import values from file
  - Reference values from other object

- Secure

  - Encrypt/decrypt sensitive values

- Flexible

  - Make logical expression to derive values
  - Combine with `jinja2 <http://jinja.pocoo.org/docs/2.10/>`_ template based

- Powerful

  - Add custom functions in Python
  - Link name data from Python

Feedback and Discussion
-----------------------

Come to Gitter channel to discuss, pass any feedbacks and suggestions. If you like to be contributor, please do let me know.

Important Notes
---------------

Parsing Order
^^^^^^^^^^^^^

conff will only parse and resolve variable/names top to bottom order. Please ensure you arrange your configuration
in the same manner, there is no auto-dependencies resolver to handle complex and advanced names currently.

dict vs collections.OrderedDict
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In Python 3.5, the dict data type has inconsistent ordering, it is **STRONGLY** recommended to use **OrderedDict** if
you manually parse object. If you load from YAML file, the library already handled it. The reason of order is important,
this due to simplification and assumption of order execution. The library will parse the values from top to bottom as
per order in the key-value dictionary.

Install
-------

.. code:: bash

   [sudo] pip install conff

Basic Usage
-----------

To get very basic parsing:

Simple parse
^^^^^^^^^^^^

.. code:: python

    import conff
    p = conff.Parser()
    r = p.parse({'math': '1 + 3'})
    assert r == {'math': 4}

Load YAML file
^^^^^^^^^^^^^^

.. code:: python

    import conff
    p = conff.Parser()
    r = p.load('path_of_file.yml')

Template based config
^^^^^^^^^^^^^^^^^^^^^

Using `jinja2 <http://jinja.pocoo.org/docs/2.10/>`_ to craft more powerful config.

.. code:: python

    import conff
    p = conff.Parser()
    r = p.parse('F.template("{{ 1 + 2 }}")')
    assert r == 3


Examples
--------

More advances examples:

Parse with simple expression
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    import conff
    p = conff.Parser()
    r = p.parse('1 + 2')
    assert r == 3

Parse object
^^^^^^^^^^^^

.. code:: python

    import conff
    p = conff.Parser()
    r = p.parse({"math": "1 + 2"})
    assert r == {'math': 3}

Ignore expression (declare it as string)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    import conff
    p = conff.Parser()
    r = conff.parse('"1 + 2"')
    assert r == '1 + 2'

Parse error behaviours
^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    import conff
    p = conff.Parser()
    r = p.parse({'math': '1 / 0'})
    # Exception raised
    # ZeroDivisionError: division by zero


import files
^^^^^^^^^^^^

.. code:: python

    import conff
    ## y1.yml
    # shared_conf: 1
    ## y2.yml
    # conf: F.inc('y1.yml')

    p = conff.Parser()
    r = p.load('y2.yml')
    assert r == {'conf': {'shared_conf': 1}}

Parse with functions
^^^^^^^^^^^^^^^^^^^^

.. code:: python

    import conff
    def fn_add(a, b):
        return a + b
    p = conff.Parser(fns={'add': fn_add})
    r = p.parse('F.add(1, 2)')
    assert r == 3

Parse with names
^^^^^^^^^^^^^^^^

.. code:: python

    import conff
    p = conff.Parser(names={'a': 1, 'b': 2})
    r = conff.parse('a + b')
    assert r == 3

Parse with extends
^^^^^^^^^^^^^^^^^^

.. code:: python

    import conff
    data = {
       't1': {'a': 'a'},
       't2': {
           'F.extend': 'R.t1',
           'b': 'b'
       }
    }
    p = conff.Parser()
    r = p.parse(data)
    assert r == {'t1': {'a': 'a'}, 't2': {'a': 'a', 'b': 'b'}}

Parse with updates
^^^^^^^^^^^^^^^^^^

.. code:: python

    import conff
    data = {
       't1': {'a': 'a'},
       't2': {
           'b': 'b',
           'F.update': {
               'c': 'c'
           },
       }
    }
    p = conff.Parser()
    r = p.parse(data)
    assert r == {'t1': {'a': 'a'}, 't2': {'b': 'b', 'c': 'c'}}

Parse with extends and updates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    import conff
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
    p = conff.Parser()
    r = p.parse(data)
    assert r == {'t1': {'a': 'a'}, 't2': {'a': 'A', 'b': 'b', 'c': 'c'}}

Create a list of values
^^^^^^^^^^^^^^^^^^^^^^^

This creates a list of floats, similar to numpy.linspace

.. code:: python

    import conff
    data = {'t2': 'F.linspace(0, 10, 5)'}
    p = conff.Parser()
    r = p.parse(data)
    assert r == {'t2': [0.0, 2.5, 5.0, 7.5, 10.0]}

This also creates a list of floats, but behaves like numpy.arange (although
slightly different in that it is inclusive of the endpoint).

.. code:: python

    import conff
    data = {'t2': 'F.arange(0, 10, 2)'}
    p = conff.Parser()
    r = p.parse(data)
    assert r == {'t2': [0, 2, 4, 6, 8, 10]}

Parse with for each
^^^^^^^^^^^^^^^^^^^

One can mimic the logic of a for loop with the following example

.. code:: python

    import conff
    data = {'t1': 2,
           'F.foreach': {
               'values': 'F.linspace(0, 10, 2)',
               # You have access to loop.index, loop.value, and loop.length
               # within the template, as well as all the usual names
               'template': {
                    '"test%i"%loop.index': 'R.t1*loop.value',
                    'length': 'loop.length'
                    }
               }
          }
    p = conff.Parser()
    r = p.parse(data)
    assert r == {'length': 3, 't1': 2, 'test0': 0.0, 'test1': 10.0, 'test2': 20.0}

Encryption
----------

This section to help you to quickly generate encryption key, initial encrypt values and test to decrypt the value.

.. code:: python

    import conff
    # generate key, save it somewhere safe
    names = {'R': {'_': {'etype': 'fernet'}}}
    etype = conff.generate_key(names)()
    # or just
    ekey = conff.generate_key()('fernet')

    # encrypt data
    # BIG WARNING: this should be retrieved somewhere secured for example in ~/.secret
    # below just for example purposes
    ekey = 'FOb7DBRftamqsyRFIaP01q57ZLZZV6MVB2xg1Cg_E7g='
    names = {'R': {'_': {'etype': 'fernet', 'ekey': ekey}}}
    # gAAAAABbBBhOJDMoQSbF9jfNgt97FwyflQEZRxv2L2buv6YD_Jiq8XNrxv8VqFis__J7YlpZQA07nDvzYwMU562Mlm978uP9BQf6M9Priy3btidL6Pm406w=
    encrypted_value = conff.encrypt(names)('ACCESSSECRETPLAIN1234')

    # decrypt data
    ekey = 'FOb7DBRftamqsyRFIaP01q57ZLZZV6MVB2xg1Cg_E7g='
    names = {'R': {'_': {'etype': 'fernet', 'ekey': ekey}}}
    encrypted_value = 'gAAAAABbBBhOJDMoQSbF9jfNgt97FwyflQEZRxv2L2buv6YD_Jiq8XNrxv8VqFis__J7YlpZQA07nDvzYwMU562Mlm978uP9BQf6M9Priy3btidL6Pm406w='
    conff.decrypt(names)(encrypted_value)

Real World Examples
-------------------

All the example below located in `data directory <https://github.com/kororo/conff/tree/master/conff/data>`_.
Imagine you start an important project, your code need to analyse image/videos which involves workflow
with set of tasks with AWS Rekognition. The steps will be more/less like this:

    1. Read images/videos from a specific folder, if images goes to (2), if videos goes to (3).

    2. Analyse the images with AWS API, then goes (4)

    3. Analyse the videos with AWS API, then goes (4)

    4. Write the result back to JSON file, finished

The configuration required:

    1. Read images/videos (where is the folder)

    2. Analyse images (AWS API credential and max resolution for image)

    3. Analyse videos (AWS API credential and max resolution for video)

    4. Write results (where is the result should be written)

1. Without conff library
^^^^^^^^^^^^^^^^^^^^^^^^

File: `data/sample_config_01.yml <https://github.com/kororo/conff/tree/master/conff/data/sample_config_01.yml>`_

Where it is all started, if we require to store the configuration as per normally, it should be like this.

.. code:: yaml

    job:
      read_image:
        # R01
        root_path: /data/project/images_and_videos/
      analyse_image:
        # R02
        api_cred:
          region_name: ap-southeast-2
          aws_access_key_id: ACCESSKEY1234
          # R03
          aws_secret_access_key: ACCESSSECRETPLAIN1234
        max_res: [1024, 768]
      analyse_video:
        # R04
        api_cred:
          region_name: ap-southeast-2
          aws_access_key_id: ACCESSKEY1234
          aws_secret_access_key: ACCESSSECRETPLAIN1234
        max_res: [800, 600]
      write_result:
        # R05
        output_path: /data/project/result.json

.. code:: python

    import yaml
    with open('data/sample_config_01.yml') as stream:
        r1 = yaml.safe_load(stream)

Notes:

    - R01: The subpath of "/data/project" is repeated between R01 and R05
    - R02: api_cred is repeatedly defined with R04
    - R03: the secret is plain visible, if this stored in GIT, it is pure disaster

2. Fix the repeat
^^^^^^^^^^^^^^^^^

File: `data/sample_config_02.yml <https://github.com/kororo/conff/tree/master/conff/data/sample_config_02.yml>`_

Repeating values/configuration is bad, this could potentially cause human mistake if changes made is not
consistently applied in all occurences.

.. code:: yaml

    # this can be any name, as long as not reserved in Python
    shared:
      project_path: /data/project
      aws_cred:
        region_name: ap-southeast-2
        aws_access_key_id: ACCESSKEY1234
        # F03
        aws_secret_access_key: F.decrypt('gAAAAABbBBhOJDMoQSbF9jfNgt97FwyflQEZRxv2L2buv6YD_Jiq8XNrxv8VqFis__J7YlpZQA07nDvzYwMU562Mlm978uP9BQf6M9Priy3btidL6Pm406w=')

    job:
      read_image:
        # F01
        root_path: R.shared.project_path + '/images_and_videos/'
      analyse_image:
        # F02
        api_cred: R.shared.aws_cred
        max_res: [1024, 768]
      analyse_video:
        # F04
        api_cred: R.shared.aws_cred
        max_res: [800, 600]
      write_result:
        # F05
        output_path: R.shared.project_path + '/result.json'

.. code:: python

    import conff
    # ekey is the secured encryption key
    # WARNING: this is just demonstration purposes
    ekey = 'FOb7DBRftamqsyRFIaP01q57ZLZZV6MVB2xg1Cg_E7g='
    r2 = conff.load(fs_path='data/sample_config_02.yml', params={'ekey': ekey})

Notes:

    - F01: it is safe if the prefix '/data/project' need to be changed, it will automatically changed for F05
    - F02: no more duplicated config with F04
    - F03: it is secured to save this to GIT, as long as the encryption key is stored securely somewhere in server such
      as ~/.secret

3. Optimise to the extreme
^^^^^^^^^^^^^^^^^^^^^^^^^^

File: `data/sample_config_03.yml <https://github.com/kororo/conff/tree/master/conff/data/sample_config_03.yml>`_

This is just demonstration purposes to see the full capabilities of this library.

.. code:: yaml

    # this can be any name, as long as not reserved in Python
    shared:
      project_path: /data/project
      analyse_image_video:
        api_cred:
          region_name: ap-southeast-2
          aws_access_key_id: ACCESSKEY1234
          aws_secret_access_key: F.decrypt('gAAAAABbBBhOJDMoQSbF9jfNgt97FwyflQEZRxv2L2buv6YD_Jiq8XNrxv8VqFis__J7YlpZQA07nDvzYwMU562Mlm978uP9BQf6M9Priy3btidL6Pm406w=')
        max_res: [1024, 768]
    job:
      read_image:
        root_path: R.shared.project_path + '/images_and_videos/'
      analyse_image: R.shared.analyse_image_video
      analyse_video:
        F.extend: R.shared.analyse_image_video
        F.update:
          max_res: [800, 600]
      write_result:
        output_path: R.shared.project_path + '/result.json'

For completeness, ensuring data is consistent and correct between sample_config_01.yml, sample_config_02.yml
and sample_config_03.yml.

.. code:: python

    # nose2 conff.test.ConffTestCase.test_sample
    fs_path = 'data/sample_config_01.yml'
    with open(fs_path) as stream:
        r1 = yaml.safe_load(stream)
    fs_path = 'data/sample_config_02.yml'
    ekey = 'FOb7DBRftamqsyRFIaP01q57ZLZZV6MVB2xg1Cg_E7g='
    r2 = conff.load(fs_path=fs_path, params={'ekey': ekey})
    fs_path = 'data/sample_config_03.yml'
    r3 = conff.load(fs_path=fs_path, params={'ekey': ekey})
    self.assertDictEqual(r1['job'], r2['job'], 'Mismatch value')
    self.assertDictEqual(r2['job'], r3['job'], 'Mismatch value')

Test
----

To test this project:

.. code:: bash

   # default test
   nose2

   # test with coverage
   nose2 --with-coverage

   # test specific
   nose2 conff.test.ConffTestCase.test_sample

TODO
----

- [X] Setup basic necessity

  - [X] Stop procrastinating
  - [X] Project registration in pypi
  - [X] Create unit tests
  - [X] Setup travis
  - [X] Setup coveralls

- [ ] Add more support on `Python versions <https://en.wikipedia.org/wiki/CPython#Version_history>`_

  - [ ] 2.7
  - [ ] 3.4
  - [X] 3.5
  - [X] 3.6

- [ ] Features

  - Wish List Features now moved to `wiki page <https://github.com/kororo/conff/wiki/Wish-List-Features>`_.

- [ ] Improve docs

  - [ ] Add more code comments and visibilities
  - [ ] Make github layout code into two left -> right
  - [X] Put more examples
  - [ ] Setup readthedocs
  - [ ] Add code conduct, issue template into git project.
  - [ ] Add information that conff currently accept YML and it not limited, it can take any objects


Other Open Source
-----------------

This project uses other awesome projects:

- `cryptography <https://github.com/pyca/cryptography>`_
- `jinja2 <http://jinja.pocoo.org/docs/2.10/>`_
- `munch <https://github.com/Infinidat/munch>`_
- `simpleeval <https://github.com/danthedeckie/simpleeval>`_
- `yaml <https://github.com/yaml/pyyaml>`_

Who uses conff?
---------------

Please send a PR to keep the list growing, if you may please add your handle and company.
