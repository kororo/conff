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


Why Another Config Parser Module?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This project inspired of the necessity complex config in a project. By means complex:

- Reusability

  - Import values from file
  - Reference values from other object

- Secure

  - Encrypt/decrypt sensitive values

- Flexible

  - Make logical expression to derive values

- Powerful

  - Add custom functions in Python
  - Link name data from Python

TODO
~~~~

- [X] Setup basic necessity

  - [X] Stop procrastinating
  - [X] Project registration in pypi
  - [X] Create unit tests
  - [X] Setup travis
  - [X] Setup coveralls

- [ ] Add more support on Python versions (based on. `Python versions <https://en.wikipedia.org/wiki/CPython#Version_history)>`_

  - [ ] 2.7
  - [ ] 3.4
  - [X] 3.5
  - [X] 3.6

- [ ] Features

  - [X] Add more functions for encryption
  - [ ] Test on multilanguage
  - [ ] Add better exception handling
  - [ ] Add circular dependencies error
  - [ ] Ensure this is good on production environment
  - [X] Add options to give more flexibility
  - [ ] Check safety on the evaluator, expose more of its options such as (MAX_STRING)

- [ ] Improve docs

  - [ ] Add more code comments and visibilities
  - [ ] Make github layout code into two left -> right
  - [X] Put more examples
  - [ ] Setup readthedocs

Install
~~~~~~~

.. code:: bash

   [sudo] pip install conff

Basic Usage
-----------

To get very basic parsing:

.. code:: python

   import conff
   r = conff.parse({'math': '1 + 3'})
   r = {'math': '4'}

load YAML file
^^^^^^^^^^^^^^

.. code:: python

   import conff
   r = conff.load('path_of_file.yaml')

import files
^^^^^^^^^^^^

.. code:: python

   import conff
   ## y1.yml
   # shared_conf: 1
   ## y2.yml
   # conf: F.inc('y1.yml')

   r = conff.load('y2.yml')
   r = {'conf': {'shared_conf': 1}}


Real World Examples
-------------------

All the example below located in `data directory <https://github.com/kororo/conff/tree/master/conff/data>`_.
Imagine you start an important project, your code need to analyse image/videos which involves workflow
with set of tasks involve with AWS Rekognition. The steps will be more/less like this:

    1. Read images/videos from a specific folder, if images goes to (2), if videos goes to (3).

    2. Analyse the images with AWS API

    3. Analyse the videos with AWS API

    4. Write the result back to JSON file

The configuration required:

    1. Read images/videos (where is the folder)

    2. Analyse images (AWS API credential and max resolution for image)

    3. Analyse videos  (AWS API credential and max resolution for image)

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

    # this can be any name, global, conf, shared
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

Examples
--------

More advances examples:

Parse with simple expression
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

   import conff
   r = conff.parse('1 + 2')
   r = 3

Parse object
^^^^^^^^^^^^

.. code:: python

   import conff
   r = conff.parse({"math": "1 + 2"})
   r = {'math': 3}

Ignore expression (declare it as string)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

   import conff
   r = conff.parse('"1 + 2"')
   r = '1 + 2'

Parse error behaviours
^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

   import conff
   errors = []
   r = conff.parse({"math": "1 / 0"}, errors=errors)
   r = {'math': '1 / 0'}
   errors = [['1 / 0', ZeroDivisionError('division by zero',)]]

Parse with functions
^^^^^^^^^^^^^^^^^^^^

.. code:: python

   import conff
   def fn_add(a, b):
       return a + b
   r = conff.parse('F.add(1, 2)', fns={'add': fn_add})
   r = 3

Parse with names
^^^^^^^^^^^^^^^^

.. code:: python

   import conff
   r = conff.parse('a + b', names={'a': 1, 'b': 2})
   r = 3

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
   r = conff.parse(data)
   r = {'t1': {'a': 'a'}, 't2': {'a': 'a', 'b': 'b'}}

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
   r = conff.parse(data)
   r = {'t1': {'a': 'a'}, 't2': {'b': 'b', 'c': 'c'}}

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
   r = conff.parse(data)
   r = {'t1': {'a': 'a'}, 't2': {'a': 'A', 'b': 'b', 'c': 'c'}}

Encryption
~~~~~~~~~~

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

Test
~~~~

To test this project:

.. code:: bash

   # default test
   nose2

   # test with coverage
   nose2 --with-coverage

   # test specific
   nose2 conff.test.ConffTestCase.test_sample


Other Open Source
~~~~~~~~~~~~~~~~~

This project uses other awesome projects:

- `munch <https://github.com/Infinidat/munch>`_
- `simpleeval <https://github.com/danthedeckie/simpleeval>`_
- `cryptography <https://github.com/pyca/cryptography>`_

Who uses conff?
~~~~~~~~~~~~~~~

Please send a PR to keep the list growing, if you may please add your handle and company.
