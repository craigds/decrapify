#!/usr/bin/env python3
"""
A sample pybowler pipeline that demonstrates replacement of
x-unit style tests with pytest-style ones.

Not particularly thorough.

For simplicity, doesn't really handle boolean/None values well:

    assertEqual(a, None)
        --> a == None
    assertEqual(a, False)
        --> a == False
"""

import argparse
from functools import wraps

from fissix.fixer_util import (
    parenthesize,
    Call,
    Comma,
    Attr,
    KeywordArg,
    ArgList,
    touch_import,
)
from fissix.pygram import python_symbols as syms

from bowler import Query, TOKEN
from bowler.types import Leaf, Node

flags = {}


# NOTE: these don't take inversions into account.
# Hence why assertNotEqual is a synonym of assertEqual
SYNONYMS = {
    "assertEquals": "assertEqual",
    "failUnlessEqual": "assertEqual",
    "assertNotEqual": "assertEqual",
    "failIfEqual": "assertEqual",
    "assertIsNot": "assertIs",
    "assertNotIn": "assertIn",
    "failUnless": "assertTrue",
    "assert_": "assertTrue",
    "assertFalse": "assertTrue",
    "failIf": "assertTrue",
    "assertIsNotNone": "assertIsNone",
    "assertMultiLineEqual": "assertEqual",
    "assertSequenceEqual": "assertEqual",
    "assertListEqual": "assertEqual",
    "assertTupleEqual": "assertEqual",
    "assertSetEqual": "assertEqual",
    "assertDictEqual": "assertEqual",
    "assertNotIsInstance": "assertIsInstance",
    "assertNotAlmostEqual": "assertAlmostEqual",
}


ARGUMENTS = {
    "assertEqual": 2,
    "assertIs": 2,
    "assertIn": 2,
    "assertGreater": 2,
    "assertLess": 2,
    "assertGreaterEqual": 2,
    "assertLessEqual": 2,
    "assertIsInstance": 2,
    # TODO: assertRaises()
    "assertAlmostEqual": 2,
    "assertTrue": 1,
    "assertIsNone": 1,
}


OPERATORS = {
    "assertEqual": Leaf(TOKEN.EQEQUAL, "==", prefix=" "),
    "assertIs": Leaf(TOKEN.NAME, "is", prefix=" "),
    "assertIn": Leaf(TOKEN.NAME, "in", prefix=" "),
    "assertTrue": [],
    "assertIsNone": [
        Leaf(TOKEN.NAME, "is", prefix=" "),
        Leaf(TOKEN.NAME, "None", prefix=" "),
    ],
    "assertGreater": Leaf(TOKEN.GREATER, ">", prefix=" "),
    "assertLess": Leaf(TOKEN.LESS, "<", prefix=" "),
    "assertGreaterEqual": Leaf(TOKEN.GREATEREQUAL, ">=", prefix=" "),
    "assertLessEqual": Leaf(TOKEN.LESSEQUAL, "<=", prefix=" "),
}


# Functions where we invert the operator, or add a 'not'
INVERT_FUNCTIONS = {
    "assertNotEqual",
    "failIfEqual",
    "assertIsNot",
    "assertNotIn",
    "assertFalse",
    "failIf",
    "assertIsNotNone",
    "assertNotIsInstance",
    "assertNotAlmostEqual",
}
BOOLEAN_VALUES = ("True", "False")


def kw(name, **kwargs):
    """
    A helper to produce keyword nodes
    """
    kwargs.setdefault("prefix", " ")
    return Leaf(TOKEN.NAME, name, **kwargs)


# TODO : Add this to fissix.fixer_util
def Assert(test, message=None, **kwargs):
    """Build an assertion statement"""
    if not isinstance(test, list):
        test = [test]
    test[0].prefix = " "
    if message is not None:
        if not isinstance(message, list):
            message = [message]
        message.insert(0, Comma())
        message[1].prefix = " "

    return Node(
        syms.assert_stmt,
        [Leaf(TOKEN.NAME, "assert")] + test + (message or []),
        **kwargs,
    )


def is_multiline(node):
    if isinstance(node, list):
        return any(is_multiline(n) for n in node)

    for leaf in node.leaves():
        if "\n" in leaf.prefix:
            return True
    return False


def parenthesize_if_necessary(node):
    if is_multiline(node):
        # If not already parenthesized, parenthesize
        for first_leaf in node.leaves():
            if first_leaf.type in (TOKEN.LPAR, TOKEN.LBRACE, TOKEN.LSQB):
                # Already parenthesized
                return node
            break
        return parenthesize(node.clone())
    return node


