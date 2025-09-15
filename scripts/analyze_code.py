import subprocess
import os
from pathlib import Path

branch = os.environ.get("GITHUB_REF", "").replace("refs/heads/", "")
sha = (os.environ.get("GITHUB_SHA") or "")[:7]

# Prepare output folder
output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)
out_path = output_dir / f"analysis_{branch}_{sha}.md"

def run(cmd):
    """Run a shell command and return output"""
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    return result.stdout.strip()

summary = f"# Code Analysis Report — {branch} @ {sha}\n\n"

# Syntax & linting checks
summary += "## Flake8 Linting\n```\n" + run("flake8 . || true") + "\n```\n\n"
summary += "## Pylint Report\n```\n" + run("pylint **/*.py || true") + "\n```\n\n"
summary += "## Type Checking (mypy)\n```\n" + run("mypy . || true") + "\n```\n\n"

# Formatting suggestions
summary += "## Formatting suggestions\n```\n" + run("black --check . || true") + "\n```\n"
summary += "## Import sorting check\n```\n" + run("isort --check-only . || true") + "\n```\n"

out_path.write_text(summary)
print(f"Analysis written to {out_path}")