import unittest

from version_utils import versions_match


class VersionUtilsTests(unittest.TestCase):
    def test_matches_tags_with_or_without_v_prefix(self):
        self.assertTrue(versions_match("v1.0.8.2", "1.0.8.2"))

    def test_does_not_match_different_versions(self):
        self.assertFalse(versions_match("v1.0.8.2", "v1.0.8.1"))

    def test_ignores_surrounding_whitespace_and_prefix_case(self):
        self.assertTrue(versions_match(" V1.0.8.2 ", "1.0.8.2"))


if __name__ == "__main__":
    unittest.main()
