# Analysis methodology

Read [product-strategy-taxonomy.md](product-strategy-taxonomy.md) first.

## Main principle

Classify strategy before search, search each category through multiple directions, evaluate within categories, then assemble a portfolio. Never use one universal ranking across mainstream, novel, aesthetic, scenario, premium, and bundle products. A reference product anchors demand but does not limit the portfolio to exact matches.

## Unit of analysis

> demand evidence × job to be done × use scenario × strategy category × product form × supply feasibility

The 1688 result tests supply availability and form diversity. It does not prove downstream demand, margin, quality, compliance, or market-wide novelty.

## Evidence layers

1. **Demand evidence**: source demands, audiences, scenarios, search language, and upstream validation plan.
2. **Query evidence**: exact query, origin (`upstream_exact` or `derived_category_query`), and intended category.
3. **Listing evidence**: title, SKU, image, price, MOQ, sales, stock, services, and supplier fields.
4. **Visual evidence**: visible structure, shape, color, material appearance, styling, and packaging from the CLI-returned main image rendered by URL in the review page.
5. **Validation gaps**: detail-page, documents, samples, economics, compliance, and real supplier capability.

## Product classification

Classify every product exactly once into one of the six strategy categories or `out_of_scope`. Query provenance is a lead, not the final category: a mainstream item returned by an aesthetic query remains `market_proven` if the image offers no aesthetic distinction.

Also assign:

- decision: `shortlist`, `observe`, or `exclude`;
- fit: `low`, `medium`, or `high`;
- portfolio role: `traffic`, `benchmark`, `content`, `brand`, `conversion`, `profit`, or `aov`;
- category rank for non-excluded products;
- secondary tags describing visible or functional traits.

## Visual review

Open `visual-review.html` and inspect source images. For any non-excluded `novel_structure` or `aesthetic` product, require:

- an allowlisted CLI-returned image URL that rendered during review;
- `reviewed: true`;
- visible evidence, not title-only inference;
- a sample-relative distinctiveness explanation;
- confidence and unresolved ambiguity.

Do not call a product novel across the whole market without external market evidence. Do not infer high aesthetics from sales or price.

Do not download, copy, or cache product images into the output. If a remote URL does not render, record the missing visual evidence and do not retain the item as a novel/aesthetic candidate.

## Category findings

Write exactly one finding for each required category, including its portfolio purpose, all queries and directions used, candidate count, status (`found` or `gap`), class-specific assessment, and next test. A gap is valid only after at least two materially distinct directions executed successfully. One narrow or exact-match-dominated query is not evidence of a gap.

Use a default comparison width of 4–8 retained products per `found` category. Prefer 1–3 `shortlist` items for immediate verification and use `observe` for credible alternates that preserve price, form, material, supplier, or scenario diversity. Deduplicate near-identical listings and avoid filling all slots with the same product form or supplier when defensible alternatives exist. If only 1–3 products survive, first change search direction and collect again; only after the multi-direction breadth audit may `shortfall_reason` explain the remaining evidence limit. A `gap` has zero retained products and must record why every executed direction failed.

## Supplier interpretation

Assess supplier records independently of product popularity. Use returned company, location, collaboration modes, services, proofing, factory labels, monthly orders, and satisfaction signals. These are platform snapshots, not audited capability. Match priority suppliers to the forms/categories that need sampling or customization where evidence allows.

## Opportunity conclusion

- `candidate_found`: at least one category contains a defensible candidate and a feasible validation path.
- `needs_refinement`: supply exists, but category recall or visual/functional distinction is too mixed.
- `supply_gap`: approved queries did not find relevant supply.
- `blocked`: required CLI or image-review branches failed materially.

## Portfolio synthesis

Select representative candidates by role, not maximum sales:

- one mainstream benchmark where available;
- one or more differentiated novel/aesthetic candidates where defensible;
- scenario, premium, or bundle candidates that add a distinct job or economic role.

Explicitly state category gaps, supplier concentration, likely commoditization, and unresolved margin/compliance/quality evidence.

The retained set is a comparison portfolio, not a claim that all retained products are equally strong. More coverage must come from defensible `observe` candidates and materially different query directions, never from lowering relevance or visual-evidence requirements. Do not let the market baseline or reference-model family occupy all six lanes merely because it has the strongest exact-match evidence.
