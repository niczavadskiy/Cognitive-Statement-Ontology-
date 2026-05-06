# DAG preparation, epistemic layer, and transformation layer

This document consolidates **DAG / cycle preparation** (precondition for stable inference), **what happens mathematically** on CSO’s **epistemic (Bayesian-style) layer**, and **transformation-layer** tooling (strengthening, debiasing, graph edits)—for graphs where cycles would otherwise break inference pipelines. Authoritative schema: [`ontology/schema.json`](../ontology/schema.json), [`ontology/Bayesian_modeling/schema_bayesian.json`](../ontology/Bayesian_modeling/schema_bayesian.json). Implementation reference: [`tools/bayesian/argument_probability_calculator.py`](../tools/bayesian/argument_probability_calculator.py).

---

## 1. Three layers (reminder)

1. **Structural** — nodes, edges, credibility labels, bias flags (`ontology/schema.json`).
2. **Epistemic** — numeric priors, posteriors, edge evidence (Bayes factors, θ, weights), VFE and Total Predictability.
3. **Transformation** — structural edits (strengthening, contextual enrichment), **DAG-oriented cycle removal** when you need stable layer-2 scores, debiasing, then epistemic **(re)calculation**.

**Ordering for inference:** Posteriors, VFE, and Total Predictability are **epistemic-layer** outputs. Their calculators assume **acyclic** support paths, so **DAG / cycle readiness must be achieved *before* those runs** whenever cycles are present—not only “after” other transformation steps. Strengthening and merges can **add** cycles; **re-check** before each epistemic pass you rely on.

Layers 2–3 are **under active development**; treat formulas below as describing the **current reference implementation**, not a claim of a fully specified global Bayesian network.

---

## 2. Epistemic layer (layer 2) — reference mathematics

### 2.1 Priors and posteriors

- Each participating **statement** / **argument** may carry `prior_probability` ∈ [0, 1].
- **Posterior** `posterior_probability` for arguments is **computed** by tooling (do not hand-edit in automated runs).

### 2.2 Single-edge update (Bayes factor)

Along one edge, probability is updated with a **Bayes factor** BF > 0:

```math
P_{\text{post}} = \frac{P_{\text{prior}} \cdot \text{BF}}{P_{\text{prior}} \cdot \text{BF} + (1 - P_{\text{prior}})}
```

**Plain:** $`P_{\text{post}} = (P_{\text{prior}} \cdot \mathrm{BF}) / (P_{\text{prior}} \cdot \mathrm{BF} + 1 - P_{\text{prior}})`$.

In code, when BF is missing, a **heuristic** BF may be synthesized from `relation`, `strength`, and `weight` (e.g. `supports` / `contradicts`). For serious analyses, **set or review BF explicitly** on edges.

### 2.3 Chains from statements to an argument

For each argument, the calculator finds paths from **statement** nodes to that argument. Along each path, probabilities are composed using the edge update above. Multiple chains from the same statement–argument pair are considered; an **optimal** chain is selected per pair (implementation detail in `argument_probability_calculator.py`).

### 2.4 Combining multiple chains (independence-style)

For several chain probabilities $`P_1,\ldots,P_n`$ treated as **independent support**, the implementation combines them as:

```math
P_{\text{combined}} = 1 - \prod_{i=1}^{n}(1 - P_i)
```

**Plain (noisy-OR):** combined = $`1 - (1-P_1)(1-P_2)\cdots(1-P_n)`$.

This is the “noisy-OR” style combination used in the current code (see comments in `_calculate_argument_posterior`). **Real evidence is often dependent**; document assumptions per study.

### 2.5 Variational Free Energy (per argument)

The implementation defines metrics aligned with a VFE-style decomposition (see `calculate_variational_free_energy`).

**Noisy-OR aggregate over chains** — with per-chain probabilities $`p_i`$ (from the implementation’s chain propagation, not necessarily a literal $`P(y \mid x)`$ in a fully specified joint model):

```math
m = 1 - \prod_i (1 - p_i)
```

(clamped away from 0 for logs). **This $`m`$ is not** Bayesian **model evidence** $`P(y)`$ (marginal likelihood of an observation under $`P(y,x)`$); it is a **combiner** for parallel support channels (independence of “failure” $`(1-p_i)`$ is an assumption to document per use case).

**Accuracy-style term** — let $`\ell = -\ln(m)`$ (same as **`accuracy_part`** / **`log_evidence`** in code). It plays a **surprise / penalty** role analogous to terms tied to fit-to-evidence in variational bounds, but **must not** be read as $`-\ln P(y)`$ unless you build a generative model that identifies $`m`$ with $`P(y)`$.

