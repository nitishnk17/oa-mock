"""Compiles and runs submitted code with the compilers on this computer.

C++17 uses the newest GCC it can find (Homebrew g++-NN on macOS; WinLibs/MSYS2 on Windows),
then clang++. Set OA_CXX to force a compiler. Apple clang lacks <bits/stdc++.h> and old
MinGW GCC (< 10) ships a broken one in C++17 mode, so a shim header is used for those.
Java uses javac/java from a JDK; Python uses the interpreter running this server.
"""
import glob, os, re, shutil, subprocess, sys, tempfile, time

IS_WIN = os.name == "nt"

def which(*names):
    for n in names:
        p = shutil.which(n)
        if p: return p
    return None

IS_MAC = sys.platform == "darwin"

# bits/stdc++.h replacement, used when the compiler's own one is missing (Apple clang)
# or broken (MinGW GCC 8/9 on Windows: its <filesystem> doesn't compile in C++17 mode).
SHIM_HEADERS = """#pragma once
""" + "".join("#include <%s>\n" % h for h in (
    "cassert cctype cerrno cfloat cinttypes climits cmath cstdarg cstddef cstdint cstdio cstdlib cstring ctime "
    "cwchar cwctype algorithm array bitset chrono complex deque exception fstream functional initializer_list "
    "iomanip ios iosfwd iostream istream iterator limits list locale map memory new numeric optional ostream "
    "queue random ratio regex set sstream stack stdexcept streambuf string string_view tuple type_traits "
    "typeinfo unordered_map unordered_set utility valarray variant vector").split())


