# Debiasing Methodology

## Goal

Reduce inflated or distorted confidence caused by cognitive bias influence in the graph.

## Core correction rule

For one bias:

`corrected_bayes_factor = original_bayes_factor * (1 - bias_weight)`

For multiple biases:

`correction_factor = Π(1 - bias_weight_i)`

`corrected_bayes_factor = original_bayes_factor * correction_factor`

## Process

1. Detect bias nodes and related statement or argument nodes.
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
