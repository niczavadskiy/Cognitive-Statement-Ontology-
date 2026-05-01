#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verbose test driver for the CSO Bayesian-style tooling.
Prints detailed information for each scenario, inputs, and outputs.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from bayesian_calculator import BayesianCalculator, interpret_bayes_factor
from bayesian_validator import BayesianValidator
from technical_rules import BayesianModelingRules


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_subsection(title):
    """Print a subsection header."""
    print(f"\n--- {title} ---")


def test_basic_calculations():
    """Exercise core calculator functions with verbose logging."""
    print_section("TEST 1: Basic Bayesian calculations")

    print("""
This block exercises the reference calculator:
1. Bayes factor (BF)
2. Posterior probability
3. Aggregating multiple evidence items
""")

    calculator = BayesianCalculator()

    print_subsection("Test 1.1: Bayes factor")
    print("INPUT:")
    print("  - prior_prob = 0.7")
    print("  - likelihood_h1 = 0.8 (likelihood under H1)")
    print("  - likelihood_h0 = 0.3 (likelihood under H0)")

    bf = calculator.calculate_bayes_factor(0.7, 0.8, 0.3)

    print(f"\nOUTPUT:")
    print(f"  - Bayes factor: {bf:.4f}")
    print(f"  - Label: {interpret_bayes_factor(bf)}")
    print(f"  - BF = P(E|H1) / P(E|H0) = {0.8} / {0.3} = {bf:.4f}")

    print_subsection("Test 1.2: Posterior probability")
    print("INPUT:")
    print(f"  - prior_prob = 0.6")
    print(f"  - bayes_factor = {bf:.4f} (from previous step)")

    posterior = calculator.calculate_posterior_probability(0.6, bf)

    print(f"\nOUTPUT:")
    print(f"  - Posterior: {posterior:.4f}")
    print(f"  - Delta: {0.6} → {posterior:.4f} ({posterior - 0.6:+.4f})")
    print(f"  - P(H|E) = P(H)*BF / (P(H)*BF + P(~H))")

    print_subsection("Test 1.3: Multiple evidences")
    print("INPUT:")
    print("  - prior_prob = 0.5")
    print("  - Evidence list:")
    evidence = [
        {'bayes_factor': 3.0, 'weight': 0.8},
        {'bayes_factor': 2.0, 'weight': 0.6},
        {'bayes_factor': 1.5, 'weight': 0.4}
    ]
    for i, ev in enumerate(evidence, 1):
        print(f"    {i}. BF={ev['bayes_factor']}, weight={ev['weight']}")

    final_prob = calculator.aggregate_multiple_evidences(0.5, evidence)

    print(f"\nOUTPUT:")
    print(f"  - Aggregated probability: {final_prob:.4f}")
    print(f"  - Delta: 0.500 → {final_prob:.4f} ({final_prob - 0.5:+.4f})")

    print("\n✅ Test 1 completed.")


def test_validation():
    """Validation on a deliberately broken ontology."""
    print_section("TEST 2: Data validation")

    print("""
Validate a synthetic ontology that contains intentional errors
to ensure the validator surfaces them.
""")

    test_ontology = {
        "nodes": [
            {
                "id": "test_stmt",
                "type": "statement",
                "text": "Test statement",
                "prior_probability": 0.7
            },
            {
                "id": "test_arg",
                "type": "argument",
                "text": "Test argument",
                "prior_probability": 0.8,
                "posterior_probability": 1.2  # invalid: > 1.0
            }
        ],
        "edges": [
            {
                "source": "test_arg",
                "target": "test_stmt",
                "relation": "supports",
                "weight": -0.5,  # invalid: negative
                "bayes_factor": 2.5
            }
        ],
        "metadata": {
            "id_author": "test",
            "name_author": "Test Author",
            "date_time": "2024-01-15T10:00:00Z",
            "source": "Test",
            "version": "2.0.0"
        }
    }

    print_subsection("Fixture")
    print("NODES:")
    for node in test_ontology['nodes']:
        print(f"  - {node['id']} ({node['type']})")
        print(f"    prior_prob: {node.get('prior_probability', 'N/A')}")
        if 'posterior_probability' in node:
            print(f"    posterior_prob: {node.get('posterior_probability')} ⚠️ invalid: > 1.0")

    print("\nEDGES:")
    for edge in test_ontology['edges']:
        print(f"  - {edge['source']} → {edge['target']}")
        print(f"    relation: {edge['relation']}")
        print(f"    weight: {edge['weight']} ⚠️ invalid: negative")
        print(f"    bayes_factor: {edge.get('bayes_factor', 'N/A')}")

    print_subsection("Validator output")
    validator = BayesianValidator()
    is_valid, errors = validator.validate_ontology(test_ontology)

    print(f"STATUS: {'✅ VALID' if is_valid else '❌ INVALID (expected)'}")

    if errors:
        print(f"\nISSUES: {len(errors)}")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")

    report = validator.generate_validation_report(test_ontology)
    stats = report['statistics']

    print_subsection("Ontology statistics")
    print(f"  - Nodes: {stats['total_nodes']}")
    print(f"  - Edges: {stats['total_edges']}")
    print(f"  - Node types: {stats['node_types']}")

    print("\n✅ Test 2 completed (errors detected as expected).")


