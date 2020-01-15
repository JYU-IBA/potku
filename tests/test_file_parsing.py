
"""
TODO add license etc
"""

import unittest

from modules import file_parsing as fp


class TestFileParsing(unittest.TestCase):
    def test_parse_strs(self):
        """Tests for parsing multiple strings"""
        self.assertEqual((), fp.parse_strs([], [], []))
        self.assertEqual((["foo"],), fp.parse_strs(["foo"], [0], [str]))
        self.assertEqual((["foo"], ["bar"]), fp.parse_strs(["foo bar"], [0, 1],
                                                           [str, str]))
        self.assertEqual((["foo", "foo"], ["bar", "baz"]),
                         fp.parse_strs(
                             ["foo bar", "foo  baz"], [0, 1], [str, str]))

    def test_parse_str(self):
        """Tests for parsing single string"""
        self.assertEqual((), fp.parse_str("", [], []))
        self.assertEqual((), fp.parse_str("foo", [], []))
        self.assertEqual(("foo",), fp.parse_str("foo", [0], [str]))

        # Column index must be within the column range and number of indexes
        # must match the number of converters
        self.assertRaises(IndexError,
                          lambda: fp.parse_str("foo", [1], [str]))
        self.assertRaises(ValueError,
                          lambda: fp.parse_str("foo", [0], []))

        # Conversion test
        self.assertEqual(("bar",),
                         fp.parse_str("foo", [0],
                                      [lambda x: "bar" if x == "foo" else x]))

        # By default, parse_str will split strings into a list of
        # non-whitespace characters
        self.assertEqual(
            (1, 2, 4.5, "foo"),
            fp.parse_str("    1 \n  2   3 4.5   foo  ",
                         [0, 1, 3, 4],
                         [int, int, float, str])
        )

        # Caller can also define a custom separator
        self.assertEqual(
            (1, 2, 4.5, "foo"),
            fp.parse_str("1,2,3,4.5,foo,",
                         [0, 1, 3, 4],
                         [int, int, float, str],
                         separator=",")
        )

        # Same column can be parsed multiple times
        self.assertEqual(
            (1, "1", True), fp.parse_str("1", [0, 0, 0], [int, str, bool])
        )



if __name__ == "__main__":
    unittest.main()