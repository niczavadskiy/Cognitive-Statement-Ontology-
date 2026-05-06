# Debiasing Methodology

## Terminology: two kinds of debiasing

CSO uses the word *debiasing* in two different ways. Keep them separate when reading or writing docs.

1. **Epistemic (Bayes-factor) debiasing** — what **this document** specifies. Numeric correction: edge Bayes factors are multiplied by factors derived from bias **weights**, then posteriors are recomputed. Implemented in [`tools/debiasing/cso_debiasing_tool.py`](../tools/debiasing/cso_debiasing_tool.py). The Bayesian calculators do **not** apply this automatically; you run the tool (or equivalent) when you want this layer.

2. **Structural / editorial debiasing** — you **change the graph itself**: rewrite statements, adjust or remove edges involving [`cognitive_bias`](../ontology/schema.json) nodes, or otherwise model the discourse so that a claim is no longer distorted *as represented*. That is authoring and graph maintenance, described mainly in [Working with Cognitive Biases](cognitive_biases.md). It is **not** a closed-form recipe here; it does **not** add a separate numeric operator inside `tools/bayesian/`. After edits, re-validate the JSON and **re-run** epistemic tools on the updated graph if you need new posteriors / VFE.

## Goal (epistemic debiasing)

Reduce inflated or distorted **numerical confidence** (via posteriors driven by BFs) that is attributed to cognitive bias influence **under the multiplicative BF correction model** below.

## Core correction rule

For one bias:

`corrected_bayes_factor = original_bayes_factor * (1 - bias_weight)`

For multiple biases:

`correction_factor = Π(1 - bias_weight_i)`

`corrected_bayes_factor = original_bayes_factor * correction_factor`

## Process (epistemic debiasing)

1. Detect bias nodes and related statement or argument nodes (as **inputs** to weighting — distinct from replacing those nodes or statements through editorial debiasing).
2. Aggregate bias impact per affected node.
3. Correct edge Bayes factors.
4. Recompute posterior probabilities (e.g. via `tools/debiasing/cso_debiasing_tool.py` and follow-up scoring in `tools/bayesian/` as needed).
5. Compare baseline vs debiased outcomes.

## Output requirements

A debiasing run should report:

- found biases
- affected nodes
- correction factors
- posterior deltas by argument
- assumptions used

## Key assumptions and risks

- Bias weights approximate effect magnitude.
- Combined effects are multiplicative.
- Evidence independence may be violated in real data.

These assumptions must be documented in each analysis run.
