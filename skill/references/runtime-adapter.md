# Atomic runtime contract

The application depends on `@petercjl/1688cli >=0.4 <1`, with `1688-products@1` and `1688-suppliers@1`. Run `1688-opportunity-sourcing-research script discover_runtime.py`; read the emitted canonical Skill completely before returning to the acquisition node. Installed npm dependency is preferred, then the configured entry or a discovered global CLI. Missing dependencies stop acquisition explicitly.

Product tasks retain the legacy handoff identifier `1688-product-find.text_search` for input compatibility and map to `1688cli products search <exact-query> --limit 50 --score-level high`. Supplier handoff tasks `1688-source-suppliers` map to `1688cli suppliers search <exact-query>`. These legacy identifiers are input vocabulary, not direct provider calls.

The collector preserves normalized products[]/suppliers[] envelopes, exact queries, category provenance and failures. The evidence adapter accepts both the normalized contract and historical saved provider envelopes. Business data acquisition and credentials belong exclusively to the capability package. doctor checks local configuration, not remote authorization validity. Failed service calls preserve their errors and partial collection; collection exits nonzero if any task fails.

Node resolves Python 3 and enforces UTF-8 for both file and subprocess I/O on macOS/Windows. Scripts are allowlisted at the application CLI; execute through its script command. Direct standalone execution of acquisition scripts lacks dependency discovery and fails explicitly.

Application state is a new task directory chosen by the caller. Outputs use exclusive creation; existing paths are not reused. Report images remain exact HTTPS URLs from query evidence. The local report may be served over a loopback-only static server for visual QA; this is not a business acquisition route.
