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

## Input Data Format

The input JSON file should follow the cognitive ontology schema. See `schema.json` for details. 