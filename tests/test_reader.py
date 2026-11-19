import unittest
from datetime import datetime, timezone
from reader import select_slot, read_window
from digest import windows
from test_digest import CONFIG

REPO = 'example-org/project-board'

def feed(schema=2):
    f = {'schema':schema, 'repository':REPO, 'checked_at':'2026-11-18T21:38:00+00:00',
         'windows':[{'slot':'2026-11-18T22:00:00+00:00', 'from':'2026-11-18T15:00:00+00:00',
                     'through':'2026-11-18T21:38:00+00:00', 'fresh':True, 'limits':[],
                     'first_sequence':1,'last_sequence':1}],
         'updates':[{'sequence':1,'topic':7,'kind':'comment','change':'updated',
                     'url':f'https://github.com/{REPO}/issues/7#issuecomment-5',
                     'title':'Old title','area':'Engineering'}]}
    if schema == 3:
        f['topics'] = {'7': {'title':'New title','area':'Operations',
                             'url':f'https://github.com/{REPO}/issues/7'}}
        del f['updates'][0]['title'];del f['updates'][0]['area']
    return f

class ReaderTests(unittest.TestCase):
    def test_early_scheduled_vs_manual_and_explicit_intended(self):
        now=datetime(2026,11,18,21,58,tzinfo=timezone.utc)
        self.assertEqual(select_slot(now,CONFIG).isoformat(),'2026-11-18T22:00:00+00:00')
        self.assertEqual(select_slot(now,CONFIG,manual=True).isoformat(),'2026-11-18T16:00:00+00:00')
        self.assertEqual(select_slot(now,CONFIG,intended_slot='2026-11-18T22:00:00Z').isoformat(),'2026-11-18T22:00:00+00:00')

    def test_schema2_and_3_exact_link(self):
        now=datetime(2026,11,18,22,0,tzinfo=timezone.utc)
        for schema in (2,3):
            with self.subTest(schema=schema):
                result=read_window(feed(schema),REPO,CONFIG,now)
                self.assertEqual(result['status'],'observed')
                self.assertTrue(result['updates'][0]['url'].endswith('#issuecomment-5'))
                self.assertEqual(result['delivery'],'unverified')

    def test_missing_and_stale_are_not_success(self):
        now=datetime(2026,11,18,22,0,tzinfo=timezone.utc)
        f=feed();f['windows'][0]['first_sequence']=0
        self.assertEqual(read_window(f,REPO,CONFIG,now)['status'],'partial')
        f=feed();f['windows'][0]['fresh']=False
        self.assertEqual(read_window(f,REPO,CONFIG,now)['status'],'stale')
        f=feed();f['windows']=[]
        self.assertEqual(read_window(f,REPO,CONFIG,now)['status'],'unavailable')

    def test_reject_mismatched_repository(self):
        with self.assertRaises(ValueError):
            read_window(feed(), 'wrong-org/repo', CONFIG, datetime(2026,11,18,22,tzinfo=timezone.utc))

if __name__=='__main__': unittest.main()