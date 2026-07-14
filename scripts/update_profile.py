#!/usr/bin/env python3
"""Generate a sanitized, factual GitHub profile snapshot for the static page."""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
from dataclasses import dataclass
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any
from urllib.request import Request, urlopen

USERNAME = "mahmadnet"
FEATURED_REPOSITORY = "mahmadnet.github.io"
CONTRIBUTIONS_URL = f"https://github.com/users/{USERNAME}/contributions"
USER_URL = f"https://api.github.com/users/{USERNAME}"
REPOSITORIES_URL = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=updated"
GRAPHQL_URL = "https://api.github.com/graphql"
USER_AGENT = "mahmadnet.github.io profile updater"

REGIONS = {
    "facts": ("<!-- PROFILE_DATA:FACTS:START -->", "<!-- PROFILE_DATA:FACTS:END -->"),
    "repository": ("<!-- PROFILE_DATA:REPOSITORY:START -->", "<!-- PROFILE_DATA:REPOSITORY:END -->"),
    "contributions": ("<!-- PROFILE_DATA:CONTRIBUTIONS:START -->", "<!-- PROFILE_DATA:CONTRIBUTIONS:END -->"),
    "activity": ("<!-- PROFILE_DATA:ACTIVITY:START -->", "<!-- PROFILE_DATA:ACTIVITY:END -->"),
}


@dataclass(frozen=True)
class ContributionDay:
    date: dt.date
    level: int
    count: int


@dataclass(frozen=True)
class ProfileFacts:
    public_repositories: int
    member_since: int


@dataclass(frozen=True)
class RepositoryFacts:
    name: str
    description: str
    language: str
    updated_at: dt.datetime
    url: str


@dataclass(frozen=True)
class MonthlyActivity:
    month: dt.date
    total: int
    commits: int
    pull_requests: int
    reviews: int
    issues: int
    repositories: int
    private: int


@dataclass(frozen=True)
class Snapshot:
    rolling_total: int
    days: tuple[ContributionDay, ...]
    profile: ProfileFacts
    repository: RepositoryFacts
    months: tuple[MonthlyActivity, ...]
    updated: dt.date


class ContributionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.heading_parts: list[str] = []
        self.in_heading = False
        self.raw_days: list[dict[str, Any]] = []
        self.tooltips: dict[str, str] = {}
        self.tooltip_for: str | None = None
        self.tooltip_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "h2" and values.get("id") == "js-contribution-activity-description":
            self.in_heading = True
        elif tag == "td" and values.get("data-date"):
            self.raw_days.append({
                "date": values["data-date"],
                "level": int(values.get("data-level", "0")),
                "id": values.get("id", ""),
            })
        elif tag == "tool-tip" and values.get("for"):
            self.tooltip_for = values["for"]
            self.tooltip_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_heading:
            self.heading_parts.append(data)
        if self.tooltip_for:
            self.tooltip_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "h2":
            self.in_heading = False
        elif tag == "tool-tip" and self.tooltip_for:
            self.tooltips[self.tooltip_for] = " ".join(self.tooltip_parts).strip()
            self.tooltip_for = None
            self.tooltip_parts = []


def request_text(url: str, *, token: str | None = None, payload: dict[str, Any] | None = None) -> str:
    headers = {
        "Accept": "application/vnd.github+json, text/html",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = Request(url, headers=headers, data=data)
    with urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"GitHub returned HTTP {response.status} for {url}")
        return response.read().decode("utf-8")


def parse_contributions(source: str) -> tuple[int, tuple[ContributionDay, ...]]:
    parser = ContributionParser()
    parser.feed(source)
    heading = " ".join(" ".join(parser.heading_parts).split())
    total_match = re.search(r"([\d,]+)\s+contributions?", heading)
    if not total_match:
        raise ValueError("Contribution total was not found")

    days: list[ContributionDay] = []
    for raw in parser.raw_days:
        tooltip = parser.tooltips.get(raw["id"], "")
        count_match = re.match(r"([\d,]+)\s+contributions?", tooltip)
        count = int(count_match.group(1).replace(",", "")) if count_match else 0
        days.append(ContributionDay(dt.date.fromisoformat(raw["date"]), raw["level"], count))

    days.sort(key=lambda day: day.date)
    total = int(total_match.group(1).replace(",", ""))
    validate_contributions(total, days)
    return total, tuple(days)


