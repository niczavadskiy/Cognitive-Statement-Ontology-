# CSO Rules

## Basic Rules

1. **Identifier Uniqueness**: Each object (node) must have a unique `id`.
2. **Typing**: Each node must have a type: `statement`, `argument`, `cognitive_bias`, `quotation`, `question`.
3. **Relations**: All relationships between objects are defined through edges with a type (`relation`).
4. **Credibility**: Use `credibility` on statements when recording expert assessment; the schema default is `gray` if omitted.
5. **Flexibility and Extensibility**: New types and relationships can be added as needed.
6. **Visualization**: Different notations are used for structure analysis (see respective files).

## JSON File Rules

### Required Metadata Fields

1. **Ontology Metadata**
   - `id_author` (string): Unique identifier of the ontology author (pattern: `^[a-zA-Z0-9_-]+$`)
   - `name_author` (string): Full name of the ontology author
   - `date_time` (string): When the ontology was created or last modified (ISO 8601 format)
   - `source` (string): Source or origin of the ontology
   - `version` (string): Version of the schema used (pattern: `^[0-9]+\.[0-9]+\.[0-9]+$`, default: "1.0.2")
   - These fields are required and must be present in the metadata section
   - Each ontology can have only one set of these metadata fields

### Optional Metadata Fields

1. **Additional Metadata**
   - `title` (string): Title of the cognitive graph
   - `description` (string): Description of the cognitive graph
   - `expert` (string): Name of the LLM model used for processing this cognitive graph
   - `created_at` (string): When the graph was created (ISO 8601 format)
   - `updated_at` (string): When the graph was last updated (ISO 8601 format)

### Required Fields for Nodes

1. **All Node Types**
   - `id` (string): unique identifier (pattern: `^[a-zA-Z0-9_-]+$`)
   - `type` (string): must be one of "statement", "argument", "cognitive_bias", "quotation", "question"
   - `text` (string): content of the node (minLength: 1)

2. **Cognitive Bias Specific Fields**
   - `manifestation_of_ones_thought` (integer): 1 if the author manifests this cognitive bias, 0 otherwise
   - `fixation_of_someones_bias` (integer): 1 if the author records someone else's cognitive bias, 0 otherwise

3. **Optional Node Fields**
   - `credibility` (string): credibility level - "green", "yellow", "red", or "gray" (default: "gray")
   - `author` (string): author of the statement or quotation
   - `timestamp` (string): when the statement was made or recorded (ISO 8601 format)
   - `metadata` (object): additional metadata about the node

### Node Metadata Fields

1. **Node Metadata Object**
   - `tags` (array): tags for categorizing the node (items: string)
   - `confidence` (number): confidence level in the statement's accuracy (0-1)
   - `notes` (string): additional notes or context

### Edge Types

1. **Required Edge Fields**
   - `source` (string): ID of the source node
   - `target` (string): ID of the target node
   - `relation` (string): type of relationship between nodes

2. **Valid Relation Types**
   - `supports`: one node supports another
   - `contradicts`: one node contradicts another
   - `influences`: one node influences another
   - `responds_to`: one node responds to another
   - `quotes`: one node quotes another
   - `cites`: one node cites another
   - `related_to`: nodes are related to each other
   - `answered_by`: question → statement/argument (the statement/argument answers the question)
   - `answers`: statement/argument → question (the statement/argument answers the question)
   - `asks_about`: question → statement/argument (the question asks about the statement/argument)

3. **Optional Edge Fields**
   - `strength` (number): strength of the relationship (0-1)
   - `metadata` (object): additional metadata about the relationship

### Edge Metadata Fields

1. **Edge Metadata Object**
   - `context` (string): context of the relationship
   - `timestamp` (string): when the relationship was established (ISO 8601 format)

### Credibility Levels

1. **Statement Credibility**
   - `green` - highly credible statement
   - `yellow` - moderately credible statement
   - `red` - low credibility statement
   - `gray` - unknown or unverified credibility (default)

### Connection Rules

1. **General Rules**
   - All relationships must be defined through edges
   - Edge source and target must reference existing node IDs
   - No self-references (source cannot equal target)
   - No circular references in directed relationships

2. **Node Type Relationships**
   - Any node type can connect to any other node type
   - Relationships are defined by the `relation` field in edges
   - Multiple relationships can exist between the same nodes

3. **Argument Direction Rules**
   - Arguments must ALWAYS be the target (never source) in relationships
   - EXCEPTION: Arguments can be sources when connecting to questions (bidirectional)
   - Statements, cognitive biases, quotations, or questions can point TO arguments
   - Arguments cannot point to other nodes (except questions - arguments are always endpoints otherwise)
   - Example: `{"source": "stmt1", "target": "arg1", "relation": "supports"}`
   - Example (with question): `{"source": "arg1", "target": "quest1", "relation": "answers"}`

### Validation Rules

1. **Required Fields**
   - All required fields must be present
   - Fields must have correct types as defined in schema
   - Arrays must contain valid items of specified types

2. **ID References**
   - All referenced IDs in edges must exist in nodes array
   - IDs must be unique across all nodes
   - IDs must follow the pattern `^[a-zA-Z0-9_-]+$`

3. **Data Types**
   - String fields must be non-empty where required
   - Number fields must be within specified ranges (0-1 for strength, confidence)
   - Date-time fields must be in ISO 8601 format
   - Enum fields must contain only allowed values

4. **Schema Compliance**
   - All objects must follow the JSON schema structure
   - No additional properties are allowed unless specified
   - All required properties must be present

### Question Node Type

1. **Question Properties**
   - Questions do NOT participate in argument probability calculations
   - Questions can have bidirectional connections with arguments (unlike other node types)
   - Questions can connect to statements, cognitive biases, quotations, and other questions
   - Questions do NOT require `prior_probability` or `posterior_probability`
   - Questions can have optional fields: `author`, `timestamp`, `credibility`, `metadata`

2. **Question Relationships**
   - `answered_by`: question → statement/argument (the statement/argument answers the question)
   - `answers`: statement/argument → question (the statement/argument answers the question)
   - `asks_about`: question → statement/argument (the question asks about the statement/argument)
   - `responds_to`: question → question/statement (the question is a response to another question/statement)
   - `influences`: question → statement/argument (the question influences reasoning)
   - `related_to`: general relationship

3. **Question Examples**
   ```json
   {
     "id": "quest1",
     "type": "question",
     "text": "What evidence supports this claim?"
   }
   ```
   
   ```json
   {
     "source": "stmt5",
     "target": "quest1",
     "relation": "answers"
   }
   ```