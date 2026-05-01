"""
Argumentation strengthener for CSO: policy-driven argumentation improvement.
"""

import os
import json
import logging
import glob
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set, Any
from collections import defaultdict, deque
import sys
import numpy as np

# Add paths for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
bayesian_tools_path = os.path.join(project_root, 'tools', 'bayesian')
sys.path.append(bayesian_tools_path)

from argument_probability_calculator import ArgumentProbabilityCalculator


class ArgumentationStrengthener:
    """
    Improves CSO argumentation by applying a rotating set of policies via LLM.
    """

    def __init__(self, llm_processor, config: Dict[str, Any]):
        """
        Initialize the argumentation strengthener.

        Args:
            llm_processor: LLMProcessorBM instance for LLM calls.
            config: Pipeline configuration (e.g. config_bm_test.yaml).
        """
        self.llm_processor = llm_processor
        self.config = config

        self.strengthening_config = config.get('pipeline', {}).get('argumentation_strengthening', {})
        self.enabled = self.strengthening_config.get('enabled', False)
        self.policies_file = self.strengthening_config.get('policies_file', 'config/policies.json')
        self.n_last_politics = self.strengthening_config.get('n_last_politics', 3)
        self.total_predictability_diff_min = self.strengthening_config.get('total_predictability_diff_min', 0.01)
        self.max_upd = self.strengthening_config.get('max_upd', 100)

        self.calculator = ArgumentProbabilityCalculator()

        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

        self.policies = self._load_policies()

        self.policy_application_counter = 0
        
    def _load_policies(self) -> List[Dict]:
        """
        Load policies from JSON file.

        Returns:
            List of policy dicts.
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)

        if not os.path.isabs(self.policies_file):
            policies_path = os.path.join(base_dir, self.policies_file)
        else:
            policies_path = self.policies_file

        if not os.path.exists(policies_path):
            self.logger.error(f"Policies file not found: {policies_path}")
            return []

        try:
            with open(policies_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                policies = data.get('policies', [])
                policies.sort(key=lambda x: x.get('number', 0))
                self.logger.info(f"Loaded {len(policies)} policies from {policies_path}")
                return policies
        except Exception as e:
            self.logger.error(f"Error loading policies: {e}")
            return []
    
    def _prepare_cso_for_llm(self, cso_data: Dict, max_text_length: int = 300) -> Dict:
        """
        Minimize CSO for LLM prompts: strip merge metadata and computed bloat.

        Args:
            cso_data: Full CSO dict.
            max_text_length: Max characters per node text field.

        Returns:
            Minimal nodes/edges only (no graph-level metadata).
        """
        nodes = []
        for node in cso_data.get('nodes', []):
            minimal_node = {
                'id': node.get('id'),
                'type': node.get('type'),
                'text': node.get('text', '')[:max_text_length] if len(node.get('text', '')) > max_text_length else node.get('text', '')
            }

            if 'prior_probability' in node:
                minimal_node['prior_probability'] = node['prior_probability']
            if 'posterior_probability' in node:
                minimal_node['posterior_probability'] = node['posterior_probability']

            if node.get('type') == 'cognitive_bias':
                if 'manifestation_of_ones_thought' in node:
                    minimal_node['manifestation_of_ones_thought'] = node['manifestation_of_ones_thought']
                if 'fixation_of_someones_bias' in node:
                    minimal_node['fixation_of_someones_bias'] = node['fixation_of_someones_bias']

            nodes.append(minimal_node)

        edges = []
        for edge in cso_data.get('edges', []):
            minimal_edge = {
                'source': edge.get('source'),
                'target': edge.get('target'),
                'relation': edge.get('relation'),
                'theta_i1': edge.get('theta_i1'),
                'theta_i0': edge.get('theta_i0')
            }

            if 'bayes_factor' in edge:
                minimal_edge['bayes_factor'] = edge['bayes_factor']

            edges.append(minimal_edge)
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    
    def _analyze_cso_weaknesses(self, cso_data: Dict) -> Dict:
        """
        Heuristic scan for weak spots in the CSO graph (for prompt context).

        Args:
            cso_data: CSO dict.

        Returns:
            Dict of weakness lists keyed by category.
        """
        weaknesses = {
            'arguments_without_edges': [],
            'arguments_with_few_edges': [],
            'low_prior_probability_statements': [],
            'high_prior_probability_statements': [],
            'weak_edges': [],
            'neutral_edges': [],
            'isolated_nodes': [],
            'statements_without_connections_to_arguments': [],
            'quotes_without_connections': [],
            'cognitive_biases_without_connections': [],
            'edges_with_inconsistent_theta': [],
            'arguments_with_only_supporting_edges': [],
            'questions_without_connections': [],
            'questions_without_answers': [],
        }

        nodes = cso_data.get('nodes', [])
        edges = cso_data.get('edges', [])
        nodes_by_id = {node['id']: node for node in nodes}
        edges_by_target = defaultdict(list)
        edges_by_source = defaultdict(list)
        
        for edge in edges:
            edges_by_target[edge['target']].append(edge)
            edges_by_source[edge['source']].append(edge)
        
        arguments = [n for n in nodes if n.get('type') == 'argument']
        for arg in arguments:
            arg_id = arg['id']
            incoming_edges = edges_by_target.get(arg_id, [])
            
            if len(incoming_edges) == 0:
                weaknesses['arguments_without_edges'].append({
                    'id': arg_id,
                    'text': arg.get('text', '')[:100] + '...' if len(arg.get('text', '')) > 100 else arg.get('text', '')
                })
            elif len(incoming_edges) < 2:
                weaknesses['arguments_with_few_edges'].append({
                    'id': arg_id,
                    'edges_count': len(incoming_edges),
                    'text': arg.get('text', '')[:100] + '...' if len(arg.get('text', '')) > 100 else arg.get('text', '')
                })
            
            supporting_edges = [e for e in incoming_edges if e.get('relation') == 'supports']
            contradicting_edges = [e for e in incoming_edges if e.get('relation') == 'contradicts']
            if len(supporting_edges) > 0 and len(contradicting_edges) == 0:
                weaknesses['arguments_with_only_supporting_edges'].append({
                    'id': arg_id,
                    'supporting_count': len(supporting_edges)
                })
        
        statements = [n for n in nodes if n.get('type') == 'statement']
        for stat in statements:
            stat_id = stat['id']
            prior_prob = stat.get('prior_probability', 0.5)
            
            if prior_prob < 0.4:
                weaknesses['low_prior_probability_statements'].append({
                    'id': stat_id,
                    'prior_probability': prior_prob,
                    'text': stat.get('text', '')[:80] + '...' if len(stat.get('text', '')) > 80 else stat.get('text', '')
                })
            elif prior_prob > 0.9:
                weaknesses['high_prior_probability_statements'].append({
                    'id': stat_id,
                    'prior_probability': prior_prob,
                    'text': stat.get('text', '')[:80] + '...' if len(stat.get('text', '')) > 80 else stat.get('text', '')
                })
            
            outgoing_edges = edges_by_source.get(stat_id, [])
            connected_to_args = any(e['target'] in [a['id'] for a in arguments] for e in outgoing_edges)
            if not connected_to_args and len(outgoing_edges) == 0:
                weaknesses['statements_without_connections_to_arguments'].append({
                    'id': stat_id,
                    'text': stat.get('text', '')[:80] + '...' if len(stat.get('text', '')) > 80 else stat.get('text', '')
                })
        
        for edge in edges:
            bayes_factor = edge.get('bayes_factor', 1.0)
            relation = edge.get('relation', '')
            theta_i1 = edge.get('theta_i1', 0.5)
            theta_i0 = edge.get('theta_i0', 0.5)
            
            if abs(bayes_factor - 1.0) < 0.01:
                weaknesses['neutral_edges'].append({
                    'source': edge['source'],
                    'target': edge['target'],
                    'relation': relation,
                    'bayes_factor': bayes_factor
                })
            elif bayes_factor < 1.5:
                weaknesses['weak_edges'].append({
                    'source': edge['source'],
                    'target': edge['target'],
                    'relation': relation,
                    'bayes_factor': bayes_factor
                })
            
            if relation == 'supports' and theta_i1 <= theta_i0:
                weaknesses['edges_with_inconsistent_theta'].append({
                    'source': edge['source'],
                    'target': edge['target'],
                    'theta_i1': theta_i1,
                    'theta_i0': theta_i0
                })
        
        all_node_ids = {n['id'] for n in nodes}
        for node in nodes:
            node_id = node['id']
            has_incoming = node_id in edges_by_target
            has_outgoing = node_id in edges_by_source
            
            if not has_incoming and not has_outgoing:
                weaknesses['isolated_nodes'].append({
                    'id': node_id,
                    'type': node.get('type', 'unknown'),
                    'text': node.get('text', '')[:80] + '...' if len(node.get('text', '')) > 80 else node.get('text', '')
                })
        
        quotes = [n for n in nodes if n.get('type') == 'quotation']
        for quote in quotes:
            quote_id = quote['id']
            if quote_id not in edges_by_source and quote_id not in edges_by_target:
                weaknesses['quotes_without_connections'].append({
                    'id': quote_id,
                    'text': quote.get('text', '')[:80] + '...' if len(quote.get('text', '')) > 80 else quote.get('text', '')
                })
        
        biases = [n for n in nodes if n.get('type') == 'cognitive_bias']
        for bias in biases:
            bias_id = bias['id']
            if bias_id not in edges_by_source and bias_id not in edges_by_target:
                weaknesses['cognitive_biases_without_connections'].append({
                    'id': bias_id,
                    'text': bias.get('text', '')
                })
        
        questions = [n for n in nodes if n.get('type') == 'question']
        for question in questions:
            question_id = question['id']
            incoming_edges = edges_by_target.get(question_id, [])
            outgoing_edges = edges_by_source.get(question_id, [])
            
            if not incoming_edges and not outgoing_edges:
                weaknesses['questions_without_connections'].append({
                    'id': question_id,
                    'text': question.get('text', '')[:80] + '...' if len(question.get('text', '')) > 80 else question.get('text', '')
                })
            
            has_answers = any(
                e.get('relation') in ['answers', 'answered_by'] 
                for e in incoming_edges + outgoing_edges
            )
            if not has_answers and (incoming_edges or outgoing_edges):
                weaknesses['questions_without_answers'].append({
                    'id': question_id,
                    'text': question.get('text', '')[:80] + '...' if len(question.get('text', '')) > 80 else question.get('text', ''),
                    'connections_count': len(incoming_edges) + len(outgoing_edges)
                })
        
        return weaknesses
    
    def _create_strengthening_prompt(self, cso_data: Dict, policy: Dict, weaknesses: Optional[Dict] = None, max_upd_x: Optional[int] = None) -> str:
        """
        Build the LLM prompt for one policy application.

        Args:
            cso_data: CSO without top-level metadata / merge_report.
            policy: Policy dict to apply.
            weaknesses: Optional weakness summary from _analyze_cso_weaknesses.
            max_upd_x: Optional cap on number of edits in the response.

        Returns:
            Prompt string.
        """
        cso_json = json.dumps(cso_data, ensure_ascii=False, indent=2)

        weaknesses_section = ""
        if weaknesses:
            weaknesses_summary = {}
            for key, items in weaknesses.items():
                if items:
                    weaknesses_summary[key] = len(items)
                    if len(items) <= 5:
                        weaknesses_summary[f"{key}_details"] = items[:5]
            
            if weaknesses_summary:
                weaknesses_json = json.dumps(weaknesses_summary, ensure_ascii=False, indent=2)
                weaknesses_section = f"""

