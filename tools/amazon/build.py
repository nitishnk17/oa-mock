"""Builds data/amazon/ (company.json + questions/*.json) from the sources in this folder.

    python3 tools/amazon/build.py

Needs Python 3.8+, node and g++ (the coding generator checks references against brute force)."""
import json, random, html, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(ROOT, 'data', 'amazon')
H = lambda *p: os.path.join(HERE, *p)
sys.path.insert(0, HERE)

# 1. regenerate the coding tests and the watchlist tests
subprocess.run([sys.executable, H('gen_coding.py')], check=True)
subprocess.run(['node', H('watchlist', 'gen_tests.js')], check=True)

esc = html.escape
import fnstyle
coding = fnstyle.apply(json.load(open(H('build', 'coding_qs.json'))))
pre = open(H('watchlist', 'prelude.js')).read()
post = open(H('watchlist', 'post.js')).read()
starter = open(H('watchlist', 'starter.js')).read()
fixed = open(H('watchlist', 'fixed.js')).read()
wt = json.load(open(H('build', 'watchlist_tests.json')))

M = lambda i: "65f0a1b2c3d4e5f6%08d" % i
movies = ["The Shawshank Redemption", "Interstellar", "The Dark Knight", "Spirited Away", "Parasite", "Inception"]
movie_rows = "".join("<tr><td>%s</td><td>%s</td></tr>" % (esc(t), M(i + 1)) for i, t in enumerate(movies))

debug_body = f"""
<p><b>MovieDB</b> is an app where users explore movies, rate them and write reviews. The <b>watchlist</b> feature lets a user save movies to watch later. It is broken on the backend.</p>
<p><b>Issue:</b> users can add movies to their watchlist, but the movies never appear on the Watchlist page. Removing a movie, either from the Watchlist page or by toggling <i>Add to Watchlist</i> on the movie page, doesn't work either. Fix the backend of the watchlist feature.</p>
<p><b>Additional requirement:</b> to stop spam, each user may add or remove movies at most <b>10 times in any 2-minute window</b>, with adds and removes counted together.</p>
<p>The acceptance criteria are the predefined tests. Use the failing ones to guide your debugging. The repo may also contain issues unrelated to this task; leave those alone.</p>

<h3>Expected API (README.md)</h3>
<p>Every route needs <code>Authorization: Bearer &lt;token&gt;</code>. <code>authMiddleware</code> sets <code>req.userId</code> or answers <code>401</code>.</p>
<div class="scroll-x"><table class="dtable" style="font-family:var(--f-body)"><thead><tr><th>Route</th><th>Success</th><th>Errors</th></tr></thead><tbody>
<tr><td>GET /api/watchlist/</td><td>200, an array of the user's <b>movie</b> documents in the order they were added</td><td>500 Server error</td></tr>
<tr><td>GET /api/watchlist/check/:movieId</td><td>200 <code>{{"isInWatchlist": true|false}}</code></td><td>400 Invalid movie ID format</td></tr>
<tr><td>POST /api/watchlist/add<br>body <code>{{"movieId"}}</code></td><td>201 Movie added to watchlist successfully</td><td>400 Movie ID is required · 400 Invalid movie ID format · 404 Movie not found · 400 Movie already in watchlist · 429 rate limit</td></tr>
<tr><td>POST /api/watchlist/remove<br>body <code>{{"movieId"}}</code></td><td>200 Movie removed from watchlist successfully</td><td>400 Movie ID is required · 400 Invalid movie ID format · 404 Movie not found in watchlist · 429 rate limit</td></tr>
</tbody></table></div>
<p>The 429 body is <code>{{"message": "Too many watchlist operations. You can add or remove movies up to 10 times within 2 minutes."}}</code>. The limiter runs before the controller, so every add or remove request it lets through counts, even one that then fails validation. A request rejected with 429 does not count. A request made at time <code>t</code> stops counting once <code>now − t ≥ 2 minutes</code>.</p>
<p>When a movie is added or removed, the watchlist entry must really be created in or deleted from the database.</p>

<h3>How the tests work</h3>
<p>The editor holds three files from the repo: <code>controllers/watchlistController.js</code>, <code>middleware/rateLimiter.js</code> and <code>routes/watchlistRoutes.js</code>. On every run a fresh database is seeded and a test client sends requests to the app. Each test is a script, one request per line:</p>
<pre>&lt;seconds since start&gt; &lt;sam | alex | -&gt; &lt;GET|POST&gt; &lt;url&gt; [JSON body]</pre>
<p><code>-</code> sends no token. For each request the client prints the status code and the JSON body. For the watchlist list it prints only the movie titles, so <code>200 ["Interstellar"]</code> means one movie document whose title is Interstellar. Lines starting with <code>[log]</code> are server logs, such as <code>console.error</code> output. They are shown to help you and are ignored when grading. Tick <i>Custom input</i> to send your own request script.</p>
<p>The rest of the repo is read-only. Its files are below.</p>
<div class="scroll-x"><table class="dtable"><caption>Seeded movies</caption><thead><tr><th>title</th><th>_id</th></tr></thead><tbody>{movie_rows}</tbody></table></div>
<details class="files"><summary>Read-only files: framework, models/Movie.js, models/Watchlist.js, middleware/auth.js</summary><pre>{esc(pre)}</pre></details>
<details class="files"><summary>Read-only file: app.js and the test client</summary><pre>{esc(post)}</pre></details>
"""

