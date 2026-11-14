import unittest
from datetime import datetime, timezone
from site_analytics import summarize, validate_event


class AnalyticsTests(unittest.TestCase):
    def test_private_fields_rejected(self):
        with self.assertRaises(ValueError):
            validate_event({'event_name': 'page_view', 'child_name': 'private'})

    def test_invalid_ids_rejected(self):
        with self.assertRaises(ValueError):
            validate_event({'event_name': 'page_view', 'session_id': 'bad', 'event_id': 'bad'})

    def test_funnel_deduplicates_and_requires_prior_steps(self):
        now = datetime(2026, 11, 14, 12, tzinfo=timezone.utc)
        def event(name, session='a', at=None, **extra):
            return dict(event_name=name, session_id=session, created_at=(at or now).isoformat(), **extra)
        rows = [event('page_view'), event('page_view'), event('creation_started'),
                event('hero_completed'), event('preview_succeeded', 'b', duration_ms=2000),
                event('heartbeat', 'old', datetime(2026, 11, 14, 11, tzinfo=timezone.utc))]
        stats = summarize(rows, now)
        self.assertEqual(stats['visits'], 1)
        self.assertEqual(stats['active'], 2)
        self.assertEqual([r['Sessions'] for r in stats['funnel']], [1, 1, 1, 0, 0, 0])
        self.assertEqual(stats['average_seconds'], 2)


if __name__ == '__main__':
    unittest.main()
