"""Static safety assertions for GitHub Actions workflows.

Hosted fork isolation, workflow_run emission, and privilege boundaries must be
observed independently; these tests validate the reviewed configuration only.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class WorkflowSafetyTests(unittest.TestCase):
    def test_contributor_ci_is_read_only(self):
        text = (ROOT / '.github/workflows/ci.yml').read_text()
        self.assertIn('pull_request:', text)
        self.assertIn('contents: read', text)
        self.assertIn('persist-credentials: false', text)
        self.assertNotIn('contents: write', text)
        self.assertNotIn('pull_request_target', text)
        self.assertNotIn('secrets.', text)

    def test_publisher_only_runs_trusted_default_branch_code(self):
        text = (ROOT / '.github/workflows/publish.yml').read_text()
        self.assertIn('workflows: [Contributor CI]', text)
        self.assertIn('types: [completed]', text)
        self.assertIn("github.event.workflow_run.event == 'pull_request'", text)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", text)
        self.assertIn("github.ref == 'refs/heads/main'", text)
        self.assertIn('ref: ${{ github.event.repository.default_branch }}', text)
        self.assertNotIn('github.event.workflow_run.head_sha', text)
        self.assertNotIn('download-artifact', text)

    def test_remote_lookup_never_conflates_failure_with_absence(self):
        text = (ROOT / '.github/workflows/publish.yml').read_text()
        self.assertIn('case "$lookup" in', text)
        self.assertIn('            2)', text)
        self.assertIn('            *)', text)
        self.assertIn('exit "$lookup"', text)

if __name__ == '__main__':
    unittest.main()