**IDENTIFIED WEAKNESSES IN CSO:**
{weaknesses_json}

**IMPORTANT:** Focus on addressing these weaknesses in your recommendations. These are concrete areas that need improvement.
"""
        
        max_changes_instruction = ""
        if max_upd_x is not None:
            max_changes_instruction = f"""

**CRITICAL LIMITATION:** The returned response must contain no more than {max_upd_x} changes. Change count calculation: number of elements in 'delete' array + number of elements in 'edit' array + number of elements in 'new.nodes' array + number of elements in 'new.edges' array. The total number of changes must not exceed {max_upd_x}.
"""
        
        task_instructions = """**TASK:**
Your goal is to actively improve the argumentation structure. Look for opportunities to:
- Add missing connections between statements and arguments
- Strengthen weak arguments by adding supporting statements
- Correct parameter values (prior_probability, theta_i1, theta_i0) that seem inaccurate
- Remove redundant or contradictory elements
- Balance the argumentation by adding counter-arguments where needed
- Connect isolated nodes to the argumentation structure
- Fix weak edges (bayes_factor close to 1.0) by adjusting theta parameters
- Add questions to clarify ambiguous arguments or statements
- Create bidirectional connections between questions and arguments where appropriate

**IMPORTANT:** Try to make at least 1-3 meaningful changes per policy application. Even small improvements are valuable. Focus on structural improvements that enhance the overall argumentation quality.
"""
        
        prompt = f"""You are an expert in argumentation analysis and cognitive ontology. Your task is to strengthen the argumentation in the provided CSO (Cognitive Statement Ontology) structure according to the given policy.

**POLICY #{policy.get('number', 0)}: {policy.get('name', '')}**

**Policy Description:**
{policy.get('description', '')}
{weaknesses_section}
{task_instructions}{max_changes_instruction}

