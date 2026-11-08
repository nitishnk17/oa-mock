You are helping add a coding question to OA Mock (https://github.com/rgabhi/oa-mock), a practice platform for online assessments. I'll give you my notes, photos or memory of a question from a real OA. Write ONE JSON object for it, in this exact format, and nothing else:

```json
{
  "id": "pairsum",
  "type": "code",
  "title": "Pairs With Sum K",
  "diff": "Easy",
  "src": "Company OA 2026 (SDE intern, on-campus)",
  "year": 2026,
  "month": 8,
  "college": "IIT Delhi",
  "role": "SDE Intern",
  "body": "<p>Statement in your own words, as HTML (<p>, <code>, <ul>, <b>).</p>",
  "inp": "First line: n and k. Second line: n integers a[1..n].",
  "out": "The number of pairs.",
  "cons": "1 ≤ n ≤ 2·10^5, |a[i]| ≤ 10^9",
  "samples": [
    {"in": "4 5\n1 4 2 3\n", "out": "2", "ex": "Pairs (1,4) and (2,3)."}
  ],
  "hidden": [
    {"in": "3 4\n2 2 1\n", "out": "1"}
  ],
  "spec": {
    "fn": "countPairs",
    "read": [["_n", "int"], ["k", "int"], ["nums", "int[]", "_n"]],
    "ret": "long",
    "returns": "the number of pairs"
  },
  "ref": "class Solution:\n    def countPairs(self, k: int, nums: List[int]) -> int:\n        c = Counter(); r = 0\n        for x in nums:\n            r += c[k - x]; c[x] += 1\n        return r\n",
  "refcpp": "class Solution {\npublic:\n    long long countPairs(int k, vector<int>& nums) { ... }\n};\n",
  "wrong": [
    {"why": "brute force O(n^2)", "ref": "class Solution:\n    def countPairs(self, k, nums): ..."},
    {"why": "counts a pair of an element with itself", "ref": "class Solution:\n    def countPairs(self, k, nums): ..."}
  ]
}
```

Rules:
- `id`: short, lowercase, no spaces. `diff`: Easy, Medium or Hard. Add `year`, `month`, `college`, `role` only if my notes say them. Never guess them.
- The statement is in your own words. No candidate names, emails or roll numbers.
- Tests are plain stdin text and the exact expected stdout. `samples`: 1-2 with an explanation in `ex`. `hidden`: 8-15 tests covering edge cases (smallest n, duplicates, negatives, all equal, answer 0, overflow) and at least one maximum-size input. Hidden tests must not all have the same answer.
- Compute every expected output by running the reference solution. Don't work outputs out by hand.
- `spec` says how the hidden driver reads the input and calls the function (LeetCode style). `read` items, in input order:
  - `[name, "int"|"long"|"str"]` reads one token.
  - `[name, "int[]"|"long[]"|"str[]", L]` reads L tokens. L is a number or the name of an earlier item.
  - `[name, "int[][]", R, C]` reads R rows of C ints.
  - `[name, "line"]` reads the whole input as one string.
  - `["rows", L, [[name, type], ...]]` reads L rows of mixed columns, one array per column.
  - Names starting with `_` are read but not passed to the function (counts the arrays already carry).
  - Use `long` for values that can exceed 2^31.
  - `ret` is one of `int`, `long`, `str`, `bool`, `int[]`, `long[]`, `str[]` (printed on one line), `int[]/lines`, `long[]/lines`, `str[]/lines`, `bool[]/lines` (one value per line) or `int[][]` (one row per line).
- `ref`: Python 3, `class Solution` with the function named in `spec.fn`. Its parameters are the `read` names without `_`, in order. `List`, `Counter`, `defaultdict`, `heapq`, `bisect`, `math` and so on are already imported. It must be fast enough for the maximum input (about 1-2 s).
- `refcpp` (optional): C++17 `class Solution` with the same function.
- `wrong`: 1-2 plausible wrong solutions in the same shape as `ref`, such as brute force that is too slow, an off-by-one, or a missed edge case. The checks make sure the hidden tests catch them.

After the JSON, list anything you had to assume because my notes were incomplete.

My notes:
