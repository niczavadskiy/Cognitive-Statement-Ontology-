# CSO Rules

## Basic Rules

1. **Identifier Uniqueness**: Each object (node) must have a unique `id`.
2. **Typing**: Each node must have a type: `statement`, `argument`, `cognitive_bias`, `quotation`.
3. **Relations**: All relationships between objects are defined through edges with a type (`relation`).
4. **Credibility**: Statements must have a credibility level (`credibility`).
5. **Flexibility and Extensibility**: New types and relationships can be added as needed.
6. **Visualization**: Different notations are used for structure analysis (see respective files).

## JSON File Rules

### Required Fields for Nodes

1. **Statement**
   - `id` (string): unique identifier
   - `type` (string): must be "statement"
   - `text` (string): statement content
   - `credibility` (string): credibility level
   - `source` (string): statement source
   - `timestamp` (string): creation time
   - `biases` (array): list of bias IDs
   - `quotes` (array): list of quote IDs
   - `arguments` (array): list of argument IDs
   - `leads_to` (array): list of statement IDs this leads to

2. **Argument**
   - `id` (string): unique identifier
   - `type` (string): must be "argument"
   - `text` (string): argument content
   - `statements` (array): list of statement IDs
   - `leads_to` (array): list of statement IDs this leads to

3. **Cognitive Bias**
   - `id` (string): unique identifier
   - `type` (string): must be "cognitive_bias"
   - `name` (string): bias name
   - `description` (string): bias description
   - `statements` (array): list of statement IDs
   - `related_biases` (array): list of related bias IDs

4. **Quotation**
   - `id` (string): unique identifier
   - `type` (string): must be "quotation"
   - `text` (string): quote content
   - `author` (string): quote author
   - `source` (string): quote source
   - `timestamp` (string): quote time
   - `statements` (array): list of statement IDs

### Specific Fields

1. **Statement**
   - `credibility` can be:
     * `true` - true statement
     * `false` - false statement
     * `controversial` - controversial statement
     * `unknown` - unknown credibility

2. **Quotation**
   - `author` can be:
     * `self` - if the statement author is quoting themselves
     * Author's name - if quoting another person
     * `unknown` - if author is unknown

### Connection Rules

1. **Statement to Statement**
   - One statement can lead to multiple statements
   - One statement can be led to by multiple statements
   - Statements cannot lead to themselves
   - Statements cannot form cycles

2. **Statement to Bias**
   - One statement can be influenced by multiple biases
   - One bias can influence multiple statements
   - All statements must be connected to at least one bias

3. **Statement to Quote**
   - One statement can be based on multiple quotes
   - One quote can be used in multiple statements
   - All statements must be based on at least one quote

4. **Statement to Argument**
   - One statement can be part of multiple arguments
   - One argument can contain multiple statements
   - All statements must be part of at least one argument

### Edge Types

1. **Directed Edges**
   - `leads_to`: statement leads to another statement
   - `based_on`: statement is based on a quote
   - `part_of`: statement is part of an argument

2. **Undirected Edges**
   - `influenced_by`: statement is influenced by a bias
   - `related_to`: bias is related to another bias

### Validation Rules

1. **Required Fields**
   - All required fields must be present
   - Fields must have correct types
   - Arrays must contain valid IDs

2. **ID References**
   - All referenced IDs must exist
   - IDs must be unique across all nodes
   - IDs must be strings

3. **Relationships**
   - All relationships must be valid
   - No circular references
   - No self-references 