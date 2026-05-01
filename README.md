# Cognitive Statement Ontology (CSO)

Welcome to the **Cognitive Statement Ontology (CSO)** project.

## Overview

Cognitive Statement Ontology (CSO) is a framework for representing discourse as a structured graph of statements, arguments, evidence relations, cognitive biases, and epistemic metadata.

The project is **not primarily a visualization tool**. Its main goal is to transform unstructured text into an explicit knowledge structure that can be inspected, evaluated, updated, strengthened, and compared over time.

**CSO is not primarily a visualization tool. It is a machine-readable structure of knowledge for iterative epistemic and structural transformation.**

CSO separates three layers:

1. **Structural layer** — statements, arguments, quotations, questions, cognitive biases, and typed relations between them.
2. **Epistemic layer** — credibility, confidence, prior probabilities, posterior probabilities, Bayes factors, and uncertainty-aware evaluation.
3. **Transformation layer** — tools and policies for iterative graph improvement: merging, strengthening, debiasing, contextual enrichment, and recalculation of argument predictability.

The **Bayesian extension** adds **Bayesian-style** probabilistic scoring over argument graphs: graphs can be evaluated quantitatively, updated through analyst-specified evidence (including Bayes factors on edges), and analyzed with metrics such as Variational Free Energy (VFE) and Total Predictability. This is a **Bayesian-inspired epistemic layer** for graph scoring and iterative refinement—not a claim of fully specified Bayesian inference as a complete probabilistic graphical model.

In this sense, CSO is intended as a machine-readable structure of knowledge for agent memory, argument evaluation, epistemic debugging, and iterative improvement of world models.

## Bayesian extension

The **`bayesian-extension`** branch carries the **Bayesian extension**: an epistemic layer for CSO graphs. It adds:

- node-level priors and posteriors;
- edge-level conditional parameters `theta_i1` and `theta_i0` (where used in the schema);
- evidence propagation using analyst-set **Bayes factors** (not auto-inferred as universal fact);
- argument-level Variational Free Energy metrics;
- graph-level Total Predictability;
- policy-based graph strengthening;
- contextual strengthening from external CSO graphs (where the pipeline is configured).

The Bayesian extension treats a CSO graph not only as a static representation of discourse, but as an object that can be iteratively updated and epistemically refined.

See [Bayesian Layer Overview](docs/bayesian_overview.md), [Bayesian Schema Extensions](docs/bayesian_schema.md), and [Bayesian Inference Workflow](docs/bayesian_inference_workflow.md). The machine-readable extensions are defined in [`ontology/Bayesian_modeling/schema_bayesian.json`](ontology/Bayesian_modeling/schema_bayesian.json).

## Architecture

CSO consists of four main parts (conceptual — concrete types and fields are defined in the JSON schemas):

```text
CSO graph
├── Structural ontology
│   ├── node types: statement, argument, quotation, question, cognitive_bias, …
│   ├── edge types: supports, contradicts, and other typed relations (see schema)
│   └── base JSON schema (ontology/schema.json)
│
├── Epistemic / Bayesian layer
│   ├── prior_probability, posterior_probability
│   ├── theta_i1 / theta_i0 (edge parameters, where present)
│   ├── Bayes factors (analyst-set on edges)
│   ├── VFE metrics, Total Predictability, …
│   └── schema: ontology/Bayesian_modeling/schema_bayesian.json
│
├── Transformation policies
│   ├── argument strengthening
│   ├── contextual strengthening
│   ├── debiasing
│   ├── graph merging (where supported)
│   └── recalculation of epistemic metrics
│
└── Visualization and inspection
    ├── sequential notation
    ├── context notation
    └── bias-oriented notation
```

The `visualisations/` directory holds **generated outputs** (e.g. PNGs from the render tool), not a core ontology artifact.

## Repository structure

```text
docs/
  Conceptual and methodological documentation.

ontology/
  JSON schemas, notation definitions, example CSO graphs,
  and Bayesian schema extensions under ontology/Bayesian_modeling/.

tools/
  Executable tools: rendering, validation, Bayesian calculation,
  strengthening, debiasing, and related scripts (see tools/README.md).

visualisations/
  Generated graph outputs (optional; may be empty in a fresh clone).
```

## Documentation

### Core ontology

- [Definition and Scope](docs/definition.md)
- [Ontology Rules](docs/rules.md)
- [Use Cases](docs/use_cases.md)

### Epistemic / Bayesian layer

- [Epistemic math, transformation layer, and DAG](docs/epistemic_transformation_dag.md)
- [Bayesian Layer Overview](docs/bayesian_overview.md)
- [Bayesian Schema Extensions](docs/bayesian_schema.md)
- [Bayesian Inference Workflow](docs/bayesian_inference_workflow.md)

### Cognitive bias and debiasing

- [Working with Cognitive Biases](docs/cognitive_biases.md)
- [Debiasing Methodology](docs/debiasing_methodology.md)

### Evaluation

- [Statement Credibility Assessment](docs/credibility.md)
- [Evaluation checklist (draft)](docs/evaluation_checklist_draft.md)

### Visualization

- [Notation Comparison](docs/comparison.md)
- Notation specs: [`ontology/notations/`](ontology/notations/)

## Current status

The **Bayesian extension** is under **active development**. The structural CSO schema is usable, while the Bayesian layer, strengthening tools, and layout may change. Treat APIs, metrics, and folder paths as unstable until a release is tagged.

## Getting started

Setup and commands: [Tools documentation](tools/README.md).

## License

See [LICENSE](LICENSE).
