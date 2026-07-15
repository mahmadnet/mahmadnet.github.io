import datetime as dt
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import update_profile


def activity_fragment(month: str = "July 2026", include_pagination: bool = True) -> str:
    pagination = (
        '<form class="js-show-more-timeline-form" '
        'action="/mahmadnet?tab=overview&amp;from=2026-06-01&amp;to=2026-06-30&amp;include_header=no"></form>'
        if include_pagination else ""
    )
    return f"""
    <div class="contribution-activity-listing">
      <h3><span>{month}</span></h3>
      <div class="TimelineItem">
        <details><summary>Created 2 commits in 1 repository</summary>
          <a href="/mahmadnet/secret-repository">secret-repository</a>
        </details>
      </div>
      <div class="TimelineItem">
        <div class="TimelineItem-body">
          <span class="f4 lh-condensed">7 contributions in private repositories</span>
          <span class="float-right f6 color-fg-muted pt-1">Jul 1 – Jul 14</span>
        </div>
      </div>
      {pagination}
    </div>
    """


class ProfileUpdaterTests(unittest.TestCase):
    def test_contribution_metrics(self):
        days = (
            update_profile.ContributionDay(dt.date(2026, 1, 1), 1, 2),
            update_profile.ContributionDay(dt.date(2026, 1, 2), 2, 4),
            update_profile.ContributionDay(dt.date(2026, 1, 3), 0, 0),
            update_profile.ContributionDay(dt.date(2026, 1, 4), 4, 8),
            update_profile.ContributionDay(dt.date(2026, 2, 1), 1, 1),
        )
        metrics = update_profile.contribution_metrics(days)
        self.assertEqual(metrics["active_days"], 4)
        self.assertEqual(metrics["longest_streak"], 2)
        self.assertEqual(metrics["busiest_day"].date, dt.date(2026, 1, 4))
        self.assertEqual(metrics["busiest_month"], dt.date(2026, 1, 1))
        self.assertEqual(metrics["busiest_month_total"], 14)
        self.assertAlmostEqual(metrics["average"], 3.75)
        snapshot = update_profile.Snapshot(15, days, (), dt.date(2026, 2, 1))
        summary = update_profile.render_about_summary(snapshot)
        self.assertIn("<strong>15</strong> contributions in the last year", summary)
        self.assertIn("<strong>4</strong> active days", summary)
        self.assertIn("<strong>2-day</strong> longest streak", summary)
    def test_activity_month_window_has_current_plus_previous_eleven(self):
        now = dt.datetime(2026, 7, 14, 12, tzinfo=dt.timezone.utc)
        months = update_profile.activity_months(now)
        self.assertEqual(len(months), 12)
        self.assertEqual(months[0], dt.date(2026, 7, 1))
        self.assertEqual(months[-1], dt.date(2025, 8, 1))

    def test_fragment_parser_sanitizes_events_and_pagination(self):
        events, next_url = update_profile.parse_activity_fragment(
            activity_fragment(),
            dt.date(2026, 7, 1),
            dt.date(2026, 6, 1),
        )
        self.assertEqual(
            events,
            (
                update_profile.ActivityEvent(dt.date(2026, 7, 1), "commits", 2, 1),
                update_profile.ActivityEvent(
                    dt.date(2026, 7, 1),
                    "contributions",
                    7,
                    date_label="Jul 1 – Jul 14",
                ),
            ),
        )
        self.assertEqual(
            next_url,
            "https://github.com/mahmadnet?tab=overview&from=2026-06-01&to=2026-06-30&include_header=no",
        )
        rendered = update_profile.render_activity(events)
        self.assertNotIn("private", rendered.lower())
        self.assertNotIn("secret-repository", rendered)
        self.assertNotIn("href=", rendered)

    def test_all_supported_event_types_and_pluralization(self):
        month = dt.date(2026, 7, 1)
        cases = (
            ("Created 1 commit in 1 repository", "commits", "Created 1 commit in 1 repository"),
            ("Created 2 repositories", "repositories", "Created 2 repositories"),
            ("Opened 1 pull request in 1 repository", "pull_requests", "Opened 1 pull request in 1 repository"),
            ("Reviewed 2 pull requests in 3 repositories", "reviews", "Reviewed 2 pull requests in 3 repositories"),
            ("Opened 1 issue in 1 repository", "issues", "Opened 1 issue in 1 repository"),
        )
        for source, kind, expected in cases:
            with self.subTest(source=source):
                event = update_profile.parse_activity_item(month, source, "", "")
                self.assertEqual(event.kind, kind)
                self.assertEqual(update_profile.activity_summary(event), expected)

    def test_unknown_event_and_invalid_pagination_fail(self):
        month = dt.date(2026, 7, 1)
        with self.assertRaises(ValueError):
            update_profile.parse_activity_item(month, "Starred a repository", "", "")
        with self.assertRaises(ValueError):
            update_profile.expected_pagination_url(
                "https://example.com/mahmadnet?tab=overview&from=2026-06-01&to=2026-06-30&include_header=no",
                dt.date(2026, 6, 1),
            )
        with self.assertRaises(ValueError):
            update_profile.parse_activity_fragment(
                activity_fragment(include_pagination=False),
                month,
                dt.date(2026, 6, 1),
            )

    def test_activity_reconciliation(self):
        month = dt.date(2026, 7, 1)
        days = (
            update_profile.ContributionDay(dt.date(2026, 7, 1), 1, 2),
            update_profile.ContributionDay(dt.date(2026, 7, 2), 2, 7),
        )
        events = (
            update_profile.ActivityEvent(month, "commits", 2, 1),
            update_profile.ActivityEvent(month, "contributions", 7),
        )
        update_profile.reconcile_activity(events, days, (month,))
        with self.assertRaises(ValueError):
            update_profile.reconcile_activity(events[:1], days, (month,))

    def test_activity_shows_six_events_then_one_disclosure(self):
        month = dt.date(2026, 7, 1)
        events = tuple(
            update_profile.ActivityEvent(
                update_profile.shift_month(month, -(index // 2)),
                "contributions",
                index + 1,
            )
            for index in range(8)
        )
        rendered = update_profile.render_activity(events)
        visible, expandable = rendered.split('<details class="activity-more">', 1)
        self.assertEqual(visible.count('class="activity-event"'), 6)
        self.assertEqual(expandable.count('class="activity-event"'), 2)
        self.assertEqual(rendered.count("<details"), 1)
        self.assertIn('<span class="activity-more-label">See more activity</span>', rendered)
        self.assertIn('<span class="activity-less-label">See less activity</span>', rendered)
        self.assertNotIn("activity-metric", rendered)
        self.assertNotIn("privacy", rendered.lower())

    def test_activity_omits_disclosure_when_six_or_fewer(self):
        events = tuple(
            update_profile.ActivityEvent(dt.date(2026, 7, 1), "contributions", index + 1)
            for index in range(6)
        )
        self.assertNotIn("<details", update_profile.render_activity(events))

    def test_missing_region_and_invalid_calendar_fail_without_output(self):
        with self.assertRaises(ValueError):
            update_profile.replace_region("unchanged", "START", "END", "replacement")
        with self.assertRaises(ValueError):
            update_profile.validate_contributions(
                1,
                [update_profile.ContributionDay(dt.date(2026, 7, 14), 1, 1)],
            )



if __name__ == "__main__":
    unittest.main()
