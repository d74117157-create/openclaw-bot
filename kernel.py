"""
OpenClaw — kernel.py
The MAIN BRAIN kernel: GitHub automation agent + swarm coordination hub.
Runs as a standalone service for GitHub operations.
"""
import os, json, time, requests
from dotenv import load_dotenv
from memory import init_db, save_decision, save_deployment
from worker.ai_worker import process_task, orchestrate_task, AGENT_PERSONAS

load_dotenv()

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO  = os.environ.get("GITHUB_REPO", "")   # owner/repo
GITHUB_API   = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def gh_get(path: str) -> dict:
    r = requests.get(f"{GITHUB_API}/{path}", headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def gh_post(path: str, payload: dict) -> dict:
    r = requests.post(f"{GITHUB_API}/{path}", headers=HEADERS, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def gh_patch(path: str, payload: dict) -> dict:
    r = requests.patch(f"{GITHUB_API}/{path}", headers=HEADERS, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def gh_put(path: str, payload: dict) -> dict:
    r = requests.put(f"{GITHUB_API}/{path}", headers=HEADERS, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def create_branch(repo: str, branch_name: str, from_branch: str = "main") -> dict:
    ref_data = gh_get(f"repos/{repo}/git/ref/heads/{from_branch}")
    sha = ref_data["object"]["sha"]
    result = gh_post(f"repos/{repo}/git/refs", {
        "ref": f"refs/heads/{branch_name}",
        "sha": sha
    })
    save_decision(f"Created branch {branch_name} from {from_branch}", f"Repo: {repo}", "success")
    return result


def create_issue(repo: str, title: str, body: str, labels: list = None) -> dict:
    payload = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    result = gh_post(f"repos/{repo}/issues", payload)
    save_decision(f"Created issue: {title}", f"Repo: {repo}", "success")
    return result


def create_pull_request(repo: str, title: str, body: str, head: str, base: str = "main") -> dict:
    result = gh_post(f"repos/{repo}/pulls", {
        "title": title,
        "body": body,
        "head": head,
        "base": base,
    })
    save_decision(f"Created PR: {title}", f"Repo: {repo} | {head}>{base}", "success")
    return result


def list_open_prs(repo: str) -> list:
    return gh_get(f"repos/{repo}/pulls?state=open")


def list_open_issues(repo: str) -> list:
    return gh_get(f"repos/{repo}/issues?state=open")


def get_repo_info(repo: str) -> dict:
    return gh_get(f"repos/{repo}")


def create_file(repo: str, path: str, content_b64: str, message: str, branch: str = "main") -> dict:
    import base64
    result = gh_put(f"repos/{repo}/contents/{path}", {
        "message": message,
        "content": content_b64,
        "branch": branch,
    })
    return result


def trigger_workflow(repo: str, workflow_id: str, ref: str = "main", inputs: dict = None) -> dict:
    payload = {"ref": ref}
    if inputs:
        payload["inputs"] = inputs
    r = requests.post(
        f"{GITHUB_API}/repos/{repo}/actions/workflows/{workflow_id}/dispatches",
        headers=HEADERS,
        json=payload,
        timeout=15
    )
    r.raise_for_status()
    return {"status": "triggered", "workflow": workflow_id}


def list_workflow_runs(repo: str, limit: int = 5) -> list:
    data = gh_get(f"repos/{repo}/actions/runs?per_page={limit}")
    return data.get("workflow_runs", [])


def add_pr_comment(repo: str, pr_number: int, comment: str) -> dict:
    return gh_post(f"repos/{repo}/issues/{pr_number}/comments", {"body": comment})


def close_issue(repo: str, issue_number: int, comment: str = "") -> dict:
    if comment:
        gh_post(f"repos/{repo}/issues/{issue_number}/comments", {"body": comment})
    return gh_patch(f"repos/{repo}/issues/{issue_number}", {"state": "closed"})


def ai_generate_github_action(task: str) -> str:
    prompt = (
        f"Generate a complete GitHub Actions workflow YAML file for: {task}\n"
        f"Requirements: trigger on push/PR to main, Python 3.11, pip install requirements.txt, "
        f"run tests, deploy to Railway on success. Include all required steps."
    )
    return process_task(prompt, "github")


def ai_review_pr_content(pr_body: str) -> str:
    return process_task(f"Review this PR:\n{pr_body}", "reviewer")


def ai_generate_commit_message(diff: str) -> str:
    prompt = (
        f"Write a conventional commit message for this diff:\n{diff[:2000]}\n"
        f"Format: <type>(<scope>): <short description>\n\n<body>"
    )
    return process_task(prompt, "coder")


def kernel_status() -> dict:
    status = {
        "kernel": "OpenClaw Kernel v1.0",
        "repo": GITHUB_REPO,
        "github_auth": bool(GITHUB_TOKEN),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if GITHUB_TOKEN and GITHUB_REPO:
        try:
            info = get_repo_info(GITHUB_REPO)
            status["repo_info"] = {
                "name": info.get("name"),
                "stars": info.get("stargazers_count"),
                "open_issues": info.get("open_issues_count"),
                "default_branch": info.get("default_branch"),
                "last_push": info.get("pushed_at"),
            }
            runs = list_workflow_runs(GITHUB_REPO, 3)
            status["recent_runs"] = [
                {"name": r["name"], "status": r["status"], "conclusion": r.get("conclusion")}
                for r in runs
            ]
        except Exception as e:
            status["repo_error"] = str(e)
    return status


if __name__ == "__main__":
    init_db()
    print("[Kernel] OpenClaw Kernel starting...")
    s = kernel_status()
    print(json.dumps(s, indent=2))
    print("[Kernel] Ready. GitHub agent operational.")