def test_technical_rules():
    """Technical rules helpers."""
    print_section("TEST 3: Technical rules")

    print("""
Exercises:
1. Cycle detection
2. Probability aggregation
3. Uncertainty intervals
""")

    rules = BayesianModelingRules()

    print_subsection("Test 3.1: Cycle detection")
    print("INPUT: directed cycle A → B → C → A")
    test_edges = [
        {"source": "A", "target": "B", "relation": "supports"},
        {"source": "B", "target": "C", "relation": "supports"},
        {"source": "C", "target": "A", "relation": "supports"}
    ]

    cycles = rules.detect_cycles(test_edges)
    print(f"\nOUTPUT:")
    print(f"  - Cycle count: {len(cycles)}")
    if cycles:
        for i, cycle in enumerate(cycles, 1):
            print(f"  - Cycle {i}: {' → '.join(cycle)}")

    print_subsection("Test 3.2: Probability aggregation")
    probs = [0.7, 0.3, 0.8]
    weights = [0.6, 0.3, 0.1]

    print("INPUT:")
    print(f"  - Probabilities: {probs}")
    print(f"  - Weights: {weights}")

    geometric_result = rules.calculate_aggregated_probability(
        probs, weights, method='weighted_geometric'
    )
    log_odds_result = rules.calculate_aggregated_probability(
        probs, weights, method='log_odds'
    )

    print(f"\nOUTPUT:")
    print(f"  - Weighted geometric: {geometric_result:.4f}")
    print(f"  - Log-odds: {log_odds_result:.4f}")

    print_subsection("Test 3.3: Uncertainty intervals")
    print("INPUT:")
    print("  - Probability: 0.7")
    print("  - Confidence: 95%")

    lower, upper = rules.apply_uncertainty_intervals(0.7, confidence_level=0.95)

    print(f"\nOUTPUT:")
    print(f"  - 95% interval: [{lower:.4f}, {upper:.4f}]")
    print(f"  - Width: {upper - lower:.4f}")

    print("\n✅ Test 3 completed.")


