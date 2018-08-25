#!/usr/bin/env python3
"""
A sample pybowler pipeline that demonstrates replacement of
various types of string-interpolation with f-strings.

Implemented:
    * 'stringliteral %s' % name

TODO: plenty:
    * Handle other printf-style things other than '%s', e.g. '%20d' etc.
    * Handle interpolating with a tuple of names instead of just one name
    * Handle .format(), with both args and kwargs
"""

from pprint import pprint
import re
import sys

from bowler import Query, TOKEN
from bowler.types import Leaf, Node


RE_OLD_INTERPOLATION = re.compile(r'(?<!%)%s')


def convert_to_fstrings(node, capture, filename):
    pprint (capture)
    pprint(list(capture['node'].children))

    formatstring = node.children[0]
    operand = node.children[2]
    if isinstance(operand, Leaf) and operand.type == TOKEN.NAME:
        # string interpolation (old style), where the thing on the right is a name.
        # First, check that there's only one instance of '%s' in the string.
        if len(RE_OLD_INTERPOLATION.findall(formatstring.value)) == 1:
            # Replace '%s' in the formatstring with '{argumentname}'
            replacement_value = RE_OLD_INTERPOLATION.sub(
                '{%s}' % operand.value,
                formatstring.value
            )
            # Convert to an f-string.
            if not replacement_value.startswith('f'):
                replacement_value = f'f{replacement_value}'  # dogfooding!

            # Finally, replace the formatstring node in the CST, and remove the operator/operand.
            formatstring.value = replacement_value
            node.children[1:] = []

    elif isinstance(operand, Node):
        # string interpolation (old style), where the thing on the right is a tuple
        # In this case, we need to match the arguments with the '%s' bits.
        # TODO
        pass

    # formatstring = leaves[0]
    # if capture['node'].children
    return node


query = (
    # Look for files in the current working directory
    Query(sys.argv[1])

    # try to match:
    # string interpolation (old style), where the thing on the right is a name
    # string interpolation (old style), where the thing on the right is a tuple
    # TODO: .format()
    .select('''
        (
            term< STRING '%' NAME >
        |
            term< STRING '%' atom< '(' (testlist_gexp< any ',' >)* ')' > >
        )
    ''')
    .modify(callback=convert_to_fstrings)
    .diff(interactive=True)
)
