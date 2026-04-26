# Cognitive Ontology

Welcome to the Cognitive Statement Ontology project!

## Overview

This project provides a framework for analyzing and visualizing cognitive statements, their relationships, and the cognitive biases that influence them. The ontology helps in understanding how statements are connected to cognitive biases and how they can be evaluated for credibility.

## Structure

- `ontology/` — core ontology definitions and rules
  - `notations/` — different visualization notations
  - `examples/` — example data files
- `docs/` — project documentation
  - [Definition and Scope](definition.md)
  - [Ontology Rules](rules.md)
  - [Use Cases](use_cases.md)
  - [Working with Cognitive Biases](cognitive_biases.md)
  - [Statement Credibility Assessment](credibility.md)
  - [Notation Comparison](comparison.md)
  - [Bayesian Layer Overview](bayesian_overview.md)
  - [Bayesian Schema Extensions](bayesian_schema.md)
  - [Bayesian Inference Workflow](bayesian_inference_workflow.md)
  - [Debiasing Methodology](debiasing_methodology.md)
  - [Evaluation and Benchmarks](evaluation_benchmarks.md)
- `tools/` — visualization and analysis tools
  - [Technical Documentation](../tools/README.md)

## Probabilistic layer (Bayesian)

CSO includes an optional probabilistic layer for quantitative assessment of statement graphs:

- prior and posterior probabilities for nodes
- evidence strength via Bayes factors
- influence weighting on edges
- debiasing and post-processing for cognitive bias correction

See [Bayesian Layer Overview](bayesian_overview.md) and [Bayesian Inference Workflow](bayesian_inference_workflow.md).

## Supported Notations

The project supports multiple visualization notations to represent cognitive statements and their relationships:

- [Sequential notation](../ontology/notations/sequential_notation.md) — linear representation of statements and their connections
- [Context notation](../ontology/notations/context_notation.md) — shows statements in the context of cognitive biases
- [Bias-oriented notation](../ontology/notations/bias_notation.md) — focuses on relationships between cognitive biases

## Getting Started

For technical setup and usage instructions, please refer to the [Tools Documentation](../tools/README.md).
