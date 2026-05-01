#!/usr/bin/env python3
"""
Test script for the Bayesian CSO system

This script demonstrates the functionality of the new Bayesian extensions
to the Cognitive Ontology framework.
"""

import json
import sys
from pathlib import Path

# Add the parent directory to the path to import our modules
sys.path.append(str(Path(__file__).parent))

from bayesian_calculator import BayesianCalculator, interpret_bayes_factor
from bayesian_validator import BayesianValidator
from technical_rules import BayesianModelingRules


def test_basic_calculations():
    """Test basic Bayesian calculations"""
    print("=== Testing Basic Bayesian Calculations ===")
    
    calculator = BayesianCalculator()
    
    # Test 1: Simple Bayes Factor calculation (for reference only)
    # NOTE: In CSO, Bayes Factor should be set by analyst, not calculated automatically
    bf = calculator.calculate_bayes_factor(0.7, 0.8, 0.3)
    print(f"Bayes Factor: {bf:.3f} - {interpret_bayes_factor(bf)}")
    
    # Test 2: Posterior probability calculation
    posterior = calculator.calculate_posterior_probability(0.6, bf)
    print(f"Prior: 0.6 → Posterior: {posterior:.3f}")
    
    # Test 3: Multiple evidence aggregation
    evidence = [
        {'bayes_factor': 3.0, 'weight': 0.8},
        {'bayes_factor': 2.0, 'weight': 0.6}, 
        {'bayes_factor': 1.5, 'weight': 0.4}
    ]
    final_prob = calculator.aggregate_multiple_evidences(0.5, evidence)
    print(f"Aggregated probability from multiple evidence: {final_prob:.3f}")
    
    print()


def test_validation():
    """Test validation functionality"""
    print("=== Testing Validation System ===")
    
    # Test data with some intentional issues
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
                "posterior_probability": 1.2  # Invalid: > 1.0
            }
        ],
        "edges": [
            {
                "source": "test_arg",
                "target": "test_stmt",
                "relation": "supports",
                "weight": -0.5,  # Invalid: negative weight
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
    
    validator = BayesianValidator()
    is_valid, errors = validator.validate_ontology(test_ontology)
    
    print(f"Validation result: {'✅ VALID' if is_valid else '❌ INVALID'}")
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
    
    # Generate full report
    report = validator.generate_validation_report(test_ontology)
    print(f"\nValidation report statistics:")
    stats = report['statistics']
    print(f"  Total nodes: {stats['total_nodes']}")
    print(f"  Total edges: {stats['total_edges']}")
    print(f"  Node types: {stats['node_types']}")
    
    print()


def test_technical_rules():
    """Test technical rules implementation"""
    print("=== Testing Technical Rules ===")
    
    rules = BayesianModelingRules()
    
    # Test cycle detection
    test_edges = [
        {"source": "A", "target": "B", "relation": "supports"},
        {"source": "B", "target": "C", "relation": "supports"},
        {"source": "C", "target": "A", "relation": "supports"}  # Creates cycle
    ]
    
    cycles = rules.detect_cycles(test_edges)
    print(f"Detected cycles: {cycles}")
    
    # Test probability aggregation
    probs = [0.7, 0.3, 0.8]
    weights = [0.6, 0.3, 0.1]
    
    geometric_result = rules.calculate_aggregated_probability(
        probs, weights, method='weighted_geometric'
    )
    log_odds_result = rules.calculate_aggregated_probability(
        probs, weights, method='log_odds'
    )
    
    print(f"Weighted geometric aggregation: {geometric_result:.3f}")
    print(f"Log-odds aggregation: {log_odds_result:.3f}")
    
    # Test uncertainty intervals
    lower, upper = rules.apply_uncertainty_intervals(0.7, confidence_level=0.95)
    print(f"95% Confidence interval for p=0.7: [{lower:.3f}, {upper:.3f}]")
    
    print()


def test_example_files():
    """Test validation of example files"""
    print("=== Testing Example Files ===")
    
    examples_dir = Path(__file__).parent.parent / "examples_bayesian"
    validator = BayesianValidator()
    
    example_files = list(examples_dir.glob("*.json"))
    
    for example_file in example_files:
        print(f"\nValidating {example_file.name}...")
        is_valid, errors = validator.validate_file(str(example_file))
        
        if is_valid:
            print("  ✅ Valid")
            
            # Load and show some statistics
            with open(example_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            nodes = data.get('nodes', [])
            edges = data.get('edges', [])
            
            node_types = {}
            for node in nodes:
                node_type = node.get('type', 'unknown')
                node_types[node_type] = node_types.get(node_type, 0) + 1
            
            prior_probs = [n.get('prior_probability') for n in nodes if 'prior_probability' in n]
            bayes_factors = [e.get('bayes_factor') for e in edges if 'bayes_factor' in e]
            
            print(f"    Nodes: {len(nodes)} ({node_types})")
            print(f"    Edges: {len(edges)}")
            if prior_probs:
                print(f"    Prior probabilities: {len(prior_probs)} (avg: {sum(prior_probs)/len(prior_probs):.3f})")
            if bayes_factors:
                finite_bfs = [bf for bf in bayes_factors if bf is not None]
                if finite_bfs:
                    print(f"    Bayes factors: {len(finite_bfs)} (avg: {sum(finite_bfs)/len(finite_bfs):.3f})")
        else:
            print("  ❌ Invalid")
            for error in errors[:3]:  # Show first 3 errors
                print(f"    - {error}")
            if len(errors) > 3:
                print(f"    ... and {len(errors) - 3} more errors")


def test_full_model_update():
    """Test full model probability updating"""
    print("=== Testing Full Model Update ===")
    
    # Simple test model
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
    
    calculator = BayesianCalculator()
    
    print("Before update:")
    for node in test_nodes:
        if 'prior_probability' in node:
            print(f"  {node['id']}: prior = {node['prior_probability']}")
    
    # Update the model
    updated_nodes, updated_edges = calculator.update_node_probabilities(test_nodes, test_edges)
    
    print("\nAfter update:")
    for node in updated_nodes:
        if 'posterior_probability' in node:
            print(f"  {node['id']}: prior = {node.get('prior_probability', 'N/A')}, "
                  f"posterior = {node['posterior_probability']:.3f}")
        elif 'prior_probability' in node:
            print(f"  {node['id']}: prior = {node['prior_probability']} (no update)")
    
    print("\nEdge Bayes factors:")
    for edge in updated_edges:
        if 'bayes_factor' in edge:
            print(f"  {edge['source']} → {edge['target']}: BF = {edge['bayes_factor']:.3f}")
    
    print()


def main():
    """Run all tests"""
    print("🧠 CSO Bayesian System Test Suite")
    print("=" * 50)
    
    try:
        test_basic_calculations()
        test_validation()
        test_technical_rules()
        test_example_files()
        test_full_model_update()
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
