"""Pure reference reader: no connectors, persistence, or write privileges.

A scheduler must separately demonstrate that it selected the intended run,
read the feed, displayed a result, and delivered any notification.
"""
from bisect import bisect_right
from datetime import datetime, timedelta, timezone
from digest import instant, slots_around


def select_slot(now, cfg, intended_slot=None, manual=False, early_minutes=5):
    """Choose an actual configured slot; intended scheduler occurrence wins."""
    now = now.astimezone(timezone.utc)
    slots = slots_around(now, cfg)
    if intended_slot is not None and not manual:
        selected = instant(intended_slot)
        if selected not in slots:
            raise ValueError('Intended occurrence is not a configured reader slot')
        return selected
    i = bisect_right(slots, now)
    if not manual and i < len(slots) and timedelta(0) < slots[i] - now <= timedelta(minutes=early_minutes):
        return slots[i]
    return slots[i - 1]


def resolve_entry(item, topics, schema):
    """Keep exact comment/review URLs; historical overrides beat current topic."""
    if schema == 2:
        return dict(item)
    topic = topics.get(str(item.get('topic')), {}) if item.get('topic') is not None else {}
    resolved = dict(item)
    for field in ('title', 'area', 'url', 'area_warnings'):
        if field not in resolved and field in topic:
            resolved[field] = topic[field]
    if not resolved.get('url'):
        raise ValueError('Missing exact item link and topic base link')
    return resolved


def read_window(feed, repository, cfg, now, intended_slot=None, manual=False):
    """Validate a snapshot without equating freshness with notification delivery."""
    if feed.get('schema') not in (2, 3):
        raise ValueError('Unsupported schema')
    if feed.get('repository') != repository:
        raise ValueError('Repository mismatch')
    checked = instant(feed['checked_at'])
    if checked > now.astimezone(timezone.utc) + timedelta(minutes=2):
        raise ValueError('Snapshot timestamp is in the future')
    expected = select_slot(now, cfg, intended_slot, manual)
    matched = [w for w in feed['windows'] if instant(w['slot']) == expected]
    if len(matched) != 1:
        return {'status': 'unavailable', 'slot': expected.isoformat(), 'reason': 'matching_slot_missing', 'updates': []}
    w = matched[0]
    instant(w['from']); instant(w['through'])
    lo, hi = w['first_sequence'], w['last_sequence']
    if (lo is None) != (hi is None):
        raise ValueError('Incomplete sequence bounds')
    if lo is None:
        rows = []
        gap = False
    else:
        rows = [item for item in feed['updates'] if lo <= item['sequence'] <= hi]
        gap = ([item['sequence'] for item in rows] != list(range(lo, hi + 1)))
    limits = list(w.get('limits', []))
    if gap:
        limits.append('missing_entries')
    status = 'stale' if not w['fresh'] else ('partial' if limits else 'observed')
    return {'status': status, 'slot': expected.isoformat(), 'from': w['from'],
            'through': w['through'], 'limits': limits,
            'updates': [resolve_entry(item, feed.get('topics', {}), feed['schema']) for item in rows],
            'delivery': 'unverified'}