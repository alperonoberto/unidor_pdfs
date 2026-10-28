import unittest

from unidor_pdfs.version_utils import is_newer_version, versions_match


class VersionUtilsTests(unittest.TestCase):
    def test_matches_tags_with_or_without_v_prefix(self):
        self.assertTrue(versions_match("v1.0.8.2", "1.0.8.2"))

    def test_does_not_match_different_versions(self):
        self.assertFalse(versions_match("v1.0.8.2", "v1.0.8.1"))

    def test_ignores_surrounding_whitespace_and_prefix_case(self):
        self.assertTrue(versions_match(" V1.0.8.2 ", "1.0.8.2"))

    def test_detects_newer_version(self):
        self.assertTrue(is_newer_version("v1.0.9", "v1.0.8.2"))

    def test_stable_release_is_newer_than_same_prerelease(self):
        self.assertTrue(is_newer_version("v1.0.9", "v1.0.9-beta"))
        self.assertFalse(is_newer_version("v1.0.9-beta", "v1.0.9"))

    def test_does_not_offer_same_or_older_version(self):
        self.assertFalse(is_newer_version("v1.0.8.2", "1.0.8.2"))
        self.assertFalse(is_newer_version("v1.0.8.1", "v1.0.8.2"))

    def test_treats_trailing_zero_components_as_equivalent(self):
        self.assertFalse(is_newer_version("v1.0.0", "1.0"))

    def test_rejects_non_numeric_versions(self):
        with self.assertRaises(ValueError):
            is_newer_version("latest", "v1.0.0")


if __name__ == "__main__":
    unittest.main()
