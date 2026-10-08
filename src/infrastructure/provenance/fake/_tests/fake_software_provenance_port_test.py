import unittest

from infrastructure.provenance.fake.fake_software_provenance_port import (
    GIT_UNAVAILABLE,
    FakeSoftwareProvenancePort,
)


class TestFakeSoftwareProvenancePort(unittest.TestCase):
    def test_default_is_a_clean_tree(self):
        provenance = FakeSoftwareProvenancePort().read()
        self.assertIs(provenance.dirty, False)
        self.assertIsNotNone(provenance.commit)

    def test_git_unavailable_has_the_real_failure_shape(self):
        provenance = FakeSoftwareProvenancePort(GIT_UNAVAILABLE).read()
        self.assertIsNone(provenance.commit)
        self.assertIsNone(provenance.dirty)
        self.assertTrue(provenance.unknown_reason)


if __name__ == "__main__":
    unittest.main()
