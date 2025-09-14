import subprocess
import sys

def get_diff():
    # Get diff for the last commit
    result = subprocess.run(
        ["git", "diff", "HEAD~1", "HEAD"],
        capture_output=True,
        text=True
    )
    return result.stdout

def summarize(diff: str) -> str:
    summary = []
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            file = line.replace("+++ b/", "")
            summary.append(f"📂 File changed: `{file}`")
        elif line.startswith("+") and not line.startswith("+++"):
            summary.append(f"➕ Added: `{line[1:].strip()}`")
        elif line.startswith("-") and not line.startswith("---"):
            summary.append(f"➖ Removed: `{line[1:].strip()}`")
    if not summary:
        return "No meaningful changes detected."
    return "\n".join(summary)

if __name__ == "__main__":
    diff = get_diff()
    english_summary = summarize(diff)
    print("## 🔎 Code Summary\n")
    print(english_summary)
