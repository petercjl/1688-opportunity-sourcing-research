#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "build_search_plan.py"
CATEGORIES = {
    "market_proven",
    "novel_structure",
    "aesthetic",
    "scenario_specific",
    "premium_quality",
    "solution_bundle",
}


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        source = root / "source.json"
        output = root / "plan.json"
        exact_query = "参考款核心品类 精确基准"
        source.write_text(json.dumps({
            "handoff_type": "ai_dianjing_to_1688_product_selection",
            "execution_policy": {"mode": "read_only_research"},
            "opportunities": [{
                "opportunity_id": "breadth-test",
                "name": "参考款",
                "job_to_be_done": "寻找参考图同款和同模具货源",
                "product_forms": ["带精确特征的参考款"],
                "portfolio_product_family": "核心产品族",
                "use_scenarios": ["目标场景"],
                "required_attributes": ["同款基准必须按参考图核对", "关键属性"],
                "search_tasks": [{
                    "task_id": "exact-baseline",
                    "capability": "1688-product-find.text_search",
                    "query": exact_query,
                }],
            }],
        }, ensure_ascii=False), encoding="utf-8")
        subprocess.run([sys.executable, str(SCRIPT), "--input", str(source), "--output", str(output)], check=True)
        plan = json.loads(output.read_text(encoding="utf-8"))
        tasks = plan["opportunities"][0]["search_tasks"]
        grouped = defaultdict(list)
        for task in tasks:
            if task["capability"] == "1688-product-find.text_search":
                grouped[task["strategy_category"]].append(task)
        assert set(grouped) == CATEGORIES
        assert exact_query in {task["query"] for task in grouped["market_proven"]}
        assert all(len(category_tasks) >= 3 for category_tasks in grouped.values())
        assert all(task.get("search_direction") for category_tasks in grouped.values() for task in category_tasks)
        assert all(task.get("search_round") == 1 for category_tasks in grouped.values() for task in category_tasks)
        derived_queries = [task["query"] for category_tasks in grouped.values() for task in category_tasks if task["query_origin"] == "derived_category_query"]
        assert all("参考图" not in query and "同款" not in query and "同模具" not in query for query in derived_queries)
        assert any("核心产品族" in query for query in derived_queries)
        assert len({task["task_id"] for task in tasks}) == len(tasks)

        missing_family = root / "missing-family.json"
        missing_output = root / "missing-plan.json"
        invalid = json.loads(source.read_text(encoding="utf-8"))
        del invalid["opportunities"][0]["portfolio_product_family"]
        missing_family.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")
        failed = subprocess.run([sys.executable, str(SCRIPT), "--input", str(missing_family), "--output", str(missing_output)], text=True, capture_output=True)
        assert failed.returncode != 0
        assert "require a broad portfolio_product_family" in (failed.stdout + failed.stderr)
    print("search expansion: ok")


if __name__ == "__main__":
    main()
