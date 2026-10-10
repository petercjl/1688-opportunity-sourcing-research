---
name: 1688-opportunity-sourcing-research
description: Research products and suppliers on 1688 with category-first sourcing across market-proven, novel, aesthetic, scenario, premium, and bundle strategies, using installed 1688 CLI evidence, URL-based image review, a clickable HTML portfolio report, and a traceable candidate JSON. Use for six-category sourcing portfolios from a compatible product-opportunities.json handoff, or when the user explicitly requests this application.
---

# 1688分类机会选品研究

Turn validated demand directions into a broad six-category product portfolio. Keep deterministic CLI acquisition, Agent classification and visual judgment, and deterministic output validation separate.

## Portfolio breadth iron law

This Skill is a portfolio-sourcing workflow, not a single-item exact-match workflow. A reference product, image, or upstream baseline anchors the demand direction but must never collapse all six categories into the same model.

- Always provide meaningful choice across market-proven, novel structure, aesthetic, scenario-specific, premium-quality, and solution-bundle strategies when relevant 1688 supply exists.
- Never declare a category `gap`, or accept fewer than four retained products, after only one narrow query direction.
- When a category returns empty, irrelevant, homogeneous, or exact-match-dominated results, change the search direction automatically within the authorized read-only research scope. Do not wait for user approval merely to run transparent derived queries.
- Preserve every executed query and direction in the plan and evidence. Broaden product form, structure, style language, scenario/job language, material/quality language, or bundle composition rather than repeatedly adding more exact-match attributes.
- A final gap is allowed only after multiple distinct directions were executed successfully and the report records why those directions still failed. Never use the reference product's similarity as a reason to skip the other five strategy lanes.

Use this application for six-category portfolio selection. The executable main line requires a compatible `product-opportunities.json`; when missing, resolve the input contract with the caller. Keyword or reference-image sourcing belongs to the independently published `1688-product-sourcing` application.

## Package lifecycle

Canonical source: `1688-opportunity-sourcing-research skill source --json`. Install/update with `skill install|update --agent codex|sealseek|workbuddy`; inspect `skill status --json`, `version`, `capabilities`, and `doctor --json`. `update check|install` manages stable npm releases. The bundled scripts use Python 3 standard library discovered by the Node entry; always invoke through `script` to preserve cross-platform UTF-8 and dependency discovery.

## Required capabilities

- Execute local commands, inspect installed Agent Skill packages, create files, and visually inspect an HTML review page that references CLI-returned image URLs.
- Resolve the installed `@petercjl/1688cli >=0.4 <1` dependency and its current canonical `1688cli` Skill.
- Use Python 3 standard library for bundled scripts.
- Access 1688 business data only through the atomic 1688cli capability package.

If the atomic dependency is absent, stop its task branch with a compatibility error. Never replace business-data acquisition with browser scraping, web search, raw HTTP, or guessed commands.

## Main line

### 1. Validate input and establish a new output directory

Require one UTF-8 `product-opportunities.json` with:

- `handoff_type: ai_dianjing_to_1688_product_selection`
- `execution_policy.mode: read_only_research`
- only `1688-product-find.text_search` and `1688-source-suppliers` tasks
- stable, unique task IDs and non-empty exact queries
- for reference-led or exact-match inputs, a broad `portfolio_product_family` that names the category to diversify; keep exact visual invariants in `required_attributes`, not in this breadth field

Select a new, nonexistent path such as `outputs/1688-sourcing-<campaign-id>-<date-time>/`. Never overwrite an existing file or directory.

### 2. Build the category-first search plan

Read [references/product-strategy-taxonomy.md](references/product-strategy-taxonomy.md) and [references/search-expansion-policy.md](references/search-expansion-policy.md) completely. Then run:

```bash
1688-opportunity-sourcing-research script build_search_plan.py \
  --input "<product-opportunities.json>" \
  --output "<new-parent>/search-plan.json"
```

The plan must contain multiple distinct product-search directions for each category:

1. `market_proven` — 市场验证款；
2. `novel_structure` — 新颖结构款；
3. `aesthetic` — 高颜值款；
4. `scenario_specific` — 场景专用款；
5. `premium_quality` — 品质升级款；
6. `solution_bundle` — 组合解决方案。

Preserve every upstream product query exactly as the `market_proven` baseline. Add at least two transparent derived directions for every category, including the market baseline lane. Every derived query must be explicit in `search-plan.json`, tagged `query_origin: derived_category_query`, carry `search_direction`, and remain traceable to the opportunity. Supplier tasks remain `supplier_baseline` tasks.

Do not over-lock derived queries to the reference item's exact shape, color, size, or component arrangement. Use the reference to define the demand and product family; use category-specific directions to discover different structures, looks, scenarios, quality levels, and bundles.

