"""
Argument Probability Calculator for CSO
Implements the correct algorithm for calculating argument posterior probabilities using odds multiplication
"""

import logging
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict, deque
import json
from datetime import datetime
import math
import numpy as np

class ArgumentProbabilityCalculator:
    """
    Calculates argument posterior probabilities based on the correct odds multiplication algorithm
    """
    
    def __init__(self):
        self.used_chains_log = set()  # Log of chains already consumed
        self.calculation_log = []     # Detailed calculation log
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
    
    def calculate_all_argument_probabilities(self, nodes: List[Dict], edges: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Main method: calculate posterior probabilities for all arguments
        
        Args:
            nodes: List of all nodes
            edges: List of all edges
            
        Returns:
            Tuple of (updated_nodes, updated_edges)
        """
        self.logger.info("Starting calculation of argument probabilities using odds multiplication")
        
        # Deep-enough copies for local mutation
        updated_nodes = [node.copy() for node in nodes]
        updated_edges = [edge.copy() for edge in edges]
        
        # Collect statements and arguments
        statements = [node for node in updated_nodes if node['type'] == 'statement']
        arguments = [node for node in updated_nodes if node['type'] == 'argument']
        
        self.logger.info(f"Found {len(statements)} statements and {len(arguments)} arguments")
        
        # Reset used-chain registry for a fresh run
        self.used_chains_log.clear()
        
        # Process each argument node
        for argument in arguments:
            self.logger.info(f"Processing argument: {argument['id']}")
            
            # Posterior and VFE for this argument
            posterior_prob, vfe_metrics = self._calculate_argument_posterior(
                argument, statements, updated_nodes, updated_edges
            )
            
            # Count statement→argument edges for this argument
            edges_count = self._count_S_to_A_edges(argument['id'], updated_edges, updated_nodes)
            
            # F̄_k and predictability contribution (use full VFE, not accuracy_part alone)
            F_k_vfe = vfe_metrics.get('variational_free_energy', 0.0)
            F_bar_k = F_k_vfe / (1 + edges_count) if (1 + edges_count) > 0 else F_k_vfe
            predictability_contribution = np.exp(-F_bar_k)
            
            # Attach derived fields on the vfe dict
            vfe_metrics['F_bar_k'] = float(F_bar_k)
            vfe_metrics['edges_count'] = edges_count
            vfe_metrics['predictability_contribution'] = float(predictability_contribution)
            
            # Write back onto the argument node
            argument['posterior_probability'] = posterior_prob
            argument['vfe'] = vfe_metrics  # Attach VFE metrics
            
            self.logger.info(f"Argument {argument['id']}: prior={argument.get('prior_probability', 0.5):.3f}, "
                           f"posterior={posterior_prob:.3f}, VFE={vfe_metrics['variational_free_energy']:.4f}, "
                           f"F̄_k={F_bar_k:.4f}, edges={edges_count}")
        
        # Fill missing Bayes factors on edges (heuristic; analyst override preferred)
        self._calculate_and_add_bayes_factors(updated_nodes, updated_edges)
        
        # Graph-level Total Predictability
        self.total_predictability = self.calculate_total_predictability(updated_nodes, updated_edges)
        
        self.logger.info(f"Total Predictability: {self.total_predictability['total_predictability']:.4f} "
                        f"(from {self.total_predictability['arguments_count']} arguments)")
        
        # Persist calculation log
        self._save_calculation_log()
        
        return updated_nodes, updated_edges
    
    def _calculate_argument_posterior(self, argument: Dict, statements: List[Dict], 
                                    all_nodes: List[Dict], all_edges: List[Dict]) -> Tuple[float, Dict]:
        """
        Calculate posterior probability and VFE for a single argument using odds multiplication
        
        Args:
            argument: Target argument node
            statements: List of all statement nodes
            all_nodes: List of all nodes
            all_edges: List of all edges
            
        Returns:
            Tuple of (posterior_probability, vfe_metrics)
        """
        argument_id = argument['id']
        prior_prob = argument.get('prior_probability', 0.5)
        
        # All statement→argument chains for this argument
        all_chains = []
        
        for statement in statements:
            statement_id = statement['id']
            chains = self._find_all_chains(statement_id, argument_id, all_nodes, all_edges)
            
            # Pick one chain per (statement, argument) pair
            optimal_chain = self._select_optimal_chain(chains, statement_id, argument_id)
            
            if optimal_chain:
                all_chains.append(optimal_chain)
                self.logger.debug(f"Selected chain for {statement_id} → {argument_id}: {' → '.join(optimal_chain)}")
        
        if not all_chains:
            self.logger.warning(f"No valid chains found for argument {argument_id}, using prior probability")
            # Return VFE with zero evidence
            vfe_metrics = self.calculate_variational_free_energy(
                chain_probabilities=[],
                prior_prob=prior_prob,
                posterior_prob=prior_prob
            )
            return prior_prob, vfe_metrics
        
        # Per-chain probability, then combine (not raw odds multiply)
        chain_probabilities = []
        chain_details = []
        
        for i, chain in enumerate(all_chains):
            # End-to-end probability along this chain
            chain_prob = self._calculate_chain_probability(chain, all_nodes, all_edges)
            chain_probabilities.append(chain_prob)
            
            # Odds for logging
            odds = chain_prob / (1 - chain_prob) if chain_prob < 1.0 else float('inf')
            
            chain_info = {
                'chain': ' → '.join(chain),
                'length': len(chain),
                'odds': odds
            }
            chain_details.append(chain_info)
            
            self.logger.info(f"  Chain {i+1}: {chain_info['chain']} (length: {chain_info['length']}, prob: {chain_prob:.4f}, odds: {odds:.4f})")
        
        # Combine chains as independent support: P = 1 - ∏(1 - P_i)
        if chain_probabilities:
            # Noisy-OR style combination of independent supports
            combined_prob = 1.0
            for prob in chain_probabilities:
                combined_prob *= (1.0 - prob)
            posterior_prob = 1.0 - combined_prob
            
            # Log combined draw
            total_odds = posterior_prob / (1 - posterior_prob) if posterior_prob < 1.0 else float('inf')
            self.logger.info(f"  Correct Bayesian combination: P = {posterior_prob:.4f}, odds = {total_odds:.4f}")
        else:
            posterior_prob = prior_prob
        
        # Clamp to [0, 1]
        posterior_prob = max(0.0, min(1.0, posterior_prob))
        
        self.logger.info(f"  Final posterior probability: {posterior_prob:.4f}")
        
        # VFE metrics
        vfe_metrics = self.calculate_variational_free_energy(
            chain_probabilities=chain_probabilities,
            prior_prob=prior_prob,
            posterior_prob=posterior_prob
        )
        
        # Log run including VFE
        self._log_argument_calculation(argument_id, all_chains, chain_probabilities, posterior_prob, chain_details, vfe_metrics)
        
        return posterior_prob, vfe_metrics
    
    def _find_all_chains(self, source_id: str, target_id: str, 
                         all_nodes: List[Dict], all_edges: List[Dict]) -> List[List[str]]:
        """
        Find all possible chains from source to target using BFS
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            all_nodes: List of all nodes
            all_edges: List of all edges
            
        Returns:
            List of chains (each chain is a list of node IDs)
        """
        # Build adjacency for path search
        graph = defaultdict(list)
        for edge in all_edges:
            graph[edge['source']].append(edge['target'])
        
        # Node lookup
        node_lookup = {node['id']: node for node in all_nodes}
        
        # BFS enumerate paths
        all_chains = []
        queue = deque([(source_id, [source_id])])
        max_depth = 5  # Cap search depth
        
        while queue:
            current_id, current_chain = queue.popleft()
            
            # Depth guard
            if len(current_chain) > max_depth:
                continue
            
            if current_id == target_id:
                all_chains.append(current_chain)
                continue
            
            # Expand frontier
            for next_id in graph[current_id]:
                if next_id not in current_chain:  # No cycles in path
                    new_chain = current_chain + [next_id]
                    queue.append((next_id, new_chain))
        
        return all_chains
    
    def _select_optimal_chain(self, chains: List[List[str]], statement_id: str, argument_id: str) -> Optional[List[str]]:
        """
        Select optimal chain according to the rules:
        1. Prioritize longer chains
        2. If equal length, choose first by ID
        3. Avoid already used chains and subsets
        
        Args:
            chains: List of available chains
            statement_id: Source statement ID
            argument_id: Target argument ID
            
        Returns:
            Selected optimal chain or None
        """
        if not chains:
            return None
        
        # Drop chains already used or subsumed
        available_chains = []
        for chain in chains:
            chain_tuple = tuple(chain)
            
            # Skip if chain already logged
            if chain_tuple in self.used_chains_log:
                continue
            
            # Skip if subset of a used chain
            is_subset = False
            for used_chain in self.used_chains_log:
                if self._is_subset(chain, list(used_chain)):
                    is_subset = True
                    break
            
            if not is_subset:
                available_chains.append(chain)
        
        if not available_chains:
            return None
        
        # Prefer longer chains, then lexicographic tie-break
        available_chains.sort(key=lambda x: (-len(x), x[0]))
        
        selected_chain = available_chains[0]
        
        # Mark chain as consumed
        self.used_chains_log.add(tuple(selected_chain))
        
        return selected_chain
    
    def _is_subset(self, chain: List[str], used_chain: List[str]) -> bool:
        """
        Check if chain is a subset of used_chain
        
        Args:
            chain: Chain to check
            used_chain: Previously used chain
            
        Returns:
            True if chain is subset of used_chain
        """
        if len(chain) >= len(used_chain):
            return False
        
        # True if chain is a contiguous subsequence of used_chain
        for i in range(len(used_chain) - len(chain) + 1):
            if used_chain[i:i+len(chain)] == chain:
                return True
        
        return False
    
    def _calculate_chain_probability(self, chain: List[str], 
                                   all_nodes: List[Dict], all_edges: List[Dict]) -> float:
        """
        Calculate final probability along a chain using proper Bayesian updating
        
        Args:
            chain: Chain of node IDs
            all_nodes: List of all nodes
            all_edges: List of all edges
            
        Returns:
            Final probability for the chain
        """
        if len(chain) < 2:
            return 0.5  # Neutral probability
        
        # Node lookup
        node_lookup = {node['id']: node for node in all_nodes}
        
        # Start from chain head prior
        current_prob = node_lookup[chain[0]].get('prior_probability', 0.5)
        
        # Walk the chain updating probability
        for i in range(1, len(chain)):
            current_node_id = chain[i]
            previous_node_id = chain[i-1]
            
            # Edge from previous to current
            edge = self._find_edge(previous_node_id, current_node_id, all_edges)
            if not edge:
                continue
            
            # Skip bias / quotation / question hops except final hop
            current_node = node_lookup.get(current_node_id)
            if current_node and current_node['type'] in ['cognitive_bias', 'quotation', 'question'] and i < len(chain) - 1:
                continue
            
            # One-step BF update
            current_prob = self._update_probability_with_edge(
                current_prob, edge, current_node
            )
        
        return max(0.001, min(0.999, current_prob))  # Clamp

    def _calculate_chain_odds(self, chain: List[str], 
                             all_nodes: List[Dict], all_edges: List[Dict]) -> float:
        """
        Calculate odds along a chain using Bayesian updating
        
        Args:
            chain: Chain of node IDs
            all_nodes: List of all nodes
            all_edges: List of all edges
            
        Returns:
            Calculated odds for the chain
        """
        if len(chain) < 2:
            return 1.0  # Neutral odds
        
        # Node lookup
        node_lookup = {node['id']: node for node in all_nodes}
        
        # Start from chain head prior
        current_prob = node_lookup[chain[0]].get('prior_probability', 0.5)
        
        # Walk the chain updating probability
        for i in range(1, len(chain)):
            current_node_id = chain[i]
            previous_node_id = chain[i-1]
            
            # Edge from previous to current
            edge = self._find_edge(previous_node_id, current_node_id, all_edges)
            if not edge:
                continue
            
            # Skip bias / quotation / question hops except final hop
            current_node = node_lookup.get(current_node_id)
            if current_node and current_node['type'] in ['cognitive_bias', 'quotation', 'question'] and i < len(chain) - 1:
                continue
            
            # One-step BF update
            current_prob = self._update_probability_with_edge(
                current_prob, edge, current_node
            )
        
        # Probability to odds
        odds = current_prob / (1 - current_prob) if current_prob < 1.0 else float('inf')
        
        return max(0.001, odds)  # Floor odds to avoid zero
    
    def _find_edge(self, source_id: str, target_id: str, all_edges: List[Dict]) -> Optional[Dict]:
        """
        Find edge between source and target nodes
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            all_edges: List of all edges
            
        Returns:
            Edge dictionary or None
        """
        for edge in all_edges:
            if edge['source'] == source_id and edge['target'] == target_id:
                return edge
        return None
    
    def _update_probability_with_edge(self, prior_prob: float, edge: Dict, target_node: Optional[Dict]) -> float:
        """
        Update probability using Bayesian formula with edge information
        
        Args:
            prior_prob: Prior probability from previous node
            edge: Edge connecting nodes
            target_node: Target node (can be None)
            
        Returns:
            Updated probability
        """
        # BF from edge or heuristic from relation/strength
        bayes_factor = edge.get('bayes_factor')
        
        if bayes_factor is None:
            # Heuristic BF from relation and strength
            relation = edge.get('relation', 'influences')
            strength = edge.get('strength', 0.5)
            weight = edge.get('weight', 1.0)
            
            if relation == 'supports':
                # supports: BF > 1
                bayes_factor = 1.0 + strength * weight * 2.0
            elif relation == 'contradicts':
                # contradicts: BF < 1
                bayes_factor = 1.0 - strength * weight * 0.8
                bayes_factor = max(0.1, bayes_factor)  # BF floor
            else:
                # default edge
                bayes_factor = 1.0
        
        # Bayes update step
        posterior_prob = (prior_prob * bayes_factor) / (prior_prob * bayes_factor + (1 - prior_prob))
        
        return max(0.001, min(0.999, posterior_prob))  # Clamp
    
    def calculate_variational_free_energy(
        self,
        chain_probabilities: List[float],
        prior_prob: float,
        posterior_prob: float
    ) -> Dict[str, float]:
        """
        Calculate Variational Free Energy (VFE) for an argument
        
        VFE = -ln(marginal_evidence) + KL[q||p]
        
        where:
        - marginal_evidence: Probability of observing the evidence given the model
        - KL[q||p]: Kullback-Leibler divergence between posterior (q) and prior (p)
        
        Args:
            chain_probabilities: List of probabilities for each evidence chain
            prior_prob: Prior probability of argument
            posterior_prob: Posterior probability of argument
            
        Returns:
            Dictionary with VFE metrics:
            - variational_free_energy: Main quality metric (lower is better)
            - log_evidence: Surprise term (-ln(marginal_evidence))
            - accuracy_part: Accuracy part (F_k^acc) - only S→A factors, without KL prior
            - marginal_evidence: Raw evidence probability
            - kl_divergence: Complexity penalty (KL divergence)
        """
        # 1. Calculate marginal evidence
        if chain_probabilities:
            marginal_evidence = 1.0
            for prob in chain_probabilities:
                marginal_evidence *= (1.0 - prob)
            marginal_evidence = 1.0 - marginal_evidence
            marginal_evidence = max(marginal_evidence, 1e-10)  # Avoid log(0)
            log_evidence = -np.log(marginal_evidence)
        else:
            marginal_evidence = 1.0
            log_evidence = 0.0
        
        # Accuracy part: F_k^acc = log_evidence (only S→A factors, without KL prior)
        accuracy_part = log_evidence
        
        # 2. Calculate KL divergence: KL(q||p) = q * ln(q/p) for discrete case
        # For binary outcomes: KL = posterior * ln(posterior/prior) + (1-posterior) * ln((1-posterior)/(1-prior))
        prior_safe = max(prior_prob, 1e-10)
        prior_complement = max(1 - prior_prob, 1e-10)
        posterior_safe = max(posterior_prob, 1e-10)
        posterior_complement = max(1 - posterior_prob, 1e-10)
        
        kl_divergence = (
            posterior_safe * np.log(posterior_safe / prior_safe) +
            posterior_complement * np.log(posterior_complement / prior_complement)
        )
        
        # 3. Total Variational Free Energy
        variational_free_energy = log_evidence + kl_divergence
        
        return {
            'variational_free_energy': float(variational_free_energy),
            'log_evidence': float(log_evidence),
            'accuracy_part': float(accuracy_part),  # Accuracy part without KL
            'marginal_evidence': float(marginal_evidence),
            'kl_divergence': float(kl_divergence)
        }
    
    def _calculate_and_add_bayes_factors(self, nodes: List[Dict], edges: List[Dict]):
        """
        Calculate and add Bayes Factor for all edges that don't have it
        
        NOTE: In CSO, Bayes Factor should be set by analyst, not calculated automatically.
        This method is provided for reference calculations only.
        
        Args:
            nodes: List of all nodes
            edges: List of all edges
        """
        self.logger.info("Calculating Bayes Factors for edges...")
        
        # Node lookup
        node_lookup = {node['id']: node for node in nodes}
        
        bayes_factors_added = 0
        
        for edge in edges:
            # Keep analyst-provided BF
            if 'bayes_factor' in edge and edge['bayes_factor'] is not None:
                continue
            
            source_id = edge['source']
            target_id = edge['target']
            relation = edge.get('relation', 'influences')
            strength = edge.get('strength', 0.5)
            weight = edge.get('weight', 1.0)
            
            # Resolve endpoints
            source_node = node_lookup.get(source_id)
            target_node = node_lookup.get(target_id)
            
            if not source_node or not target_node:
                continue
            
            # Synthesize BF
            bayes_factor = self._calculate_bayes_factor_for_edge(
                source_node, target_node, relation, strength, weight
            )
            
            # Write onto edge
            edge['bayes_factor'] = bayes_factor
            bayes_factors_added += 1
            
            self.logger.debug(f"Added BF={bayes_factor:.3f} to edge {source_id} → {target_id} ({relation})")
        
        self.logger.info(f"Added Bayes Factors to {bayes_factors_added} edges")
    
    def _calculate_bayes_factor_for_edge(self, source_node: Dict, target_node: Dict, 
                                        relation: str, strength: float, weight: float) -> float:
        """
        Calculate Bayes Factor for an edge based on relationship type and node probabilities
        
        NOTE: In CSO, Bayes Factor should be set by analyst, not calculated automatically.
        This method is provided for reference calculations only.
        
        Args:
            source_node: Source node
            target_node: Target node
            relation: Type of relationship
            strength: Strength of relationship
            weight: Weight of relationship
            
        Returns:
            Calculated Bayes Factor
        """
        # Source node probability
        source_prob = source_node.get('posterior_probability') or source_node.get('prior_probability', 0.5)
        
        # Relation-dependent BF scaffold
        if relation == 'supports':
            # supports: high source credence → higher BF
            base_bf = 1.0 + (source_prob * strength * weight * 8.0)  # ~max BF 9
            
        elif relation == 'contradicts':
            # contradicts: pull BF below 1
            base_bf = 1.0 - (source_prob * strength * weight * 0.9)  # ~min BF 0.1
            base_bf = max(0.05, base_bf)  # BF floor
            
        elif relation == 'influences':
            # influences: moderate BF
            if source_prob > 0.5:
                base_bf = 1.0 + ((source_prob - 0.5) * strength * weight * 4.0)  # ~max 3
            else:
                base_bf = 1.0 - ((0.5 - source_prob) * strength * weight * 0.6)  # ~min 0.4
                base_bf = max(0.2, base_bf)
                
        elif relation == 'related_to':
            # related_to: weak tilt
            base_bf = 1.0 + ((source_prob - 0.5) * strength * weight * 2.0)  # ~max 2
            
        else:
            # fallback
            base_bf = 1.0
            
        # Clamp BF
        return max(0.05, min(20.0, base_bf))
    
    def _count_S_to_A_edges(self, argument_id: str, all_edges: List[Dict], 
                            all_nodes: List[Dict]) -> int:
        """
        Count number of direct edges S→A for an argument
        
        Args:
            argument_id: ID of the argument
            all_edges: List of all edges
            all_nodes: List of all nodes (for type checking)
            
        Returns:
            Number of direct edges from statements to this argument
        """
        node_lookup = {node['id']: node for node in all_nodes}
        count = 0
        
        for edge in all_edges:
            if edge['target'] == argument_id:
                source_node = node_lookup.get(edge['source'])
                if source_node and source_node['type'] == 'statement':
                    count += 1
        
        return count
    
    def calculate_total_predictability(self, nodes: List[Dict], edges: List[Dict]) -> Dict:
        """
        Calculate Total Predictability for the entire argumentation system
        
        P_tot = Σ_k e^(-F̄_k)
        where F̄_k = F_k^VFE / (1 + |E_k|)
        
        F_k^VFE is the full Variational Free Energy (variational_free_energy = accuracy_part + kl_divergence)
        |E_k| is the number of direct edges S→A for argument k
        
        Args:
            nodes: List of all nodes (with calculated VFE)
            edges: List of all edges
            
        Returns:
            Dictionary with Total Predictability metrics
        """
        arguments = [node for node in nodes if node['type'] == 'argument' and 'vfe' in node]
        
        if not arguments:
            return {
                'total_predictability': 0.0,
                'arguments_count': 0,
                'arguments_contributions': [],
                'average_contribution': 0.0
            }
        
        contributions = []
        P_tot = 0.0
        
        for arg in arguments:
            arg_id = arg['id']
            vfe_metrics = arg['vfe']
            
            # F_k^VFE = variational_free_energy (accuracy_part + kl_divergence)
            F_k_vfe = vfe_metrics.get('variational_free_energy', 0.0)
            
            # |E_k| = count of S→A edges
            E_k_count = self._count_S_to_A_edges(arg_id, edges, nodes)
            
            # F̄_k = F_k^VFE / (1 + |E_k|)
            F_bar_k = F_k_vfe / (1 + E_k_count) if (1 + E_k_count) > 0 else F_k_vfe
            
            # Contribution exp(-F̄_k) toward P_tot
            contribution = np.exp(-F_bar_k)
            P_tot += contribution
            
            contributions.append({
                'argument_id': arg_id,
                'F_k_vfe': float(F_k_vfe),
                'edges_count': E_k_count,
                'F_bar_k': float(F_bar_k),
                'contribution': float(contribution)
            })
        
        # Sort by contribution descending
        contributions.sort(key=lambda x: x['contribution'], reverse=True)
        
        return {
            'total_predictability': float(P_tot),
            'arguments_count': len(arguments),
            'arguments_contributions': contributions,
            'average_contribution': float(P_tot / len(arguments)) if arguments else 0.0
        }
    
    def _log_argument_calculation(self, argument_id: str, chains: List[List[str]], 
                                 chain_probabilities: List[float], posterior_prob: float, 
                                 chain_details: List[Dict], vfe_metrics: Optional[Dict] = None,
                                 edges_count: Optional[int] = None):
        """
        Log detailed calculation for an argument including VFE metrics and Total Predictability
        
        Args:
            argument_id: Argument ID
            chains: All chains used
            chain_probabilities: Probabilities for each chain
            posterior_prob: Final posterior probability
            chain_details: Detailed information about each chain
            vfe_metrics: VFE metrics dictionary (optional)
            edges_count: Number of S→A edges (optional)
        """
        # Probabilities to odds for logging
        individual_odds = [prob / (1 - prob) if prob < 1.0 else float('inf') for prob in chain_probabilities]
        total_odds = posterior_prob / (1 - posterior_prob) if posterior_prob < 1.0 else float('inf')
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'argument_id': argument_id,
            'chains': [' → '.join(chain) for chain in chains],
            'chain_details': chain_details,
            'individual_odds': individual_odds,
            'total_odds': total_odds,
            'posterior_probability': posterior_prob,
            'chains_count': len(chains),
            'calculation_method': 'bayesian_inference',
            'vfe_metrics': vfe_metrics  # VFE block in log
        }
        
        # Optional Total Predictability fields
        if vfe_metrics and edges_count is not None:
            log_entry['edges_count'] = edges_count
            if 'F_bar_k' in vfe_metrics:
                log_entry['F_bar_k'] = vfe_metrics['F_bar_k']
                log_entry['predictability_contribution'] = vfe_metrics.get('predictability_contribution', 0.0)
        self.calculation_log.append(log_entry)
        
        # Debug output
        self.logger.debug(f"=== CALCULATION DETAILS FOR {argument_id} ===")
        self.logger.debug(f"Chains found: {len(chains)}")
        for i, (detail, prob) in enumerate(zip(chain_details, chain_probabilities)):
            self.logger.debug(f"  Chain {i+1}: {detail['chain']} (prob: {prob:.4f}, odds: {detail['odds']:.4f})")
        self.logger.debug(f"Combined probability: {posterior_prob:.4f}")
        self.logger.debug(f"Total odds: {total_odds:.4f}")
        self.logger.debug("=" * 50)
    
    def _save_calculation_log(self):
        """Save detailed calculation log to file"""
        try:
            log_file = 'argument_calculation_log.json'
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.calculation_log, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Calculation log saved to {log_file}")
        except Exception as e:
            self.logger.error(f"Failed to save calculation log: {e}")
    
    def calculate_probabilities_without_auto_bayes_factors(self, nodes: List[Dict], edges: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Calculate argument probabilities using only analyst-provided Bayes Factors
        Does NOT automatically generate Bayes Factors for edges
        
        Args:
            nodes: List of all nodes
            edges: List of all edges
            
        Returns:
            Tuple of (updated_nodes, updated_edges)
        """
        self.logger.info("Starting calculation of argument probabilities WITHOUT auto-generating Bayes Factors")
        
        # Deep-enough copies for local mutation
        updated_nodes = [node.copy() for node in nodes]
        updated_edges = [edge.copy() for edge in edges]
        
        # Collect statements and arguments
        statements = [node for node in updated_nodes if node['type'] == 'statement']
        arguments = [node for node in updated_nodes if node['type'] == 'argument']
        
        self.logger.info(f"Found {len(statements)} statements and {len(arguments)} arguments")
        
        # Reset used-chain registry for a fresh run
        self.used_chains_log.clear()
        
        # Process each argument node
        for argument in arguments:
            self.logger.info(f"Processing argument: {argument['id']}")
            
            # Posterior and VFE for this argument
            posterior_prob, vfe_metrics = self._calculate_argument_posterior(
                argument, statements, updated_nodes, updated_edges
            )
            
            # Count statement→argument edges for this argument
            edges_count = self._count_S_to_A_edges(argument['id'], updated_edges, updated_nodes)
            
            # F̄_k and predictability contribution (use full VFE, not accuracy_part alone)
            F_k_vfe = vfe_metrics.get('variational_free_energy', 0.0)
            F_bar_k = F_k_vfe / (1 + edges_count) if (1 + edges_count) > 0 else F_k_vfe
            predictability_contribution = np.exp(-F_bar_k)
            
            # Attach derived fields on the vfe dict
            vfe_metrics['F_bar_k'] = float(F_bar_k)
            vfe_metrics['edges_count'] = edges_count
            vfe_metrics['predictability_contribution'] = float(predictability_contribution)
            
            # Write back onto the argument node
            argument['posterior_probability'] = posterior_prob
            argument['vfe'] = vfe_metrics  # Attach VFE metrics
            
            self.logger.info(f"Argument {argument['id']}: prior={argument.get('prior_probability', 0.5):.3f}, "
                           f"posterior={posterior_prob:.3f}, VFE={vfe_metrics['variational_free_energy']:.4f}, "
                           f"F̄_k={F_bar_k:.4f}, edges={edges_count}")
        
        # Do not auto-fill BFs — analyst values only
        self.logger.info("Skipping automatic Bayes Factor generation - using only analyst-provided values")
        
        # Graph-level Total Predictability
        self.total_predictability = self.calculate_total_predictability(updated_nodes, updated_edges)
        
        self.logger.info(f"Total Predictability: {self.total_predictability['total_predictability']:.4f} "
                        f"(from {self.total_predictability['arguments_count']} arguments)")
        
        # Persist calculation log
        self._save_calculation_log()
        
        return updated_nodes, updated_edges

    def get_calculation_summary(self) -> Dict:
        """Get summary of calculations"""
        total_chains = sum(len(entry['chains']) for entry in self.calculation_log)
        
        summary = {
            'total_arguments_processed': len(self.calculation_log),
            'total_chains_used': total_chains,
            'used_chains_count': len(self.used_chains_log),
            'calculation_log': self.calculation_log
        }
        
        # Attach Total Predictability if computed
        if hasattr(self, 'total_predictability'):
            summary['total_predictability'] = self.total_predictability
        
        return summary

# Example usage and testing
if __name__ == "__main__":
    # Test the calculator with sample data
    calculator = ArgumentProbabilityCalculator()
    
    # Sample nodes
    nodes = [
        {"id": "stat1", "type": "statement", "prior_probability": 0.6},
        {"id": "stat2", "type": "statement", "prior_probability": 0.7}, 
        {"id": "arg1", "type": "argument", "prior_probability": 0.5}
    ]
    
    # Sample edges
    edges = [
        {"source": "stat1", "target": "arg1", "relation": "supports", "weight": 0.8, "bayes_factor": 3.0},
        {"source": "stat2", "target": "arg1", "relation": "supports", "weight": 0.7, "bayes_factor": 2.5}
    ]
    
    updated_nodes, updated_edges = calculator.calculate_all_argument_probabilities(nodes, edges)
    
    print("=== Argument Probability Calculator Test ===")
    for node in updated_nodes:
        if node['type'] == 'argument':
            print(f"Argument {node['id']}: prior={node.get('prior_probability', 0.5):.3f}, "
                  f"posterior={node.get('posterior_probability', 0.5):.3f}")
    
    print("\nCalculation Summary:")
    print(calculator.get_calculation_summary())

