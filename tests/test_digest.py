import json
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock

from digest import capture, reconcile, feed_for, windows, publish, configuration, encoded

REPO = 'example-org/project-board'
CONFIG = {
    'repository': REPO, 'timezone': 'America/Denver', 'reader_times': ['09:00', '15:00'],
    'publisher_lead_minutes': 23, 'overlap_minutes': 60,
    'labels': {'area:engineering': 'Engineering'}, 'default_area': 'General',
    'max_feed_bytes': 16000, 'state_branch': 'digest-state'
}
T0 = '2026-11-18T15:00:00+00:00'
T1 = '2026-11-18T21:38:00+00:00'


def issue(**kw):
    return {'id': 101, 'number': 1, 'title': 'Synthetic issue', 'body': 'Fictional text',
            'state': 'open', 'labels': [{'name': 'area:engineering'}],
            'assignees': [{'login': 'example-reviewer'}], 'updated_at': T0,
            'html_url': f'https://github.com/{REPO}/issues/1', **kw}


def mock_read(issues, comments=None, reviews=None, inline=None):
    def reader(repo, endpoint):
        if endpoint == 'issues?state=all':
            return issues
        if endpoint.startswith('issues/comments'):
            return comments or []
        if endpoint.startswith('pulls/') and endpoint.endswith('/reviews'):
            return reviews or []
        if endpoint.startswith('pulls/') and endpoint.endswith('/comments'):
            return inline or []
        raise AssertionError(endpoint)
    return reader


class PublisherTests(unittest.TestCase):
    def test_baseline_quiet_repeat_and_assignment_regression(self):
        first = capture(REPO, CONFIG, mock_read([issue()]))
        seed = reconcile({}, first, T0)
        self.assertEqual(seed['sequence'], 0)
        again = reconcile(seed, capture(REPO, CONFIG, mock_read([issue()])), T1)
        self.assertEqual(again['updates'], [])
        changed = capture(REPO, CONFIG, mock_read([issue(assignees=[{'login': 'example-new-reviewer'}])]))
        result = reconcile(again, changed, T1)
        self.assertEqual(result['updates'][0]['key'], 'issue:101')
        self.assertNotIn('Fictional text', json.dumps(result))

    def test_comment_edit_and_closure(self):
        original = issue()
        c = {'id': 201, 'body': 'Synthetic text', 'issue_url': 'https://api.github.com/issues/1',
             'html_url': f'https://github.com/{REPO}/issues/1#issuecomment-201', 'updated_at': T1}
        seed = reconcile({}, capture(REPO, CONFIG, mock_read([original])), T0)
        state = reconcile(seed, capture(REPO, CONFIG, mock_read([original], [c])), T1)
        self.assertEqual(state['updates'][0]['change'], 'new')
        c['body'] = 'Edited synthetic text'
        original['state'] = 'closed'
        new = reconcile(state, capture(REPO, CONFIG, mock_read([original], [c])), T1)
        self.assertEqual({x['key'] for x in new['updates'][1:]}, {'issue:101', 'comment:201'})
        self.assertNotIn('Edited synthetic text', json.dumps(new))

    def test_pr_head_and_review_revision(self):
        row = issue(pull_request={})
        pr = {'head': {'sha': 'abc123'}, 'merged_at': None, 'draft': False, 'base': {'ref': 'main'}}
        rev = {'id': 88, 'state': 'APPROVED', 'body': 'Synthetic approval', 'commit_id': 'abc123',
               'submitted_at': T1, 'html_url': f'https://github.com/{REPO}/pull/1#pullrequestreview-88'}
        current = capture(REPO, CONFIG, mock_read([row], reviews=[rev]), lambda *_: pr)
        seed = reconcile({}, capture(REPO, CONFIG, mock_read([row]), lambda *_: pr), T0)
        result = reconcile(seed, current, T1)
        self.assertEqual(result['updates'][0]['reviewed_sha'], 'abc123')
        self.assertEqual(result['updates'][0]['review_state'], 'APPROVED')

    def test_window_local_time_dst_and_lead(self):
        state = {'checked_at': '2026-03-08T14:38:00+00:00', 'coverage_started_at': '2026-03-07T00:00:00+00:00'}
        before, morning = windows(state, [], None, CONFIG)
        self.assertEqual(before['slot'], '2026-03-07T22:00:00+00:00')
        self.assertEqual(morning['slot'], '2026-03-08T15:00:00+00:00')
        self.assertTrue(morning['fresh'])
        state['checked_at'] = '2026-03-08T14:36:59+00:00'
        self.assertFalse(windows(state, [], None, CONFIG)[1]['fresh'])

    def test_overlap_and_partial(self):
        state = {'checked_at': T1, 'coverage_started_at': '2026-11-18T16:00:00+00:00'}
        entries = [{'sequence': 8, 'observed_at': '2026-11-18T20:00:00+00:00'},
                   {'sequence': 9, 'observed_at': '2026-11-18T21:00:00+00:00'}]
        result = windows(state, entries, '2026-11-18T19:00:00+00:00', CONFIG)
        self.assertEqual(result[0]['limits'], ['baseline', 'retention'])
        self.assertEqual(result[1]['first_sequence'], 8)
        self.assertEqual(result[1]['last_sequence'], 9)

    def test_budget_and_explicit_gap(self):
        state = {'checked_at': T1, 'coverage_started_at': T0, 'sequence': 100,
                 'dropped_through_at': None, 'updates': [
                     {'sequence': n, 'observed_at': T1, 'title': 'Fictional event '+ ('é' * 160)}
                     for n in range(1, 101)]}
        feed = feed_for(REPO, state, CONFIG)
        self.assertLessEqual(len(encoded(feed)), 16000)
        self.assertGreater(feed['oldest_sequence'], 1)
        self.assertIn('retention', feed['windows'][1]['limits'])

    def test_failed_api_keeps_state_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            d = Path(temp)
            (d / 'cursor.json').write_text('{}')
            (d / 'inbox.json').write_text('{}')
            def broken(*_):
                raise RuntimeError('synthetic API failure')
            with self.assertRaises(RuntimeError):
                publish(REPO, d, CONFIG, broken)
            self.assertEqual((d / 'cursor.json').read_text(), '{}')
            self.assertEqual((d / 'inbox.json').read_text(), '{}')

    def test_fictional_fixture(self):
        fixture = json.loads((Path(__file__).resolve().parents[1] / 'fixtures/example-issues.json').read_text())
        result = capture(REPO, CONFIG, mock_read(fixture['issues'], fixture['comments']))
        self.assertEqual(len(result), 2)
        self.assertNotIn('Fictional comment', json.dumps(result))

    def test_repository_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                publish('other-org/project', Path(temp), CONFIG)


if __name__ == '__main__':
    unittest.main()