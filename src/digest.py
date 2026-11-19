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
        unknown = sorted(x for x in labels if x.startswith(cfg.get('area_label_prefix', 'area:')) and x not in areas)
        warnings = []
        if unknown:
            warnings.append('unregistered_area')
        if len(matches) == 0:
            warnings.append('missing_area')
        elif len(matches) > 1:
            warnings.append('conflicting_areas')
        record = {
            'key': f'{kind}:{row["id"]}', 'kind': kind, 'topic': issue['number'],
            'title': issue['title'], 'area': matches[0] if len(matches) == 1 else cfg['default_area'],
            'actor': (row.get('user') or {}).get('login'),
            'url': row['html_url'],
            'source_time': row.get('updated_at') or row.get('submitted_at') or row.get('created_at'),
            'fingerprint': fingerprint(kind, detail),
            'fingerprints': {'1': fingerprint(kind, detail),
                             '2': fingerprint(kind, detail, extra.get('lock_detail') if extra else None)},
        }
        if warnings:
            record['area_warnings'] = warnings
        if extra:
            record.update({k: v for k, v in extra.items() if k != 'lock_detail'})
        records[record['key']] = record

    for issue in issues:
        labels = sorted(x['name'] for x in issue.get('labels', []))
        num = issue['number']
        topic_map[num] = issue
        pull = 'pull_request' in issue
        detail = [issue.get('title'), issue.get('body'), issue.get('state'), labels,
                  sorted(a['login'] for a in issue.get('assignees', [])), issue.get('milestone', {}).get('number') if issue.get('milestone') else None]
        extra = {'state': issue.get('state'), 'lock_detail': [issue.get('locked'), issue.get('active_lock_reason')]}
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


def same_fingerprint(old, row):
    """Compare newest jointly supported fingerprint version, for safe upgrades.

    Legacy cursors only carry `fingerprint` (v1); re-baselining new v2
    fields must not fabricate edits on all existing topics.
    """
    old_versions = dict(old.get('fingerprints') or {'1': old['fingerprint']})
    new_versions = dict(row.get('fingerprints') or {'1': row['fingerprint']})
    common = sorted(set(old_versions) & set(new_versions), key=int)
    return bool(common) and old_versions[common[-1]] == new_versions[common[-1]]


def reconcile(previous, current, checked_at):
    if not previous:
        return {'checked_at': checked_at, 'coverage_started_at': checked_at,
                'dropped_through_at': None, 'sequence': 0, 'records': current, 'updates': []}
    if instant(checked_at) < instant(previous['checked_at']):
        raise ValueError('Clock moved backwards')
    before = previous['records']
    changes = []
    for key, row in current.items():
        if key not in before or not same_fingerprint(before[key], row):
            changes.append((row, 'new' if key not in before else 'updated'))
    for key in before.keys() - current.keys():
        changes.append((before[key], 'no_longer_visible'))
    sequence = previous['sequence']
    updates = list(previous['updates'])
    for row, change in sorted(changes, key=lambda item: (item[0].get('source_time') or '', item[0]['key'])):
        sequence += 1
        updates.append({**{k: v for k, v in row.items() if k not in ('fingerprint', 'fingerprints')},
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


def compact_updates(items, records):
    """Schema-3 presentation: title/area/base URL stored once per topic.

    Exact source links and historical title/area differences remain on entries.
    The source cursor retains FULL entries, not these compact projections.
    """
    topics = {}
    for item in items:
        topic = item.get('topic')
        if topic is None:
            continue
        key = str(topic)
        if key in topics:
            continue
        parent = next((v for v in records.values()
                       if v.get('topic') == topic and v.get('kind') in ('issue', 'pull_request')),
                      item)
        entry = {'title': parent.get('title'), 'area': parent.get('area'),
                 'url': parent.get('url')}
        if parent.get('area_warnings'):
            entry['area_warnings'] = parent['area_warnings']
        topics[key] = {k: v for k, v in entry.items() if v is not None}
    compact = []
    for item in items:
        out = {k: v for k, v in item.items() if v is not None}
        canonical = topics.get(str(item.get('topic')), {})
        for key in ('title', 'area', 'url', 'area_warnings'):
            if key == 'url' and item.get('kind') in ('comment', 'review', 'inline_comment'):
                continue  # Keep exact permalinks regardless of topic URL.
            actual = item.get(key, [] if key == 'area_warnings' else None)
            expected = canonical.get(key, [] if key == 'area_warnings' else None)
            if actual == expected:
                out.pop(key, None)
            elif key == 'area_warnings':
                out[key] = actual  # Explicit [] overrides a newer routing warning.
        compact.append(out)
    return compact, topics


def feed_for(repository, state, cfg, revisions=None):
    updates = state['updates']
    schema = cfg.get('feed_schema', 2)
    if schema not in (2, 3):
        raise ValueError('Unsupported publication schema')

    def candidate(first):
        full = updates[first:]
        dropped = updates[first - 1]['observed_at'] if first else state.get('dropped_through_at')
        retained, topics = compact_updates(full, state.get('records', {})) if schema == 3 else (full, {})
        result = {'schema': schema, 'repository': repository,
                  'checked_at': state['checked_at'], 'sequence': state['sequence'],
                  'coverage_started_at': state['coverage_started_at'], 'dropped_through_at': dropped,
                  'oldest_sequence': retained[0]['sequence'] if retained else None,
                  'windows': windows(state, retained, dropped, cfg), 'updates': retained}
        if schema == 3:
            result['topics'] = topics
        if revisions:
            result['revisions'] = revisions
        return result

    answer = candidate(len(updates))
    if len(encoded(answer)) > cfg['max_feed_bytes']:
        raise ValueError('Feed budget cannot fit metadata')
    for idx in range(len(updates) - 1, -1, -1):
        possible = candidate(idx)
        if len(encoded(possible)) > cfg['max_feed_bytes']:
            break
        answer = possible
    return answer


def instruction_revisions(cfg, tree='HEAD', runner=subprocess.check_output):
    """Hash ONLY canonical files, never mixed runbooks or native task settings."""
    revisions = {}
    for key, path in cfg.get('revision_files', {}).items():
        if not path or path.startswith('/') or '..' in Path(path).parts:
            raise ValueError('Revision paths must be relative to the repository')
        listing = runner(['git', 'ls-tree', tree, '--', path], text=True).strip()
        if not listing or len(listing.splitlines()) != 1:
            raise ValueError('Missing or ambiguous canonical revision path: ' + path)
        parts = listing.split('\t', 1)[0].split()
        if len(parts) != 3 or parts[1] != 'blob':
            raise ValueError('Expected tracked canonical file: ' + path)
        revisions[key] = parts[2]
    return revisions


def trim_cursor(state, cfg):
    """Bound full-version cursor storage separately from the compact feed."""
    limit = cfg.get('cursor_max_events', 2000)
    if not isinstance(limit, int) or limit < 1:
        raise ValueError('Invalid cursor retention count')
    updates = state['updates']
    if len(updates) > limit:
        removed = updates[:-limit]
        state['dropped_through_at'] = removed[-1]['observed_at']
        state['updates'] = updates[-limit:]
    return state


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
    if cfg.get('feed_schema', 2) not in (2, 3):
        raise ValueError('Unsupported feed schema')
    if cfg.get('cursor_max_events', 2000) < 1:
        raise ValueError('Invalid cursor retention count')
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
    trim_cursor(state, cfg)
    feed = feed_for(repo, state, cfg, instruction_revisions(cfg))
    # The cursor retains complete event versions; only the published projection is
    # compact and byte-bounded. Never store schema-3 projections as cursor history.
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