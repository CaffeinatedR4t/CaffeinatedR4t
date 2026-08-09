#!/usr/bin/env python3
"""
today.py
Pulls live stats from the GitHub API (repos, stars, followers, total
commits, and total lines of code contributed) and stamps them into
light_mode.svg / dark_mode.svg for use in a GitHub profile README.

Requires an environment variable ACCESS_TOKEN with a GitHub Personal
Access Token that has at least `read:user` and `repo` scope.
"""

import os
import json
import requests
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "CaffeinatedR4t")
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]

HEADERS = {"Authorization": f"bearer {ACCESS_TOKEN}"}
GRAPHQL_URL = "https://api.github.com/graphql"
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)


def graphql_query(query, variables=None):
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
    """Followers, public repo count, and total stars across owned repos."""
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
    """
    contributionsCollection only covers one year at a time, so walk back
    year by year from account creation until totalCommitContributions is 0
    two years running (cheap heuristic that avoids over-querying).
    """
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
    """
    GitHub's API has no direct 'lines of code' field, so this sums
    additions/deletions from each owned repo's default branch stats
    endpoint, caching per-repo results since this is the expensive part.
    Returns (net_loc, total_added, total_deleted).
    """
    cache_file = CACHE_DIR / "loc_cache.json"
    cache = json.loads(cache_file.read_text()) if cache_file.exists() else {}

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


def stamp_svg(template_path, output_path, values):
    text = Path(template_path).read_text()
    for key, val in values.items():
        text = text.replace(f"{{{{ {key} }}}}", format_number(val) if isinstance(val, int) else str(val))
    Path(output_path).write_text(text)


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

    # Note: only {{ repos }}, {{ stars }}, {{ commits }}, {{ followers }},
    # {{ loc }}, {{ loc_added }}, {{ loc_deleted }} exist as placeholders
    # in the templates now — personal fields (OS, Uptime, Contact, etc.)
    # are plain hardcoded text you edit directly in the *_template.svg
    # files, since GitHub's API has no concept of those.
    stamp_svg("light_mode_template.svg", "light_mode.svg", values)
    stamp_svg("dark_mode_template.svg", "dark_mode.svg", values)

    print("Updated SVGs with:", values)


if __name__ == "__main__":
    main()
