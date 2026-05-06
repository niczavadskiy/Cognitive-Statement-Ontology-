# CSO debiasing tool

## Description

`cso_debiasing_tool.py` performs **epistemic (Bayes-factor) debiasing**: it uses links to **`cognitive_bias`** nodes (and weights) to **scale edge Bayes factors** and recompute posteriors. That is **not** the same as **structural / editorial debiasing** — rewriting statements or changing bias linkage in the graph; see [docs/cognitive_biases.md](../../docs/cognitive_biases.md) and the terminology block in [docs/debiasing_methodology.md](../../docs/debiasing_methodology.md).

## How it works

The script analyzes the graph, finds nodes linked to cognitive biases (via relations such as `related_to` per your pipeline), then **adjusts Bayes factors** on affected edges by multiplying by `(1 - bias_weight)` (and combines multiple biases multiplicatively).

### Correction formula

For a single bias:

```
corrected_bayes_factor = original_bayes_factor * (1 - bias_weight)
```

For multiple biases affecting the same correction (multiplicative):

```
correction_factor = ∏(1 - bias_weight_i)  over contributing biases
```

## Usage

### Command line

```bash
python cso_debiasing_tool.py "path/to/your/cso_file.json"
```

### Example

```bash
python cso_debiasing_tool.py "ontology/Bayesian_modeling/examples_bayesian/bayesian_example.json"
```

## Output file

The script writes a sibling file with suffix `_debiased.json` containing:

### Output structure (illustrative)

```json
{
  "debiasing_summary": {
    "original_file": "source_file.json",
    "debiasing_timestamp": "ISO_timestamp",
    "total_cognitive_biases_found": 5,
    "total_nodes_affected": 3,
    "total_arguments_recalculated": 4
  },
  "cognitive_biases_removed": [
    {
      "bias_id": "BC1-S5-B21",
      "bias_name": "Overconfidence Effect",
      "bias_weight": 0.8,
      "affected_nodes": ["stat5"],
      "correction_factor": 0.2
    }
  ],
  "node_corrections": [
    {
      "node_id": "stat1",
      "node_type": "statement",
      "node_text": "statement text...",
      "original_bayes_factors": [3.56, 3.24],
      "correction_factor": 0.04,
      "corrected_bayes_factors": [0.1424, 0.1296],
      "cognitive_biases_influencing": ["BC1-S5-B10", "BC1-S5-B7"],
      "bias_weights_applied": [0.8, 0.8]
    }
  ],
  "argument_recalculations": [
    {
      "argument_id": "arg1",
      "argument_text": "argument text...",
      "original_posterior": 0.998,
      "debiased_posterior": 0.915,
      "change_percentage": -8.3,
      "original_odds": 545.88,
      "debiased_odds": 10.8,
      "chains_affected": [
        {
          "chain": "stat1 → arg1",
          "original_bayes_factor": 3.56,
          "corrected_bayes_factor": 0.1424,
          "correction_factor": 0.04,
          "correction_reason": "Affected by multiple biases: Self-serving Bias, Illusory Superiority"
        }
      ]
    }
  ],
  "debiasing_methodology": {
    "description": "Bias correction methodology summary",
    "formula": "corrected_bayes_factor = original_bayes_factor * (1 - bias_weight)",
    "multiple_biases_formula": "correction_factor = ∏(1 - bias_weight_i)",
    "assumptions": [
      "Biases affect outgoing links from impacted nodes in a uniform way",
      "Bias weights represent how much influence to remove",
      "Multiple biases combine multiplicatively"
    ]
  }
}
```

## Recognized bias IDs (example set)

The script may tag biases such as:

- **BC1-S5-B21** — Overconfidence Effect  
- **BC1-S5-B13** — Optimism Bias  
- **BC1-S5-B8** — Illusion of Control  
- **BC1-S5-B10** — Self-serving Bias  
- **BC1-S5-B7** — Illusory Superiority  

(Exact behavior depends on graph content and tool version.)

## Sample console output

```
Summary:
   Biases found: 5
   Nodes affected: 3
   Arguments recalculated: 4

Biases removed:
   • Overconfidence Effect (weight: 0.8)
   ...

Argument probability changes:
   arg1: 0.998 → 0.915 (-8.3%)
   ...
```

## Testing

```bash
python test_debiasing_example.py
```

(`test_debiasing_example.py` uses a path you configure to an existing CSO JSON file.)

## Requirements

- Python 3.6+
- Standard library: `json`, `os`, `sys`, `pathlib`, `datetime`, `logging`
- Input: CSO JSON

## Integration

Use as a post-processing step after argumentation extraction, or embed in a larger CSO pipeline.
