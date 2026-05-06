# Bayesian Inference Workflow

For DAG / cycle preparation and formulas (VFE, Total Predictability, debiasing), see [DAG preparation, epistemic layer, and transformation layer](epistemic_transformation_dag.md).

## Epistemic precondition (layer 2)

**Posterior propagation, VFE, and Total Predictability** are computed on the **epistemic layer**. The calculators traverse **directed** support paths and assume **acyclic** structure on those paths. **Cycles must be resolved (or the graph otherwise brought to DAG readiness) *before* the first posterior / VFE / predictability run** you intend to interpret—not as a step that logically “follows” strengthening by default. Optional **strengthening** can add edges and recreate cycles; **repeat SCC / DAG checks before every epistemic recalculation** that matters for your analysis.

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

4. **Confirm DAG readiness (before epistemic propagation)**
   - **Epistemic-layer** tools in step 5 require **acyclic** traversed paths. If the support subgraph has directed cycles, run SCC reporting and DAG-oriented resolution per [DAG preparation, epistemic layer, and transformation layer](epistemic_transformation_dag.md) **before** step 5.
   - If you already know the graph is acyclic on all paths the calculator uses, document that and skip tooling.

5. **Run posterior / VFE updates**
   - Use `tools/bayesian/` (e.g. `argument_probability_calculator.py`, `calculate_vfe.py`) to propagate analyst-set **Bayes factors** and weights where applicable.
   - Compute or refresh `posterior_probability` and optional `vfe` / graph `total_predictability` blocks.

6. **Run debiasing (optional)**
   - `python tools/debiasing/cso_debiasing_tool.py <graph.json>`
   - Adjust edge Bayes factors for bias influence and recalculate posteriors (still subject to the same **DAG / cycle** expectations if you re-run calculators).

7. **Generate report**
   - Prior vs posterior deltas.
   - High-impact edges.
   - Sensitivity observations.

## Operational rule

Always keep outputs from:

- baseline posterior run
- debiased posterior run

This enables transparent comparison and auditability.
