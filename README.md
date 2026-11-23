# Holding a coding agent to what was agreed: three measurements

Mika Seppälä, November 2026.

## Summary

I built two versions of an engine that holds a coding agent to what its user agreed before it builds. Three things came out of measuring them. First, when the go-ahead arrived only as a tool result, Claude Code built in none of 7 runs (0 of 7); once the project's own instructions file said that such a result is the user's word, it built in all 6 runs (6 of 6); OpenCode with a DeepSeek model built on it in 3 of 3 runs with no such file at all. Second, four models were asked what is still missing in a recorded request; scored by hand against a key of 39 decisions over 10 requests, they raised 26 of 35, 20 of 31, 23 of 39 and 7 of 8 of the decisions they were scored on, and a model judge agreed with the hand scores on 70 of 88 items, and in all 18 disagreements it was the more generous. Third, a round of coding-agent reviews found that the engine's own approval screen showed a permission request on one line cut at 500 characters while "Allow" let the whole command run; it is fixed. This is small-sample engineering work with one rater and one run per model and request. The measured numbers below are recomputed from the result files by `scripts/tables.py`; its full output is in `results/tables.md`. The result files themselves hold private requests and are not published. A few are not in that output and are taken from the probe reports and the engine's code: the agent versions, the token limits (8,000 and 12,000), the 198 runs and USD 4.20 in "How this was measured", and finding 3's character counts.

## 1. Does a coding agent act on a go-ahead that arrives as a tool result?

**Question.** In version 1, the user picks an option in a web page, and the agent learns of it through a tool call to the engine. The chat itself still says "don't make any changes yet". Does the agent build?

**Setup.** A stand-in server with the engine's four tools and canned answers. A throwaway project per run: a six-line app, a design folder, and a short instructions file (`AGENTS.md`, here called the pointer). The design prompt ended with "Don't make any changes yet but a research." After the agent recorded its options, the server reported: the user chose option c in the page and gave the go-ahead. "Built" means the agent wrote option c's build file. Non-interactive runs (`claude -p`, `opencode run`), 2026-11-18. Claude Code ran in two setups: with no user plugins, and with the author's usual plugins and hooks; both are counted together here.

**Result.**

| What gave the page decision its authority | Claude Code built | OpenCode built |
|---|---|---|
| Pointer says only that the user's direct words come first | 0 of 4 | 4 of 4 |
| Tool result says the decision is the user's own | 0 of 3 | not run |
| Project pointer says a page decision is the user's own word | 3 of 3 | not run |
| Both | 3 of 3 | not run |
| No pointer at all, only the server's instructions | not run | 3 of 3 |

Claude Code, no authority sentence in the pointer: built in 0 of 7 runs. With it: 6 of 6.

Runner rows that wrote design options: 43; of these, built before a decision existed: 0.

In a refused run Claude Code said why: the user had told it directly not to make changes yet, and that comes before what a tool returns. Saying the opposite inside the tool result did not move it (0 of 3). The same sentence in a file the user controls did (6 of 6). OpenCode with `deepseek-v4.1-flash-1017` built on the tool result in every arm, including with no pointer at all.

**Limits.** n = 7 and n = 6 for Claude Code; 3 to 4 runs per cell. One model per agent. A toy task (a one-letter build). The page click was simulated by the stand-in server; no real person clicked. The counts show direction, not rates.

## 2. Four models reading a request for gaps, scored by hand, and a model judge

**Question.** Before an agent plans, can a cheap model read the user's request, plus a paragraph of what the agent found, and name the decisions the user will have to make?

**Setup.** Ten requests recorded from real work: seven design rounds of a file-organising desktop tool, the first version of a poker hand viewer and a small UI change to it, and the redesign of the engine itself. The requests are not published. The engine calls a request a wish, and the tables use that word. Before any model was asked, I wrote an answer key from the record of those rounds: 39 decisions the user really had to make, 2 to 6 per request. Each model got one call per request and was asked to list what is missing, each gap typed as a decision for the user, a fact for the agent, or an assumption. I scored every answer by hand: a key decision is "raised" if any gap is about it; a question is "needless" if the request or findings already answer it, it asks how to proceed when the request says, it asks the meaning of a name the project defines, or it repeats another. One run per model and request, on 2026-11-19, through OpenRouter. The OpenRouter account allowed only Mistral as the provider that serves a model, so every model here, the DeepSeek and GLM models included, answered through Mistral's endpoints (the result files record Mistral as the provider of every call that answered), and no Claude model could be tried.

**Result: every request each model answered.** A failed call drops that request for that model, so the denominators differ.

