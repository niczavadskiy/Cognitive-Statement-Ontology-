# Credibility Assessment

CSO supports two complementary credibility tracks.

## 1) Expert categorical credibility (structural layer)

Each statement can have one of the following levels:

- **green** — credible (confirmed)
- **yellow** — controversial (requires verification)
- **red** — not credible (refuted)
- **gray** — uncertain

Color-coded assessment of statements is primarily used in the sequential notation. Each statement is assessed by an expert. When preparing a CSO description, the expert identifies cognitive biases and their influence on statements based on their knowledge.

## 2) Probabilistic credibility (Bayesian layer)

For quantitative analysis, CSO can additionally use:

- `prior_probability` — initial confidence before aggregation
- On edges: **`theta_i1` / `theta_i0`** (required by the Bayesian schema) plus, in typical pipelines, **`bayes_factor`** and **`weight`** for analyst-informed updates
- `posterior_probability` — updated confidence after **Bayesian-style** propagation in `tools/bayesian/`

This allows comparing expert judgment (categorical labels) with model-updated belief (posterior values).

## Recommended usage

Use both layers together:

1. Assign categorical credibility for interpretability.
2. Run Bayesian-style scoring / updates in `tools/bayesian/` for quantitative results.
3. Compare disagreements (for example, `green` but low posterior) as review triggers.
4. Optionally apply debiasing and re-evaluate posterior stability.

See [Bayesian Layer Overview](bayesian_overview.md) and [Debiasing Methodology](debiasing_methodology.md).
