# Epistemic layer, transformation layer, and DAG preparation

This document consolidates **what happens mathematically** on CSO’s **epistemic (Bayesian-style) layer** and **transformation layer**, and **how graphs are driven toward a DAG** when cycles break inference pipelines. Authoritative schema: [`ontology/schema.json`](../ontology/schema.json), [`ontology/Bayesian_modeling/schema_bayesian.json`](../ontology/Bayesian_modeling/schema_bayesian.json). Implementation reference: [`tools/bayesian/argument_probability_calculator.py`](../tools/bayesian/argument_probability_calculator.py).

---

## 1. Three layers (reminder)

1. **Structural** — nodes, edges, credibility labels, bias flags (`ontology/schema.json`).
2. **Epistemic** — numeric priors, posteriors, edge evidence (Bayes factors, θ, weights), VFE and Total Predictability.
3. **Transformation** — strengthening, contextual enrichment, debiasing, optional **cycle removal / DAG enforcement**, then metric recalculation.

Layers 2–3 are **under active development**; treat formulas below as describing the **current reference implementation**, not a claim of a fully specified global Bayesian network.

---

## 2. Epistemic layer (layer 2) — reference mathematics

### 2.1 Priors and posteriors

- Each participating **statement** / **argument** may carry `prior_probability` ∈ [0, 1].
- **Posterior** `posterior_probability` for arguments is **computed** by tooling (do not hand-edit in automated runs).

### 2.2 Single-edge update (Bayes factor)

Along one edge, probability is updated with a **Bayes factor** BF > 0:

\[
P_{\text{post}} = \frac{P_{\text{prior}} \cdot \text{BF}}{P_{\text{prior}} \cdot \text{BF} + (1 - P_{\text{prior}})}
\]

In code, when BF is missing, a **heuristic** BF may be synthesized from `relation`, `strength`, and `weight` (e.g. `supports` / `contradicts`). For serious analyses, **set or review BF explicitly** on edges.

### 2.3 Chains from statements to an argument

For each argument, the calculator finds paths from **statement** nodes to that argument. Along each path, probabilities are composed using the edge update above. Multiple chains from the same statement–argument pair are considered; an **optimal** chain is selected per pair (implementation detail in `argument_probability_calculator.py`).

### 2.4 Combining multiple chains (independence-style)

For several chain probabilities \(P_1,\ldots,P_n\) treated as **independent support**, the implementation combines them as:

\[
P_{\text{combined}} = 1 - \prod_{i=1}^{n}(1 - P_i)
\]

This is the “noisy-OR” style combination used in the current code (see comments in `_calculate_argument_posterior`). **Real evidence is often dependent**; document assumptions per study.

### 2.5 Variational Free Energy (per argument)

The implementation defines metrics aligned with a VFE-style decomposition (see `calculate_variational_free_energy`):

- **Marginal evidence** from chain probabilities: with evidence probabilities \(p_i\),
  \[
  m = 1 - \prod_i (1 - p_i)
  \]
  (clamped away from 0 for logs).
- **Log-evidence / accuracy term:** \(\text{log\_evidence} = -\ln(m)\). The code also exposes this as **`accuracy_part`** (same as `log_evidence` in the current implementation).
- **KL divergence** between posterior \(q\) and prior \(p\) (Bernoulli):
  \[
  D_{\mathrm{KL}}(q\|p) = q\ln\frac{q}{p} + (1-q)\ln\frac{1-q}{1-p}
  \]
- **Total VFE (reported):**
  \[
  F_k^{\mathrm{VFE}} = \text{log\_evidence} + D_{\mathrm{KL}}(q\|p)
  \]

Lower VFE is treated as “better” in narrative terms; use comparisons **within** a fixed modeling setup, not as absolute truth.

### 2.6 Normalized VFE and per-argument predictability contribution

Let \(|E_k|\) be the number of **statement → argument** edges incident on argument \(k\). The code uses:

\[
\bar{F}_k = \frac{F_k^{\mathrm{VFE}}}{1 + |E_k|}
\]

**Per-argument contribution** to a predictability sum:

\[
\text{contribution}_k = e^{-\bar{F}_k}
\]

### 2.7 Total Predictability (graph-level)

\[
P_{\mathrm{tot}} = \sum_k e^{-\bar{F}_k}
\]

The aggregated structure is also written into graph metadata when the pipeline runs (see `schema_bayesian.json` under `metadata.total_predictability`).

