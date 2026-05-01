"""
Bayesian Calculator for CSO
Based on "Bayesian Cognitive Modeling" by Michael D. Lee and Eric-Jan Wagenmakers

This module implements Bayesian probability calculations for the Cognitive Ontology framework,
enabling calculation of prior and posterior probabilities, Bayes factors, and model updates.
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import json


class BayesianCalculator:
    """
    Main calculator class for Bayesian operations in CSO
    """
    
    def __init__(self, convergence_threshold: float = 0.001, max_iterations: int = 100):
        """
        Initialize the Bayesian Calculator
        
        Args:
            convergence_threshold: Threshold for iterative calculations
            max_iterations: Maximum number of iterations for convergence
        """
        self.convergence_threshold = convergence_threshold
        self.max_iterations = max_iterations
        self.calculation_history = []
    
    def calculate_bayes_factor(self, 
                             prior_prob: float, 
                             likelihood_h1: float, 
                             likelihood_h0: float = None) -> float:
        """
        Calculate Bayes Factor (BF) = P(E|H1) / P(E|H0)
        
        NOTE: In CSO, Bayes Factor should be set by analyst, not calculated automatically.
        This method is provided for reference calculations only.
        
        Args:
            prior_prob: Prior probability of hypothesis H1
            likelihood_h1: Likelihood of evidence given H1
            likelihood_h0: Likelihood of evidence given H0 (default: 1-likelihood_h1)
            
        Returns:
            Bayes Factor value
        """
        if likelihood_h0 is None:
            likelihood_h0 = 1 - likelihood_h1
        
        if likelihood_h0 == 0:
            return float('inf') if likelihood_h1 > 0 else 1.0
        
        bf = likelihood_h1 / likelihood_h0
        
        # Store calculation in history
        self.calculation_history.append({
            'operation': 'bayes_factor',
            'prior': prior_prob,
            'likelihood_h1': likelihood_h1,
            'likelihood_h0': likelihood_h0,
            'result': bf
        })
        
        return bf
    
    def calculate_posterior_probability(self, 
                                     prior_prob: float, 
                                     bayes_factor: float) -> float:
        """
        Calculate posterior probability using Bayes Factor
        
        P(H|E) = P(H) * BF / (P(H) * BF + P(~H))
        
        Args:
            prior_prob: Prior probability of hypothesis
            bayes_factor: Bayes Factor from evidence
            
        Returns:
            Posterior probability
        """
        if bayes_factor == 0:
            return 0.0
        
        if bayes_factor == float('inf'):
            return 1.0
        
        numerator = prior_prob * bayes_factor
        denominator = prior_prob * bayes_factor + (1 - prior_prob)
        
        if denominator == 0:
            return prior_prob
        
        posterior = numerator / denominator
        
        # Ensure probability is in valid range
        posterior = max(0.0, min(1.0, posterior))
        
        self.calculation_history.append({
            'operation': 'posterior_probability',
            'prior': prior_prob,
            'bayes_factor': bayes_factor,
            'result': posterior
        })
        
        return posterior
    
    def aggregate_multiple_evidences(self, 
                                   prior_prob: float,
                                   evidence_list: List[Dict]) -> float:
        """
        Aggregate multiple pieces of evidence using sequential Bayesian updates
        
        Args:
            prior_prob: Initial prior probability
            evidence_list: List of evidence dictionaries with 'bayes_factor' and 'weight'
            
        Returns:
            Final posterior probability after all evidence
        """
        current_prob = prior_prob
        
        # Sort evidence by weight (strongest first)
        sorted_evidence = sorted(evidence_list, key=lambda x: x.get('weight', 1.0), reverse=True)
        
        for evidence in sorted_evidence:
            bf = evidence.get('bayes_factor', 1.0)
            weight = evidence.get('weight', 1.0)
            
            # Apply weight to Bayes Factor
            weighted_bf = bf ** weight
            
            # Update probability
            current_prob = self.calculate_posterior_probability(current_prob, weighted_bf)
        
        return current_prob
    
    def calculate_competing_hypotheses(self, 
                                     hypotheses: List[Dict]) -> List[Dict]:
        """
        Calculate probabilities for competing hypotheses
        
        Args:
            hypotheses: List of hypothesis dictionaries with 'prior' and 'likelihood'
            
        Returns:
            List of hypotheses with calculated posterior probabilities
        """
        # Calculate marginal likelihood (normalization constant)
        marginal_likelihood = sum(h['prior'] * h['likelihood'] for h in hypotheses)
        
        if marginal_likelihood == 0:
            # Equal probabilities if no evidence
            equal_prob = 1.0 / len(hypotheses)
            for h in hypotheses:
                h['posterior'] = equal_prob
            return hypotheses
        
        # Calculate posterior for each hypothesis
        for hypothesis in hypotheses:
            posterior = (hypothesis['prior'] * hypothesis['likelihood']) / marginal_likelihood
            hypothesis['posterior'] = posterior
            hypothesis['bayes_factor'] = hypothesis['likelihood'] / (marginal_likelihood / hypothesis['prior'])
        
        return hypotheses
    
    def update_node_probabilities(self, 
                                nodes: List[Dict], 
                                edges: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Update posterior probabilities for all nodes based on connections
        
        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries
            
        Returns:
            Tuple of (updated_nodes, updated_edges)
        """
        updated_nodes = [node.copy() for node in nodes]
        updated_edges = [edge.copy() for edge in edges]
        
        # Create node lookup
        node_lookup = {node['id']: i for i, node in enumerate(updated_nodes)}
        
        # Iterate until convergence
        for iteration in range(self.max_iterations):
            old_probs = {node['id']: node.get('posterior_probability', node.get('prior_probability', 0.5)) 
                        for node in updated_nodes}
            
            # Update each argument node
            for node in updated_nodes:
                if node['type'] == 'argument':
                    self._update_argument_probability(node, updated_nodes, updated_edges, node_lookup)
            
            # Update Bayes factors for edges
            for edge in updated_edges:
                self._update_edge_bayes_factor(edge, updated_nodes, node_lookup)
            
            # Check convergence
            converged = True
            for node in updated_nodes:
                node_id = node['id']
                new_prob = node.get('posterior_probability', node.get('prior_probability', 0.5))
                if abs(new_prob - old_probs[node_id]) > self.convergence_threshold:
                    converged = False
                    break
            
            if converged:
                break
        
        return updated_nodes, updated_edges
    
    def _update_argument_probability(self, 
                                   argument_node: Dict, 
                                   all_nodes: List[Dict], 
                                   all_edges: List[Dict],
                                   node_lookup: Dict) -> None:
        """
        Update probability of a single argument node
        """
        node_id = argument_node['id']
        prior_prob = argument_node.get('prior_probability', 0.5)
        
        # Find all incoming edges
        incoming_edges = [edge for edge in all_edges if edge['target'] == node_id]
        
        if not incoming_edges:
            # No incoming evidence, use prior
            argument_node['posterior_probability'] = prior_prob
            return
        
        # Collect evidence from incoming edges
        evidence_list = []
        for edge in incoming_edges:
            source_node_idx = node_lookup.get(edge['source'])
            if source_node_idx is not None:
                source_node = all_nodes[source_node_idx]
                
                # Calculate likelihood based on source probability and relation
                source_prob = source_node.get('posterior_probability', 
                                            source_node.get('prior_probability', 0.5))
                
                likelihood = self._calculate_likelihood_from_relation(
                    edge['relation'], source_prob, edge.get('strength', 0.5)
                )
                
                bf = self.calculate_bayes_factor(prior_prob, likelihood)
                weight = edge.get('weight', 1.0)
                
                evidence_list.append({
                    'bayes_factor': bf,
                    'weight': weight,
                    'source': edge['source'],
                    'relation': edge['relation']
                })
                
                # Update edge with calculated BF
                edge['bayes_factor'] = bf
        
        # Aggregate all evidence
        posterior_prob = self.aggregate_multiple_evidences(prior_prob, evidence_list)
        argument_node['posterior_probability'] = posterior_prob
    
    def _update_edge_bayes_factor(self, 
                                edge: Dict, 
                                all_nodes: List[Dict],
                                node_lookup: Dict) -> None:
        """
        Update Bayes factor for an edge
        """
        source_idx = node_lookup.get(edge['source'])
        target_idx = node_lookup.get(edge['target'])
        
        if source_idx is None or target_idx is None:
            return
        
        source_node = all_nodes[source_idx]
        target_node = all_nodes[target_idx]
        
        source_prob = source_node.get('posterior_probability', 
                                    source_node.get('prior_probability', 0.5))
        target_prior = target_node.get('prior_probability', 0.5)
        
        likelihood = self._calculate_likelihood_from_relation(
            edge['relation'], source_prob, edge.get('strength', 0.5)
        )
        
        bf = self.calculate_bayes_factor(target_prior, likelihood)
        edge['bayes_factor'] = bf
    
    def _calculate_likelihood_from_relation(self, 
                                          relation: str, 
                                          source_prob: float, 
                                          strength: float) -> float:
        """
        Calculate likelihood based on relation type and source probability
        """
        if relation == 'supports':
            # Supporting relation: higher source probability increases likelihood
            return 0.5 + (source_prob - 0.5) * strength
        elif relation == 'contradicts':
            # Contradicting relation: higher source probability decreases likelihood
            return 0.5 - (source_prob - 0.5) * strength
        elif relation == 'influences':
            # General influence: use strength as base likelihood modifier
            return 0.5 + (source_prob - 0.5) * strength * 0.5
        else:
            # Neutral relations
            return 0.5
    
    def calculate_confidence_interval(self, 
                                    probability: float, 
                                    sample_size: int = 100,
                                    confidence_level: float = 0.95) -> Tuple[float, float]:
        """
        Calculate confidence interval for a probability estimate
        
        Args:
            probability: Point estimate of probability
            sample_size: Effective sample size
            confidence_level: Confidence level (default 0.95)
            
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if sample_size <= 0:
            return (0.0, 1.0)
        
        # Wilson score interval
        z = 1.96 if confidence_level == 0.95 else 2.576  # 99% confidence
        
        p = probability
        n = sample_size
        
        denominator = 1 + z**2 / n
        centre = (p + z**2 / (2*n)) / denominator
        margin = z * math.sqrt(p * (1-p) / n + z**2 / (4*n**2)) / denominator
        
        lower = max(0.0, centre - margin)
        upper = min(1.0, centre + margin)
        
        return (lower, upper)
    
    def get_calculation_summary(self) -> Dict:
        """
        Get summary of all calculations performed
        """
        return {
            'total_calculations': len(self.calculation_history),
            'operations': [calc['operation'] for calc in self.calculation_history],
            'convergence_threshold': self.convergence_threshold,
            'max_iterations': self.max_iterations
        }
    
    def reset_history(self):
        """
        Reset calculation history
        """
        self.calculation_history = []


def interpret_bayes_factor(bf: float) -> str:
    """
    Interpret Bayes Factor according to Kass and Raftery (1995) scale
    
    Args:
        bf: Bayes Factor value
        
    Returns:
        Interpretation string
    """
    if bf < 1:
        return "Evidence against hypothesis"
    elif bf < 3:
        return "Weak evidence for hypothesis" 
    elif bf < 10:
        return "Moderate evidence for hypothesis"
    elif bf < 30:
        return "Strong evidence for hypothesis"
    elif bf < 100:
        return "Very strong evidence for hypothesis"
    else:
        return "Decisive evidence for hypothesis"


# Example usage and testing
if __name__ == "__main__":
    calculator = BayesianCalculator()
    
    # Test basic calculations
    print("=== Bayesian Calculator Test ===")
    
    # Test 1: Basic Bayes Factor
    bf = calculator.calculate_bayes_factor(0.7, 0.8, 0.2)
    print(f"Bayes Factor: {bf:.3f} - {interpret_bayes_factor(bf)}")
    
    # Test 2: Posterior probability
    posterior = calculator.calculate_posterior_probability(0.7, bf)
    print(f"Posterior Probability: {posterior:.3f}")
    
    # Test 3: Multiple evidence aggregation
    evidence = [
        {'bayes_factor': 3.0, 'weight': 0.8},
        {'bayes_factor': 2.0, 'weight': 0.6},
        {'bayes_factor': 1.5, 'weight': 0.4}
    ]
    final_prob = calculator.aggregate_multiple_evidences(0.5, evidence)
    print(f"Aggregated Probability: {final_prob:.3f}")
    
    # Test 4: Confidence interval
    lower, upper = calculator.calculate_confidence_interval(0.7, 50)
    print(f"95% Confidence Interval: [{lower:.3f}, {upper:.3f}]")
    
    print("\nCalculation Summary:")
    print(calculator.get_calculation_summary())
