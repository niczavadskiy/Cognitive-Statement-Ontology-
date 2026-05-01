"""
Validator for Bayesian CSO schema

This module provides validation functionality for Bayesian-enhanced CSO ontologies,
ensuring data integrity and adherence to Bayesian modeling rules.
"""

import json
import jsonschema
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import math


class BayesianValidator:
    """
    Validator for Bayesian CSO ontologies
    """
    
    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize validator with Bayesian schema
        
        Args:
            schema_path: Path to the Bayesian schema file
        """
        if schema_path is None:
            repo_root = Path(__file__).resolve().parent.parent.parent
            schema_path = repo_root / "ontology" / "Bayesian_modeling" / "schema_bayesian.json"
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Bayesian schema not found at {schema_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in schema file: {e}")
    
    def validate_ontology(self, ontology_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate ontology against Bayesian schema
        
        Args:
            ontology_data: Dictionary containing the ontology
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Schema validation
        try:
            jsonschema.validate(instance=ontology_data, schema=self.schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
        except Exception as e:
            errors.append(f"Unexpected schema validation error: {str(e)}")
        
        # Custom Bayesian validations
        nodes = ontology_data.get('nodes', [])
        edges = ontology_data.get('edges', [])
        
        errors.extend(self.validate_probability_constraints(nodes))
        errors.extend(self.validate_connection_coherence(nodes, edges))
        errors.extend(self.validate_bayesian_consistency(nodes, edges))
        errors.extend(self.validate_weight_constraints(edges))
        errors.extend(self.validate_node_references(nodes, edges))
        
        return len(errors) == 0, errors
    
    def validate_probability_constraints(self, nodes: List[Dict]) -> List[str]:
        """
        Validate that all probability values are within valid ranges [0,1]
        
        Args:
            nodes: List of node dictionaries
            
        Returns:
            List of validation errors
        """
        errors = []
        
        for node in nodes:
            node_id = node.get('id', 'unknown')
            
            # Check prior probability
            if 'prior_probability' in node:
                prob = node['prior_probability']
                if not isinstance(prob, (int, float)):
                    errors.append(f"Node {node_id}: prior_probability must be numeric")
                elif not (0 <= prob <= 1):
                    errors.append(f"Node {node_id}: prior_probability {prob} not in [0,1]")
            
            # Check posterior probability
            if 'posterior_probability' in node:
                prob = node['posterior_probability']
                if not isinstance(prob, (int, float)):
                    errors.append(f"Node {node_id}: posterior_probability must be numeric")
                elif not (0 <= prob <= 1):
                    errors.append(f"Node {node_id}: posterior_probability {prob} not in [0,1]")
                
                # Arguments should have both prior and posterior probabilities
                if node.get('type') == 'argument' and 'prior_probability' not in node:
                    errors.append(f"Argument node {node_id}: missing required prior_probability")
            
            # Questions should NOT have prior_probability
            if node.get('type') == 'question' and 'prior_probability' in node:
                errors.append(f"Question node {node_id}: should NOT have prior_probability (questions do not participate in probability calculations)")
        
        return errors
    
    def validate_connection_coherence(self, nodes: List[Dict], edges: List[Dict]) -> List[str]:
        """
        Validate coherence of connections (relation types vs effects)
        
        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries
            
        Returns:
            List of validation errors
        """
        errors = []
        node_lookup = {node['id']: node for node in nodes}
        
        for edge in edges:
            source_id = edge.get('source', '')
            target_id = edge.get('target', '')
            relation = edge.get('relation', '')
            weight = edge.get('weight', 1.0)
            
            # Check if weight is valid
            if not isinstance(weight, (int, float)):
                errors.append(f"Edge {source_id}->{target_id}: weight must be numeric")
            elif not (0 <= weight <= 1):
                errors.append(f"Edge {source_id}->{target_id}: weight {weight} not in [0,1]")
            
            # Check relation-specific constraints
            if relation == 'supports':
                if weight < 0:
                    errors.append(f"Supporting edge {source_id}->{target_id}: weight should be positive")
            elif relation == 'contradicts':
                # For contradicts, we expect the effect to be negative, 
                # but weight itself should still be positive (it's the strength of contradiction)
                pass  # Weight validation already handles range
            
            # Check if nodes exist
            if source_id not in node_lookup:
                errors.append(f"Edge references non-existent source node: {source_id}")
            if target_id not in node_lookup:
                errors.append(f"Edge references non-existent target node: {target_id}")
            
            # Check argument direction rule: arguments must ALWAYS be targets, never sources
            # EXCEPTION: arguments can be sources when connecting to questions (bidirectional)
            source_node = node_lookup.get(source_id, {})
            target_node = node_lookup.get(target_id, {})
            if source_node.get('type') == 'argument' and target_node.get('type') != 'question':
                errors.append(f"Argument {source_id} cannot be a source in edge {source_id}->{target_id}. Arguments must always be targets (except when connecting to questions).")
        
        return errors
    
    def validate_bayesian_consistency(self, nodes: List[Dict], edges: List[Dict]) -> List[str]:
        """
        Validate Bayesian consistency (e.g., proper Bayes factors)
        
        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries
            
        Returns:
            List of validation errors
        """
        errors = []
        
        for edge in edges:
            source_id = edge.get('source', '')
            target_id = edge.get('target', '')
            
            # Check Bayes factor if present
            if 'bayes_factor' in edge:
                bf = edge['bayes_factor']
                if not isinstance(bf, (int, float)):
                    errors.append(f"Edge {source_id}->{target_id}: bayes_factor must be numeric")
                elif bf < 0:
                    errors.append(f"Edge {source_id}->{target_id}: bayes_factor {bf} cannot be negative")
                elif math.isinf(bf) and bf < 0:
                    errors.append(f"Edge {source_id}->{target_id}: bayes_factor cannot be negative infinity")
        
        # Check for required probabilities on statement and argument nodes
        for node in nodes:
            node_type = node.get('type', '')
            node_id = node.get('id', 'unknown')
            
            if node_type in ['statement', 'argument']:
                if 'prior_probability' not in node:
                    errors.append(f"{node_type.capitalize()} node {node_id}: missing required prior_probability")
            
            if node_type == 'argument':
                # Arguments should eventually have posterior probabilities calculated
                # This is a warning rather than an error since they might be calculated later
                pass
        
        return errors
    
    def validate_weight_constraints(self, edges: List[Dict]) -> List[str]:
        """
        Validate weight constraints and their proper usage
        
        Args:
            edges: List of edge dictionaries
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Group edges by target to check weight distribution
        target_groups = {}
        for edge in edges:
            target = edge.get('target', '')
            if target not in target_groups:
                target_groups[target] = []
            target_groups[target].append(edge)
        
        # Check each target's incoming weights
        for target_id, target_edges in target_groups.items():
            total_weight = sum(edge.get('weight', 1.0) for edge in target_edges)
            
            # Warning if total weight is much larger than 1.0 per edge
            if len(target_edges) > 1 and total_weight > len(target_edges):
                errors.append(f"Node {target_id}: total incoming weight {total_weight:.2f} "
                            f"might be too high for {len(target_edges)} connections")
            
            # Check for edges with weight 0 (which effectively removes the connection)
            for edge in target_edges:
                weight = edge.get('weight', 1.0)
                if weight == 0:
                    source_id = edge.get('source', '')
                    errors.append(f"Edge {source_id}->{target_id}: weight of 0 makes connection ineffective")
        
        return errors
    
    def validate_node_references(self, nodes: List[Dict], edges: List[Dict]) -> List[str]:
        """
        Validate that all node references in edges exist
        
        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries
            
        Returns:
            List of validation errors
        """
        errors = []
        node_ids = {node.get('id') for node in nodes}
        
        for edge in edges:
            source_id = edge.get('source')
            target_id = edge.get('target')
            
            if source_id not in node_ids:
                errors.append(f"Edge references non-existent source node: {source_id}")
            if target_id not in node_ids:
                errors.append(f"Edge references non-existent target node: {target_id}")
            
            # Check for self-references (might be valid in some cases, but flag for review)
            if source_id == target_id:
                errors.append(f"Self-referencing edge detected: {source_id} -> {target_id}")
        
        return errors
    
    def validate_file(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        Validate a JSON file containing Bayesian CSO ontology
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ontology_data = json.load(f)
            return self.validate_ontology(ontology_data)
        except FileNotFoundError:
            return False, [f"File not found: {file_path}"]
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON in file {file_path}: {e}"]
        except Exception as e:
            return False, [f"Unexpected error validating file {file_path}: {e}"]
    
    def check_cycle_detection(self, edges: List[Dict]) -> List[str]:
        """
        Detect cycles in the graph which might cause convergence issues
        
        Args:
            edges: List of edge dictionaries
            
        Returns:
            List of warnings about cycles
        """
        warnings = []
        
        # Build adjacency list
        graph = {}
        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            if source not in graph:
                graph[source] = []
            graph[source].append(target)
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        cycles_found = []
        
        def dfs(node, path):
            if node in rec_stack:
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles_found.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            if node in graph:
                for neighbor in graph[node]:
                    dfs(neighbor, path.copy())
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        for cycle in cycles_found:
            warnings.append(f"Cycle detected: {' -> '.join(cycle)}")
        
        return warnings
    
    def generate_validation_report(self, ontology_data: Dict) -> Dict:
        """
        Generate comprehensive validation report
        
        Args:
            ontology_data: Dictionary containing the ontology
            
        Returns:
            Dictionary with validation results and statistics
        """
        is_valid, errors = self.validate_ontology(ontology_data)
        
        nodes = ontology_data.get('nodes', [])
        edges = ontology_data.get('edges', [])
        
        # Statistics
        node_types = {}
        for node in nodes:
            node_type = node.get('type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        relation_types = {}
        for edge in edges:
            relation = edge.get('relation', 'unknown')
            relation_types[relation] = relation_types.get(relation, 0) + 1
        
        # Cycle detection
        cycle_warnings = self.check_cycle_detection(edges)
        
        # Probability statistics
        prob_stats = self._calculate_probability_statistics(nodes)
        
        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': cycle_warnings,
            'statistics': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'node_types': node_types,
                'relation_types': relation_types,
                'probability_statistics': prob_stats
            }
        }
    
    def _calculate_probability_statistics(self, nodes: List[Dict]) -> Dict:
        """
        Calculate statistics about probability distributions
        """
        prior_probs = []
        posterior_probs = []
        
        for node in nodes:
            if 'prior_probability' in node:
                prior_probs.append(node['prior_probability'])
            if 'posterior_probability' in node:
                posterior_probs.append(node['posterior_probability'])
        
        stats = {}
        
        if prior_probs:
            stats['prior_probabilities'] = {
                'count': len(prior_probs),
                'mean': sum(prior_probs) / len(prior_probs),
                'min': min(prior_probs),
                'max': max(prior_probs)
            }
        
        if posterior_probs:
            stats['posterior_probabilities'] = {
                'count': len(posterior_probs),
                'mean': sum(posterior_probs) / len(posterior_probs),
                'min': min(posterior_probs),
                'max': max(posterior_probs)
            }
        
        return stats


# Command-line interface for validation
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python bayesian_validator.py <ontology_file.json>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        validator = BayesianValidator()
        is_valid, errors = validator.validate_file(file_path)
        
        print(f"Validation of {file_path}:")
        print(f"Status: {'✅ VALID' if is_valid else '❌ INVALID'}")
        
        if errors:
            print("\nErrors found:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("\n✅ No errors found!")
        
        # Generate full report
        with open(file_path, 'r', encoding='utf-8') as f:
            ontology_data = json.load(f)
        
        report = validator.generate_validation_report(ontology_data)
        
        print(f"\nStatistics:")
        stats = report['statistics']
        print(f"  Nodes: {stats['total_nodes']}")
        print(f"  Edges: {stats['total_edges']}")
        print(f"  Node types: {stats['node_types']}")
        print(f"  Relation types: {stats['relation_types']}")
        
        if report['warnings']:
            print(f"\nWarnings:")
            for warning in report['warnings']:
                print(f"  ⚠️  {warning}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