fixnotes = """<ul>
<li><code>getWatchlist</code> called <code>Watchlist.findByUser</code>, which doesn't exist, so the list always failed with 500. Use <code>Watchlist.find({ user: userId }).populate('movie')</code> so the response contains movie documents, not ids.</li>
<li><code>addToWatchlist</code> answered 201 but never called <code>Watchlist.create</code>. A duplicate must answer <b>400</b> Movie already in watchlist. Answering 404 here was a common mistake; the unique index's error code 11000 is a second safety net.</li>
<li><code>removeFromWatchlist</code> never deleted anything and never answered 404. Use <code>findOneAndDelete</code> and check the result.</li>
<li><code>checkWatchlistStatus</code> returned the array from <code>find</code>. It must return a boolean: <code>!!(await Watchlist.findOne(...))</code>.</li>
<li><code>watchlistRateLimiter</code>: <code>windowMs</code> was never defined (ReferenceError, so 500). The filter kept the <i>expired</i> timestamps (<code>&gt;=</code> instead of <code>&lt;</code>). <code>if (requests)</code> is always true because an empty array is truthy. <code>validRequests</code> was never declared. It should be: keep timestamps with <code>now − t &lt; 2 min</code>, reject when 10 or more remain, otherwise push <code>now</code>.</li>
<li>The routes never used the limiter. Wiring <code>watchlistRateLimiter</code> without calling it passes the factory as middleware, so the request hangs (the real test runner showed a 20 s timeout). Use <code>watchlistRateLimiter()</code>. The generic <code>rateLimiter</code> keys by path, so it would count adds and removes separately; it isn't the right tool here.</li>
</ul>"""

watchlist = {
    "id": "watchlist", "type": "debug", "title": "MovieDB Watchlist (repo debugging)", "diff": "Debug",
    "src": "Amazon SDE Intern OA 2026 · section 2, repository debugging (MERN)",
    "body": debug_body,
    "inp": "A request script (see How the tests work). The repo's test client reads it, so you don't parse input yourself.",
    "out": "One line per request: <code>&lt;status&gt; &lt;JSON body&gt;</code>, printed by the test client.",
    "cons": ["Edit only the three files in the editor; the framework, models, auth and test client are fixed", "Language: JavaScript (the real repo is Node + Express + MongoDB)", "The tests run against an in-memory database seeded fresh on every run"],
    "samples": wt["samples"], "hidden": wt["hidden"],
    "starter": starter, "pre": pre, "post": post, "ref": fixed, "fixnotes": fixnotes,
    "lc": None, "lcurl": None,
}

