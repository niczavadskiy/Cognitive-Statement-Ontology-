"""
Technical Rules Implementation for CSO Bayesian Modeling

This module implements technical rules and algorithms for Bayesian modeling
in the Cognitive Ontology framework, providing concrete implementations
of the theoretical rules defined in bayesian_modeling_rules.md
"""

from typing import Dict, List, Tuple, Optional, Set
import math
import numpy as np
from collections import defaultdict, deque
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BayesianModelingRules:
    """
    Implementation of CSO Bayesian Modeling Rules
    """
    
    def __init__(self, 
                 max_iterations: int = 100, 
                 convergence_threshold: float = 1e-6,
                 max_cycle_depth: int = 10):
        """
        Initialize the rules engine
        
        Args:
            max_iterations: Maximum iterations for convergence
            convergence_threshold: Threshold for convergence detection
            max_cycle_depth: Maximum depth for cycle detection
        """
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.max_cycle_depth = max_cycle_depth
        self.validation_errors = []
        self.warnings = []
    
    def validate_probability_constraints(self, nodes: List[Dict]) -> List[str]:
        """
        Rule 7: Probability Constraints Validation
        
        Ensures all probability values are within [0,1] range
        """
        errors = []
        
        for node in nodes:
            node_id = node.get('id', 'unknown')
            
            # Check prior probability
            if 'prior_probability' in node:
                prob = node['prior_probability']
                if not isinstance(prob, (int, float)):
                    errors.append(f"Node {node_id}: prior_probability must be numeric, got {type(prob)}")
                elif not (0 <= prob <= 1):
                    errors.append(f"Node {node_id}: prior_probability {prob} not in [0,1]")
                elif math.isnan(prob):
                    errors.append(f"Node {node_id}: prior_probability is NaN")
                elif math.isinf(prob):
                    errors.append(f"Node {node_id}: prior_probability is infinite")
            
            # Check posterior probability
            if 'posterior_probability' in node:
                prob = node['posterior_probability']
                if not isinstance(prob, (int, float)):
                    errors.append(f"Node {node_id}: posterior_probability must be numeric, got {type(prob)}")
                elif not (0 <= prob <= 1):
                    errors.append(f"Node {node_id}: posterior_probability {prob} not in [0,1]")
                elif math.isnan(prob):
                    errors.append(f"Node {node_id}: posterior_probability is NaN")
                elif math.isinf(prob):
                    errors.append(f"Node {node_id}: posterior_probability is infinite")
        
        return errors
    
    def validate_connection_coherence(self, nodes: List[Dict], edges: List[Dict]) -> List[str]:
        """
        Rule 8: Connection Coherence Validation
        
        Validates that connections are logically coherent
        """
        errors = []
        node_lookup = {node['id']: node for node in nodes}
        
        for edge in edges:
            source_id = edge.get('source', '')
            target_id = edge.get('target', '')
            relation = edge.get('relation', '')
            weight = edge.get('weight', 1.0)
            strength = edge.get('strength', 0.5)
            
            # Validate weight
            if not isinstance(weight, (int, float)):
                errors.append(f"Edge {source_id}->{target_id}: weight must be numeric, got {type(weight)}")
            elif not (0 <= weight <= 1):
                errors.append(f"Edge {source_id}->{target_id}: weight {weight} not in [0,1]")
            elif math.isnan(weight):
                errors.append(f"Edge {source_id}->{target_id}: weight is NaN")
            elif math.isinf(weight):
                errors.append(f"Edge {source_id}->{target_id}: weight is infinite")
            
            # Validate strength
            if not isinstance(strength, (int, float)):
                errors.append(f"Edge {source_id}->{target_id}: strength must be numeric, got {type(strength)}")
            elif not (0 <= strength <= 1):
                errors.append(f"Edge {source_id}->{target_id}: strength {strength} not in [0,1]")
            
            # Validate relation-specific constraints
            if relation == 'supports':
                if weight < 0:
                    errors.append(f"Supporting edge {source_id}->{target_id}: weight should be non-negative")
            elif relation == 'contradicts':
                # For contradicts, weight represents strength of contradiction (positive)
                if weight < 0:
                    errors.append(f"Contradicting edge {source_id}->{target_id}: weight should be non-negative")
            
            # Check node existence
            if source_id not in node_lookup:
                errors.append(f"Edge references non-existent source node: {source_id}")
            if target_id not in node_lookup:
                errors.append(f"Edge references non-existent target node: {target_id}")
                
            # Check for self-loops
            if source_id == target_id:
                errors.append(f"Self-loop detected: {source_id} -> {target_id}")
        
        return errors
    
    def detect_cycles(self, edges: List[Dict]) -> List[List[str]]:
        """
        Rule 12: Cycle Detection using DFS
        
        Returns list of cycles found in the graph
        """
        # Build adjacency list
        graph = defaultdict(list)
        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            if source and target:
                graph[source].append(target)
        
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> None:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph[node]:
                dfs(neighbor, path.copy())
            
            rec_stack.remove(node)
        
        # Start DFS from all unvisited nodes
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def calculate_aggregated_probability(self, 
                                       individual_probs: List[float], 
                                       weights: List[float],
                                       method: str = 'weighted_geometric') -> float:
        """
        Rule 6: Aggregation of Multiple Connections
        
        Args:
            individual_probs: List of individual probabilities
            weights: List of weights for each probability
            method: Aggregation method ('weighted_geometric', 'weighted_arithmetic', 'log_odds')
        """
        if not individual_probs or not weights:
            return 0.5
        
        if len(individual_probs) != len(weights):
            raise ValueError("Individual probabilities and weights must have same length")
        
        # Filter out zero weights and corresponding probabilities
        filtered_data = [(p, w) for p, w in zip(individual_probs, weights) if w > 0]
        if not filtered_data:
            return 0.5
        
        probs, weights = zip(*filtered_data)
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight == 0:
            return 0.5
        
        normalized_weights = [w / total_weight for w in weights]
        
        if method == 'weighted_geometric':
            # Weighted geometric mean of probabilities
            log_prob = sum(w * math.log(max(p, 1e-10)) for p, w in zip(probs, normalized_weights))
            return min(1.0, max(0.0, math.exp(log_prob)))
        
        elif method == 'weighted_arithmetic':
            # Weighted arithmetic mean
            return sum(p * w for p, w in zip(probs, normalized_weights))
        
        elif method == 'log_odds':
            # Log-odds aggregation (more principled for probabilities)
            def prob_to_log_odds(p):
                p = max(1e-10, min(1-1e-10, p))  # Avoid division by zero
                return math.log(p / (1 - p))
            
            def log_odds_to_prob(log_odds):
                return 1 / (1 + math.exp(-log_odds))
            
            weighted_log_odds = sum(w * prob_to_log_odds(p) for p, w in zip(probs, normalized_weights))
            return log_odds_to_prob(weighted_log_odds)
        
        else:
            raise ValueError(f"Unknown aggregation method: {method}")
    
    def apply_cognitive_bias_correction(self, 
                                      node: Dict, 
                                      bias_type: str, 
                                      correction_factor: float,
                                      bias_strength: float = 1.0) -> Dict:
        """
        Rule 10: Cognitive Bias Correction
        
        Args:
            node: Node to correct
            bias_type: Type of cognitive bias
            correction_factor: Strength of correction [0,1]
            bias_strength: Strength of the bias effect [0,1]
        """
        corrected_node = node.copy()
        
        if bias_type == 'confirmation_bias':
            # Confirmation bias increases confidence in prior beliefs
            if 'prior_probability' in corrected_node:
                prior = corrected_node['prior_probability']
                # Push probability away from 0.5 (neutral) towards extremes
                if prior > 0.5:
                    bias_effect = (prior - 0.5) * bias_strength * correction_factor
                    corrected_node['prior_probability'] = min(1.0, prior + bias_effect)
                else:
                    bias_effect = (0.5 - prior) * bias_strength * correction_factor
                    corrected_node['prior_probability'] = max(0.0, prior - bias_effect)
        
        elif bias_type == 'anchoring_bias':
            # Anchoring bias makes probabilities stick closer to initial values
            if 'prior_probability' in corrected_node and 'posterior_probability' in corrected_node:
                prior = corrected_node['prior_probability']
                posterior = corrected_node['posterior_probability']
                # Pull posterior towards prior
                anchoring_effect = (prior - posterior) * bias_strength * correction_factor
                corrected_node['posterior_probability'] = posterior + anchoring_effect
                corrected_node['posterior_probability'] = max(0.0, min(1.0, corrected_node['posterior_probability']))
        
        elif bias_type == 'hindsight_bias':
            # Hindsight bias inflates posterior probabilities
            if 'posterior_probability' in corrected_node:
                posterior = corrected_node['posterior_probability']
                # Increase confidence in hindsight
                if posterior > 0.5:
                    bias_effect = (posterior - 0.5) * bias_strength * correction_factor
                    corrected_node['posterior_probability'] = min(1.0, posterior + bias_effect)
                else:
                    bias_effect = (0.5 - posterior) * bias_strength * correction_factor
                    corrected_node['posterior_probability'] = max(0.0, posterior - bias_effect)
        
        elif bias_type == 'availability_heuristic':
            # Availability heuristic overweights easily recalled evidence
            # This affects the weights of incoming edges rather than the node itself
            pass  # Handled in edge processing
        
        return corrected_node
    
    def calculate_quality_metrics(self, nodes: List[Dict], edges: List[Dict]) -> Dict:
        """
        Rules 13-14: Quality Metrics Calculation
        
        Returns comprehensive quality metrics for the Bayesian model
        """
        metrics = {}
        
        # Basic statistics
        total_nodes = len(nodes)
        total_edges = len(edges)
        
        # Node type distribution
        node_types = defaultdict(int)
        for node in nodes:
            node_types[node.get('type', 'unknown')] += 1
        
        # Probability statistics
        prior_probs = [n.get('prior_probability') for n in nodes if 'prior_probability' in n]
        posterior_probs = [n.get('posterior_probability') for n in nodes if 'posterior_probability' in n]
        
        if prior_probs:
            metrics['prior_probability_stats'] = {
                'count': len(prior_probs),
                'mean': np.mean(prior_probs),
                'std': np.std(prior_probs),
                'min': np.min(prior_probs),
                'max': np.max(prior_probs),
                'median': np.median(prior_probs)
            }
        
        if posterior_probs:
            metrics['posterior_probability_stats'] = {
                'count': len(posterior_probs),
                'mean': np.mean(posterior_probs),
                'std': np.std(posterior_probs),
                'min': np.min(posterior_probs),
                'max': np.max(posterior_probs),
                'median': np.median(posterior_probs)
            }
        
        # Calibration metric (how close posteriors are to priors on average)
        if prior_probs and posterior_probs:
            # Match nodes with both prior and posterior
            matched_pairs = []
            for node in nodes:
                if 'prior_probability' in node and 'posterior_probability' in node:
                    matched_pairs.append((node['prior_probability'], node['posterior_probability']))
            
            if matched_pairs:
                prior_vals, posterior_vals = zip(*matched_pairs)
                calibration_error = np.mean([abs(p - q) for p, q in matched_pairs])
                metrics['calibration'] = {
                    'mean_absolute_error': calibration_error,
                    'correlation': np.corrcoef(prior_vals, posterior_vals)[0, 1] if len(matched_pairs) > 1 else 0
                }
        
        # Resolution metric (spread of probabilities)
        if posterior_probs:
            metrics['resolution'] = {
                'posterior_variance': np.var(posterior_probs),
                'effective_range': np.max(posterior_probs) - np.min(posterior_probs)
            }
        
        # Cycle analysis
        cycles = self.detect_cycles(edges)
        metrics['cycle_analysis'] = {
            'cycle_count': len(cycles),
            'max_cycle_length': max([len(c) for c in cycles]) if cycles else 0,
            'cycles': cycles[:5]  # Return first 5 cycles as examples
        }
        
        # Edge statistics
        edge_weights = [e.get('weight', 1.0) for e in edges if 'weight' in e]
        edge_strengths = [e.get('strength', 0.5) for e in edges if 'strength' in e]
        bayes_factors = [e.get('bayes_factor') for e in edges if 'bayes_factor' in e and e['bayes_factor'] is not None]
        
        if edge_weights:
            metrics['edge_weight_stats'] = {
                'mean': np.mean(edge_weights),
                'std': np.std(edge_weights),
                'min': np.min(edge_weights),
                'max': np.max(edge_weights)
            }
        
        if bayes_factors:
            # Filter out infinite values for statistics
            finite_bfs = [bf for bf in bayes_factors if math.isfinite(bf)]
            if finite_bfs:
                metrics['bayes_factor_stats'] = {
                    'count': len(finite_bfs),
                    'mean': np.mean(finite_bfs),
                    'median': np.median(finite_bfs),
                    'strong_evidence_count': sum(1 for bf in finite_bfs if bf >= 10),
                    'moderate_evidence_count': sum(1 for bf in finite_bfs if 3 <= bf < 10),
                    'weak_evidence_count': sum(1 for bf in finite_bfs if 1 <= bf < 3)
                }
        
        # Overall model health
        metrics['model_health'] = {
            'total_nodes': total_nodes,
            'total_edges': total_edges,
            'node_types': dict(node_types),
            'connectivity': total_edges / total_nodes if total_nodes > 0 else 0,
            'has_cycles': len(cycles) > 0,
            'probability_coverage': len(prior_probs) / total_nodes if total_nodes > 0 else 0
        }
        
        return metrics
    
    def apply_uncertainty_intervals(self, 
                                  probability: float, 
                                  confidence_level: float = 0.95,
                                  method: str = 'wilson') -> Tuple[float, float]:
        """
        Rule 17: Uncertainty Intervals calculation
        
        Args:
            probability: Point estimate
            confidence_level: Confidence level (0.95 or 0.99)
            method: Method to use ('wilson', 'clopper_pearson', 'jeffreys')
        """
        if method == 'wilson':
            return self._wilson_score_interval(probability, confidence_level)
        elif method == 'clopper_pearson':
            return self._clopper_pearson_interval(probability, confidence_level)
        elif method == 'jeffreys':
            return self._jeffreys_interval(probability, confidence_level)
        else:
            raise ValueError(f"Unknown interval method: {method}")
    
    def _wilson_score_interval(self, p: float, confidence_level: float, n: int = 100) -> Tuple[float, float]:
        """Wilson score interval for binomial proportion"""
        if confidence_level == 0.95:
            z = 1.96
        elif confidence_level == 0.99:
            z = 2.576
        else:
            z = 1.96  # Default to 95%
        
        if p == 0:
            lower = 0
            upper = 1 - (1 - confidence_level) ** (1 / n)
        elif p == 1:
            lower = confidence_level ** (1 / n)
            upper = 1
        else:
            denominator = 1 + z**2 / n
            centre = (p + z**2 / (2*n)) / denominator
            margin = z * math.sqrt(p * (1 - p) / n + z**2 / (4*n**2)) / denominator
            
            lower = max(0, centre - margin)
            upper = min(1, centre + margin)
        
        return lower, upper
    
    def _clopper_pearson_interval(self, p: float, confidence_level: float) -> Tuple[float, float]:
        """Clopper-Pearson exact interval"""
        # Simplified implementation - in practice would use beta distribution
        alpha = 1 - confidence_level
        
        if p == 0:
            return 0.0, alpha
        elif p == 1:
            return 1 - alpha, 1.0
        else:
            # Approximate with normal distribution for simplicity
            return self._wilson_score_interval(p, confidence_level)
    
    def _jeffreys_interval(self, p: float, confidence_level: float) -> Tuple[float, float]:
        """Jeffreys interval using Beta distribution"""
        # Simplified implementation
        alpha = 1 - confidence_level
        
        # Jeffreys prior: Beta(0.5, 0.5)
        # Posterior: Beta(0.5 + successes, 0.5 + failures)
        # For point estimate p, assume n=100 observations
        n = 100
        successes = p * n
        failures = n - successes
        
        # Use normal approximation to beta distribution
        a = 0.5 + successes
        b = 0.5 + failures
        
        mean = a / (a + b)
        variance = (a * b) / ((a + b)**2 * (a + b + 1))
        std = math.sqrt(variance)
        
        # Normal approximation
        z = 1.96 if confidence_level == 0.95 else 2.576
        lower = max(0.0, mean - z * std)
        upper = min(1.0, mean + z * std)
        
        return lower, upper
    
    def validate_model_consistency(self, nodes: List[Dict], edges: List[Dict]) -> Tuple[bool, List[str]]:
        """
        Comprehensive model consistency validation
        """
        errors = []
        
        # Run all validation rules
        errors.extend(self.validate_probability_constraints(nodes))
        errors.extend(self.validate_connection_coherence(nodes, edges))
        
        # Check for required fields
        for node in nodes:
            node_type = node.get('type')
            node_id = node.get('id', 'unknown')
            
            if node_type in ['statement', 'argument'] and 'prior_probability' not in node:
                errors.append(f"{node_type} node {node_id} missing required prior_probability")
            
            # Questions should NOT have prior_probability
            if node_type == 'question' and 'prior_probability' in node:
                errors.append(f"question node {node_id} should NOT have prior_probability (questions do not participate in probability calculations)")
        
        # Check Bayes factor validity
        for edge in edges:
            if 'bayes_factor' in edge:
                bf = edge['bayes_factor']
                if bf < 0:
                    errors.append(f"Edge {edge.get('source')}->{edge.get('target')}: negative Bayes factor {bf}")
        
        return len(errors) == 0, errors


