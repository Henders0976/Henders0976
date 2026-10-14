#!/usr/bin/env python3
"""Gera os cartões SVG do perfil a partir da API GraphQL do GitHub.

Uso: gen_cards.py [pasta_de_saida] [--sample]
Sem --sample, lê GITHUB_TOKEN do ambiente.
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from collections import defaultdict
from html import escape

USER = os.environ.get("GH_USER", "Henders0976")
BG, BORDER, TITLE, ACCENT, TEXT, MUTED = "#0D1117", "#4C1D95", "#A78BFA", "#7C3AED", "#C9D1D9", "#8B949E"
PALETTE = ["#A78BFA", "#7C3AED", "#6366F1", "#818CF8", "#C4B5FD", "#4C1D95"]
FONT = "Montserrat, 'Segoe UI', Arial, sans-serif"

LABELS = {
    "pt": dict(stats="Estatísticas", commits="Commits no último ano", prs="Pull requests", issues="Issues",
               stars="Estrelas recebidas", repos="Repositórios públicos", streak="Sequência de contribuições",
               total="Contribuições", year="no último ano", current="Sequência atual", longest="Maior sequência",
               days="dias", langs="Linguagens mais usadas", activity="Atividade de contribuição", trophy="Troféus",
               trophies=dict(commits="Commits", repos="Repositórios", stars="Estrelas", followers="Seguidores",
                             prs="Pull requests", streak="Maior sequência")),
    "en": dict(stats="Stats", commits="Commits in the last year", prs="Pull requests", issues="Issues",
               stars="Stars received", repos="Public repositories", streak="Contribution streak",
               total="Contributions", year="in the last year", current="Current streak", longest="Longest streak",
               days="days", langs="Top languages", activity="Contribution activity", trophy="Trophies",
               trophies=dict(commits="Commits", repos="Repositories", stars="Stars", followers="Followers",
                             prs="Pull requests", streak="Longest streak")),
}

QUERY = """query($u:String!){user(login:$u){followers{totalCount}
 repositories(ownerAffiliation:OWNER,privacy:PUBLIC,isFork:false,first:100){totalCount nodes{stargazerCount
  languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}
 pullRequests{totalCount} issues{totalCount}
 contributionsCollection{totalCommitContributions contributionCalendar{totalContributions
  weeks{contributionDays{date contributionCount}}}}}}"""


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"u": USER}}).encode(),
        headers={"Authorization": "bearer " + os.environ["GITHUB_TOKEN"], "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if "errors" in body or not body.get("data", {}).get("user"):
        sys.exit("GraphQL error: " + json.dumps(body)[:500])
    return body["data"]["user"]


def sample():
    today = dt.date.today()
    days = [{"date": (today - dt.timedelta(days=364 - i)).isoformat(),
             "contributionCount": (i * 7 % 11) if i % 9 else 0} for i in range(365)]
    weeks = [{"contributionDays": days[i:i + 7]} for i in range(0, 365, 7)]
    langs = [("HTML", 7000), ("C++", 2500), ("Dart", 500)]
    return {"followers": {"totalCount": 2},
            "repositories": {"totalCount": 2, "nodes": [
                {"stargazerCount": 1,
                 "languages": {"edges": [{"size": s, "node": {"name": n}} for n, s in langs]}}]},
            "pullRequests": {"totalCount": 3}, "issues": {"totalCount": 1},
            "contributionsCollection": {"totalCommitContributions": 120, "contributionCalendar": {
                "totalContributions": sum(d["contributionCount"] for d in days), "weeks": weeks}}}


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] else 0
        longest = max(longest, run)
    cur, seq = 0, days[:]
    if seq and not seq[-1]["contributionCount"]:
        seq = seq[:-1]  # o dia de hoje ainda pode estar zerado
    for d in reversed(seq):
        if not d["contributionCount"]:
            break
        cur += 1
    return cur, longest


def card(w, h, title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="{escape(title)}"><title>{escape(title)}</title>'
            f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>'
            f'<g font-family="{FONT}">'
            f'<text x="24" y="34" font-size="16" font-weight="700" fill="{TITLE}">{escape(title)}</text>{body}</g></svg>')


def t(x, y, s, size=13, fill=TEXT, weight=400, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}">{escape(str(s))}</text>')


def stats_card(L, v):
    rows = [(L["commits"], v["commits"]), (L["prs"], v["prs"]), (L["issues"], v["issues"]),
            (L["stars"], v["stars"]), (L["repos"], v["repos"])]
    body = "".join(t(24, 66 + i * 24, k) + t(376, 66 + i * 24, n, weight=700, fill=TITLE, anchor="end")
                   for i, (k, n) in enumerate(rows))
    return card(400, 190, L["stats"], body)


def streak_card(L, v):
    cols = [(L["total"], v["total"], L["year"]), (L["current"], v["cur"], L["days"]),
            (L["longest"], v["longest"], L["days"])]
    body = ""
    for i, (k, n, sub) in enumerate(cols):
        x = 24 + 120 * i + 56
        body += t(x, 98, n, size=28, weight=700, fill=TITLE if i == 1 else TEXT, anchor="middle")
        body += t(x, 124, k, size=11, anchor="middle") + t(x, 142, sub, size=10, fill=MUTED, anchor="middle")
    return card(400, 190, L["streak"], body)


def langs_card(L, langs):
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]
    bars, legend, x = "", "", 24.0
    for i, (name, size) in enumerate(top):
        wbar = 352 * size / total
        bars += f'<rect x="{x:.1f}" y="52" width="{wbar:.1f}" height="10" fill="{PALETTE[i]}"/>'
        x += wbar
        cx, cy = 24 + 180 * (i % 2), 98 + 28 * (i // 2)
        legend += (f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{PALETTE[i]}"/>'
                   + t(cx + 18, cy, f"{name}  {100 * size / total:.1f}%", size=12))
    clip = '<clipPath id="c"><rect x="24" y="52" width="352" height="10" rx="5"/></clipPath>'
    return card(400, 190, L["langs"], f'{clip}<g clip-path="url(#c)">{bars}</g>{legend}')


def trophies(L, v):
    items = [("commits", v["commits"]), ("repos", v["repos"]), ("stars", v["stars"]),
             ("followers", v["followers"]), ("prs", v["prs"]), ("streak", v["longest"])]
    body = ""
    for i, (key, n) in enumerate(items):
        x = 24 + i * 134
        body += (f'<rect x="{x}" y="50" width="122" height="70" rx="8" fill="#161B22" stroke="{BORDER}"/>'
                 f'<circle cx="{x + 61}" cy="66" r="4" fill="{ACCENT}"/>'
                 + t(x + 61, 94, n, size=20, weight=700, fill=TITLE, anchor="middle")
                 + t(x + 61, 111, L["trophies"][key], size=10, fill=MUTED, anchor="middle"))
    return card(840, 140, L["trophy"], body)


def activity(L, days):
    weeks = defaultdict(int)
    for i, d in enumerate(days):
        weeks[i // 7] += d["contributionCount"]
    vals = [weeks[i] for i in sorted(weeks)]
    n, mx = len(vals), max(vals) or 1
    x0, x1, y0, y1 = 44, 816, 190, 60
    pts = [(x0 + i * (x1 - x0) / max(n - 1, 1), y0 - v / mx * (y0 - y1)) for i, v in enumerate(vals)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    body = (f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{ACCENT}" stop-opacity="0.55"/>'
            f'<stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></linearGradient></defs>'
            f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="#30363D"/>'
            f'<polygon points="{x0},{y0} {line} {x1},{y0}" fill="url(#g)"/>'
            f'<polyline points="{line}" fill="none" stroke="{TITLE}" stroke-width="2" stroke-linejoin="round"/>')
    last = None
    for i in range(0, len(days), 7):
        m = days[i]["date"][:7]
        if m != last:
            label = dt.date.fromisoformat(days[i]["date"]).strftime("%b")
            body += t(pts[i // 7][0], 212, label, size=10, fill=MUTED, anchor="middle")
            last = m
    return card(840, 226, L["activity"], body)


def main():
    out = next((a for a in sys.argv[1:] if not a.startswith("--")), "dist")
    u = sample() if "--sample" in sys.argv else fetch()
    cal = u["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    cur, longest = streaks(days)
    langs = defaultdict(int)
    for r in u["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] += e["size"]
    v = dict(commits=u["contributionsCollection"]["totalCommitContributions"], prs=u["pullRequests"]["totalCount"],
             issues=u["issues"]["totalCount"], stars=sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
             repos=u["repositories"]["totalCount"], followers=u["followers"]["totalCount"],
             total=cal["totalContributions"], cur=cur, longest=longest)
    os.makedirs(out, exist_ok=True)
    for lang, L in LABELS.items():
        cards = (("stats", stats_card(L, v)), ("streak", streak_card(L, v)), ("langs", langs_card(L, langs)),
                 ("trophies", trophies(L, v)), ("activity", activity(L, days)))
        for name, svg in cards:
            with open(os.path.join(out, f"github-{name}.{lang}.svg"), "w", encoding="utf8") as f:
                f.write(svg)


if __name__ == "__main__":
    main()
