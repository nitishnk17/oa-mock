"""Installing C++ or Java from the app: runs the setup script for just that language in the background.

  status()               {langs: {cpp: {ok, desc, plan}, java: ...}, job}
  start("install", lang) scripts/setup.sh --only <lang> --gui-auth   (scripts/setup.ps1 -Only <lang> on Windows)
  start("cancel")        stops the running install

The password is never typed into the page. The operating system asks for it:
  macOS    C++: Apple's Command Line Tools installer window. Java: Homebrew (no password), or the
           Temurin .pkg through the administrator dialog (osascript).
  Linux    pkexec (the desktop's polkit dialog), else sudo -A with zenity / kdialog / ssh-askpass.
           Nothing to ask if you're root or sudo needs no password. Without a desktop session there's
           no dialog to show, so the page says which command to run in a terminal instead.
  Windows  winget; Windows shows its UAC prompt when an installer needs it.

Only the fixed script with a language from LANGS runs, so the page can't start anything else.
After the script finishes, judge.detect() looks for the compilers again; no restart needed.
"""
import os, shutil, signal, subprocess, sys, threading, time

from . import data, judge

ROOT = data.ROOT
LANGS = {"cpp": "C++", "java": "Java"}
IS_WIN, IS_MAC = os.name == "nt", sys.platform == "darwin"
TIMEOUT_S = 75 * 60          # the Command Line Tools installer alone can take 15+ minutes
_job = {"id": 0, "state": "idle"}
_proc = None
_lock = threading.Lock()
_plan_cache = {}             # lang -> (time, plan)


def _have(c):
    return shutil.which(c) is not None


def _pm():
    for name, cmd in (("apt", "apt-get"), ("dnf", "dnf"), ("yum", "yum"), ("pacman", "pacman"), ("zypper", "zypper"), ("apk", "apk")):
        if _have(cmd):
            return name
    return None


