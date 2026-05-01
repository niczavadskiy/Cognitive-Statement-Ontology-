# Cognitive Statement Ontology — Tools

Executable utilities for **Cognitive Statement Ontology (CSO)**: rendering, validation, Bayesian-style epistemic scoring, strengthening, and debiasing.

## Setup

1. Install [Graphviz](https://graphviz.org/download/) (system package) for graph rendering.

2. Python dependencies (from repository root):

   ```sh
   pip install -r tools/requirements.txt
   ```

   The same dependencies cover `tools/render/` and `tools/bayesian/`. The render-only list is also in [`tools/render/requirements.txt`](render/requirements.txt) if you need a minimal set.

## Architecture (tools layout)

```text
tools/
├── render/           # Graphviz rendering (PNG → visualisations/)
├── bayesian/         # Validation, posteriors, VFE, odds / Bayes-factor helpers
├── strengthening/    # Argument and contextual strengthening pipelines
└── debiasing/        # Bias correction on Bayes factors and recalculation
```

Schemas and example JSON graphs remain under `ontology/` (including `ontology/Bayesian_modeling/`).

## Render (`tools/render/`)

Renders CSO JSON into PNGs under the repository `visualisations/` folder (generated output, not source).

### Usage

```sh
python tools/render/render_graph.py <input_file> [notation_type]
```

- `notation_type`: `context` (default in some flows), `bias`, `sequential`, or `hierarchical` — see script help and [`docs/comparison.md`](../docs/comparison.md).

### Examples

```sh
python tools/render/render_graph.py ontology/examples/mini_example_2.json context
python tools/render/render_graph.py ontology/examples/mini_example_2.json bias
python tools/render/render_graph.py ontology/examples/mini_example_2.json sequential
```

## Bayesian and epistemic tools (`tools/bayesian/`)

Implements a **Bayesian-inspired epistemic layer** for CSO graph scoring and iterative refinement. Bayes factors on edges are **set by the analyst** in the graph model, not magically inferred for all domains.

Main entry points:

| Script | Role |
|--------|------|
| `bayesian_validator.py` | Validate CSO JSON against `ontology/Bayesian_modeling/schema_bayesian.json` |
| `bayesian_calculator.py` | Posterior / BF helpers (library + CLI patterns in tests) |
| `argument_probability_calculator.py` | Argument posteriors, VFE, Total Predictability along chains |
| `calculate_vfe.py` | Batch VFE on a CSO file |
| `technical_rules.py` | Modeling rule helpers |

### Usage (from repository root)

```sh
python tools/bayesian/bayesian_validator.py ontology/Bayesian_modeling/examples_bayesian/bayesian_example.json
python tools/bayesian/test_bayesian_system.py
python tools/bayesian/calculate_vfe.py path/to/graph.json
```

Or run from `tools/bayesian/` with paths relative to that directory; see [`tools/bayesian/README.md`](bayesian/README.md).

## Debiasing (`tools/debiasing/`)

```sh
python tools/debiasing/cso_debiasing_tool.py path/to/cso.json
python tools/debiasing/test_debiasing_example.py
```

Details: [`tools/debiasing/DEBIASING_README.md`](debiasing/DEBIASING_README.md).

## Strengthening (`tools/strengthening/`)

- `argumentation_strengthener.py` — policy-driven argument improvement (requires an LLM processor in your pipeline).
- `contextual_strengthener.py` — context from other CSO graphs; may expect `demo-site/src` modules if that optional stack is present.

## Documentation

- [Epistemic math, transformation layer, and DAG](../docs/epistemic_transformation_dag.md)
- [Bayesian overview](../docs/bayesian_overview.md)
- [Bayesian inference workflow](../docs/bayesian_inference_workflow.md)
- [Project README](../README.md)

## Input format

CSO JSON must conform to `ontology/schema.json`; Bayesian fields follow `ontology/Bayesian_modeling/schema_bayesian.json`.
