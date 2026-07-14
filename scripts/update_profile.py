#!/usr/bin/env python3
"""Generate a sanitized, factual GitHub profile snapshot for the static page."""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
from dataclasses import dataclass
import html
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import tempfile
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse
from urllib.request import Request, urlopen

USERNAME = "mahmadnet"
CONTRIBUTIONS_URL = f"https://github.com/users/{USERNAME}/contributions"
ACTIVITY_URL = f"https://github.com/{USERNAME}?action=show&controller=profiles&tab=contributions&user_id={USERNAME}"
ACTIVITY_MONTHS = 12
USER_AGENT = "mahmadnet.github.io profile updater"

REGIONS = {
    "about_summary": ("<!-- PROFILE_DATA:ABOUT_SUMMARY:START -->", "<!-- PROFILE_DATA:ABOUT_SUMMARY:END -->"),
    "contributions": ("<!-- PROFILE_DATA:CONTRIBUTIONS:START -->", "<!-- PROFILE_DATA:CONTRIBUTIONS:END -->"),
    "activity": ("<!-- PROFILE_DATA:ACTIVITY:START -->", "<!-- PROFILE_DATA:ACTIVITY:END -->"),
}


@dataclass(frozen=True)
class ContributionDay:
    date: dt.date
    level: int
    count: int



@dataclass(frozen=True)
class ActivityEvent:
    month: dt.date
    kind: str
    count: int
    repository_count: int | None = None
    date_label: str | None = None


@dataclass(frozen=True)
class Snapshot:
    rolling_total: int
    days: tuple[ContributionDay, ...]
    events: tuple[ActivityEvent, ...]
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


