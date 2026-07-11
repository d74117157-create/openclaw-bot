"""GitHub automation agent — branches, issues, PRs, workflows."""
import os
import base64
import json
import time
import requests
import logging
from dotenv import load_dotenv
from worker.ai_worker import process_task
from memory import save_decision

load_dotenv()
logger = logging.getLogger("openclaw.github")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
GITHUB_API = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _gh_get(path: str) -> dict:
    r = requests.get(f"{GITHUB_API}/{path}", headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def _gh_post(path: str, payload: dict) -> dict:
    r = requests.post(f"{GITHUB_API}/{path}", headers=HEADERS, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def _gh_patch(path: str, payload: dict) -> dict:
    r = requests.patch(f"{GITHUB_API}/{path}", headers=HEADERS, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def _gh_put(path: str, payload: dict) -> dict:
    r = requests.put(f"{GITHUB_API}/{path}", headers=HEADERS, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def create_branch(repo: str, branch_name: str, from_branch: str = "main") -> dict:
    ref_data = _gh_get(f"repos/{repo}/git/ref/heads/{from_branch}")
    sha = ref_data["object"]["sha"]
    result = _gh_post(f"repos/{repo}/git/refs", {"ref": f"refs/heads/{branch_name}", "sha": sha})
    save_decision(f"Created branch {branch_name} from {from_branch}", f"Repo: {repo}", "success")
    return result


def create_issue(repo: str, title: str, body: str, labels: list = None) -> dict:
    payload = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    result = _gh_post(f"repos/{repo}/issues", payload)
    save_decision(f"Created issue: {title}", f"Repo: {repo}", "success")
    return result


def create_pull_request(repo: str, title: str, body: str, head: str, base: str = "main") -> dict:
    result = _gh_post(f"repos/{repo}/pulls", {"title": title, "body": body, "head": head, "base": base})
    save_decision(f"Created PR: {title}", f"Repo: {repo} | {head}>{base}", "success")
    return result


def list_open_prs(repo: str) -> list:
    return _gh_get(f"repos/{repo}/pulls?state=open")


def list_open_issues(repo: str) -> list:
    return _gh_get(f"repos/{repo}/issues?state=open")


def get_repo_info(repo: str) -> dict:
    return _gh_get(f"repos/{repo}")


def create_file(repo: str, path: str, content_b64: str, message: str, branch: str = "main") -> dict:
    return _gh_put(f"repos/{repo}/contents/{path}", {"message": message, "content": content_b64, "branch": branch})


def trigger_workflow(repo: str, workflow_id: str, ref: str = "main", inputs: dict = None) -> dict:
    payload = {"ref": ref}
    if inputs:
        payload["inputs"] = inputs
    r = requests.post(
        f"{GITHUB_API}/repos/{repo}/actions/workflows/{workflow_id}/dispatches",
        headers=HEADERS, json=payload, timeout=15
    )
    r.raise_for_status()
    return {"status": "triggered", "workflow": workflow_id}


def list_workflow_runs(repo: str, limit: int = 5) -> list:
    data = _gh_get(f"repos/{repo}/actions/runs?per_page={limit}")
    return data.get("workflow_runs", [])


def add_pr_comment(repo: str, pr_number: int, comment: str) -> dict:
    return _gh_post(f"repos/{repo}/issues/{pr_number}/comments", {"body": comment})


def close_issue(repo: str, issue_number: int, comment: str = "") -> dict:
    if comment:
        _gh_post(f"repos/{repo}/issues/{issue_number}/comments", {"body": comment})
    return _gh_patch(f"repos/{repo}/issues/{issue_number}", {"state": "closed"})


class GitHubAgent:
    def __init__(self, repo: str = None):
        self.repo = repo or GITHUB_REPO

    def repo_summary(self) -> str:
        if not self.repo:
            return "GITHUB_REPO not set."
        try:
            info = get_repo_info(self.repo)
            prs = list_open_prs(self.repo)
            issues = list_open_issues(self.repo)
            runs = list_workflow_runs(self.repo, 3)
            summary = (
                f"Repo: {info['full_name']}\n"
                f"Stars: {info['stargazers_count']} | Forks: {info['forks_count']} | Open issues: {info['open_issues_count']}\n"
                f"Default branch: {info['default_branch']}\nLast push: {info['pushed_at']}\n\n"
                f"Open PRs ({len(prs)}):\n"
            )
            for pr in prs[:5]:
                summary += f"  #{pr['number']} {pr['title']} ({pr['head']['ref']})\n"
            summary += f"\nRecent Workflow Runs:\n"
            for run in runs:
                icon = "OK" if run.get("conclusion") == "success" else "FAIL"
                summary += f"  {icon} {run['name']} — {run['status']} ({run.get('conclusion', 'pending')})\n"
            return summary
        except Exception as e:
            return f"GitHub error: {e}"

    def new_feature_branch(self, feature_name: str) -> str:
        safe = feature_name.lower().replace(" ", "-")[:40]
        branch = f"feature/{safe}"
        try:
            result = create_branch(self.repo, branch)
            return f"Branch created: {branch}\nRef: {result.get('ref')}"
        except Exception as e:
            return f"Branch error: {e}"

    def open_issue(self, title: str, body: str, labels: list = None) -> str:
        try:
            result = create_issue(self.repo, title, body, labels or ["enhancement"])
            return f"Issue #{result['number']} opened: {result['html_url']}"
        except Exception as e:
            return f"Issue error: {e}"

    def open_bug_issue(self, description: str) -> str:
        ai_body = process_task(
            f"Write a detailed GitHub bug report for: {description}\nInclude: Steps to reproduce, Expected behavior, Actual behavior, Environment.",
            "github"
        )
        return self.open_issue(title=f"Bug: {description[:60]}", body=ai_body, labels=["bug"])

    def open_pr(self, title: str, body: str, head: str, base: str = "main") -> str:
        try:
            result = create_pull_request(self.repo, title, body, head, base)
            return f"PR #{result['number']} opened: {result['html_url']}"
        except Exception as e:
            return f"PR error: {e}"

    def execute(self, command: str) -> str:
        cmd = command.lower()
        if "summary" in cmd or "status" in cmd or "info" in cmd:
            return self.repo_summary()
        elif "branch" in cmd and ("feature" in cmd or "new" in cmd):
            name = command.replace("create", "").replace("branch", "").replace("feature", "").strip()
            return self.new_feature_branch(name or "unnamed-feature")
        elif "bug" in cmd or ("issue" in cmd and "bug" in cmd):
            return self.open_bug_issue(command)
        elif "issue" in cmd and ("open" in cmd or "create" in cmd or "new" in cmd):
            return self.open_issue(command[:80], command)
        elif "pr" in cmd or "pull request" in cmd:
            return self.open_pr(f"[OpenClaw] {command[:60]}", command, "feature/auto")
        else:
            return process_task(f"Execute this GitHub operation on repo {self.repo}: {command}\nReturn exact gh CLI commands or GitHub API calls.", "github")