def conversion(func):
    """
    Decorator. Handle some boilerplate
    """

    @wraps(func)
    def wrapper(node, capture, filename):
        if flags["debug"]:
            print("Selected expression: ", list(node.children))

        if capture.get("function_def"):
            # Not interested in `def assertEqual`, leave that alone.
            # We only care about *calls*
            return node

        arguments_nodes = capture["function_arguments"]
        if not arguments_nodes:
            return node

        # This is wrapped in a list for some reason?
        arguments_node = arguments_nodes[0]

        if arguments_node.type == syms.arglist:
            # multiple arguments
            actual_arguments = [
                n for n in arguments_node.children if n.type != TOKEN.COMMA
            ]
        else:
            # one argument
            actual_arguments = [arguments_node]

        # Un-multi-line, where a and b are on separate lines
        actual_arguments = [a.clone() for a in actual_arguments]
        for a in actual_arguments:
            a.prefix = " "

            if flags.get("skip_multiline_expressions"):
                if is_multiline(a):
                    return

        # Avoid creating syntax errors for multi-line nodes
        # (this is overly restrictive, but better than overly lax)
        # https://github.com/facebookincubator/Bowler/issues/12
        actual_arguments = [parenthesize_if_necessary(a) for a in actual_arguments]

        assertion = func(node, capture, actual_arguments)

        if assertion is not None:
            if flags["debug"]:
                print(f"Replacing:\n\t{node}")
                print(f"With: {assertion}")
                print()

            node.replace(assertion)
            return assertion

    return wrapper


@conversion
def assertmethod_to_assert(node, capture, arguments):
    """
    self.assertEqual(foo, bar, msg)
    --> assert foo == bar, msg

    self.assertTrue(foo, msg)
    --> assert foo, msg

    self.assertIsNotNone(foo, msg)
    --> assert foo is not None, msg

    .. etc
    """
    function_name = capture["function_name"].value
    invert = function_name in INVERT_FUNCTIONS
    function_name = SYNONYMS.get(function_name, function_name)
    num_arguments = ARGUMENTS[function_name]

    if len(arguments) not in (num_arguments, num_arguments + 1):
        # Not sure what this is. Leave it alone.
        return None

    if len(arguments) == num_arguments:
        message = None
    else:
        message = arguments.pop()
        if message.type == syms.argument:
            # keyword argument (e.g. `msg=abc`)
            message = message.children[2].clone()

    if function_name == "assertIsInstance":
        arguments[0].prefix = ""
        assert_test_nodes = [
            Call(kw("isinstance"), [arguments[0], Comma(), arguments[1]])
        ]
        if invert:
            assert_test_nodes.insert(0, kw("not"))
    elif function_name == "assertAlmostEqual":
        arguments[1].prefix = ""
        # TODO: insert the `import pytest` at the top of the file
        if invert:
            op_token = Leaf(TOKEN.NOTEQUAL, "!=", prefix=" ")
        else:
            op_token = Leaf(TOKEN.EQEQUAL, "==", prefix=" ")
        assert_test_nodes = [
            Node(
                syms.comparison,
                [
                    arguments[0],
                    op_token,
                    Node(
                        syms.power,
                        Attr(kw("pytest"), kw("approx", prefix=""))
                        + [
                            ArgList(
                                [
                                    arguments[1],
                                    Comma(),
                                    KeywordArg(kw("abs"), Leaf(TOKEN.NUMBER, "1e-7")),
                                ]
                            )
                        ],
                    ),
                ],
            )
        ]
        # Adds a 'import pytest' if there wasn't one already
        touch_import(None, "pytest", node)

    else:
        op_tokens = OPERATORS[function_name]
        if not isinstance(op_tokens, list):
            op_tokens = [op_tokens]
        op_tokens = [o.clone() for o in op_tokens]

        if invert:
            if not op_tokens:
                op_tokens.append(kw("not"))
            elif op_tokens[0].type == TOKEN.NAME and op_tokens[0].value == "is":
                op_tokens[0] = Node(syms.comp_op, [kw("is"), kw("not")], prefix=" ")
            elif op_tokens[0].type == TOKEN.NAME and op_tokens[0].value == "in":
                op_tokens[0] = Node(syms.comp_op, [kw("not"), kw("in")], prefix=" ")
            elif op_tokens[0].type == TOKEN.EQEQUAL:
                op_tokens[0] = Leaf(TOKEN.NOTEQUAL, "!=", prefix=" ")

        if num_arguments == 2:
            # a != b, etc.
            assert_test_nodes = [arguments[0]] + op_tokens + [arguments[1]]
        elif function_name == "assertTrue":
            assert_test_nodes = op_tokens + [arguments[0]]
            # not a
        elif function_name == "assertIsNone":
            # a is not None
            assert_test_nodes = [arguments[0]] + op_tokens

    return Assert(
        assert_test_nodes, message.clone() if message else None, prefix=node.prefix
    )


