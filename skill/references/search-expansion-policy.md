# Search expansion policy

Use this policy when building the initial plan and whenever a category is empty, irrelevant, homogeneous, or dominated by the reference model.

## Iron rule

The reference item defines the demand anchor, not the portfolio boundary. Search every strategy lane for additional product choices. Never convert a portfolio task into a single-item exact-match report.

For reference-led inputs, normalize a broad `portfolio_product_family` such as the category noun. Keep exact-match language and visual invariants for baseline comparison, but filter any attribute containing phrases such as “reference image,” “same model,” or “same mold” out of every derived query. Select the next non-locking task attribute or fall back to the scenario; never depend on field ordering.

Do not accept a gap or a comparison set below four products after one narrow direction. Execute at least two materially distinct successful directions for that category; prefer three in the initial plan.

## Direction ladder

Move outward by changing the semantic axis, not by stacking more exact-match attributes.

1. **Product-form direction** — search the core product family and adjacent forms that solve the same job.
2. **Structure direction** — search different mechanisms, operation methods, shapes, modularity, storage, ergonomics, or multifunction designs.
3. **Style direction** — search coherent shape language, color systems, material appearance, gifting, display, or packaging rather than one exact reference color.
4. **Scenario direction** — search the job, audience, environment, frequency, or professional/household context; retain explicit task language.
5. **Quality direction** — search material, thickness, workmanship, professional grade, compliance, durability, or ergonomic upgrades as listing claims pending verification.
6. **Bundle direction** — search coherent job-step coverage, starter sets, replacement systems, or complementary tools; reject random assortments.

## Category defaults

- `market_proven`: upstream exact baseline; mainstream product-family demand; factory/wholesale or high-supply baseline.
- `novel_structure`: structural innovation; alternative operation or multifunction form; adjacent form solving the same job.
- `aesthetic`: designed/high-visual product family; coherent style or material appearance; gifting/display/packaging direction.
- `scenario_specific`: exact use scenario; audience or environment specialization; professional/high-frequency task direction.
- `premium_quality`: high-quality/material upgrade; professional or commercial grade; workmanship/compliance/durability direction.
- `solution_bundle`: product-family set; full scenario kit; multi-step solution or replacement/accessory system.

## Failure-driven patches

- If results repeat the reference model, remove exact color, size, hole, seam, or component-position locks and search the broader product family plus the category axis.
- If results are generic commodities, add the category's discriminating axis instead of more baseline nouns.
- If a scenario query returns finished goods instead of tools, keep the task attribute and add explicit tool/use language.
- If titles look promising but images are homogeneous, change structure or adjacent-form language and review the new images.
- If a broad query becomes irrelevant, restore the core job or product-family noun while keeping the new direction.

Every added task must retain a unique task ID, exact query, `query_origin: derived_category_query`, `strategy_category`, `search_direction`, and increasing `search_round`. Create a new plan and output directory rather than overwriting prior evidence.
