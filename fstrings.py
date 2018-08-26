#!/usr/bin/env python3
"""
A sample pybowler pipeline that demonstrates replacement of
various types of string-interpolation with f-strings.

Implemented:
    * 'stringliteral %s' % name
        --> f'stringliteral {name}'

    * 'stringliteral %s %d' % (foo, bar)
        --> f'stringliteral {foo} {bar}'

TODO: plenty:
    * Handle other printf-style things other than %s/%d/%f, e.g. '%20d' etc.
    * Handle .format(), with both args and kwargs
"""

import argparse
import re
import sys

from bowler import Query, TOKEN
from bowler.types import Leaf, Node


RE_OLD_INTERPOLATION_BASIC = re.compile(r'(?<!%)%[fds]')


def convert_to_fstrings(node, capture, filename):
    print("Selected expression: ", list(node.children))

    formatstring = node.children[0]
    operand = node.children[2]
    if isinstance(operand, Leaf) and operand.type == TOKEN.NAME:
        # string interpolation (old style), where the thing on the right is a name.
        # e.g. `'foo %s' % bar
        interpolation_args = [operand.value]
    elif isinstance(operand, Node):
        # string interpolation (old style), where the thing on the right is a tuple.
        # e.g. `'foo %s %s' % (bar, baz)
        # first, find the 'bar' and 'baz' bits:
        interpolation_args = [
            o.value
            for o in operand.children[1].children
            if isinstance(o, Leaf) and o.type == TOKEN.NAME
        ]

    if len(RE_OLD_INTERPOLATION_BASIC.findall(formatstring.value)) != len(interpolation_args):
        # TODO: The arguments don't line up 1:1 with the number of '%s' bits.
        # This could be a bug in the program.
        # More likely, it's because our regex isn't that inclusive.
        # e.g. if one of them is '%.20f' we'll miss that one and skip the whole expression.
        # We could implement this, by using f'{foo!.20f}' for that case.
        return node

    # Replace all occurrences of '%s' in the formatstring with the matching '{argumentname}'
    replacement_value = RE_OLD_INTERPOLATION_BASIC.sub(
        lambda matchobj: ('{%s}' % interpolation_args.pop(0)),
        formatstring.value,
    )
    # Make sure we consumed all the arguments, otherwise something went wrong.
    assert not interpolation_args

    # Convert to an f-string.
    if not replacement_value.startswith('f'):
        replacement_value = f'f{replacement_value}'  # dogfooding!

    # Finally, replace the formatstring node in the CST, and remove the operator & operand.
    formatstring.value = replacement_value
    node.children[1:] = []

    return node


def main():
    parser = argparse.ArgumentParser(
        description="Converts string interpolation expressions to use f-strings where possible."
    )
    parser.add_argument(
        '--no-input',
        dest='interactive',
        default=True,
        action='store_false',
        help="Non-interactive mode"
    )
    parser.add_argument(
        '--no-write',
        dest='write',
        default=True,
        action='store_false',
        help="Don't write the changes to the source file, just output a diff to stdout"
    )
    parser.add_argument(
        'files',
        nargs='+',
        help="The python source file(s) to operate on."
    )
    args = parser.parse_args()

    query = (
        # Look for files in the current working directory
        Query(*args.files)

        # try to match:
        # string interpolation (old style), where the thing on the right is a name
        # string interpolation (old style), where the thing on the right is a tuple
        # TODO: .format()
        .select('''
            (
                term< STRING '%' NAME >
            |
                term< STRING '%' atom< '(' (testlist_gexp< (NAME ',')* NAME [','] >) ')' > >
            )
        ''')
        .modify(callback=convert_to_fstrings)
        .execute(
            # interactive diff implies write (for the bits the user says 'y' to)
            interactive=(args.interactive and args.write),
            write=args.write,
        )
    )


if __name__ == '__main__':
    main()
