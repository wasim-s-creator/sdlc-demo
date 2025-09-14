#!/usr/bin/env python3
import subprocess, os, re, datetime

BASE = os.environ.get("BASE_BRANCH", "origin/main")

def run(cmd):
    return subprocess.check_output(cmd, text=True).strip()

def safe_run(cmd):
    try:
        return run(cmd)
    except subprocess.CalledProcessError:
        return ""

def get_branch_and_sha():
    branch = safe_run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    sha = safe_run(["git", "rev-parse", "--short", "HEAD"])
    return branch, sha

def analyze_diff(diff_text):
    added, removed = 0, 0
    todos, funcs_added = [], []
    for line in diff_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
            if "TODO" in line or "FIXME" in line:
                todos.append(line.strip()[1:])
            m = re.match(r"^\+\s*def\s+(\w+)\(", line)
            if m:
                funcs_added.append(m.group(1))
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    return added, removed, funcs_added, todos

def main():
    branch, sha = get_branch_and_sha()
    subprocess.run(["git", "fetch", "origin", "main"], check=False)
    diff_files = safe_run(["git", "diff", "--name-only", f"{BASE}..HEAD"]).splitlines()

    if not diff_files:
        print("No changes detected.")
        return

    summary = [f"# Code summary — {branch} @ {sha}", ""]
    for f in diff_files:
        diff_text = safe_run(["git", "diff", "--unified=0", f"{BASE}..HEAD", "--", f])
        added, removed, funcs, todos = analyze_diff(diff_text)
        line = f"- `{f}`: +{added}/-{removed}"
        if funcs:
            line += f"; functions added: {', '.join(funcs)}"
        if todos:
            line += f"; TODOs: {len(todos)}"
        summary.append(line)

    os.makedirs("outputs", exist_ok=True)
    out_file = f"outputs/summary_{branch}_{sha}.md"
    with open(out_file, "w") as f:
        f.write("\n".join(summary))

    print("\n".join(summary))

if __name__ == "__main__":
    main()
