#!/usr/bin/env bash
# One-line install for macOS and Linux:
#   curl -fsSL https://raw.githubusercontent.com/rgabhi/oa-mock/main/install.sh | bash
# Makes a slim clone in ./oa-mock (the app + Flipkart's questions, ~4 MB; download more companies on the
# home page), then runs ./setup.sh. Options after "bash -s --" go to setup.sh, e.g.  | bash -s -- --no-java
# OA_DIR=path changes the folder; OA_FULL=1 clones every company.
set -eu
REPO="${OA_REPO:-https://github.com/rgabhi/oa-mock.git}"
DIR="${OA_DIR:-oa-mock}"
SAMPLE="flipkart"
have() { command -v "$1" >/dev/null 2>&1; }
say()  { printf '\033[1m%s\033[0m\n' "$1"; }

if ! have git; then
  say "git is needed. Installing it..."
  if [ "$(uname -s)" = "Darwin" ]; then
    xcode-select --install 2>/dev/null || true
    echo "Finish the Apple Command Line Tools installer (it includes git), then run this command again."; exit 1
  fi
  S=""; [ "$(id -u)" -ne 0 ] && have sudo && S="sudo"
  if   have apt-get; then $S apt-get update -y >/dev/null && $S apt-get install -y git
  elif have dnf;     then $S dnf install -y git
  elif have yum;     then $S yum install -y git
  elif have pacman;  then $S pacman -S --needed --noconfirm git
  elif have zypper;  then $S zypper install -y git
  elif have apk;     then $S apk add git
  fi
  have git || { echo "Couldn't install git. Install it with your package manager and run this again."; exit 1; }
fi

# Slim clones need git 2.27+ (partial clone + cone-mode sparse checkout).
ver="$(git --version | sed 's/[^0-9.]*\([0-9][0-9]*\)\.\([0-9][0-9]*\).*/\1 \2/')"
major="${ver% *}"; minor="${ver#* }"
slim=1; { [ "$major" -lt 2 ] || { [ "$major" -eq 2 ] && [ "$minor" -lt 27 ]; }; } && slim=0
[ "${OA_FULL:-0}" = 1 ] && slim=0

if [ -d "$DIR/.git" ]; then
  say "$DIR already exists: updating it"
  git -C "$DIR" pull --ff-only || true
elif [ -e "$DIR" ]; then
  echo "$DIR exists and isn't an OA Mock clone. Set OA_DIR to another folder."; exit 1
elif [ "$slim" = 1 ]; then
  say "Downloading OA Mock (slim: the app + $SAMPLE)"
  git clone --filter=blob:none --sparse "$REPO" "$DIR"
  git -C "$DIR" sparse-checkout set --cone $(git -C "$DIR" ls-tree -d --name-only HEAD | grep -vx data) "data/$SAMPLE"
else
  say "Downloading OA Mock (every company)"
  git clone "$REPO" "$DIR"
fi

cd "$DIR"
say "Setting up in $(pwd)"
exec bash ./setup.sh "$@"
