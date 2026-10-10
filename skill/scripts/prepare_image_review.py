#!/usr/bin/env python3
import argparse
import html
import json
import os
from pathlib import Path
from urllib.parse import urlparse


ALLOWED_HOST_SUFFIXES = ("alicdn.com", "alibaba.com")


def fail(message):
    raise SystemExit(message)


def load(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def allowed_image_url(url):
    parsed = urlparse(str(url))
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and any(
        host == suffix or host.endswith("." + suffix)
        for suffix in ALLOWED_HOST_SUFFIXES
    )


def main():
    parser = argparse.ArgumentParser(
        description="Build a URL-based visual-review page without downloading product images"
    )
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--review", required=True)
    args = parser.parse_args()
    for path in (args.manifest, args.review):
        if os.path.exists(path):
            fail(f"Refusing to overwrite existing file: {path}")

    evidence = load(args.evidence)
    records = []
    products = {}
    for opportunity in evidence.get("opportunities", []):
        opportunity_id = opportunity["opportunity_id"]
        for product in opportunity.get("products", []):
            product_id = str(product.get("product_id", ""))
            image_url = str(product.get("image_url", ""))
            url_allowed = allowed_image_url(image_url)
            records.append(
                {
                    "opportunity_id": opportunity_id,
                    "product_id": product_id,
                    "image_url": image_url,
                    "url_allowed": url_allowed,
                    "error": "" if url_allowed else "unsupported image URL",
                }
            )
            products[(opportunity_id, product_id)] = product

    manifest = {
        "schema_version": "2.0",
        "mode": "remote_url_reference",
        "records": records,
        "allowed_count": sum(1 for record in records if record["url_allowed"]),
        "rejected_count": sum(1 for record in records if not record["url_allowed"]),
        "downloaded_file_count": 0,
    }
    Path(args.manifest).parent.mkdir(parents=True, exist_ok=True)
    Path(args.review).parent.mkdir(parents=True, exist_ok=True)
    with open(args.manifest, "x", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    cards = []
    for record in records:
        product = products[(record["opportunity_id"], record["product_id"])]
        if record["url_allowed"]:
            image = (
                f'<img src="{html.escape(record["image_url"], quote=True)}" '
                f'alt="{html.escape(str(product.get("title", "")), quote=True)}" '
                'loading="lazy" referrerpolicy="no-referrer">'
            )
        else:
            image = '<div class="missing">图片 URL 不可用</div>'
        categories = sorted(
            {
                provenance.get("strategy_category", "")
                for provenance in product.get("provenance", [])
                if provenance.get("strategy_category")
            }
        )
        detail_url = html.escape(str(product.get("detail_url", "")), quote=True)
        cards.append(
            f'<article>{image}<b>{html.escape(record["product_id"])}</b>'
            f'<p>{html.escape(str(product.get("title", "")))}</p>'
            f'<small>{html.escape(" / ".join(categories))}</small>'
            f'<p><a href="{detail_url}" target="_blank" rel="noopener noreferrer">查看商品</a></p>'
            "</article>"
        )
    review = (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>1688 URL 图片审查</title><style>'
        'body{font:14px sans-serif;margin:20px;background:#f4f5f7}'
        'main{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px}'
        'article{background:#fff;padding:10px;border-radius:10px;min-width:0}'
        'img,.missing{width:100%;aspect-ratio:1;object-fit:contain;background:#eee}'
        '.missing{display:grid;place-items:center}p{margin:6px 0;overflow-wrap:anywhere}'
        'small{color:#667085}a{color:#3159c8}</style></head><body><main>'
        + "".join(cards)
        + "</main></body></html>"
    )
    with open(args.review, "x", encoding="utf-8") as handle:
        handle.write(review)
    print(
        json.dumps(
            {
                "manifest": args.manifest,
                "review": args.review,
                "allowed": manifest["allowed_count"],
                "rejected": manifest["rejected_count"],
                "downloaded_files": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
