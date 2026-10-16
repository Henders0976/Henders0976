#!/usr/bin/env python3
"""Gera os cartões SVG do perfil a partir da API GraphQL do GitHub.

Uso: gen_cards.py [pasta_de_saida] [--sample]
Sem --sample, lê GITHUB_TOKEN do ambiente.
"""
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from html import escape

USER = os.environ.get("GH_USER", "henderson-grossi")
BG, BORDER, TITLE, ACCENT, TEXT, MUTED = "#0D1117", "#4C1D95", "#A78BFA", "#7C3AED", "#C9D1D9", "#8B949E"
PALETTE = ["#A78BFA", "#7C3AED", "#6366F1", "#818CF8", "#C4B5FD", "#4C1D95"]
FONT = "Montserrat, 'Segoe UI', Arial, sans-serif"

LABELS = {
    "pt": dict(stats="Estatísticas", commits="Commits no último ano", prs="Pull requests", issues="Issues",
               stars="Estrelas recebidas", repos="Repositórios públicos", streak="Sequência de contribuições",
               total="Contribuições", year="no último ano", current="Sequência atual", longest="Maior sequência",
               days="dias", langs="Linguagens mais usadas", cal="contribuições no último ano",
               ov="Visão geral da atividade", review="Revisão de código", less="Menos", more="Mais",
               touched="Contribuiu em {n} repositórios",
               months=["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
               wd=["", "seg", "", "qua", "", "sex", ""],
               commits_short="Commits", role="Desenvolvedor Full Stack",
               panel_alt="Painel de apresentação de Henderson Lerio Grossi",
               panel=[("cmd", "whoami"), ("kv", "nome: Henderson Lerio Grossi"),
                      ("kv", "curso: Análise e Desenvolvimento de Sistemas, UNIFEOB"),
                      ("kv", "período: noturno"), ("kv", "foco: desenvolvimento full stack"),
                      ("cmd", "cat stack.txt"), ("kv", "linguagens: Dart, JavaScript, TypeScript, C++, HTML, CSS"),
                      ("kv", "front e mobile: Flutter, React"), ("kv", "back e dados: Node.js, MySQL, Firebase"),
                      ("kv", "ferramentas: Git, GitHub, Arduino, Figma"),
                      ("cmd", "ls projetos"),
                      ("kv", "RV Label: app Flutter, API Node.js e MySQL, em andamento"),
                      ("kv", "Projeto Integrado IoT: Arduino, React e Web Serial API"),
                      ("cmd", "echo $ABERTO_A"), ("kv", "estágio: desenvolvimento de software"),
                      ("kv", "colaboração: projetos em equipe e código aberto"),
                      ("kv", "contato: hendersonleriogrossi@gmail.com")]),
    "en": dict(stats="Stats", commits="Commits in the last year", prs="Pull requests", issues="Issues",
               stars="Stars received", repos="Public repositories", streak="Contribution streak",
               total="Contributions", year="in the last year", current="Current streak", longest="Longest streak",
               days="days", langs="Top languages", cal="contributions in the last year",
               ov="Activity overview", review="Code review", less="Less", more="More",
               touched="Contributed to {n} repositories",
               months=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
               wd=["", "Mon", "", "Wed", "", "Fri", ""],
               commits_short="Commits", role="Full Stack Developer",
               panel_alt="Introduction panel of Henderson Lerio Grossi",
               panel=[("cmd", "whoami"), ("kv", "name: Henderson Lerio Grossi"),
                      ("kv", "course: Systems Analysis and Development, UNIFEOB"),
                      ("kv", "program: evening"), ("kv", "focus: full stack development"),
                      ("cmd", "cat stack.txt"), ("kv", "languages: Dart, JavaScript, TypeScript, C++, HTML, CSS"),
                      ("kv", "front and mobile: Flutter, React"), ("kv", "back and data: Node.js, MySQL, Firebase"),
                      ("kv", "tooling: Git, GitHub, Arduino, Figma"),
                      ("cmd", "ls projects"),
                      ("kv", "RV Label: Flutter app, Node.js API and MySQL, in progress"),
                      ("kv", "IoT Integrated Project: Arduino, React and Web Serial API"),
                      ("cmd", "echo $OPEN_TO"), ("kv", "internship: software development"),
                      ("kv", "collaboration: team projects and open source"),
                      ("kv", "contact: hendersonleriogrossi@gmail.com")]),
}

QUERY = """query($u:String!){user(login:$u){followers{totalCount}
 repositories(ownerAffiliations:OWNER,privacy:PUBLIC,isFork:false,first:100){totalCount nodes{stargazerCount
  languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}
 pullRequests{totalCount} issues{totalCount}
 contributionsCollection{totalCommitContributions totalPullRequestContributions totalIssueContributions
  totalPullRequestReviewContributions commitContributionsByRepository(maxRepositories:100){repository{nameWithOwner}}
  contributionCalendar{totalContributions
  weeks{contributionDays{date contributionCount}}}}}}"""


def fail(msg):
    print("::error::" + msg.replace("\n", " "), flush=True)  # aparece como anotação na execução
    sys.exit(1)


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"u": USER}}).encode(),
        headers={"Authorization": "bearer " + os.environ["GITHUB_TOKEN"], "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.load(r)
    except urllib.error.HTTPError as e:
        fail(f"HTTP {e.code}: {e.read().decode()[:300]}")
    if "errors" in body or not (body.get("data") or {}).get("user"):
        fail("GraphQL: " + json.dumps(body)[:300])
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
            "contributionsCollection": {"totalCommitContributions": 120, "totalPullRequestContributions": 6,
                                        "totalIssueContributions": 2, "totalPullRequestReviewContributions": 3,
                                        "commitContributionsByRepository": [{}, {}, {}], "contributionCalendar": {
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
    body = "".join(t(28, 72 + i * 30, k, size=14) + t(552, 72 + i * 30, n, size=15, weight=700, fill=TITLE, anchor="end")
                   for i, (k, n) in enumerate(rows))
    return card(580, 230, L["stats"], body)


def streak_card(L, v):
    cols = [(L["total"], v["total"], L["year"]), (L["current"], v["cur"], L["days"]),
            (L["longest"], v["longest"], L["days"])]
    body = ""
    for i, (k, n, sub) in enumerate(cols):
        x = 197 + 393 * i
        if i:
            body += f'<line x1="{x - 196}" y1="58" x2="{x - 196}" y2="146" stroke="{BORDER}"/>'
        body += t(x, 98, n, size=36, weight=700, fill=TITLE if i == 1 else TEXT, anchor="middle")
        body += t(x, 124, k, size=13, anchor="middle") + t(x, 144, sub, size=11, fill=MUTED, anchor="middle")
    return card(1180, 170, L["streak"], body)


def langs_card(L, langs):
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]
    bars, legend, x = "", "", 28.0
    for i, (name, size) in enumerate(top):
        wbar = 524 * size / total
        bars += f'<rect x="{x:.1f}" y="60" width="{wbar:.1f}" height="12" fill="{PALETTE[i]}"/>'
        x += wbar
        cx, cy = 28 + 270 * (i % 2), 112 + 36 * (i // 2)
        legend += (f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{PALETTE[i]}"/>'
                   + t(cx + 20, cy, f"{name}  {100 * size / total:.1f}%", size=13))
    clip = '<clipPath id="c"><rect x="28" y="60" width="524" height="12" rx="6"/></clipPath>'
    return card(580, 230, L["langs"], f'{clip}<g clip-path="url(#c)">{bars}</g>{legend}')


CELL = ["#161B22", "#312E81", "#4C1D95", "#7C3AED", "#A78BFA"]


def calendar_card(L, cal):
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    mx = max((d["contributionCount"] for d in days), default=0) or 1
    x0, y0, step, size = 64, 70, 20, 16
    body, last, col = "", None, -1
    for w in cal["weeks"]:
        col += 1
        for d in w["contributionDays"]:
            date = dt.date.fromisoformat(d["date"])
            row = (date.weekday() + 1) % 7
            c = d["contributionCount"]
            lvl = 0 if not c else min(4, 1 + int(3 * c / mx))
            body += (f'<rect x="{x0 + col * step}" y="{y0 + row * step}" width="{size}" height="{size}" rx="3" '
                     f'fill="{CELL[lvl]}"><title>{c} {escape(L["cal"])}, {d["date"]}</title></rect>')
        first = dt.date.fromisoformat(w["contributionDays"][0]["date"])
        if first.month != last and col < 51:
            body += t(x0 + col * step, 56, L["months"][first.month - 1], size=11, fill=MUTED)
        last = first.month
    for i, name in enumerate(L["wd"]):
        if name:
            body += t(28, y0 + i * step + 13, name, size=10, fill=MUTED)
    lx = 1180 - 28 - 5 * 20 - 90
    body += t(lx, 222, L["less"], size=11, fill=MUTED, anchor="end")
    body += "".join(f'<rect x="{lx + 10 + i * 20}" y="210" width="16" height="16" rx="3" fill="{c}"/>'
                    for i, c in enumerate(CELL))
    body += t(lx + 120, 222, L["more"], size=11, fill=MUTED)
    body += t(28, 222, f'{cal["totalContributions"]} {L["cal"]}', size=13, fill=TEXT, weight=600)
    return card(1180, 240, L["total"], body)


def overview_card(L, v):
    keys = [("commits", L["commits_short"]), ("issues", L["issues"]), ("review", L["review"]), ("prs", L["prs"])]
    tot = sum(v[k] for k, _ in keys) or 1
    mx = max(v[k] for k, _ in keys) or 1  # raio relativo ao maior eixo, como no gráfico do GitHub
    cx, cy, R = 330, 150, 80
    dirs = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # topo, direita, base, esquerda
    body = ""
    for f in (0.25, 0.5, 0.75, 1.0):
        pts = " ".join(f"{cx + dx * R * f:.1f},{cy + dy * R * f:.1f}" for dx, dy in dirs)
        body += f'<polygon points="{pts}" fill="none" stroke="#30363D"/>'
    body += f'<line x1="{cx}" y1="{cy - R}" x2="{cx}" y2="{cy + R}" stroke="#30363D"/>'
    body += f'<line x1="{cx - R}" y1="{cy}" x2="{cx + R}" y2="{cy}" stroke="#30363D"/>'
    shape = " ".join(f"{cx + dx * R * max(v[k] / mx, 0.06):.1f},{cy + dy * R * max(v[k] / mx, 0.06):.1f}"
                     for (dx, dy), (k, _) in zip(dirs, keys))
    body += (f'<polygon points="{shape}" fill="{ACCENT}" fill-opacity="0.35" stroke="{TITLE}" stroke-width="2" '
             f'stroke-linejoin="round"/>')
    body += t(cx, cy - R - 14, f'{100 * v["commits"] / tot:.0f}%', size=13, weight=700, fill=TITLE, anchor="middle")
    body += t(cx, cy - R - 30, keys[0][1], size=11, fill=MUTED, anchor="middle")
    body += t(cx + R + 14, cy - 2, f'{100 * v["issues"] / tot:.0f}%', size=13, weight=700, fill=TITLE)
    body += t(cx + R + 14, cy + 14, keys[1][1], size=11, fill=MUTED)
    body += t(cx, cy + R + 22, f'{100 * v["review"] / tot:.0f}%', size=13, weight=700, fill=TITLE, anchor="middle")
    body += t(cx, cy + R + 38, keys[2][1], size=11, fill=MUTED, anchor="middle")
    body += t(cx - R - 14, cy - 2, f'{100 * v["prs"] / tot:.0f}%', size=13, weight=700, fill=TITLE, anchor="end")
    body += t(cx - R - 14, cy + 14, keys[3][1], size=11, fill=MUTED, anchor="end")
    for i, (k, name) in enumerate(keys):
        y = 92 + i * 34
        body += (f'<rect x="680" y="{y - 14}" width="440" height="26" rx="6" fill="#161B22"/>'
                 f'<circle cx="698" cy="{y - 1}" r="5" fill="{PALETTE[i]}"/>'
                 + t(714, y + 3, name, size=13) + t(1104, y + 3, f'{v[k]}  ({100 * v[k] / tot:.0f}%)',
                                                      size=13, weight=700, fill=TITLE, anchor="end"))
    body += t(680, 250, L["touched"].format(n=v["touched"]), size=12, fill=MUTED)
    return card(1180, 290, L["ov"], body)


def header(L):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="150" viewBox="0 0 1180 150" role="img" '
            f'aria-label="Henderson Lerio Grossi, {escape(L["role"])}"><title>Henderson Lerio Grossi</title>'
            f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1E1B4B"/>'
            f'<stop offset="0.55" stop-color="#4C1D95"/><stop offset="1" stop-color="#1D4ED8"/></linearGradient>'
            f'<linearGradient id="ln" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6366F1"/>'
            f'<stop offset="1" stop-color="#A78BFA"/></linearGradient></defs>'
            f'<rect width="1180" height="150" rx="14" fill="url(#bg)"/>'
            f'<g font-family="{FONT}" text-anchor="middle">'
            f'<text x="590" y="70" font-size="42" font-weight="800" fill="#EDE9FE">Henderson Lerio Grossi'
            f'<animate attributeName="opacity" values="0;1" dur="1.2s" fill="freeze"/></text>'
            f'<text x="590" y="104" font-size="18" font-weight="500" fill="#C4B5FD">{escape(L["role"])}'
            f'<animate attributeName="opacity" values="0;1" dur="1.2s" begin="0.6s" fill="freeze"/></text></g>'
            f'<rect x="440" y="124" width="300" height="3" rx="1.5" fill="url(#ln)">'
            f'<animate attributeName="width" values="0;300" dur="1.4s" fill="freeze"/>'
            f'<animate attributeName="x" values="590;440" dur="1.4s" fill="freeze"/></rect></svg>')


def panel(L):
    mono = "'JetBrains Mono','Fira Code',Consolas,'Courier New',monospace"
    lines = L["panel"]
    body, y = "", 108
    for i, (kind, text) in enumerate(lines):
        if kind == "cmd":
            y += 14 if i else 0
            row = (f'<text x="36" y="{y}" font-size="16" fill="{ACCENT}">$</text>'
                   f'<text x="58" y="{y}" font-size="16" fill="{TITLE}" font-weight="700">{escape(text)}</text>')
        else:
            k, _, val = text.partition(": ")
            row = (f'<text x="58" y="{y}" font-size="15" fill="{MUTED}">{escape(k)}</text>'
                   f'<text x="290" y="{y}" font-size="15" fill="{TEXT}">{escape(val)}</text>')
        d, tot = 0.3 + i * 0.25, 0.7 + i * 0.25
        body += (f'<g>{row}<animate attributeName="opacity" values="0;0;1" keyTimes="0;{d / tot:.3f};1" '
                 f'dur="{tot:.2f}s" fill="freeze"/></g>')
        y += 26
    h = y + 40
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="{h}" viewBox="0 0 1180 {h}" role="img" '
            f'aria-label="{escape(L["panel_alt"])}"><title>{escape(L["panel_alt"])}</title>'
            f'<rect x="0.5" y="0.5" width="1179" height="{h - 1}" rx="12" fill="#0A0C14" stroke="{BORDER}"/>'
            f'<rect x="0.5" y="0.5" width="1179" height="44" rx="12" fill="#161B22"/>'
            f'<rect x="0.5" y="30" width="1179" height="15" fill="#161B22"/>'
            f'<circle cx="28" cy="22" r="6" fill="#4C1D95"/><circle cx="50" cy="22" r="6" fill="#6366F1"/>'
            f'<circle cx="72" cy="22" r="6" fill="#A78BFA"/>'
            f'<text x="590" y="27" font-family="{FONT}" font-size="12" fill="{MUTED}" text-anchor="middle">'
            f'henderson@github: ~</text><g font-family="{mono}">{body}'
            f'<rect x="58" y="{y - 14}" width="9" height="18" fill="{TITLE}">'
            f'<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect></g></svg>')


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
    c = u["contributionsCollection"]
    o = dict(commits=c["totalCommitContributions"], prs=c["totalPullRequestContributions"],
             issues=c["totalIssueContributions"], review=c["totalPullRequestReviewContributions"],
             touched=len(c["commitContributionsByRepository"]))
    os.makedirs(out, exist_ok=True)
    for lang, L in LABELS.items():
        cards = (("stats", stats_card(L, v)), ("streak", streak_card(L, v)), ("langs", langs_card(L, langs)),
                 ("calendar", calendar_card(L, cal)), ("overview", overview_card(L, o)),
                 ("header", header(L)), ("panel", panel(L)))
        for name, svg in cards:
            with open(os.path.join(out, f"github-{name}.{lang}.svg"), "w", encoding="utf8") as f:
                f.write(svg)


if __name__ == "__main__":
    main()
