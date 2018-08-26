#!/usr/bin/env python3
"""
A sample pybowler pipeline that demonstrates replacement of
various types of string-interpolation with f-strings.

Implemented:
    * 'stringliteral %s' % name
        --> f'stringliteral {name}'

    * 'stringliteral %s %d' % (foo, bar)
        --> f'stringliteral {foo} {bar}'

    * 'stringliteral {} {bar}'.format(foo, bar=bar)
        --> f'stringliteral {foo} {bar}'

TODO: plenty:
    * Handle other printf-style things other than %s/%d/%f, e.g. '%20d' etc.
    * Same for .format() - handle '!20d' etc
    * Handle old-style dict interpolation, e.g. '%(a)s' % {'a': 'a'}
"""

import argparse
import re
import sys

from bowler import Query, TOKEN, SYMBOL
from bowler.types import Leaf, Node, STARS

flags = {}


RE_OLD_INTERPOLATION_BASIC = re.compile(r'(?<!%)%[fds]')

# TODO: currently excludes modifiers like `{!d}`
# TODO/FIXME: what's the syntax for a negative lookahead? Need to avoid matching '}}' escape.
# No 're' docs on my flight :(
RE_NEW_INTERPOLATION_BASIC = re.compile(r'(?<!{)\{[^{}!]*\}')


