# Evaluation checklist (draft)

Working notes for **sanity-checking** Bayesian, debiasing, and (where used) **argumentation-strengthening** outputs in this repository. This is **not** a full evaluation methodology, external benchmark spec, or claim of statistical calibration on a labeled dataset.

## Purpose and audience

- **Who:** graph authors, reviewers, anyone changing `tools/bayesian/`, `tools/debiasing/`, or **`tools/strengthening/`** behavior.
- **What:** decide whether numeric outputs and graph edits are stable and interpretable enough to use in an analysis or report.
- **What this is not:** ground-truth labeling for every statement; automated truth discovery; replacement for domain expert judgment.

## Preconditions

Before treating a run as evaluable, confirm and record:

1. **Validation:** base CSO passes `ontology/schema.json` expectations; Bayesian fields align with `tools/bayesian/bayesian_validator.py` and `ontology/Bayesian_modeling/schema_bayesian.json` where you rely on the validator.
2. **DAG:** satisfy the policy and artifact rules in **[DAG preparation (concentrated)](#dag-preparation-concentrated)** whenever you interpret posteriors / VFE / Total Predictability.
3. **Analyst assumptions:** priors, Bayes factors, and edge weights—especially which edges used **explicit** BF vs **heuristic** synthesis in code—are written down for the study or ticket.
4. **Reproducibility:** commit hash or tag, input JSON path(s), and commands run (calculator, debiasing, strengthening, tests). After code changes, run `tools/bayesian/test_bayesian_system.py` as a smoke test.

## DAG preparation (concentrated)

Use this section as the **single checklist** for cycles and DAG-oriented edits. Full math and tooling context: [DAG preparation, epistemic layer, and transformation layer](epistemic_transformation_dag.md); step order: [Bayesian inference workflow](bayesian_inference_workflow.md).

### Policy

- For **interpreted** epistemic runs, the subgraph the calculator traverses should be **acyclic**, **or** you must **explicitly document** that directed cycles remain and that you are **not** interpreting propagation order.

### Detection

- Run `tools/bayesian/technical_rules.py` (`detect_cycles`) and review **validator** cycle warnings (`bayesian_validator.py`). Record whether cycles exist on paths the calculator actually uses.

### Artifacts (before / after structural DAG prep)

If you apply **DAG-oriented cycle removal** (edits whose purpose is to break cycles before epistemic scoring):

1. Keep an **immutable** copy **before** the step (e.g. `graph_before_dag.json`) and **after** (`graph_after_dag.json`).
2. **Re-validate** both files; note which path backs each reported metric.
3. Compare posteriors / VFE / `total_predictability` **pre vs post** where priors and BFs are held comparable, so shifts attribute to **structural** edits, not ambiguous re-runs.

### After other graph edits

**Strengthening** and merges can **add** edges and recreate cycles. After [argumentation strengthening](#argumentation-strengthening-llm-and-policy) (or manual enrichment), **repeat cycle detection** and this DAG policy before the next epistemic pass you care about.

## Argumentation strengthening (LLM and policy)

Two tools; **iteration count and cost** differ between them.

| Mode | Module | What drives the run |
|------|--------|---------------------|
| **Policy-driven** | `argumentation_strengthener.py` | Rotating **policies** (JSON) and pipeline config block `argumentation_strengthening` (e.g. YAML). |
| **Contextual** | `contextual_strengthener.py` | A **second CSO** as context; caps on new statements derived from discussion size. |

Behavior is **not** closed-form; evaluation mixes **structure**, **schema**, and **optional metrics**.

### Artifacts

- Save **`before_strengthen`** and **`after_strengthen`** JSON (or checkpoint names) plus **pipeline config** (e.g. `total_predictability_diff_min`, `max_upd`, `n_last_politics`, `policies_file`; for contextual: `max_new_statements_coefficient`).
- Record **LLM model** and **policies file version** or **context CSO path** so the run is reproducible.

### Iterations: how they are defined and measured

**Policy-driven strengthening**

- **Iteration** means one **policy application**: typically one LLM call (with possible retries on bad JSON) that proposes a batch of graph edits, then merge into the CSO. The outer loop **rotates policies** and may stop when gains in `total_predictability` fall below a threshold or limits are hit.
- **Measure:** count **successful** applications (e.g. entries in `merge_report` / update history with `policy_number`, when your run records them); count **LLM API calls** from logs; note **last policy number** and **stop reason** (e.g. below `total_predictability_diff_min`, manual stop).
- **`max_upd`:** in code this caps **atomic edits in a single LLM response** (deletes + edits + new nodes + new edges in that payload)—**not** the total number of edits across the whole strengthening session. Do not equate it with “number of iterations.”
- **`n_last_politics`:** size of the recent-update window used when checking stagnation (see `argumentation_strengthener.py`).

**Contextual strengthening**

- **Not** a policy loop. A typical **`strengthen_with_context`** invocation uses **one** main LLM completion that may add up to  
  `max_new_statements = ceil(statement_count × max_new_statements_coefficient)`  
  new statements (implementation enforces at least 1 when the ceiling would be 0).
- **Measure:** **# contextual LLM calls** (usually 1); **Δ statements / edges**; tool logs report how many statements were added vs the cap.

State explicitly in reports **policy vs contextual** so iteration and cost numbers stay comparable.

### Cost and effort (building CSO vs strengthening)

**Initial CSO construction**

- **Human:** authoring, review, disambiguation of statements/arguments, bias tags, hand-entered priors/BFs.
- **Automation:** any LLM or extraction stack that **creates** the first graph from text (may be outside this repo)—log **calls and failures** if you need build-vs-strengthen cost separation.
- **Record (lightweight):** rough **person-time**, **|nodes| / |edges|** when the graph first validates, and how many **validation/fix** rounds were needed.

**Strengthening**

- **Prompt size** scales with **serialized JSON**. Policy mode sends the evolving graph on each application; contextual mode sends **discussion + context** CSO in one prompt—both grow with graph size.
- **Policy path:** cost scales roughly with **# policy applications × typical prompt size**, plus calculator runs if the pipeline refreshes VFE / predictability between steps.
- **Context path:** often **one** call; cost is dominated by **input** tokens (two graphs) and **output** (full updated CSO).
- **Record:** **model id**, **approx. input/output tokens** if the API exposes them, **wall time**, and **quota/billing** if tracked; **temperature / max_tokens** for repeatability.

This supports **evaluation of pipelines**, not just outputs: the same quality target can be reached with very different spend.

### Structure and validity

- Re-validate against **base CSO** (and Bayesian validator if you score the result).
- **Re-run cycle / DAG checks** after strengthening; treat as input to [DAG preparation](#dag-preparation-concentrated) before interpreted posteriors.

### Substance (expert pass)

- Spot-check edits: **alignment with the active policy**, no unsupported new claims, node types and relations remain coherent.
- For **contextual** strengthening: document **source CSO** for context; do not treat context facts as given in the primary discourse without marking provenance.

### Metrics (use with caution)

- Compare **before vs after** `metadata.total_predictability` (and posteriors / VFE if you run calculators). **Higher predictability is not truth**—LLM edits can optimize structure under heuristics.
- Log **stop reason** for policy mode: marginal gain below `total_predictability_diff_min`, empty patch, loop exhaustion, interrupt—not “hit `max_upd`” as total-iteration shorthand (`max_upd` is mainly a **per-response** edit cap).

### Stability and size

- Optional **second run** (different seed/model): note variance in structure and metrics.
- Track **counts** of new nodes/edges; for contextual flows, respect caps (e.g. `max_new_statements_coefficient`) and flag **graph bloat**.

### Pipeline readiness

- Policy-driven strengthener may expect **existing** VFE / `total_predictability` on input; confirm the graph is **pre-computed** when your pipeline requires it.

More: [Tools README — Strengthening](../tools/README.md), [epistemic / transformation doc](epistemic_transformation_dag.md) §3.2.

## Core quality checks

Go beyond yes/no: each check should produce **short notes or a mini-table** you could paste into an issue or lab book.

### Calibration

- **Against what:** expert ordinal judgments (“A stronger than B”), rough confidence bands, or scenario expectations—not only raw posterior numbers.
- **Record:** for a few key arguments, expected ranking or interval vs model output; flag large surprises and whether they trace to a single edge BF or to aggregation.

### Sensitivity

- **How:** vary one or two **high-leverage** inputs (e.g. ±10–20% on a dominant BF, or a prior on a hub argument); recompute.
- **Record:** define upfront what delta in posterior or in VFE / graph predictability counts as “material” for your use case; note which parameters flip that threshold.

### Robustness

- **How:** small, plausible perturbations—slightly lower `weight`, drop one weak edge, fix a typo-level prior—should not cause **disproportionate** jumps unless the graph is genuinely knife-edge (e.g. competing chains, near-tie BFs, or cycles—see [DAG preparation](#dag-preparation-concentrated)).
- **Record:** if a jump happens, tie it to mechanism using [epistemic / transformation doc](epistemic_transformation_dag.md) and [risk examples](../tools/bayesian/risk_examples.md).

### Debiasing impact

Applies to **epistemic (BF) debiasing** via `tools/debiasing/` — not to **structural / editorial** changes to statements or `cognitive_bias` links alone (those need a normal re-run of the calculator on the edited graph). See [debiasing methodology](debiasing_methodology.md#terminology-two-kinds-of-debiasing).

- **Check:** after `tools/debiasing/`, corrected BFs and recomputed posteriors move in a **directionally plausible** way relative to linked bias nodes and documented weights.
- **Record:** baseline vs debiased posteriors for affected targets; note any correction that feels wrong on substance and whether the bias formalism is appropriate for that case.

## Graph and tooling sanity

- **Cycles / DAG:** follow **[DAG preparation](#dag-preparation-concentrated)**; do not duplicate checks here.
- **Schema vs runtime:** θ fields are schema-driven; BF / weight / strength may be tool-popular without all being strictly required—note gaps before batch jobs.

## Suggested exercise scenarios

Use these as **repeatable passes**. Prefer fixed example files so results are comparable across time and contributors.

| Scenario | Intent | Suggested starting graphs (examples) |
|----------|--------|--------------------------------------|
| Simple support chain | Direction of support is clear; posteriors should follow intuition. | `ontology/Bayesian_modeling/examples_bayesian/bayesian_example.json`; `ontology/examples/mini_example.json` |
| Conflicting or asymmetric evidence | Competing support; test aggregation and dominance of stronger BF. | `ontology/Bayesian_modeling/examples_bayesian/bayesian_trust.json`; `bayesian_curiosity.json` |
| Multi-bias / debiasing | Cumulative bias correction on BFs; baseline vs debiased. | `ontology/Bayesian_modeling/examples_bayesian/bayesian_curiosity.json` (multiple bias nodes); `bayesian_example.json` |
| Sparse evidence | Few edges; expect high sensitivity and wide uncertainty in narrative terms. | `ontology/examples/mini_example.json`; or a manually trimmed subgraph from a larger file |

If no bundled file fits, build a **minimal CSO JSON** with 3–5 nodes and log its path as the scenario fixture.

## Known failure modes (sanity, not exhaustive)

- **Directed cycles** on scored paths without the [DAG preparation](#dag-preparation-concentrated) policy—unstable or order-dependent updates.
- **Dependent evidence** modeled as independent combination—see math notes in [epistemic / transformation doc](epistemic_transformation_dag.md).
- **One dominant BF** or edge swamping the rest; check sensitivity.
- **Missing explicit BF** where heuristics fill in—results become harder to defend; prefer analyst-set BF for serious runs.

More discussion: [risk examples](../tools/bayesian/risk_examples.md), [Bayesian modeling rules](../tools/bayesian/bayesian_modeling_rules.md).

## Reporting template

For each scenario (or each ticket), record:

| Field | Notes |
|-------|--------|
| Scenario id / date / repo commit | |
| Input graph path(s) | `before_dag` / `after_dag` if applicable (see [DAG preparation](#dag-preparation-concentrated)); `before_strengthen` / `after_strengthen` if applicable |
| CSO build cost (optional) | Person-time; extraction/LLM calls to create v1; \|V\|/\|E\| at first valid graph |
| Graph summary | Target arguments, critical edges, priors/BFs worth mentioning |
| Preconditions | Validator ok; DAG policy (short); strengthening config + model if used |
| Strengthening mode & iterations | **Policy** vs **contextual**; # policy applications / # LLM calls; contextual: # calls, Δ statements vs cap |
| Strengthening cost (optional) | Tokens in/out, wall time, model id; note large prompts if graph grew |
| Baseline posteriors / VFE / predictability | From calculator output or exported JSON |
| Post-DAG posteriors (if applicable) | Diff vs pre-DAG |
| Post-strengthening metrics (if applicable) | Predictability / posteriors; stop reason |
| Debiased posteriors (if applicable) | vs baseline |
| Sensitivity / robustness | Table: parameter → baseline → perturbed → key posteriors |
| Interpretation | What you conclude for this graph |
| Limitations | Independence assumptions, missing data, heuristic BF, LLM edits |
| **Go / no-go** | Whether these numbers (and structure) are fit to cite in a report |

**Operational rule:** keep paired artifacts for **baseline**, **post-DAG** (if used), **post-strengthening** (if used), and **debiased** runs so comparisons stay auditable—aligned with [Bayesian inference workflow](bayesian_inference_workflow.md).

## Related documentation

- [Bayesian inference workflow](bayesian_inference_workflow.md)
- [DAG preparation, epistemic layer, and transformation layer](epistemic_transformation_dag.md)
- [Bayesian overview](bayesian_overview.md) · [Bayesian schema extensions](bayesian_schema.md)
- [Debiasing methodology](debiasing_methodology.md) · [Statement credibility](credibility.md)
- [Tools README](../tools/README.md) (Bayesian, debiasing, **strengthening**) · [Risk examples](../tools/bayesian/risk_examples.md)
