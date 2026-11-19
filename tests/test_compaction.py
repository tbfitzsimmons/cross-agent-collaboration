import unittest
import json
from pathlib import Path
import tempfile
from unittest.mock import Mock
from digest import compact_updates, feed_for, encoded, reconcile, capture, instruction_revisions, trim_cursor, publish
from reader import read_window
from test_digest import CONFIG, REPO, T0, T1, issue, mock_read
from datetime import datetime,timezone

class CompactionTests(unittest.TestCase):
    def setUp(self):
        self.cfg={**CONFIG, 'feed_schema':3}
        self.parent={'key':'issue:1','kind':'issue','topic':7,'title':'New title','area':'Engineering',
                     'url':f'https://github.com/{REPO}/issues/7'}
        self.comment={'key':'comment:1','kind':'comment','topic':7,'title':'Old title','area':'Engineering',
                      'url':f'https://github.com/{REPO}/issues/7#issuecomment-1', 'observed_at':T1, 'sequence':1}

    def state(self, events=None):
        return {'checked_at':T1,'coverage_started_at':T0,'sequence':len(events or [self.comment]),
                'dropped_through_at':None,'updates':events or [self.comment],
                'records':{'issue:1':self.parent}}

    def test_exact_comment_and_historical_rename(self):
        f=feed_for(REPO,self.state(),self.cfg)
        self.assertEqual(f['schema'],3)
        self.assertEqual(f['topics']['7']['title'],'New title')
        self.assertEqual(f['updates'][0]['title'],'Old title')
        self.assertTrue(f['updates'][0]['url'].endswith('#issuecomment-1'))
        result=read_window(f, REPO, self.cfg, datetime(2026,11,18,22,0,tzinfo=timezone.utc))
        self.assertEqual(result['updates'][0]['title'],'Old title')
        self.assertTrue(result['updates'][0]['url'].endswith('#issuecomment-1'))

    def test_compact_capacity_utf8_and_cursor_full_versions(self):
        events=[]
        for n in range(1,70):
            events.append({**self.comment,'sequence':n,'title':'Old title',
                           'observed_at':T1,'source_time':T1, 'actor':'synthetic-'+('é'*60)})
        s=self.state(events);s['sequence']=len(events)
        compact=feed_for(REPO,s,self.cfg)
        legacy=feed_for(REPO,s,CONFIG)
        self.assertLessEqual(len(encoded(compact)),self.cfg['max_feed_bytes'])
        self.assertGreater(len(compact['updates']),len(legacy['updates']))
        self.assertEqual(len(s['updates']),69)  # Reading the feed never clips cursor.
        self.assertEqual(compact['updates'][-1]['sequence'],69)
        self.assertIn('retention',compact['windows'][1]['limits'])

    def test_revisions_only_canonical_files(self):
        runner=Mock(return_value='100644 blob abcdef1234\tdocs/reader-operational.md\n')
        self.assertEqual(instruction_revisions({'revision_files':{'reader_prompt':'docs/reader-operational.md'}},runner=runner),{'reader_prompt':'abcdef1234'})
        self.assertEqual(runner.call_args[0][0][-1],'docs/reader-operational.md')
        with self.assertRaises(ValueError): instruction_revisions({'revision_files':{'x':'../private'}})

    def test_legacy_fingerprint_upgrade_does_not_emit_false_events(self):
        old=capture(REPO,CONFIG,mock_read([issue()]))
        baseline=reconcile({},old,T0)
        baseline['records']['issue:101'].pop('fingerprints') # old cursor version
        current=capture(REPO,CONFIG,mock_read([issue()]))
        migrated=reconcile(baseline,current,T1)
        self.assertEqual(migrated['sequence'],0)
        changed=capture(REPO,CONFIG,mock_read([issue(state='closed')]))
        actual=reconcile(baseline,changed,T1)
        self.assertEqual(actual['updates'][0]['change'],'updated')
        self.assertEqual(actual['updates'][0]['sequence'],1)

    def test_new_fingerprint_version_observes_lock_change_after_migration(self):
        first=capture(REPO,CONFIG,mock_read([issue(locked=False)]))
        baseline=reconcile({},first,T0)
        current=capture(REPO,CONFIG,mock_read([issue(locked=True)]))
        changed=reconcile(baseline,current,T1)
        self.assertEqual(len(changed['updates']),1)

    def test_schema3_cursor_roundtrip_preserves_full_record_links(self):
        comments = []
        c = {'id': 501, 'body': 'Fictional edit', 'issue_url':'https://api.github.com/issues/1',
             'html_url':f'https://github.com/{REPO}/issues/1#issuecomment-501','updated_at':T1}
        cfg = {**self.cfg, 'revision_files':{}}
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            publish(REPO, folder, cfg, mock_read([issue()], comments), now=datetime.fromisoformat(T0))
            comments.append(c)
            first=publish(REPO, folder, cfg, mock_read([issue()], comments), now=datetime.fromisoformat(T1))
            full=json.loads((folder/'cursor.json').read_text())
            published=json.loads((folder/'inbox.json').read_text())
            self.assertEqual(first, published)
            self.assertEqual(full['updates'][0]['url'], c['html_url'])
            self.assertEqual(full['updates'][0]['title'], issue()['title'])
            self.assertEqual(published['schema'],3)
            self.assertTrue(published['updates'][0]['url'].endswith('#issuecomment-501'))
            quiet=publish(REPO, folder, cfg, mock_read([issue()], comments), now=datetime.fromisoformat(T1))
            self.assertEqual(quiet['sequence'], first['sequence'])

    def test_revision_map_multiple_independent_blobs(self):
        def runner(cmd, text):
            path=cmd[-1]
            sha={'docs/reader-operational.md':'abc111','docs/collaboration-protocol.md':'def222'}[path]
            return f'100644 blob {sha}\t{path}\n'
        revisions=instruction_revisions({'revision_files':{
            'reader_prompt':'docs/reader-operational.md',
            'collaboration_protocol':'docs/collaboration-protocol.md'}},runner=runner)
        self.assertEqual(revisions,{'reader_prompt':'abc111','collaboration_protocol':'def222'})

    def test_cursor_trim_explicit_watermark(self):
        events=[{**self.comment,'sequence':n,'observed_at':T1} for n in range(1,9)]
        s=self.state(events)
        trim_cursor(s,{**self.cfg,'cursor_max_events':3})
        self.assertEqual([x['sequence'] for x in s['updates']],[6,7,8])
        self.assertEqual(s['dropped_through_at'],T1)
        feed=feed_for(REPO,s,self.cfg)
        self.assertIn('retention',feed['windows'][1]['limits'])

if __name__ == '__main__':unittest.main()