class ActivityFragmentParser(HTMLParser):
    """Extract only month-level contribution summaries from GitHub's public fragment."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.scope_depth = 0
        self.month_depth = 0
        self.month_parts: list[str] = []
        self.item_depth = 0
        self.summary_depth = 0
        self.summary_parts: list[str] = []
        self.aggregate_depth = 0
        self.aggregate_parts: list[str] = []
        self.date_depth = 0
        self.date_parts: list[str] = []
        self.raw_items: list[tuple[str, str, str]] = []
        self.pagination_actions: list[str] = []

    @staticmethod
    def classes(attrs: dict[str, str | None]) -> set[str]:
        return set((attrs.get("class") or "").split())

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        classes = self.classes(values)
        if tag == "form" and "js-show-more-timeline-form" in classes:
            action = values.get("action")
            if action:
                self.pagination_actions.append(action)
        if self.scope_depth:
            self.scope_depth += 1
        elif tag == "div" and "contribution-activity-listing" in classes:
            self.scope_depth = 1
        else:
            return
        if self.item_depth:
            self.item_depth += 1
            if self.summary_depth:
                self.summary_depth += 1
            elif tag == "summary":
                self.summary_depth = 1
            if self.aggregate_depth:
                self.aggregate_depth += 1
            elif tag == "span" and {"f4", "lh-condensed"}.issubset(classes):
                self.aggregate_depth = 1
            if self.date_depth:
                self.date_depth += 1
            elif tag == "span" and {"float-right", "f6", "color-fg-muted"}.issubset(classes):
                self.date_depth = 1
        elif tag == "div" and "TimelineItem" in classes:
            self.item_depth = 1
            self.summary_parts = []
            self.aggregate_parts = []
            self.date_parts = []
        if self.month_depth:
            self.month_depth += 1
        elif tag == "h3":
            self.month_depth = 1
            self.month_parts = []

    def handle_data(self, data: str) -> None:
        if not self.scope_depth:
            return
        if self.month_depth:
            self.month_parts.append(data)
        if self.summary_depth:
            self.summary_parts.append(data)
        if self.aggregate_depth:
            self.aggregate_parts.append(data)
        if self.date_depth:
            self.date_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self.scope_depth:
            return
        if self.month_depth:
            self.month_depth -= 1
        if self.summary_depth:
            self.summary_depth -= 1
        if self.aggregate_depth:
            self.aggregate_depth -= 1
        if self.date_depth:
            self.date_depth -= 1
        if self.item_depth:
            self.item_depth -= 1
            if self.item_depth == 0:
                self.raw_items.append((
                    normalize_text(self.summary_parts),
                    normalize_text(self.aggregate_parts),
                    normalize_text(self.date_parts),
                ))
        self.scope_depth -= 1


def normalize_text(parts: list[str] | str) -> str:
    value = " ".join(parts) if isinstance(parts, list) else parts
    return " ".join(value.split())

def request_text(url: str, *, fragment: bool = False) -> str:
    headers = {
        "Accept": "application/vnd.github+json, text/html",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if fragment:
        headers["X-Requested-With"] = "XMLHttpRequest"
    request = Request(url, headers=headers)
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



def shift_month(month: dt.date, offset: int) -> dt.date:
    index = month.year * 12 + month.month - 1 + offset
    return dt.date(index // 12, index % 12 + 1, 1)


def activity_months(now: dt.datetime) -> tuple[dt.date, ...]:
    current = now.date().replace(day=1)
    return tuple(shift_month(current, -index) for index in range(ACTIVITY_MONTHS))


def parse_month_label(parts: list[str]) -> dt.date:
    label = normalize_text(parts)
    try:
        return dt.datetime.strptime(label, "%B %Y").date().replace(day=1)
    except ValueError as error:
        raise ValueError(f"Invalid activity month label: {label!r}") from error


def parse_activity_item(month: dt.date, summary: str, aggregate: str, date_label: str) -> ActivityEvent:
    patterns = (
        (r"Created ([\d,]+) commits? in ([\d,]+) repositor(?:y|ies)", "commits", True),
        (r"Created ([\d,]+) repositor(?:y|ies)", "repositories", False),
        (r"Opened ([\d,]+) (?:other )?pull requests?(?: in ([\d,]+) repositor(?:y|ies))?", "pull_requests", True),
        (r"Reviewed ([\d,]+) (?:other )?pull requests?(?: in ([\d,]+) repositor(?:y|ies))?", "reviews", True),
        (r"Opened ([\d,]+) (?:other )?issues?(?: in ([\d,]+) repositor(?:y|ies))?", "issues", True),
    )
    for pattern, kind, has_repository_count in patterns:
        match = re.fullmatch(pattern, summary)
        if match:
            count = int(match.group(1).replace(",", ""))
            repository_count = (
                int(match.group(2).replace(",", ""))
                if has_repository_count and match.group(2)
                else None
            )
            return ActivityEvent(month, kind, count, repository_count)
    aggregate_match = re.fullmatch(r"([\d,]+) contributions? in private repositories", aggregate)
    if aggregate_match and not summary:
        count = int(aggregate_match.group(1).replace(",", ""))
        return ActivityEvent(month, "contributions", count, date_label=date_label or None)
    detail = summary or aggregate or "(empty event)"
    raise ValueError(f"Unsupported activity event: {detail}")


def expected_pagination_url(action: str, expected_month: dt.date) -> str:
    url = urljoin("https://github.com", action)
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    month_end = dt.date(expected_month.year, expected_month.month, calendar.monthrange(expected_month.year, expected_month.month)[1])
    expected = {
        "tab": ["overview"],
        "from": [expected_month.isoformat()],
        "to": [month_end.isoformat()],
        "include_header": ["no"],
    }
    if parsed.scheme != "https" or parsed.netloc != "github.com" or parsed.path != f"/{USERNAME}" or query != expected:
        raise ValueError("Activity pagination URL failed validation")
    return url


def parse_activity_fragment(source: str, expected_month: dt.date, expected_previous: dt.date | None) -> tuple[tuple[ActivityEvent, ...], str | None]:
    parser = ActivityFragmentParser()
    parser.feed(source)
    if parser.scope_depth or parser.item_depth or parser.summary_depth or parser.aggregate_depth:
        raise ValueError("Activity fragment contains unbalanced HTML")
    month = parse_month_label(parser.month_parts)
    if month != expected_month:
        raise ValueError(f"Expected activity for {expected_month:%B %Y}, received {month:%B %Y}")
    events = tuple(parse_activity_item(month, *item) for item in parser.raw_items)
    if expected_previous is None:
        next_url = None
    else:
        if len(parser.pagination_actions) != 1:
            raise ValueError("Activity fragment did not contain exactly one pagination action")
        next_url = expected_pagination_url(parser.pagination_actions[0], expected_previous)
    return events, next_url


def reconcile_activity(events: tuple[ActivityEvent, ...], days: tuple[ContributionDay, ...], months: tuple[dt.date, ...]) -> None:
    calendar_totals = {month: 0 for month in months}
    for day in days:
        month = day.date.replace(day=1)
        if month in calendar_totals:
            calendar_totals[month] += day.count
    event_totals = {month: 0 for month in months}
    for event in events:
        if event.month not in event_totals or event.count <= 0:
            raise ValueError("Activity event fell outside the requested window or had an invalid count")
        event_totals[event.month] += event.count
    for month in months:
        if event_totals[month] != calendar_totals[month]:
            raise ValueError(f"Activity for {month:%B %Y} did not reconcile: {event_totals[month]} != {calendar_totals[month]}")


def fetch_activity(now: dt.datetime, days: tuple[ContributionDay, ...]) -> tuple[ActivityEvent, ...]:
    months = activity_months(now)
    url = ACTIVITY_URL
    events: list[ActivityEvent] = []
    for index, month in enumerate(months):
        source = request_text(url, fragment=True)
        previous = months[index + 1] if index + 1 < len(months) else None
        month_events, url = parse_activity_fragment(source, month, previous)
        events.extend(month_events)
    result = tuple(events)
    reconcile_activity(result, days, months)
    return result


def fetch_snapshot(now: dt.datetime) -> Snapshot:
    contribution_source = request_text(CONTRIBUTIONS_URL)
    rolling_total, days = parse_contributions(contribution_source)
    events = fetch_activity(now, days)
    return Snapshot(rolling_total, days, events, now.date())


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



def render_about_summary(snapshot: Snapshot) -> str:
    metrics = contribution_metrics(snapshot.days)
    active_days = metrics["active_days"]
    longest_streak = metrics["longest_streak"]
    return (
        f'            <p class="about-summary"><strong>{snapshot.rolling_total:,}</strong> '
        f'{plural(snapshot.rolling_total, "contribution")} in the last year across '
        f'<strong>{active_days}</strong> active {plural(active_days, "day")}, including '
        f'a <strong>{longest_streak}-day</strong> longest streak.</p>'
    )

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


def activity_summary(event: ActivityEvent) -> str:
    if event.kind == "commits":
        return (
            f"Created {event.count:,} {plural(event.count, 'commit')} in "
            f"{event.repository_count:,} "
            f"{plural(event.repository_count or 0, 'repository', 'repositories')}"
        )
    if event.kind == "repositories":
        return f"Created {event.count:,} {plural(event.count, 'repository', 'repositories')}"
    if event.kind in {"pull_requests", "reviews", "issues"}:
        verb = "Reviewed" if event.kind == "reviews" else "Opened"
        noun = "issue" if event.kind == "issues" else "pull request"
        summary = f"{verb} {event.count:,} {plural(event.count, noun)}"
        if event.repository_count:
            summary += (
                f" in {event.repository_count:,} "
                f"{plural(event.repository_count, 'repository', 'repositories')}"
            )
        return summary
    if event.kind == "contributions":
        return f"{event.count:,} {plural(event.count, 'contribution')}"
    raise ValueError(f"Unsupported activity kind: {event.kind}")


def render_activity_list(events: tuple[ActivityEvent, ...], indent: str = "          ") -> list[str]:
    lines = [f'{indent}<ol class="activity-timeline">']
    current_month: dt.date | None = None
    for event in events:
        if event.month != current_month:
            current_month = event.month
            lines.extend([f'{indent}  <li class="activity-month">', f'{indent}    <h3>{event.month.strftime("%B %Y")}</h3>', f'{indent}  </li>'])
        lines.extend([
            f'{indent}  <li class="activity-event">',
            f'{indent}    <span class="activity-marker" aria-hidden="true"></span>',
            f'{indent}    <p>{html.escape(activity_summary(event))}</p>',
        ])
        if event.date_label:
            lines.append(f'{indent}    <span class="activity-date">{html.escape(event.date_label)}</span>')
        lines.append(f'{indent}  </li>')
    lines.append(f"{indent}</ol>")
    return lines


def render_activity(events: tuple[ActivityEvent, ...]) -> str:
    if not events:
        return '          <p class="data-placeholder">No contribution activity in this period.</p>'
    visible = events[:6]
    earlier = events[6:]
    lines = render_activity_list(visible)
    if earlier:
        lines.extend([
            '          <details class="activity-more">',
            '            <summary>Show more activity</summary>',
            *render_activity_list(earlier, "            "),
            "          </details>",
        ])
    return "\n".join(lines)


def replace_region(source: str, start: str, end: str, replacement: str) -> str:
    if source.count(start) != 1 or source.count(end) != 1:
        raise ValueError(f"Expected one generated region bounded by {start} and {end}")
    before, remainder = source.split(start, 1)
    _, after = remainder.split(end, 1)
    return f"{before}{start}\n{replacement}\n{end}{after}"


def render_index(source: str, snapshot: Snapshot) -> str:
    replacements = {
        "about_summary": render_about_summary(snapshot),
        "contributions": render_contributions(snapshot),
        "activity": render_activity(snapshot.events),
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

    now = dt.datetime.now(dt.timezone.utc)
    snapshot = fetch_snapshot(now)
    current = args.index.read_text(encoding="utf-8")
    rendered = render_index(current, snapshot)

    if args.dry_run:
        state = "current" if rendered == current else "would change"
        print(f"Validated {len(snapshot.days)} days, {snapshot.rolling_total:,} rolling contributions, 12 months of sanitized timeline activity; index {state}.")
        return 0
    if rendered != current:
        atomic_write(args.index, rendered)
        print(f"Updated index with {snapshot.rolling_total:,} rolling contributions and reconciled timeline activity.")
    else:
        print("Index is already current.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Profile update failed: {error}", file=sys.stderr)
        raise SystemExit(1)
