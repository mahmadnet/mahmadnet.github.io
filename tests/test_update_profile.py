import datetime as dt
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import update_profile


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

    def test_monthly_activity_is_uniform_and_reconciled(self):
        now = dt.datetime(2026, 7, 14, 12, tzinfo=dt.timezone.utc)
        user = {}
        for index in range(12):
            user[f"m{index}"] = {
                "totalCommitContributions": 2 if index == 0 else 0,
                "totalIssueContributions": 0,
                "totalPullRequestContributions": 1 if index == 0 else 0,
                "totalPullRequestReviewContributions": 0,
                "totalRepositoryContributions": 1 if index == 0 else 0,
                "restrictedContributionsCount": 3 if index == 0 else 0,
                "contributionCalendar": {"totalContributions": 7 if index == 0 else 0},
            }
        months = update_profile.parse_monthly_activity(json.dumps({"data": {"user": user}}), now)
        self.assertEqual(len(months), 12)
        self.assertEqual(months[0].month, dt.date(2026, 7, 1))
        self.assertEqual(months[-1].month, dt.date(2025, 8, 1))
        self.assertEqual(months[0].private, 3)
        self.assertEqual(months[1].total, 0)

    def test_monthly_activity_rejects_unreconciled_data(self):
        now = dt.datetime(2026, 7, 14, 12, tzinfo=dt.timezone.utc)
        user = {f"m{index}": {
            "totalCommitContributions": 0,
            "totalIssueContributions": 0,
            "totalPullRequestContributions": 0,
            "totalPullRequestReviewContributions": 0,
            "totalRepositoryContributions": 0,
            "restrictedContributionsCount": 0,
            "contributionCalendar": {"totalContributions": 1 if index == 0 else 0},
        } for index in range(12)}
        with self.assertRaises(ValueError):
            update_profile.parse_monthly_activity(json.dumps({"data": {"user": user}}), now)

    def test_query_contains_twelve_non_overlapping_months(self):
        now = dt.datetime(2026, 7, 14, 12, tzinfo=dt.timezone.utc)
        query = update_profile.monthly_query(now)
        self.assertEqual(query.count("contributionsCollection("), 12)
        self.assertIn('m0: contributionsCollection(from: "2026-07-01T00:00:00Z"', query)
        self.assertIn('m1: contributionsCollection(from: "2026-06-01T00:00:00Z", to: "2026-06-30T23:59:59Z"', query)
        self.assertIn('m11: contributionsCollection(from: "2025-08-01T00:00:00Z"', query)

    def test_profile_facts_come_only_from_the_rest_user_response(self):
        source = json.dumps({
            "login": "mahmadnet",
            "public_repos": 2,
            "created_at": "2018-02-18T12:00:00Z",
        })
        profile = update_profile.parse_profile_facts(source)
        self.assertEqual(profile.public_repositories, 2)
        self.assertEqual(profile.member_since, 2018)
        self.assertEqual(
            set(profile.__dataclass_fields__),
            {"public_repositories", "member_since"},
        )

    def test_only_approved_repository_is_rendered(self):
        source = json.dumps([
            {
                "name": "another-public-repository",
                "private": False,
                "fork": False,
                "html_url": "https://github.com/mahmadnet/another-public-repository",
                "updated_at": "2026-07-01T00:00:00Z",
            },
            {
                "name": "mahmadnet.github.io",
                "description": "GitHub Pages user site for mahmadnet",
                "language": "HTML",
                "private": False,
                "fork": False,
                "html_url": "https://github.com/mahmadnet/mahmadnet.github.io",
                "updated_at": "2026-07-14T00:00:00Z",
            },
        ])
        repository = update_profile.parse_featured_repository(source)
        rendered = update_profile.render_repository(repository, 2)
        self.assertIn("mahmadnet.github.io", rendered)
        self.assertNotIn("another-public-repository", rendered)

    def test_activity_shows_three_months_then_nine_more(self):
        months = tuple(update_profile.MonthlyActivity(
            dt.date(2026, 7, 1) - dt.timedelta(days=28 * index),
            0, 0, 0, 0, 0, 0, 0,
        ) for index in range(12))
        rendered = update_profile.render_activity(months)
        visible, expandable = rendered.split('<details class="activity-more">', 1)
        self.assertEqual(visible.count('class="activity-item"'), 3)
        self.assertEqual(expandable.count('class="activity-item"'), 9)
        self.assertIn("Show 9 earlier months", expandable)
        self.assertEqual(rendered.count('class="activity-metric is-zero"'), 72)

    def test_missing_generated_region_fails_without_output(self):
        with self.assertRaises(ValueError):
            update_profile.replace_region("unchanged", "START", "END", "replacement")

    def test_invalid_calendar_is_rejected(self):
        with self.assertRaises(ValueError):
            update_profile.validate_contributions(
                1,
                [update_profile.ContributionDay(dt.date(2026, 7, 14), 1, 1)],
            )


if __name__ == "__main__":
    unittest.main()
