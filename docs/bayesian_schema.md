# Bayesian schema extensions

Authoritative machine-readable definition: [`ontology/Bayesian_modeling/schema_bayesian.json`](../ontology/Bayesian_modeling/schema_bayesian.json).

The **Bayesian extension** layers numeric belief and diagnostics on top of the base CSO graph. It remains under **active development**.

## Nodes

Fields commonly used in Bayesian-style analysis (see the JSON Schema for required/optional per profile):

- **`prior_probability`** — initial belief for statements and arguments participating in scoring (range [0, 1]).
- **`posterior_probability`** — updated belief after propagation (often **computed** by tools; do not hand-edit in automated workflows).
- **`vfe`** — optional object holding Variational Free Energy-related metrics (e.g. `variational_free_energy`, `F_bar_k`, `predictability_contribution`, `edges_count`, …) when the calculator has run.

Cognitive-bias nodes keep the same `manifestation_of_ones_thought` / `fixation_of_someones_bias` flags as in the base schema.

## Edges

The Bayesian schema requires, for each edge:

- `source`, `target`, `relation`
- **`theta_i1`**, **`theta_i0`** — conditional parameters P(target = 1 | source = 1) and P(target = 1 | source = 0), each in [0, 1]

## Operational fields (pipeline / Python tools)

Graphs used with `tools/bayesian/` (e.g. `argument_probability_calculator.py`, debiasing) often also include:

- **`bayes_factor`** — evidence multiplier on an edge; **should be set or reviewed by the analyst** for serious use (the tool may synthesize a value only when missing).
- **`weight`** — influence weight in [0, 1] (used with strength heuristics in code paths).
- **`strength`** — optional edge strength (0–1) aligned with the base schema where present.

These fields are **not** all listed as required in `schema_bayesian.json`, but they appear in example graphs and in tooling. **Validate** files with `tools/bayesian/bayesian_validator.py` before batch jobs to ensure θ and other required Bayesian fields match the schema.

## Metadata

Bayesian runs may add or use:

- `bayesian_model_info` (e.g. convergence settings) inside `metadata` when used by your pipeline
- **`total_predictability`** summary (graph-level) after VFE / predictability aggregation — see schema properties under `metadata`

## Graph shape for inference

Calculators traverse **directed** support paths. **Cycles** can make posterior updates order-dependent or ill-defined; treat **DAG-oriented** preparation (e.g. SCC analysis and optional collapse) as part of graph readiness, not only schema validity. See [DAG preparation, epistemic layer, and transformation layer](epistemic_transformation_dag.md).

## Validation expectations

1. Base structural graph is valid CSO (`ontology/schema.json`).
2. Bayesian JSON satisfies `schema_bayesian.json` for the validator.
3. Analyst assumptions (priors, Bayes factors, bias weights) are documented per study.
