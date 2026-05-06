# Bayesian Layer Overview

## Purpose

The Bayesian layer extends CSO from structural representation to **quantitative, Bayesian-style belief updating and scoring** over the graph.

It adds (see [bayesian_schema.md](bayesian_schema.md) and `schema_bayesian.json`):

- prior / posterior probabilities for statements and arguments
- edge-level parameters **`theta_i1` / `theta_i0`** (required by the Bayesian schema)
- in operational graphs and tools: **Bayes factors** and **weights** on edges (analyst-set or review strongly recommended)
- optional **VFE** and **Total Predictability** diagnostics after running `tools/bayesian/` calculators
- post-processing **debiasing** (`tools/debiasing/`)

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
- Claiming a fully specified global Bayesian network with verified independence structure for every domain
- Guaranteeing independence of all evidence sources

## Integration principle

Use a two-layer workflow:

1. Build and validate the structural CSO graph (`ontology/schema.json`). If you will run quantitative updates, review **cycles** and DAG readiness ([DAG preparation, epistemic layer, and transformation layer](epistemic_transformation_dag.md)).
2. Enrich with Bayesian fields, validate with `tools/bayesian/bayesian_validator.py`, then run **Bayesian-style** updates / VFE and optional debiasing (`tools/bayesian/`, `tools/debiasing/`).
