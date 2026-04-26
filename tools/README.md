# Cognitive Ontology Tools

This directory contains tools for visualizing and analyzing cognitive ontology data.

## Setup

1. Install Graphviz system package:
   - Windows: Download and install from https://graphviz.org/download/
   - Linux (Ubuntu/Debian): `sudo apt-get install graphviz`
   - macOS: `brew install graphviz`

2. Install Python dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Available Tools

### Graph Visualization (`render_graph.py`)

This tool creates visualizations of cognitive ontology data using different notations.

#### Usage

```sh
python render_graph.py <input_file> [notation_type]
```

Where:
- `<input_file>` is the path to a JSON file containing cognitive ontology data
- `[notation_type]` is optional and can be one of:
  - `context` (default) - shows statements in the context of cognitive biases
  - `bias` - focuses on relationships between cognitive biases
  - `sequential` - linear representation of statements and their connections

#### Examples

```sh
# Create a context-oriented visualization
python render_graph.py ../ontology/examples/mini_example_2.json context

# Create a bias-oriented visualization
python render_graph.py ../ontology/examples/mini_example_2.json bias

# Create a sequential visualization
python render_graph.py ../ontology/examples/mini_example_2.json sequential
```

#### Output

The tool generates PNG files in the `visualisations/` directory. The output filename is based on the input filename and notation type.

### Bayesian modeling tools (`ontology/Bayesian_modeling/bayesian_tools/`)

Probabilistic extensions for CSO graph assessment.

#### Main scripts

- `bayesian_validator.py` — validates CSO JSON with Bayesian schema extensions
- `bayesian_calculator.py` — computes posterior updates
- `cso_debiasing_tool.py` — applies bias correction to Bayes factors and recalculates posteriors

#### Usage (from repository root)

```sh
python ontology/Bayesian_modeling/bayesian_tools/bayesian_validator.py <path_to_cso_json>
python ontology/Bayesian_modeling/bayesian_tools/test_bayesian_system.py
python ontology/Bayesian_modeling/bayesian_tools/cso_debiasing_tool.py <path_to_cso_json>
```

Alternatively, run scripts from `ontology/Bayesian_modeling/bayesian_tools/` and pass paths relative to that directory (see that folder’s README).

#### Notes

- The Bayesian layer is optional but recommended for quantitative credibility analysis.
- Keep the structural ontology valid first, then run probabilistic and debiasing stages.

Documentation: [Bayesian tools README](../ontology/Bayesian_modeling/bayesian_tools/README.md), [docs: Bayesian overview](../docs/bayesian_overview.md).

## Input Data Format

The input JSON file should follow the cognitive ontology schema. See `schema.json` for details.

## Supported File Formats

The system supports the following input file formats:
- `.txt` - Plain text files
- `.docx` - Microsoft Word documents (requires python-docx)
- `.doc` - Legacy Microsoft Word documents (requires pywin32 on Windows)
- `.fb2` - FictionBook 2.0 format (requires lxml) 