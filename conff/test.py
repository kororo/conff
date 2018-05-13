import os
from unittest import TestCase
from cryptography.fernet import Fernet

import conff


class ConffTestCase(TestCase):
    def setUp(self):
        super(ConffTestCase, self).setUp()
        # set path
        current_path = os.path.dirname(os.path.abspath(__file__))
        self.test_data_path = os.path.join(current_path, 'data')

    def get_test_data_path(self, fs_path: str):
        return os.path.join(self.test_data_path, fs_path)

    def test_simple_load_yaml(self):
        fs_path = self.get_test_data_path('test_config_01.yml')
        data = conff.load(fs_path=fs_path)
        data = data if data else {}
        self.assertDictEqual(data, {'test_1': 'test_1', 'test_2': ''})

    def test_complex_load_yml(self):
        fs_path = self.get_test_data_path('test_config_02.yml')
        key = Fernet.generate_key()
        data = conff.load(fs_path=fs_path, params={'ekey': key})
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
        self.assertListEqual(data.get('test_9', {}).get('test_9_1'), [True, False])
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

    def test_error_load_yaml(self):
        fs_path = self.get_test_data_path('test_config_03.yml')
        data = conff.load(fs_path=fs_path)
        self.assertIsNone(data)

    def test_parse(self):
        data = conff.parse('{"a": "a", "b": "1/0"}', names={}, fns={})
        self.assertDictEqual(data, {'a': 'a', 'b': '1/0'})