**CSO Structure:**
{cso_json}

**OUTPUT FORMAT:**
You MUST return ONLY a valid JSON object with the following structure:

{{
  "delete": [
    {{
      "id": "node_or_edge_id",
      "full_object": {{ /* full node or edge object */ }},
      "reason": "Why this item is removed"
    }}
  ],
  "edit": [
    {{
      "id": "node_or_edge_id",
      "old_properties": {{
        /* changed properties only (old values) */
      }},
      "new_properties": {{
        /* changed properties only (new values) */
      }},
      "reason": "Why this edit is made"
    }}
  ],
  "new": {{
    "nodes": [
      {{
        "id": "new_node_id",
        "type": "statement|argument|quotation|cognitive_bias|question",
        "text": "...",
        "prior_probability": 0.7,
        /* all other required properties per CSO schema */
      }}
    ],
    "edges": [
      {{
        "source": "source_id",
        "target": "target_id",
        "relation": "supports|contradicts|influences|responds_to|quotes|cites|related_to|answered_by|answers|asks_about",
        "theta_i1": 0.8,
        "theta_i0": 0.3,
        /* all other required edge properties */
      }}
    ]
  }}
}}

**IMPORTANT RULES:**
1. For edges identification: use format "source_id|target_id" (e.g., "stat1|arg1")
2. For nodes: use the node's "id" field
3. In "edit", include ONLY changed properties in both old_properties and new_properties
4. In "delete", include the FULL object that will be deleted
5. For new nodes/edges, include ALL required properties according to CSO schema
6. Arguments must always be targets (never sources) in edges
   EXCEPTION: Arguments can be sources when connecting to questions (bidirectional)
7. All new nodes must have unique IDs that don't conflict with existing ones
8. If no meaningful improvements can be made according to the policy, you can return an empty response (all lists empty)

**CRITICAL:**
- Return ONLY valid JSON, no additional text
- Ensure all IDs are valid (exist in the provided CSO or are new unique IDs)
- All changes should align with the policy goal
- Focus on improving total_predictability of the argumentation system
- Be proactive in finding and fixing issues in the argumentation structure{max_changes_instruction if max_upd_x is not None else ""}

**QUESTION NODE TYPE:**
- Questions do NOT participate in argument probability calculations
- Questions do NOT require prior_probability or posterior_probability
- Questions can have bidirectional connections with arguments
- When creating question nodes, use IDs starting with 'quest' (e.g., 'quest1', 'quest_001')
- Question-specific relation types:
  * "answered_by": question → statement/argument
  * "answers": statement/argument → question
  * "asks_about": question → statement/argument
  * "responds_to": question → question/statement
  * "influences": question → statement/argument
  * "related_to": general relationship

