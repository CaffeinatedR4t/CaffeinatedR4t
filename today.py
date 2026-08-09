#!/usr/bin/env python3
import os
import json
import requests
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "CaffeinatedR4t")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "")

HEADERS = {"Authorization": f"bearer {ACCESS_TOKEN}"} if ACCESS_TOKEN else {}
GRAPHQL_URL = "https://api.github.com/graphql"
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

def graphql_query(query, variables=None):
    if not ACCESS_TOKEN:
        return {"user": {"name": USERNAME, "followers": {"totalCount": 0}, "repositories": {"totalCount": 0, "pageInfo": {"hasNextPage": False}, "nodes": []}, "contributionsCollection": {"totalCommitContributions": 0, "restrictedContributionsCount": 0}}}
    resp = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables or {}},
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def get_profile_stats():
    query = """
    query($login: String!, $after: String) {
      user(login: $login) {
        name
        followers { totalCount }
        repositories(first: 100, after: $after, ownerAffiliations: OWNER,
                      isFork: false, privacy: PUBLIC) {
          totalCount
          pageInfo { hasNextPage endCursor }
          nodes { stargazerCount }
        }
      }
    }
    """
    name = None
    followers = 0
    repo_count = 0
    stars = 0
    after = None

    while True:
        data = graphql_query(query, {"login": USERNAME, "after": after})
        user = data["user"]
        name = user["name"] or USERNAME
        followers = user["followers"]["totalCount"]
        repos = user["repositories"]
        repo_count = repos["totalCount"]
        stars += sum(r["stargazerCount"] for r in repos["nodes"])

        if repos["pageInfo"]["hasNextPage"]:
            after = repos["pageInfo"]["endCursor"]
        else:
            break

    return {"name": name, "followers": followers, "repos": repo_count, "stars": stars}


