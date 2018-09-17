#!/usr/bin/env python3
"""
A sample pybowler pipeline that demonstrates replacement of
x-unit style tests with pytest-style ones.

Not particularly thorough.
"""

import argparse
import re
import sys

from fissix.pygram import python_symbols as syms

from bowler import Query, TOKEN, SYMBOL
from bowler.types import Leaf, Node, STARS

flags = {}


OPERATORS = {
    'assertEqual': Leaf(TOKEN.EQEQUAL, '==', prefix=' '),
    'assertEquals': Leaf(TOKEN.EQEQUAL, '==', prefix=' '),
    'failUnlessEqual': Leaf(TOKEN.EQEQUAL, '==', prefix=' '),
    'assertNotEqual': Leaf(TOKEN.NOTEQUAL, '!=', prefix=' '),
    'failIfEqual': Leaf(TOKEN.NOTEQUAL, '!=', prefix=' '),
}
BOOLEAN_VALUES = ('True', 'False')


# TODO : Add this to fissix.fixer_util
def Assert(test, message=None, **kwargs):
    """Build an assertion statement"""
    if not isinstance(test, list):
        test = [test]
    test[0].prefix = ' '
    if message is not None:
        if not isinstance(message, list):
            message = [message]
        message.insert(0, Leaf(TOKEN.COMMA, ','))
        message[1].prefix = ' '

    return Node(
        syms.assert_stmt,
        [Leaf(TOKEN.NAME, 'assert')] + test + (message or []),
        **kwargs
    )


def assertequal_to_assert(node, capture, filename):
    """
    self.assertEqual(foo, bar, msg)
    --> assert foo == bar, msg

    self.assertNotEqual(foo, bar, msg)
    --> assert foo != bar, msg
    """

    if flags['debug']:
        print("Selected expression: ", list(node.children))

    if capture.get('function_def'):
        # Not interested in `def assertEqual`, leave that alone.
        # We only care about *calls*
        return node

    arguments_nodes = capture['function_arguments']
    if not arguments_nodes:
        return node

    # This is wrapped in a list for some reason?
    arguments_node = arguments_nodes[0]

    if arguments_node.type != syms.arglist:
        # self.assertEqual(*args) perhaps. Can't do much with this really.
        return node

    actual_arguments = [
        n
        for n in arguments_node.children
        if n.type != TOKEN.COMMA
    ]
    if len(actual_arguments) not in (2, 3):
        # Not sure what this is. Leave it alone.
        return node

    a, b, *rest = actual_arguments
    message = None
    if rest:
        message = rest[0]
        if message.type == syms.argument:
            # keyword argument (e.g. `msg=abc`)
            message = message.children[2]

    # Figure out the appropriate operator
    function_name = capture['function_name']
    op_token = OPERATORS[function_name.value]

    # Un-multi-line, where a and b are on separate lines
    b = b.clone()
    b.prefix = ' '

    assert_test_nodes = [a.clone(), op_token.clone(), b]

    # Handle some special cases
    if getattr(a, 'value', None) in BOOLEAN_VALUES or getattr(b, 'value', None) in BOOLEAN_VALUES:
        # use `assert a` instead of `assert a == True` etc
        if getattr(a, 'value') in BOOLEAN_VALUES:
            bool_, tok = a, b
        else:
            tok, bool_ = a, b

        # handle negatives and double negatives:
        # assertNotEqual(x, False) --> assert x`
        invert = bool_.value == 'False'
        if op_token.type == TOKEN.NOTEQUAL:
            invert = not invert
        tok = tok.clone()
        tok.prefix = ' '
        if invert:
            assert_test_nodes = [Leaf(TOKEN.NAME, 'not'), tok]
        else:
            assert_test_nodes = [tok]

    elif getattr(a, 'value', None) == 'None' or getattr(b, 'value', None) == 'None':
        # use `assert a is None` instead of `assert a == None` etc
        if getattr(a, 'value') == 'None':
            none_, tok = a, b
        else:
            tok, none_ = a, b

        none_ = none_.clone()
        none_.prefix = ' '

        assert_test_nodes = [tok.clone(), Leaf(TOKEN.NAME, 'is', prefix=' '), none_]
        if op_token.type == TOKEN.NOTEQUAL:
            assert_test_nodes.insert(-1, Leaf(TOKEN.NAME, 'not', prefix=' '))

    # Finally, apply the whole thing
    assertion = Assert(
        assert_test_nodes,
        message.clone() if message else None,
        prefix=node.prefix,
    )

    if flags['debug']:
        print(f"Replacing:\n\t{node}")
        print(f"With: {assertion}")
        print()

    node.replace(assertion)
    return assertion


def main():
    parser = argparse.ArgumentParser(
        description="Converts x-unit style tests to be pytest-style where possible."
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
        '--debug',
        dest='debug',
        default=False,
        action='store_true',
        help="Spit out debugging information"
    )
    parser.add_argument(
        'files',
        nargs='+',
        help="The python source file(s) to operate on."
    )
    args = parser.parse_args()

    # No way to pass this to .modify() callables, so we just set it at module level
    flags['debug'] = args.debug

    query = (
        # Look for files in the current working directory
        Query(*args.files)

        # NOTE: You can append as many .select().modify() bits as you want to one query.
        # Each .modify() acts only on the .select[_*]() immediately prior.

        .select_method('assertEqual').modify(callback=assertequal_to_assert)
        .select_method('assertEquals').modify(callback=assertequal_to_assert)
        .select_method('failUnlessEqual').modify(callback=assertequal_to_assert)

        .select_method('assertNotEqual').modify(callback=assertequal_to_assert)
        .select_method('failIfEqual').modify(callback=assertequal_to_assert)

        # Actually run all of the above.
        .execute(
            # interactive diff implies write (for the bits the user says 'y' to)
            interactive=(args.interactive and args.write),
            write=args.write,
        )
    )


if __name__ == '__main__':
    main()