def validate_contributions(total: int, days: list[ContributionDay]) -> None:
    dates = [day.date for day in days]
    if not 365 <= len(days) <= 371:
        raise ValueError(f"Expected a rolling-year calendar, received {len(days)} days")
    if len(set(dates)) != len(dates):
        raise ValueError("Contribution calendar contains duplicate dates")
    if any((right - left).days != 1 for left, right in zip(dates, dates[1:])):
        raise ValueError("Contribution calendar dates are not consecutive")
    if any(day.level not in range(5) for day in days):
        raise ValueError("Contribution calendar contains an invalid level")
    if sum(day.count for day in days) != total:
        raise ValueError("Contribution cell counts do not match the reported total")


def parse_profile_facts(user_source: str) -> ProfileFacts:
    user = json.loads(user_source)
    if user.get("login") != USERNAME or not isinstance(user.get("public_repos"), int):
        raise ValueError("GitHub user response did not match the expected profile")
    created = dt.datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
    return ProfileFacts(user["public_repos"], created.year)


def parse_featured_repository(source: str) -> RepositoryFacts:
    repositories = json.loads(source)
    if not isinstance(repositories, list):
        raise ValueError("GitHub repositories response was not a list")
    matches = [repo for repo in repositories if repo.get("name") == FEATURED_REPOSITORY]
    if len(matches) != 1:
        raise ValueError("The approved featured repository was not found exactly once")
    repo = matches[0]
    expected_url = f"https://github.com/{USERNAME}/{FEATURED_REPOSITORY}"
    if repo.get("private") or repo.get("fork") or repo.get("html_url") != expected_url:
        raise ValueError("Featured repository failed its public-source validation")
    updated = dt.datetime.fromisoformat(repo["updated_at"].replace("Z", "+00:00"))
    return RepositoryFacts(
        FEATURED_REPOSITORY,
        repo.get("description") or "Public GitHub Pages profile home.",
        repo.get("language") or "Unspecified",
        updated,
        expected_url,
    )


