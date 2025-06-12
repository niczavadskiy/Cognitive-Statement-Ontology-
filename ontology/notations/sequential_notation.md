# Sequential Notation

## Purpose

The sequential notation is designed to analyze the chronological flow of statements and their relationships. It helps identify:
- The temporal sequence of statements
- How statements build upon each other
- The development of arguments over time

## Key Features

1. **Statement Objects**
   - Each statement is represented as a separate object
   - Statements can have temporal relationships
   - The `timestamp` property shows when statements were made

2. **Connection Types**
   - Statements can be connected based on:
     * Temporal sequence
     * Logical dependencies
     * Response relationships
   - Multiple connection types can exist between statements

3. **Visualization**
   - Statements are shown as nodes in chronological order
   - Connections show relationships between statements
   - Different line styles indicate different connection types
   - A dedicated "No Cognitive Biases" column is shown on the left for statements without bias connections

## Use Cases

- Analyzing the development of arguments
- Understanding statement dependencies
- Identifying response patterns
- Tracking the evolution of ideas

## Example

```json
{
  "statements": [
    {
      "id": "s1",
      "text": "The project will be completed on time",
      "timestamp": "2024-01-01T10:00:00",
      "responds_to": null
    },
    {
      "id": "s2",
      "text": "But we need more resources",
      "timestamp": "2024-01-01T10:05:00",
      "responds_to": "s1"
    }
  ]
}
```

## Visual Elements

### Nodes
- **Statements**: 
  - Displayed as white rectangles
  - Arranged in chronological order
  - Size indicates the number of connections
- **No Cognitive Biases**:
  - Displayed as a gray column on the left
  - Contains statements without bias connections

### Connections
- Solid lines show direct responses
- Dotted lines show logical dependencies
- Arrows indicate the direction of influence
- Line thickness shows the strength of the relationship

## Usage
```sh
python tools/render_graph.py <input_file> sequential
```

## Example
![Example of sequential notation](../examples/visualisations/example_sequential.png) 