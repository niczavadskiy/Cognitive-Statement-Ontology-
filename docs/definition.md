# Definition and Scope

Cognitive Statement Ontology (CSO) is a formal structure for representing and analyzing statements, arguments, cognitive biases, and their interrelationships as a **machine-readable graph**, with **optional** visualization for inspection. This ontology is designed to describe statements in the form of text of any size. This ontology is primarily intended for describing existing (recorded) statements, arguments, and other objects. Secondarily, it is used for finding causal relationships, sources of errors, understanding the structure of correct and incorrect statements, and the dynamics of these structures. The ultimate goal of using the statement ontology is to improve the statements of the analyzed actor.

## Application Areas

- Education and critical thinking development
- Cognitive therapy and self-reflection
- Cognitive sciences

See more applications: [use_cases.md](use_cases.md)

The ontology allows modeling complex reasoning, identifying the influence of biases, and tracking the sources of statements. For more information on working with cognitive biases, see [cognitive_biases.md](cognitive_biases.md).

The ontology description is universal but can be represented in three complementary notations, depending on the analysis purpose. For notation comparison, see [comparison.md](comparison.md).

**Context-oriented notation** ([`ontology/notations/context_notation.md`](../ontology/notations/context_notation.md))  
Shows which quotes and which biases shaped a given statement. A quotation node may include an `author` field: use `self` when the quotation author matches the statement author, or the author's name otherwise.

**Sequential notation** ([`ontology/notations/sequential_notation.md`](../ontology/notations/sequential_notation.md))  
A logical chain of statements leads to a conclusion (an argument), with additional links to biases.

**Bias-oriented notation** ([`ontology/notations/bias_notation.md`](../ontology/notations/bias_notation.md))  
Emphasizes which statements each bias is associated with and how biases connect through shared statements.

Rendering: `tools/render/render_graph.py` with `context`, `sequential`, or `bias` (and `hierarchical`) modes — see [tools README](../tools/README.md).