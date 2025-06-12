# Definition and Scope

Cognitive Statement Ontology is a formal structure for representing, analyzing, and visualizing statements, arguments, cognitive biases, and their interrelationships. This ontology is designed to describe statements in the form of text of any size. This ontology is primarily intended for describing existing (recorded) statements, arguments, and other objects. Secondarily, it is used for finding causal relationships, sources of errors, understanding the structure of correct and incorrect statements, and the dynamics of these structures. The ultimate goal of using the statement ontology is to improve the statements of the analyzed actor.

## Application Areas

- Education and critical thinking development
- Cognitive therapy and self-reflection
- Cognitive sciences

See more applications: [use_cases.md](use_cases.md)

The ontology allows modeling complex reasoning, identifying the influence of biases, and tracking the sources of statements. For more information on working with cognitive biases, see [cognitive_biases.md](cognitive_biases.md).

The ontology description is universal but can be represented in three complementary notations, depending on the analysis purpose. For notation comparison, see [comparison.md](comparison.md):

[Context-oriented notation](context_notation.md)
Shows which quotes and which biases formed a given statement. A quote object can have an `author` property, which is filled with the value `self` (if the statement author matches the quote author) or the quote author's name.

[Sequential notation](sequential_notation.md)
A logical chain of statements leads to a conclusion—an argument, with additional undirected connections to biases.

[Bias-oriented notation](bias_notation.md)
Focuses on which groups of statements each cognitive bias supports and how biases are interconnected.