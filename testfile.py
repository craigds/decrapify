# This file exists for testing.
# TODO write proper tests ;)
a = 'a'

b = a % ()

c = 'this is a string'

interpolated = 'interpolated'
d = 'this is an %s string' % interpolated
e = 'this is an %s string' % (interpolated,)
f = 'this is an {} string'.format(interpolated)
g = 'this is an {interpolated} string'.format(interpolated=interpolated)
