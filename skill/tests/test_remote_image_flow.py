#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "prepare_image_review.py"


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        evidence = root / "evidence.json"
        manifest = root / "nested" / "image-references.json"
        review = root / "other-nested" / "visual-review.html"
        evidence.write_text(
            json.dumps(
                {
                    "schema_version": "2.0",
                    "opportunities": [
                        {
                            "opportunity_id": "test-opportunity",
                            "products": [
                                {
                                    "product_id": "allowed-product",
                                    "title": "允许的远程图片",
                                    "image_url": "https://cbu01.alicdn.com/example.jpg",
                                    "detail_url": "https://detail.1688.com/offer/1.html",
                                    "provenance": [{"strategy_category": "market_proven"}],
                                },
                                {
                                    "product_id": "rejected-product",
                                    "title": "拒绝的外部图片",
                                    "image_url": "https://example.com/example.jpg",
                                    "detail_url": "https://detail.1688.com/offer/2.html",
                                    "provenance": [{"strategy_category": "aesthetic"}],
                                },
                            ],
                        }
                    ],
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--evidence",
                str(evidence),
                "--manifest",
                str(manifest),
                "--review",
                str(review),
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        result = json.loads(completed.stdout)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        html = review.read_text(encoding="utf-8")

        assert result["downloaded_files"] == 0
        assert data["mode"] == "remote_url_reference"
        assert data["allowed_count"] == 1
        assert data["rejected_count"] == 1
        assert data["downloaded_file_count"] == 0
        assert data["records"][0]["image_url"] == "https://cbu01.alicdn.com/example.jpg"
        assert data["records"][0]["url_allowed"] is True
        assert data["records"][1]["url_allowed"] is False
        assert "https://cbu01.alicdn.com/example.jpg" in html
        assert "https://example.com/example.jpg" not in html
        assert "referrerpolicy=\"no-referrer\"" in html
        assert not any(path.is_dir() and "product-image" in path.name for path in root.rglob("*"))
        assert not any(
            field in record
            for record in data["records"]
            for field in ("relative_path", "local_path", "file_path")
        )

    print("remote image flow: ok")


if __name__ == "__main__":
    main()