### 2.8 Schema vs tooling: θ, BF, weight

- **`theta_i1`, `theta_i0`**: required on edges by **`schema_bayesian.json`** for validation (conditional parameters for target given source).
- **`bayes_factor`, `weight`, `strength`**: heavily used by **`tools/bayesian/`** for propagation and heuristics. Keep validator + analyst workflow aligned: validate JSON, then run calculators.

---

## 3. Transformation layer (layer 3)

### 3.1 Strengthening

- **Policy-driven argument strengthening** — [`tools/strengthening/argumentation_strengthener.py`](../tools/strengthening/argumentation_strengthener.py): LLM-guided edits / new nodes and edges under rotation of policies (no closed-form “math” — behavior is policy- and prompt-defined).
- **Contextual strengthening** — [`tools/strengthening/contextual_strengthener.py`](../tools/strengthening/contextual_strengthener.py): merges evidence from external CSO graphs; may require `demo-site` modules when that stack is enabled.

After structural changes, **re-run** validation and epistemic scoring if you rely on posteriors / VFE / \(P_{\mathrm{tot}}\).

### 3.2 Debiasing (closed-form on Bayes factors)

From [debiasing_methodology.md](debiasing_methodology.md), implemented in [`tools/debiasing/cso_debiasing_tool.py`](../tools/debiasing/cso_debiasing_tool.py):

**One bias** with weight \(w\):

\[
\text{BF}' = \text{BF} \cdot (1 - w)
\]

**Several biases** with weights \(w_i\):

\[
\text{BF}' = \text{BF} \cdot \prod_i (1 - w_i)
\]

Then posteriors are recomputed using the corrected factors. Assumptions (multiplicative combination, approximate weights) must be documented per run.

### 3.3 DAG-oriented cycle removal (pipeline)

**Why:** Some scoring paths assume **acyclic** structure for stable chaining / interpretation. Strongly connected components (SCC) with more than one node indicate directed cycles.

**Reporting (SCC analysis):**

- [`ParliamentSpeakers/Validation/clipped/find_scc_cycles_report.py`](../ParliamentSpeakers/Validation/clipped/find_scc_cycles_report.py) — Tarjan **O(V+E)** SCC enumeration; text report for merged/strengthened graphs.

**Resolution tool:**

- [`ParliamentSpeakers/dag_resolution.py`](../ParliamentSpeakers/dag_resolution.py) — Loop: detect cycles → call **LLM** with a fixed JSON patch format (`delete` / `edit` / `new`) → apply patches → repeat until no SCC of size > 1 (or limits). Then **`ArgumentProbabilityCalculator`** recomputes **VFE** and **`total_predictability`** and writes a `*_DAG.json` style output.

**Launch (examples):**

```text
cd ParliamentSpeakers
python dag_resolution.py "data_bm_cso\...\file_strengthened.json"
```

Or use [`ParliamentSpeakers/run_dag_resolution.bat`](../ParliamentSpeakers/run_dag_resolution.bat).

**Policy (summary):** The script’s system prompt prioritizes (1) removing illegal **argument → \*** edges, (2) dropping weak or auto-generated edges, (3) for “semantic” cycles, deactivating edges by priority (`influences` → context-like → `supports`), then escalation to re-atomization / composite SCC only if needed. Exact wording lives in `DAG_SYSTEM_INSTRUCTION` inside `dag_resolution.py`.

**Metric tools after DAG:**

- Same as layer 2: [`tools/bayesian/`](../tools/README.md) (`calculate_vfe.py`, full graph passes, etc.).

---

## 4. Suggested tool index

| Task | Location |
|------|----------|
| Validate base CSO | Structural JSON Schema + optional custom checks |
| Validate Bayesian extension | `python tools/bayesian/bayesian_validator.py <graph.json>` |
| Posteriors, VFE, \(P_{\mathrm{tot}}\) | `tools/bayesian/argument_probability_calculator.py`, `calculate_vfe.py` |
| Debiasing | `tools/debiasing/cso_debiasing_tool.py` |
| Strengthening | `tools/strengthening/*.py` |
| SCC report | `ParliamentSpeakers/Validation/clipped/find_scc_cycles_report.py` |
| LLM DAG resolution + metric refresh | `ParliamentSpeakers/dag_resolution.py` |

See also: [bayesian_inference_workflow.md](bayesian_inference_workflow.md), [tools/README.md](../tools/README.md).
