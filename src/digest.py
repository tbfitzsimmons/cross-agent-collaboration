"""Publish metadata-only, bounded GitHub activity with stateless reporting windows."""
import argparse
from bisect import bisect_right
from datetime import datetime, time, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

SCHEMA = 2


def instant(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Timestamps must include UTC offset')
    return result.astimezone(timezone.utc)


def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')


def fingerprint(*parts):
    return hashlib.sha256(encoded(parts)).hexdigest()


def api_pages(repo, path):
    sep = '&' if '?' in path else '?'
    payload = subprocess.check_output(['gh', 'api', '--paginate', '--slurp',
                                       f'repos/{repo}/{path}{sep}per_page=100'], text=True)
    pages = json.loads(payload)
    if not isinstance(pages, list) or any(not isinstance(p, list) for p in pages):
        raise ValueError(f'Unexpected API pagination structure: {path}')
    return [row for page in pages for row in page]


def api_one(repo, path):
    return json.loads(subprocess.check_output(['gh', 'api', f'repos/{repo}/{path}'], text=True))


def capture(repo, cfg, read=api_pages, read_one=api_one):
    """Fail closed on API errors; never store human-authored bodies in the feed/cursor."""
    issues = read(repo, 'issues?state=all')
    topic_map = {}
    records = {}
    areas = cfg['labels']

    def add(kind, row, issue, detail, extra=None):
        labels = sorted(x['name'] for x in issue.get('labels', []))
        matches = sorted({areas[x] for x in labels if x in areas})
        record = {
            'key': f'{kind}:{row["id"]}', 'kind': kind, 'topic': issue['number'],
            'title': issue['title'], 'area': matches[0] if len(matches) == 1 else cfg['default_area'],
            'actor': (row.get('user') or {}).get('login'),
            'url': row['html_url'],
            'source_time': row.get('updated_at') or row.get('submitted_at') or row.get('created_at'),
            'fingerprint': fingerprint(kind, detail),
        }
        if extra:
            record.update(extra)
        records[record['key']] = record

    for issue in issues:
        labels = sorted(x['name'] for x in issue.get('labels', []))
        num = issue['number']
        topic_map[num] = issue
        pull = 'pull_request' in issue
        detail = [issue.get('title'), issue.get('body'), issue.get('state'), labels,
                  sorted(a['login'] for a in issue.get('assignees', [])), issue.get('milestone', {}).get('number') if issue.get('milestone') else None]
        extra = {'state': issue.get('state')}
        if pull:
            p = read_one(repo, f'pulls/{num}')
            detail += [p['head']['sha'], p.get('merged_at'), p.get('draft'), p.get('base', {}).get('ref')]
            extra.update(head_sha=p['head']['sha'], merged_at=p.get('merged_at'))
            for review in read(repo, f'pulls/{num}/reviews'):
                if review.get('state') != 'PENDING':
                    add('review', review, issue, [review.get('state'), review.get('body'), review.get('commit_id')],
                        {'review_state': review.get('state'), 'reviewed_sha': review.get('commit_id')})
            for comment in read(repo, f'pulls/{num}/comments'):
                add('inline_comment', comment, issue, [comment.get('body'), comment.get('path'), comment.get('line')])
        add('pull_request' if pull else 'issue', issue, issue, detail, extra)

    for comment in read(repo, 'issues/comments?sort=updated&direction=asc'):
        num = int(comment['issue_url'].rsplit('/', 1)[-1])
        if num in topic_map:
            add('comment', comment, topic_map[num], [comment.get('body')])
    return records


def reconcile(previous, current, checked_at):
    if not previous:
        return {'checked_at': checked_at, 'coverage_started_at': checked_at,
                'dropped_through_at': None, 'sequence': 0, 'records': current, 'updates': []}
    if instant(checked_at) < instant(previous['checked_at']):
        raise ValueError('Clock moved backwards')
    before = previous['records']
    changes = []
    for key, row in current.items():
        if key not in before or before[key]['fingerprint'] != row['fingerprint']:
            changes.append((row, 'new' if key not in before else 'updated'))
    for key in before.keys() - current.keys():
        changes.append((before[key], 'no_longer_visible'))
    sequence = previous['sequence']
    updates = list(previous['updates'])
    for row, change in sorted(changes, key=lambda item: (item[0].get('source_time') or '', item[0]['key'])):
        sequence += 1
        updates.append({**{k: v for k, v in row.items() if k != 'fingerprint'},
                        'sequence': sequence, 'change': change, 'observed_at': checked_at})
    return {'checked_at': checked_at, 'coverage_started_at': previous['coverage_started_at'],
            'dropped_through_at': previous.get('dropped_through_at'),
            'sequence': sequence, 'records': current, 'updates': updates}


def slots_around(checked, cfg):
    tz = ZoneInfo(cfg['timezone'])
    day = checked.astimezone(tz).date()
    slots = []
    for offset in range(-3, 4):
        for hour_min in cfg['reader_times']:
            hour, minute = map(int, hour_min.split(':'))
            slot = datetime.combine(day + timedelta(days=offset), time(hour, minute), tzinfo=tz)
            slots.append(slot.astimezone(timezone.utc))
    return sorted(set(slots))


def windows(state, retained, dropped, cfg):
    checked = instant(state['checked_at'])
    baseline = instant(state['coverage_started_at'])
    slots = slots_around(checked, cfg)
    i = bisect_right(slots, checked)
    result = []
    for position in (i - 1, i):
        slot = slots[position]
        start = slots[position - 1] - timedelta(minutes=cfg['overlap_minutes'])
        # A snapshot before a future slot is provisional: publish a candidate, not a delivered event.
        matches = [x['sequence'] for x in retained if start <= instant(x['observed_at']) <= checked]
        limits = []
        if start < baseline:
            limits.append('baseline')
        if dropped and start <= instant(dropped):
            limits.append('retention')
        result.append({'slot': slot.isoformat(), 'from': start.isoformat(),
                       'through': checked.isoformat(),
                       'fresh': checked >= slot - timedelta(minutes=cfg['publisher_lead_minutes']),
                       'limits': limits,
                       'first_sequence': matches[0] if matches else None,
                       'last_sequence': matches[-1] if matches else None})
    return result


def feed_for(repository, state, cfg):
    updates = state['updates']

    def candidate(first):
        remaining = updates[first:]
        dropped = updates[first - 1]['observed_at'] if first else state.get('dropped_through_at')
        return {'schema': SCHEMA, 'repository': repository,
                'checked_at': state['checked_at'], 'sequence': state['sequence'],
                'coverage_started_at': state['coverage_started_at'], 'dropped_through_at': dropped,
                'oldest_sequence': remaining[0]['sequence'] if remaining else None,
                'windows': windows(state, remaining, dropped, cfg), 'updates': remaining}

    answer = candidate(len(updates))
    if len(encoded(answer)) > cfg['max_feed_bytes']:
        raise ValueError('Feed budget cannot fit metadata')
    for idx in range(len(updates) - 1, -1, -1):
        possible = candidate(idx)
        if len(encoded(possible)) > cfg['max_feed_bytes']:
            break
        answer = possible
    return answer


def configuration(path):
    cfg = json.loads(Path(path).read_text(encoding='utf-8'))
    ZoneInfo(cfg['timezone'])
    for clock in cfg['reader_times']:
        h, m = map(int, clock.split(':'))
        time(h, m)
    if len(set(cfg['reader_times'])) != len(cfg['reader_times']) or not cfg['reader_times']:
        raise ValueError('Reader slots must be nonempty and unique')
    if not 0 <= cfg['overlap_minutes'] <= 1440 or not 0 <= cfg['publisher_lead_minutes'] <= 1440:
        raise ValueError('Invalid interval')
    if cfg['max_feed_bytes'] < 1024:
        raise ValueError('Max feed bytes too small')
    return cfg


def publish(repo, directory, cfg, read=api_pages, read_one=api_one, now=None):
    if cfg.get('repository') and cfg['repository'] != repo:
        raise ValueError('Repository mismatch')
    cursor = directory / 'cursor.json'
    prior = json.loads(cursor.read_text(encoding='utf-8')) if cursor.exists() else {}
    checked = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    current = capture(repo, cfg, read, read_one)
    state = reconcile(prior, current, checked)
    feed = feed_for(repo, state, cfg)
    state['updates'] = feed['updates']
    state['dropped_through_at'] = feed['dropped_through_at']
    directory.mkdir(parents=True, exist_ok=True)
    # Write only after *all* API calls and validation have succeeded.
    for name, obj in [('cursor.json', state), ('inbox.json', feed)]:
        (directory / (name + '.tmp')).write_bytes(encoded(obj))
    for name in ('cursor.json', 'inbox.json'):
        (directory / (name + '.tmp')).replace(directory / name)
    return feed


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', required=True)
    p.add_argument('--state-dir', type=Path, required=True)
    p.add_argument('--config', default='config.json')
    args = p.parse_args()
    publish(args.repo, args.state_dir, configuration(args.config))


if __name__ == '__main__':
    main()