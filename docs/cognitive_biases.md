# Working with Cognitive Biases

## Definition of Cognitive Biases

If you haven't encountered the task of identifying cognitive biases before, we recommend using the collection in [Bias Codex](https://www.biascodex.com/). For description in the Cognitive Statement Ontology (CSO), any set of cognitive biases can be used at the researcher's discretion.

Bias Codex provides:
- Detailed descriptions of various types of cognitive biases
- Examples of bias manifestations in real life
- Strategies for overcoming biases
- Categorization of biases by application areas

## Representation in Notations

Cognitive biases are represented in all three notations of the Cognitive Statement Ontology (CSO):

### Hierarchical notation (`hierarchical` in `render_graph.py`)
- Biases can be emphasized at the top of the layout
- Connected to statements through directed links
- Useful for tracing bias influence on statements

### Context Notation
- Biases are represented as columns
- Statements can be connected to multiple biases
- Allows analyzing the context of bias influence

### Bias-oriented Notation
- Biases are represented as colored blocks
- Statements are placed inside bias blocks
- Shows connections between biases through common statements

## Usage Recommendations

1. **Notation Selection**:
   - Use hierarchical notation for analyzing bias influence
   - Apply context notation for studying interrelationships
   - Choose bias-oriented notation for detailed analysis of specific biases

2. **Bias Identification**:
   - Start by identifying main biases in the research area
   - Use Bias Codex to find and describe biases
   - Document connections between biases and statements

3. **Influence Analysis**:
   - Track direct and indirect bias influences
   - Analyze relationships between different biases
   - Evaluate influence strength through number of connections 


## New properties for cognitive_bias nodes

### manifestation_of_ones_thought
- **Description:** 1 if the author manifests this cognitive bias in their own thinking or writing; 0 if not.
- **Applicable only to nodes of type cognitive_bias.**

### fixation_of_someones_bias
- **Description:** 1 if the author identifies, points out, or records someone else's cognitive bias, or describes behavior involving a bias and marks it as erroneous or problematic; 0 if not.
- **Applicable only to nodes of type cognitive_bias.**

### Possible value combinations
Allowed value combinations for cognitive_bias nodes:
- **manifestation_of_ones_thought = 1, fixation_of_someones_bias = 0** — The author manifests this cognitive bias in their own thinking or writing.
  - Example: Author writes "Everyone knows that women are worse drivers" (the author themselves expresses this stereotype).
- **manifestation_of_ones_thought = 0, fixation_of_someones_bias = 1** — The author identifies or points out someone else's cognitive bias, or describes behavior involving a bias and marks it as erroneous or problematic. **For this situation, it is characteristic that the author must necessarily indicate in their statement that this is an error.**
  - Example: Author writes "My colleague keeps saying 'everyone knows women are worse drivers' — this is a stereotype" (the author identifies the bias in another's statement).
  - Example: Author writes "This argument is flawed because it relies on confirmation bias" (the author points out the bias in reasoning).
- **manifestation_of_ones_thought = 1, fixation_of_someones_bias = 1** — The author both manifests the bias and recognizes it as problematic.
  - Example: Author writes "Everyone knows that women are worse drivers... wait, that's a stereotype I'm reproducing right now" (the author manifests the bias and also recognizes it as problematic).
- **manifestation_of_ones_thought = 0, fixation_of_someones_bias = 0** — The author describes behavior that may involve a cognitive bias but does not manifest it themselves and does not explicitly identify it as a bias.
  - Example: Author writes "Kornilova and her husband continue to communicate and forgive each other despite the crime and sentence" (describes behavior that may involve Sunk Cost Fallacy but does not manifest or analyze it as a bias).

**Key points for experts:**
- `fixation_of_someones_bias = 1` means the author critically evaluates the bias, points out its erroneous nature, or marks it as problematic. **The author must explicitly indicate that this is an error or problematic behavior.**
- `manifestation_of_ones_thought = 1` means the author themselves uses or demonstrates this bias in their own thinking or writing.
- If the author simply describes the bias neutrally, use `fixation_of_someones_bias = 0`.
- If the author criticizes the bias or explicitly marks it as erroneous, use `fixation_of_someones_bias = 1`.