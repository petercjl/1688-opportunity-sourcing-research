#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path


def fail(message):
    raise SystemExit(message)


def load(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def first_list(value, paths):
    for path in paths:
        cursor = value
        for key in path:
            cursor = cursor.get(key, {}) if isinstance(cursor, dict) else {}
        if isinstance(cursor, list):
            return cursor
    return []


def text_values(items):
    values = []
    for item in items or []:
        if isinstance(item, dict):
            value = item.get("value") or item.get("type")
        else:
            value = item
        if value not in (None, ""):
            values.append(str(value))
    return values


def normalize_product(row):
    return {
        "product_id": str(row.get("offer_id", row.get("product_id", ""))),
        "title": row.get("title", ""),
        "image_url": row.get("image_url", ""),
        "detail_url": row.get("url", row.get("detail_url", "")),
        "similarity_score": row.get("similarity_score"),
        "price": row.get("price"),
        "sku_id": str(row.get("sku_id", "")) if row.get("sku_id") is not None else "",
        "sku_title": row.get("sku_title", ""),
        "yx_index": row.get("yx_index"),
        "quantity_begin": row.get("moq", row.get("quantity_begin")),
        "unit": row.get("unit", ""),
        "supplier": row.get("supplier_name", row.get("supplier", "")),
        "sold_count": row.get("sold_count"),
        "stock_amount": row.get("stock_amount"),
        "promotion_tags": text_values(row.get("promotion_tags", [])),
        "service_infos": text_values(row.get("service_infos", [])),
        "selling_points": text_values(row.get("selling_points", [])),
    }


def normalize_supplier(row):
    return {
        "company_name": row.get("company_name", row.get("companyName", "")),
        "company_url": row.get("url", row.get("companyUrl", "")),
        "location": row.get("location", ""),
        "factory_level": row.get("factory_level", row.get("factoryLevel", "")),
        "factory_types": [str(v) for v in row.get("factory_types", row.get("factoryType", []))],
        "recommendation_tags": [str(v) for v in row.get("recommendation_tags", row.get("recTags", []))],
        "cooperation_modes": [str(v) for v in row.get("cooperation_modes", row.get("cooperationMode", []))],
        "services": [str(v) for v in row.get("services", [])],
        "satisfied_rate": row.get("satisfied_rate", row.get("satisfiedRate", "")),
        "monthly_orders": row.get("monthly_orders", row.get("monthlyOrders")),
        "support_proofing": row.get("supports_proofing", row.get("supportProofing")),
        "platform_score": row.get("provider_score", row.get("score")),
    }


def merge_provenance(existing, task):
    entry = {
        "task_id": task["task_id"],
        "query": task["query"],
        "capability": task["capability"],
        "strategy_category": task.get("strategy_category", ""),
        "query_origin": task.get("query_origin", "unknown"),
        "search_direction": task.get("search_direction", ""),
        "search_round": task.get("search_round", 1),
    }
    if entry not in existing["provenance"]:
        existing["provenance"].append(entry)


def main():
    parser = argparse.ArgumentParser(description="Normalize 1688 sourcing collection")
    parser.add_argument("--collection", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if os.path.exists(args.output):
        fail(f"Refusing to overwrite existing file: {args.output}")
    collection_path = Path(args.collection)
    root = collection_path.parent
    collection = load(collection_path)
    source = load(root / collection["source_file"])
    source_opportunities = {o["opportunity_id"]: o for o in source.get("opportunities", [])}
    grouped = {opp_id: {"products": {}, "suppliers": {}, "tasks": [], "raw_product_rows": 0, "raw_supplier_rows": 0, "retrieval_by_category": {}} for opp_id in source_opportunities}

    for task in collection.get("tasks", []):
        opp_id = task["opportunity_id"]
        if opp_id not in grouped:
            fail(f"Unknown opportunity in collection: {opp_id}")
        grouped[opp_id]["tasks"].append(task)
        envelope = load(root / task["raw_result"])
        if not task.get("success"):
            continue
        if task["capability"] == "1688-product-find.text_search":
            rows = first_list(envelope, [("products",), ("data", "data", "similar_products"), ("data", "similar_products"), ("similar_products",)])
            grouped[opp_id]["raw_product_rows"] += len(rows)
            category = task.get("strategy_category", "")
            grouped[opp_id]["retrieval_by_category"].setdefault(category, {"task_count": 0, "raw_rows": 0})
            grouped[opp_id]["retrieval_by_category"][category]["task_count"] += 1
            grouped[opp_id]["retrieval_by_category"][category]["raw_rows"] += len(rows)
            for row in rows:
                product = normalize_product(row)
                key = product["product_id"]
                if not key:
                    continue
                existing = grouped[opp_id]["products"].setdefault(key, {**product, "provenance": []})
                merge_provenance(existing, task)
        else:
            rows = first_list(envelope, [("suppliers",), ("data", "factories"), ("data", "data", "factories"), ("factories",)])
            grouped[opp_id]["raw_supplier_rows"] += len(rows)
            for row in rows:
                supplier = normalize_supplier(row)
                key = supplier["company_url"] or supplier["company_name"]
                if not key:
                    continue
                existing = grouped[opp_id]["suppliers"].setdefault(key, {**supplier, "provenance": []})
                merge_provenance(existing, task)

    opportunities = []
    for opp_id, original in source_opportunities.items():
        group = grouped[opp_id]
        opportunities.append({
            "opportunity_id": opp_id,
            "name": original.get("name", ""),
            "priority": original.get("priority", ""),
            "confidence": original.get("confidence", ""),
            "job_to_be_done": original.get("job_to_be_done", ""),
            "use_scenarios": original.get("use_scenarios", []),
            "target_audiences": original.get("target_audiences", []),
            "product_forms": original.get("product_forms", []),
            "required_attributes": original.get("required_attributes", []),
            "source_search_terms": original.get("source_search_terms", []),
            "upstream_risks": original.get("risks", []),
            "upstream_validation_plan": original.get("validation_plan", []),
            "required_strategy_categories": original.get("required_strategy_categories", []),
            "tasks": group["tasks"],
            "products": list(group["products"].values()),
            "suppliers": list(group["suppliers"].values()),
            "coverage": {
                "task_count": len(group["tasks"]),
                "success_count": sum(1 for task in group["tasks"] if task.get("success")),
                "failure_count": sum(1 for task in group["tasks"] if not task.get("success")),
                "product_count": len(group["products"]),
                "supplier_count": len(group["suppliers"]),
                "raw_product_rows": group["raw_product_rows"],
                "duplicate_product_rows": max(0, group["raw_product_rows"] - len(group["products"])),
                "raw_supplier_rows": group["raw_supplier_rows"],
                "retrieval_by_category": group["retrieval_by_category"],
            },
        })

    evidence = {
        "schema_version": "2.0",
        "source": source.get("source", {}),
        "collection_quality": {
            "task_count": collection.get("task_count", 0),
            "success_count": collection.get("success_count", 0),
            "failure_count": collection.get("failure_count", 0),
            "authentication": collection.get("authentication", {}),
        },
        "opportunities": opportunities,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "x", encoding="utf-8") as handle:
        json.dump(evidence, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"opportunities": len(opportunities), "products": sum(len(o["products"]) for o in opportunities), "suppliers": sum(len(o["suppliers"]) for o in opportunities)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
