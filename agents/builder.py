"""Empire Builder - Clone repos, analyze with Claude, generate new modules."""
import os
import subprocess
import shutil
import anthropic
from typing import Optional, List

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

class EmpireBuilder:
    """Clones repos, analyzes them, and builds new empire modules."""

    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        )

    def clone_and_analyze(self, source_repo: str, build_prompt: str, max_files: int = 15) -> str:
        """
        Clone a repo, read key files, and ask Claude to build something new.

        Args:
            source_repo: GitHub URL to clone
            build_prompt: What to build based on the repo
            max_files: How many files to feed to Claude
        """
        tmp_dir = f"/tmp/empire_build_{os.urandom(4).hex()}"
        repo_name = source_repo.rstrip("/").split("/")[-1].replace(".git", "")

        try:
            # Clone
            print(f"[BUILDER] Cloning {source_repo}...")
            subprocess.run(
                ["git", "clone", "--depth", "1", source_repo, tmp_dir],
                check=True, capture_output=True, text=True
            )

            # Read files
            files = self._read_repo_files(tmp_dir, max_files)

            # Ask Claude
            print(f"[BUILDER] Sending {len(files)} files to Claude...")
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8192,
                system="""You are the Empire Builder. You analyze GitHub repositories and generate production-ready Python code for the OpenClaw bot swarm. 

Rules:
- Generate complete, working Python files
- Use FastAPI, discord.py, python-telegram-bot, slack-bolt
- Follow the existing OpenClaw architecture patterns
- Include proper error handling and logging
- Output code in ```python blocks with file paths as comments""",
                messages=[{
                    "role": "user",
                    "content": f"""Source repo: {source_repo}

Repository files:
{chr(10).join(files)}

Build instruction: {build_prompt}

Generate complete, production-ready Python code. Include file paths in comments."""
                }]
            )

            return response.content[0].text

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _read_repo_files(self, repo_path: str, max_files: int) -> List[str]:
        """Read key source files from cloned repo."""
        files = []
        extensions = (".py", ".js", ".ts", ".md", ".json", ".yaml", ".yml", ".toml")

        for root, _, filenames in os.walk(repo_path):
            # Skip common non-source dirs
            if any(skip in root for skip in [".git", "node_modules", "__pycache__", ".venv", "venv"]):
                continue

            for filename in filenames:
                if filename.endswith(extensions):
                    path = os.path.join(root, filename)
                    rel = os.path.relpath(path, repo_path)
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            # Skip huge files
                            if len(content) > 10000:
                                content = content[:10000] + "\n... [truncated]"
                            files.append(f"--- {rel} ---\n{content}")
                    except Exception:
                        pass

                    if len(files) >= max_files:
                        return files
        return files

    def save_build(self, claude_output: str, output_dir: str = "agents/generated") -> List[str]:
        """Parse Claude's output and save generated files."""
        os.makedirs(output_dir, exist_ok=True)
        saved = []

        # Simple parser for ```python blocks
        import re
        blocks = re.findall(r"```python\n(.*?)```", claude_output, re.DOTALL)

        for i, block in enumerate(blocks):
            # Try to extract filename from first comment
            fname_match = re.search(r"#\s*(\S+\.py)", block)
            fname = fname_match.group(1) if fname_match else f"generated_{i}.py"

            path = os.path.join(output_dir, fname)
            with open(path, "w") as f:
                f.write(block)
            saved.append(path)
            print(f"[BUILDER] Saved: {path}")

        return saved