### 3. Resolve and inspect the current 1688 runtime

Run `1688-opportunity-sourcing-research script discover_runtime.py --require-all`. Read the complete current `SKILL.md` at its emitted `skill_source`; resolve resources relative to that directory. The dependency contract requires `1688-products@1` and `1688-suppliers@1`, inspected from the live CLI. Input is the exact planned query and explicit limit; output is normalized products/suppliers JSON with source provenance. Missing or incompatible dependencies return `DEPENDENCY_UNAVAILABLE` / `CONTRACT_UNSUPPORTED`. After loading the dependency, return here and continue Step 4. See [runtime contract](references/runtime-adapter.md).

### 4. Acquire platform data through the CLI packages

Run the collector against the category search plan:

```bash
1688-opportunity-sourcing-research script collect_results.py \
  --input "<search-plan.json>" \
  --output-dir "<new-output-dir>" \
  --product-limit 50
```

The collector invokes the dependency through its discovered Node entry. It:

- requests 50 products per product-search task by default so the Agent classifies a broad pool rather than a small top slice;
- requires all six product strategy categories per opportunity;
- records product and supplier branch readiness from atomic doctor; remote validity is determined by each query;
- passes every planned query exactly as recorded;
- preserves category, task, query, and raw-envelope provenance;
- records failed branches without fabricating substitutes;
- never calls inquiry, purchase, order, publish, or distribution capabilities.

The boundary is strict: CLI packages acquire platform facts; the Agent determines categories, suitability, visual character, and recommendations.

### 5. Prepare evidence and URL-based image review

Run:

```bash
1688-opportunity-sourcing-research script prepare_evidence.py \
  --collection "<output-dir>/collection.json" \
  --output "<output-dir>/evidence.json"

1688-opportunity-sourcing-research script prepare_image_review.py \
  --evidence "<output-dir>/evidence.json" \
  --manifest "<output-dir>/image-references.json" \
  --review "<output-dir>/visual-review.html"
```

The evidence step deduplicates products and suppliers while retaining every task/query/category provenance. The image-review step records only the exact HTTPS image URLs already returned by the CLI and builds an HTML review page that references those URLs directly. It must not download, copy, cache, or create a product-image directory, and must never search, query, scrape, or obtain other business data directly.

Open `<output-dir>/visual-review.html` through the Agent's link application or browser and inspect the rendered remote images. Do not infer novelty, structure, aesthetics, color language, material appearance, or presentation quality from a title alone. If an image URL does not render, treat visual evidence as unavailable.

### 6. Analyze by category, then assemble the portfolio

Read [references/analysis-methodology.md](references/analysis-methodology.md) and [references/output-contracts.md](references/output-contracts.md) completely, then analyze `evidence.json` with `image-references.json`.

For each opportunity:

1. Classify every product exactly once into one primary category, or `out_of_scope` when irrelevant.
2. Classify it as `shortlist`, `observe`, or `exclude` and assign one portfolio role.
3. Rank products only against products in the same primary category. Never use one universal score across categories.
4. Use sales, stock, MOQ, price, and supply maturity strongly for `market_proven`, but only as secondary signals for `novel_structure` and `aesthetic`.
5. For every retained novel or aesthetic candidate, cite the exact CLI-returned image URL, visible cues, evidence, and confidence. Novelty means distinct within the retrieved sample unless broader market evidence exists.
6. For every defensible `found` category, retain a useful comparison set: target 4–8 non-excluded products, normally 1–3 `shortlist` plus the remaining `observe`.
7. Before accepting fewer than four retained products or a `gap`, audit the executed directions. If fewer than two distinct successful directions exist, or the results remain dominated by the reference model, return to Step 2, create a new non-overwriting search plan with additional directions from [references/search-expansion-policy.md](references/search-expansion-policy.md), rerun collection in a new output directory, and then return to Step 5. This expansion is mandatory and does not require new user approval.
8. Produce exactly one `found` or `gap` finding for all six categories only after the breadth audit. Never admit irrelevant or unsupported products merely to reach the target, but never use a single narrow query as evidence of a real gap.
9. Classify every supplier exactly once and connect it only to supported categories.
10. Build a portfolio that explains the role of traffic/benchmark, content, brand, conversion, profit, and AOV candidates without letting the exact-match baseline monopolize all categories.

Write `<output-dir>/analysis.json` using schema `2.0`. Treat platform price, stock, sales, ratings, services, factory labels, materials, and certifications as claims pending manual verification. Never invent contacts, factory capacity, certifications, margins, market size, or product performance.

### 7. Build the HTML and candidate handoff

Run:

```bash
1688-opportunity-sourcing-research script build_outputs.py \
  --evidence "<output-dir>/evidence.json" \
  --images "<output-dir>/image-references.json" \
  --analysis "<output-dir>/analysis.json" \
  --template "<skill-root>/assets/report-template.html" \
  --html "<output-dir>/1688-sourcing-report.html" \
  --candidates "<output-dir>/sourcing-candidates.json"
```

The HTML must present a classification matrix before individual products, display each category separately, show category-specific evidence and gaps, reference only reviewed CLI-returned remote image URLs, and retain supplier and raw-query evidence. The candidate JSON is a read-only handoff grouped by category, retaining original opportunity, exact queries, product identity, source links, Agent decisions, image evidence, supplier support, portfolio role, and unresolved checks.

Deliver the HTML report as a clickable link in the final response using the current Agent application's supported link syntax. Do not inline a large raw HTML payload, and do not create a separate image-download folder for presentation.

The report must also show a `召回与筛选漏斗`: raw product rows, deduplicated products, excluded products, observed products, and shortlisted products. Never present the retained set as if it were the complete CLI recall.

### 8. QA and handoff

Verify:

- every upstream opportunity and all six categories appear exactly once;
- every returned product and supplier is classified exactly once;
- category queries equal planned/executed queries exactly;
- category counts, found/gap states, and within-category ranks are consistent;
- every found category retains 4–8 products, or explicitly records why the defensible pool is smaller;
- every gap or sub-four category has at least two distinct successfully executed search directions; a one-direction gap is invalid;
- category queries demonstrate real directional change rather than repeated exact-match attribute stacking;
- the reference model does not monopolize all six categories when different product forms are present in the retrieved evidence;
- the recall funnel reconciles raw rows, deduplicated products, excludes, observations, and shortlists;
- every retained novel/aesthetic item has an allowlisted CLI-returned image URL that rendered during review and has actual visual-review notes;
- ordinary high-sales items do not automatically occupy novelty or aesthetic categories;
- raw envelopes contain no credential fields and no forbidden capability ran;
- HTML and JSON parse, remote images render, links come from CLI evidence, and failed branches remain visible;
- no copied product image files or product-image directory exist in the output;
- HTML has no JavaScript/page errors at desktop and mobile widths.

Return clickable links for the HTML report and image review page, plus paths or links for the candidate JSON and search plan. Summarize the strongest candidate in each non-gap category, the clearest supply signal, the largest evidence gap, and the next manual validation step.

## Branches and return rules

### Product and supplier branch readiness differs

Continue successful read-only branches and mark unavailable branches `blocked`. Never copy or print credential values. Return to Main line Step 5.

### Empty, irrelevant, or homogeneous results

Do not stop at the first empty, irrelevant, homogeneous, or exact-match-dominated result set. Exclude false positives, identify why the direction failed, and automatically add at least two materially different derived directions using [references/search-expansion-policy.md](references/search-expansion-policy.md). Preserve the original query, label every added direction, rerun the expanded plan in a new output directory, and return to Main line Step 5.

Only report a category `gap` after multiple distinct directions execute successfully and still yield no defensible candidates. Record the attempted directions and their failure modes. Do not ask for approval merely to perform this in-scope read-only expansion.

If a scenario phrase is also a finished-product noun, keep a required task attribute and explicit `专用工具` wording in the derived scenario query. Do not accept finished goods as tool candidates merely because they match the scenario phrase.

### Image unavailable or visually ambiguous

Do not download the image as a fallback and do not retain the item as a novel/aesthetic candidate. Assign it to an evidence-supported category, set it to `observe`/`exclude`, or report a category gap. Record the missing evidence and return to Main line Step 6.

### Rate limit or service failure

Preserve the real error. Do not auto-retry beyond current runtime policy and do not use browser/web fallbacks. Return a partial report if other branches succeeded.

### Duplicate offers or factories

Deduplicate deterministically while retaining all source task/query/category provenance, then return to Main line Step 6.

### Missing economics

Do not infer profit from purchase price alone. Require retail price, logistics, packaging, platform fees, defect rate, returns, and advertising cost before a launch decision.

### Browser policy blocks direct local-file navigation

Serve only the completed output directory through a temporary loopback-only static server bound to `127.0.0.1`, run desktop/mobile checks, then stop it. The report may load only exact CLI-returned allowlisted product image URLs. This server is for local artifact QA only and must not proxy, fetch, or scrape business data. If blocked, record visual QA as environment-blocked and retain JavaScript and structure checks rather than claiming a visual pass.

## Evolution rule

When runtime schemas, category logic, or product-development needs change, update the relevant script, contract, taxonomy, or runtime adapter; rerun format, portability, script, visual, and clean-context tests. Fold recurring exceptions into the main line or a named branch instead of leaving a manual workaround.
