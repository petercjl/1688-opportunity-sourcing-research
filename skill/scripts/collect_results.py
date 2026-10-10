#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from discover_runtime import invoke, inspect


ALLOWED = {"1688-product-find.text_search", "1688-source-suppliers"}
STRATEGY_CATEGORIES = {"market_proven", "novel_structure", "aesthetic", "scenario_specific", "premium_quality", "solution_bundle"}
SECRET_KEY = re.compile(r"(?:^|_)(?:ak|token|secret|password|cookie)(?:$|_)", re.I)


def fail(message):
    raise SystemExit(message)


def load(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def redact(value):
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if SECRET_KEY.search(str(k)) else redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def parse_envelope(stdout):
    text = stdout.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        if start < 0:
            return {"success": False, "markdown": "CLI did not return a JSON envelope", "raw_text": text}
        try:
            value, _ = json.JSONDecoder().raw_decode(text[start:])
            return value
        except json.JSONDecodeError:
            return {"success": False, "markdown": "CLI returned invalid JSON", "raw_text": text}


def run_cli(args):
    value,code=invoke(args)
    # Preserve the normalized capability envelope; application evidence reads this contract.
    value["success"]=value.get("ok") is True
    value["markdown"]=str(value.get("error",{}).get("message") or "query complete")
    return redact(value),code


def validate_input(data):
    if data.get("handoff_type") != "ai_dianjing_to_1688_product_selection":
        fail("Unsupported handoff_type")
    policy = data.get("execution_policy", {})
    if policy.get("mode") != "read_only_research":
        fail("Input execution policy must be read_only_research")
    seen = set()
    tasks = []
    for opportunity in data.get("opportunities", []):
        opp_id = str(opportunity.get("opportunity_id", ""))
        if not opp_id:
            fail("Every opportunity requires opportunity_id")
        product_categories = set()
        for task in opportunity.get("search_tasks", []):
            task_id = str(task.get("task_id", ""))
            if not re.fullmatch(r"[A-Za-z0-9_-]+", task_id) or task_id in seen:
                fail(f"Task IDs must be present and globally unique: {task_id!r}")
            seen.add(task_id)
            capability = task.get("capability")
            if capability not in ALLOWED:
                fail(f"Forbidden capability: {capability}")
            query = task.get("query")
            if not isinstance(query, str) or not query.strip():
                fail(f"Task {task_id} has an empty query")
            strategy_category = task.get("strategy_category")
            if capability == "1688-product-find.text_search":
                if strategy_category not in STRATEGY_CATEGORIES:
                    fail(f"Product task {task_id} requires a valid strategy_category")
                if not str(task.get("search_direction", "")).strip():
                    fail(f"Product task {task_id} requires search_direction")
                if not isinstance(task.get("search_round"), int) or task.get("search_round") < 1:
                    fail(f"Product task {task_id} requires a positive integer search_round")
                product_categories.add(strategy_category)
            elif strategy_category != "supplier_baseline":
                fail(f"Supplier task {task_id} must use strategy_category supplier_baseline")
            tasks.append((opportunity, task))
        missing_categories = STRATEGY_CATEGORIES - product_categories
        if missing_categories:
            fail(f"Opportunity {opp_id} is missing product search categories: {sorted(missing_categories)}")
    if not tasks:
        fail("No search tasks found")
    priority_order = {"high": 0, "medium": 1, "low": 2}
    return sorted(tasks, key=lambda pair: (priority_order.get(pair[0].get("priority"), 9), pair[0]["opportunity_id"], pair[1].get("priority", 999)))


def main():
    parser = argparse.ArgumentParser(description="Collect read-only 1688 sourcing evidence")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--product-limit", type=int, default=50, help="Products requested per product-search task (default: 50, max: 50)")
    args = parser.parse_args()
    if args.product_limit < 1 or args.product_limit > 50:
        fail("product-limit must be between 1 and 50")
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        fail(f"Refusing to use existing output directory: {output_dir}")
    inspect()

    source = load(args.input)
    tasks = validate_input(source)
    output_dir.mkdir(parents=True)
    (output_dir / "raw-results").mkdir()
    write_new(output_dir / "source.json", source)

    health,health_code=invoke(["doctor","--json"])
    product_ready=bool(health.get("product_skill",{}).get("available") and health.get("python",{}).get("available") and health.get("ak",{}).get("available"))
    supplier_ready=bool(health.get("supplier_skill",{}).get("available") and health.get("python",{}).get("available") and health.get("ak",{}).get("available"))
    auth={"product_find":{"configured":product_ready,"verified":False},"source_suppliers":{"configured":supplier_ready,"verified":False}}
    task_records = []

    for opportunity, task in tasks:
        capability = task["capability"]
        task_id = task["task_id"]
        query = task["query"]
        if capability == "1688-product-find.text_search":
            ready = product_ready
            cli_available = True
            command = ["products", "search", query, "--limit", str(args.product_limit), "--score-level", "high"]
        else:
            ready = supplier_ready
            cli_available = True
            command = ["suppliers", "search", query]

        if ready:
            result, exit_code = run_cli(command)
        else:
            message = "Authentication is not configured for this CLI branch" if cli_available else "Required runtime package is unavailable for this CLI branch"
            result, exit_code = ({"success": False, "markdown": message, "data": {}}, 1 if cli_available else 127)
        raw_name = f"{task_id}.json"
        write_new(output_dir / "raw-results" / raw_name, result)
        task_records.append({
            "opportunity_id": opportunity["opportunity_id"],
            "task_id": task_id,
            "capability": capability,
            "query": query,
            "priority": task.get("priority"),
            "strategy_category": task.get("strategy_category"),
            "query_origin": task.get("query_origin", "unknown"),
            "category_purpose": task.get("category_purpose", ""),
            "search_direction": task.get("search_direction", ""),
            "search_round": task.get("search_round", 1),
            "success": bool(result.get("success")) and exit_code == 0,
            "exit_code": exit_code,
            "raw_result": f"raw-results/{raw_name}",
            "message": str(result.get("markdown", "")).splitlines()[0][:300],
        })

    collection = {
        "schema_version": "2.0",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "source_file": "source.json",
        "source": source.get("source", {}),
        "authentication": auth,
        "task_count": len(task_records),
        "success_count": sum(1 for task in task_records if task["success"]),
        "failure_count": sum(1 for task in task_records if not task["success"]),
        "tasks": task_records,
    }
    write_new(output_dir / "collection.json", collection)
    print(json.dumps({"output_dir": str(output_dir), "tasks": len(task_records), "success": collection["success_count"], "failed": collection["failure_count"]}, ensure_ascii=False))

    if collection["failure_count"]:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
