#!/usr/bin/env bash
# OA Mock setup for macOS and Linux (run it from the app's folder):
#   ./scripts/setup.sh               install what's missing (Python 3, C++, Java), add the oa-mock command, start the mock
#   ./scripts/setup.sh --no-java     skip the JDK
#   ./scripts/setup.sh --no-start    set up only, don't start the runner
#   ./scripts/setup.sh --no-command  don't add the oa-mock command
#   ./scripts/setup.sh --only cpp    set up just one language (python, cpp or java); implies --no-start
#   ./scripts/setup.sh --gui-auth    ask for the password in the system's own dialog instead of the terminal
#                                    (the app uses this when you install a language from the language menu)
set -u
cd "$(dirname "$0")/.."   # the app's folder

WANT_JAVA=1; START=1; ONLY=""; GUI_AUTH=0; MAKE_CMD=1
while [ $# -gt 0 ]; do
  case "$1" in
    --no-java) WANT_JAVA=0 ;;
    --no-start) START=0 ;;
    --no-command) MAKE_CMD=0 ;;
    --only) shift; ONLY="${1:-}"; START=0
            case "$ONLY" in python|cpp|java) ;; *) echo "--only needs python, cpp or java"; exit 2 ;; esac ;;
    --gui-auth) GUI_AUTH=1 ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1"; exit 2 ;;
  esac
  shift
done

if [ -t 1 ]; then
  ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
  warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }
  step() { printf '\n\033[1m%s\033[0m\n' "$1"; }
else   # output goes to the app's progress log: no colours
  ok()   { printf '  ✓ %s\n' "$1"; }
  warn() { printf '  ! %s\n' "$1"; }
  step() { printf '\n%s\n' "$1"; }
fi
have() { command -v "$1" >/dev/null 2>&1; }
want() { [ -z "$ONLY" ] || [ "$ONLY" = "$1" ]; }

OS="$(uname -s)"
if [ "$OS" = "Darwin" ]; then   # started from the app, PATH may not include Homebrew
  for d in /opt/homebrew/bin /usr/local/bin; do
    [ -d "$d" ] && case ":$PATH:" in *":$d:"*) ;; *) PATH="$d:$PATH" ;; esac
  done
  export PATH
fi

PM=""
if [ "$OS" = "Darwin" ]; then PM="brew"
elif have apt-get; then PM="apt"
elif have dnf; then PM="dnf"
elif have yum; then PM="yum"
elif have pacman; then PM="pacman"
elif have zypper; then PM="zypper"
elif have apk; then PM="apk"
fi

PROMPT="OA Mock needs your password to install a programming language."
TMP_DIR=""
cleanup() { [ -n "$TMP_DIR" ] && rm -rf "$TMP_DIR"; }
trap cleanup EXIT
tmpdir() { [ -n "$TMP_DIR" ] || TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/oamock-setup.XXXXXX")"; }

# as_root "<command>": run one shell command as root, asking for the password once.
# In a terminal that's sudo. With --gui-auth it's the system's own dialog:
#   macOS: the administrator dialog (osascript);  Linux: pkexec (polkit), else sudo -A with zenity/kdialog/ssh-askpass.
as_root() {
  if [ "$(id -u)" -eq 0 ]; then sh -c "$1"; return; fi
  if [ "$OS" = "Darwin" ]; then
    if [ "$GUI_AUTH" = 1 ]; then
      local out rc
      out="$(osascript -e 'on run argv' -e "do shell script (item 1 of argv) with prompt \"$PROMPT\" with administrator privileges" -e 'end run' "$1" 2>&1)"; rc=$?
      [ -n "$out" ] && printf '%s\n' "$out"
      case "$out" in *"-128"*) warn "The password dialog was cancelled, so nothing was installed." ;; esac
      return $rc
    else
      sudo sh -c "$1"
    fi
    return
  fi
  if have sudo && sudo -n true 2>/dev/null; then sudo -n sh -c "$1"; return; fi   # no password needed
  if [ "$GUI_AUTH" = 0 ]; then
    if have sudo; then sudo sh -c "$1"; return; fi
    warn "This step needs root and sudo isn't installed. Run it as root."; return 1
  fi
  if [ -z "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then
    warn "There's no desktop session to show a password dialog in. Run this in a terminal instead: ./scripts/setup.sh --only ${ONLY:-cpp}"
    return 1
  fi
  if have pkexec; then
    echo "  Asking for your password (system dialog)..."
    pkexec /bin/sh -c "$1"; local rc=$?
    case $rc in 126|127) warn "The password dialog was cancelled or the password was refused, so nothing was installed." ;; esac
    return $rc
  fi
  if have sudo; then
    tmpdir; local ap="$TMP_DIR/askpass"
    if have zenity; then printf '#!/bin/sh\nexec zenity --password --title="OA Mock"\n' > "$ap"
    elif have kdialog; then printf '#!/bin/sh\nexec kdialog --title "OA Mock" --password "%s"\n' "$PROMPT" > "$ap"
    elif have ssh-askpass; then printf '#!/bin/sh\nexec ssh-askpass "%s"\n' "$PROMPT" > "$ap"
    elif have ksshaskpass; then printf '#!/bin/sh\nexec ksshaskpass "%s"\n' "$PROMPT" > "$ap"
    else ap=""; fi
    if [ -n "$ap" ]; then
      chmod 700 "$ap"; echo "  Asking for your password (system dialog)..."
      SUDO_ASKPASS="$ap" sudo -A sh -c "$1"; return
    fi
  fi
  warn "No password dialog is available (install pkexec, zenity or kdialog). Run this in a terminal instead: ./scripts/setup.sh --only ${ONLY:-cpp}"
  return 1
}

