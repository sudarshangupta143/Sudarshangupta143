"""Generates assets/stats.svg and assets/langs.svg from the GitHub API.
Runs inside GitHub Actions (needs GITHUB_TOKEN). Set DEMO=1 to render without network."""
import os, json, html, urllib.request

USER = os.environ.get("USERNAME", "sudarshangupta143")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
FONT = "'Segoe UI','Helvetica Neue',Arial,sans-serif"
E = html.escape
PALETTE = ["#00f0ff", "#8b5cff", "#ff3df2", "#ffb347", "#3ddc97"]

QUERY = """
query($login:String!){ user(login:$login){
  followers{totalCount}
  repositories(ownerAffiliations:OWNER,isFork:false,first:100,privacy:PUBLIC){
    totalCount
    nodes{ stargazerCount languages(first:10,orderBy:{field:SIZE,direction:DESC}){ edges{size node{name color}} } }
  }
  contributionsCollection{
    totalCommitContributions totalPullRequestContributions totalIssueContributions
    contributionCalendar{totalContributions}
  }
}}"""

def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": "bearer " + os.environ["GITHUB_TOKEN"], "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        u = json.load(r)["data"]["user"]
    repos = u["repositories"]["nodes"]
    langs = {}
    for rp in repos:
        for e in rp["languages"]["edges"]:
            n = e["node"]["name"]
            langs.setdefault(n, [0, e["node"]["color"] or "#8b5cff"])[0] += e["size"]
    top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:5]
    cc = u["contributionsCollection"]
    return {
        "Repos": u["repositories"]["totalCount"],
        "Stars": sum(r["stargazerCount"] for r in repos),
        "Followers": u["followers"]["totalCount"],
        "Contributions": cc["contributionCalendar"]["totalContributions"],
        "Pull Requests": cc["totalPullRequestContributions"],
        "Issues": cc["totalIssueContributions"],
    }, [(n, v[0], v[1]) for n, v in top]

DEFS = """<defs>
<linearGradient id="bd" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#00f0ff"/><stop offset=".5" stop-color="#8b5cff"/><stop offset="1" stop-color="#ff3df2"/></linearGradient>
<linearGradient id="ttl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#00f0ff"/><stop offset="1" stop-color="#ff3df2"/></linearGradient>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0d1233"/><stop offset="1" stop-color="#06070f"/></linearGradient>
<style>
.in{animation:i .8s ease both}@keyframes i{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
.bar{transform-box:fill-box;transform-origin:left;animation:g 1.4s cubic-bezier(.2,.8,.2,1) both}@keyframes g{from{transform:scaleX(0)}to{transform:scaleX(1)}}
</style></defs>"""

def shell(title, body, W=500, H=260):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{DEFS}'
            f'<rect x="3" y="3" width="{W-6}" height="{H-6}" rx="18" fill="url(#bg)" stroke="url(#bd)" stroke-width="2"/>'
            f'<text x="28" y="44" font-family="{FONT}" font-size="15" font-weight="800" letter-spacing="5" fill="url(#ttl)">{title}</text>'
            f'<rect x="28" y="56" width="{W-56}" height="1.5" fill="url(#bd)" opacity=".5"/>{body}</svg>')

def stats_svg(s):
    t = []
    for i, (k, v) in enumerate(s.items()):
        x = 28 + (i % 3) * 148; y = 76 + (i // 3) * 84
        t.append(f'<g class="in" style="animation-delay:{i*.12:.2f}s">'
                 f'<rect x="{x}" y="{y}" width="136" height="72" rx="12" fill="#141b44" stroke="#2a3470"/>'
                 f'<text x="{x+16}" y="{y+37}" font-family="{FONT}" font-size="28" font-weight="800" fill="url(#ttl)">{v}</text>'
                 f'<text x="{x+16}" y="{y+58}" font-family="{FONT}" font-size="10" letter-spacing="1" fill="#8ea0ff">{E(k.upper())}</text></g>')
    t.append(f'<text x="472" y="246" text-anchor="end" font-family="{FONT}" font-size="11" letter-spacing="2" fill="#5b679e">@{E(USER)}</text>')
    return shell("GITHUB STATS", "".join(t))

def langs_svg(langs):
    t = []
    if not langs:
        t.append(f'<text x="250" y="150" text-anchor="middle" font-family="{FONT}" font-size="15" fill="#8ea0ff">Push your first repo — languages appear here</text>')
    total = sum(v for _, v, _ in langs) or 1
    for i, (n, v, c) in enumerate(langs):
        y = 94 + i * 30; pct = v * 100 / total; w = max(4, 230 * pct / 100)
        t.append(f'<g class="in" style="animation-delay:{i*.12:.2f}s">'
                 f'<text x="28" y="{y+10}" font-family="{FONT}" font-size="13" fill="#dfe4ff">{E(n)}</text>'
                 f'<rect x="150" y="{y}" width="230" height="10" rx="5" fill="#1a2250"/>'
                 f'<rect class="bar" style="animation-delay:{i*.12+.2:.2f}s" x="150" y="{y}" width="{w:.0f}" height="10" rx="5" fill="{E(c)}"/>'
                 f'<text x="472" y="{y+10}" text-anchor="end" font-family="{FONT}" font-size="12" fill="#8ea0ff">{pct:.1f}%</text></g>')
    return shell("TOP LANGUAGES", "".join(t))

if __name__ == "__main__":
    if os.environ.get("DEMO"):
        s = {"Repos": 0, "Stars": 0, "Followers": 0, "Contributions": 0, "Pull Requests": 0, "Issues": 0}; l = []
    else:
        s, l = fetch()
    open(os.path.join(OUT, "stats.svg"), "w", encoding="utf-8").write(stats_svg(s))
    open(os.path.join(OUT, "langs.svg"), "w", encoding="utf-8").write(langs_svg(l))
    print("stats + langs written", s)
