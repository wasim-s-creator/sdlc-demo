import subprocess
import os
from pathlib import Path

# Get branch & commit sha
branch = os.environ.get("GITHUB_REF", "").replace("refs/heads/", "")
sha = (os.environ.get("GITHUB_SHA") or "")[:7]

# Prepare output folder
output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)
out_path = output_dir / f"summary_{branch}_{sha}.md"

def run(cmd):
    return subprocess.check_output(cmd, shell=True, text=True).strip()

# Show what changed in the last commit
diff_stat = run("git diff --stat HEAD~1 HEAD || true")
diff_patch = run("git diff --unified=3 HEAD~1 HEAD || true")

summary = f"# Code summary — {branch} @ {sha}\n\n"
if diff_stat:
    summary += f"## Changed files\n```\n{diff_stat}\n```\n\n"
else:
    summary += "_No file changes detected._\n\n"

if diff_patch:
    summary += f"## Diff details\n```diff\n{diff_patch}\n```\n"
else:
    summary += "_No diff details available._\n"

# Save to file
out_path.write_text(summary)
print(f"Summary written to {out_path}")
