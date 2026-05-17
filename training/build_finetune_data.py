"""Build local fine-tuning datasets from DisasterRAG benchmark runs.

Outputs:
- sft_tool_planner.jsonl: query -> agent/tool planning targets
- sft_answerer.jsonl: evidence summary -> grounded final answer targets
- dpo_preferences.jsonl: chosen/rejected pairs built from multiple runs
- summary.json: dataset statistics and reward summaries

This is a no-dependency pipeline using only stdlib so it can run on the
same Windows environment as the app.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Ensure the repo root is on sys.path when the file is executed directly.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from training.rewarding import (
    extract_assistant_text,
    json_dumps_compact,
    make_answer_context,
    make_answer_target,
    make_planner_target,
    make_rejected_target,
    sample_reward,
)


SYSTEM_PLANNER = (
    "You are DisasterRAG's routing planner. Given a user query, choose the"
    " correct agent scope and tool plan for disaster management, weather, and"
    " flight operations. Return strict JSON only."
)

SYSTEM_ANSWERER = (
    "You are DisasterRAG's answer synthesizer. Given the query and a compact"
    " evidence summary from the agent runtime, produce a concise, grounded"
    " response. Avoid unsupported claims."
)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_queries(repo_root: Path) -> Dict[int, Dict[str, Any]]:
    queries_path = repo_root / "benchmark_queries.json"
    queries = load_json(queries_path)
    return {int(item["id"]): item for item in queries}


def read_runs(repo_root: Path) -> List[Tuple[str, List[Dict[str, Any]]]]:
    runs: List[Tuple[str, List[Dict[str, Any]]]] = []
    for path in sorted(glob.glob(str(repo_root / "benchmark_runs" / "run_*.json"))):
        data = load_json(Path(path))
        if isinstance(data, list):
            runs.append((Path(path).name, data))
    return runs


def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json_dumps_compact(row) + "\n")


def build_datasets(repo_root: Path) -> Dict[str, Any]:
    queries = read_queries(repo_root)
    runs = read_runs(repo_root)

    per_query_results: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for run_name, run_rows in runs:
        for result in run_rows:
            qid = int(result["id"])
            entry = dict(result)
            entry["run_name"] = run_name
            per_query_results[qid].append(entry)

    planner_rows: List[Dict[str, Any]] = []
    answer_rows: List[Dict[str, Any]] = []
    preference_rows: List[Dict[str, Any]] = []
    reward_summary: List[Dict[str, Any]] = []

    for qid, query_meta in queries.items():
        candidates = per_query_results.get(qid, [])
        if not candidates:
            continue

        scored: List[Tuple[float, Dict[str, float], Dict[str, Any]]] = []
        for result in candidates:
            reward, components = sample_reward(query_meta, result)
            scored.append((reward, components, result))

        scored.sort(key=lambda item: item[0], reverse=True)
        best_reward, best_components, best_result = scored[0]
        worst_reward, worst_components, worst_result = scored[-1]

        planner_rows.append(
            {
                "messages": [
                    {"role": "system", "content": SYSTEM_PLANNER},
                    {"role": "user", "content": query_meta["query"]},
                    {"role": "assistant", "content": make_planner_target(query_meta, best_result)},
                ],
                "metadata": {
                    "query_id": qid,
                    "category": query_meta.get("category"),
                    "best_reward": best_reward,
                    "run_name": best_result.get("run_name"),
                },
            }
        )

        answer_rows.append(
            {
                "messages": [
                    {"role": "system", "content": SYSTEM_ANSWERER},
                    {"role": "user", "content": make_answer_context(query_meta, best_result)},
                    {"role": "assistant", "content": make_answer_target(query_meta, best_result)},
                ],
                "metadata": {
                    "query_id": qid,
                    "category": query_meta.get("category"),
                    "best_reward": best_reward,
                    "run_name": best_result.get("run_name"),
                    "synthetic": True,
                },
            }
        )

        if (best_reward - worst_reward) >= 0.15:
            preference_rows.append(
                {
                    "prompt": [
                        {"role": "system", "content": SYSTEM_ANSWERER},
                        {"role": "user", "content": make_answer_context(query_meta, best_result)},
                    ],
                    "chosen": make_answer_target(query_meta, best_result),
                    "rejected": make_rejected_target(query_meta),
                    "metadata": {
                        "query_id": qid,
                        "category": query_meta.get("category"),
                        "chosen_reward": best_reward,
                        "rejected_reward": worst_reward,
                        "chosen_run": best_result.get("run_name"),
                        "rejected_run": worst_result.get("run_name"),
                        "chosen_components": best_components,
                        "rejected_components": worst_components,
                        "synthetic": True,
                    },
                }
            )

        reward_summary.append(
            {
                "query_id": qid,
                "query": query_meta.get("query"),
                "category": query_meta.get("category"),
                "best_reward": best_reward,
                "worst_reward": worst_reward,
                "reward_gap": round(best_reward - worst_reward, 3),
                "runs_seen": len(candidates),
                "best_run": best_result.get("run_name"),
                "best_components": best_components,
            }
        )

    return {
        "planner_rows": planner_rows,
        "answer_rows": answer_rows,
        "preference_rows": preference_rows,
        "summary": {
            "queries_with_runs": len(reward_summary),
            "planner_examples": len(planner_rows),
            "answer_examples": len(answer_rows),
            "preference_examples": len(preference_rows),
            "reward_summary": reward_summary,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build local fine-tuning data from benchmark runs.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "data" / "training")
    args = parser.parse_args()

    datasets = build_datasets(args.repo_root)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    write_jsonl(output_dir / "sft_tool_planner.jsonl", datasets["planner_rows"])
    write_jsonl(output_dir / "sft_answerer.jsonl", datasets["answer_rows"])
    write_jsonl(output_dir / "dpo_preferences.jsonl", datasets["preference_rows"])

    summary_path = output_dir / "summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(datasets["summary"], f, indent=2, ensure_ascii=True)

    print(f"Wrote planner dataset: {output_dir / 'sft_tool_planner.jsonl'}")
    print(f"Wrote answer dataset:  {output_dir / 'sft_answerer.jsonl'}")
    print(f"Wrote preference data: {output_dir / 'dpo_preferences.jsonl'}")
    print(f"Wrote summary:         {summary_path}")
    print(
        f"Samples: planner={len(datasets['planner_rows'])}, "
        f"answer={len(datasets['answer_rows'])}, "
        f"preferences={len(datasets['preference_rows'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
