# Contributing

This is a group effort. If you sat an OA, or have a write-up or photos of one, add it so the next person can practise on it. Using an LLM to turn your notes into questions and tests is fine, as long as you check the result (step 4 below).

## How to add an OA

1. **Fork** this repo and create a branch, e.g. `add-google-oa-2026`.
2. **Transcribe the source** into `sources/<company>/` as Markdown, or JSON for structured parts such as an API spec. Put the original PDFs or photos in `raw-sources/` (git-ignored). Never commit them.
3. **Write the questions** in `data/<company>/`:
   - `company.json`: `key`, `name`, `tagline`, `blurb`, `headline`, `defaultFmt`, `formats` (with `pools` of question ids), `order`, `custom`, `offlist`. Copy `data/flipkart/company.json` as a template.
   - `questions/<id>.json`, one per question. Copy an existing one. A coding question needs `id`, `type: "code"`, `title`, `diff` (Easy/Medium/Hard), `src`, `body`, `inp`, `out`, `cons`, `samples` (each `{in, out, ex}`), `hidden` (each `{in, out}`), `ref` (Python) and ideally `refcpp`.
   - **Give every coding question a `stub`** with starter code for all four languages (`py`, `cpp`, `java`, `js`). The stub must already do the question's own I/O — read exactly the format described in `inp` and print exactly the format described in `out` — and leave an empty function for the candidate to fill, as in `data/mathworks/questions/twodenom.json`. Without `stub` the editor falls back to a generic "read all of stdin" skeleton, so the candidate burns OA time writing parsing instead of solving. Use a 64-bit return type where the answer can exceed 2<sup>31</sup>.
   - For LeetCode-style questions (the user fills in a function and the harness does the I/O), add `driver` per language alongside `stub`, as in `data/amazon/questions/flip.json`.
4. **Check it:**
   ```
   python3 tools/check_refs.py <company>     # every reference must pass every test
   python3 run.py                            # open it and try the question yourself
   ```
   Make the hidden tests cover edge cases and at least one maximum-size input, so slow solutions fail.
   Also switch the editor to each of the four languages and run the untouched stub against sample 1: it must compile and print output of the right shape (placeholder values are fine). A stub that does not compile, or that misparses the input, is worse than no stub.
5. **Open a pull request.** Say where the questions come from (company, role, college, date) and what you guessed where the source was incomplete.

## Rules

- Paraphrase statements in your own words. Don't paste the test platform's text wholesale.
- No personal data: no names, emails or roll numbers of candidates. Demo credentials shown inside a test are fine.
- If a statement is too incomplete to grade, add it to `offlist` in `company.json` with a short reason instead of guessing.
- Keep the server dependency-free (Python standard library only) and the frontend build-free.

## Prompt you can give an LLM

> Here are my notes/photos from the `<Company>` OA. Following the format of `data/amazon/questions/flip.json` in https://github.com/rgabhi/oa-mock, write one JSON file per question with a clear statement, 2 samples with explanations, 8–12 hidden tests (edge cases plus one large input), reference solutions in Python and C++, and a `stub` for all four languages (`py`, `cpp`, `java`, `js`) that reads the question's input format and prints its output format, leaving an empty function for me to fill. Also write a Markdown transcription of the notes for `sources/<company>/`. List anything you had to assume.

Then run `tools/check_refs.py` before you open the PR. LLM-written tests are often wrong.
