#!/usr/bin/env python3
import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


CATEGORIES = ["market_proven", "novel_structure", "aesthetic", "scenario_specific", "premium_quality", "solution_bundle"]
PRIMARY_CATEGORIES = set(CATEGORIES) | {"out_of_scope"}
OPPORTUNITY_STATUS = {"candidate_found", "needs_refinement", "supply_gap", "blocked"}
CONFIDENCE = {"low", "medium", "high"}
PRODUCT_DECISION = {"shortlist", "observe", "exclude"}
SUPPLIER_DECISION = {"priority", "observe", "exclude"}
PORTFOLIO_ROLE = {"traffic", "benchmark", "content", "brand", "conversion", "profit", "aov", "none"}
ALLOWED_IMAGE_HOST_SUFFIXES = ("alicdn.com", "alibaba.com")


def fail(message):
    raise SystemExit(message)


def load(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def require_list(value, label):
    if not isinstance(value, list):
        fail(f"{label} must be an array")
    return value


def allowed_image_url(url):
    parsed = urlparse(str(url))
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and any(
        host == suffix or host.endswith("." + suffix)
        for suffix in ALLOWED_IMAGE_HOST_SUFFIXES
    )


def validate_template(template):
    if "__REPORT_DATA__" not in template:
        fail("Template is missing __REPORT_DATA__")
    for phrase in ("召回与筛选漏斗", "分类选品矩阵", "市场验证款", "新颖结构款", "高颜值款", "供应链信号", "原始检索证据"):
        if phrase not in template:
            fail(f"Template is missing required section: {phrase}")
    if re.search(r"<(?:script|link)[^>]+(?:src|href)=[\"'](?:https?:)?//", template, re.I):
        fail("Template must not load external scripts or stylesheets")


def validate(evidence, images, analysis):
    if analysis.get("schema_version") != "2.0":
        fail("analysis schema_version must be 2.0")
    if images.get("schema_version") != "2.0" or images.get("mode") != "remote_url_reference":
        fail("images must be a schema 2.0 remote_url_reference manifest")
    if images.get("downloaded_file_count") != 0:
        fail("Remote image-reference manifest must not contain downloaded files")
    evidence_opps = {o["opportunity_id"]: o for o in evidence.get("opportunities", [])}
    expected_images = {
        (opportunity["opportunity_id"], str(product["product_id"])): str(product.get("image_url", ""))
        for opportunity in evidence.get("opportunities", [])
        for product in opportunity.get("products", [])
    }
    records = require_list(images.get("records"), "images.records")
    image_keys = [(record.get("opportunity_id"), str(record.get("product_id", ""))) for record in records]
    if len(image_keys) != len(set(image_keys)) or set(image_keys) != set(expected_images):
        fail("Every evidence product must have exactly one image-reference record")
    image_records = dict(zip(image_keys, records))
    for key, record in image_records.items():
        image_url = str(record.get("image_url", ""))
        if image_url != expected_images[key]:
            fail(f"Image reference must equal the CLI-returned product image URL: {key[1]}")
        if bool(record.get("url_allowed")) != allowed_image_url(image_url):
            fail(f"Image URL allowlist decision mismatch: {key[1]}")
        if any(field in record for field in ("relative_path", "local_path", "file_path")):
            fail(f"Remote image-reference record must not contain a local path: {key[1]}")
    analyzed = require_list(analysis.get("opportunities"), "analysis.opportunities")
    ids = [o.get("opportunity_id") for o in analyzed]
    if len(ids) != len(set(ids)) or set(ids) != set(evidence_opps):
        fail("Every evidence opportunity must appear exactly once")

    enriched = []
    for item in analyzed:
        opp_id = item["opportunity_id"]
        source = evidence_opps[opp_id]
        if item.get("status") not in OPPORTUNITY_STATUS or item.get("confidence") not in CONFIDENCE:
            fail(f"Invalid status/confidence: {opp_id}")
        executed_queries = {}
        successful_directions = {}
        for task in source.get("tasks", []):
            category = task.get("strategy_category")
            if category in CATEGORIES and task.get("capability") == "1688-product-find.text_search":
                executed_queries.setdefault(category, set()).add(task.get("query"))
                if task.get("success"):
                    successful_directions.setdefault(category, set()).add(task.get("search_direction") or task.get("query"))
        findings = require_list(item.get("category_findings"), f"{opp_id}.category_findings")
        finding_categories = [f.get("category") for f in findings]
        if len(finding_categories) != len(set(finding_categories)) or set(finding_categories) != set(CATEGORIES):
            fail(f"Every strategy category must have exactly one finding in {opp_id}")
        findings = sorted(findings, key=lambda finding: CATEGORIES.index(finding["category"]))

        products = {p["product_id"]: p for p in source.get("products", [])}
        coverage = source.get("coverage", {})
        raw_rows = coverage.get("raw_product_rows", len(products))
        if not isinstance(raw_rows, int) or raw_rows < len(products):
            fail(f"raw_product_rows must be at least the deduplicated product count: {opp_id}")
        if coverage.get("duplicate_product_rows", raw_rows - len(products)) != raw_rows - len(products):
            fail(f"duplicate_product_rows mismatch: {opp_id}")
        assessments = require_list(item.get("product_assessments"), f"{opp_id}.product_assessments")
        assessed_ids = [str(p.get("product_id", "")) for p in assessments]
        if len(assessed_ids) != len(set(assessed_ids)) or set(assessed_ids) != set(products):
            fail(f"Every product in {opp_id} must be classified exactly once")
        product_views = []
        counts = {category: 0 for category in CATEGORIES}
        ranks = {category: [] for category in CATEGORIES}
        for assessment in assessments:
            product_id = str(assessment["product_id"])
            category = assessment.get("primary_category")
            decision = assessment.get("decision")
            if category not in PRIMARY_CATEGORIES or decision not in PRODUCT_DECISION or assessment.get("fit") not in CONFIDENCE:
                fail(f"Invalid product classification: {product_id}")
            if assessment.get("portfolio_role") not in PORTFOLIO_ROLE:
                fail(f"Invalid portfolio role: {product_id}")
            image_record = image_records.get((opp_id, product_id), {"url_allowed": False, "image_url": "", "error": "missing manifest record"})
            visual = assessment.get("visual_review", {})
            if visual.get("image_url", "") not in ("", image_record.get("image_url", "")):
                fail(f"Unknown visual image URL for {product_id}")
            if category in {"novel_structure", "aesthetic"} and decision != "exclude":
                if not image_record.get("url_allowed") or not visual.get("reviewed") or not visual.get("visible_cues"):
                    fail(f"Novel/aesthetic candidate requires reviewed URL visual evidence: {product_id}")
                if visual.get("image_url") != image_record.get("image_url"):
                    fail(f"Novel/aesthetic candidate must cite its CLI-returned image URL: {product_id}")
                if visual.get("confidence") not in CONFIDENCE or not visual.get("sample_relative_distinctiveness"):
                    fail(f"Novel/aesthetic candidate requires visual confidence and sample-relative distinctiveness: {product_id}")
                field = "novelty_evidence" if category == "novel_structure" else "aesthetic_evidence"
                if not assessment.get(field):
                    fail(f"Missing {field} for {product_id}")
            if decision != "exclude" and category in CATEGORIES:
                counts[category] += 1
                rank = assessment.get("category_rank")
                if not isinstance(rank, int) or rank < 1:
                    fail(f"Non-excluded product requires a positive category_rank: {product_id}")
                ranks[category].append(rank)
            product_views.append({**products[product_id], "image_record": image_record, "assessment": assessment})
        for category, values in ranks.items():
            if len(values) != len(set(values)):
                fail(f"Duplicate category ranks in {opp_id}.{category}")

        finding_views = []
        for finding in findings:
            category = finding["category"]
            if finding.get("status") not in {"found", "gap"}:
                fail(f"Invalid category status: {opp_id}.{category}")
            if finding.get("candidate_count") != counts[category]:
                fail(f"candidate_count mismatch: {opp_id}.{category}")
            if counts[category] > 8:
                fail(f"Found category exceeds the 8-product comparison limit: {opp_id}.{category}")
            if counts[category] < 4 and not str(finding.get("shortfall_reason", "")).strip():
                fail(f"Category below the 4-product target requires shortfall_reason: {opp_id}.{category}")
            if counts[category] < 4 and len(successful_directions.get(category, set())) < 2:
                fail(f"Category below the 4-product target requires at least two successful search directions: {opp_id}.{category}")
            queries = require_list(finding.get("queries"), f"{opp_id}.{category}.queries")
            if set(queries) != executed_queries.get(category, set()):
                fail(f"Category queries must equal exact executed queries: {opp_id}.{category}")
            if (counts[category] > 0) != (finding.get("status") == "found"):
                fail(f"Category found/gap status mismatch: {opp_id}.{category}")
            finding_views.append({**finding, "products": sorted([p for p in product_views if p["assessment"]["primary_category"] == category and p["assessment"]["decision"] != "exclude"], key=lambda p: p["assessment"]["category_rank"])})

        suppliers = {(s.get("company_url") or s.get("company_name")): s for s in source.get("suppliers", [])}
        supplier_assessments = require_list(item.get("supplier_assessments"), f"{opp_id}.supplier_assessments")
        supplier_ids = [s.get("company_url") for s in supplier_assessments]
        if len(supplier_ids) != len(set(supplier_ids)) or set(supplier_ids) != set(suppliers):
            fail(f"Every supplier in {opp_id} must be classified exactly once by company_url")
        supplier_views = []
        for assessment in supplier_assessments:
            key = assessment["company_url"]
            if assessment.get("decision") not in SUPPLIER_DECISION:
                fail(f"Invalid supplier decision: {key}")
            supported = require_list(assessment.get("supported_categories"), f"{key}.supported_categories")
            if not set(supported).issubset(CATEGORIES):
                fail(f"Unknown supplier category: {key}")
            supplier_views.append({**suppliers[key], "assessment": assessment})
        if source.get("coverage", {}).get("failure_count", 0) and item.get("status") == "candidate_found" and item.get("confidence") == "high":
            fail(f"{opp_id} cannot claim high confidence with failed branches")
        enriched.append({**source, "analysis": item, "product_views": product_views, "category_views": finding_views, "supplier_views": supplier_views})
    return enriched


def main():
    parser = argparse.ArgumentParser(description="Build category-first 1688 sourcing outputs")
    for flag in ("evidence", "images", "analysis", "template", "html", "candidates"):
        parser.add_argument(f"--{flag}", required=True)
    args = parser.parse_args()
    for path in (args.html, args.candidates):
        if os.path.exists(path):
            fail(f"Refusing to overwrite existing file: {path}")
    evidence, images, analysis = load(args.evidence), load(args.images), load(args.analysis)
    opportunities = validate(evidence, images, analysis)
    with open(args.template, "r", encoding="utf-8") as handle:
        template = handle.read()
    validate_template(template)
    report = {"title": analysis.get("report_title", "1688分类选品与供应链研究"), "executive_summary": analysis.get("executive_summary", []), "overall_recommendation": analysis.get("overall_recommendation", ""), "source": evidence.get("source", {}), "collection_quality": evidence.get("collection_quality", {}), "category_order": CATEGORIES, "opportunities": opportunities}
    html_text = template.replace("__REPORT_DATA__", json.dumps(report, ensure_ascii=False).replace("</", "<\\/"))

    handoff_opps = []
    for opp in opportunities:
        a = opp["analysis"]
        categories = []
        for view in opp["category_views"]:
            categories.append({"category": view["category"], "purpose": view.get("purpose", ""), "status": view["status"], "summary": view.get("summary", ""), "queries": view.get("queries", []), "shortlisted_products": [p for p in view["products"] if p["assessment"]["decision"] == "shortlist"], "observed_products": [p for p in view["products"] if p["assessment"]["decision"] == "observe"]})
        handoff_opps.append({"opportunity_id": opp["opportunity_id"], "name": opp.get("name", ""), "status": a["status"], "confidence": a["confidence"], "conclusion": a.get("conclusion", ""), "categories": categories, "priority_suppliers": [s for s in opp["supplier_views"] if s["assessment"]["decision"] == "priority"], "portfolio_summary": a.get("portfolio_summary", []), "unresolved_validation": a.get("risks", []) + a.get("next_validation_steps", []), "task_coverage": opp.get("coverage", {})})
    candidates = {"schema_version": "2.0", "handoff_type": "1688_category_sourcing_candidates", "generated_at": datetime.now(timezone.utc).isoformat(), "source": evidence.get("source", {}), "research_policy": {"mode": "read_only", "ranking_rule": "within_category_only", "shortlist_meaning": "advance_to_manual_verification", "not_authorized": ["inquiry", "purchase", "order", "publish", "distribution"]}, "opportunities": handoff_opps}
    Path(args.html).parent.mkdir(parents=True, exist_ok=True)
    with open(args.candidates, "x", encoding="utf-8") as handle:
        json.dump(candidates, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with open(args.html, "x", encoding="utf-8") as handle:
        handle.write(html_text)
    print(json.dumps({"html": args.html, "candidates": args.candidates, "opportunities": len(opportunities), "categories": len(opportunities) * len(CATEGORIES)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