# ---- SJT: shuffle option order (seeded) so the best answer isn't always in the same slot
random.seed(7)
items = json.load(open(H('sjt.json')))
for it in items:
    random.shuffle(it["o"])
sjt = {
    "id": "sjt", "type": "sjt", "title": "Workplace Situational Judgement", "diff": "SJT",
    "src": "Amazon SDE Intern OA 2026 · section 3 (scenarios written for this mock)",
    "body": "<p>For each scenario, pick the response you would most likely take. The real section covers teamwork and communication, ownership and customer focus, handling disagreement, taking feedback and decision making, and it maps onto Amazon's Leadership Principles.</p><p class=\"muted\">The real OA's scenarios weren't shared, so these are original ones in the same style. Scoring: 2 points for the best answer, 1 for a partly good one, 0 otherwise.</p>",
    "items": items, "inp": "", "out": "", "cons": [], "samples": [], "hidden": [], "ref": "",
    "lc": None, "lcurl": None,
}

QS = coding + [watchlist, sjt]
CFG = {
    "key": "amz", "name": "Amazon OA Mock",
    "tagline": "SDE Intern 2026: coding · repo debugging · situational judgement",
    "headline": "Sit a timed Amazon OA, then see what passed.",
    "blurb": "questions reported from Amazon's 2026 SDE intern OAs: coding, a repo-debugging task and situational judgement",
    "defaultFmt": "sde",
    "ioRule": "Coding questions are LeetCode-style: complete the given function and return the answer. Input and output are handled for you, so don't print anything yourself: extra output counts as a wrong answer.", "custom": ["flip", "findpairs", "parcels", "outlier", "winners", "qmarks", "watchlist", "sjt"],
    "formats": {
        "sde": {"name": "SDE Intern OA 2026", "desc": "3 sections: coding (Longest Run After One Flip), MovieDB repo debugging, situational judgement · 120 min", "mins": 120, "pools": [["flip"], ["watchlist"], ["sjt"]]},
        "coding": {"name": "IIITD coding set", "desc": "Palindrome-Ready Subsequences + Even Blocks of At Most Two (IIIT Delhi, 4 July) · 70 min", "mins": 70, "pools": [["palsub"], ["evenrun"]]},
        "online2024": {"name": "Online coding set 2024", "desc": "Five coding questions reported from Amazon's 2024 online OAs (HackerRank) · 150 min", "mins": 150, "pools": [["findpairs"], ["parcels"], ["outlier"], ["winners"], ["qmarks"]]},
        "debug": {"name": "Debugging section", "desc": "MovieDB watchlist repo: fix the backend until the integration tests pass · 60 min", "mins": 60, "pools": [["watchlist"]]},
        "custom": {"name": "Custom", "desc": "Pick the questions and the time", "mins": 60, "pools": []},
    },
    "offlist": [
        {"t": "Return/Risk Evaluation System (repo debugging)", "s": "Amazon SDE-1 Intern OA 2026 · section 2",
         "why": "Only an outline was shared (7+ files, return-window checks, linked accounts, risk scoring, approve/review/reject decisions, 6 integrated tests). The MovieDB question practises the same read-trace-fix workflow."},
    ],
}


# 2. write data/amazon/
CFG["order"] = [q["id"] for q in QS]
os.makedirs(os.path.join(OUT, "questions"), exist_ok=True)
json.dump(CFG, open(os.path.join(OUT, "company.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
META_KEYS = ("year", "month", "college", "role", "alsoSeen")   # kept from the existing file, so a rebuild doesn't drop them
for q in QS:
    p = os.path.join(OUT, "questions", q["id"] + ".json")
    if os.path.isfile(p):
        old = json.load(open(p, encoding="utf-8"))
        for k in META_KEYS:
            if k in old and k not in q: q[k] = old[k]
    json.dump(q, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("wrote", OUT, [q["id"] for q in QS])