def _gcc_major(path):
    try:
        v = subprocess.run([path, "-dumpversion"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20).stdout.decode().strip()
        return int(v.split(".")[0])
    except Exception:
        return 0


def _candidates():
    """Every C++ compiler we can find, most specific first."""
    c = []
    if os.environ.get("OA_CXX"):
        c.append(os.environ["OA_CXX"])
    for d in ("/opt/homebrew/bin", "/usr/local/bin", "/home/linuxbrew/.linuxbrew/bin"):
        c += glob.glob(os.path.join(d, "g++-[0-9]*"))
    if IS_WIN:
        la = os.environ.get("LOCALAPPDATA", "")
        c += glob.glob(os.path.join(la, "Microsoft", "WinGet", "Links", "g++.exe"))
        c += glob.glob(os.path.join(la, "Microsoft", "WinGet", "Packages", "BrechtSanders.WinLibs*", "mingw*", "bin", "g++.exe"))
        for root in ("C:\\msys64", "C:\\mingw64", "C:\\mingw-w64"):
            c += glob.glob(os.path.join(root, "*", "bin", "g++.exe")) + glob.glob(os.path.join(root, "bin", "g++.exe"))
    for n in ["g++-%d" % v for v in range(16, 9, -1)] + ["g++", "clang++"]:
        p = shutil.which(n)
        if p:
            c.append(p)
    # macOS: /usr/bin/g++ and clang++ are stubs that open Apple's installer until the Command Line Tools are in
    clt = True
    if IS_MAC:
        try: clt = subprocess.run(["xcode-select", "-p"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20).returncode == 0
        except Exception: clt = False
    seen, out = set(), []
    for p in c:
        k = os.path.normcase(os.path.realpath(p))
        if not clt and k.startswith("/usr/bin/"):
            continue
        if k not in seen and os.path.isfile(p):
            seen.add(k); out.append(p)
    return out


def find_cxx():
    """The compiler to use: OA_CXX if set, else the newest real GCC, else clang.

    Returns (path, is_clang, gcc_major, first line of --version)."""
    best = None
    for c in _candidates():
        try:
            v = subprocess.run([c, "--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20).stdout.decode("utf-8", "replace")
        except Exception:
            continue
        if not v.strip():
            continue
        clang = "clang" in v.lower() or "apple" in v.lower()
        cand = (c, clang, 0 if clang else _gcc_major(c), v.splitlines()[0])
        if os.environ.get("OA_CXX") and c == os.environ["OA_CXX"]:
            return cand
        rank = (not clang, cand[2])          # any GCC beats clang; newer GCC beats older
        if best is None or rank > best[0]:
            best = (rank, cand)
    return best[1] if best else (None, False, 0, "")


SHIM_DIR = os.path.join(tempfile.gettempdir(), "oamock_shim")
os.makedirs(os.path.join(SHIM_DIR, "bits"), exist_ok=True)
with open(os.path.join(SHIM_DIR, "bits", "stdc++.h"), "w") as f:
    f.write(SHIM_HEADERS)


def _java_dirs():
    """JDK bin folders that often aren't on PATH: Homebrew's keg-only openjdk, Temurin/Microsoft JDKs on Windows."""
    if IS_MAC:
        return ["/opt/homebrew/opt/openjdk/bin", "/usr/local/opt/openjdk/bin"]
    if IS_WIN:
        out = []
        for base in (os.environ.get("ProgramFiles", r"C:\Program Files"),):
            for vendor in ("Eclipse Adoptium", "Microsoft", "Java", "Zulu"):
                out += sorted(glob.glob(os.path.join(base, vendor, "*", "bin")), reverse=True)
        return out
    return []


def _javac_works(javac):
    # macOS ships /usr/bin/javac as a stub that pops up an "install Java" dialog when there's no JDK;
    # java_home answers the same question silently.
    if IS_MAC and os.path.realpath(javac).startswith("/usr/bin/"):
        try:
            if subprocess.run(["/usr/libexec/java_home"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20).returncode:
                return False
        except Exception:
            return False
    try:
        return subprocess.run([javac, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60).returncode == 0
    except Exception:
        return False


def find_java():
    """(javac, java) from a working JDK, or (None, None)."""
    for d in [None] + _java_dirs():
        javac, java = shutil.which("javac", path=d), shutil.which("java", path=d)
        if javac and java and _javac_works(javac):
            return javac, java
    return None, None


def _refresh_windows_path():
    """A compiler installed after this server started is on the registry PATH, not on ours yet."""
    try:
        import winreg
        parts = []
        for root, key in ((winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
                          (winreg.HKEY_CURRENT_USER, r"Environment")):
            try:
                with winreg.OpenKey(root, key) as k:
                    parts += os.path.expandvars(winreg.QueryValueEx(k, "Path")[0]).split(";")
            except OSError:
                pass
        parts.append(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Links"))
        cur = os.environ.get("PATH", "").split(";")
        os.environ["PATH"] = ";".join(cur + [p for p in parts if p and p not in cur])
    except Exception:
        pass


def detect():
    """Find the compilers (again). Called at import, and after the app installs a language."""
    global GPP, GPP_IS_CLANG, GPP_MAJOR, GPP_DESC, OLD_MINGW, USE_SHIM, JAVAC, JAVA
    if IS_WIN:
        _refresh_windows_path()
    GPP, GPP_IS_CLANG, GPP_MAJOR, GPP_DESC = find_cxx()
    OLD_MINGW = bool(GPP) and IS_WIN and not GPP_IS_CLANG and 0 < GPP_MAJOR < 10
    USE_SHIM = GPP_IS_CLANG or OLD_MINGW or os.environ.get("OA_FORCE_SHIM") == "1"
    JAVAC, JAVA = find_java()


def available():
    """{lang: True/False} for the languages that run here (JavaScript runs in the page)."""
    return {"cpp": bool(GPP), "java": bool(JAVAC and JAVA), "py": True, "js": True}


detect()


def cxx_args(src, exe, shim=None):
    a = [GPP, "-std=c++17", "-O2"]
    if USE_SHIM if shim is None else shim:
        a += ["-I", SHIM_DIR]
    if IS_MAC:
        a += ["-Wl,-stack_size,0x10000000"]   # 256 MB stack for deep recursion
    elif IS_WIN and not GPP_IS_CLANG:
        a += ["-Wl,--stack,268435456"]        # Windows default is 1 MB
        a += ["-static"]                      # avoid depending on MinGW DLLs not on PATH
    return a + ["-o", exe, src]


def compile_cxx(src, exe):
    """Compile; if the compiler's own <bits/stdc++.h> breaks (seen with MinGW GCC 8), retry with the shim."""
    c = subprocess.run(cxx_args(src, exe), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
    err = c.stderr.decode("utf-8", "replace")
    if c.returncode != 0 and not USE_SHIM and re.search(r"fs_path\.h|bits[/\\]fs_|<filesystem>", err):
        c = subprocess.run(cxx_args(src, exe, shim=True), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
        err = c.stderr.decode("utf-8", "replace")
    return c.returncode, err


PY = sys.executable

def run_cmd(args, inp, limit_s, cwd):
    t = time.perf_counter()
    try:
        p = subprocess.run(args, input=inp.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=limit_s, cwd=cwd)
        ms = (time.perf_counter() - t) * 1000
        out = p.stdout.decode("utf-8", "replace")
        err = p.stderr.decode("utf-8", "replace")
        if p.returncode != 0 and not err: err = "Process exited with code %d" % p.returncode
        elif p.returncode == 0: err = ""
        return {"out": out[:200000], "err": err[-4000:], "ms": ms, "tle": False}
    except subprocess.TimeoutExpired:
        return {"out": "", "err": "", "ms": limit_s * 1000, "tle": True}

def judge(lang, code, inputs, limit_ms):
    limit = max(0.5, min(limit_ms / 1000.0, 15))
    d = tempfile.mkdtemp(prefix="oamock_")
    try:
        if lang == "cpp":
            if not GPP: return {"compile_error": "No C++ compiler found. Install it from the language menu (the download icon next to C++17), or run the setup script."}
            src = os.path.join(d, "main.cpp"); exe = os.path.join(d, "main.exe" if IS_WIN else "main")
            open(src, "w", encoding="utf-8").write(code)
            rc, err = compile_cxx(src, exe)
            if rc != 0: return {"compile_error": err[-6000:]}
            args = [exe]
        elif lang == "java":
            if not (JAVAC and JAVA): return {"compile_error": "javac/java were not found. Install a JDK from the language menu (the download icon next to Java), or run the setup script."}
            open(os.path.join(d, "Main.java"), "w", encoding="utf-8").write(code)
            c = subprocess.run([JAVAC, "-encoding", "UTF-8", "Main.java"], cwd=d, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
            if c.returncode != 0: return {"compile_error": c.stderr.decode("utf-8", "replace")[-6000:]}
            args = [JAVA, "-Xss256m", "-cp", d, "Main"]
        elif lang == "py":
            open(os.path.join(d, "main.py"), "w", encoding="utf-8").write(code)
            args = [PY, "-X", "utf8", os.path.join(d, "main.py")]
        else:
            return {"compile_error": "Unsupported language: %s" % lang}
        return {"results": [run_cmd(args, i, limit, d) for i in inputs]}
    finally:
        shutil.rmtree(d, ignore_errors=True)



def describe():
    """One line per language, printed at start-up."""
    return [
        ("C++", (GPP_DESC + ("  [bits/stdc++.h provided by the runner]" if USE_SHIM else "")
                + ("\n          old MinGW GCC %d: it works, but run setup.bat to install a current GCC" % GPP_MAJOR if OLD_MINGW else "")) if GPP else "NOT FOUND: install it from the language menu in the app, or run the setup script"),
        ("Java", JAVAC or "NOT FOUND: install it from the language menu in the app, or run the setup script"),
        ("Python", PY),
    ]

