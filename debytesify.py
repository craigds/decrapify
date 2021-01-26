#!/usr/bin/env python3
"""
Removes bytestring literals. Be careful with this!
"""

import argparse

from bowler import Query, TOKEN
from bowler.types import Leaf

flags = {}


def debytesify(node, capture, arguments):
    i = 0
    for i, char in enumerate(node.value):
        if char in ('"', "'"):
            return
        elif char == 'b':
            break

    value = node.value[:i] + node.value[i + 1 :]
    new_node = Leaf(TOKEN.STRING, value, prefix=node.prefix)
    node.replace(new_node)


def main():
    parser = argparse.ArgumentParser(
        description="Removes bytestring literals. Be careful with this!"
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
            STRING
            """
        )
        .modify(callback=debytesify)
        # Actually run all of the above.
        .execute(
            # interactive diff implies write (for the bits the user says 'y' to)
            interactive=(args.interactive and args.write),
            write=args.write,
        )
    )


if __name__ == '__main__':
    main()
