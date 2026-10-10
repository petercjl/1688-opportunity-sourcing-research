#!/usr/bin/env python3
import argparse
import json
import os
import re
from copy import deepcopy
from pathlib import Path


CATEGORIES = {
    "market_proven": "建立通货基准，验证成熟需求与供应",
    "novel_structure": "寻找结构或操作方式差异，服务内容传播与差异化",
    "aesthetic": "寻找造型、颜色、材质视觉或包装更突出的款式",
    "scenario_specific": "寻找针对具体场景、任务语言或人群的专用款",
    "premium_quality": "寻找材质、工艺、手感和可验证品质升级",
    "solution_bundle": "寻找覆盖多个任务步骤的合理套装",
}

REFERENCE_TOKENS = ("参考图", "同款", "同模具", "reference image", "same model", "same mold")


def fail(message):
    raise SystemExit(message)


def load(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def stable_slug(value):
    value = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return value or "opportunity"


def first_text(values, fallback):
    for value in values or []:
        if str(value).strip():
            return str(value).strip()
    return fallback


def contains_reference_lock(value):
    text = str(value).lower()
    return any(token in text for token in REFERENCE_TOKENS)


def first_breadth_text(values, fallback):
    for value in values or []:
        if str(value).strip() and not contains_reference_lock(value):
            return str(value).strip()
    return fallback


def derived_queries(opportunity):
    name = opportunity.get("name") or opportunity.get("opportunity_id")
    form = first_text(opportunity.get("product_forms"), name)
    family = str(opportunity.get("portfolio_product_family") or form).strip()
    scenario = first_text(opportunity.get("use_scenarios"), opportunity.get("job_to_be_done") or name)
    task_attribute = first_breadth_text(opportunity.get("required_attributes"), scenario)
    job = str(opportunity.get("job_to_be_done") or scenario).strip()
    if contains_reference_lock(job):
        job = scenario
    return {
        "market_proven": [
            ("mainstream_family", f"主流 热销 {family}"),
            ("factory_wholesale", f"{family} 工厂 批发"),
        ],
        "novel_structure": [
            ("structural_innovation", f"创新结构 多功能 {family}"),
            ("alternative_operation", f"{scenario} 创意 专用工具 新款"),
            ("adjacent_form", f"{job} 新结构 工具"),
        ],
        "aesthetic": [
            ("designed_form", f"高颜值 {family} 设计款"),
            ("style_system", f"{family} 风格化 配色 质感"),
            ("gifting_display", f"{scenario} 高颜值 工具 礼盒"),
        ],
        "scenario_specific": [
            ("attribute_scenario", f"{task_attribute} {family} {scenario} 专用工具"),
            ("scenario_task", f"{scenario} 专用 {family}"),
            ("professional_context", f"专业 高频 {scenario} 工具"),
        ],
        "premium_quality": [
            ("material_upgrade", f"高品质 加厚 材质升级 {family}"),
            ("professional_grade", f"专业级 商用 {family}"),
            ("workmanship_compliance", f"{family} 耐用 工艺 品质 认证"),
        ],
        "solution_bundle": [
            ("product_family_set", f"{family} 套装 组合"),
            ("scenario_kit", f"{scenario} 工具套装 全套"),
            ("multi_step_solution", f"{job} 一站式 组合工具"),
        ],
    }


def validate_source(data):
    if data.get("handoff_type") != "ai_dianjing_to_1688_product_selection":
        fail("Unsupported handoff_type")
    if data.get("execution_policy", {}).get("mode") != "read_only_research":
        fail("Input must authorize read_only_research")
    if not data.get("opportunities"):
        fail("No opportunities found")
    reference_source = data.get("source", {}).get("type") == "user_reference_images"
    for opportunity in data["opportunities"]:
        text = " ".join(str(opportunity.get(field, "")) for field in ("name", "job_to_be_done"))
        family = str(opportunity.get("portfolio_product_family", "")).strip()
        if (reference_source or contains_reference_lock(text)) and not family:
            fail("Reference-led opportunities require a broad portfolio_product_family")
        if family and contains_reference_lock(family):
            fail("portfolio_product_family must not contain reference or same-model locking language")


def main():
    parser = argparse.ArgumentParser(description="Build category-first 1688 search plan")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if os.path.exists(args.output):
        fail(f"Refusing to overwrite existing file: {args.output}")
    data = load(args.input)
    validate_source(data)
    plan = deepcopy(data)
    plan["schema_version"] = "2.0"
    plan["search_strategy"] = {
        "mode": "category_first_multi_direction",
        "categories": [{"category": key, "purpose": value} for key, value in CATEGORIES.items()],
        "query_policy": "Preserve upstream queries exactly; execute multiple transparent directions per category before accepting a shortfall or gap.",
    }
    seen = set()
    for opportunity in plan["opportunities"]:
        opp_slug = stable_slug(opportunity.get("opportunity_id"))
        original = opportunity.get("search_tasks", [])
        product_tasks = [task for task in original if task.get("capability") == "1688-product-find.text_search"]
        supplier_tasks = [task for task in original if task.get("capability") == "1688-source-suppliers"]
        tasks = []
        if product_tasks:
            for index, task in enumerate(product_tasks, 1):
                task = deepcopy(task)
                task["strategy_category"] = "market_proven"
                task["query_origin"] = "upstream_exact"
                task["category_purpose"] = CATEGORIES["market_proven"]
                task["search_direction"] = "upstream_exact_baseline"
                task["search_round"] = 1
                task["priority"] = index
                tasks.append(task)
        else:
            tasks.append({
                "task_id": f"{opp_slug}-market-proven",
                "capability": "1688-product-find.text_search",
                "query": opportunity.get("name", opportunity.get("opportunity_id")),
                "intent": "find_market_proven",
                "priority": 1,
                "strategy_category": "market_proven",
                "query_origin": "derived_category_query",
                "category_purpose": CATEGORIES["market_proven"],
                "search_direction": "derived_baseline",
                "search_round": 1,
            })
        priority = len(tasks) + 1
        for category, directions in derived_queries(opportunity).items():
            for index, (direction, query) in enumerate(directions, 1):
                tasks.append({
                    "task_id": f"{opp_slug}-{category.replace('_', '-')}-{index}",
                    "capability": "1688-product-find.text_search",
                    "query": query,
                    "intent": f"find_{category}",
                    "priority": priority,
                    "strategy_category": category,
                    "query_origin": "derived_category_query",
                    "category_purpose": CATEGORIES[category],
                    "search_direction": direction,
                    "search_round": 1,
                    "source_terms": opportunity.get("source_search_terms", []),
                })
                priority += 1
        for task in supplier_tasks:
            task = deepcopy(task)
            task["strategy_category"] = "supplier_baseline"
            task["query_origin"] = "upstream_exact"
            task["category_purpose"] = "验证基础供应商与产业带信号"
            task["search_direction"] = "supplier_baseline"
            task["search_round"] = 1
            task["priority"] = priority
            tasks.append(task)
            priority += 1
        for task in tasks:
            task_id = task.get("task_id")
            if not task_id or task_id in seen:
                fail(f"Task IDs must be globally unique: {task_id!r}")
            seen.add(task_id)
        opportunity["search_tasks"] = tasks
        opportunity["required_strategy_categories"] = list(CATEGORIES)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "x", encoding="utf-8") as handle:
        json.dump(plan, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"output": args.output, "opportunities": len(plan["opportunities"]), "tasks": sum(len(o["search_tasks"]) for o in plan["opportunities"]), "categories": list(CATEGORIES)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
