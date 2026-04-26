# Bayesian Layer Overview

## Purpose

The Bayesian layer extends CSO from structural representation to quantitative belief updating.

It adds:

- prior/posterior probabilities for statements and arguments
- edge-level evidence strength (Bayes factors)
- influence weights
- post-processing debiasing options

## Why this layer is needed

Structural CSO answers:

- what nodes and relations exist
- which biases are present

Bayesian CSO additionally answers:

- how strongly evidence shifts confidence
- which arguments become more or less credible after aggregation
- how much confidence changes after bias correction

## Scope

This layer is intended for:

- argument strength analysis
- comparative scenario testing
- sensitivity and robustness analysis
- confidence-aware reporting

## Non-goals

- Replacing expert semantic interpretation
- Fully automating truth determination
- Guaranteeing independence of all evidence sources

## Integration principle

Use a two-layer workflow:

1. Build and validate the structural CSO graph.
2. Apply Bayesian inference and optional debiasing for quantitative assessment.