def test_example_files():
    """Validate shipped Bayesian example JSON files."""
    print_section("TEST 4: Example JSON files")

    print("""
Validates every `*.json` under ontology/Bayesian_modeling/examples_bayesian/.
""")

    repo_root = Path(__file__).resolve().parent.parent.parent
    examples_dir = repo_root / "ontology" / "Bayesian_modeling" / "examples_bayesian"
    print(f"\nExamples directory: {examples_dir}")

    if not examples_dir.exists():
        print("❌ Directory not found.")
        return

    validator = BayesianValidator()
    example_files = list(examples_dir.glob("*.json"))

    print(f"Files found: {len(example_files)}\n")

    for i, example_file in enumerate(example_files, 1):
        print_subsection(f"File {i}/{len(example_files)}: {example_file.name}")
        print(f"Path: {example_file}")

        is_valid, errors = validator.validate_file(str(example_file))

        if is_valid:
            print("RESULT: ✅ Valid")

            with open(example_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            nodes = data.get('nodes', [])
            edges = data.get('edges', [])

            node_types = {}
            for node in nodes:
                node_type = node.get('type', 'unknown')
                node_types[node_type] = node_types.get(node_type, 0) + 1

            prior_probs = [n.get('prior_probability') for n in nodes if 'prior_probability' in n]
            posterior_probs = [n.get('posterior_probability') for n in nodes if 'posterior_probability' in n]
            bayes_factors = [e.get('bayes_factor') for e in edges if 'bayes_factor' in e and e['bayes_factor'] is not None]

            print("\nSTATS:")
            print(f"  Nodes: {len(nodes)}")
            for node_type, count in node_types.items():
                print(f"    - {node_type}: {count}")

            print(f"  Edges: {len(edges)}")

            if prior_probs:
                print(f"  Priors:")
                print(f"    - Count: {len(prior_probs)}")
                print(f"    - Mean: {sum(prior_probs)/len(prior_probs):.4f}")
                print(f"    - Min: {min(prior_probs):.4f}, Max: {max(prior_probs):.4f}")

            if posterior_probs:
                print(f"  Posteriors:")
                print(f"    - Count: {len(posterior_probs)}")
                print(f"    - Mean: {sum(posterior_probs)/len(posterior_probs):.4f}")
                print(f"    - Min: {min(posterior_probs):.4f}, Max: {max(posterior_probs):.4f}")

            if bayes_factors:
                finite_bfs = [bf for bf in bayes_factors if bf != float('inf')]
                if finite_bfs:
                    print(f"  Bayes factors:")
                    print(f"    - Count: {len(finite_bfs)}")
                    print(f"    - Mean: {sum(finite_bfs)/len(finite_bfs):.4f}")
                    print(f"    - Min: {min(finite_bfs):.4f}, Max: {max(finite_bfs):.4f}")

                    weak = sum(1 for bf in finite_bfs if 1 <= bf < 3)
                    moderate = sum(1 for bf in finite_bfs if 3 <= bf < 10)
                    strong = sum(1 for bf in finite_bfs if bf >= 10)
                    print(f"    - Weak (1-3): {weak}")
                    print(f"    - Moderate (3-10): {moderate}")
                    print(f"    - Strong (≥10): {strong}")
        else:
            print("RESULT: ❌ Invalid")
            print(f"Issues: {len(errors)}")
            for j, error in enumerate(errors[:5], 1):
                print(f"  {j}. {error}")
            if len(errors) > 5:
                print(f"  ... {len(errors) - 5} more")

    print("\n✅ Test 4 completed.")


def test_full_model_update():
    """Full-graph probability refresh."""
    print_section("TEST 5: Full model update")

    print("""
Runs `update_node_probabilities` on a toy graph.
""")

    test_nodes = [
        {
            "id": "evidence1",
            "type": "argument",
            "text": "Strong evidence",
            "prior_probability": 0.8
        },
        {
            "id": "evidence2",
            "type": "argument",
            "text": "Weak evidence",
            "prior_probability": 0.4
        },
        {
            "id": "conclusion",
            "type": "statement",
            "text": "Main conclusion",
            "prior_probability": 0.5
        }
    ]

    test_edges = [
        {
            "source": "evidence1",
            "target": "conclusion",
            "relation": "supports",
            "strength": 0.8,
            "weight": 0.9
        },
        {
            "source": "evidence2",
            "target": "conclusion",
            "relation": "supports",
            "strength": 0.6,
            "weight": 0.3
        }
    ]

    print_subsection("Before")
    print("NODES:")
    for node in test_nodes:
        if 'prior_probability' in node:
            print(f"  - {node['id']} ({node['type']}): prior = {node['prior_probability']}")

    print("\nEDGES:")
    for edge in test_edges:
        print(f"  - {edge['source']} → {edge['target']}")
        print(f"    relation: {edge['relation']}, strength: {edge['strength']}, weight: {edge['weight']}")

    calculator = BayesianCalculator()
    updated_nodes, updated_edges = calculator.update_node_probabilities(test_nodes, test_edges)

    print_subsection("After")
    print("NODES:")
    for node in updated_nodes:
        node_id = node['id']
        node_type = node['type']
        prior = node.get('prior_probability', 'N/A')

        if 'posterior_probability' in node:
            posterior = node['posterior_probability']
            change = posterior - prior if isinstance(prior, (int, float)) else 0
            print(f"  - {node_id} ({node_type}):")
            print(f"    prior: {prior:.4f} → posterior: {posterior:.4f}")
            print(f"    delta: {change:+.4f}")
        else:
            print(f"  - {node_id} ({node_type}): prior = {prior} (unchanged)")

    print("\nEDGES (with synthesized Bayes factors where applicable):")
    for edge in updated_edges:
        if 'bayes_factor' in edge:
            bf = edge['bayes_factor']
            interpretation = interpret_bayes_factor(bf)
            print(f"  - {edge['source']} → {edge['target']}")
            print(f"    BF: {bf:.4f} ({interpretation})")

    print("\n✅ Test 5 completed.")


def main():
    print("\n" + "=" * 80)
    print("  🧠 CSO BAYESIAN SYSTEM — VERBOSE TEST")
    print("=" * 80)
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Python: {sys.version.split()[0]}")
    print("=" * 80)

    try:
        test_basic_calculations()
        test_validation()
        test_technical_rules()
        test_example_files()
        test_full_model_update()

        print("\n" + "=" * 80)
        print("  ✅ ALL TEST BLOCKS FINISHED")
        print("=" * 80)

    except Exception as e:
        print("\n" + "=" * 80)
        print(f"  ❌ TEST FAILED: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