pkg_install() {   # pkg_install <apt> <dnf/yum> <pacman> <zypper> <apk> <brew>
  local c=""
  case "$PM" in
    apt)    c="export DEBIAN_FRONTEND=noninteractive; apt-get update -y >/dev/null && apt-get install -y $1" ;;
    dnf)    c="dnf install -y $2" ;;
    yum)    c="yum install -y $2" ;;
    pacman) c="pacman -S --needed --noconfirm $3" ;;
    zypper) c="zypper --non-interactive install $4" ;;
    apk)    c="apk add $5" ;;
    brew)   if have brew; then brew install $6; return; else return 1; fi ;;   # Homebrew refuses to run as root
    *)      return 1 ;;
  esac
  as_root "$c"
}

python_ok() { "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; }

echo "OA Mock setup ($OS)"
RESULT=0   # with --only: 1 if that language still isn't usable

# ---------- Python ----------
PY=""
if want python || [ "$START" = 1 ]; then
  step "1/3 Python 3.8+"
  for c in python3 python; do have "$c" && python_ok "$c" && { PY="$c"; break; }; done
  if [ -z "$PY" ]; then
    warn "Python 3.8+ not found. Installing..."
    if [ "$OS" = "Darwin" ] && ! have brew; then
      warn "Install Python from https://www.python.org/downloads/macos/ (or install Homebrew from https://brew.sh), then run ./scripts/setup.sh again."
      exit 1
    fi
    pkg_install python3 python3 python python3 python3 python || { warn "Couldn't install Python automatically. Install Python 3.8+ and run this again."; exit 1; }
    for c in python3 python; do have "$c" && python_ok "$c" && { PY="$c"; break; }; done
    [ -z "$PY" ] && { warn "Python still not found on PATH. Open a new terminal and run this again."; exit 1; }
  fi
  ok "$($PY --version 2>&1) ($(command -v $PY))"
fi

# ---------- C++ ----------
clt_ready() { xcode-select -p >/dev/null 2>&1 && /usr/bin/clang++ --version >/dev/null 2>&1; }   # -p first: the clang++ stub opens an installer
if want cpp; then
  step "2/3 C++ compiler (for C++17 answers)"
  CXX=""
  for c in g++ clang++; do
    if [ "$OS" = "Darwin" ] && ! xcode-select -p >/dev/null 2>&1 && [ "$(command -v "$c")" = "/usr/bin/$c" ]; then continue; fi
    if have "$c" && "$c" --version >/dev/null 2>&1; then CXX="$c"; break; fi
  done
  if [ -n "$CXX" ]; then
    ok "$("$CXX" --version 2>/dev/null | head -1)"
  elif [ "$OS" = "Darwin" ]; then
    warn "No compiler yet. Opening the Apple Command Line Tools installer..."
    xcode-select --install 2>/dev/null || true
    if [ -n "$ONLY" ]; then
      echo "  Finish the installer window that just opened (about 5 to 15 minutes). Waiting for it..."
      i=0
      while [ $i -lt 720 ] && ! clt_ready; do sleep 5; i=$((i + 1)); done
      if clt_ready; then ok "$(/usr/bin/clang++ --version | head -1) (Apple clang works: the runner supplies <bits/stdc++.h>)"
      else warn "The Command Line Tools aren't installed yet. Finish the installer, then try again."; RESULT=1; fi
    else
      warn "Finish the installer window, then run ./scripts/setup.sh again. (Apple clang works: the runner supplies <bits/stdc++.h>.)"
    fi
  else
    warn "Installing g++..."
    if pkg_install g++ gcc-c++ gcc gcc-c++ g++ gcc && have g++; then ok "$(g++ --version | head -1)"
    else warn "Couldn't install g++. Install it with your package manager. Python and JavaScript answers still work."; RESULT=1; fi
  fi
fi

# ---------- Java ----------
java_ok() {
  if [ "$OS" = "Darwin" ]; then   # /usr/bin/javac is a stub until a JDK is installed; java_home asks silently
    for d in /opt/homebrew/opt/openjdk/bin /usr/local/opt/openjdk/bin; do [ -x "$d/javac" ] && "$d/javac" -version >/dev/null 2>&1 && return 0; done
    /usr/libexec/java_home >/dev/null 2>&1 || return 1
  fi
  have javac || return 1
  javac -version >/dev/null 2>&1
}
java_ver() {
  for j in /opt/homebrew/opt/openjdk/bin/javac /usr/local/opt/openjdk/bin/javac javac; do
    "$j" -version >/dev/null 2>&1 && { "$j" -version 2>&1 | tail -1; return; }
  done
}
temurin_pkg() {   # macOS without Homebrew: Eclipse Temurin 21's .pkg installer
  local arch; arch="$(uname -m)"; [ "$arch" = "arm64" ] && arch="aarch64"; [ "$arch" = "x86_64" ] && arch="x64"
  tmpdir; local pkg="$TMP_DIR/temurin-21.pkg"
  echo "  Downloading Eclipse Temurin 21 (about 180 MB)..."
  curl -fsSL --retry 2 -o "$pkg" "https://api.adoptium.net/v3/installer/latest/21/ga/mac/$arch/jdk/hotspot/normal/eclipse" || { warn "Download failed."; return 1; }
  echo "  Installing it (asks for your password)..."
  as_root "/usr/sbin/installer -pkg '$pkg' -target /"
}
if want java; then
  step "3/3 Java JDK (for Java answers)"
  if java_ok; then
    ok "$(java_ver)"
  elif [ "$WANT_JAVA" = 0 ]; then
    warn "Skipped (--no-java). C++, Python and JavaScript still work."
  else
    warn "No JDK found. Installing..."
    if [ "$OS" = "Darwin" ]; then
      if have brew; then
        brew install openjdk && {
          JH="$(brew --prefix openjdk)"
          if [ -d /Library/Java/JavaVirtualMachines ] && [ ! -e /Library/Java/JavaVirtualMachines/openjdk.jdk ]; then
            if [ "$GUI_AUTH" = 1 ]; then   # the mock finds Homebrew's JDK by itself; the link is only for Terminal
              echo "  To use java in Terminal too: sudo ln -sfn $JH/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk.jdk"
            else
              sudo ln -sfn "$JH/libexec/openjdk.jdk" /Library/Java/JavaVirtualMachines/openjdk.jdk 2>/dev/null || true
            fi
          fi
          export PATH="$JH/bin:$PATH"
        }
      else
        temurin_pkg || warn "Install a JDK from https://adoptium.net (or install Homebrew from https://brew.sh and run this again)."
      fi
    else
      pkg_install default-jdk-headless java-21-openjdk-devel jdk-openjdk java-21-openjdk-devel openjdk21 openjdk || true
    fi
    if java_ok; then ok "$(java_ver)"; else warn "No JDK. Java answers won't run; everything else does."; RESULT=1; fi
  fi
fi

if [ -n "$ONLY" ]; then exit $RESULT; fi

# ---------- the oa-mock command ----------
CMD_NOTE=""
if [ "$MAKE_CMD" = 1 ]; then
  step "The oa-mock command"
  BIN="$HOME/.local/bin"
  here="$(pwd)"; q="$(printf '%s' "$here" | sed "s/'/'\\\\''/g")"   # quoted for the script below
  if mkdir -p "$BIN" && cat > "$BIN/oa-mock" <<LAUNCHER
#!/bin/sh
# Starts OA Mock from any folder. Made by scripts/setup.sh; run that again if you move the app.
if [ ! -x '$q/start.sh' ]; then
  echo "OA Mock isn't in $here any more. Run ./scripts/setup.sh --no-start in its new folder."; exit 1
fi
exec '$q/start.sh' "\$@"
LAUNCHER
  then
    chmod +x "$BIN/oa-mock"
    case ":$PATH:" in
      *":$BIN:"*) ok "Type oa-mock in any terminal to start the mock." ;;
      *)
        case "$(basename "${SHELL:-sh}")" in
          zsh)  RC="$HOME/.zshrc" ;;
          bash) if [ "$OS" = "Darwin" ]; then RC="$HOME/.bash_profile"; else RC="$HOME/.bashrc"; fi ;;
          *)    RC="$HOME/.profile" ;;
        esac
        if ! grep -qs 'OA Mock setup' "$RC"; then
          printf '\n# added by OA Mock setup, for the oa-mock command\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$RC"
        fi
        ok "Type oa-mock in a new terminal window to start the mock (~/.local/bin was added to PATH in ~/${RC##*/})."
        CMD_NOTE=" (in new terminal windows)" ;;
    esac
  else
    warn "Couldn't create $BIN/oa-mock. Start the mock with ./start.sh instead."
  fi
fi

step "Done"
if [ "$OS" = "Darwin" ]; then
  ok "Start the mock any time: oa-mock$CMD_NOTE, ./start.sh in this folder, or double-click Start OA Mock.command in Finder."
else
  ok "Start the mock any time: oa-mock$CMD_NOTE, or ./start.sh in this folder."
fi
ok "Stop it with Ctrl+C."

if [ "$START" = 1 ]; then
  echo
  exec "$PY" app/run.py
fi
