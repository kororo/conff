import conff
from conff import utils
from unittest import TestCase

class Munch2TestCase(TestCase):
    def setUp(self):
        super(Munch2TestCase, self).setUp()
        self.maxDiff = None

    def test_path_splitter(self):
        d = {'a': {'b1': 1, 'b2': 2, 'b3': {'c1': 1}}}
        m = utils.Munch2.fromDict(d)
        self.assertListEqual(utils.splitall('a/b/c'), ['a', 'b', 'c'])
        self.assertListEqual(utils.splitall('/a/b/c'), ['a', 'b', 'c'])
        self.assertListEqual(utils.splitall('a/b/c/'), ['a', 'b', 'c'])
        self.assertListEqual(utils.splitall('/a/b/c/'), ['a', 'b', 'c'])
        self.assertListEqual(utils.splitall('a/../b/c'), ['b', 'c'])
        self.assertListEqual(utils.splitall('/a/../b/c/'), ['b', 'c'])
        self.assertListEqual(utils.splitall('/a/../a/b/c/'), ['a', 'b', 'c'])

    def test_get(self):
        d = {'a': {'b1': 1, 'b2': 2, 'b3': {'c1': 1}}}
        m = utils.Munch2.fromDict(d)
        self.assertEqual(m.a.b1, 1)
        self.assertEqual(m['a/b1'], 1)
        self.assertEqual(m.a.b3.c1, 1)
        self.assertEqual(m['a/b3/c1'], 1)
        self.assertDictEqual(m.a, {'b1': 1, 'b2': 2, 'b3': {'c1': 1}})
        self.assertDictEqual(m.a.b3, {'c1': 1})
        self.assertDictEqual(m['a'], {'b1': 1, 'b2': 2, 'b3': {'c1': 1}})
        self.assertDictEqual(m['a/b3'], {'c1': 1})
        with self.assertRaises(KeyError) as context:
            m['a/nonsense']
        self.assertTrue("missing from path" in str(context.exception))

    def test_set(self):
        d = {'a': {'b1': 1, 'b2': 2, 'b3': {'c1': 1}}}
        m = utils.Munch2.fromDict(d)
        m['a/b2'] = 4
        self.assertEqual(m.a.b2, 4)
        self.assertEqual(m['a/b2'], 4)
        m['a/b3'] = {'c1': 2, 'c2': 3}
        self.assertDictEqual(m['a/b3'], {'c1': 2, 'c2': 3})
        m['a/b3'] = [1, '2']
        self.assertListEqual(m['a/b3'], [1, '2'])
        m['a'] = 'done'
        self.assertEqual(m['a'], 'done')
        # Test setting nested items in an empty Munch
        empty = utils.Munch2()
        empty['a/b1'] = 3
        self.assertDictEqual(empty['a'], {'b1': 3})
        self.assertEqual(empty['a/b1'], 3)

    def test_del(self):
        d = {'a': {'b1': 1, 'b2': 2, 'b3': {'c1': 1}}}
        m = utils.Munch2.fromDict(d)
        del m['a/b2']
        self.assertDictEqual(m, {'a': {'b1': 1, 'b3': {'c1': 1}}})
        del m['a/b3']
        self.assertDictEqual(m, {'a': {'b1': 1}})
        del m['a']
        self.assertDictEqual(m, {})

