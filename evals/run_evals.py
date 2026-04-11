#!/usr/bin/env python3
"""
Mubert Skills Eval Runner

Follows the Agent Skills eval specification:
https://agentskills.io/skill-creation/evaluating-skills

Runs each eval with and without the skill, grades assertions,
computes delta, and outputs structured workspace results.

Uses local Claude Code CLI (`claude -p`) — skills load automatically.

Usage:
    cd /path/to/skills

    # Run all evals (iteration auto-increments)
    python evals/run_evals.py

    # Single skill
    python evals/run_evals.py --skill mubert-generate

    # Trigger evals only (fast)
    python evals/run_evals.py --trigger-only

    # Functional evals only
    python evals/run_evals.py --functional-only

    # Specific iteration number
    python evals/run_evals.py --iteration 3

    # Preview
    python evals/run_evals.py --dry-run

Workspace structure (per spec):
    evals/workspace/
    └── iteration-1/
        ├── mubert-generate/
        │   ├── eval-1/
        │   │   ├── with_skill/
        │   │   │   ├── outputs/
        │   │   │   ├── timing.json
        │   │   │   └── grading.json
        │   │   └── without_skill/
        │   │       ├── outputs/
        │   │       ├── timing.json
        │   │       └── grading.json
        │   └── trigger/
        │       └── results.json
        ├── benchmark.json
        └── feedback.json
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from statistics import mean, stdev

SKILLS_ROOT = Path(__file__).resolve().parent.parent
EVALS_ROOT = Path(__file__).resolve().parent
WORKSPACE = EVALS_ROOT / "workspace"
SKILLS = [
    "mubert-setup",
    "mubert-generate",
    "mubert-streaming",
    "mubert-library",
    "mubert-manage",
]

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"


# --- Claude Code CLI ---


def claude_run(prompt: str, *, skill_path: str | None = None, timeout: int = 180) -> dict:
    """
    Run a prompt through Claude Code CLI.
    If skill_path is None, runs with --disable-slash-commands (no skills = baseline).
    """
    cmd = [
        "claude", "-p",
        "--output-format", "json",
        "--no-session-persistence",
        "--dangerously-skip-permissions",
    ]
    if skill_path is None:
        cmd.append("--disable-slash-commands")

    cmd.append(prompt)

    start = time.time()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(SKILLS_ROOT),
        timeout=timeout,
    )
    duration_ms = int((time.time() - start) * 1000)

    if result.returncode != 0:
        return {
            "text": f"[ERROR] {result.stderr.strip()}",
            "duration_ms": duration_ms,
            "total_tokens": 0,
        }

    try:
        data = json.loads(result.stdout)
        text = data.get("result", result.stdout.strip())
        total_tokens = 0
        usage = data.get("usage", {})
        if usage:
            total_tokens = usage.get("total_tokens", 0) or (
                usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            )
        return {"text": text, "duration_ms": duration_ms, "total_tokens": total_tokens}
    except json.JSONDecodeError:
        return {"text": result.stdout.strip(), "duration_ms": duration_ms, "total_tokens": 0}


# --- Grading ---


def grade_assertions(agent_output: str, assertions: list[str]) -> dict:
    """
    Grade assertions against agent output using Claude as judge.
    Returns grading.json structure per spec.
    """
    assertions_text = "\n".join(f"{i+1}. {a}" for i, a in enumerate(assertions))

    prompt = (
        "You are a strict grader. For each assertion, check if the agent output satisfies it.\n"
        "Require concrete evidence for a PASS — don't give the benefit of the doubt.\n\n"
        f"AGENT OUTPUT:\n---\n{agent_output}\n---\n\n"
        f"ASSERTIONS:\n{assertions_text}\n\n"
        "Respond with ONLY this JSON (no markdown fences, no explanation):\n"
        '{"assertion_results": [{"text": "assertion", "passed": true, "evidence": "quote or reason"}], '
        '"summary": {"passed": N, "failed": N, "total": N, "pass_rate": 0.XX}}'
    )

    result = claude_run(prompt, skill_path="grader")
    text = result["text"].strip()

    # Strip markdown fences
    if "```" in text:
        parts = text.split("```")
        for part in parts[1:]:
            cleaned = part.strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
            if cleaned.startswith("{"):
                text = cleaned
                break

    try:
        grading = json.loads(text)
        # Ensure summary exists
        if "summary" not in grading:
            results = grading.get("assertion_results", [])
            p = sum(1 for r in results if r.get("passed"))
            t = len(results)
            grading["summary"] = {
                "passed": p,
                "failed": t - p,
                "total": t,
                "pass_rate": round(p / t, 3) if t else 0,
            }
        return grading
    except json.JSONDecodeError:
        n = len(assertions)
        return {
            "assertion_results": [
                {"text": a, "passed": False, "evidence": "Grading parse error"}
                for a in assertions
            ],
            "summary": {"passed": 0, "failed": n, "total": n, "pass_rate": 0.0},
        }


# --- Trigger Evals ---


def run_trigger_evals(skill_name: str, iter_dir: Path) -> dict | None:
    eval_file = EVALS_ROOT / skill_name / "trigger_eval.json"
    if not eval_file.exists():
        return None

    data = json.loads(eval_file.read_text())
    triggers = data["triggers"]

    # Load all skill descriptions
    descriptions = []
    for sn in SKILLS:
        skill_md = SKILLS_ROOT / sn / "SKILL.md"
        if not skill_md.exists():
            continue
        text = skill_md.read_text()
        name = desc = ""
        for line in text.split("\n"):
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip()
            elif line.startswith("description:"):
                desc = line.split(":", 1)[1].strip()
        if name:
            descriptions.append(f"- {name}: {desc}")
    skills_list = "\n".join(descriptions)

    results = []
    passed = 0

    for t in triggers:
        prompt = t["prompt"]
        should_trigger = t["should_trigger"]

        ask = (
            f"You have these skills:\n\n{skills_list}\n\n"
            f'User says: "{prompt}"\n\n'
            f'Reply with ONLY the skill name (e.g. "mubert-generate") or "none". Nothing else.'
        )

        response = claude_run(ask, timeout=60)
        answer = response["text"].strip().lower()

        did_pass = (skill_name in answer) if should_trigger else (skill_name not in answer)
        if did_pass:
            passed += 1

        results.append({
            "prompt": prompt,
            "should_trigger": should_trigger,
            "agent_answer": answer,
            "passed": did_pass,
        })

        status = f"{GREEN}PASS{RESET}" if did_pass else f"{RED}FAIL{RESET}"
        expect = f"trigger={skill_name}" if should_trigger else "no trigger"
        print(f"  [{status}] {expect}: \"{prompt}\" → {answer}")

    total = len(triggers)
    result = {
        "skill": skill_name,
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 3) if total else 0,
        "results": results,
    }

    # Save to workspace
    trigger_dir = iter_dir / skill_name / "trigger"
    trigger_dir.mkdir(parents=True, exist_ok=True)
    (trigger_dir / "results.json").write_text(json.dumps(result, indent=2))

    return result


# --- Functional Evals ---


def run_single_eval(
    prompt: str,
    assertions: list[str],
    *,
    skill_path: str | None,
    output_dir: Path,
) -> dict:
    """Run one eval (with or without skill) and save results per spec."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir = output_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    # Run the prompt
    response = claude_run(prompt, skill_path=skill_path)

    # Save timing.json
    timing = {
        "total_tokens": response["total_tokens"],
        "duration_ms": response["duration_ms"],
    }
    (output_dir / "timing.json").write_text(json.dumps(timing, indent=2))

    # Save raw output
    (outputs_dir / "response.txt").write_text(response["text"])

    # Grade assertions
    grading = grade_assertions(response["text"], assertions)
    (output_dir / "grading.json").write_text(json.dumps(grading, indent=2))

    return {
        "timing": timing,
        "grading": grading,
    }