```math
\ell = -\ln(m)
```

**KL divergence** between posterior $`q`$ and prior $`p`$ (Bernoulli):

```math
D_{\mathrm{KL}}(q\parallel p) = q\ln\frac{q}{p} + (1-q)\ln\frac{1-q}{1-p}
```

**Total VFE (reported):**

```math
F_k^{\mathrm{VFE}} = \ell + D_{\mathrm{KL}}(q\parallel p)
```

**Relation to active inference.** The functional $`\mathbb{E}_Q[\ln Q - \ln P(y,x)]`$ and equivalent rearrangements are standard: Parr, Pezzulo, & Friston (2022), ch. 4 §4.2, eq. (4.2)–(4.4), and app. A, eq. (A.29) ([*Active Inference*](https://mitpress.mit.edu/9780262045353/active-inference/), MIT Press). Equation (4.4) highlights one form: $`F[Q,y] = D_{\mathrm{KL}}[Q(x)\,\|\,P(x\,|\,y)] - \ln P(y)`$ (KL to the **true** posterior and **marginal likelihood** $`P(y)`$). Other equivalent ELBO-style splits use $`D_{\mathrm{KL}}[Q\,\|\,P(x)]`$ (KL to the **prior**) together with an expected log-likelihood / accuracy term—so KL between approximate posterior $`q`$ and prior $`p`$ here is **in that familiar family**, not an ad-hoc substitute for “correct” variational inference. What is specific to CSO is the **accuracy surrogate**: $`\ell = -\ln m`$ from the noisy-OR aggregate $`m`$ over chain $`p_i`$, which is **not** $`-\ln P(y)`$ unless you explicitly equate $`m`$ to model evidence in a defined generative model.

Lower VFE is treated as “better” in narrative terms; use comparisons **within** a fixed modeling setup, not as absolute truth.

### 2.6 Normalized VFE and per-argument predictability contribution

Let $`|E_k|`$ denote the **cardinality** (count) of **direct** edges **statement → argument $`k`$** — not “absolute value” of a number. The code uses:

```math
\bar{F}_k = \frac{F_k^{\mathrm{VFE}}}{1 + |E_k|}
```

**How $`|E_k|`$ is counted** (see `_count_S_to_A_edges` in [`tools/bayesian/argument_probability_calculator.py`](../tools/bayesian/argument_probability_calculator.py)):

- Scan all edges in the CSO graph.
- Count an edge **iff** `edge.target` is the id of argument $`k`$ **and** the `edge.source` node has `type == "statement"`.
- **Only one-hop links** count: a path such as statement → … → intermediate nodes → argument $`k`$ does **not** increase $`|E_k|`$ unless there is also a **direct** edge from some statement to $`k`$.
- **Relation** (`supports`, `contradicts`, etc.) is **not** used in this count — any directed edge from a statement node to argument $`k`$ is included.

**Per-argument contribution** to a predictability sum:

```math
\text{contribution}_k = e^{-\bar{F}_k}
```

### 2.7 Total Predictability (graph-level)

```math
P_{\mathrm{tot}} = \sum_k e^{-\bar{F}_k}
```

**Plain:** $`P_{\mathrm{tot}} = \sum_k \exp(-\bar{F}_k)`$.

The aggregated structure is also written into graph metadata when the pipeline runs (see `schema_bayesian.json` under `metadata.total_predictability`).

### 2.8 Schema vs tooling: θ, BF, weight

- **`theta_i1`, `theta_i0`**: required on edges by **`schema_bayesian.json`** for validation (conditional parameters for target given source).
- **`bayes_factor`, `weight`, `strength`**: heavily used by **`tools/bayesian/`** for propagation and heuristics. Keep validator + analyst workflow aligned: validate JSON, then run calculators.

---

## 3. Transformation layer (layer 3)

Section 3 groups **operational tools** that edit the graph or prepare it for scoring. **Logically**, **DAG / cycle resolution is an epistemic precondition** (layer 2): run it **before** posterior / VFE / Total Predictability whenever directed cycles appear on traversed paths. It is documented here because implementations live next to other graph-edit pipelines. **Strengthening** often runs earlier in a project, but it is **not** a substitute for DAG prep—strengthening can create cycles, so you may need another DAG pass **before** the next epistemic run.

### 3.1 DAG-oriented cycle removal (pipeline)

**Why (epistemic):** Layer-2 calculators walk **directed** support paths. **Cycles** make propagation order-dependent and undermine interpretation of posteriors, VFE, and $`P_{\mathrm{tot}}`$. **Remove or collapse cycles before** invoking those tools on the subgraph you care about.

**Cycle detection (in this repo):**

- [`tools/bayesian/technical_rules.py`](../tools/bayesian/technical_rules.py) — `TechnicalRules.detect_cycles()` returns directed cycles from an edge list (DFS-style listing).
- [`tools/bayesian/bayesian_validator.py`](../tools/bayesian/bayesian_validator.py) — `check_cycle_detection` can surface cycle warnings during validation.

For **strongly connected components** (Tarjan, **O(V+E)**) or machine-readable SCC reports, use a graph library or a small external script; CSO does **not** currently ship a dedicated SCC CLI under `tools/`.

**Breaking cycles / enforcing a DAG:**

This repository does **not** include an automated DAG-resolution driver. **Manually** edit the CSO JSON (remove or retype edges, refactor nodes) until the support subgraph you score is acyclic, or plug in **your own** automation (e.g. scripted or LLM-assisted patches, then re-validate). Typical **policy-style** heuristics people use: (1) remove schema-invalid **argument → \*** edges, (2) drop weak or placeholder edges, (3) for “semantic” cycles, deactivate edges in a documented order (e.g. `influences` → context-like relations → `supports`), escalating to re-atomization only if needed.

After the graph is DAG-ready on the paths you care about, run **`ArgumentProbabilityCalculator`** and related tools so **VFE** and **`total_predictability`** match that structure; save under a new filename if you want to keep both versions.

**Epistemic tools (run only after DAG readiness on that graph):**

- [`tools/bayesian/`](../tools/README.md) — `argument_probability_calculator.py`, `calculate_vfe.py`, full graph passes, etc.

### 3.2 Strengthening

- **Policy-driven argument strengthening** — [`tools/strengthening/argumentation_strengthener.py`](../tools/strengthening/argumentation_strengthener.py): LLM-guided edits / new nodes and edges under rotation of policies (no closed-form “math” — behavior is policy- and prompt-defined).
- **Contextual strengthening** — [`tools/strengthening/contextual_strengthener.py`](../tools/strengthening/contextual_strengthener.py): merges evidence from external CSO graphs; may require `demo-site` modules when that stack is enabled.

After structural changes, **re-run** schema validation; **re-check SCC / DAG** before the next **epistemic** pass if posteriors / VFE / $`P_{\mathrm{tot}}`$ must stay interpretable.

### 3.3 Epistemic debiasing (closed-form on Bayes factors)

This subsection is **only** [epistemic (BF) debiasing](debiasing_methodology.md#terminology-two-kinds-of-debiasing): multiply edge Bayes factors, then recompute posteriors. **Structural / editorial debiasing** — revising statements and `cognitive_bias` linkage so the modeled discourse is less distorted — is separate; see [cognitive_biases.md](cognitive_biases.md). It changes the graph; calculators simply consume whatever graph you save (no extra debiasing operator beyond BF correction).

From [debiasing_methodology.md](debiasing_methodology.md), implemented in [`tools/debiasing/cso_debiasing_tool.py`](../tools/debiasing/cso_debiasing_tool.py):

**One bias** with weight $`w`$:

```math
\text{BF}' = \text{BF} \cdot (1 - w)
```

**Several biases** with weights $`w_i`$:

```math
\text{BF}' = \text{BF} \cdot \prod_i (1 - w_i)
```

Then posteriors are recomputed using the corrected factors. Assumptions (multiplicative combination, approximate weights) must be documented per run. (Same **acyclicity** expectations apply as for any other epistemic recalculation.)

---

## 4. Suggested tool index

| Task | Location |
|------|----------|
| Validate base CSO | Structural JSON Schema + optional custom checks |
| Validate Bayesian extension | `python tools/bayesian/bayesian_validator.py <graph.json>` |
| List directed cycles (simple) | `tools/bayesian/technical_rules.py` — `detect_cycles`; validator warnings in `bayesian_validator.py` |
| SCC / automated DAG repair | Not shipped in `tools/` — external script, graph library, or manual JSON edits |
| Posteriors, VFE, $`P_{\mathrm{tot}}`$ | `tools/bayesian/argument_probability_calculator.py`, `calculate_vfe.py` |
| Strengthening | `tools/strengthening/*.py` |
| Epistemic (BF) debiasing | `tools/debiasing/cso_debiasing_tool.py` |

See also: [bayesian_inference_workflow.md](bayesian_inference_workflow.md), [tools/README.md](../tools/README.md).
