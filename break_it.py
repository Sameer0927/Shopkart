"""The 'Deploy bad commit' button for your demo.

It removes the null check from apply_discount(), commits it with a
believable message, and pushes to GitHub. Your deploy step (or you,
restarting the app) then runs the broken code.

Run:  python break_it.py
"""
import subprocess

FILE = "app.py"
SAFE = (
    "    if not coupon:  # null check\n"
    "        return total  # null check\n"
)

src = open(FILE).read()
if SAFE not in src:
    raise SystemExit("Null check already removed. Nothing to break.")

open(FILE, "w").write(src.replace(SAFE, ""))
subprocess.run(["git", "add", FILE], check=True)
subprocess.run(["git", "commit", "-m", "refactor discount calc"], check=True)
subprocess.run(["git", "push"], check=True)
print("Bad commit pushed. Restart the app (or let auto-deploy do it).")
