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

# Cases to *ignore* (mostly we only really want basic names in f-strings,
# because including too much can harm readability)
'this is an {} string'.format('interpolated')
'this is an {} string'.format(a_dict['a'])