def run_functional_evals(skill_name: str, iter_dir: Path) -> dict | None:
    eval_file = EVALS_ROOT / skill_name / "evals.json"
    if not eval_file.exists():
        return None

    data = json.loads(eval_file.read_text())
    evals = data["evals"]
    skill_dir = iter_dir / skill_name

    eval_results = []

    for eval_case in evals:
        eval_id = eval_case["id"]
        prompt = eval_case["prompt"]
        assertions = eval_case.get("assertions", [])
        eval_name = f"eval-{eval_id}"

        print(f"\n  Eval #{eval_id}: \"{prompt}\"")

        # --- with_skill ---
        print(f"    Running with skill...")
        with_result = run_single_eval(
            prompt, assertions,
            skill_path=str(SKILLS_ROOT / skill_name),
            output_dir=skill_dir / eval_name / "with_skill",
        )

        # --- without_skill ---
        print(f"    Running without skill...")
        without_result = run_single_eval(
            prompt, assertions,
            skill_path=None,
            output_dir=skill_dir / eval_name / "without_skill",
        )

        # Print assertion results — with_skill (detailed)
        ws = with_result["grading"]["summary"]
        print(f"    With skill: {ws['passed']}/{ws['total']}")
        for ar in with_result["grading"]["assertion_results"]:
            s = f"{GREEN}PASS{RESET}" if ar["passed"] else f"{RED}FAIL{RESET}"
            print(f"      [{s}] {ar['text']}")
            if not ar["passed"]:
                print(f"             → {ar['evidence']}")

        # Without skill — collapsed summary (failures are expected)
        wos = without_result["grading"]["summary"]
        print(f"    {DIM}Without skill: {wos['passed']}/{wos['total']} (baseline){RESET}")

        eval_results.append({
            "eval_id": eval_id,
            "prompt": prompt,
            "with_skill": {
                "pass_rate": with_result["grading"]["summary"]["pass_rate"],
                "tokens": with_result["timing"]["total_tokens"],
                "duration_ms": with_result["timing"]["duration_ms"],
            },
            "without_skill": {
                "pass_rate": without_result["grading"]["summary"]["pass_rate"],
                "tokens": without_result["timing"]["total_tokens"],
                "duration_ms": without_result["timing"]["duration_ms"],
            },
        })

    # Aggregate per spec
    with_rates = [e["with_skill"]["pass_rate"] for e in eval_results]
    without_rates = [e["without_skill"]["pass_rate"] for e in eval_results]
    with_tokens = [e["with_skill"]["tokens"] for e in eval_results]
    without_tokens = [e["without_skill"]["tokens"] for e in eval_results]
    with_times = [e["with_skill"]["duration_ms"] / 1000 for e in eval_results]
    without_times = [e["without_skill"]["duration_ms"] / 1000 for e in eval_results]

    def safe_stdev(vals):
        return round(stdev(vals), 3) if len(vals) > 1 else 0.0

    summary = {
        "skill": skill_name,
        "total_evals": len(evals),
        "run_summary": {
            "with_skill": {
                "pass_rate": {"mean": round(mean(with_rates), 3), "stddev": safe_stdev(with_rates)},
                "time_seconds": {"mean": round(mean(with_times), 1), "stddev": safe_stdev(with_times)},
                "tokens": {"mean": round(mean(with_tokens)), "stddev": safe_stdev(with_tokens)},
            },
            "without_skill": {
                "pass_rate": {"mean": round(mean(without_rates), 3), "stddev": safe_stdev(without_rates)},
                "time_seconds": {"mean": round(mean(without_times), 1), "stddev": safe_stdev(without_times)},
                "tokens": {"mean": round(mean(without_tokens)), "stddev": safe_stdev(without_tokens)},
            },
            "delta": {
                "pass_rate": round(mean(with_rates) - mean(without_rates), 3),
                "time_seconds": round(mean(with_times) - mean(without_times), 1),
                "tokens": round(mean(with_tokens) - mean(without_tokens)),
            },
        },
        "eval_results": eval_results,
    }

    return summary


