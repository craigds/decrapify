# Try:
#    ./fstrings.py testfile.py
# TODO write proper tests ;)
a = 'a'

b = a % ()

c = 'this is a string'

interpolated = 'interpolated'
string = 'string'
a_dict = {'a': 'interpolated'}

'this is an %s string' % interpolated
'this is an %s string' % (interpolated,)
'this is an %s %s' % (interpolated, string)
'this is an %s %s' % (interpolated, string,)

'this is an {} string'.format(interpolated)
'this is an {} {}'.format(interpolated, string)
'this is an {1} {0}'.format(string, interpolated)

'this is an {} {string}'.format(interpolated, string=string)
'this is an {} {xyz}'.format(interpolated, xyz=string)
'this is an {a} {0}'.format(string, **a_dict)

'this is an {interpolated} string'.format(interpolated=interpolated)

u"the 'u' should go away from this {string}".format(string=string)
r"the 'r' should be preserved in this {string}".format(string=string)

# Cases to *ignore*:
# mostly we only really want basic names in f-strings,
# because including too much can harm readability:
'this is an {} string'.format('interpolated')
'this is an {} string'.format(a_dict['a'])
# 'b' and 'f' prefixes can't be combined
b"this kind of {string} shouldn't become an f-string".format(string=string)


# pytestify.py

class Foo(unittest.TestCase):
    # This won't be modified
    def assertEqual(self, foo, bar, msg):
        pass

    def test_assertequal(self):
        # won't be modified
        self.assertEqual()
        self.assertEqual('a')
        self.assertEqual('a', 'b', 'c', 'd')
        self.assertEqual(*args)
        self.assertNotEqual()
        self.assertNotEqual('a')
        self.assertNotEqual('a', 'b', 'c', 'd')
        self.assertNotEqual(*args)

        # will be modified
        self.assertEqual( 'a', 'b' )
        self.assertEqual('a', 'b')
        self.assertEqual('a', 'b', 'c')
        self.assertEqual('a', 'b', message='c')
        self.assertEqual('a', 1, message='c')
        self.assertNotEqual( 'a', 'b' )
        self.assertNotEqual('a', 'b')
        self.assertNotEqual('a', 'b', 'c')
        self.assertNotEqual('a', 'b', message='c')
        self.assertNotEqual('a', 1, message='c')

        # special cases
        # --> 'assert a is None', etc
        self.assertEqual(a, None)
        self.assertEqual(None, a)
        self.assertNotEqual(a, None)
        self.assertNotEqual(None, a)
        # --> 'assert a', etc. NOTE: assertEqual *doesn't* do `assert a is True`
        self.assertEqual(a, True)
        self.assertNotEqual(a, True)
        self.assertEqual(a, False)
        self.assertNotEqual(a, False)
        self.assertEqual(True, a)

        # some synonyms
        self.assertEquals('a', 'b', 'c')
        self.failUnlessEqual('a', 'b', 'c')
        self.failIfEqual('a', 'b', 'c')

        # multi-line ones
        self.assertEqual(
            'a',
            'b')
        self.assertEqual('a',
            'b')
        self.assertEqual(
            'a',
            'b'
        )
        self.assertEqual(
            'a'
            ,
            'b'
            ,
            'message'
            ,
        )

        self.assertIn(x, y)
        self.assertNotIn(x, y)

        self.assertEqual((a, b, c), (d, e, f))

        self.assertIsInstance(a, b, msg)
        self.assertNotIsInstance(a, b, msg)

    def test_asserttrue(self):
        # ignored
        self.assertTrue()
        self.assertTrue(a, b, c)

        # modified
        self.assertTrue(a == b)
        self.assertTrue(a == b, message)
        self.assertTrue('a'
            ' string', message
        )
        self.failIf(a == b)

        # some synonyms
        self.failIf(a)
        self.failUnless(a)
        self.assert_(a)


# obvious_cleanup.py

# left alone
a == b
a != b

# modified
not a == b
not a != b
not a is not b
not a < b
not a > b
not a <= b
not a >= b
not a is not b
not a is b

a == None
a != None

dict([(a, b) for a, b in x])
dict((a, b) for a, b in x)
dict(((a, b) for a, b in x))
{a: b for a, b in x}

dict([(a, b) for a, b in x if y])
dict((a, b) for a, b in x if y)
dict(((a, b) for a, b in x if y))
{a: b for a, b in x if y}

dict([
    (a, b)
    for a, b in x
])
dict(
    (a, b) for a, b
    in x
)
dict(
    (
        (a, b) for a, b in x
    )
)


set([a for a in x])
set((a for a in x))
set(a for a in x)

set([
    a for a in x
])
set(
    (
        a for a in x
    )
)
set(
    a for a in x
)
