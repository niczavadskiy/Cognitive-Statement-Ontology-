# CSO Bayesian modeling tools

This directory contains tools for Bayesian-style modeling in the **Bayesian extension** of **Cognitive Statement Ontology (CSO)**.

## Overview

The Bayesian extension adds:

- Prior and posterior probabilities for statements and arguments
- Bayes factors for evidence strength
- Influence weights between nodes
- Handling of competing arguments and cognitive biases

**DAG / cycles:** Calculators walk directed paths; **cycles** need explicit handling before stable inference. See [DAG preparation, epistemic layer, and transformation layer](../../docs/epistemic_transformation_dag.md).

## File layout

### Core modules

- **`bayesian_calculator.py`** — Core Bayesian calculations
- **`bayesian_validator.py`** — Validation against the Bayesian schema
- **`technical_rules.py`** — Technical rule helpers

### Documentation

- **`bayesian_modeling_rules.md`** — Rules and principles
- **`risk_examples.md`** — Risk examples and mitigations
- **`README.md`** — This file

### Tests

- **`test_bayesian_system.py`** — System test script

## Quick start

### 1. Dependencies

```bash
pip install numpy jsonschema
```

### 2. Run tests

```bash
cd tools/bayesian
python test_bayesian_system.py
```

### 3. Validate a file

```bash
# from tools/bayesian
python bayesian_validator.py ../../ontology/Bayesian_modeling/examples_bayesian/bayesian_example.json
```

Schema: `ontology/Bayesian_modeling/schema_bayesian.json`. Strengthening and debiasing: `tools/strengthening/` and `tools/debiasing/`.

## Usage

### Core calculations

```python
from bayesian_calculator import BayesianCalculator, interpret_bayes_factor

calculator = BayesianCalculator()

# Bayes factor (for reference)
# NOTE: In CSO the Bayes factor is set by the analyst, not auto-derived as ground truth
bf = calculator.calculate_bayes_factor(
    prior_prob=0.7,
    likelihood_h1=0.8,
    likelihood_h0=0.3
)
print(f"Bayes Factor: {bf:.3f} - {interpret_bayes_factor(bf)}")

# Posterior probability
posterior = calculator.calculate_posterior_probability(0.6, bf)
print(f"Posterior probability: {posterior:.3f}")
```

### Validating data

```python
from bayesian_validator import BayesianValidator

validator = BayesianValidator()
is_valid, errors = validator.validate_file('path/to/ontology.json')

if is_valid:
    print("Ontology is valid")
else:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")
```

### Updating the model

```python
# Load nodes and edges from JSON
updated_nodes, updated_edges = calculator.update_node_probabilities(nodes, edges)

# Inspect updated probabilities
for node in updated_nodes:
    if 'posterior_probability' in node:
        print(f"{node['id']}: {node['posterior_probability']:.3f}")
```

## Schema fields

### Nodes

For statements and arguments:

- **`prior_probability`** (required) — Prior probability [0, 1]
- **`posterior_probability`** (calculated) — Posterior probability [0, 1]

### Edges

- **`bayes_factor`** (set by analyst) — Evidence strength (analyst responsibility)
- **`weight`** (required in many profiles) — Influence on the target node [0, 1]

### Metadata

Optional `bayesian_model_info`:

```json
"bayesian_model_info": {
  "prior_distribution": "expert_informed",
  "convergence_threshold": 0.001,
  "max_iterations": 100
}
```

## Examples

Under `ontology/Bayesian_modeling/examples_bayesian/`:

- **`bayesian_example.json`** — Simple confirmation-bias style example
- **`bayesian_trust.json`** — Trust with competing arguments
- **`bayesian_curiosity.json`** — Curiosity model with cognitive biases

## Interpreting Bayes factor

| BF | Interpretation |
|----|----------------|
| BF < 1 | Evidence against the hypothesis |
| 1 ≤ BF < 3 | Weak evidence |
| 3 ≤ BF < 10 | Moderate evidence |
| 10 ≤ BF < 30 | Strong evidence |
| 30 ≤ BF < 100 | Very strong evidence |
| BF ≥ 100 | Decisive evidence |

## Main rules

### 1. Initializing probabilities

- Prefer expert-informed priors over flat 0.5 when you have knowledge
- Document prior sources
- Use existing domain knowledge where possible

### 2. Edge weights

- Direct evidence typically gets higher weight than indirect
- Meta-analyses and reviews often get high weight
- Anecdotal evidence gets low weight

### 3. Model validation

- Check the model on known cases
- Use multiple quality metrics
- Watch for cycles and instability

## Warnings

**Important:** Bayesian probabilities encode **credence**, not long-run frequencies.

**Risk:** Mis-set edge weights can strongly distort results.

**Limitation:** The toolkit often assumes **independent** pieces of evidence; real arguments are correlated.

## Support

Open an issue in the repository for questions or improvements to the CSO Bayesian extension.

## License

Same license as the main CSO project.