def _sudo_free():
    if not _have("sudo"):
        return False
    try:
        return subprocess.run(["sudo", "-n", "true"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              stdin=subprocess.DEVNULL, timeout=5).returncode == 0
    except Exception:
        return False


def _script():
    return os.path.join(ROOT, "scripts", "setup.ps1" if IS_WIN else "setup.sh")


def _terminal_cmd(lang):
    return ("powershell -ExecutionPolicy Bypass -File scripts\\setup.ps1 -Only %s" % lang) if IS_WIN else ("./scripts/setup.sh --only %s" % lang)


def plan(lang):
    """What installing `lang` here would do: {can, what, auth, terminal, why?}."""
    hit = _plan_cache.get(lang)
    if hit and time.time() - hit[0] < 30:
        return hit[1]
    p = {"can": True, "terminal": _terminal_cmd(lang)}
    if not os.path.isfile(_script()):
        p.update(can=False, why="%s is missing from this copy of the app." % os.path.basename(_script()))
    elif IS_WIN:
        if not _have("winget"):
            p.update(can=False, why="winget isn't available. Install “App Installer” from the Microsoft Store, then try again.")
        else:
            p.update(what="WinLibs GCC with winget" if lang == "cpp" else "Eclipse Temurin 21 with winget",
                     auth="Windows may ask you to allow the installer (UAC).")
    elif IS_MAC:
        if lang == "cpp":
            p.update(what="Apple's Command Line Tools (clang)",
                     auth="An Apple installer window opens. Click Install there; it takes 5 to 15 minutes.")
        elif _have("brew") or os.path.exists("/opt/homebrew/bin/brew") or os.path.exists("/usr/local/bin/brew"):
            p.update(what="OpenJDK with Homebrew", auth="No password needed.")
        else:
            p.update(what="Eclipse Temurin 21 (about 180 MB download)", auth="macOS asks for your password in its own dialog.")
    else:
        pm = _pm()
        pkg = {"cpp": "g++", "java": "a JDK"}[lang]
        if not pm:
            p.update(can=False, why="No supported package manager (apt, dnf, yum, pacman, zypper, apk) was found. Install %s yourself." % pkg)
        else:
            p["what"] = "%s with %s" % (pkg, {"apt": "apt-get"}.get(pm, pm))
            gui = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
            askpass = _have("sudo") and any(_have(a) for a in ("zenity", "kdialog", "ssh-askpass", "ksshaskpass"))
            if hasattr(os, "geteuid") and os.geteuid() == 0:
                p["auth"] = "No password needed (running as root)."
            elif _sudo_free():
                p["auth"] = "No password needed (sudo is already allowed)."
            elif gui and (_have("pkexec") or askpass):
                p["auth"] = "Your system asks for your password in its own dialog."
            else:
                p.update(can=False, why="There's no way to show a password dialog here (no desktop session, or no pkexec / zenity / kdialog). "
                                        "Run this in a terminal in the app's folder instead:")
    _plan_cache[lang] = (time.time(), p)
    return p


def status():
    judge_ok = judge.available()
    desc = {"cpp": judge.GPP_DESC if judge.GPP else "", "java": judge.JAVAC or ""}
    return {"langs": {l: {"ok": judge_ok[l], "desc": desc[l], "plan": None if judge_ok[l] else plan(l)} for l in LANGS},
            "job": job()}


def job():
    with _lock:
        return dict(_job)


def _clean(line):
    """winget redraws a spinner with carriage returns; keep what's left on the line."""
    line = line.rstrip("\n").split("\r")[-1]
    return line if line.strip(" -\\|/█▒") else ""


def _run(lang):
    global _proc
    if IS_WIN:
        args = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", _script(), "-Only", lang]
        extra = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    else:
        args = ["bash", _script(), "--only", lang, "--gui-auth"]
        extra = {"start_new_session": True}
    log, err = [], None
    def say(line):
        with _lock:
            log.append(line); _job["log"] = "\n".join(log)[-8000:]
    try:
        p = subprocess.Popen(args, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **extra)
        with _lock:
            _proc = p
        killer = threading.Timer(TIMEOUT_S, lambda: _stop(p))
        killer.daemon = True; killer.start()
        for raw in iter(p.stdout.readline, b""):
            line = _clean(raw.decode("utf-8", "replace"))
            if line:
                say(line)
        rc = p.wait()
        killer.cancel()
        if _job.get("cancelled"):
            err = "Cancelled."
        elif rc == 2:
            err = "The setup script didn't accept the request."
    except Exception as e:
        err = "Couldn't run the setup script: %s" % e
    finally:
        with _lock:
            _proc = None
    judge.detect()
    _plan_cache.clear()
    ok = judge.available()[lang]
    with _lock:
        if ok and not err:
            _job.update(state="done", finished=time.time(), desc=judge.GPP_DESC if lang == "cpp" else judge.JAVAC)
        else:
            warns = [l.strip(" !") for l in log if l.lstrip().startswith("!") and not l.rstrip().endswith("...")]
            _job.update(state="failed", finished=time.time(),
                        error=err or (warns[0] if warns else "%s still isn't available." % LANGS[lang]))


def _stop(p):
    try:
        if IS_WIN:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.killpg(p.pid, signal.SIGTERM)
    except Exception:
        try: p.terminate()
        except Exception: pass


def start(action, lang=None):
    """action: install | cancel. Returns the job, or raises ValueError with a reason."""
    if action == "cancel":
        with _lock:
            p = _proc
            if _job.get("state") != "running" or p is None:
                raise ValueError("nothing is installing")
            _job["cancelled"] = True
        _stop(p)
        return job()
    if action != "install":
        raise ValueError("unknown action")
    if lang not in LANGS:
        raise ValueError("unknown language")
    if judge.available()[lang]:
        raise ValueError("%s is already installed" % LANGS[lang])
    pl = plan(lang)
    if not pl["can"]:
        raise ValueError(pl["why"] + " " + pl["terminal"])
    with _lock:
        if _job.get("state") == "running":
            raise ValueError("%s is still installing" % LANGS.get(_job.get("lang"), "Another language"))
        _job.clear()
        _job.update(id=int(time.time() * 1000), lang=lang, state="running", log="", started=time.time(), what=pl.get("what"), auth=pl.get("auth"))
        snapshot = dict(_job)
    threading.Thread(target=_run, args=(lang,), daemon=True).start()
    return snapshot
