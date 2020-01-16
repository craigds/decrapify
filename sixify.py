#!/usr/bin/env python3
"""
Adds some py2&3 compatibility that modernize/futurize missed
"""

import argparse
from fissix.pygram import python_symbols as syms
from fissix.fixer_util import Name, Dot, Newline, touch_import, find_binding

from bowler import Query, TOKEN
from bowler.types import Leaf, Node

flags = {}


def replace_unicode_methods(node, capture, arguments):

    # remove any existing __str__ method
    b = find_binding("__str__", capture['suite'])
    if b and b.type == syms.funcdef:
        b.remove()

    # rename __unicode__ to __str__
    funcname = capture['funcname'].clone()
    funcname.value = '__str__'
    capture['funcname'].replace(funcname)

    # Add a six import
    touch_import(None, "six", node)

    # Decorate the class with `@six.python_2_unicode_compatible`
    classdef = node.clone()
    classdef.prefix = ''
    decorated = Node(
        syms.decorated,
        [
            Node(
                syms.decorator,
                [
                    Leaf(TOKEN.AT, '@', prefix=node.prefix),
                    Node(
                        syms.dotted_name,
                        [Name('six'), Dot(), Name('python_2_unicode_compatible')],
                    ),
                    Newline(),
                ],
                prefix=node.prefix,
            ),
            classdef,
        ],
        prefix=node.prefix,
    )
    node.replace(decorated)


def main():
    parser = argparse.ArgumentParser(
        description="Adds some py2&3 compatibility that modernize/futurize missed"
    )
    parser.add_argument(
        '--no-input',
        dest='interactive',
        default=True,
        action='store_false',
        help="Non-interactive mode",
    )
    parser.add_argument(
        '--no-write',
        dest='write',
        default=True,
        action='store_false',
        help="Don't write the changes to the source file, just output a diff to stdout",
    )
    parser.add_argument(
        '--debug',
        dest='debug',
        default=False,
        action='store_true',
        help="Spit out debugging information",
    )
    parser.add_argument(
        'files', nargs='+', help="The python source file(s) to operate on."
    )
    args = parser.parse_args()

    # No way to pass this to .modify() callables, so we just set it at module level
    flags['debug'] = args.debug

    (
        # Look for files in the current working directory
        Query(*args.files)
        .select(
            """
            classdef<
                "class" classname=NAME any* ":"
                suite=suite<
                    any*
                    func=funcdef< "def" funcname="__unicode__" parameters< "(" NAME ")" > any*  >
                    any*
                >
            >
            """
        )
        .modify(callback=replace_unicode_methods)
        # Actually run all of the above.
        .execute(
            # interactive diff implies write (for the bits the user says 'y' to)
            interactive=(args.interactive and args.write),
            write=args.write,
        )
    )


if __name__ == '__main__':
    main()