def get_total_commits():
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          restrictedContributionsCount
        }
      }
    }
    """
    from datetime import datetime, timedelta, timezone

    total = 0
    year_start = datetime.now(timezone.utc).replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    misses = 0
    year = year_start
    while misses < 2 and year.year > 2007:
        frm = year.isoformat()
        to = (year.replace(year=year.year + 1) - timedelta(seconds=1)).isoformat()
        data = graphql_query(query, {"login": USERNAME, "from": frm, "to": to})
        c = data["user"]["contributionsCollection"]
        count = c["totalCommitContributions"] + c["restrictedContributionsCount"]
        if count == 0:
            misses += 1
        else:
            misses = 0
        total += count
        year = year.replace(year=year.year - 1)

    return total


def get_lines_of_code():
    cache_file = CACHE_DIR / "loc_cache.json"
    cache = json.loads(cache_file.read_text()) if cache_file.exists() else {}

    if not ACCESS_TOKEN:
        return 0, 0, 0

    repos_resp = requests.get(
        f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner",
        headers={"Authorization": f"token {ACCESS_TOKEN}"},
        timeout=30,
    )
    repos_resp.raise_for_status()
    repos = repos_resp.json()

    total_added = 0
    total_deleted = 0
    for repo in repos:
        full_name = repo["full_name"]
        sha = repo.get("pushed_at", "")
        cached = cache.get(full_name)
        if cached and cached.get("pushed_at") == sha:
            total_added += cached["added"]
            total_deleted += cached["deleted"]
            continue

        stats_resp = requests.get(
            f"https://api.github.com/repos/{full_name}/stats/contributors",
            headers={"Authorization": f"token {ACCESS_TOKEN}"},
            timeout=30,
        )
        if stats_resp.status_code != 200:
            continue
        contributors = stats_resp.json()
        if not isinstance(contributors, list):
            continue

        repo_added = 0
        repo_deleted = 0
        for c in contributors:
            author = c.get("author") or {}
            if author.get("login") == USERNAME:
                for week in c.get("weeks", []):
                    repo_added += week.get("a", 0)
                    repo_deleted += week.get("d", 0)

        cache[full_name] = {"pushed_at": sha, "added": repo_added, "deleted": repo_deleted}
        total_added += repo_added
        total_deleted += repo_deleted

    cache_file.write_text(json.dumps(cache, indent=2))
    return max(total_added - total_deleted, 0), total_added, total_deleted


def format_number(n):
    return f"{n:,}"


def get_uptime():
    from datetime import datetime
    import calendar
    birth_date = datetime(2006, 1, 16)
    today = datetime.now()
    
    years = today.year - birth_date.year
    months = today.month - birth_date.month
    days = today.day - birth_date.day
    
    if days < 0:
        months -= 1
        prev_month = today.month - 1 if today.month > 1 else 12
        prev_month_year = today.year if today.month > 1 else today.year - 1
        _, num_days = calendar.monthrange(prev_month_year, prev_month)
        days += num_days
        
    if months < 0:
        years -= 1
        months += 12
        
    return f"{years} years, {months} months, {days} days"

def generate_svg(mode, values):
    dark_bg = "#161b22"
    dark_avatar = "#bec5ce"
    dark_label = "#ffa657"
    dark_value = "#a5d6ff"
    dark_header = "#bec5ce"
    dark_dots = "#474d55"
    
    light_bg = "#f6f8fa"
    light_avatar = "#24292e"
    light_label = "#d73a49"
    light_value = "#0366d6"
    light_header = "#24292e"
    light_dots = "#d1d5da"
    
    bg = dark_bg if mode == 'dark' else light_bg
    avatar_color = dark_avatar if mode == 'dark' else light_avatar
    label_color = dark_label if mode == 'dark' else light_label
    value_color = dark_value if mode == 'dark' else light_value
    header_color = dark_header if mode == 'dark' else light_header
    dots_color = dark_dots if mode == 'dark' else light_dots
    
    width = 1160
    height = 578
    
    svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
<style>
.avatar {{ font-family: "Courier New", monospace; font-size: 14px; fill: {avatar_color}; white-space: pre; }}
.header {{ font-family: "Consolas", "Courier New", monospace; font-size: 14px; font-weight: 700; fill: {header_color}; }}
.label {{ font-family: "Consolas", "Courier New", monospace; font-size: 14px; fill: {label_color}; }}
.value {{ font-family: "Consolas", "Courier New", monospace; font-size: 14px; fill: {value_color}; }}
</style>
<rect x="0.5" y="0.5" rx="10" width="{width-1}" height="{height-1}" fill="{bg}" stroke="{dots_color}" stroke-width="1"/>
'''

    ascii_art = [
        '@@@@@@@@@@@@@@@@@@@@@@@@@@GYYYYYYYYYYY5&amp;@@@@@@@@@@@@@@@@@@@@&amp;5YYYYYYYYYYYG@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!            B@@@@@@@@@@@@@@@@@@@@B            ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!            B@@@@@@@@@@@@@@@@@@@@B            ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!      ?P555P&amp;@@@@@@@@@@@@@@@@@@@@@P555PJ      ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!      G@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@G      ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!      P@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@G      ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!      P@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@G      ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!      P@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@G      ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!      P@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@G      ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!      P@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@G      ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!      P@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@G      ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!      P@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@G      ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!      P@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@G      ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!      P@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@G      ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!      P@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@G      ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!      P@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@G      ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!      G@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@G      ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!      ?PPP5P&amp;@@@@@@@@@@@@@@@@@@@@&amp;P5PPPJ      ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!            G@@@@@@@@@@@@@@@@@@@@G            ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@!            G@@@@@@@@@@@@@@@@@@@@G            ~@@@@@@@@@@@@@@@@@@@@@@@@@@',
        '@@@@@@@@@@@@@@@@@@@@@@@@@@GJJJJJJJJJJJY&amp;@@@@@@@@@@@@@@@@@@@@&amp;YJJJJJJJJJJJP@@@@@@@@@@@@@@@@@@@@@@@@@@'
    ]

    y = 40
    for a_line in ascii_art:
        trimmed_line = a_line[22:-22]
        svg += f'<text x="40" y="{y:.1f}" class="avatar" xml:space="preserve">{trimmed_line}</text>\n'
        y += 22

    char_width = 8.1  # slightly wider than 7.7 to ensure it doesn't overlap text
    right_col_x = 520
    max_right_x = 1130
    
    y_idx = 40
    
    def add_line(label, value=""):
        nonlocal y_idx
        lbl_str = f". {label}"
        svg_chunk = f'<text x="{right_col_x}" y="{y_idx}" class="label">{lbl_str}</text>\n'
        if value:
            # calculate exact x coordinates for the dotted line dynamically
            x1 = right_col_x + (len(lbl_str) + 1) * char_width
            x2 = max_right_x - (len(value) + 1) * char_width
            if x2 > x1:
                svg_chunk += f'<line x1="{x1}" y1="{y_idx-4}" x2="{x2}" y2="{y_idx-4}" stroke="{dots_color}" stroke-width="2" stroke-dasharray="2, 6"/>\n'
            svg_chunk += f'<text x="{max_right_x}" y="{y_idx}" class="value" text-anchor="end">{value}</text>\n'
        y_idx += 22
        return svg_chunk
        
    def add_header(title):
        nonlocal y_idx
        svg_chunk = f'<text x="{right_col_x}" y="{y_idx}" class="header">{title}</text>\n'
        x1 = right_col_x + (len(title) + 1) * char_width
        x2 = max_right_x
        if x2 > x1:
            svg_chunk += f'<line x1="{x1}" y1="{y_idx-4}" x2="{x2}" y2="{y_idx-4}" stroke="{dots_color}" stroke-width="1" stroke-dasharray="4, 4"/>\n'
        y_idx += 22
        return svg_chunk
        
    def add_gap():
        nonlocal y_idx
        y_idx += 8

    content = ""
    content += add_header("jeremy@pohar")
    content += add_line("OS:", "Windows 10, Android 16, Ubuntu")
    content += add_line("Uptime:", get_uptime())
    content += add_line("Host:", "Creativeans")
    content += add_line("Kernel:", "Fullstack Developer Intern")
    content += add_line("IDE:", "VSCode, Android Studio")
    content += add_line("Languages.Programming:", "Python, JS, TS, Kotlin, Java, PHP, C#")
    content += add_line("Languages.Computer:", "SQL, HTML, CSS")
    content += add_line("Languages.Real:", "English, Indonesian")
    content += add_line("Hobbies.Tech:", "Cybersecurity, PC Building, Keyboards")
    content += add_line("Hobbies.Personal:", "Boxing, Movies, Learning")
    content += add_header("- Contact")
    content += add_line("Email:", "jeremy.yosep@gmail.com")
    content += add_line("LinkedIn:", "linkedin.com/in/jeremyjosephpohar")
    content += add_line("Instagram:", "@jeremyjpohar")
    content += add_header("- GitHub Stats")
    
    content += add_line("Repos:", format_number(values["repos"]))
    content += add_line("Stars:", format_number(values["stars"]))
    content += add_line("Commits:", format_number(values["commits"]))
    content += add_line("Followers:", format_number(values["followers"]))
    content += add_line("Lines of Code:", f"{format_number(values['loc'])} ( {format_number(values['loc_added'])}++, {format_number(values['loc_deleted'])}-- )")
    
    svg += content
    svg += "</svg>"
    
    with open(f"{mode}_mode.svg", "w") as f:
        f.write(svg)


def main():
    profile = get_profile_stats()
    commits = get_total_commits()
    loc, loc_added, loc_deleted = get_lines_of_code()

    values = {
        "name": profile["name"],
        "repos": profile["repos"],
        "stars": profile["stars"],
        "followers": profile["followers"],
        "commits": commits,
        "loc": loc,
        "loc_added": loc_added,
        "loc_deleted": loc_deleted,
    }

    generate_svg("light", values)
    generate_svg("dark", values)

    print("Updated SVGs with:", values)


if __name__ == "__main__":
    main()
