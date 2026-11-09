"""Start the OA mock:  ./start.sh  (or  python3 app/run.py).

Options:  --port N   (default 8765, or $OA_PORT)
          --no-browser
"""
import argparse, os, sys, webbrowser

from . import __version__, data, judge, server, submissions


def main(argv=None):
    ap = argparse.ArgumentParser(prog="oa-mock", description="Practice OA mocks, served on 127.0.0.1.")
    ap.add_argument("--port", type=int, default=int(os.environ.get("OA_PORT", "8765")))
    ap.add_argument("--no-browser", action="store_true", help="don't open a browser tab")
    args = ap.parse_args(argv)

    names = [n for _, n, _ in data.companies()]
    print("OA Mock %s (%s)" % (__version__, ", ".join(names) or "no companies in data/"))
    for lang, desc in judge.describe():
        print("  %-7s %s" % (lang + ":", desc))

    print("  %-7s %s" % ("Saved:", submissions.SUB_DIR))
    srv = server.serve(args.port)
    url = "http://127.0.0.1:%d/" % srv.server_address[1]
    print("\nOpen %s   (Ctrl+C to stop)" % url)
    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        srv.server_close()


if __name__ == "__main__":
    sys.exit(main())
