# CSO documentation baseline (May 2026)

This note aligns documentation with the **current structural core** (`ontology/schema.json`), the **Bayesian extension** (`ontology/Bayesian_modeling/schema_bayesian.json`), and the **tool layout** under `tools/` (render, bayesian, strengthening, debiasing). It replaces older Russian-only release notes.

## What CSO is (structural layer)

Cognitive Statement Ontology (CSO) is a machine-readable graph format for **recorded** discourse: statements, arguments, quotations, questions, cognitive biases, and typed edges. Visualization is optional; the primary artifact is validated JSON.

## Data model (structural schema)

### Node types (`type` enum)

| Type | Role |
|------|------|
| `statement` | Asserted content at any granularity |
| `argument` | Conclusion / endpoint in a reasoning chain |
| `cognitive_bias` | Bias nodes; use `manifestation_of_ones_thought` and `fixation_of_someones_bias` (0 or 1) |
| `quotation` | Quoted material; `author` when known |
| `question` | Questions; excluded from argument probability machinery unless the pipeline explicitly includes them |

### Required node fields

- `id` — string, pattern `^[a-zA-Z0-9_-]+$`
- `type` — one of the enum values above
- `text` — non-empty string

### Common optional node fields

- `credibility` — `green` | `yellow` | `red` | `gray` (default `gray` in schema)
- `author`, `timestamp`, `metadata` (`tags`, `confidence`, `notes`)

### Edge relations (`relation` enum, base schema)

`supports`, `contradicts`, `influences`, `responds_to`, `quotes`, `cites`, `related_to`, `answered_by`, `answers`, `asks_about`

### Argument direction (pipeline / validation rules)

- In general, **arguments are targets** of supporting or influencing edges (statements, biases, quotations, questions point **to** arguments).
- **Exception:** arguments may appear as **sources** for **question** links (e.g. `answers`), as documented in [rules.md](rules.md).

### Graph-level metadata (required in base schema)

`metadata` must include: `id_author`, `name_author`, `date_time`, `source`, `version` (default schema example: `1.0.2`, semver pattern).

Optional: `title`, `description`, `expert`, `created_at`, `updated_at`.

## Credibility

Discrete labels: **green**, **yellow**, **red**, **gray** — see [credibility.md](credibility.md). These are independent of the Bayesian numeric layer.

## Visualization notations

The Graphviz renderer (`tools/render/render_graph.py`) supports notation modes including:

- `context` — biases as columns, contextual layout
- `bias` — bias-centric blocks and cross-bias structure
- `sequential` — ordered / chain-oriented layout
- `hierarchical` — tree-like layout

Outputs are written to the repository `visualisations/` directory (generated artifacts).

## Tools (executable layout)

| Path | Purpose |
|------|---------|
| `tools/render/` | Render CSO JSON to PNG (Graphviz) |
| `tools/bayesian/` | Bayesian-schema validation, posteriors, VFE / predictability helpers |
| `tools/strengthening/` | Argument and contextual strengthening (pipeline-oriented; may depend on external LLM modules) |
| `tools/debiasing/` | Adjust edge evidence for bias effects and recalculate |

Install: `pip install -r tools/requirements.txt` (from repo root). See [tools/README.md](../tools/README.md).

## Bayesian extension

- **Schema:** `ontology/Bayesian_modeling/schema_bayesian.json` — adds priors, posteriors, VFE-related node fields, `theta_i1` / `theta_i0` on edges (required by that schema), and metadata such as `total_predictability` when present.
- **Practice:** Python utilities in `tools/bayesian/` often use **`bayes_factor`** and **`weight`** (and `strength`) on edges for updating; graphs used in the wild may carry **both** θ parameters and BF/weight. Validate with `tools/bayesian/bayesian_validator.py` before batch runs.
- **Stance:** treat numeric updating as **Bayesian-style / analyst-informed** scoring, not as a fully specified global PGM (see project [README.md](../README.md)).

## Ingestion formats

The **interchange format** for the ontology core is **JSON** matching `ontology/schema.json`. Text, DOCX, FB2, and other formats are handled by **upstream extraction / LLM pipelines** (e.g. demo or research scripts), not by the schema itself.

## Validation

- **Structural:** JSON Schema validation against `ontology/schema.json` (`nodes`, `edges`, `metadata` required; `additionalProperties: false` on items as defined in the schema file).
- **Bayesian:** use `ontology/Bayesian_modeling/schema_bayesian.json` via `tools/bayesian/bayesian_validator.py`.

## Further reading

- [definition.md](definition.md), [rules.md](rules.md), [use_cases.md](use_cases.md)
- [DAG preparation, epistemic layer, and transformation layer](epistemic_transformation_dag.md) — graph prep for inference; math for layers 2–3; SCC and transformation tooling
- [bayesian_overview.md](bayesian_overview.md), [bayesian_schema.md](bayesian_schema.md), [bayesian_inference_workflow.md](bayesian_inference_workflow.md)
