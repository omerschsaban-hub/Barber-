# MCP mapping

The 20× architecture is intentionally mapped onto existing MCP/engineering primitives rather than adding a tool for every layer.

| Layer group | MCP responsibility |
|---|---|
| CAD + deterministic geometry | bind STEP, extract B-Rep/topology/features, measure geometry |
| DFM + repair | evaluate rule graph, apply deterministic repair, revalidate |
| Physics | construct declared simulation inputs, execute simulations, expose uncertainty/provenance |
| Physical/CV | define tests, ingest observations, validate image scale/alignment, extract measurements |
| ML | compute residuals, fit interpretable error/system-identification models, held-out validation, calibration |
| Experimentation | rank next experiments by information value/cost/risk |
| LLM | bounded orchestration and explanation over evidence |
| Release | evaluate evidence gates and require human approval |

A single shared evidence model prevents the UI and MCP from developing separate interpretations of the same sim-to-real result.
