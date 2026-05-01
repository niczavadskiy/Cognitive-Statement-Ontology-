# Bayesian Inference Workflow

For formulas (VFE, Total Predictability, debiasing, DAG tooling), see [Epistemic math, transformation layer, and DAG](epistemic_transformation_dag.md).

## End-to-end pipeline

1. **Prepare structural graph**
   - Create nodes, edges, and metadata.
   - Validate against the base CSO schema.

2. **Enrich with Bayesian fields**
   - Set node priors (and posteriors only if seeding a run manually).
   - On each participating edge: set **`theta_i1` and `theta_i0`** per `schema_bayesian.json`; add **`bayes_factor`** / **`weight`** when using the Python calculators in `tools/bayesian/`.
   - Define `bayesian_model_info` in `metadata` when used.

3. **Run Bayesian validation**
   - `python tools/bayesian/bayesian_validator.py <graph.json>`
   - Check value ranges, required θ fields on edges, and compatibility with `ontology/Bayesian_modeling/schema_bayesian.json`.

4. **Run posterior / VFE updates**
   - Use `tools/bayesian/` (e.g. `argument_probability_calculator.py`, `calculate_vfe.py`) to propagate analyst-set **Bayes factors** and weights where applicable.
   - Compute or refresh `posterior_probability` and optional `vfe` / graph `total_predictability` blocks.

5. **Run debiasing (optional)**
   - `python tools/debiasing/cso_debiasing_tool.py <graph.json>`
   - Adjust edge Bayes factors for bias influence and recalculate posteriors.

6. **Generate report**
   - Prior vs posterior deltas.
   - High-impact edges.
   - Sensitivity observations.

## Operational rule

Always keep outputs from:

- baseline posterior run
- debiased posterior run

This enables transparent comparison and auditability.
