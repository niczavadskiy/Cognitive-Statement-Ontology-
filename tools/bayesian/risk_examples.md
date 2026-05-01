# Risk examples in CSO Bayesian-style modeling

Use with `tools/bayesian/` and [bayesian_modeling_rules.md](bayesian_modeling_rules.md). Import helpers with `PYTHONPATH` including `tools/bayesian` or run from that directory:

```python
from technical_rules import BayesianModelingRules
```

## Risk 1: Mis-stated influence on the target

### Example 1: Overstated weight
**Situation:** `weight = 1.0` on a link from a weak argument to a strong statement.

**Sample data:**
```json
{
  "nodes": [
    {
      "id": "weak_arg",
      "type": "argument",
      "text": "Weak guess without evidence",
      "prior_probability": 0.3
    },
    {
      "id": "strong_stmt",
      "type": "statement",
      "text": "Important high-credibility claim",
      "prior_probability": 0.8
    }
  ],
  "edges": [
    {
      "source": "weak_arg",
      "target": "strong_stmt",
      "relation": "supports",
      "weight": 1.0,
      "bayes_factor": 0.85
    }
  ]
}
```

**Effect:** A weak line of support can pull down a strong statement (e.g. 0.8 → 0.773) if weights/BFs are not reviewed.

**Fix:** Lower the weight (e.g. 0.2) to reflect weak evidence; re-elicit BF.

### Example 2: Understated weight
**Situation:** `weight = 0.1` from a strong meta-analytic argument to the target.

**Effect:** Strong evidence barely moves the posterior (e.g. 0.5 → 0.542).

**Fix:** Raise weight (e.g. 0.8) for high-quality evidence.

### Example 3: Ignoring context
**Situation:** Same weight for direct experimental support and indirect correlational support.

**Effect:** Indirect evidence gets the same pull as direct evidence.

**Fix:** Context-specific weights; document evidence grading.

## Risk 2: Misinterpreting Bayes factor scale

**Wrong:** “BF = 5 means five times as much proof.”

**Right:** Use calibrated verbal labels (weak / moderate / strong). See `interpret_bayes_factor` in `bayesian_calculator.py`.

## Risk 3: Ignoring background knowledge

**Wrong:** `prior_probability = 0.5` for every node, including well-established facts and wild speculations.

**Fix:** Informative priors where science or domain practice supports them; document rationale.

## Risk 4: Cycles in the graph

**Situation:** Mutual reinforcement A → B → C → A.

**Effects:** Runaway posteriors; metrics become unstable.

**Detection:**
```python
rules = BayesianModelingRules()
cycles = rules.detect_cycles(edges)
print(f"Cycles: {cycles}")
```

**Remediation:** Remove or re-type an edge, lower weights, or run DAG tooling (see `docs/epistemic_transformation_dag.md`).

## Risk 5: Invalid aggregation of probabilities

**Wrong:** Add probabilities from independent hints: \(0.3 + 0.4 + 0.5 > 1\).

**Right:** Use log-odds or weighted geometric aggregation via `BayesianModelingRules`, or the chain / noisy-OR logic in `argument_probability_calculator.py`.

## Risk mitigation practices

1. **Expert panels for weights** — median/IQR of ratings; shrink weight if disagreement is high.
2. **Validation sets** — known outcomes; track accuracy and calibration.
3. **Adaptive tuning** — adjust weights from feedback with caps in [0, 1].
4. **Multiple metrics** — accuracy, calibration, discrimination, stability, interpretability; combine with explicit metric weights.

These scenarios show where naive Bayesian-style graph scoring fails and how to harden real workflows.
