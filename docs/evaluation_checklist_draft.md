# Evaluation checklist (draft)

Working notes for sanity-checking Bayesian and debiasing outputs in this repo. Not a full evaluation methodology or external benchmark spec.

## Why evaluate

Posteriors and corrections are only useful if they are stable, interpretable, and consistent with expert review.

## Core quality checks

- **Calibration check**: do posterior levels match observed expert confidence patterns?
- **Sensitivity check**: how much do outputs change when priors or weights vary?
- **Robustness check**: do small input perturbations cause disproportionate output jumps?
- **Debiasing impact check**: are corrections plausible and directionally consistent?

## Suggested exercise scenarios

Use these as repeatable passes over example graphs (e.g. under `ontology/Bayesian_modeling/examples_bayesian/` and `ontology/examples/`):

1. Simple support chain with known expected direction.
2. Conflicting arguments with asymmetric evidence strengths.
3. Multi-bias affected node with cumulative correction.
4. Sparse evidence case (high uncertainty expected).

## Minimum reporting fields

For each scenario, record:

- input graph summary
- baseline posterior results
- debiased posterior results (if applicable)
- interpretation notes
- identified model limitations
