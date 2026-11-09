#!/usr/bin/env bash
# Start OA Mock (macOS / Linux). Stop it with Ctrl+C (Ctrl+Z only pauses it and keeps the port busy).
# First time? Run ./scripts/setup.sh instead: it installs what's missing and adds the oa-mock command.
cd "$(dirname "$0")"

# Copies from before the app moved into app/ (Nov 2026): a slim clone needs the new folders checked out,
# and the old folders can linger with only Python's caches in them.
if [ ! -f app/run.py ] && [ "$(git config --get core.sparseCheckout 2>/dev/null)" = "true" ]; then
  echo "Fetching the app's new folders (one time)..."
  git sparse-checkout add app scripts || { echo "Couldn't fetch them. Run: git sparse-checkout add app scripts"; exit 1; }
fi
for d in oa_mock web; do
  if [ -d "$d" ] && [ -z "$(find "$d" -type f ! -path '*/__pycache__/*' -print -quit)" ]; then rm -rf "$d"; fi
done

for c in python3 python; do command -v "$c" >/dev/null 2>&1 && exec "$c" app/run.py "$@"; done
echo "Python 3 not found. Run ./scripts/setup.sh first."; exit 1