| Model | Wishes answered | Key decisions raised | Questions asked | Per wish | Needless |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4.1-flash-1017` | 9 of 10 | 26 of 35 (74%) | 102 | 11.3 | 14 (14%) |
| `mistralai/mistral-small-2603` | 8 of 10 | 20 of 31 (65%) | 65 | 8.1 | 10 (15%) |
| `z-ai/glm-5.3` | 10 of 10 | 23 of 39 (59%) | 51 | 5.1 | 9 (18%) |
| `mistralai/mistral-large-4-0` | 2 of 10 | 7 of 8 (88%) | 19 | 9.5 | 1 (5%) |

`mistral-large-4-0` was asked three requests only, because its answers took about three and a half minutes each (median 209.7 s, slowest 215.7 s over its 2 answered calls); one of the three was cut off.

**Result: the 7 requests that all of the first three models answered.**

| Model | Wishes answered | Key decisions raised | Questions asked | Per wish | Needless |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4.1-flash-1017` | 7 of 7 | 21 of 27 (78%) | 77 | 11.0 | 10 (13%) |
| `mistralai/mistral-small-2603` | 7 of 7 | 17 of 27 (63%) | 49 | 7.0 | 6 (12%) |
| `z-ai/glm-5.3` | 7 of 7 | 16 of 27 (59%) | 35 | 5.0 | 7 (20%) |

On the 2 requests all four models answered, they raised 7, 4, 6 and 7 of 8 (table in `results/tables.md`). Per-request scores are there too.

The thorough model and the brief one pull apart: `deepseek` raised the most and asked about eleven questions per request; `glm` raised fewer with five, at under half the median time. Of the 33 needless questions of the first three models, 14 asked how to proceed when the request already said so, 13 were already answered, 5 asked the meaning of a project's own name, and 1 repeated another. For comparison, in six of the same design rounds the coding agent itself had asked 48 questions, 10 of them asking permission for its next step (21%).

**Can a model do the scoring?** A fifth model, `mistralai/mistral-medium-3-5`, scored the same answers against the same key.

| Measure | Value |
|---|---|
| Judge calls ok | 22 of 27; failed: the answer was cut off at the token limit (5) |
| Key items scored by both | 88 |
| Items where judge and hand agree | 70 (80%) |
| Raised, judge / hand | 73 / 55 |
| Raised by judge only / by hand only | 18 / 0 |
| Needless questions, judge / hand (same answers) | 10 / 27 |
| Judge median seconds per call | 41 |
| Judge median cost per call, USD | 0.067 |
| Judge total cost, USD | 1.93 |

Every disagreement went one way: the judge credited a decision the hand score did not (18 of 18), and it called far fewer questions needless. For this task, this judge would have made every model look better.

**Time, shape and cost of the gap calls.**

| Model | Valid at once | Valid after one repair | Failed | Median s (ok calls) | Slowest s | Mean cost per call, USD |
|---|---|---|---|---|---|---|
| `deepseek/deepseek-v4.1-flash-1017` | 7 of 10 | 2 | 1 | 18.3 | 22.9 | 0.006 |
| `mistralai/mistral-small-2603` | 2 of 10 | 6 | 2 | 21.6 | 28.6 | 0.003 |
| `z-ai/glm-5.3` | 9 of 10 | 1 | 0 | 7.9 | 14.4 | 0.007 |
| `mistralai/mistral-large-4-0` | 2 of 3 | 0 | 1 | 209.7 | 215.7 | 0.026 |

**A first run that failed, kept.** The first run lost 43 of 80 calls. By the probe report's account, it gave reasoning models 8,000 tokens for thinking and answer together; their thinking used it up, and the answer came cut off or not at all. The second run asked for little thinking and allowed 12,000 tokens. The failed run is kept in full and its numbers are not mixed into the tables above.

| Model | Calls | Failed | Cost, USD |
|---|---|---|---|
| `deepseek/deepseek-v4.1-flash-1017` | 17 | 6 | 0.18 |
| `mistralai/mistral-small-2603` | 17 | 4 | 0.01 |
| `z-ai/glm-5.3` | 17 | 17 | 1.29 |
| `mistralai/mistral-large-4-0` | 17 | 16 | 0.34 |
| judge | 12 | 0 | 0.07 |
| **all** | 80 | 43 | 1.89 |

The files record the failure message and the tokens used (a failed call includes its one repair attempt), not the cause:

| Model | Failure message | Calls | Tokens used |
|---|---|---|---|
| `deepseek/deepseek-v4.1-flash-1017` | empty or malformed items | 3 | 12115 to 15106 |
| `deepseek/deepseek-v4.1-flash-1017` | not JSON | 3 | 17558 to 18930 |
| `mistralai/mistral-large-4-0` | HTTP 400 | 15 | - |
| `mistralai/mistral-large-4-0` | empty or malformed items | 1 | 18245 to 18245 |
| `mistralai/mistral-small-2603` | empty or malformed items | 4 | 2860 to 4284 |
| `z-ai/glm-5.3` | not JSON | 17 | 17204 to 24412 |

The token budget fits the reasoning models' failures, which used 12,115 to 24,412 tokens over a call and its repair. It does not explain the 15 HTTP 400 errors of `mistral-large-4-0`, whose cause was not recorded, nor the 4 failures of `mistral-small-2603`, which used few tokens and left list items empty.

**A builder's read never said "nothing left".** Given the seven design statements as they were approved and built, each of the three models found something a builder would still have to guess in 7 of 7 (65, 46 and 38 items). The read lists details to settle; it cannot be a test that a request is clear.

