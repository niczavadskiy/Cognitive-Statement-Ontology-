# Bayesian Schema Extensions

## Node-level fields

### Required for Bayesian analysis

- `prior_probability` (float, [0, 1])

### Computed or derived

- `posterior_probability` (float, [0, 1])

## Edge-level fields

### Required

- `weight` (float, [0, 1]) — influence magnitude

### Analyst-provided

- `bayes_factor` (float, > 0) — evidence strength for the update

## Metadata extension

Recommended section:

```json
"bayesian_model_info": {
  "prior_distribution": "expert_informed",
  "convergence_threshold": 0.001,
  "max_iterations": 100
}
```

## Validation expectations

- All required Bayesian fields are present for nodes and edges that participate in inference.
- Values are constrained to valid ranges.
- IDs and references remain valid under the base CSO schema.
- Structural validity is checked before probabilistic validity.
