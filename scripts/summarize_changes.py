# import subprocess
# import os
# from pathlib import Path
# import re

# branch = os.environ.get("GITHUB_REF", "").replace("refs/heads/", "")
# sha = (os.environ.get("GITHUB_SHA") or "")[:7]

# # Prepare output folder
# output_dir = Path("outputs")
# output_dir.mkdir(exist_ok=True)
# out_path = output_dir / f"summary_{branch}_{sha}.md"

# def run(cmd):
#     return subprocess.check_output(cmd, shell=True, text=True, errors="ignore").strip()

# # Show file stats & diff
# diff_stat = run("git diff --stat HEAD~1 HEAD || true")
# diff_patch = run("git diff --unified=3 HEAD~1 HEAD || true")

# summary = f"# Code summary — {branch} @ {sha}\n\n"

# if diff_stat:
#     summary += f"## Changed files\n```\n{diff_stat}\n```\n\n"
# else:
#     summary += "_No file changes detected._\n\n"

# # --- Natural Language Explanation ---
# explanation = []
# if diff_patch:
#     for line in diff_patch.splitlines():
#         if line.startswith("+") and not line.startswith("+++"):
#             code_line = line[1:].strip()
#             if code_line.startswith("def "):
#                 func_name = re.findall(r"def\s+(\w+)", code_line)
#                 if func_name:
#                     explanation.append(f"Added function `{func_name[0]}()`.")
#             elif code_line.startswith("class "):
#                 class_name = re.findall(r"class\s+(\w+)", code_line)
#                 if class_name:
#                     explanation.append(f"Introduced class `{class_name[0]}`.")
#             elif "TODO" in code_line:
#                 explanation.append("Added a TODO comment.")
#             elif "print(" in code_line:
#                 explanation.append(f"Added a print statement: `{code_line}`")
#             elif "=" in code_line:
#                 explanation.append(f"New assignment or variable update: `{code_line}`")

#         elif line.startswith("-") and not line.startswith("---"):
#             code_line = line[1:].strip()
#             if code_line.startswith("def "):
#                 func_name = re.findall(r"def\s+(\w+)", code_line)
#                 if func_name:
#                     explanation.append(f"Removed function `{func_name[0]}()`.")
#             elif code_line.startswith("class "):
#                 class_name = re.findall(r"class\s+(\w+)", code_line)
#                 if class_name:
#                     explanation.append(f"Removed class `{class_name[0]}`.")
#             elif "print(" in code_line:
#                 explanation.append(f"Removed print statement: `{code_line}`")
#             else:
#                 explanation.append(f"Removed line: `{code_line}`")

#     if explanation:
#         summary += "## English Summary\n"
#         for exp in explanation:
#             summary += f"- {exp}\n"
#         summary += "\n"

# # Include raw diff for reference
# if diff_patch:
#     summary += f"## Diff details\n```diff\n{diff_patch}\n```\n"
# else:
#     summary += "_No diff details available._\n"

# out_path.write_text(summary)
# print(f"Summary written to {out_path}")