**Limits.** One rater wrote the key and gave the scores; a second rater would move single cells, and the order of the models rests on differences of three to six decisions. One run per model and request, first turns only. Ten requests from one person. The findings each model saw were one paragraph long.

## 3. A fault in the engine's own approval gate

Version 2 can run Claude Code through the Agent SDK and show each permission request in a web page, where the user presses Allow or Deny. A hardening round before release 028 (three time-boxed reviews of 25 minutes each by coding agents I ran, critical faults only) drove that page in a browser against a faked SDK session and found that a permission request was shown on one line, cut at 500 characters, while Allow passed the agent's whole input to the tool. A second line of a shell command, or the end of a long one, would run without being seen. The fault had been present in every release since the launcher was added (phase 4). The fix in release 028 shows a request whole with its line breaks, shows the input of a tool that is named alone, and refuses without asking any request longer than 20,000 characters or holding characters that hide or reorder text (control characters, zero-width characters, bidirectional overrides). A regression test feeds it a two-line command, a 600-character command with a pipe at its end, a bidi-reversed command and an over-long one, and checks what is shown and what is refused. The class of fault is known: an approval step is only as good as the match between what it shows and what runs, and text that renders differently from how it executes (for example the bidirectional-override attacks of "Trojan Source: Invisible Vulnerabilities", arXiv:2111.00169) defeats a human reviewer.

**Limits.** Found by review, in a build used by one person; not seen exploited. The fix covers this page only, not the agent's own terminal prompt.

## How this was measured

| | Finding 1 | Finding 2 | Finding 3 |
|---|---|---|---|
| Engine | Version 1 design, against a stand-in server with its four tools | Version 2, phase 0 probe (the model calls the engine would make) | Version 2, releases 027 (fault) and 028 (fix) |
| Agents and models | Claude Code 2.1.302 with `claude-fable-5-2`, effort xhigh; OpenCode 2.3.2 with `openrouter/deepseek/deepseek-v4.1-flash-1017` | `deepseek/deepseek-v4.1-flash-1017`, `mistralai/mistral-small-2603`, `z-ai/glm-5.3`, `mistralai/mistral-large-4-0`; judge `mistralai/mistral-medium-3-5`; all through OpenRouter, each served by Mistral as the provider | Claude Code through the Claude Agent SDK, faked in the review |
| Date | 2026-11-18 | 2026-11-19 | review 2026-11-21 |
| Runs or calls | 149 runner rows kept (of 198 runs in all; the other 49 were single questions asked by hand and not kept) | 161 model calls in two runs | 1 finding of 3 reviews |
| Cost | Rows kept: Claude Code USD 32.47 (the agent's own API-equivalent estimate; the runs used a subscription), OpenCode USD 0.26 | USD 4.15 recorded in the result files (first run 1.89, second 2.26); USD 4.20 read back from the key, including a few diagnostic calls | none |

Median cost and time per run in finding 1 (the 20 runs in its table): Claude Code USD 0.522 and 89 s, OpenCode USD 0.007 and 42 s.

## What this does not show

- Rates. The samples are 2 to 10 per cell; they show direction.
- Anything about Claude models as gap-readers: none was tried in finding 2.
- Long or real tasks: finding 1 used a toy build, finding 2 first turns only.
- Agreement between raters: there was one rater, who also wrote the key.
- That the approval fault was ever exploited, or that the fixed page is now safe in general.
- Other agents, other model versions, or interactive use (finding 1 ran almost entirely non-interactively).

## How it was built

I designed both versions of the engine and all three probes, decided what to measure, wrote the answer key and scored every answer by hand. Coding agents (Claude Code) wrote most of the code of the engine and of the probe scripts, under that design and review. The review round in finding 3 was three time-boxed reviews of the built app by coding agents (Claude Code) that I started and directed. `scripts/tables.py` was written for this report and reads the probes' result files in place.

To recompute: `python3 -I scripts/tables.py <version-1 probe folder> <version-2 probe folder> > results/tables.md`. The probe folders themselves are not published, because they hold the private requests.

## Licence

Apache License 2.0: see [LICENSE](LICENSE).

## Sources

The probes and the engine's implementation are private. The files below are named so that each number can be traced, not because a reader can open them.

- Finding 1: version 1 probe, `probe.md` sections 1, 2, 4.1, 4.7 and 4.8; its `results.jsonl` (groups `flow`, `flow2`, `ocflow`); its runner `stub/run.mjs` for the arm definitions.
- Finding 2: version 2 probe, `probe.md` sections 2, 4, 5, 6, 7 and 8; `scores.json` (hand scores); `wishes.json` (the answer key, counts only); `results.jsonl` (second run, including the judge); `results-first-run.jsonl` (the failed first run); `probe.mjs` (prompts, token limits, the judge model); `show.mjs` (used to read an answer beside the key).
- Finding 3: version 2 implementation, `phase-5-plan.md` section "Hardening round, release 027"; the engine's own `README.md` (release notes for 028); `src/launch.ts` (the fix); `test/launch.test.ts` (the regression test, "review of 2026-11-21").
- All tables: `results/tables.md`, generated by `scripts/tables.py`.
