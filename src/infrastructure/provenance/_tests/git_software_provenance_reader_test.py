import subprocess
import unittest

from infrastructure.provenance.git_software_provenance_reader import GitSoftwareProvenanceReader

ANSWERS = {
    ("rev-parse", "HEAD"): "71d88feabeb8341267fdaa52617f4027e41eec66",
    ("rev-parse", "--abbrev-ref", "HEAD"): "develop",
    ("status", "--porcelain"): "",
}


def git(answers):
    def run(args):
        answer = answers[tuple(args)]
        if isinstance(answer, Exception):
            raise answer
        return answer

    return run


class TestGitSoftwareProvenanceReader(unittest.TestCase):
    def test_clean_tree(self):
        provenance = GitSoftwareProvenanceReader(run_git=git(ANSWERS), read_version=lambda: "0.1.0").read()
        self.assertEqual(provenance.commit, ANSWERS[("rev-parse", "HEAD")])
        self.assertEqual(provenance.branch, "develop")
        self.assertIs(provenance.dirty, False)
        self.assertEqual(provenance.version, "0.1.0")
        self.assertIsNone(provenance.unknown_reason)

    def test_modified_tree_is_dirty(self):
        answers = {**ANSWERS, ("status", "--porcelain"): " M src/main.py"}
        self.assertIs(GitSoftwareProvenanceReader(run_git=git(answers), read_version=lambda: None).read().dirty, True)

    def test_git_unavailable_is_unknown_not_an_exception(self):
        answers = {key: FileNotFoundError("git") for key in ANSWERS}
        provenance = GitSoftwareProvenanceReader(run_git=git(answers), read_version=lambda: None).read()
        self.assertIsNone(provenance.commit)
        self.assertIsNone(provenance.dirty)
        self.assertIn("FileNotFoundError", provenance.unknown_reason)

    def test_timeout_is_unknown(self):
        answers = {**ANSWERS, ("status", "--porcelain"): subprocess.TimeoutExpired("git", 5)}
        provenance = GitSoftwareProvenanceReader(run_git=git(answers), read_version=lambda: None).read()
        self.assertIsNone(provenance.dirty)
        self.assertIsNotNone(provenance.commit)

    def test_reads_this_repository(self):
        """The real git and pyproject of this checkout: never raises."""
        provenance = GitSoftwareProvenanceReader().read()
        self.assertEqual(provenance.name, "AEFI Acquisition")
        self.assertEqual(provenance.version, "0.1.0")


if __name__ == "__main__":
    unittest.main()
