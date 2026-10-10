#!/usr/bin/env python3
import copy
import importlib.util
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "build_outputs.py"
CATEGORIES = [
    "market_proven",
    "novel_structure",
    "aesthetic",
    "scenario_specific",
    "premium_quality",
    "solution_bundle",
]


def load_module():
    spec = importlib.util.spec_from_file_location("build_outputs", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixtures():
    image_url = "https://cbu01.alicdn.com/example.jpg"
    tasks = []
    for category in CATEGORIES:
        for direction in ("family", "alternate"):
            tasks.append({
                "task_id": f"task-{category}-{direction}",
                "capability": "1688-product-find.text_search",
                "query": f"query-{category}-{direction}",
                "strategy_category": category,
                "search_direction": direction,
                "success": True,
            })
    evidence = {
        "schema_version": "2.0",
        "opportunities": [
            {
                "opportunity_id": "test-opportunity",
                "tasks": tasks,
                "products": [{"product_id": "product-1", "image_url": image_url}],
                "suppliers": [],
                "coverage": {"raw_product_rows": 1, "product_count": 1, "duplicate_product_rows": 0},
            }
        ],
    }
    images = {
        "schema_version": "2.0",
        "mode": "remote_url_reference",
        "downloaded_file_count": 0,
        "records": [
            {
                "opportunity_id": "test-opportunity",
                "product_id": "product-1",
                "image_url": image_url,
                "url_allowed": True,
                "error": "",
            }
        ],
    }
    findings = [
        {
            "category": category,
            "status": "found" if category == "market_proven" else "gap",
            "queries": [f"query-{category}-family", f"query-{category}-alternate"],
            "candidate_count": 1 if category == "market_proven" else 0,
            "shortfall_reason": "fixture intentionally contains only one product",
        }
        for category in CATEGORIES
    ]
    analysis = {
        "schema_version": "2.0",
        "opportunities": [
            {
                "opportunity_id": "test-opportunity",
                "status": "candidate_found",
                "confidence": "high",
                "category_findings": findings,
                "product_assessments": [
                    {
                        "product_id": "product-1",
                        "primary_category": "market_proven",
                        "decision": "shortlist",
                        "fit": "high",
                        "portfolio_role": "benchmark",
                        "category_rank": 1,
                        "visual_review": {
                            "reviewed": True,
                            "image_url": image_url,
                            "visible_cues": ["round"],
                            "confidence": "high",
                        },
                        "novelty_evidence": [],
                        "aesthetic_evidence": [],
                    }
                ],
                "supplier_assessments": [],
            }
        ],
    }
    return evidence, images, analysis


def expect_failure(module, evidence, images, analysis, expected):
    try:
        module.validate(evidence, images, analysis)
    except SystemExit as error:
        assert expected in str(error), error
    else:
        raise AssertionError(f"Expected validation failure containing: {expected}")


def main():
    module = load_module()
    evidence, images, analysis = fixtures()
    module.validate(evidence, images, analysis)

    wrong_url = copy.deepcopy(images)
    wrong_url["records"][0]["image_url"] = "https://cbu01.alicdn.com/wrong.jpg"
    expect_failure(module, evidence, wrong_url, analysis, "must equal the CLI-returned")

    forged_allowlist = copy.deepcopy(images)
    forged_allowlist["records"][0]["image_url"] = "https://example.com/example.jpg"
    evidence_with_external_url = copy.deepcopy(evidence)
    evidence_with_external_url["opportunities"][0]["products"][0]["image_url"] = "https://example.com/example.jpg"
    expect_failure(module, evidence_with_external_url, forged_allowlist, analysis, "allowlist decision mismatch")

    local_path = copy.deepcopy(images)
    local_path["records"][0]["relative_path"] = "product-images/product-1.jpg"
    expect_failure(module, evidence, local_path, analysis, "must not contain a local path")

    one_direction = copy.deepcopy(evidence)
    one_direction["opportunities"][0]["tasks"] = [
        task for task in one_direction["opportunities"][0]["tasks"]
        if task["strategy_category"] == "market_proven" or task["search_direction"] == "family"
    ]
    one_direction_findings = copy.deepcopy(analysis)
    for finding in one_direction_findings["opportunities"][0]["category_findings"]:
        if finding["category"] != "market_proven":
            finding["queries"] = [f"query-{finding['category']}-family"]
    expect_failure(module, one_direction, images, one_direction_findings, "requires at least two successful search directions")

    print("build output image validation: ok")


if __name__ == "__main__":
    main()
