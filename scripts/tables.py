#!/usr/bin/env python3
"""Recompute the measured numbers in README.md from the two probes' own files, read in place.

    python3 -I scripts/tables.py <version-1 probe folder> <version-2 probe folder> > results/tables.md

Standard library only. It reads results.jsonl (version 1) and wishes.json, scores.json, results.jsonl and
results-first-run.jsonl (version 2). It prints counts, model ids and costs only: never the text of a wish,
an answer key item or a model's answer, since those are private.
"""
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path


def jsonl(path):
    return [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]


def pct(a, b):
    return f"{round(100 * a / b)}%" if b else "-"


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


# ---------------------------------------------------------------- version 1: authority of a tool result
def v1(folder):
    rows = jsonl(Path(folder) / "results.jsonl")
    built = lambda r: r["files"].get("built") == "c"
    claude = lambda r: r["agent"].startswith("claude")
    # The arms, as the runner names them (stub/run.mjs): group "flow" has the pointer without the authority
    # sentence; group "flow2" has notes "result", "pointer", "both"; group "ocflow" note "instructions" has no pointer at all.
    arms = [
        ("Pointer says only that the user's direct words come first", lambda r: r["group"] == "flow"),
        ("Tool result says the decision is the user's own", lambda r: r["group"] == "flow2" and r["note"] == "result"),
        ("Project pointer says a page decision is the user's own word", lambda r: r["group"] == "flow2" and r["note"] == "pointer"),
        ("Both", lambda r: r["group"] == "flow2" and r["note"] == "both"),
        ("No pointer at all, only the server's instructions", lambda r: r["group"] == "ocflow" and r["note"] == "instructions"),
    ]
    out = ["## Version 1: does the agent build after a go-ahead that arrives as a tool result?\n"]
    trs = []
    for name, f in arms:
        cells = []
        for is_claude in (True, False):
            sel = [r for r in rows if f(r) and claude(r) == is_claude]
            cells.append(f"{sum(map(built, sel))} of {len(sel)}" if sel else "not run")
        trs.append([name, *cells])
    out.append(table(["What gave the page decision its authority", "Claude Code built", "OpenCode built"], trs))
    without = [r for r in rows if claude(r) and (arms[0][1](r) or arms[1][1](r))]
    with_ = [r for r in rows if claude(r) and (arms[2][1](r) or arms[3][1](r))]
    out.append(f"\nClaude Code, no authority sentence in the pointer: built in {sum(map(built, without))} of {len(without)} runs. "
               f"With it: {sum(map(built, with_))} of {len(with_)}.")
    wrote_options = [r for r in rows if r["files"].get("options", 0) > 0]
    early = sum(1 for r in wrote_options if r["files"].get("builtBeforeDecision"))
    out.append(f"\nRunner rows that wrote design options: {len(wrote_options)}; of these, built before a decision existed: {early}.")
    models = Counter(r["init"]["model"] for r in rows if claude(r) and isinstance(r.get("init"), dict) and r["init"].get("model"))
    out.append(f"\nRows in results.jsonl: {len(rows)}. Claude Code model as reported by the agent: "
               + ", ".join(f"`{m}` ({n} rows)" for m, n in models.items()) + ".")
    cost = defaultdict(list)
    for name, f in arms:
        for r in rows:
            if f(r):
                cost["Claude Code" if claude(r) else "OpenCode"].append((float(r["cost"]), float(r["secs"])))
    out.append("\n" + table(["Agent, runs above", "Runs", "Median cost per run, USD", "Median seconds per run"],
                            [[a, len(v), f"{statistics.median(c for c, _ in v):.3f}", f"{statistics.median(s for _, s in v):.0f}"] for a, v in cost.items()]))
    tot = Counter()
    for r in rows:
        tot["Claude Code" if claude(r) else "OpenCode"] += float(r["cost"] or 0)
    out.append("\nAll runner rows in results.jsonl, total cost: " + ", ".join(f"{a} USD {v:.2f}" for a, v in tot.items()) + ".")
    out.append("\nClaude Code costs are the agent's own estimate of API-equivalent cost; the runs used a subscription.")
    return "\n".join(out)


# ---------------------------------------------------------------- version 2: four models read a wish for gaps
# Neutral categories in place of the wishes' titles; the wishes themselves are not published.
CATEGORY = {
    "c": "A. Design round, file-organising desktop tool",
    "d": "B. Design round, file-organising desktop tool",
    "e": "C. Design round, file-organising desktop tool",
    "f": "D. Design round, file-organising desktop tool",
    "g": "E. Design round, file-organising desktop tool",
    "l": "F. Design round, file-organising desktop tool",
    "h": "G. Design round, file-organising desktop tool",
    "p1": "H. First version of a poker hand viewer",
    "p2": "I. Small UI change to that hand viewer (no findings)",
    "v2": "J. Redesign of the agent engine itself (no findings)",
}
SHORT = {"deepseek/deepseek-v4.1-flash-1017": "deepseek", "mistralai/mistral-small-2603": "mistral-small",
         "z-ai/glm-5.3": "glm", "mistralai/mistral-large-4-0": "mistral-large"}