@conversion
def assertalmostequal_to_assert(node, capture, arguments):
    function_name = capture["function_name"].value
    invert = function_name in INVERT_FUNCTIONS
    function_name = SYNONYMS.get(function_name, function_name)

    nargs = len(arguments)
    if nargs < 2 or nargs > 5:
        return None

    def get_kwarg_value(index, name):
        i = 0
        for a in arguments:
            if a.type == syms.argument:
                if a.children[0].value == name:
                    return a.children[2].clone()
            else:
                if i == index:
                    return a.clone()
                i += 1
        return None

    first = get_kwarg_value(0, "first")
    second = get_kwarg_value(1, "second")

    if first is None or second is None:
        # Not sure what this is, leave it alone
        return

    places = get_kwarg_value(2, "places")
    msg = get_kwarg_value(3, "msg")
    delta = get_kwarg_value(4, "delta")

    if delta is not None:
        try:
            abs_delta = float(delta.value)
        except ValueError:
            # this should be a number, give up.
            return
    else:
        if places is None:
            places = 7
        else:
            try:
                places = int(places.value)
            except (ValueError, AttributeError):
                # this should be an int, give up.
                return
        abs_delta = "1e-%d" % places

    arguments[1].prefix = ""
    if invert:
        op_token = Leaf(TOKEN.NOTEQUAL, "!=", prefix=" ")
    else:
        op_token = Leaf(TOKEN.EQEQUAL, "==", prefix=" ")
    assert_test_nodes = [
        Node(
            syms.comparison,
            [
                arguments[0],
                op_token,
                Node(
                    syms.power,
                    Attr(kw("pytest"), kw("approx", prefix=""))
                    + [
                        ArgList(
                            [
                                arguments[1],
                                Comma(),
                                KeywordArg(kw("abs"), Leaf(TOKEN.NUMBER, abs_delta)),
                            ]
                        )
                    ],
                ),
            ],
        )
    ]
    # Adds a 'import pytest' if there wasn't one already
    touch_import(None, "pytest", node)

    return Assert(assert_test_nodes, msg.clone() if msg else None, prefix=node.prefix)


def main():
    parser = argparse.ArgumentParser(
        description="Converts x-unit style tests to be pytest-style where possible."
    )
    parser.add_argument(
        "--no-input",
        dest="interactive",
        default=True,
        action="store_false",
        help="Non-interactive mode",
    )
    parser.add_argument(
        "--no-write",
        dest="write",
        default=True,
        action="store_false",
        help="Don't write the changes to the source file, just output a diff to stdout",
    )
    parser.add_argument(
        "--debug",
        dest="debug",
        default=False,
        action="store_true",
        help="Spit out debugging information",
    )
    parser.add_argument(
        "--skip-multiline-expressions",
        default=False,
        action="store_true",
        help=(
            "Skip handling lines that contain multiline expressions. "
            "The code isn't yet able to handle them well. Output is valid but not pretty"
        ),
    )
    parser.add_argument(
        "files", nargs="+", help="The python source file(s) to operate on."
    )
    args = parser.parse_args()

    # No way to pass this to .modify() callables, so we just set it at module level
    flags["debug"] = args.debug
    flags["skip_multiline_expressions"] = args.skip_multiline_expressions

    query = (
        # Look for files in the current working directory
        Query(*args.files)
        # NOTE: You can append as many .select().modify() bits as you want to one query.
        # Each .modify() acts only on the .select[_*]() immediately prior.
        .select_method("assertEqual")
        .modify(callback=assertmethod_to_assert)
        .select_method("assertEquals")
        .modify(callback=assertmethod_to_assert)
        .select_method("failUnlessEqual")
        .modify(callback=assertmethod_to_assert)
        .select_method("assertNotEqual")
        .modify(callback=assertmethod_to_assert)
        .select_method("failIfEqual")
        .modify(callback=assertmethod_to_assert)
        .select_method("assertIs")
        .modify(callback=assertmethod_to_assert)
        .select_method("assertIsNot")
        .modify(callback=assertmethod_to_assert)
        .select_method("assertIn")
        .modify(callback=assertmethod_to_assert)
        .select_method("assertNotIn")
        .modify(callback=assertmethod_to_assert)
        .select_method("assertTrue")
        .modify(callback=assertmethod_to_assert)
        .select_method("assert_")
        .modify(callback=assertmethod_to_assert)
        .select_method("failUnless")
        .modify(callback=assertmethod_to_assert)
        .select_method("assertFalse")
        .modify(callback=assertmethod_to_assert)
        .select_method("failIf")
        .modify(callback=assertmethod_to_assert)
        .select_method("assertIsNone")
        .modify(callback=assertmethod_to_assert)
        .select_method("assertIsNotNone")
        .modify(callback=assertmethod_to_assert)
        .select_method("assertGreater")
        .modify(callback=assertmethod_to_assert)
        .select_method("assertGreaterEqual")
        .modify(callback=assertmethod_to_assert)
        .select_method("assertLess")
        .modify(callback=assertmethod_to_assert)
        .select_method("assertLessEqual")
        .modify(callback=assertmethod_to_assert)
        .select_method("assertIsInstance")
        .modify(callback=assertmethod_to_assert)
        .select_method("assertNotIsInstance")
        .modify(callback=assertmethod_to_assert)
        .select_method("assertAlmostEqual")
        .modify(callback=assertalmostequal_to_assert)
        .select_method("assertNotAlmostEqual")
        .modify(callback=assertalmostequal_to_assert)
        # Actually run all of the above.
        .execute(
            # interactive diff implies write (for the bits the user says 'y' to)
            interactive=(args.interactive and args.write),
            write=args.write,
        )
    )


if __name__ == "__main__":
    main()
