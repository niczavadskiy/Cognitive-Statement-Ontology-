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

### Hierarchical Notation
- Biases are displayed at the top of the graph
- Connected to statements through directed links
- Allows tracking the influence of biases on statements

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
- **Description:** 1 if the author manifests this cognitive bias; 0 if not.
- **Applicable only to nodes of type cognitive_bias.**

### fixation_of_someones_bias
- **Description:** 1 if the author records someone else's cognitive bias; 0 if not.
- **Applicable only to nodes of type cognitive_bias.**

### Possible value combinations
Allowed value combinations for cognitive_bias nodes:
  - manifestation_of_ones_thought = 1, fixation_of_someones_bias = 0 — the author manifests the bias but does not record it as a bias.
    Example: Author writes "Everyone knows that women are worse drivers" (manifests stereotype) but doesn't recognize it as a cognitive bias.
  - manifestation_of_ones_thought = 0, fixation_of_someones_bias = 1 — the author records someone else's bias but does not manifest it themselves.
    Example: Author writes "My colleague keeps saying 'everyone knows women are worse drivers' — this is a stereotype" (notices bias in others but doesn't manifest it).
  - manifestation_of_ones_thought = 1, fixation_of_someones_bias = 1 — the author both manifests and records the bias.
    Example: Author writes "Everyone knows that women are worse drivers... wait, that's a stereotype I'm reproducing right now" (manifests bias AND recognizes it).
  - manifestation_of_ones_thought = 0, fixation_of_someones_bias = 0 — the author describes behavior that may involve cognitive bias but does not manifest it themselves and does not explicitly identify it as a bias.
    Example: Author writes "Kornilova and her husband continue to communicate and forgive each other despite the crime and sentence" (describes behavior that may involve Sunk Cost Fallacy but doesn't manifest or analyze it as bias).