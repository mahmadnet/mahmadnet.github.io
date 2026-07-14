#!/usr/bin/env python3
"""Refresh sanitized public GitHub activity in index.html without dependencies."""
from __future__ import annotations
import argparse, calendar, datetime as dt, html, json, re, sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

USER="mahmadnet"
CONTRIB=f"https://github.com/users/{USER}/contributions"
EVENTS=f"https://api.github.com/users/{USER}/events/public?per_page=100&page={{}}"
CS="<!-- PROFILE_DATA:CONTRIBUTIONS:START -->"; CE="<!-- PROFILE_DATA:CONTRIBUTIONS:END -->"
AS="<!-- PROFILE_DATA:ACTIVITY:START -->"; AE="<!-- PROFILE_DATA:ACTIVITY:END -->"

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.heading=[]; self.in_heading=False
        self.days=[]; self.tips={}; self.tip=None; self.tip_text=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="h2" and a.get("id")=="js-contribution-activity-description": self.in_heading=True
        elif tag=="td" and a.get("data-date"):
            self.days.append({"date":a["data-date"],"level":int(a.get("data-level","0")),"id":a.get("id","")})
        elif tag=="tool-tip" and a.get("for"): self.tip=a["for"]; self.tip_text=[]
    def handle_data(self,data):
        if self.in_heading:self.heading.append(data)
        if self.tip:self.tip_text.append(data)
    def handle_endtag(self,tag):
        if tag=="h2":self.in_heading=False
        elif tag=="tool-tip" and self.tip:
            self.tips[self.tip]=" ".join(self.tip_text).strip(); self.tip=None

def fetch(url):
    req=Request(url,headers={"Accept":"application/vnd.github+json, text/html","User-Agent":"mahmadnet.github.io profile updater","X-GitHub-Api-Version":"2022-11-28"})
    with urlopen(req,timeout=30) as response:
        if response.status!=200: raise RuntimeError(f"GitHub returned HTTP {response.status}")
        return response.read().decode()

def fetch_events():
    result=[]
    for page in range(1,4):
        data=json.loads(fetch(EVENTS.format(page)))
        if not isinstance(data,list):raise ValueError("Events response was not a list")
        result.extend(data)
        if len(data)<100:break
    return result

def parse_contributions(source):
    p=Parser(); p.feed(source); heading=" ".join(" ".join(p.heading).split())
    match=re.search(r"([\d,]+)\s+contributions?",heading)
    if not match:raise ValueError("Contribution total was not found")
    total=int(match.group(1).replace(",","")); days=[]
    for raw in p.days:
        count_match=re.match(r"([\d,]+)\s+contributions?",p.tips.get(raw["id"],""))
        days.append({"date":dt.date.fromisoformat(raw["date"]),"level":raw["level"],"count":int(count_match.group(1).replace(",","")) if count_match else 0})
    days.sort(key=lambda x:x["date"]); validate(total,days); return total,days

def validate(total,days):
    dates=[x["date"] for x in days]
    if not 365<=len(days)<=371:raise ValueError(f"Expected rolling-year calendar; received {len(days)} days")
    if len(set(dates))!=len(dates) or any((b-a).days!=1 for a,b in zip(dates,dates[1:])):raise ValueError("Calendar dates are not unique and consecutive")
    if any(x["level"] not in range(5) for x in days):raise ValueError("Invalid contribution level")
    if sum(x["count"] for x in days)!=total:raise ValueError("Cell counts do not match total")

def label(day):
    date=day["date"].strftime("%B %d, %Y").replace(" 0"," "); unit="contribution" if day["count"]==1 else "contributions"
    return f'{day["count"]} {unit} on {date}'

