# Context-oriented Notation

## Purpose

The context-oriented notation is designed to analyze the sources and influences that shaped a particular statement. It helps identify:
- Which quotes influenced the statement
- Which cognitive biases affected the reasoning
- The relationship between the statement author and quote authors

## Key Features

1. **Quote Objects**
   - Each quote is represented as a separate object
   - Quotes can have an `author` property
   - The `author` property can be:
     * `self` - if the statement author is quoting themselves
     * Author's name - if quoting another person

2. **Bias Connections**
   - Biases are connected to statements they influenced
   - Multiple biases can be connected to a single statement
   - Bias connections show the cognitive patterns in reasoning
   - Statements without bias connections are placed in a dedicated "No Cognitive Biases" column

3. **Visualization**
   - Statements are shown as nodes
   - Quotes are connected to statements they influenced
   - Biases are connected to statements they affected
   - Author relationships are shown through quote properties
   - A dedicated "No Cognitive Biases" column is shown on the left for statements without bias connections

## Use Cases

- Analyzing the sources of arguments
- Identifying cognitive biases in reasoning
- Understanding the influence of external sources
- Tracking self-referential statements

## Example

```json
{
  "statements": [
    {
      "id": "s1",
      "text": "The project will be completed on time",
      "quotes": ["q1"],
      "biases": ["optimism_bias"]
    }
  ],
  "quotes": [
    {
      "id": "q1",
      "text": "We have enough resources",
      "author": "self"
    }
  ]
}
```

## Visual Elements

### Nodes
- **Cognitive Biases**: 
  - Displayed as colored columns
  - Each bias is assigned a unique pastel color from a set of 12 colors
  - Colors repeat in a cycle if there are more than 12 biases
- **No Cognitive Biases**:
  - Displayed as a gray column on the left
  - Contains statements without bias connections
- **Statements**:
  - Displayed in corresponding columns based on bias connections
  - Placed in white rectangles within columns
  - If a statement is connected to multiple biases:
    - Text is displayed in the rightmost rectangle
    - Empty rectangles are created in other columns
    - Rectangles are connected with dotted lines
- **Quotes**: 
  - Displayed in the right "CONTEXT" block
  - Evenly distributed vertically

### Connections
- Dotted lines between rectangles of the same statement
- Placement of a statement in a bias column indicates a connection
- Lines from statements to quotes
- Quotes are connected to the rightmost rectangle of the statement

## Features
- Visual separation of main content and context
- Color differentiation of biases
- Clear representation of connections between statements and biases
- Compact context representation
- The diagram can be sorted by quote chronology or statement chronology depending on the researcher's needs

## Usage
```sh
python tools/render_graph.py <input_file> context
```

## Example
![Example of context-oriented notation](../examples/visualisations/example_context.png) 