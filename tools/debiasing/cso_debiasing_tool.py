"""
CSO Debiasing Tool
Removes cognitive bias influence from argumentation by adjusting Bayes factors
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging
import math

class CSODebiasingTool:
    """
    Tool for removing cognitive bias influence from CSO argumentation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
    def debias_cso_file(self, cso_file_path: str) -> str:
        """
        Main method to debias a CSO file
        
        Args:
            cso_file_path: Path to the CSO JSON file
            
        Returns:
            Path to the generated debiased file
        """
        try:
            # Load CSO file
            with open(cso_file_path, 'r', encoding='utf-8') as f:
                cso_data = json.load(f)
            
            self.logger.info(f"Loaded CSO file: {cso_file_path}")
            
            # Extract components
            nodes = cso_data.get('nodes', [])
            edges = cso_data.get('edges', [])
            
            # Find cognitive biases and their connections
            bias_connections = self._find_cognitive_bias_connections(nodes, edges)
            
            if not bias_connections:
                self.logger.info("No cognitive biases found in the file")
                return None
            
            # Calculate correction factors for affected nodes
            node_corrections = self._calculate_node_corrections(nodes, bias_connections)
            
            # Recalculate argument probabilities
            recalculated_arguments = self._recalculate_argument_probabilities(
                nodes, edges, node_corrections
            )
            
            # Generate debiased output
            debiased_data = self._generate_debiased_output(
                cso_file_path, bias_connections, node_corrections, recalculated_arguments, nodes, edges
            )
            
            # Save debiased file
            output_path = self._generate_output_path(cso_file_path)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(debiased_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Debiased file saved: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error processing file {cso_file_path}: {str(e)}")
            raise
    
    def _find_cognitive_bias_connections(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, Dict]:
        """
        Find all cognitive bias connections and their affected nodes
        """
        bias_connections = {}
        
        # Find cognitive bias nodes
        cognitive_biases = [node for node in nodes if node['type'] == 'cognitive_bias']
        
        self.logger.info(f"Found {len(cognitive_biases)} cognitive biases")
        
        for bias in cognitive_biases:
            bias_id = bias['id']
            bias_connections[bias_id] = {
                'bias_info': bias,
                'affected_nodes': [],
                'connections': []
            }
            
            # Find edges where this bias is the source
            for edge in edges:
                if edge['source'] == bias_id and edge['relation'] == 'related_to':
                    target_node = next((n for n in nodes if n['id'] == edge['target']), None)
                    if target_node:
                        bias_connections[bias_id]['affected_nodes'].append(target_node)
                        bias_connections[bias_id]['connections'].append(edge)
        
        return bias_connections
    
    def _calculate_node_corrections(self, nodes: List[Dict], bias_connections: Dict) -> Dict[str, Dict]:
        """
        Calculate correction factors for nodes affected by cognitive biases
        """
        node_corrections = {}
        
        for bias_id, bias_data in bias_connections.items():
            # Get bias weight from the edge connection
            for connection in bias_data['connections']:
                bias_weight = connection.get('weight', 0.8)  # Default weight if not specified
                
                for affected_node in bias_data['affected_nodes']:
                    node_id = affected_node['id']
                    
                    if node_id not in node_corrections:
                        node_corrections[node_id] = {
                            'node_info': affected_node,
                            'correction_factor': 1.0,
                            'affecting_biases': [],
                            'bias_weights': []
                        }
                    
                    # Apply multiplicative correction: (1 - bias_weight)
                    node_corrections[node_id]['correction_factor'] *= (1 - bias_weight)
                    node_corrections[node_id]['affecting_biases'].append(bias_id)
                    node_corrections[node_id]['bias_weights'].append(bias_weight)
        
        return node_corrections
    
    def _recalculate_argument_probabilities(self, nodes: List[Dict], edges: List[Dict], 
                                         node_corrections: Dict) -> List[Dict]:
        """
        Recalculate argument probabilities using corrected Bayes factors
        """
        arguments = [node for node in nodes if node['type'] == 'argument']
        recalculated = []
        
        for argument in arguments:
            arg_id = argument['id']
            
            # Find all edges supporting this argument
            supporting_edges = [edge for edge in edges 
                              if edge['target'] == arg_id and edge['relation'] == 'supports']
            
            original_odds = 1.0
            corrected_odds = 1.0
            chain_details = []
            
            # Calculate odds from supporting chains
            for edge in supporting_edges:
                source_id = edge['source']
                original_bf = edge.get('bayes_factor', 1.0)
                
                # Apply correction if source node is affected by biases
                correction_factor = node_corrections.get(source_id, {}).get('correction_factor', 1.0)
                corrected_bf = original_bf * correction_factor
                
                # Convert bayes factors to odds ratios
                original_odds *= original_bf
                corrected_odds *= corrected_bf
                
                chain_details.append({
                    'chain': f"{source_id} → {arg_id}",
                    'original_bayes_factor': round(original_bf, 6),
                    'corrected_bayes_factor': round(corrected_bf, 6),
                    'correction_factor': round(correction_factor, 6),
                    'correction_reason': self._get_correction_reason(source_id, node_corrections)
                })
            
            # Calculate probabilities from odds
            # posterior = odds / (1 + odds)
            original_posterior = original_odds / (1 + original_odds) if original_odds > 0 else 0
            corrected_posterior = corrected_odds / (1 + corrected_odds) if corrected_odds > 0 else 0
            
            # Get original posterior from the file if available
            file_original_posterior = argument.get('posterior_probability', original_posterior)
            
            change_percentage = 0
            if file_original_posterior > 0:
                change_percentage = ((corrected_posterior - file_original_posterior) / file_original_posterior) * 100
            
            recalculated.append({
                'argument_id': arg_id,
                'argument_text': argument.get('text', ''),
                'original_posterior': round(file_original_posterior, 6),
                'debiased_posterior': round(corrected_posterior, 6),
                'change_percentage': round(change_percentage, 1),
                'original_odds': round(original_odds, 6),
                'debiased_odds': round(corrected_odds, 6),
                'chains_affected': chain_details
            })
        
        return recalculated
    
    def _get_correction_reason(self, node_id: str, node_corrections: Dict) -> str:
        """
        Generate human-readable reason for correction
        """
        if node_id not in node_corrections:
            return "No bias influence detected"
        
        affecting_biases = node_corrections[node_id]['affecting_biases']
        bias_names = []
        
        for bias_id in affecting_biases:
            # Extract readable bias name
            if 'BC1-S5-B21' in bias_id:
                bias_names.append('Overconfidence Effect')
            elif 'BC1-S5-B13' in bias_id:
                bias_names.append('Optimism Bias')
            elif 'BC1-S5-B8' in bias_id:
                bias_names.append('Illusion of Control')
            elif 'BC1-S5-B10' in bias_id:
                bias_names.append('Self-serving Bias')
            elif 'BC1-S5-B7' in bias_id:
                bias_names.append('Illusory Superiority')
            else:
                bias_names.append(bias_id)
        
        if len(bias_names) == 1:
            return f"Affected by {bias_names[0]}"
        else:
            return f"Affected by multiple biases: {', '.join(bias_names)}"
    
    def _get_edge_bayes_factors(self, node_id: str, edges: List[Dict]) -> List[float]:
        """
        Get Bayes factors for all outgoing edges from a node
        """
        outgoing_edges = [edge for edge in edges if edge['source'] == node_id]
        return [edge.get('bayes_factor', 1.0) for edge in outgoing_edges]
    
    def _generate_debiased_output(self, original_file_path: str, bias_connections: Dict, 
                                 node_corrections: Dict, recalculated_arguments: List[Dict],
                                 nodes: List[Dict], edges: List[Dict]) -> Dict:
        """
        Generate the debiased output structure
        """
        # Count total biases and affected nodes
        total_biases = len(bias_connections)
        total_affected_nodes = len(node_corrections)
        total_arguments = len(recalculated_arguments)
        
        # Prepare cognitive biases summary
        biases_removed = []
        for bias_id, bias_data in bias_connections.items():
            # Get bias weight from connections
            bias_weights = [conn.get('weight', 0.8) for conn in bias_data['connections']]
            avg_bias_weight = sum(bias_weights) / len(bias_weights) if bias_weights else 0.8
            
            biases_removed.append({
                'bias_id': bias_id,
                'bias_name': bias_data['bias_info'].get('text', bias_id),
                'bias_weight': avg_bias_weight,
                'affected_nodes': [node['id'] for node in bias_data['affected_nodes']],
                'correction_factor': round(1 - avg_bias_weight, 6)
            })
        
        # Prepare node corrections summary
        node_corrections_summary = []
        for node_id, correction_data in node_corrections.items():
            original_bayes_factors = self._get_edge_bayes_factors(node_id, edges)
            corrected_bayes_factors = [bf * correction_data['correction_factor'] for bf in original_bayes_factors]
            
            node_corrections_summary.append({
                'node_id': node_id,
                'node_type': correction_data['node_info']['type'],
                'node_text': correction_data['node_info'].get('text', ''),
                'original_bayes_factors': [round(bf, 6) for bf in original_bayes_factors],
                'correction_factor': round(correction_data['correction_factor'], 6),
                'corrected_bayes_factors': [round(bf, 6) for bf in corrected_bayes_factors],
                'cognitive_biases_influencing': correction_data['affecting_biases'],
                'bias_weights_applied': correction_data['bias_weights']
            })
        
        return {
            "debiasing_summary": {
                "original_file": str(Path(original_file_path).name),
                "debiasing_timestamp": datetime.now().isoformat(),
                "total_cognitive_biases_found": total_biases,
                "total_nodes_affected": total_affected_nodes,
                "total_arguments_recalculated": total_arguments
            },
            "cognitive_biases_removed": biases_removed,
            "node_corrections": node_corrections_summary,
            "argument_recalculations": recalculated_arguments,
            "debiasing_methodology": {
                "description": "Bayes factors for nodes connected to cognitive biases are multiplied by (1 - bias_weight) to remove bias influence",
                "formula": "corrected_bayes_factor = original_bayes_factor * (1 - bias_weight)",
                "multiple_biases_formula": "correction_factor = ∏(1 - bias_weight_i) for all biases affecting the node",
                "assumptions": [
                    "Cognitive biases uniformly affect all connections from affected nodes",
                    "Bias weights represent the degree of influence to be removed",
                    "Multiple biases affecting the same node have multiplicative correction effects",
                    "Posterior probabilities are recalculated using corrected Bayes factors"
                ]
            }
        }
    
    def _generate_output_path(self, input_path: str) -> str:
        """
        Generate output path with 'debiased' suffix
        """
        input_path = Path(input_path)
        output_name = f"{input_path.stem}_debiased{input_path.suffix}"
        return str(input_path.parent / output_name)

def main():
    """
    Main function for command line usage
    """
    if len(sys.argv) != 2:
        print("Usage: python cso_debiasing_tool.py <path_to_cso_file>")
        print("Example: python cso_debiasing_tool.py 'demo-site/data_bm_cso/author/book_chapter.json'")
        sys.exit(1)
    
    cso_file_path = sys.argv[1]
    
    if not os.path.exists(cso_file_path):
        print(f"Error: File {cso_file_path} not found")
        sys.exit(1)
    
    try:
        debiasing_tool = CSODebiasingTool()
        output_path = debiasing_tool.debias_cso_file(cso_file_path)
        
        if output_path:
            print(f"Successfully created debiased file: {output_path}")
        else:
            print("No cognitive biases found in the file - no debiasing needed")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
















