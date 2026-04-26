# Bayesian Inference Workflow

## End-to-end pipeline

1. **Prepare structural graph**
   - Create nodes, edges, and metadata.
   - Validate against the base CSO schema.

2. **Enrich with Bayesian fields**
   - Set node priors.
   - Set edge Bayes factors and weights.
   - Define `bayesian_model_info` when used.

3. **Run Bayesian validation**
   - Check value ranges and required fields.
   - Check graph compatibility for the inference stage.

4. **Run posterior updates**
   - Propagate evidence through the argument graph.
   - Compute `posterior_probability` for target nodes.

5. **Run debiasing (optional)**
   - Detect cognitive-bias-affected nodes.
   - Correct Bayes factors.
   - Recalculate posteriors.

6. **Generate report**
   - Prior vs posterior deltas.
   - High-impact edges.
   - Sensitivity observations.

## Operational rule

Always keep outputs from:

- baseline posterior run
- debiased posterior run

This enables transparent comparison and auditability.
