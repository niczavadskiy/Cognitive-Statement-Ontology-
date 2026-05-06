# CSO Bayesian modeling rules

## Core principles

### 1. Prior probability
- **Statements** should carry `prior_probability` — baseline credence in truth.
- **Arguments** should carry `prior_probability` — initial credence.
- **Range:** [0, 1], where 0 = certainly false, 1 = certainly true.
- **Default:** 0.5 (uninformative) when nothing better is available.

### 2. Bayesian updating
- **Posterior** for arguments is computed from the graph (see `argument_probability_calculator.py`).
- **Reference formula:** $P(H|E) = P(H) \times \mathrm{BF} / (P(H)\times\mathrm{BF} + P(\neg H))$.
- **BF (Bayes factor):** strength of evidence (should be analyst-set in serious use).

### 3. Weighted influence
- **Edge `weight`:** how much the source moves the target.
- **Range:** [0, 1], where 1 = full influence in the heuristic used by tools.
- **Default in code paths:** often 1.0.

## Computation rules

### 4. Setting Bayes factors
Bayes factors should be set by the **analyst** from substantive judgment.

Reference definition:
```
BF = P(E|H1) / P(E|H0)
```
where:
- E = evidence
- H1 = main hypothesis
- H0 = alternative

**Important:** BF is not “the truth from data alone”; expert choice matters.

### 5. Single-step posterior update
```
Posterior = Prior × BF / (Prior × BF + (1 - Prior))
```

### 6. Aggregating multiple links (conceptual)
When multiple links hit one node, implementations may use weighted geometric or other schemes; see code and [risk_examples.md](risk_examples.md).

## Validation rules

### 7. Probability bounds
- All probabilities in [0, 1].
- Mutually exclusive exhaustive events sum to ≤ 1 where applicable.
- Posterior must stay in [0, 1].

### 8. Relation coherence
- `supports` should move belief toward the target in the intended direction.
- `contradicts` should move against.
- `influences` may be signed either way depending on modeling.

### 9. Updates after edits
- Add/remove nodes: recompute dependent posteriors.
- Change edges: recompute downstream nodes.
- After debiasing: full graph recalculation is typical.

## Special cases

### 10. Cognitive biases
- **Confirmation bias:** may inflate weights on confirming links (modeling choice).
- **Anchoring:** may freeze priors.
- **Hindsight:** may distort posteriors if not documented.

### 11. Competing arguments
- **Competition:** opposite conclusions.
- **Synergy:** mutually reinforcing.
- **Independence:** little interaction (often an approximation).

### 12. Cycles
- Detect cycles before stable metrics.
- Some pipelines use PageRank-style stabilization or **DAG resolution** (see `docs/epistemic_transformation_dag.md`).
- Cap iteration depth.

## Quality metrics

### 13. Reliability
- **Calibration:** probabilities vs outcomes.
- **Discrimination:** separating hypotheses.
- **Stability:** small input changes should not explode outputs.

### 14. Interpretability
- **Transparency:** traceable arithmetic.
- **Auditability:** where each number came from.
- **Explainability:** narrative for stakeholders.

## Practical guidance

### 15. Priors
- Expert elicitation, empirical rates, or flat priors only when justified.

### 16. Model updates
- Incremental vs batch vs adaptive — pick per workflow.

### 17. Uncertainty
- Intervals, distributions, sensitivity analysis.

## Limitations and risks

### 18. Model limits
- **Independence:** nodes often interact; independence is a shortcut.
- **Linearity:** weight may not capture nonlinear interaction.
- **Stationarity:** parameters may drift over time.

### 19. Misuse risks

#### 19.1 Confusing credence with frequency
- **Issue:** treating Bayesian probabilities as long-run frequencies.
- **Mitigation:** label outputs as belief / modeling outputs.

#### 19.2 Ignoring background knowledge
- **Issue:** default 0.5 everywhere.
- **Mitigation:** document priors from expertise.

#### 19.3 Misreading Bayes factor scale
- **Issue:** BF is not “5× more evidence” in a naive linear sense.
- **Mitigation:** use standard tables (e.g. BF > 3 moderate, > 10 strong).

#### 19.4 Wrong weights on edges
- **Issue:** weight too high/low for the substantive link.
- **Mitigation:** expert review, validation sets, iterative refinement.

#### 19.5 Ignoring context
- **Issue:** same weight for qualitatively different links.
- **Mitigation:** context-specific elicitation.

### 20. Application checklist

#### 20.1 Must-haves
- Document priors and edge BF/weights.
- Validate on held-out or known cases.
- Track multiple metrics.

#### 20.2 Validation procedures
- Cross-validation, bootstrap, sensitivity.

#### 20.3 Monitoring
- Track metric drift and anomalies.

#### 20.4 Documentation
- Change log for weights and assumptions.

## Interpreting Bayes factor (Kass & Raftery-style)

- **BF < 1:** evidence against
- **1 ≤ BF < 3:** weak
- **3 ≤ BF < 10:** moderate
- **10 ≤ BF < 30:** strong
- **30 ≤ BF < 100:** very strong
- **BF ≥ 100:** decisive

## Formulas and algorithms

### Sequential Bayes (conceptual)
```
P(H|E₁,…,Eₙ) ∝ P(H|E₁,…,Eₙ₋₁) × P(Eₙ|H, E₁,…,Eₙ₋₁)
```

### Weighted aggregation (conceptual)
```
P_final = ∏ᵢ (P_i)^(wᵢ/Σwⱼ)
```

### Cycles (conceptual workflow)
1. Initialize posteriors from priors.
2. Iterate updates until convergence or cap.
3. Check stability — or remove cycles first (DAG tooling).

## Examples

### Example 1: Simple update
```json
{
  "prior_probability": 0.3,
  "evidence_likelihood": 0.8,
  "bayes_factor": 4.0,
  "posterior_probability": 0.63
}
```

### Example 2: Multiple pieces of evidence
```json
{
  "prior_probability": 0.5,
  "evidence": [
    {"bf": 3.0, "weight": 0.8},
    {"bf": 2.0, "weight": 0.6}
  ],
  "final_posterior": 0.75
}
```
