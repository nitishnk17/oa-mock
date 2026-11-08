"""Function signatures for questions that were written as full programs (read stdin, print stdout).

tools/style/convert.py turns each spec into a LeetCode-style `stub` (what the editor shows) and a
hidden `driver` (reads the input in the question's format, calls the function, prints the result)
for Python, C++, Java and JavaScript, and replaces `ref` with the function-style Python below.

Spec fields
  fn       function name (camelCase in every language, as on LeetCode)
  read     the input, in order. Each item is one of
             (name, "int"|"long"|"str")              one token
             (name, "int[]"|"long[]"|"str[]", L)     L tokens; L is a number or an earlier name
             (name, "int[][]", R, C)                 R rows of C ints; R, C numbers or earlier names
             (name, "line")                          the whole input as one string (no trailing newline)
             ("rows", L, [(name, type), ...])        L rows of mixed columns, returned as one array per column
           Names starting with "_" are read but not passed (counts that the arrays already carry).
  ret      "int" | "long" | "str" | "bool" | "int[]" | "long[]" | "str[]"   (arrays print on one line)
           | "int[]/lines" | "long[]/lines" | "str[]/lines" | "bool[]/lines" (one value per line)
           | "int[][]"                                                       (one row per line)
  returns  what to return, for the statement
  ref      Python reference, function style (the method body of class Solution)
"""

