#!/usr/bin/env python3
"""
Contextual strengthener: enriches discussions using context documents (CSO graphs).
"""

import os
import sys
import json
import logging
import math
from typing import Dict, Any, Optional

# Module path setup for imports (repo root = parent of ontology/Bayesian_modeling)
_script_dir = os.path.dirname(os.path.abspath(__file__))
_bayesian_modeling_dir = os.path.dirname(_script_dir)
_repo_root = os.path.dirname(_bayesian_modeling_dir)
demo_site_src = os.path.join(_repo_root, 'demo-site', 'src')
if demo_site_src not in sys.path:
    sys.path.insert(0, demo_site_src)

from llm_processor_bm import LLMProcessorBM


class ContextualStrengthener:
    """
    Strengthens discussion argumentation using contextual documents represented as CSO.
    """

    def __init__(self, llm_processor: LLMProcessorBM, config: Dict[str, Any]):
        """
        Initialize the contextual strengthener.

        Args:
            llm_processor: LLMProcessorBM instance for LLM calls.
            config: Pipeline configuration (e.g. config_bm_test.yaml).
        """
        self.llm_processor = llm_processor
        self.config = config

        # Contextual strengthening settings
        self.contextual_config = config.get('pipeline', {}).get('contextual_strengthening', {})
        self.enabled = self.contextual_config.get('enabled', True)
        self.max_new_statements_coefficient = self.contextual_config.get('max_new_statements_coefficient', 0.4)

        self.logger = logging.getLogger(__name__)

    def _count_statements(self, cso_data: Dict) -> int:
        """Count statement nodes in CSO."""
        nodes = cso_data.get('nodes', [])
        return sum(1 for node in nodes if node.get('type') == 'statement')

    def _prepare_cso_for_prompt(self, cso_data: Dict) -> Dict:
        """Prepare CSO for the prompt (nodes and edges only; omit metadata and merge_report)."""
        cso_for_prompt = {
            'nodes': cso_data.get('nodes', []),
            'edges': cso_data.get('edges', [])
        }
        return cso_for_prompt

    def _create_contextual_prompt(self, discussion_cso: Dict, context_cso: Dict, max_new_statements: int) -> str:
        """Build the LLM prompt for context-based strengthening."""
        discussion_prepared = self._prepare_cso_for_prompt(discussion_cso)
        context_prepared = self._prepare_cso_for_prompt(context_cso)

        discussion_json = json.dumps(discussion_prepared, ensure_ascii=False, indent=2)
        context_json = json.dumps(context_prepared, ensure_ascii=False, indent=2)

        prompt = f"""You are given:

- A discussion represented as a CSO graph (statements/arguments and edges),
- Context documents also represented as a CSO graph (statements/arguments and edges).

Your task:

Analyze the discussion argumentation as a whole.
Find statements in the context documents that:
- are logically connected to those arguments,
- can strengthen, refine, challenge, or add an important new dimension (effects, risks, fairness, regional aspects, etc.).

Build a list of candidate statements C₁…Cₙ.

Score each candidate on:
- relevance to the key argument,
- structural usefulness (closes a gap or adds a new line of reasoning),
- epistemic strength (how reliable and significant the source is),
- novelty relative to existing CSO nodes.

Select at most {max_new_statements} best candidates and only for those:
- create new statement nodes in the discussion CSO,
- link them to existing nodes (supports/undermines/context/contradicts),
- explicitly cite the document and section they come from.

Do not invent facts or arguments: use only what is explicitly present in the context documents. Your job is to select and embed the most useful statements into the existing CSO graph.

**DISCUSSION (CSO):**
{discussion_json}

**CONTEXT DOCUMENTS (CSO):**
{context_json}

**IMPORTANT:**
- Return ONLY the updated discussion CSO (not the context graph).
- Add at most {max_new_statements} new statements.
- Every new statement must be linked to existing nodes.
- Response must be valid JSON per the CSO schema.
- Preserve all existing nodes and edges from the discussion.
- New statements must include prior_probability.

Return the answer as CSO JSON only (no extra text):
"""
        return prompt

    def strengthen_with_context(self, discussion_cso: Dict, context_cso: Dict) -> Optional[Dict]:
        """
        Strengthen the discussion graph using context CSO data.

        Args:
            discussion_cso: Discussion CSO.
            context_cso: Context documents CSO.

        Returns:
            Strengthened discussion CSO, or None on error.
        """
        if not self.enabled:
            self.logger.warning("Contextual strengthening is disabled")
            return discussion_cso

        try:
            statements_count = self._count_statements(discussion_cso)
            max_new_statements = math.ceil(statements_count * self.max_new_statements_coefficient)

            if max_new_statements < 1:
                max_new_statements = 1

            self.logger.info(
                f"Strengthening discussion with context. Statements in discussion: {statements_count}, "
                f"max new statements: {max_new_statements}"
            )

            prompt = self._create_contextual_prompt(discussion_cso, context_cso, max_new_statements)

            response = self.llm_processor.client.chat.completions.create(
                model=self.llm_processor.model,
                messages=[
                    {"role": "system", "content": "You are an expert in argumentation analysis and knowledge integration. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.llm_processor.temperature,
                max_tokens=self.llm_processor.max_tokens
            )

            response_text = response.choices[0].message.content.strip()

            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            strengthened_cso = json.loads(response_text)

            if 'nodes' not in strengthened_cso or 'edges' not in strengthened_cso:
                self.logger.error("Invalid CSO format in LLM response")
                return None

            if 'metadata' in discussion_cso:
                strengthened_cso['metadata'] = discussion_cso['metadata'].copy()

            new_statements = self._count_statements(strengthened_cso) - statements_count
            self.logger.info(
                f"Contextual strengthening completed. Added {new_statements} new statements (max was {max_new_statements})"
            )

            return strengthened_cso

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in contextual strengthening: {e}")
            if 'response_text' in locals():
                self.logger.debug(f"Response text: {response_text[:500]}")
            return None
        except Exception as e:
            self.logger.error(f"Error in contextual strengthening: {e}", exc_info=True)
            return None