def old_interpolation_to_fstrings(node, capture, filename):
    """
    '%s' % xyz
        --> f'{xyz}'
    """
    formatstring = capture['formatstring']
    interpolation_args = capture['interpolation_args']
    if isinstance(interpolation_args, Leaf):
        # string interpolation (old style), where the thing on the right is a name.
        # e.g. `'foo %s' % bar
        interpolation_args = [interpolation_args.value]
    elif isinstance(interpolation_args, list):
        # string interpolation (old style), where the thing on the right is a tuple.
        # e.g. `'foo %s %s' % (bar, baz)
        # first, find the 'bar' and 'baz' bits:
        interpolation_args = [
            o.value
            for o in interpolation_args
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

    if flags['debug']:
        print(f"Interpolating (old-style) format-string:\n\t{formatstring}")
        print(f"With arguments:\n\t{interpolation_args}")
        print(f"Replacement formatstring: {replacement_value}")
        print()

    # Make sure we consumed all the arguments, otherwise something went wrong.
    assert not interpolation_args

    # Convert to an f-string.
    if not replacement_value.startswith('f'):
        replacement_value = f'f{replacement_value}'  # dogfooding!

    # Finally, replace the formatstring node in the CST, and remove the operator & operand.
    formatstring.value = replacement_value
    node.children[1:] = []

    return node


def _interpret_format_arguments(arg):
    """
    Recursive generator.

    Given a single name, an argument, an arglist or a vararg expression,
    returns actual argument values, in order.

    Yields one of:
        positional args: yields the arg value
        keyword args: yields a dict {k: v}
        other (complex nested structures or varargs): yields None.
    )
    """
    if isinstance(arg, Leaf) and arg.type == TOKEN.COMMA:
        # Skip comma tokens between actual args
        return

    if isinstance(arg, list):
        # Handle top-level list of args. Also handles there being no args at all: .format()
        for sub_arg in arg:
            yield from _interpret_format_arguments(sub_arg)
        return

    if isinstance(arg, Node) and arg.type == SYMBOL.arglist:
        # Multiple arguments, may be either keyword or positional
        for child in arg.children:
            yield from _interpret_format_arguments(child)
        return

    if isinstance(arg, Node) and arg.type == SYMBOL.argument:
        if arg.children[0].type in STARS:
            # *args, or **kwargs.
            # Not useful for f-stringing. Give up.
            yield None
            return

        # Single keyword argument: .format(keyword=value)
        # The three child nodes here are (keyword, '=', value).
        value = arg.children[2]
        if not isinstance(value, Leaf):
            # Might be complex? Give up. This stops parsing of the entire expression,
            # beacuse having an f-string *and* a .format() is pretty nasty.
            yield None
        else:
            yield {
                arg.children[0].value: value.value
            }
    elif isinstance(arg, Leaf) and arg.type == TOKEN.NAME:
        # Single positional argument, which is just a name.
        yield arg.value
    else:
        # Something else.
        # Might be a complex expression? Give up. This stops parsing of the entire expression,
        # because having an f-string *and* a .format() is pretty nasty.
        yield None


def format_method_to_fstrings(node, capture, filename):
    """
    '{}'.format(xyz)
        --> f'{xyz}'
    """

    if flags['debug']:
        print("Selected expression: ", list(node.children))

    formatstring = capture['formatstring']
    interpolation_args = capture['interpolation_args']

    # We only convert .format() stuff to an f-string if the arguments are all simple-ish.
    # That means:
    #  * name-only: `abc`

    positional_args = []
    keyword_args = {
        # Maps kwarg names (strings) to the kwarg *value*
        # e.g. for .format(a=b) this would be {'a': 'b'}
    }
    for parsed_arg in _interpret_format_arguments(interpolation_args):
        if parsed_arg is None:
            # This arg was deemed too complex to bother pushing into an f-string.
            # Give up.
            return node
        elif isinstance(parsed_arg, dict):
            keyword_args.update(parsed_arg)
        else:
            positional_args.append(parsed_arg)

    # Actually push the new names into a new formatstring. Wrap each value with curly braces.
    replacement = formatstring.value.format(
        *['{%s}' % a for a in positional_args],
        **{k: '{%s}' % v for (k, v) in keyword_args.items()}
    )
    if flags['debug']:
        print(f"Interpolating (new-style) format-string:\n\t{formatstring}")
        print(f"With arguments:\n\t{positional_args}, {keyword_args}")
        print(f"Replacement formatstring: {replacement}")
        print()

    # Finally, apply the whole thing
    formatstring.value = replacement
    capture['trailer1'].remove()
    capture['trailer2'].remove()
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

    # TODO: merge these two queries, once I figure out how.
    # https://github.com/facebookincubator/Bowler/issues/1
    query = (
        # Look for files in the current working directory
        Query(*args.files)

        # NOTE: You can append as many .select().modify() bits as you want to one query.
        # Each .modify() acts only on the .select[_*]() immediately prior.

        # 1. String interpolation (old style):
        # ... where the thing on the right is a variable name
        # ... where the thing on the right is a tuple of variable names.
        .select('''
            (
                term<
                    formatstring=STRING '%' interpolation_args=NAME >
            |
                term< formatstring=STRING '%' atom< '('
                    (testlist_gexp< interpolation_args=((NAME ',')* NAME [',']) >)
                ')' > >
            )
        ''')
        .modify(callback=old_interpolation_to_fstrings)
        .execute(
            # interactive diff implies write (for the bits the user says 'y' to)
            interactive=(args.interactive and args.write),
            write=args.write,
        )
    )
    (
        Query(*args.files)

        # 2. New-style interpolation (.format(...))
        # The 'power<>' thing is confusing to me. What's 'power' mean in this context?
        # NOTE: this selector is quite loose; it accepts 'any*' in the arguments to format().
        # i.e. this happily accepts: ''.format(a, 2, b=3, c=d[e], *x, **y)
        # We'll need to be careful handling each of these in the modify callback,
        # since not all of those args make much sense shoved into an fstring.
        .select('''
            function_call=power<
                formatstring=STRING
                trailer1=trailer<
                    '.' 'format'
                >
                trailer2=trailer< '(' interpolation_args=any* ')' >
                any*
            >
        ''')
        .modify(callback=format_method_to_fstrings)

        .execute(
            # interactive diff implies write (for the bits the user says 'y' to)
            interactive=(args.interactive and args.write),
            write=args.write,
        )
    )


if __name__ == '__main__':
    main()