Return your response now:"""
        
        return prompt
    
    def _call_llm_for_strengthening(self, cso_data: Dict, policy: Dict, weaknesses: Optional[Dict] = None) -> Optional[Tuple[Dict, str]]:
        """
        Call the LLM for structured strengthening edits.

        Args:
            cso_data: CSO without metadata / merge_report.
            policy: Policy to apply.
            weaknesses: Optional weakness dict for the prompt.

        Returns:
            (parsed_llm_response_dict, model_name) or None on failure.
        """
        max_attempts = self.config.get('pipeline', {}).get('processing', {}).get('max_validation_attempts', 5)
        retry_models = self.llm_processor.retry_models
        
        for attempt in range(1, max_attempts + 1):
            try:
                max_upd_x = None
                if attempt > 1:
                    max_upd_x = self.max_upd // (attempt*3)
                    self.logger.info(f"Reducing max changes to {max_upd_x} due to previous JSON decode errors (attempt {attempt})")

                prompt = self._create_strengthening_prompt(cso_data, policy, weaknesses, max_upd_x)
                
                current_model = retry_models[min(attempt - 1, len(retry_models) - 1)]
                current_temperature = self.llm_processor.temperature
                if attempt > 1:
                    current_temperature = min(1.0, current_temperature + 0.1)
                
                self.logger.info(f"LLM call attempt {attempt}/{max_attempts} using model {current_model}")
                
                response = self.llm_processor.client.chat.completions.create(
                    model=current_model,
                    messages=[
                        {"role": "system", "content": "You are an expert in argumentation analysis and cognitive ontology. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=current_temperature,
                    max_tokens=self.llm_processor.max_tokens
                )
                
                response_content = response.choices[0].message.content.strip()
                
                try:
                    if response_content.startswith('```'):
                        lines = response_content.split('\n')
                        response_content = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_content
                        response_content = response_content.strip()
                        if response_content.startswith('json'):
                            response_content = response_content[4:].strip()
                    
                    llm_response = json.loads(response_content)
                    self.logger.info(f"Successfully parsed LLM response from model {current_model}")
                    return (llm_response, current_model)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON decode error on attempt {attempt}: {e}")
                    if attempt == max_attempts:
                        self.logger.error(f"Failed to parse LLM response after {max_attempts} attempts")
                        return None
                    continue

            except KeyboardInterrupt:
                self.logger.warning("LLM call interrupted by user")
                raise
            except Exception as e:
                self.logger.warning(f"LLM call error on attempt {attempt}: {e}")
                if attempt == max_attempts:
                    self.logger.error(f"Failed to call LLM after {max_attempts} attempts")
                    return None
                continue
        
        return None
    
    def _validate_llm_response(self, llm_response: Dict, cso_data: Dict) -> Tuple[bool, str]:
        """
        Validate LLM response shape (delete/edit/new).

        Args:
            llm_response: Parsed LLM JSON.
            cso_data: Current CSO (for context; ID checks are shallow).

        Returns:
            (is_valid, error_message)
        """
        if not isinstance(llm_response, dict):
            return False, "Response is not a dictionary"

        required_keys = ['delete', 'edit', 'new']
        for key in required_keys:
            if key not in llm_response:
                return False, f"Missing required key: {key}"
        
        if not isinstance(llm_response['delete'], list):
            return False, "delete must be a list"
        if not isinstance(llm_response['edit'], list):
            return False, "edit must be a list"
        if not isinstance(llm_response['new'], dict):
            return False, "new must be a dictionary"
        
        if 'nodes' not in llm_response['new'] or 'edges' not in llm_response['new']:
            return False, "new must contain 'nodes' and 'edges'"
        
        nodes_by_id = {node['id']: node for node in cso_data.get('nodes', [])}
        edges_by_id = {}
        for edge in cso_data.get('edges', []):
            edge_id = f"{edge['source']}|{edge['target']}"
            edges_by_id[edge_id] = edge
        
        for delete_item in llm_response['delete']:
            if 'id' not in delete_item:
                return False, "delete item missing 'id'"
            if 'full_object' not in delete_item:
                return False, "delete item missing 'full_object'"
        
        for edit_item in llm_response['edit']:
            if 'id' not in edit_item:
                return False, "edit item missing 'id'"
            if 'old_properties' not in edit_item or 'new_properties' not in edit_item:
                return False, "edit item missing old_properties or new_properties"
        
        return True, ""
    
    def strengthen(self, cso_file_path: str) -> Optional[str]:
        """
        Run policy loop on a CSO JSON file; write strengthened output with checkpoints.

        Args:
            cso_file_path: Path to input CSO JSON.

        Returns:
            Path to written strengthened file, or None on error / disabled.
        """
        if not self.enabled:
            self.logger.info("Argumentation strengthening is disabled")
            return None
        
        if not self.policies:
            self.logger.error("No policies loaded")
            return None
        
        file_dir = os.path.dirname(cso_file_path)

        if file_dir and os.path.exists(file_dir):
            all_json_files = glob.glob(os.path.join(file_dir, "*.json"))

            if all_json_files:
                def extract_timestamp_from_file(filepath):
                    """Parse timestamp from filename, else use file mtime."""
                    filename = os.path.basename(filepath)

                    match_strengthened = re.search(r'_strengthened_(\d{8})_(\d{6})', filename)
                    if match_strengthened:
                        try:
                            return datetime.strptime(f"{match_strengthened.group(1)}_{match_strengthened.group(2)}", "%Y%m%d_%H%M%S")
                        except ValueError:
                            pass
                    
                    match1 = re.search(r'_(\d{8})_(\d{6})', filename)
                    if match1:
                        try:
                            return datetime.strptime(f"{match1.group(1)}_{match1.group(2)}", "%Y%m%d_%H%M%S")
                        except ValueError:
                            pass
                    
                    match2 = re.search(r'_(\d{14})', filename)
                    if match2:
                        try:
                            return datetime.strptime(match2.group(1), "%Y%m%d%H%M%S")
                        except ValueError:
                            pass
                    
                    try:
                        return datetime.fromtimestamp(os.path.getmtime(filepath))
                    except:
                        return datetime.min
                
                files_with_timestamps = [(f, extract_timestamp_from_file(f)) for f in all_json_files]
                latest_file, latest_timestamp = max(files_with_timestamps, key=lambda x: x[1])

                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        latest_data = json.load(f)
                    
                    if latest_data.get('updates') or '_strengthened_' in os.path.basename(latest_file):
                        if latest_file != cso_file_path:
                            self.logger.info(f"Found latest file by timestamp: {os.path.basename(latest_file)} (timestamp: {latest_timestamp}), using it for further strengthening")
                            cso_file_path = latest_file
                        else:
                            self.logger.info(f"Latest file is the same as input file: {os.path.basename(cso_file_path)}")
                    else:
                        self.logger.info(f"Latest file {os.path.basename(latest_file)} doesn't contain updates, using input file: {os.path.basename(cso_file_path)}")
                except Exception as e:
                    self.logger.warning(f"Error checking latest file {latest_file}: {e}, using input file")
            else:
                self.logger.info(f"No JSON files found in directory, using original file: {cso_file_path}")
        else:
            self.logger.info(f"Directory not found or invalid, using original file: {cso_file_path}")
        
        try:
            with open(cso_file_path, 'r', encoding='utf-8') as f:
                cso_data = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading CSO file: {e}")
            return None
        
        if 'merge_report' not in cso_data:
            self.logger.warning("CSO file does not have merge_report (single fragment, creating empty merge_report)")
            cso_data['merge_report'] = {
                "naming_convention": {
                    "format": "single_fragment",
                    "explanation": "Single fragment - no merge performed"
                },
                "merge_steps": [],
                "final_statistics": {
                    "original_nodes_count": len(cso_data.get('nodes', [])),
                    "final_nodes_count": len(cso_data.get('nodes', [])),
                    "nodes_merged": 0
                },
                "posterior_deltas": {},
                "id_mapping": {}
            }
        
        if 'metadata' not in cso_data or 'total_predictability' not in cso_data.get('metadata', {}):
            self.logger.error("CSO file missing VFE calculations or total_predictability")
            return None
        
        initial_state = {
            'nodes': json.loads(json.dumps(cso_data.get('nodes', []))),
            'edges': json.loads(json.dumps(cso_data.get('edges', []))),
            'metadata': json.loads(json.dumps(cso_data.get('metadata', {})))
        }
        self.logger.info("Initial state saved for final delta calculation")
        
        if 'updates' not in cso_data:
            cso_data['updates'] = []
        
        if 'metadata' not in cso_data:
            cso_data['metadata'] = {}
        cso_data['metadata']['strengthening_type'] = 'policies'
        
        updates = cso_data.get('updates', [])
        if updates and len(updates) >= self.n_last_politics:
            last_updates = updates[-self.n_last_politics:]
            total_abs_diff = sum(
                abs(update.get('metadata_dif', {}).get('total_predictability_diff', 0.0))
                for update in last_updates
            )
            
            if total_abs_diff < self.total_predictability_diff_min:
                self.logger.info(f"Strengthening already stopped by condition: total_abs_diff={total_abs_diff:.6f} < min={self.total_predictability_diff_min}")
                self.logger.info(f"Returning existing file without further processing: {cso_file_path}")
                return cso_file_path
        
        last_policy_number = None
        if updates:
            self.logger.info(f"Found {len(updates)} existing updates, searching for last applied policy...")
            for update in reversed(updates):
                policy_number = update.get('policy_number')
                if policy_number is not None:
                    last_policy_number = policy_number
                    self.logger.info(f"Found last applied policy: #{last_policy_number} in update {update.get('update_id', 'unknown')}")
                    break
            if last_policy_number is None:
                self.logger.warning(f"No policy_number found in any of {len(updates)} updates")
        else:
            self.logger.info("No updates found in CSO file")
        
        if last_policy_number is not None:
            last_policy_index = None
            for idx, policy in enumerate(self.policies):
                if policy.get('number') == last_policy_number:
                    last_policy_index = idx
                    break
            
            if last_policy_index is not None:
                self.policy_application_counter = last_policy_index + 1
                next_policy_index = self.policy_application_counter % len(self.policies)
                next_policy_number = self.policies[next_policy_index].get('number')
                self.logger.info(f"Resuming from policy #{last_policy_number} (index {last_policy_index}), next policy will be #{next_policy_number} (index {next_policy_index})")
            else:
                self.policy_application_counter = 0
                self.logger.warning(f"Last applied policy #{last_policy_number} not found in policies list, starting from beginning")
        else:
            self.policy_application_counter = 0
            self.logger.info("No previous policy applications found, starting from beginning")
        
        try:
            while True:
                try:
                    policy_index = self.policy_application_counter % len(self.policies)
                    policy = self.policies[policy_index]
                    self.policy_application_counter += 1
                    
                    self.logger.info(f"Applying policy #{policy.get('number')} ({policy.get('name')}) - application #{self.policy_application_counter}")
                    
                    cso_for_llm = self._prepare_cso_for_llm(cso_data)

                    weaknesses = self._analyze_cso_weaknesses(cso_for_llm)
                    total_weaknesses = sum(len(v) for v in weaknesses.values() if isinstance(v, list))
                    self.logger.info(f"Identified {total_weaknesses} weaknesses in CSO structure")
                    
                    llm_result = self._call_llm_for_strengthening(cso_for_llm, policy, weaknesses)
                    
                    if llm_result is None:
                        self.logger.error(f"Failed to get LLM response for policy #{policy.get('number')}")
                        continue
                    
                    llm_response, llm_model = llm_result

                    is_valid, error_msg = self._validate_llm_response(llm_response, cso_data)
                    if not is_valid:
                        self.logger.error(f"Invalid LLM response: {error_msg}")
                        continue
                    
                    old_metadata = cso_data.get('metadata', {}).get('total_predictability', {})
                    cso_data_before = json.loads(json.dumps(cso_data))

                    success = self._apply_changes(cso_data, llm_response)
                    if not success:
                        self.logger.error(f"Failed to apply changes for policy #{policy.get('number')}")
                        continue
                    
                    self._recalculate_affected(cso_data, llm_response)

                    self._recalculate_total_predictability(cso_data)

                    update_entry = self._create_update_entry(
                        policy, 
                        llm_response, 
                        old_metadata,
                        cso_data.get('metadata', {}).get('total_predictability', {}),
                        cso_data_before,
                        cso_data,
                        llm_model=llm_model
                    )
                    cso_data['updates'].append(update_entry)
                    
                    try:
                        temp_output_path = self._generate_output_path(cso_file_path)
                        with open(temp_output_path, 'w', encoding='utf-8') as f:
                            json.dump(cso_data, f, ensure_ascii=False, indent=2)
                        self.logger.info(f"Checkpoint saved: {temp_output_path}")
                    except Exception as e:
                        self.logger.warning(f"Failed to save checkpoint: {e}")
                    
                    if self._should_stop(cso_data):
                        self.logger.info("Stopping criterion met - insufficient improvement in total_predictability")
                        break
                        
                except KeyboardInterrupt:
                    self.logger.warning("Policy application interrupted by user. Saving current progress...")
                    raise

        except KeyboardInterrupt:
            self.logger.warning("Process interrupted by user. Saving current progress...")

            if 'initial_state' in locals():
                final_delta = self._calculate_final_delta(initial_state, cso_data)
                self._add_final_delta_to_metadata(cso_data, initial_state, final_delta, is_partial=True)
            
            if 'metadata' not in cso_data:
                cso_data['metadata'] = {}
            statistics = self._calculate_statistics(cso_data)
            cso_data['metadata']['statistics'] = statistics
            
            try:
                output_path = self._generate_output_path(cso_file_path)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(cso_data, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Progress saved to: {output_path}")
                return output_path
            except Exception as e:
                self.logger.error(f"Failed to save progress: {e}")
            raise

        final_delta = self._calculate_final_delta(initial_state, cso_data)
        self._add_final_delta_to_metadata(cso_data, initial_state, final_delta, is_partial=False)
        
        if 'metadata' not in cso_data:
            cso_data['metadata'] = {}
        statistics = self._calculate_statistics(cso_data)
        cso_data['metadata']['statistics'] = statistics
        self.logger.info(f"Statistics updated: {statistics}")
        
        output_path = self._generate_output_path(cso_file_path)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(cso_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Strengthened CSO saved to: {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"Error saving strengthened CSO: {e}")
            return None
    
    def _apply_changes(self, cso_data: Dict, llm_response: Dict) -> bool:
        """
        Apply delete/edit/new from the LLM response to cso_data in place.

        Args:
            cso_data: CSO dict to mutate.
            llm_response: Parsed LLM JSON with delete, edit, new.

        Returns:
            True on success, False on exception.
        """
        try:
            nodes = cso_data.get('nodes', [])
            edges = cso_data.get('edges', [])

            nodes_by_id = {node['id']: i for i, node in enumerate(nodes)}
            edges_by_id = {}
            for i, edge in enumerate(edges):
                edge_id = f"{edge['source']}|{edge['target']}"
                edges_by_id[edge_id] = i

            for delete_item in llm_response.get('delete', []):
                item_id = delete_item['id']

                if item_id in nodes_by_id:
                    node_index = nodes_by_id[item_id]
                    nodes.pop(node_index)
                    nodes_by_id = {node['id']: i for i, node in enumerate(nodes)}
                    edges = [e for e in edges if e['source'] != item_id and e['target'] != item_id]
                    edges_by_id = {f"{e['source']}|{e['target']}": i for i, e in enumerate(edges)}
                elif item_id in edges_by_id:
                    edge_index = edges_by_id[item_id]
                    edges.pop(edge_index)
                    edges_by_id = {f"{e['source']}|{e['target']}": i for i, e in enumerate(edges)}
                else:
                    self.logger.warning(f"Item to delete not found: {item_id}")

            for edit_item in llm_response.get('edit', []):
                item_id = edit_item['id']
                old_props = edit_item.get('old_properties', {})
                new_props = edit_item.get('new_properties', {})

                if item_id in nodes_by_id:
                    node_index = nodes_by_id[item_id]
                    for key, value in new_props.items():
                        nodes[node_index][key] = value
                elif item_id in edges_by_id:
                    edge_index = edges_by_id[item_id]
                    for key, value in new_props.items():
                        edges[edge_index][key] = value
                else:
                    self.logger.warning(f"Item to edit not found: {item_id}")

            new_nodes = llm_response.get('new', {}).get('nodes', [])
            new_edges = llm_response.get('new', {}).get('edges', [])

            nodes.extend(new_nodes)
            edges.extend(new_edges)

            cso_data['nodes'] = nodes
            cso_data['edges'] = edges
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying changes: {e}")
            return False
    
    def _find_affected_chains(self, cso_data: Dict, llm_response: Dict) -> Set[str]:
        """
        Find argument node IDs that should be recomputed after LLM edits.

        Args:
            cso_data: Current CSO.
            llm_response: LLM delete/edit/new payload.

        Returns:
            Set of argument node IDs.
        """
        nodes = cso_data.get('nodes', [])
        edges = cso_data.get('edges', [])

        graph = defaultdict(list)
        for edge in edges:
            graph[edge['source']].append(edge['target'])
        
        affected_arguments = set()

        changed_node_ids = set()
        changed_edge_ids = set()

        for delete_item in llm_response.get('delete', []):
            item_id = delete_item['id']
            if '|' in item_id:
                changed_edge_ids.add(item_id)
                source, target = item_id.split('|', 1)
                changed_node_ids.add(source)
                changed_node_ids.add(target)
            else:
                changed_node_ids.add(item_id)

        for edit_item in llm_response.get('edit', []):
            item_id = edit_item['id']
            if '|' in item_id:
                changed_edge_ids.add(item_id)
                source, target = item_id.split('|', 1)
                changed_node_ids.add(source)
                changed_node_ids.add(target)
            else:
                changed_node_ids.add(item_id)

        for new_edge in llm_response.get('new', {}).get('edges', []):
            target = new_edge.get('target')
            if target:
                target_node = next((n for n in nodes if n['id'] == target), None)
                if target_node and target_node.get('type') == 'argument':
                    affected_arguments.add(target)

        statements = [n for n in nodes if n.get('type') == 'statement']

        for statement in statements:
            if statement['id'] in changed_node_ids:
                visited = set()
                queue = deque([statement['id']])

                while queue:
                    current_id = queue.popleft()
                    if current_id in visited:
                        continue
                    visited.add(current_id)

                    for target_id in graph.get(current_id, []):
                        target_node = next((n for n in nodes if n['id'] == target_id), None)
                        if target_node:
                            if target_node.get('type') == 'argument':
                                affected_arguments.add(target_id)
                            else:
                                if target_id not in visited:
                                    queue.append(target_id)

        for edge_id in changed_edge_ids:
            source, target = edge_id.split('|', 1)
            target_node = next((n for n in nodes if n['id'] == target), None)
            if target_node and target_node.get('type') == 'argument':
                affected_arguments.add(target)
        
        return affected_arguments
    
    def _recalculate_affected(self, cso_data: Dict, llm_response: Dict):
        """
        Recompute posteriors / VFE for affected arguments; refresh edge Bayes factors.

        Args:
            cso_data: CSO dict (mutated).
            llm_response: Latest LLM edit payload.
        """
        nodes = cso_data.get('nodes', [])
        edges = cso_data.get('edges', [])

        affected_arguments = self._find_affected_chains(cso_data, llm_response)

        if not affected_arguments:
            updated_nodes, updated_edges = self.calculator.calculate_all_argument_probabilities(nodes, edges)
        else:
            updated_nodes = [node.copy() for node in nodes]
            updated_edges = [edge.copy() for edge in edges]

            statements = [n for n in updated_nodes if n.get('type') == 'statement']

            for arg_id in affected_arguments:
                arg_node = next((n for n in updated_nodes if n['id'] == arg_id), None)
                if arg_node and arg_node.get('type') == 'argument':
                    posterior_prob, vfe_metrics = self.calculator._calculate_argument_posterior(
                        arg_node, statements, updated_nodes, updated_edges
                    )

                    edges_count = self.calculator._count_S_to_A_edges(arg_id, updated_edges, updated_nodes)

                    F_k_vfe = vfe_metrics.get('variational_free_energy', 0.0)
                    F_bar_k = F_k_vfe / (1 + edges_count) if (1 + edges_count) > 0 else F_k_vfe
                    predictability_contribution = np.exp(-F_bar_k)

                    vfe_metrics['F_bar_k'] = float(F_bar_k)
                    vfe_metrics['edges_count'] = edges_count
                    vfe_metrics['predictability_contribution'] = float(predictability_contribution)

                    arg_node['posterior_probability'] = posterior_prob
                    arg_node['vfe'] = vfe_metrics

            affected_edges = set()
            graph = defaultdict(list)
            for edge in updated_edges:
                graph[edge['source']].append((edge['target'], edge))

            for arg_id in affected_arguments:
                for statement in statements:
                    visited = set()
                    queue = deque([(statement['id'], [])])

                    while queue:
                        current_id, path = queue.popleft()
                        if current_id in visited:
                            continue
                        visited.add(current_id)

                        if current_id == arg_id:
                            for i in range(len(path) - 1):
                                edge_id = f"{path[i]}|{path[i+1]}"
                                affected_edges.add(edge_id)
                            break

                        for target_id, edge in graph.get(current_id, []):
                            if target_id not in visited:
                                new_path = path + [current_id]
                                queue.append((target_id, new_path))

            self.calculator._calculate_and_add_bayes_factors(updated_nodes, updated_edges)
        
        cso_data['nodes'] = updated_nodes
        cso_data['edges'] = updated_edges
    
    def _recalculate_total_predictability(self, cso_data: Dict):
        """
        Refresh metadata.total_predictability from current nodes and edges.

        Args:
            cso_data: CSO dict (mutated).
        """
        nodes = cso_data.get('nodes', [])
        edges = cso_data.get('edges', [])

        total_predictability = self.calculator.calculate_total_predictability(nodes, edges)

        if 'metadata' not in cso_data:
            cso_data['metadata'] = {}
        
        cso_data['metadata']['total_predictability'] = total_predictability
        cso_data['metadata']['calculation_timestamp'] = datetime.now().isoformat()
    
    def _calculate_statistics_diff(self, cso_data_before: Dict, cso_data_after: Dict) -> Dict:
        """
        Diff node-type counts and edge counts between two CSO snapshots.

        Args:
            cso_data_before: CSO before edits.
            cso_data_after: CSO after edits.

        Returns:
            Dict with nodes_by_type_diff, edges_count_diff, total_nodes_diff.
        """
        nodes_before = cso_data_before.get('nodes', [])
        nodes_after = cso_data_after.get('nodes', [])
        edges_before = cso_data_before.get('edges', [])
        edges_after = cso_data_after.get('edges', [])

        nodes_by_type_before = defaultdict(int)
        for node in nodes_before:
            node_type = node.get('type', 'unknown')
            nodes_by_type_before[node_type] += 1
        
        nodes_by_type_after = defaultdict(int)
        for node in nodes_after:
            node_type = node.get('type', 'unknown')
            nodes_by_type_after[node_type] += 1
        
        nodes_by_type_diff = {}
        all_types = set(list(nodes_by_type_before.keys()) + list(nodes_by_type_after.keys()))
        for node_type in all_types:
            diff = nodes_by_type_after.get(node_type, 0) - nodes_by_type_before.get(node_type, 0)
            if diff != 0:
                nodes_by_type_diff[node_type] = diff
        
        edges_count_diff = len(edges_after) - len(edges_before)
        total_nodes_diff = len(nodes_after) - len(nodes_before)
        
        return {
            "nodes_by_type_diff": nodes_by_type_diff,
            "edges_count_diff": edges_count_diff,
            "total_nodes_diff": total_nodes_diff
        }
    
    def _calculate_statistics(self, cso_data: Dict) -> Dict[str, Any]:
        """
        Aggregate counts by node type and edge relation.

        Args:
            cso_data: CSO dict.

        Returns:
            Stats dict for metadata.
        """
        nodes = cso_data.get('nodes', [])
        edges = cso_data.get('edges', [])

        nodes_by_type = {}
        for node in nodes:
            node_type = node.get('type', 'unknown')
            nodes_by_type[node_type] = nodes_by_type.get(node_type, 0) + 1
        
        edges_by_type = {}
        for edge in edges:
            edge_relation = edge.get('relation', 'unknown')
            edges_by_type[edge_relation] = edges_by_type.get(edge_relation, 0) + 1
        
        return {
            'total_nodes': len(nodes),
            'nodes_by_type': nodes_by_type,
            'total_edges': len(edges),
            'edges_by_type': edges_by_type
        }
    
    def _calculate_final_delta(self, initial_state: Dict, final_state: Dict) -> Dict:
        """
        Full structural diff between initial snapshot and final CSO.

        Args:
            initial_state: Dict with nodes, edges, metadata.
            final_state: Final cso_data dict.

        Returns:
            Detailed delta (added/removed/modified nodes and edges, predictability).
        """
        initial_nodes = initial_state.get('nodes', [])
        initial_edges = initial_state.get('edges', [])
        final_nodes = final_state.get('nodes', [])
        final_edges = final_state.get('edges', [])

        initial_nodes_by_id = {node['id']: node for node in initial_nodes}
        initial_edges_by_id = {}
        for edge in initial_edges:
            edge_id = f"{edge['source']}|{edge['target']}"
            initial_edges_by_id[edge_id] = edge
        
        final_nodes_by_id = {node['id']: node for node in final_nodes}
        final_edges_by_id = {}
        for edge in final_edges:
            edge_id = f"{edge['source']}|{edge['target']}"
            final_edges_by_id[edge_id] = edge
        
        added_nodes = []
        for node_id, node in final_nodes_by_id.items():
            if node_id not in initial_nodes_by_id:
                added_nodes.append({
                    'id': node_id,
                    'type': node.get('type', 'unknown'),
                    'text': node.get('text', '')[:100] + '...' if len(node.get('text', '')) > 100 else node.get('text', '')
                })
        
        removed_nodes = []
        for node_id, node in initial_nodes_by_id.items():
            if node_id not in final_nodes_by_id:
                removed_nodes.append({
                    'id': node_id,
                    'type': node.get('type', 'unknown'),
                    'text': node.get('text', '')[:100] + '...' if len(node.get('text', '')) > 100 else node.get('text', '')
                })
        
        modified_nodes = []
        for node_id in final_nodes_by_id:
            if node_id in initial_nodes_by_id:
                initial_node = initial_nodes_by_id[node_id]
                final_node = final_nodes_by_id[node_id]
                
                changes = {}
                key_properties = ['prior_probability', 'posterior_probability', 'text', 'type', 'credibility']
                
                for prop in key_properties:
                    initial_val = initial_node.get(prop)
                    final_val = final_node.get(prop)
                    if initial_val != final_val:
                        changes[prop] = {
                            'old': initial_val,
                            'new': final_val
                        }
                
                if 'vfe' in initial_node or 'vfe' in final_node:
                    initial_vfe = initial_node.get('vfe', {})
                    final_vfe = final_node.get('vfe', {})
                    if initial_vfe != final_vfe:
                        changes['vfe'] = {
                            'old': initial_vfe,
                            'new': final_vfe
                        }
                
                if changes:
                    modified_nodes.append({
                        'id': node_id,
                        'type': final_node.get('type', 'unknown'),
                        'changes': changes
                    })
        
        added_edges = []
        for edge_id, edge in final_edges_by_id.items():
            if edge_id not in initial_edges_by_id:
                added_edges.append({
                    'source': edge['source'],
                    'target': edge['target'],
                    'relation': edge.get('relation', 'unknown'),
                    'theta_i1': edge.get('theta_i1'),
                    'theta_i0': edge.get('theta_i0'),
                    'bayes_factor': edge.get('bayes_factor')
                })
        
        removed_edges = []
        for edge_id, edge in initial_edges_by_id.items():
            if edge_id not in final_edges_by_id:
                removed_edges.append({
                    'source': edge['source'],
                    'target': edge['target'],
                    'relation': edge.get('relation', 'unknown')
                })
        
        modified_edges = []
        for edge_id in final_edges_by_id:
            if edge_id in initial_edges_by_id:
                initial_edge = initial_edges_by_id[edge_id]
                final_edge = final_edges_by_id[edge_id]
                
                changes = {}
                key_properties = ['relation', 'theta_i1', 'theta_i0', 'bayes_factor', 'weight']
                
                for prop in key_properties:
                    initial_val = initial_edge.get(prop)
                    final_val = final_edge.get(prop)
                    if initial_val != final_val:
                        changes[prop] = {
                            'old': initial_val,
                            'new': final_val
                        }
                
                if changes:
                    modified_edges.append({
                        'source': final_edge['source'],
                        'target': final_edge['target'],
                        'changes': changes
                    })
        
        initial_nodes_by_type = defaultdict(int)
        for node in initial_nodes:
            initial_nodes_by_type[node.get('type', 'unknown')] += 1
        
        final_nodes_by_type = defaultdict(int)
        for node in final_nodes:
            final_nodes_by_type[node.get('type', 'unknown')] += 1
        
        nodes_by_type_diff = {}
        all_types = set(list(initial_nodes_by_type.keys()) + list(final_nodes_by_type.keys()))
        for node_type in all_types:
            diff = final_nodes_by_type.get(node_type, 0) - initial_nodes_by_type.get(node_type, 0)
            if diff != 0:
                nodes_by_type_diff[node_type] = diff
        
        initial_metadata = initial_state.get('metadata', {})
        final_metadata = final_state.get('metadata', {})
        
        initial_total_predictability = initial_metadata.get('total_predictability', {})
        final_total_predictability = final_metadata.get('total_predictability', {})
        
        if isinstance(initial_total_predictability, dict):
            initial_total = initial_total_predictability.get('total_predictability', 0.0)
        else:
            initial_total = initial_total_predictability if isinstance(initial_total_predictability, (int, float)) else 0.0
        
        if isinstance(final_total_predictability, dict):
            final_total = final_total_predictability.get('total_predictability', 0.0)
        else:
            final_total = final_total_predictability if isinstance(final_total_predictability, (int, float)) else 0.0
        
        total_predictability_diff = final_total - initial_total
        
        return {
            'summary': {
                'nodes': {
                    'initial_count': len(initial_nodes),
                    'final_count': len(final_nodes),
                    'added_count': len(added_nodes),
                    'removed_count': len(removed_nodes),
                    'modified_count': len(modified_nodes),
                    'net_change': len(final_nodes) - len(initial_nodes)
                },
                'edges': {
                    'initial_count': len(initial_edges),
                    'final_count': len(final_edges),
                    'added_count': len(added_edges),
                    'removed_count': len(removed_edges),
                    'modified_count': len(modified_edges),
                    'net_change': len(final_edges) - len(initial_edges)
                },
                'nodes_by_type_diff': nodes_by_type_diff,
                'total_predictability': {
                    'initial': initial_total,
                    'final': final_total,
                    'diff': total_predictability_diff,
                    'percent_change': (total_predictability_diff / initial_total * 100) if initial_total > 0 else 0.0
                }
            },
            'added_nodes': added_nodes,
            'removed_nodes': removed_nodes,
            'modified_nodes': modified_nodes,
            'added_edges': added_edges,
            'removed_edges': removed_edges,
            'modified_edges': modified_edges
        }
    
    def _add_final_delta_to_metadata(self, cso_data: Dict, initial_state: Dict, final_delta: Dict, is_partial: bool = False):
        """
        Write strengthening_summary and final_delta into metadata.

        Args:
            cso_data: CSO to update.
            initial_state: Snapshot at start of strengthen().
            final_delta: From _calculate_final_delta.
            is_partial: True if run ended on KeyboardInterrupt.
        """
        if 'metadata' not in cso_data:
            cso_data['metadata'] = {}

        initial_metadata = initial_state.get('metadata', {})
        initial_total_predictability_obj = initial_metadata.get('total_predictability', {})
        final_total_predictability_obj = cso_data.get('metadata', {}).get('total_predictability', {})
        
        if isinstance(initial_total_predictability_obj, dict):
            initial_total = initial_total_predictability_obj.get('total_predictability', 0.0)
        else:
            initial_total = initial_total_predictability_obj if isinstance(initial_total_predictability_obj, (int, float)) else 0.0
        
        if isinstance(final_total_predictability_obj, dict):
            final_total = final_total_predictability_obj.get('total_predictability', 0.0)
        else:
            final_total = final_total_predictability_obj if isinstance(final_total_predictability_obj, (int, float)) else 0.0
        
        total_predictability_diff = final_total - initial_total
        total_predictability_percent_change = (total_predictability_diff / initial_total * 100) if initial_total > 0 else 0.0
        
        updates = cso_data.get('updates', [])
        cumulative_diff = sum(
            update.get('metadata_dif', {}).get('total_predictability_diff', 0.0) 
            for update in updates
        )
        
        cso_data['metadata']['strengthening_summary'] = {
            'initial_total_predictability': initial_total,
            'final_total_predictability': final_total,
            'total_predictability_diff': total_predictability_diff,
            'total_predictability_percent_change': total_predictability_percent_change,
            'total_steps': len(updates),
            'cumulative_total_predictability_diff': cumulative_diff,
            'is_partial': is_partial,
            'timestamp': datetime.now().isoformat()
        }
        
        cso_data['metadata']['final_delta'] = final_delta
        cso_data['metadata']['final_delta_timestamp'] = datetime.now().isoformat()
        
        status_text = "partial" if is_partial else "complete"
        self.logger.info(
            f"Final delta calculated ({status_text}): total_predictability changed from "
            f"{initial_total:.6f} to {final_total:.6f} "
            f"(diff: {total_predictability_diff:.6f}, {total_predictability_percent_change:.2f}%)"
        )
    
    def _create_update_entry(self, policy: Dict, llm_response: Dict, 
                            old_metadata: Dict, new_metadata: Dict,
                            cso_data_before: Dict, cso_data_after: Dict,
                            llm_model: Optional[str] = None) -> Dict:
        """
        Build one entry for the cso_data['updates'] list after a policy step.

        Args:
            policy: Applied policy dict.
            llm_response: Raw LLM JSON response.
            old_metadata: Previous metadata['total_predictability'] value (dict or scalar).
            new_metadata: New metadata['total_predictability'] after recalc.
            cso_data_before: Deep copy before apply.
            cso_data_after: CSO after apply and recalc.
            llm_model: Model name used for this step.

        Returns:
            Update record dict.
        """
        stats_diff = self._calculate_statistics_diff(cso_data_before, cso_data_after)

        old_total = old_metadata.get('total_predictability', 0.0)
        new_total = new_metadata.get('total_predictability', 0.0)
        total_predictability_diff = new_total - old_total
        
        update_entry = {
            "update_id": f"update_vfe-POLICY_{self.policy_application_counter}",
            "timestamp": datetime.now().isoformat(),
            "policy_number": policy.get('number'),
            "policy_name": policy.get('name'),
            "policy_description": policy.get('description'),
            "llm_response": llm_response,
            "metadata_dif": {
                "nodes_by_type_diff": stats_diff["nodes_by_type_diff"],
                "edges_count_diff": stats_diff["edges_count_diff"],
                "total_nodes_diff": stats_diff["total_nodes_diff"],
                "total_predictability_diff": total_predictability_diff,
                "old_metadata": {
                    "total_predictability": old_metadata
                }
            }
        }
        
        if llm_model:
            update_entry["llm_model"] = llm_model
        
        return update_entry
    
    def _should_stop(self, cso_data: Dict) -> bool:
        """
        Stop if the sum of |total_predictability_diff| over the last n steps is below threshold.

        Args:
            cso_data: CSO with updates list.

        Returns:
            True to break the policy loop.
        """
        updates = cso_data.get('updates', [])

        if len(updates) < self.n_last_politics:
            return False

        last_updates = updates[-self.n_last_politics:]

        total_abs_diff = 0.0
        for update in last_updates:
            diff = update.get('metadata_dif', {}).get('total_predictability_diff', 0.0)
            total_abs_diff += abs(diff)
        
        if total_abs_diff < self.total_predictability_diff_min:
            self.logger.info(f"Stopping criterion: total absolute diff ({total_abs_diff:.6f}) < min threshold ({self.total_predictability_diff_min})")
            return True
        
        return False
    
    def _generate_output_path(self, input_path: str) -> str:
        """
        Build output path with a fresh _strengthened_<timestamp> suffix (no chained suffixes).

        Args:
            input_path: Input JSON path.

        Returns:
            Output path string.
        """
        input_path_obj = os.path.splitext(input_path)
        base_name = input_path_obj[0]
        extension = input_path_obj[1]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if '_context_strengthened_' in base_name:
            base_name = base_name.split('_context_strengthened_')[0]
            return f"{base_name}_strengthened_{timestamp}{extension}"
        elif '_strengthened_' in base_name:
            base_name = base_name.split('_strengthened_')[0]
            return f"{base_name}_strengthened_{timestamp}{extension}"
        else:
            return f"{base_name}_strengthened_{timestamp}{extension}"