# --- Workspace ---


def get_next_iteration(workspace: Path) -> int:
    if not workspace.exists():
        return 1
    existing = [
        int(d.name.split("-")[1])
        for d in workspace.iterdir()
        if d.is_dir() and d.name.startswith("iteration-")
    ]
    return max(existing, default=0) + 1


def create_feedback_template(iter_dir: Path, skills: list[str]):
    """Create empty feedback.json for human review."""
    feedback = {}
    for skill in skills:
        skill_dir = iter_dir / skill
        if not skill_dir.exists():
            continue
        for eval_dir in sorted(skill_dir.iterdir()):
            if eval_dir.is_dir() and eval_dir.name.startswith("eval-"):
                feedback[f"{skill}/{eval_dir.name}"] = ""
    (iter_dir / "feedback.json").write_text(json.dumps(feedback, indent=2))


# --- Main ---


def main():
    parser = argparse.ArgumentParser(
        description="Mubert Skills Eval Runner (per agentskills.io spec)"
    )
    parser.add_argument("--trigger-only", action="store_true", help="Trigger evals only")
    parser.add_argument("--functional-only", action="store_true", help="Functional evals only")
    parser.add_argument("--skill", type=str, help="Single skill to test")
    parser.add_argument("--iteration", type=int, help="Force iteration number")
    parser.add_argument("--dry-run", action="store_true", help="Preview what would run")
    args = parser.parse_args()

    skills_to_test = [args.skill] if args.skill else SKILLS
    run_triggers = not args.functional_only
    run_functional = not args.trigger_only

    # Check Claude Code CLI
    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Error: Claude Code CLI not found.")
        print("Install: npm install -g @anthropic-ai/claude-code")
        sys.exit(1)

    # Dry run
    if args.dry_run:
        print("Dry run — would test:\n")
        for skill in skills_to_test:
            if run_triggers:
                tf = EVALS_ROOT / skill / "trigger_eval.json"
                if tf.exists():
                    d = json.loads(tf.read_text())
                    print(f"  {skill}/trigger_eval.json — {len(d['triggers'])} triggers")
            if run_functional:
                ef = EVALS_ROOT / skill / "evals.json"
                if ef.exists():
                    d = json.loads(ef.read_text())
                    n_a = sum(len(e.get("assertions", [])) for e in d["evals"])
                    print(f"  {skill}/evals.json — {len(d['evals'])} evals, {n_a} assertions")
                    print(f"    (each eval runs twice: with_skill + without_skill)")
        return

    # Set up iteration workspace
    iteration_num = args.iteration or get_next_iteration(WORKSPACE)
    iter_dir = WORKSPACE / f"iteration-{iteration_num}"
    iter_dir.mkdir(parents=True, exist_ok=True)
    print(f"Workspace: {iter_dir}\n")

    benchmark = {
        "iteration": iteration_num,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trigger_results": [],
        "functional_results": [],
    }
    start_time = time.time()

    # --- Trigger evals ---
    if run_triggers:
        print("=" * 60)
        print("TRIGGER EVALS")
        print("=" * 60)
        for skill in skills_to_test:
            print(f"\n--- {skill} ---")
            result = run_trigger_evals(skill, iter_dir)
            if result:
                benchmark["trigger_results"].append(result)
                rate = result["pass_rate"] * 100
                c = GREEN if rate >= 80 else YELLOW if rate >= 60 else RED
                print(f"\n  Result: {result['passed']}/{result['total']} ({c}{rate:.1f}%{RESET})")

    # --- Functional evals ---
    if run_functional:
        print("\n" + "=" * 60)
        print("FUNCTIONAL EVALS (with_skill vs without_skill)")
        print("=" * 60)
        for skill in skills_to_test:
            print(f"\n--- {skill} ---")
            result = run_functional_evals(skill, iter_dir)
            if result:
                benchmark["functional_results"].append(result)
                rs = result["run_summary"]
                w = rs["with_skill"]["pass_rate"]["mean"] * 100
                wo = rs["without_skill"]["pass_rate"]["mean"] * 100
                delta = rs["delta"]["pass_rate"] * 100
                cw = GREEN if w >= 80 else YELLOW if w >= 60 else RED
                cd = GREEN if delta > 0 else RED if delta < 0 else YELLOW
                print(f"\n  With skill:    {cw}{w:.1f}%{RESET}")
                print(f"  Without skill: {wo:.1f}%")
                print(f"  Delta:         {cd}{delta:+.1f}%{RESET}")
                print(f"  Tokens delta:  {rs['delta']['tokens']:+} avg")
                print(f"  Time delta:    {rs['delta']['time_seconds']:+.1f}s avg")

    # --- Summary ---
    total_duration = time.time() - start_time
    benchmark["total_duration_s"] = round(total_duration, 1)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if benchmark["trigger_results"]:
        print("\n  Trigger evals:")
        for r in benchmark["trigger_results"]:
            rate = r["pass_rate"] * 100
            c = GREEN if rate >= 80 else YELLOW if rate >= 60 else RED
            print(f"    {r['skill']:25s} {r['passed']}/{r['total']:>3} = {c}{rate:.1f}%{RESET}")

    if benchmark["functional_results"]:
        print("\n  Functional evals (with_skill → delta):")
        for r in benchmark["functional_results"]:
            rs = r["run_summary"]
            w = rs["with_skill"]["pass_rate"]["mean"] * 100
            d = rs["delta"]["pass_rate"] * 100
            cw = GREEN if w >= 80 else YELLOW if w >= 60 else RED
            cd = GREEN if d > 0 else RED if d < 0 else YELLOW
            print(f"    {r['skill']:25s} {cw}{w:.1f}%{RESET}  ({cd}{d:+.1f}%{RESET} vs baseline)")

    print(f"\n  Duration: {total_duration:.1f}s")

    # Save benchmark
    (iter_dir / "benchmark.json").write_text(json.dumps(benchmark, indent=2, ensure_ascii=False))
    print(f"  Benchmark: {iter_dir / 'benchmark.json'}")

    # Create feedback template for human review
    if run_functional:
        create_feedback_template(iter_dir, skills_to_test)
        print(f"  Feedback:  {iter_dir / 'feedback.json'} (fill in after review)")

    print(f"\n  Next step: review outputs in {iter_dir}")
    print(f"  Then fill in feedback.json with specific, actionable notes.")


if __name__ == "__main__":
    main()