SPECS = {
# ------------------------------------------------------------------ Flipkart
"flipkart/houses": dict(fn="maxDistance", read=[("n", "int"), ("_k", "int"), ("houses", "int[]", "_k")], ret="int",
  returns="the maximum walking distance",
  ref="""
    def maxDistance(self, n: int, houses: List[int]) -> int:
        a = sorted(houses)
        best = max(a[0] - 1, n - a[-1])
        for i in range(1, len(a)):
            best = max(best, (a[i] - a[i - 1]) // 2)
        return best
"""),
"flipkart/poscode": dict(fn="positionCode", read=[("word", "str")], ret="str",
  returns='X and the letter separated by one space, e.g. <code>"55 J"</code>',
  ref="""
    def positionCode(self, word: str) -> str:
        srt = sorted(word)
        where = defaultdict(list)
        for i, c in enumerate(srt):
            where[c].append(i)
        used = defaultdict(int); base = ord(srt[-1]); X = 0
        for i, c in enumerate(word):
            j = where[c][used[c]]; used[c] += 1
            X += sum(map(int, str(abs(i - j) + base)))
        d = sum(map(int, str(X)))
        return f"{X} {chr((d - 1) % 26 + 65)}"
"""),
"flipkart/indeg": dict(fn="mostPointedTo", read=[("_n", "int"), ("rows", "_n", [("u", "str"), ("v", "str")])], ret="str",
  returns='the vertex name and its in-degree separated by one space, e.g. <code>"C 2"</code>',
  ref="""
    def mostPointedTo(self, u: List[str], v: List[str]) -> str:
        deg = {}
        for a, b in zip(u, v):
            deg.setdefault(a, 0); deg[b] = deg.get(b, 0) + 1
        m = max(deg.values())
        return f"{min(x for x in deg if deg[x] == m)} {m}"
"""),
"flipkart/colour": dict(fn="colourVertices", read=[("n", "int"), ("_m", "int"), ("edges", "int[][]", "_m", 2)], ret="int[]",
  returns="the colour of vertices 1 to n",
  ref="""
    def colourVertices(self, n: int, edges: List[List[int]]) -> List[int]:
        adj = [[] for _ in range(n + 1)]
        for u, v in edges:
            adj[u].append(v); adj[v].append(u)
        col = [0] * (n + 1)
        for v in range(1, n + 1):
            used = {col[u] for u in adj[v]}
            c = 1
            while c in used: c += 1
            col[v] = c
        return col[1:]
"""),
"flipkart/snake": dict(fn="snakeTrail", read=[("W", "int"), ("D", "int"), ("x", "int"), ("y", "int"), ("_n", "int"),
                                              ("rows", "_n", [("turns", "str"), ("steps", "int")])], ret="str[]/lines",
  returns='two strings: the distance, then <code>"(x,y) S"</code> where S is A or D',
  ref="""
    def snakeTrail(self, W: int, D: int, x: int, y: int, turns: List[str], steps: List[int]) -> List[str]:
        dirs = [(1, 0), (0, 1), (-1, 0), (0, -1)]; d = 0; seen = {(x, y)}; dist = 0
        for T, k in zip(turns, steps):
            d = (d + {'S': 0, 'L': 1, 'R': 3}[T]) % 4
            for _ in range(k):
                x += dirs[d][0]; y += dirs[d][1]; dist += 1
                if not (0 <= x <= W and 0 <= y <= D) or (x, y) in seen:
                    return [str(dist), f"({x},{y}) D"]
                seen.add((x, y))
        return [str(dist), f"({x},{y}) A"]
"""),
"flipkart/racing": dict(fn="tournament", read=[("n", "int"), ("ranks", "int[][]", 3, "n")], ret="int[][]",
  returns="two rows: the race count for Hilly, City and Off-road, then the wins of racers 1 to n",
  ref="""
    def tournament(self, n: int, ranks: List[List[int]]) -> List[List[int]]:
        rk = [[0] * (n + 1) for _ in range(3)]
        for k in range(3):
            for i, p in enumerate(ranks[k]): rk[k][p] = i + 1
        cnt = [0] * 3; w = [0] * (n + 1)
        for a in range(1, n + 1):
            for b in range(a + 1, n + 1):
                best = None
                for k in range(3):
                    win, lose = (a, b) if rk[k][a] < rk[k][b] else (b, a)
                    key = (rk[k][win], rk[k][lose], k)
                    if best is None or key < best[0]: best = (key, win)
                cnt[best[0][2]] += 1; w[best[1]] += 1
        return [cnt, w[1:]]
"""),
"flipkart/cascade": dict(fn="failureCascade", read=[("_m", "int"), ("start", "str"),
                                                    ("rows", "_m", [("machine", "str"), ("dependsOn", "str"), ("time", "int")])], ret="long[]",
  returns="two numbers: how many machines fail and the time of the last failure",
  ref="""
    def failureCascade(self, start: str, machine: List[str], dependsOn: List[str], time: List[int]) -> List[int]:
        g = defaultdict(list)
        for a, b, t in zip(machine, dependsOn, time): g[b].append((a, t))
        dist = {start: 0}; pq = [(0, start)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]: continue
            for v, w in g[u]:
                if d + w < dist.get(v, 1 << 62): dist[v] = d + w; heapq.heappush(pq, (d + w, v))
        return [len(dist), max(dist.values())]
"""),
"flipkart/bags": dict(fn="countWays", read=[("n", "int"), ("k", "int")], ret="int",
  returns="the number of ways modulo 10<sup>9</sup> + 7",
  ref="""
    def countWays(self, n: int, k: int) -> int:
        M = 10**9 + 7
        dp = [1] + [0] * k
        for i in range(1, n + 1):
            for j in range(min(i, k), 0, -1): dp[j] = (j * dp[j] + dp[j - 1]) % M
            dp[0] = 0
        return dp[k]
"""),
"flipkart/robots": dict(fn="maxGoods", read=[("_R", "int"), ("_C", "int"), ("grid", "int[][]", "_R", "_C")], ret="int",
  returns="the maximum goods collected",
  ref="""
    def maxGoods(self, grid: List[List[int]]) -> int:
        R, C = len(grid), len(grid[0]); g = grid
        NEG = -1; dp = [[NEG] * C for _ in range(C)]; dp[0][C - 1] = g[0][0] + (g[0][C - 1] if C > 1 else 0)
        for r in range(1, R):
            nd = [[NEG] * C for _ in range(C)]
            for a in range(C):
                for b in range(C):
                    if dp[a][b] < 0: continue
                    for na in (a - 1, a, a + 1):
                        if not 0 <= na < C: continue
                        for nb in (b - 1, b, b + 1):
                            if not 0 <= nb < C: continue
                            v = dp[a][b] + g[r][na] + (g[r][nb] if na != nb else 0)
                            if v > nd[na][nb]: nd[na][nb] = v
            dp = nd
        return max(max(x) for x in dp)
"""),
"flipkart/ads": dict(fn="adSequence", read=[("_n", "int"), ("rows", "_n", [("u", "str"), ("v", "str")])], ret="str[]",
  returns="the sequence of n + 1 event names",
  ref="""
    def adSequence(self, u: List[str], v: List[str]) -> List[str]:
        g = defaultdict(list)
        for a, b in zip(u, v): g[a].append(b)
        for k in g: g[k].sort(reverse=True)
        out = []; st = ["ABC"]
        while st:
            while g[st[-1]]: st.append(g[st[-1]].pop())
            out.append(st.pop())
        return out[::-1]
"""),
"flipkart/bignum": dict(fn="largestMerged", read=[("_m", "int"), ("a", "int[]", "_m"), ("_n", "int"), ("b", "int[]", "_n"), ("k", "int")], ret="int[]",
  returns="the k digits of the largest code",
  ref="""
    def largestMerged(self, a: List[int], b: List[int], k: int) -> List[int]:
        m, n = len(a), len(b)
        def pick(x, c):
            drop = len(x) - c; st = []
            for d in x:
                while drop and st and st[-1] < d: st.pop(); drop -= 1
                st.append(d)
            return st[:c]
        def merge(x, y):
            r = []
            while x or y:
                if x > y: r.append(x.pop(0))
                else: r.append(y.pop(0))
            return r
        best = []
        for i in range(max(0, k - n), min(k, m) + 1):
            best = max(best, merge(pick(a, i), pick(b, k - i)))
        return best
"""),
"flipkart/sayclap": dict(fn="sayOrClap", read=[("n", "int"), ("actions", "str")], ret="int[][]",
  returns="two rows: the eliminated players in order (or just -1 if nobody is eliminated), then the remaining players in increasing order",
  ref="""
    def sayOrClap(self, n: int, actions: str) -> List[List[int]]:
        corr = ['C' if (i + 1) % 3 == 0 or '3' in str(i + 1) else 'S' for i in range(len(actions))]
        alive = list(range(1, n + 1)); out = []
        while len(alive) > 1:
            elim = None
            for i, ch in enumerate(actions):
                if ch != corr[i]: elim = alive[i % len(alive)]; break
            if elim is None: break
            alive.remove(elim); out.append(elim)
        return [out if out else [-1], alive]
"""),
"flipkart/island": dict(fn="islandHopper", read=[("_m", "int"), ("_n", "int"), ("grid", "str[]", "_m"), ("r", "int"), ("c", "int"), ("Z", "int")], ret="str",
  returns='the remaining health as a string, or <code>"died X"</code>, or <code>"unreachable"</code>',
  ref="""
    def islandHopper(self, grid: List[str], r: int, c: int, Z: int) -> str:
        g = grid; m, n = len(g), len(g[0])
        D = [[0] * n for _ in range(m)]; q = deque()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = r + dr, c + dc
            if 0 <= a < m and 0 <= b < n and g[a][b] == '.' and not D[a][b]: D[a][b] = 1; q.append((a, b))
        best = -1
        while q:
            a, b = q.popleft()
            if any(0 <= a + x < m and 0 <= b + y < n and g[a + x][b + y] == '*' for x, y in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                best = D[a][b]; break
            for x, y in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                u, v = a + x, b + y
                if 0 <= u < m and 0 <= v < n and g[u][v] == '.' and not D[u][v]: D[u][v] = D[a][b] + 1; q.append((u, v))
        if best < 0: return "unreachable"
        cost = best * (best + 1)
        return str(Z - cost) if cost <= Z else f"died {cost - Z}"
"""),
# ------------------------------------------------------------------ Juspay
"juspay/reach": dict(fn="canReach", read=[("_n", "int"), ("members", "int[]", "_n"), ("_e", "int"),
                                           ("rows", "_e", [("follower", "int"), ("following", "int")]), ("a", "int"), ("b", "int")], ret="int",
  returns="1 if A can reach B, otherwise 0",
  ref="""
    def canReach(self, members: List[int], follower: List[int], following: List[int], a: int, b: int) -> int:
        g = defaultdict(list)
        for u, v in zip(follower, following): g[u].append(v)
        seen = {a}; q = deque([a])
        while q:
            u = q.popleft()
            if u == b: return 1
            for v in g[u]:
                if v not in seen: seen.add(v); q.append(v)
        return 0
"""),
"juspay/fastest": dict(fn="shortestTime", read=[("_n", "int"), ("members", "int[]", "_n"), ("_e", "int"),
                                                ("rows", "_e", [("follower", "int"), ("following", "int"), ("time", "int")]), ("a", "int"), ("b", "int")], ret="long",
  returns="the shortest time from A to B, or -1",
  ref="""
    def shortestTime(self, members: List[int], follower: List[int], following: List[int], time: List[int], a: int, b: int) -> int:
        g = defaultdict(list)
        for u, v, w in zip(follower, following, time): g[u].append((v, w))
        dist = {a: 0}; pq = [(0, a)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]: continue
            if u == b: return d
            for v, w in g[u]:
                if d + w < dist.get(v, 1 << 62): dist[v] = d + w; heapq.heappush(pq, (d + w, v))
        return -1
"""),
"juspay/cyclesum": dict(fn="largestCycleSum", read=[("_n", "int"), ("edge", "int[]", "_n")], ret="long",
  returns="the largest sum of cell indices on any cycle, or -1",
  ref="""
    def largestCycleSum(self, edge: List[int]) -> int:
        n = len(edge); state = [0] * n; best = -1
        for i in range(n):
            if state[i]: continue
            pos = {}; u = i; order = []
            while u != -1 and state[u] == 0:
                state[u] = 1; pos[u] = len(order); order.append(u); u = edge[u]
            if u != -1 and u in pos: best = max(best, sum(order[pos[u]:]))
            for x in order: state[x] = 2
        return best
"""),
"juspay/maxweight": dict(fn="maxWeightNode", read=[("_n", "int"), ("edge", "int[]", "_n")], ret="int",
  returns="the cell with the largest weight (the larger index on a tie)",
  ref="""
    def maxWeightNode(self, edge: List[int]) -> int:
        n = len(edge); w = [0] * n
        for i, x in enumerate(edge):
            if x != -1: w[x] += i
        m = max(w)
        return max(i for i in range(n) if w[i] == m)
"""),
"juspay/meeting": dict(fn="nearestMeetingCell", read=[("_n", "int"), ("edge", "int[]", "_n"), ("c1", "int"), ("c2", "int")], ret="int",
  returns="the nearest meeting cell, or -1",
  ref="""
    def nearestMeetingCell(self, edge: List[int], c1: int, c2: int) -> int:
        n = len(edge)
        def dist(src):
            d = [-1] * n; k = 0; u = src
            while u != -1 and d[u] == -1: d[u] = k; k += 1; u = edge[u]
            return d
        d1, d2 = dist(c1), dist(c2); best = -1; bv = None
        for i in range(n):
            if d1[i] >= 0 and d2[i] >= 0 and (bv is None or d1[i] + d2[i] < bv): bv = d1[i] + d2[i]; best = i
        return best
"""),
"juspay/treelock": dict(fn="lockTree", read=[("_n", "int"), ("m", "int"), ("_q", "int"), ("names", "str[]", "_n"),
                                             ("rows", "_q", [("op", "int"), ("name", "str"), ("uid", "int")])], ret="bool[]/lines",
  returns="one boolean per operation: whether it succeeded",
  ref="""
    def lockTree(self, m: int, names: List[str], op: List[int], name: List[str], uid: List[int]) -> List[bool]:
        n = len(names); idx = {x: i for i, x in enumerate(names)}
        par = [-1] + [(i - 1) // m for i in range(1, n)]
        by = [0] * n; cnt = [0] * n   # by: uid holding the lock (0 = none); cnt: locked nodes strictly below
        out = []
        def anc_locked(x):
            x = par[x]
            while x != -1:
                if by[x]: return True
                x = par[x]
            return False
        def bump(x, d):
            x = par[x]
            while x != -1: cnt[x] += d; x = par[x]
        for o, nm, u in zip(op, name, uid):
            x = idx[nm]
            if o == 1:
                ok = not by[x] and cnt[x] == 0 and not anc_locked(x)
                if ok: by[x] = u; bump(x, 1)
            elif o == 2:
                ok = by[x] == u
                if ok: by[x] = 0; bump(x, -1)
            else:
                ok = not by[x] and cnt[x] > 0 and not anc_locked(x)
                if ok:
                    found = []; st = [x]
                    while st and ok:
                        y = st.pop()
                        for c in range(m * y + 1, min(m * y + m, n - 1) + 1):
                            if by[c]:
                                if by[c] != u: ok = False; break
                                found.append(c)
                            if cnt[c]: st.append(c)
                    if ok:
                        for c in found: by[c] = 0; bump(c, -1)
                        by[x] = u; bump(x, 1)
            out.append(ok)
        return out
"""),
"juspay/parking": dict(fn="minMoves", read=[("_n", "int"), ("positions", "int[]", "_n")], ret="int",
  returns="the minimum number of cars to move",
  ref="""
    def minMoves(self, positions: List[int]) -> int:
        n = len(positions); a = sorted(positions); best = 0; j = 0
        for i in range(n):
            while a[i] - a[j] > n - 1: j += 1
            best = max(best, i - j + 1)
        return n - best
"""),
"juspay/rebels": dict(fn="removalOrder", read=[("_n", "int"), ("rows", "_n", [("parent", "int"), ("disrespects", "int")])], ret="int[]",
  returns="the nobles removed, in order, or just -1 if none",
  ref="""
    def removalOrder(self, parent: List[int], disrespects: List[int]) -> List[int]:
        n = len(parent); bad = [disrespects[i] == 1 for i in range(n)]
        for i in range(n):
            if parent[i] != -1 and disrespects[i] == 0: bad[parent[i] - 1] = False
        res = [i + 1 for i in range(n) if parent[i] != -1 and bad[i]]
        return res if res else [-1]
"""),
"juspay/magical": dict(fn="minOperations", read=[("s", "str")], ret="int",
  returns="the answer described above",
  ref="""
    def minOperations(self, s: str) -> int:
        xs = s.count("X")
        if xs == 0: return 0
        if s[0] == "Y" or s[-1] == "Y" or "YY" in s: return xs
        runs = [len(r) for r in s.split("Y") if r]
        return xs - min(runs) if "Y" in s else 0
"""),
"juspay/cycling": dict(fn="answerQueries", read=[("_n", "int"), ("_q", "int"), ("speeds", "int[]", "_n"), ("queries", "int[]", "_q")], ret="int[]/lines",
  returns="one answer per query",
  ref="""
    def answerQueries(self, speeds: List[int], queries: List[int]) -> List[int]:
        a = speeds; out = []
        for d in queries:
            dq = deque(); best = None
            for i, x in enumerate(a):
                while dq and a[dq[-1]] <= x: dq.pop()
                dq.append(i)
                if dq[0] <= i - d: dq.popleft()
                if i >= d - 1: best = a[dq[0]] if best is None else min(best, a[dq[0]])
            out.append(best)
        return out
"""),
"juspay/factory": dict(fn="minDays", read=[("P", "long"), ("_n", "int"), ("output", "int[]", "_n"), ("cooldown", "int[]", "_n")], ret="long",
  returns="the minimum number of days",
  ref="""
    def minDays(self, P: int, output: List[int], cooldown: List[int]) -> int:
        o, c, n = output, cooldown, len(output)
        def ok(D): return sum(o[i] * (-(-D // c[i])) for i in range(n)) >= P
        lo = hi = 1
        while not ok(hi): hi *= 2
        while lo < hi:
            mid = (lo + hi) // 2
            if ok(mid): hi = mid
            else: lo = mid + 1
        return lo
"""),
"juspay/vineyard": dict(fn="countPartitions", read=[("_n", "int"), ("field", "str[]", 2)], ret="int",
  returns="the answer described above",
  ref="""
    def countPartitions(self, field: List[str]) -> int:
        n = len(field[0]); cnt = 0
        for k in range(2):
            a, b = field[k], field[1 - k]
            for i in range(1, n - 1):
                if a[i - 1] == a[i] == a[i + 1] == "o" and b[i - 1] == "x" and b[i] == "o" and b[i + 1] == "x": cnt += 1
        return cnt
"""),
"juspay/hiker": dict(fn="countSafeTrails", read=[("_n", "int"), ("m", "int"), ("dangerous", "int[]", "_n"), ("edges", "int[][]", "_n-1", 2)], ret="int",
  returns="the number of safe trails",
  ref="""
    def countSafeTrails(self, m: int, dangerous: List[int], edges: List[List[int]]) -> int:
        n = len(dangerous); g = [[] for _ in range(n + 1)]
        for u, v in edges: g[u].append(v); g[v].append(u)
        cnt = 0; st = [(1, 0, dangerous[0])]
        while st:
            u, p, run = st.pop()
            if run > m: continue
            kids = [v for v in g[u] if v != p]
            if not kids and u != 1: cnt += 1
            for v in kids: st.append((v, u, run + 1 if dangerous[v - 1] else 0))
        return cnt
"""),
"juspay/equalize": dict(fn="maxEqual", read=[("_n", "int"), ("a", "int[]", "_n")], ret="int",
  returns="the answer described above",
  ref="""
    def maxEqual(self, a: List[int]) -> int:
        n = len(a); v = sorted(set(a)); best = 0; j = 0
        for i in range(len(v)):
            while v[i] - v[j] > n - 1: j += 1
            best = max(best, i - j + 1)
        return best
"""),
"juspay/leader": dict(fn="winner", read=[("_q", "int"), ("rows", "_q", [("names", "str"), ("scores", "int")])], ret="str",
  returns="the winner's name",
  ref="""
    def winner(self, names: List[str], scores: List[int]) -> str:
        tot = defaultdict(int)
        for nm, sc in zip(names, scores): tot[nm] += sc
        m = max(tot.values()); run = defaultdict(int)
        for nm, sc in zip(names, scores):
            run[nm] += sc
            if tot[nm] == m and run[nm] >= m: return nm
"""),
"juspay/workers": dict(fn="minMaxLoad", read=[("_n", "int"), ("k", "int"), ("jobs", "int[]", "_n")], ret="long",
  returns="the smallest possible load of the busiest worker",
  ref="""
    def minMaxLoad(self, k: int, jobs: List[int]) -> int:
        n = len(jobs); jobs = sorted(jobs, reverse=True)
        best = [sum(jobs)]; load = [0] * k
        def go(i, cur):
            if cur >= best[0]: return
            if i == n: best[0] = cur; return
            seen = set()
            for w in range(k):
                if load[w] in seen: continue
                seen.add(load[w]); load[w] += jobs[i]
                go(i + 1, max(cur, load[w])); load[w] -= jobs[i]
        go(0, 0)
        return best[0]
"""),
"juspay/openlock": dict(fn="openLock", read=[("_d", "int"), ("deadends", "str[]", "_d"), ("target", "str")], ret="int",
  returns="the minimum number of turns, or -1",
  ref="""
    def openLock(self, deadends: List[str], target: str) -> int:
        dead = set(deadends)
        if "0000" in dead: return -1
        if target == "0000": return 0
        seen = {"0000"} | dead; q = deque([("0000", 0)])
        while q:
            u, k = q.popleft()
            for i in range(4):
                for dd in (1, -1):
                    v = u[:i] + str((int(u[i]) + dd) % 10) + u[i + 1:]
                    if v == target: return k + 1
                    if v not in seen: seen.add(v); q.append((v, k + 1))
        return -1
"""),
"juspay/calc": dict(fn="calculate", read=[("s", "line")], ret="long",
  returns="the value of the expression",
  ref="""
    def calculate(self, s: str) -> int:
        res = 0; num = 0; sign = 1; st = []
        for ch in s:
            if ch.isdigit(): num = num * 10 + int(ch)
            elif ch in "+-":
                res += sign * num; num = 0; sign = 1 if ch == "+" else -1
            elif ch == "(":
                st.append((res, sign)); res = 0; sign = 1
            elif ch == ")":
                res += sign * num; num = 0; pr, ps = st.pop(); res = pr + ps * res
        return res + sign * num
"""),
"juspay/inversions": dict(fn="countInversions", read=[("_n", "int"), ("a", "int[]", "_n")], ret="long",
  returns="the number of inversion pairs",
  ref="""
    def countInversions(self, a: List[int]) -> int:
        def sort(x):
            if len(x) < 2: return x, 0
            m = len(x) // 2; l, c1 = sort(x[:m]); r, c2 = sort(x[m:]); out = []; i = j = 0; c = c1 + c2
            while i < len(l) and j < len(r):
                if r[j] < l[i]: out.append(r[j]); j += 1; c += len(l) - i
                else: out.append(l[i]); i += 1
            out += l[i:]; out += r[j:]
            return out, c
        return sort(a)[1]
"""),
"juspay/puddles": dict(fn="countPuddles", read=[("m", "int"), ("n", "int"), ("_k", "int"), ("cells", "int[][]", "_k", 2)], ret="int[]",
  returns="the number of puddles after each cell fills",
  ref="""
    def countPuddles(self, m: int, n: int, cells: List[List[int]]) -> List[int]:
        par = {}; out = []; comps = 0
        def find(x):
            while par[x] != x: par[x] = par[par[x]]; x = par[x]
            return x
        for r, c in cells:
            if (r, c) not in par:
                par[(r, c)] = (r, c); comps += 1
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nb = (r + dr, c + dc)
                    if nb in par:
                        a, b = find(nb), find((r, c))
                        if a != b: par[a] = b; comps -= 1
            out.append(comps)
        return out
"""),
# ------------------------------------------------------------------ MathWorks
"mathworks/minids": dict(fn="minIds", read=[("_n", "int"), ("m", "int"), ("arr", "int[]", "_n")], ret="int",
  returns="the fewest distinct IDs left",
  ref="""
    def minIds(self, arr: List[int], m: int) -> int:
        freq = sorted(Counter(arr).values()); left = len(freq)
        for f in freq:
            if m < f: break
            m -= f; left -= 1
        return left
""", order=["arr", "m"]),
"mathworks/twodenom": dict(fn="fewestNotes", read=[("_n", "int"), ("k", "int"), ("arr", "int[]", "_n"), ("_q", "int"), ("queries", "int[]", "_q")], ret="int[]",
  returns="one answer per amount: the fewest notes, or -1",
  ref="""
    def fewestNotes(self, arr: List[int], k: int, queries: List[int]) -> List[int]:
        best = {0: 0}                      # amount -> fewest notes using ONE value
        for v in arr:
            for c in range(1, k + 1):
                if best.get(v * c, k + 1) > c: best[v * c] = c
        res = []
        for x in queries:
            ans = best.get(x, k + 1)
            for v in arr:
                for a in range(1, k + 1):
                    r = x - v * a
                    if r < 0: break
                    b = best.get(r)
                    if b is not None and a + b < ans: ans = a + b
            res.append(ans if ans <= k else -1)
        return res
""", order=["arr", "k", "queries"]),
"mathworks/majparts": dict(fn="minSubsequences", read=[("_n", "int"), ("arr", "int[]", "_n")], ret="int",
  returns="the minimum number of subsequences",
  ref="""
    def minSubsequences(self, arr: List[int]) -> int:
        n = len(arr); covered = 0
        for groups, f in enumerate(sorted(Counter(arr).values(), reverse=True), 1):
            covered += 2 * f - 1         # f copies + up to f - 1 other elements
            if covered >= n: return groups
"""),
"mathworks/palsubs": dict(fn="countPalindromicSubstrings", read=[("_count", "int"), ("strs", "str[]", "_count")], ret="long[]/lines",
  returns="one count per string",
  ref="""
    def countPalindromicSubstrings(self, strs: List[str]) -> List[int]:
        def count(s):
            seen = {0: 1}; mask = 0; total = 0
            for ch in s:
                mask ^= 1 << (ord(ch) - 97)
                total += seen.get(mask, 0)
                for b in range(26): total += seen.get(mask ^ (1 << b), 0)
                seen[mask] = seen.get(mask, 0) + 1
            return total
        return [count(s) for s in strs]
"""),
"mathworks/beauty": dict(fn="maxBeautiful", read=[("s", "str")], ret="long",
  returns="the maximum number of beautiful substrings",
  ref="""
    def maxBeautiful(self, s: str) -> int:
        tri = lambda x: x * (x + 1) // 2
        n = len(s); runs = []; gaps = []; dots = 0
        for ch in s:
            if ch == '.': dots += 1
            elif runs and runs[-1][0] == ch: runs[-1][1] += dots + 1; dots = 0
            else: gaps.append(dots); runs.append([ch, 1]); dots = 0
        if not runs: return tri(n)
        runs[0][1] += gaps[0]; runs[-1][1] += dots
        m = len(runs); dp = {0: 0}
        for i in range(m):
            right = gaps[i + 1] if i + 1 < m else 0
            nd = {}
            for took, val in dp.items():
                for give_left in ((True, False) if right else (False,)):
                    length = runs[i][1] + took + (right if give_left else 0)
                    key = 0 if give_left else right
                    v = val + tri(length)
                    if nd.get(key, -1) < v: nd[key] = v
            dp = nd
        return max(dp.values())
"""),
}
