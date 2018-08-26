# This file exists for testing fstrings.py.
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
