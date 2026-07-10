"""
OpenClaw — worker/github_agent.py
Dedicated GitHub agent: executes real GitHub API calls driven by AI planning.
"""
import os, base64, json
from dotenv import load_dotenv
from kernel import (
    create_branch, create_issue, create_pull_request,
    list_open_prs, list_open_issues, get_repo_info,
    trigger_workflow, list_workflow_runs, add_pr_comment,
    close_issue, ai_generate_github_action,
    ai_review_pr_content, ai_generate_commit_message,
    create_file, GITHUB_REPO
)
from worker.ai_worker import process_task

load_dotenv()


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
                f"Stars: {info['stargazers_count']} | "
                f"Forks: {info['forks_count']} | "
                f"Open issues: {info['open_issues_count']}\n"
                f"Default branch: {info['default_branch']}\n"
                f"Last push: {info['pushed_at']}\n\n"
                f"Open PRs ({len(prs)}):\n"
            )
            for pr in prs[:5]:
                summary += f"  #{pr['number']} {pr['title']} ({pr['head']['ref']})\n"
            summary += f"\nRecent Workflow Runs:\n"
            for run in runs:
                icon = "OK" if run.get("conclusion") == "success" else "FAIL"
                summary += f"  {icon} {run['name']} -- {run['status']} ({run.get('conclusion', 'pending')})\n"
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

    def new_fix_branch(self, fix_name: str) -> str:
        safe = fix_name.lower().replace(" ", "-")[:40]
        branch = f"fix/{safe}"
        try:
            result = create_branch(self.repo, branch)
            return f"Fix branch: {branch}"
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
            f"Write a detailed GitHub bug report for: {description}\n"
            f"Include: Steps to reproduce, Expected behavior, Actual behavior, Environment.",
            "github"
        )
        return self.open_issue(
            title=f"Bug: {description[:60]}",
            body=ai_body,
            labels=["bug"]
        )

    def close_issue_with_note(self, issue_number: int, note: str = "") -> str:
        try:
            close_issue(self.repo, issue_number, note)
            return f"Issue #{issue_number} closed."
        except Exception as e:
            return f"Close error: {e}"

    def open_pr(self, title: str, body: str, head: str, base: str = "main") -> str:
        try:
            result = create_pull_request(self.repo, title, body, head, base)
            return f"PR #{result['number']} opened: {result['html_url']}"
        except Exception as e:
            return f"PR error: {e}"

    def ai_reviewed_pr(self, head: str, pr_description: str, base: str = "main") -> str:
        ai_body = process_task(
            f"Write a professional GitHub PR description for branch {head}: {pr_description}",
            "github"
        )
        try:
            pr = create_pull_request(
                self.repo,
                title=f"[OpenClaw] {pr_description[:60]}",
                body=ai_body,
                head=head,
                base=base
            )
            review = ai_review_pr_content(pr_description)
            add_pr_comment(self.repo, pr["number"], f"REVIEWER Agent Auto-Review:\n\n{review}")
            return f"PR #{pr['number']} opened + reviewed: {pr['html_url']}"
        except Exception as e:
            return f"PR creation error: {e}"

    def add_file_to_repo(self, path: str, content: str, message: str, branch: str = "main") -> str:
        try:
            content_b64 = base64.b64encode(content.encode()).decode()
            result = create_file(self.repo, path, content_b64, message, branch)
            return f"File {path} pushed to {branch}"
        except Exception as e:
            return f"File push error: {e}"

    def generate_and_push_workflow(self, task: str, branch: str = "main") -> str:
        yaml_content = ai_generate_github_action(task)
        safe_name = task.lower().replace(" ", "_")[:30]
        path = f".github/workflows/{safe_name}.yml"
        return self.add_file_to_repo(path, yaml_content, f"ci: add {safe_name} workflow", branch)

    def trigger_deploy(self, workflow_id: str = "deploy.yml", ref: str = "main") -> str:
        try:
            result = trigger_workflow(self.repo, workflow_id, ref)
            return f"Workflow {workflow_id} triggered on {ref}"
        except Exception as e:
            return f"Workflow trigger error: {e}"

    def workflow_status(self) -> str:
        try:
            runs = list_workflow_runs(self.repo, 5)
            lines = []
            for r in runs:
                icon = "OK" if r.get("conclusion") == "success" else "FAIL"
                lines.append(
                    f"{icon} {r['name']} -- {r['status']} "
                    f"({r.get('conclusion', 'in progress')}) -- {r['created_at'][:10]}"
                )
            return "GitHub Actions Status:\n" + "\n".join(lines) if lines else "No workflow runs found."
        except Exception as e:
            return f"Status error: {e}"

    def execute(self, command: str) -> str:
        cmd = command.lower()
        if "summary" in cmd or "status" in cmd or "info" in cmd:
            return self.repo_summary()
        elif "workflow" in cmd and ("run" in cmd or "status" in cmd):
            return self.workflow_status()
        elif "deploy" in cmd or "trigger" in cmd:
            return self.trigger_deploy()
        elif "branch" in cmd and ("feature" in cmd or "new" in cmd):
            name = command.replace("create", "").replace("branch", "").replace("feature", "").strip()
            return self.new_feature_branch(name or "unnamed-feature")
        elif "bug" in cmd or ("issue" in cmd and "bug" in cmd):
            return self.open_bug_issue(command)
        elif "issue" in cmd and ("open" in cmd or "create" in cmd or "new" in cmd):
            return self.open_issue(command[:80], command)
        elif "pr" in cmd or "pull request" in cmd:
            return self.ai_reviewed_pr("feature/auto", command)
        elif "workflow" in cmd and ("generate" in cmd or "create" in cmd or "add" in cmd):
            return self.generate_and_push_workflow(command)
        else:
            return process_task(
                f"Execute this GitHub operation on repo {self.repo}: {command}\n"
                f"Return exact gh CLI commands or GitHub API calls.",
                "github"
            )


if __name__ == "__main__":
    agent = GitHubAgent()
    print(agent.repo_summary())
