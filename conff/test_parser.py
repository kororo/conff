import os
import tempfile
import shutil
from distutils.dir_util import copy_tree
from unittest import TestCase
import yaml
import conff
from conff import utils
import pprint


class ConffTestCase(TestCase):
    def setUp(self):
        super(ConffTestCase, self).setUp()
        # set path
        current_path = os.path.dirname(os.path.abspath(__file__))
        test_data_path = os.path.join(current_path, 'data')
        self.test_data_path = tempfile.mkdtemp()
        copy_tree(test_data_path, self.test_data_path)
        self.maxDiff = None

    def tearDown(self):
        shutil.rmtree(self.test_data_path)

    def get_test_data_path(self, fs_path: str):
        return os.path.join(self.test_data_path, fs_path)

    def test_simple_load_yaml(self):
        fs_path = self.get_test_data_path('test_config_01.yml')
        p = conff.Parser()
        data = p.load(fs_path=fs_path)
        data = data if data else {}
        self.assertDictEqual(data, {'test_1': 'test_1', 'test_2': ''})

    def test_ext_up_load_yaml(self):
        fs_path = self.get_test_data_path('test_config_04.yml')
        p = conff.Parser()
        data = p.load(fs_path=fs_path)
        data = data if data else {}
        self.assertDictEqual(data, {
            "test_13": {"test_13_1": 1, "test_13_2": 2, "test_13_3": 3, "test_13_5": {"test_13_5_1": 1},
                        "test_13_6": {"test_13_6_1": 1}},
            "test_14": {"test_13_1": 11, "test_13_2": 2, "test_13_3": 3, "test_13_5": 5,
                        "test_13_6": {"test_13_6_1": 1, "test_13_6_2": {"test_13_6_2_1": 1, "test_13_6_2_2": 2}},
                        "test_13_4": 4}})

    def test_load_json(self):
        fs_path = self.get_test_data_path('test_config_01.json')
        p = conff.Parser()
        data = p.load(fs_path=fs_path)
        data = data if data else {}
        self.assertDictEqual(data, {'test_1': 1, 'test_2': 2})

    def test_complex_load_yml(self):
        p = conff.Parser()
        fs_path = self.get_test_data_path('test_config_02.yml')
        p.generate_crypto_key()
        data = p.load(fs_path=fs_path)
        data = data if data else {}
        # test simple types
        self.assertEqual(data.get('test_1'), 'test_1')
        self.assertEqual(data.get('test_2'), 2)
        self.assertListEqual(data.get('test_3'), ['test_3', 3])
        self.assertDictEqual(data.get('test_4'), {'test_4_1': 'test_4_1'})
        self.assertDictEqual(data.get('test_5'), {'test_5_1': 'test_5_1', 'test_5_2': {'test_5_2_1': 'test_5_2_1'}})
        # test expression
        self.assertEqual(data.get('test_6'), 'test_6')
        # test extends
        self.assertListEqual(data.get('test_7', {}).get('test_7_1'), [1, 2])
        self.assertListEqual(data.get('test_7', {}).get('test_7_2'), [1, 2])
        self.assertDictEqual(data.get('test_7', {}).get('test_7_3'), {'data2_1': 1, 'data2_2': 2, 'data2_3': 3})
        # test complex extends
        self.assertDictEqual(data.get('test_8'), {'data2_1': 1, 'data2_2': '2a', 'data2_3': 3, 'data2_4': 4})
        # test complex expressions
        self.assertListEqual(data.get('test_9', {}).get('test_9_1'), [True, False, True, False])
        self.assertListEqual(data.get('test_9', {}).get('test_9_2'), [1, 'RO'])
        self.assertEqual(data.get('test_9', {}).get('test_9_3'), '1 2 3')
        self.assertEqual(data.get('test_9', {}).get('test_9_4'), 'ro/ro')
        # test error expressions
        self.assertEqual(data.get('test_10'), 'F.no_exist()')
        # test encryption
        self.assertEqual(data.get('test_11'), 'test_11')
        # test importing
        self.assertDictEqual(data.get('test_12'), {'test_1': 'test_1', 'test_2': ''})
        # test update
        data_test_13 = {'test_13_1': 1, 'test_13_2': 2, 'test_13_3': 3, 'test_13_5': {'test_13_5_1': 1},
                        'test_13_6': {'test_13_6_1': 1}}
        self.assertDictEqual(data.get('test_13'), data_test_13)
        # test extend + update
        data_test_14 = {'test_13_1': 11, 'test_13_2': 2, 'test_13_3': 3, 'test_13_5': 5,
                        'test_13_6': {'test_13_6_1': 1, 'test_13_6_2': {'test_13_6_2_1': 1, 'test_13_6_2_2': 2}},
                        'test_13_4': 4}
        self.assertDictEqual(data.get('test_14'), data_test_14)
        # test foreach with linspace
        data_test_15 = {'test0': {'value': 0, 'length': 3},
                        'test1': {'value': 3, 'length': 3},
                        'test2': {'value': 6, 'length': 3}}
        self.assertDictEqual(data.get('test_15'), data_test_15)
        # test foreach with arange. Should get same result as above
        data_test_16 = data_test_15
        self.assertDictEqual(data.get('test_16'), data_test_16)
        # test foreach with arange. Testing behavior of arange
        data_test_17 = {'test0': {'value': 0, 'length': 2},
                        'test1': {'value': 4, 'length': 2}}
        self.assertDictEqual(data.get('test_17'), data_test_17)
        data_test_18 = {'test_18_1': 3}
        self.assertDictEqual(data.get('test_18'), data_test_18)

    def test_error_load_yaml(self):
        p = conff.Parser()
        fs_path = self.get_test_data_path('test_config_03.yml')
        with self.assertRaises(yaml.constructor.ConstructorError) as context:
            data = p.load(fs_path=fs_path)

    def test_error_foreach(self):
        p = conff.Parser()
        fs_path = self.get_test_data_path('malformed_foreach_01.yml')
        with self.assertRaises(ValueError):
            p.load(fs_path=fs_path)
        fs_path = self.get_test_data_path('malformed_foreach_02.yml')
        with self.assertRaises(ValueError):
            p.load(fs_path=fs_path)

    def test_parse(self):
        p = conff.Parser()
        data = p.parse('{"a": "a", "b": "1/0"}')
        self.assertDictEqual(data, {'a': 'a', 'b': '1/0'})
        data = p.parse(utils.odict([('a', 'a'), ('b', '1 + 2')]))
        self.assertDictEqual(data, {'a': 'a', 'b': 3})

    def test_parse_with_fns(self):
        def fn_add(a, b):
            return a + b

        fns = {'add': fn_add, 'test': {'add': fn_add}}
        p = conff.Parser(fns=fns)
        data = p.parse('{"a": "a", "b": "1/0", "c": F.add(1, 2), "d": F.test.add(2, 2)}')
        self.assertDictEqual(data, {'a': 'a', 'b': '1/0', 'c': 3, 'd': 4})

    def test_parse_dict_with_names(self):
        names = {'c': 1, 'd': 2}
        p = conff.Parser(names=names)
        data = p.parse(utils.odict([('a', 'a'), ('b', 'c + d')]))
        self.assertDictEqual(data, {'a': 'a', 'b': 3})

    def test_missing_operators(self):
        names = {'c': 1, 'd': 2}
        p = conff.Parser(names=names, params={'simpleeval': {'operators': {'not': 'an_operator'}}})
        with self.assertRaises(KeyError) as context:
            p.parse(utils.odict([('a', 'a'), ('b', 'c + d')]))
        self.assertTrue("<class '_ast.Add'>" in str(context.exception))

    def test_generate_crypto(self):
        p = conff.Parser()
        del p.params['etype']
        key = p.generate_crypto_key()
        self.assertTrue(key is None)
        self.assertTrue(p.params['ekey'] is None)
        p.params['etype'] = 'nonsense'
        key = p.generate_crypto_key()
        self.assertTrue(key is None)
        self.assertTrue(p.params['ekey'] is None)

    def test_encryption(self):
        # generate key, save it somewhere safe
        names = {'R': {'_': {'etype': 'fernet'}}}
        ekey = 'FOb7DBRftamqsyRFIaP01q57ZLZZV6MVB2xg1Cg_E7g='
        names = {'R': {'_': {'etype': 'fernet', 'ekey': ekey}}}
        original_value = 'ACCESSSECRETPLAIN1234'
        encrypted_value = conff.encrypt(names)(original_value)
        # decrypt data
        value = conff.decrypt(names)(encrypted_value)
        self.assertEqual(original_value, value, 'Value mismatch')

    def test_sample(self):
        # nose2 conff.test.ConffTestCase.test_sample
        fs_path = self.get_test_data_path('sample_config_01.yml')
        with open(fs_path) as stream:
            r1 = yaml.safe_load(stream)
        fs_path = self.get_test_data_path('sample_config_02.yml')
        ekey = 'FOb7DBRftamqsyRFIaP01q57ZLZZV6MVB2xg1Cg_E7g='
        errors = []
        r2 = conff.load(fs_path=fs_path, params={'ekey': ekey}, errors=errors)
        fs_path = self.get_test_data_path('sample_config_03.yml')
        r3 = conff.load(fs_path=fs_path, params={'ekey': ekey})
        print('#'*25)
        pprint.pprint("r2['job'] = {}".format(r2['job']))
        pprint.pprint("r3['job'] = {}".format(r3['job']))
        self.assertDictEqual(r1['job'], r2['job'], 'Mismatch value')
        self.assertDictEqual(r2['job'], r3['job'], 'Mismatch value')

    def test_object(self):
        # nose2 conff.test.ConffTestCase.test_object
        # TODO: add test when trying to combine config as object with conff
        # test update
        class Test(object):
            test = None

        data = Test()
        conff.update(data, {'test': 'test'})
        self.assertEqual('test', data.test, 'Value mismatch')

    def test_warning(self):
        p = conff.Parser()
        with self.assertWarns(Warning):
            data = p.parse({'a': 'a', 'b': '1 + 2'})
            print('data: ', data)
            self.assertDictEqual(data, {'a': 'a', 'b': 3})

    def test_update_recursive(self):
        fns = {'F': conff.update({'a': 1}, {'b': {'c': 2}})}
        self.assertDictEqual(fns, {'F': {'a': 1, 'b': {'c': 2}}})

    def test_parse_old(self):
        data = conff.parse('{"a": "a", "b": "1/0"}')
        self.assertDictEqual(data, {'a': 'a', 'b': '1/0'})
        data = conff.parse(utils.odict([('a', 'a'), ('b', '1 + 2')]))
        self.assertDictEqual(data, {'a': 'a', 'b': 3})

    def test_encryption_old(self):
        # generate key, save it somewhere safe
        names = {'R': {'_': {'etype': 'fernet'}}}
        etype = conff.generate_key(names)()
        ekey = 'FOb7DBRftamqsyRFIaP01q57ZLZZV6MVB2xg1Cg_E7g='
        names = {'R': {'_': {'etype': 'fernet', 'ekey': ekey}}}
        original_value = 'ACCESSSECRETPLAIN1234'
        encrypted_value = conff.encrypt(names)(original_value)
        # decrypt data
        value = conff.decrypt(names)(encrypted_value)
        self.assertEqual(original_value, value, 'Value mismatch')

    def test_fn_template(self):
        p = conff.Parser(names={'test': 1})
        fs_path = self.get_test_data_path('test_config_05.yml')
        data = p.load(fs_path)
        data = data if data else {}
        # test: simple value
        self.assertEqual(data.get('test_1'), 1)
        # test: template as string, it is seamless names from input (test) and template (test_1)
        self.assertEqual(data.get('test_2'), 2)
        # test: template as file (borrowing F.inc capabilities), if test_tpl_01.tpl is {{1 + 2}}
        self.assertEqual(data.get('test_3'), 3)
        # test: this where attaching more complex object
        data_test_4 = {
            "test_4_0": [3, 4], "test_4_1": 1, "test_4_2": 2, "test_4_3": 3, "test_4_4": 4, "test_4_5": 5,
            "test_4_6": 6
        }
        self.assertDictEqual(data.get('test_4'), data_test_4)
