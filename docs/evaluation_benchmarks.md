# Evaluation and Benchmarks

## Why evaluate

Bayesian outputs are only useful if they are stable, interpretable, and consistent with expert review.

## Core quality checks

- **Calibration check**: do posterior levels match observed expert confidence patterns?
- **Sensitivity check**: how much do outputs change when priors or weights vary?
- **Robustness check**: do small input perturbations cause disproportionate output jumps?
- **Debiasing impact check**: are corrections plausible and directionally consistent?

## Suggested benchmark scenarios

1. Simple support chain with known expected direction.
2. Conflicting arguments with asymmetric evidence strengths.
3. Multi-bias affected node with cumulative correction.
4. Sparse evidence case (high uncertainty expected).

## Reporting template

For each scenario, include:

- input graph summary
- baseline posterior results
- debiased posterior results
- interpretation notes
- identified model limitations
