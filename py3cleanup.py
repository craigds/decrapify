#!/usr/bin/env python3
"""
Removes some leftover mess from a transition to python 3.
"""

import argparse
from fissix.pygram import python_symbols as syms

from bowler import Query, TOKEN
from bowler.types import Leaf

flags = {}


def kw(name, **kwargs):
    """
    A helper to produce keyword nodes
    """
    kwargs.setdefault('prefix', ' ')
    return Leaf(TOKEN.NAME, name, **kwargs)


def remove_super_args(node, capture, arguments):
    super_classname = capture['classname'].value

    classdef = node
    while classdef.type != syms.classdef:
        classdef = classdef.parent

    actual_classname = classdef.children[1].value

    if actual_classname != super_classname:
        return

    capture['arglist'].remove()


def remove_explicit_object_superclass(node, capture, arguments):
    param = capture['param'][0]
    if param.type == TOKEN.NAME:
        # 'object'
        capture['lpar'].remove()
        param.remove()
        capture['rpar'].remove()
    elif param.type == syms.arglist:
        kwarg = capture['kwarg'].clone()
        kwarg.prefix = param.prefix
        param.replace(kwarg)


def main():
    parser = argparse.ArgumentParser(
        description="Removes artifacts from a transition to python 3."
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
        # super(MyClassName, self) --> super()
        # (where MyClassName is the type of self)
        .select(
            """
            power<
                "super"
                trailer<
                    "("
                    arglist=arglist<
                        classname=NAME "," "self"
                    >
                    ")"
                >
                any*
            >
            """
        )
        .modify(callback=remove_super_args)
        # class X(object): --> class X:
        .select(
            """
            classdef<
                "class" NAME lpar="("
                    param=(
                        "object" 
                        | arglist<
                            "object" ","
                            kwarg=argument
                        >
                    )
                rpar=")" ":" suite
            >
            """
        )
        .modify(callback=remove_explicit_object_superclass)
        # Actually run all of the above.
        .execute(
            # interactive diff implies write (for the bits the user says 'y' to)
            interactive=(args.interactive and args.write),
            write=args.write,
        )
    )


if __name__ == '__main__':
    main()