def render_contributions(total,days,updated):
    by_date={x["date"]:x for x in days}; start=days[0]["date"]-dt.timedelta(days=(days[0]["date"].weekday()+1)%7); end=days[-1]["date"]+dt.timedelta(days=(5-days[-1]["date"].weekday())%7)
    weeks=[start+dt.timedelta(weeks=i) for i in range((end-start).days//7+1)]; groups=[]
    for week in weeks:
        name=calendar.month_abbr[week.month]
        if groups and groups[-1][0]==name:groups[-1]=(name,groups[-1][1]+1)
        else:groups.append((name,1))
    out=['              <div class="contribution-summary">',f'                <p><strong>{total:,}</strong> contributions in the last year</p>',f'                <p class="updated-at">Updated <time datetime="{updated.isoformat()}">{updated.strftime("%B %d, %Y").replace(" 0"," ")}</time></p>','              </div>','              <div class="contribution-scroll" tabindex="0" aria-label="Scrollable contribution calendar">','                <table class="contribution-calendar">','                  <caption class="sr-only">Contribution calendar for the last year</caption>','                  <thead><tr><th class="weekday"><span class="sr-only">Day of week</span></th>']
    out += [f'                    <th colspan="{span}">{name}</th>' for name,span in groups]; out += ['                  </tr></thead><tbody>']
    names=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']; visible={1:'Mon',3:'Wed',5:'Fri'}
    for weekday in range(7):
        out += ['                  <tr>',f'                    <th class="weekday" scope="row"><span aria-hidden="true">{visible.get(weekday,"")}</span><span class="sr-only">{names[weekday]}</span></th>']
        for week in weeks:
            day=by_date.get(week+dt.timedelta(days=weekday))
            if not day:out.append('                    <td aria-hidden="true"></td>');continue
            text=html.escape(label(day),quote=True); out.append(f'                    <td><span class="contribution-day" data-level="{day["level"]}" title="{text}"><span class="sr-only">{text}</span></span></td>')
        out.append('                  </tr>')
    out += ['                  </tbody></table>','              </div>','              <div class="contribution-footer"><div class="contribution-legend" aria-label="Contribution intensity from less to more">','                <span>Less</span><span class="legend-cell" aria-hidden="true"></span><span class="legend-cell level-1" aria-hidden="true"></span><span class="legend-cell level-2" aria-hidden="true"></span><span class="legend-cell level-3" aria-hidden="true"></span><span class="legend-cell level-4" aria-hidden="true"></span><span>More</span>','              </div></div>']
    return "\n".join(out)

def shift_month(date,offset):
    n=date.year*12+date.month-1+offset;return dt.date(n//12,n%12+1,1)
def plural(n,one,many=None):return one if n==1 else (many or one+'s')

def event_details(events,month):
    selected=[]
    for event in events:
        try:created=dt.datetime.fromisoformat(event["created_at"].replace("Z","+00:00"))
        except (KeyError,TypeError,ValueError):continue
        if (created.year,created.month)==(month.year,month.month):selected.append(event)
    details=[]; pushes=[x for x in selected if x.get("type")=="PushEvent"]
    if pushes:
        repos={x.get("repo",{}).get("name") for x in pushes}-{None}; details.append(f"{len(pushes)} {plural(len(pushes),'push','pushes')} across {len(repos)} public {plural(len(repos),'repository','repositories')}")
    created=[x for x in selected if x.get("type")=="CreateEvent" and x.get("payload",{}).get("ref_type")=="repository"]
    if created:details.append(f"Created {len(created)} public {plural(len(created),'repository','repositories')}")
    for ref_type,noun in [('branch','branch'),('tag','tag')]:
        count=sum(x.get("type")=="CreateEvent" and x.get("payload",{}).get("ref_type")==ref_type for x in selected)
        if count:details.append(f"Created {count} public {plural(count,noun)}")
    for kind,text in [('PullRequestEvent','pull request event'),('PullRequestReviewEvent','pull request review'),('IssuesEvent','issue event'),('IssueCommentEvent','discussion comment'),('ForkEvent','repository fork'),('WatchEvent','repository star'),('ReleaseEvent','release')]:
        count=sum(x.get("type")==kind for x in selected)
        if count:details.append(f"{count} {plural(count,text)}")
    return details

def render_activity(days,events,updated):
    counts={x["date"]:x["count"] for x in days}; current=updated.replace(day=1); out=['          <ol class="panel activity-timeline">']
    for offset in range(3):
        month=shift_month(current,-offset); next_month=shift_month(month,1); total=sum(v for d,v in counts.items() if month<=d<next_month); details=event_details(events,month)
        out += ['            <li class="activity-month">','              <span class="activity-marker" aria-hidden="true"></span>',f'              <h3>{month.strftime("%B %Y")}</h3>',f'              <p class="activity-total">{total:,} {plural(total,"contribution")}</p>']
        if details:out.append('              <ul class="activity-details">');out += [f'                <li>{html.escape(x)}</li>' for x in details];out.append('              </ul>')
        out.append('            </li>')
    out.append('          </ol>');return "\n".join(out)

def replace(source,start,end,replacement):
    if source.count(start)!=1 or source.count(end)!=1:raise ValueError(f"Expected one region bounded by {start} and {end}")
    before,rest=source.split(start,1);_,after=rest.split(end,1);return before+start+'\n'+replacement+'\n'+end+after

def render_index(source,total,days,events,updated):
    return replace(replace(source,CS,CE,render_contributions(total,days,updated)),AS,AE,render_activity(days,events,updated))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--index',type=Path,default=Path('index.html'));ap.add_argument('--dry-run',action='store_true');args=ap.parse_args()
    total,days=parse_contributions(fetch(CONTRIB));events=fetch_events();updated=dt.datetime.now(dt.timezone.utc).date();current=args.index.read_text(encoding='utf-8');rendered=render_index(current,total,days,events,updated)
    if args.dry_run:print(f"Validated {len(days)} days, {total:,} contributions, and {len(events)} public events; index {'current' if rendered==current else 'would change'}.")
    elif rendered!=current:args.index.write_text(rendered,encoding='utf-8',newline='\n');print(f"Updated index with {len(days)} days, {total:,} contributions, and {len(events)} public events.")
    else:print('Index is already current.')

if __name__=='__main__':
    try:main()
    except (OSError,RuntimeError,ValueError,json.JSONDecodeError) as error:print(f"Profile update failed: {error}",file=sys.stderr);raise SystemExit(1)
