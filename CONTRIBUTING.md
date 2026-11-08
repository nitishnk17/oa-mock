# Contributing

This is a group effort. If you sat an OA, or have a write-up or photos of one, add it so the next person can practise on it. Using an LLM to turn your notes into questions and tests is fine, as long as you check the result (step 4 below).

## How to add an OA

1. **Fork** this repo and create a branch, e.g. `add-google-oa-2026`. A slim clone is enough: you only need the company you're adding to (download it on the home page, or `git sparse-checkout add data/<company>`). For a new company, `git sparse-checkout add data/<new-key>` before creating the folder, so git tracks it.
2. **Transcribe the source** into `sources/<company>/` as Markdown, or JSON for structured parts such as an API spec. Put the original PDFs or photos in `raw-sources/` (git-ignored). Never commit them.
3. **Write the questions** in `data/<company>/`:
   - `company.json`: `key`, `name`, `tagline`, `blurb`, `headline`, `defaultFmt`, `formats` (with `pools` of question ids), `order`, `custom`, `offlist`. Copy `data/flipkart/company.json` as a template.
   - `questions/<id>.json`, one per question. Copy an existing one. A coding question needs `id`, `type: "code"`, `title`, `diff` (Easy/Medium/Hard), `src`, `body`, `inp`, `out`, `cons`, `samples` (each `{in, out, ex}`), `hidden` (each `{in, out}`), `ref` (Python) and ideally `refcpp`.
   - **Add when and where it was asked**, so the bank can sort by year: `year` (e.g. `2026`), and if known `month` (1–12), `college`, `role`. Leave out anything the source doesn't say; don't guess.
   - **Questions are LeetCode-style by default:** the candidate completes a function, and a hidden driver reads the input and prints the result. Users can switch to HackerRank style in the app, where the same function is shown inside the full program. Both views are built from `stub` (the function, per language) and `driver` (`{pre, post}`, per language). Don't write them by hand. Describe the function once and generate them:
     1. Add an entry to `tools/style/specs.py`: function name, how to read the input (`int`, `str`, `int[]`, `int[][]`, rows of mixed columns, or a whole line), the return type, and a function-style Python reference. The file's docstring explains each field, and the 38 existing entries are examples.
     2. `python3 tools/style/verify.py <company>/<id>`: the Python reference, through the generated driver, must pass every test. It also flags numbers that don't fit in an `int`; use `long` for those.
     3. `python3 tools/style/selftest.py <company>/<id>`: Python, C++, Java and JavaScript must read every test input identically, and every untouched stub must compile and run.
     4. `python3 tools/style/convert.py`: writes `stub`, `driver` and the "Function to complete" section into the question file.
   - **The same question at another company or in another year?** Don't copy it. Add `"alsoSeen": ["company/id"]` to the new one instead.
4. **Check it:**
   ```
   python3 tools/check_dupes.py path/to/question.json    # is it already in the bank? (--deep also compares answers)
   python3 tools/check_refs.py <company>                  # every reference must pass every test
   python3 tools/build_catalog.py                         # updates data/catalog.json (commit it too)
   python3 run.py                                         # open it and try it in both problem styles
   ```
   Make the hidden tests cover edge cases and at least one maximum-size input, so slow solutions fail.
   If the duplicate checker flags a pair that's actually a different problem, add `"distinctFrom": ["company/id"]` to your question so it's marked as checked.
5. **Open a pull request.** Say where the questions come from (company, role, college, date) and what you guessed where the source was incomplete.

## Rules

- Paraphrase statements in your own words. Don't paste the test platform's text wholesale.
- No personal data: no names, emails or roll numbers of candidates. Demo credentials shown inside a test are fine.
- If a statement is too incomplete to grade, add it to `offlist` in `company.json` with a short reason instead of guessing.
- Keep the server dependency-free (Python standard library only) and the frontend build-free.

## Prompt you can give an LLM

> Here are my notes/photos from the `<Company>` OA. Following https://github.com/rgabhi/oa-mock (see `CONTRIBUTING.md`, `data/flipkart/questions/houses.json` and `tools/style/specs.py`), write for each question: a JSON file with a clear statement, `year`/`month`/`college`/`role` where the notes say them, 2 samples with explanations, 8–12 hidden tests (edge cases plus one maximum-size input) and a C++ reference; plus a `tools/style/specs.py` entry with the function signature, the input layout, the return type and a function-style Python reference. Also write a Markdown transcription of the notes for `sources/<company>/`. List anything you had to assume.

Then run the checks in step 4 (and `verify.py` / `selftest.py`) before you open the PR. LLM-written tests are often wrong.