# Utility functions for common operations
def normalize_probability(value: float) -> float:
    """Ensure probability is in [0,1] range"""
    return max(0.0, min(1.0, value))


def safe_log(value: float, epsilon: float = 1e-10) -> float:
    """Safe logarithm that avoids log(0)"""
    return math.log(max(epsilon, value))


def logit(p: float) -> float:
    """Convert probability to log-odds"""
    p = max(1e-10, min(1-1e-10, p))
    return math.log(p / (1 - p))


def sigmoid(log_odds: float) -> float:
    """Convert log-odds to probability"""
    return 1 / (1 + math.exp(-log_odds))


# Example usage and testing
if __name__ == "__main__":
    rules = BayesianModelingRules()
    
    print("=== Bayesian Modeling Rules Test ===")
    
    # Test 1: Cycle detection
    test_edges = [
        {"source": "A", "target": "B", "relation": "supports"},
        {"source": "B", "target": "C", "relation": "supports"},
        {"source": "C", "target": "A", "relation": "supports"}  # Creates cycle
    ]
    
    cycles = rules.detect_cycles(test_edges)
    print(f"Detected cycles: {cycles}")
    
    # Test 2: Probability aggregation
    probs = [0.7, 0.3, 0.8]
    weights = [0.5, 0.3, 0.2]
    
    aggregated = rules.calculate_aggregated_probability(probs, weights, method='log_odds')
    print(f"Aggregated probability: {aggregated:.3f}")
    
    # Test 3: Quality metrics
    test_nodes = [
        {"id": "1", "type": "statement", "prior_probability": 0.7, "posterior_probability": 0.8},
        {"id": "2", "type": "argument", "prior_probability": 0.3, "posterior_probability": 0.4}
    ]
    
    metrics = rules.calculate_quality_metrics(test_nodes, test_edges)
    print(f"Quality metrics: {metrics}")
    
    # Test 4: Uncertainty intervals
    lower, upper = rules.apply_uncertainty_intervals(0.7, confidence_level=0.95)
    print(f"95% Confidence Interval: [{lower:.3f}, {upper:.3f}]")
    
    # Test 5: Model validation
    is_valid, validation_errors = rules.validate_model_consistency(test_nodes, test_edges)
    print(f"Model valid: {is_valid}")
    if validation_errors:
        print("Validation errors:")
        for error in validation_errors:
            print(f"  - {error}")