def shift_month(month: dt.date, offset: int) -> dt.date:
    index = month.year * 12 + month.month - 1 + offset
    return dt.date(index // 12, index % 12 + 1, 1)


def monthly_query(now: dt.datetime) -> str:
    fields = """totalCommitContributions totalIssueContributions totalPullRequestContributions totalPullRequestReviewContributions totalRepositoryContributions restrictedContributionsCount contributionCalendar { totalContributions }"""
    aliases = []
    current = now.date().replace(day=1)
    for index in range(12):
        start = shift_month(current, -index)
        if index == 0:
            end = now
        else:
            next_month = shift_month(start, 1)
            end = dt.datetime.combine(next_month, dt.time.min, tzinfo=dt.timezone.utc) - dt.timedelta(seconds=1)
        start_iso = dt.datetime.combine(start, dt.time.min, tzinfo=dt.timezone.utc).isoformat().replace("+00:00", "Z")
        end_iso = end.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        aliases.append(f'm{index}: contributionsCollection(from: "{start_iso}", to: "{end_iso}") {{ {fields} }}')
    return "query { user(login: \"" + USERNAME + "\") { " + " ".join(aliases) + " } }"


def parse_monthly_activity(source: str, now: dt.datetime) -> tuple[MonthlyActivity, ...]:
    payload = json.loads(source)
    if payload.get("errors"):
        raise ValueError(f"GitHub GraphQL returned errors: {payload['errors']}")
    user = payload.get("data", {}).get("user")
    if not isinstance(user, dict):
        raise ValueError("GitHub GraphQL response did not contain the profile")

    months: list[MonthlyActivity] = []
    current = now.date().replace(day=1)
    for index in range(12):
        data = user.get(f"m{index}")
        if not isinstance(data, dict):
            raise ValueError(f"Monthly activity m{index} was missing")
        values = {
            "commits": data.get("totalCommitContributions"),
            "issues": data.get("totalIssueContributions"),
            "pull_requests": data.get("totalPullRequestContributions"),
            "reviews": data.get("totalPullRequestReviewContributions"),
            "repositories": data.get("totalRepositoryContributions"),
            "private": data.get("restrictedContributionsCount"),
            "total": data.get("contributionCalendar", {}).get("totalContributions"),
        }
        if any(not isinstance(value, int) or value < 0 for value in values.values()):
            raise ValueError(f"Monthly activity m{index} contained invalid counts")
        typed_total = sum(values[key] for key in ("commits", "issues", "pull_requests", "reviews", "repositories", "private"))
        if typed_total != values["total"]:
            raise ValueError(f"Monthly activity m{index} did not reconcile: {typed_total} != {values['total']}")
        months.append(MonthlyActivity(shift_month(current, -index), **values))
    return tuple(months)


def fetch_snapshot(token: str, now: dt.datetime) -> Snapshot:
    contribution_source = request_text(CONTRIBUTIONS_URL)
    user_source = request_text(USER_URL)
    repositories_source = request_text(REPOSITORIES_URL)
    graphql_source = request_text(GRAPHQL_URL, token=token, payload={"query": monthly_query(now)})

    rolling_total, days = parse_contributions(contribution_source)
    profile = parse_profile_facts(user_source)
    repository = parse_featured_repository(repositories_source)
    months = parse_monthly_activity(graphql_source, now)
    return Snapshot(rolling_total, days, profile, repository, months, now.date())


def plural(count: int, singular: str, plural_form: str | None = None) -> str:
    return singular if count == 1 else (plural_form or f"{singular}s")


def format_date(value: dt.date | dt.datetime, include_year: bool = True) -> str:
    pattern = "%B %d, %Y" if include_year else "%B %d"
    return value.strftime(pattern).replace(" 0", " ")


def contribution_metrics(days: tuple[ContributionDay, ...]) -> dict[str, Any]:
    active = [day for day in days if day.count > 0]
    longest = current = 0
    previous: dt.date | None = None
    for day in active:
        current = current + 1 if previous and (day.date - previous).days == 1 else 1
        longest = max(longest, current)
        previous = day.date
    busiest_day = max(days, key=lambda day: (day.count, day.date))
    month_totals: dict[dt.date, int] = {}
    for day in days:
        month = day.date.replace(day=1)
        month_totals[month] = month_totals.get(month, 0) + day.count
    busiest_month, busiest_month_total = max(month_totals.items(), key=lambda item: (item[1], item[0]))
    return {
        "active_days": len(active),
        "longest_streak": longest,
        "busiest_day": busiest_day,
        "busiest_month": busiest_month,
        "busiest_month_total": busiest_month_total,
        "average": (sum(day.count for day in active) / len(active)) if active else 0,
    }


def render_facts(profile: ProfileFacts) -> str:
    return "\n".join([
        '          <ul class="profile-facts" aria-label="GitHub profile facts">',
        f'            <li><strong>{profile.public_repositories}</strong><span>public repositories</span></li>',
        f'            <li><strong>{profile.member_since}</strong><span>GitHub member since</span></li>',
        "          </ul>",
    ])


def render_repository(repository: RepositoryFacts, public_count: int) -> str:
    return "\n".join([
        '          <article class="repository-card">',
        '            <header class="repository-header">',
        f'              <h3><a href="{html.escape(repository.url, quote=True)}">{html.escape(repository.name)}</a></h3>',
        f'              <span class="repository-count">1 of {public_count} public</span>',
        "            </header>",
        f'            <p>{html.escape(repository.description)}</p>',
        '            <footer class="repository-meta">',
        f'              <span><i aria-hidden="true"></i>{html.escape(repository.language)}</span>',
        f'              <span>Updated <time datetime="{repository.updated_at.date().isoformat()}">{format_date(repository.updated_at)}</time></span>',
        "            </footer>",
        "          </article>",
    ])


def calendar_weeks(days: tuple[ContributionDay, ...]) -> tuple[list[dt.date], dict[dt.date, ContributionDay]]:
    by_date = {day.date: day for day in days}
    start = days[0].date - dt.timedelta(days=(days[0].date.weekday() + 1) % 7)
    end = days[-1].date + dt.timedelta(days=(5 - days[-1].date.weekday()) % 7)
    weeks = [start + dt.timedelta(weeks=index) for index in range((end - start).days // 7 + 1)]
    return weeks, by_date


def month_headers(weeks: list[dt.date]) -> list[tuple[str, int]]:
    groups: list[tuple[str, int]] = []
    for week in weeks:
        label = calendar.month_abbr[week.month]
        if groups and groups[-1][0] == label:
            groups[-1] = (label, groups[-1][1] + 1)
        else:
            groups.append((label, 1))
    return groups


def render_contributions(snapshot: Snapshot) -> str:
    metrics = contribution_metrics(snapshot.days)
    weeks, by_date = calendar_weeks(snapshot.days)
    busiest_day: ContributionDay = metrics["busiest_day"]
    lines = [
        '          <div class="contribution-heading">',
        f'            <p><strong>{snapshot.rolling_total:,}</strong><span>contributions in the last year</span></p>',
        f'            <p class="updated-at">Updated <time datetime="{snapshot.updated.isoformat()}">{format_date(snapshot.updated)}</time></p>',
        "          </div>",
        '          <dl class="map-insights">',
        f'            <div><dt>Active days</dt><dd>{metrics["active_days"]}</dd></div>',
        f'            <div><dt>Longest streak</dt><dd>{metrics["longest_streak"]} {plural(metrics["longest_streak"], "day")}</dd></div>',
        f'            <div><dt>Busiest day</dt><dd>{busiest_day.count} on {format_date(busiest_day.date, False)}</dd></div>',
        f'            <div><dt>Busiest month</dt><dd>{metrics["busiest_month_total"]:,} in {metrics["busiest_month"].strftime("%B")}</dd></div>',
        f'            <div><dt>Per active day</dt><dd>{metrics["average"]:.1f} average</dd></div>',
        "          </dl>",
        '          <div class="contribution-scroll" tabindex="0" aria-label="Scrollable contribution calendar">',
        '            <table class="contribution-calendar">',
        '              <caption class="sr-only">Rolling-year GitHub contribution calendar</caption>',
        '              <thead><tr><th class="weekday"><span class="sr-only">Day of week</span></th>',
    ]
    lines.extend(f'                <th colspan="{span}">{label}</th>' for label, span in month_headers(weeks))
    lines.append("              </tr></thead><tbody>")
    weekday_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    visible = {1: "Mon", 3: "Wed", 5: "Fri"}
    for weekday in range(7):
        lines.extend([
            "              <tr>",
            f'                <th class="weekday" scope="row"><span aria-hidden="true">{visible.get(weekday, "")}</span><span class="sr-only">{weekday_names[weekday]}</span></th>',
        ])
        for week in weeks:
            day = by_date.get(week + dt.timedelta(days=weekday))
            if day is None:
                lines.append('                <td aria-hidden="true"></td>')
                continue
            unit = plural(day.count, "contribution")
            label = html.escape(f"{day.count} {unit} on {format_date(day.date)}", quote=True)
            lines.append(f'                <td><span class="contribution-day" data-level="{day.level}" title="{label}"><span class="sr-only">{label}</span></span></td>')
        lines.append("              </tr>")
    lines.extend([
        "              </tbody></table>",
        "          </div>",
        '          <div class="contribution-legend" aria-label="Contribution intensity from less to more">',
        '            <span>Less</span><i aria-hidden="true"></i><i class="level-1" aria-hidden="true"></i><i class="level-2" aria-hidden="true"></i><i class="level-3" aria-hidden="true"></i><i class="level-4" aria-hidden="true"></i><span>More</span>',
        "          </div>",
    ])
    return "\n".join(lines)


def render_activity_item(activity: MonthlyActivity) -> str:
    metrics = [
        ("Commits", activity.commits),
        ("Pull requests", activity.pull_requests),
        ("Reviews", activity.reviews),
        ("Issues", activity.issues),
        ("Repositories created", activity.repositories),
        ("Private contributions", activity.private),
    ]
    lines = [
        '            <li class="activity-item">',
        '              <span class="activity-marker" aria-hidden="true"></span>',
        '              <article>',
        '                <header class="activity-header">',
        f'                  <h3>{activity.month.strftime("%B %Y")}</h3>',
        f'                  <p><strong>{activity.total:,}</strong> {plural(activity.total, "contribution")}</p>',
        "                </header>",
        '                <dl class="activity-metrics">',
    ]
    for label, value in metrics:
        zero = " is-zero" if value == 0 else ""
        lines.append(f'                  <div class="activity-metric{zero}"><dt>{label}</dt><dd>{value:,}</dd></div>')
    lines.extend(["                </dl>", "              </article>", "            </li>"])
    return "\n".join(lines)


def render_activity(months: tuple[MonthlyActivity, ...]) -> str:
    visible = months[:3]
    earlier = months[3:]
    lines = ['          <ol class="activity-list activity-list-primary">']
    lines.extend(render_activity_item(month) for month in visible)
    lines.append("          </ol>")
    lines.extend([
        '          <details class="activity-more">',
        f'            <summary>Show {len(earlier)} earlier months</summary>',
        '            <ol class="activity-list">',
    ])
    lines.extend(render_activity_item(month) for month in earlier)
    lines.extend(["            </ol>", "          </details>"])
    return "\n".join(lines)


def replace_region(source: str, start: str, end: str, replacement: str) -> str:
    if source.count(start) != 1 or source.count(end) != 1:
        raise ValueError(f"Expected one generated region bounded by {start} and {end}")
    before, remainder = source.split(start, 1)
    _, after = remainder.split(end, 1)
    return f"{before}{start}\n{replacement}\n{end}{after}"


def render_index(source: str, snapshot: Snapshot) -> str:
    replacements = {
        "facts": render_facts(snapshot.profile),
        "repository": render_repository(snapshot.repository, snapshot.profile.public_repositories),
        "contributions": render_contributions(snapshot),
        "activity": render_activity(snapshot.months),
    }
    rendered = source
    for name, replacement in replacements.items():
        rendered = replace_region(rendered, *REGIONS[name], replacement)
    return rendered


def atomic_write(path: Path, content: str) -> None:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as handle:
            handle.write(content)
            temporary = Path(handle.name)
        temporary.replace(path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=Path("index.html"))
    parser.add_argument("--dry-run", action="store_true", help="validate live data without writing the page")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN is required for monthly aggregate data")
    now = dt.datetime.now(dt.timezone.utc)
    snapshot = fetch_snapshot(token, now)
    current = args.index.read_text(encoding="utf-8")
    rendered = render_index(current, snapshot)

    if args.dry_run:
        state = "current" if rendered == current else "would change"
        print(f"Validated {len(snapshot.days)} days, {snapshot.rolling_total:,} rolling contributions, 12 monthly summaries, and the approved featured repository; index {state}.")
        return 0
    if rendered != current:
        atomic_write(args.index, rendered)
        print(f"Updated index with {snapshot.rolling_total:,} rolling contributions and 12 reconciled monthly summaries.")
    else:
        print("Index is already current.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"Profile update failed: {error}", file=sys.stderr)
        raise SystemExit(1)