ORDER = list(SHORT)


def v2(folder):
    folder = Path(folder)
    wishes = {w["id"]: w for w in json.load(open(folder / "wishes.json", encoding="utf-8"))}
    scores = json.load(open(folder / "scores.json", encoding="utf-8"))
    rows = jsonl(folder / "results.jsonl")
    first = jsonl(folder / "results-first-run.jsonl")
    assert set(CATEGORY) == set(wishes), "the wish ids changed"
    need = {k: len(w["needed"]) for k, w in wishes.items()}
    gaps = {(r["wish"], r["model"]): r for r in rows if r["job"] == "gaps" and r["ok"]}
    asked = lambda r: sum(1 for g in r["value"]["gaps"] if g["type"] == "decision")
    hand = lambda wish, model: scores.get(wish, {}).get(SHORT[model])
    out = ["## Version 2: what four models find missing in a wish (first turn, scored by hand)\n",
           f"Wishes: {len(wishes)}. Answer key: {sum(need.values())} decisions, "
           f"{min(need.values())} to {max(need.values())} per wish.\n"]

    def score_rows(subset, models=ORDER):
        trs = []
        for m in models:
            ws = [w for w in subset if (w, m) in gaps]
            if not ws:
                continue
            for w in ws:
                assert hand(w, m) is not None, f"no hand score for {w} {m}"
            n = sum(need[w] for w in ws)
            raised = sum(len(set(hand(w, m)["raised"])) for w in ws)
            q = sum(asked(gaps[(w, m)]) for w in ws)
            nl = sum(len(hand(w, m)["needless"]) for w in ws)
            trs.append([f"`{m}`", f"{len(ws)} of {len(subset)}", f"{raised} of {n} ({pct(raised, n)})", q,
                        f"{q / len(ws):.1f}", f"{nl} ({pct(nl, q)})"])
        return table(["Model", "Wishes answered", "Key decisions raised", "Questions asked", "Per wish", "Needless"], trs)

    out.append("### All wishes each model answered\n")
    out.append(score_rows(list(wishes)))
    out.append("\n`mistral-large-4-0` was asked three wishes only. A failed call drops its wish, so the denominators differ.\n")
    three = ORDER[:3]
    common = [w for w in wishes if all((w, m) in gaps for m in three)]
    out.append(f"### Common subset: the {len(common)} wishes all of deepseek, mistral-small and glm answered\n")
    out.append(score_rows(common, three))
    common4 = [w for w in wishes if all((w, m) in gaps for m in ORDER)]
    out.append(f"\n### Common subset of all four models: {len(common4)} wishes\n")
    out.append(score_rows(common4))

    out.append("\n### Per wish: key decisions raised, then questions asked\n")
    trs = []
    for w in wishes:
        cells = [f"{len(set(hand(w, m)['raised']))} · {asked(gaps[(w, m)])}" if (w, m) in gaps else "no answer" for m in three]
        trs.append([CATEGORY[w], need[w], *cells])
    out.append(table(["Wish (category)", "Key decisions", *(SHORT[m] for m in three)], trs))

    reasons = Counter(r for w in scores if w != "_" for m in three for r in scores[w].get(SHORT[m], {}).get("needless", {}).values())
    out.append("\nWhy a question was needless, the three models together: "
               + ", ".join(f"{k} {v}" for k, v in reasons.most_common()) + f" (total {sum(reasons.values())}). "
               "process = asks how to proceed or what to deliver when the wish says; settled = the wish or findings answer it; "
               "fact = asks the meaning of a name the project defines; duplicate = repeats another question.")
    agent = [w for w in wishes.values() if w.get("agentAsked") is not None and w.get("handin") and "statement" in w]
    a, p = sum(w["agentAsked"] for w in agent), sum(w["agentProcess"] for w in agent)
    out.append(f"\nFor comparison, the coding agent itself in the {len(agent)} design rounds of the desktop tool that it asked in: "
               f"{a} questions, {p} of them asking permission for the next step ({pct(p, a)}).")

    # The judge model against the hand scores, item by item, on every answer both scored.
    judge = [r for r in rows if r["job"] == "judge"]
    items = agree = j_raised = h_raised = j_only = h_only = j_needless = h_needless = 0
    for r in judge:
        if not r["ok"]:
            continue
        h = hand(r["wish"], r["of"])
        n = need[r["wish"]]
        jr = {x["key"] for x in r["value"]["needed"] if x["covered"] and 1 <= x["key"] <= n}
        hr = set(h["raised"])
        for k in range(1, n + 1):
            items += 1
            agree += (k in jr) == (k in hr)
            j_only += k in jr and k not in hr
            h_only += k in hr and k not in jr
        j_raised += len(jr)
        h_raised += len(hr)
        j_needless += sum(1 for d in r["value"]["decisions"] if d["verdict"] == "needless")
        h_needless += len(h["needless"])
    ok = [r for r in judge if r["ok"]]
    out.append("\n### A model as judge (`mistralai/mistral-medium-3-5`) against the hand scores\n")
    out.append(table(["Measure", "Value"], [
        ["Judge calls ok", f"{len(ok)} of {len(judge)}; failed: " + ", ".join(f"{e} ({n})" for e, n in Counter(r["error"] for r in judge if not r["ok"]).items())],
        ["Key items scored by both", items],
        ["Items where judge and hand agree", f"{agree} ({pct(agree, items)})"],
        ["Raised, judge / hand", f"{j_raised} / {h_raised}"],
        ["Raised by judge only / by hand only", f"{j_only} / {h_only}"],
        ["Needless questions, judge / hand (same answers)", f"{j_needless} / {h_needless}"],
        ["Judge median seconds per call", f"{statistics.median(r['ms'] for r in ok) / 1000:.0f}"],
        ["Judge median cost per call, USD", f"{statistics.median(r['cost'] for r in ok):.3f}"],
        ["Judge total cost, USD", f"{sum(r.get('cost') or 0 for r in judge):.2f}"],
    ]))

    out.append("\n### Time, shape and cost of the gap calls (second run)\n")
    trs = []
    for m in ORDER:
        g = [r for r in rows if r["job"] == "gaps" and r["model"] == m]
        okg = [r for r in g if r["ok"]]
        trs.append([f"`{m}`", f"{sum(1 for r in okg if not r['repaired'])} of {len(g)}", sum(1 for r in okg if r["repaired"]),
                    len(g) - len(okg), f"{statistics.median(r['ms'] for r in okg) / 1000:.1f}",
                    f"{max(r['ms'] for r in okg) / 1000:.1f}", f"{statistics.mean(r['cost'] for r in g):.3f}"])
    out.append(table(["Model", "Valid at once", "Valid after one repair", "Failed", "Median s (ok calls)", "Slowest s", "Mean cost per call, USD"], trs))
    fails = Counter((r["model"], r["error"].split(":")[0]) for r in rows if r["job"] == "gaps" and not r["ok"])
    out.append("\nFailed gap calls: " + "; ".join(f"`{m}`: {e} ({n})" for (m, e), n in fails.items()) + ".")

    out.append("\n### The builder's read: seven approved statements, what a builder would still have to guess\n")
    trs = []
    for m in three:
        b = [r for r in rows if r["job"] == "builder" and r["model"] == m and r["ok"]]
        left = [x for r in b for x in r["value"]["left"]]
        trs.append([f"`{m}`", f"{sum(1 for r in b if r['value']['nothing_left'])} of {len(b)}", len(left),
                    sum(1 for x in left if x["who"] == "person"), sum(1 for x in left if x["who"] == "agent")])
    out.append(table(["Model", "Said \"nothing left\"", "Items listed", "For the person", "For the agent"], trs))

    out.append("\n### The first run, kept as it failed\n")
    trs = []
    for m in ORDER:
        f = [r for r in first if r.get("model") == m]
        trs.append([f"`{m}`", len(f), sum(1 for r in f if not r["ok"]), f"{sum(r.get('cost') or 0 for r in f):.2f}"])
    jf = [r for r in first if r["job"] == "judge"]
    trs.append(["judge", len(jf), sum(1 for r in jf if not r["ok"]), f"{sum(r.get('cost') or 0 for r in jf):.2f}"])
    trs.append(["**all**", len(first), sum(1 for r in first if not r["ok"]), f"{sum(r.get('cost') or 0 for r in first):.2f}"])
    out.append(table(["Model", "Calls", "Failed", "Cost, USD"], trs))
    kinds = Counter("provider returned HTTP 400" if "400" in str(r["error"])
                    else "not JSON after one repair" if "not JSON" in str(r["error"])
                    else "empty or malformed items after one repair" for r in first if not r["ok"])
    out.append("\nFailure messages recorded in the first run: " + ", ".join(f"{k} {v}" for k, v in kinds.most_common()) + ".")
    by = defaultdict(list)
    for r in first:
        if not r["ok"]:
            e = str(r["error"])
            k = "HTTP 400" if "400" in e else "not JSON" if "not JSON" in e else "empty or malformed items"
            by[(r["model"], k)].append(r.get("tokens"))
    trs = [[f"`{m}`", k, len(t), "-" if None in t else f"{min(t)} to {max(t)}"] for (m, k), t in sorted(by.items())]
    out.append("\n" + table(["Model", "Failure message", "Calls", "Tokens used"], trs))
    out.append(f"\nModel cost recorded in the two result files together: USD {sum(r.get('cost') or 0 for r in rows + first):.2f} "
               f"(first run {sum(r.get('cost') or 0 for r in first):.2f}, second run {sum(r.get('cost') or 0 for r in rows):.2f}). "
               f"Calls recorded: {len(first) + len(rows)}.")
    dates = sorted(r["at"][:10] for r in rows + first if r.get("at"))
    out.append(f"\nCalls dated {dates[0]}" + (f" to {dates[-1]}." if dates[-1] != dates[0] else ", all of them."))
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    print("# Tables\n\nGenerated by `scripts/tables.py` from the probes' own result files. Do not edit by hand.\n")
    print(v1(sys.argv[1]))
    print()
    print(v2(sys.argv[2]))
