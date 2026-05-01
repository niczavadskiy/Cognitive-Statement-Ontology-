#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify debiasing functionality
"""

import os
import sys
from pathlib import Path
import json

# Import the debiasing tool
from cso_debiasing_tool import CSODebiasingTool

def main():
    """Test the debiasing tool"""
    
    # Path relative to the repository root (script in tools/debiasing/)
    # Use a repo-shipped Bayesian example, or set TEST_CSO_JSON to your graph path
    test_file = os.path.join(
        os.path.dirname(__file__), "..", "..", "ontology", "Bayesian_modeling",
        "examples_bayesian", "bayesian_example.json"
    )
    
    print("CSO Debiasing Tool Test")
    print("=" * 50)
    print(f"Test file: {test_file}")
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    try:
        # Create tool and run debiasing
        tool = CSODebiasingTool()
        output_path = tool.debias_cso_file(test_file)
        
        if output_path:
            print(f"✅ Success! Created: {output_path}")
            
            # Load and show results
            with open(output_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Show summary
            summary = results.get('debiasing_summary', {})
            print(f"\n📊 Summary:")
            print(f"   Biases found: {summary.get('total_cognitive_biases_found', 0)}")
            print(f"   Nodes affected: {summary.get('total_nodes_affected', 0)}")
            print(f"   Arguments recalculated: {summary.get('total_arguments_recalculated', 0)}")
            
            # Show bias details
            print(f"\n🧠 Biases removed:")
            for bias in results.get('cognitive_biases_removed', []):
                print(f"   • {bias.get('bias_name', '')} (weight: {bias.get('bias_weight', 0)})")
            
            # Show argument changes
            print(f"\n📈 Argument probability changes:")
            for arg in results.get('argument_recalculations', []):
                change = arg.get('change_percentage', 0)
                symbol = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                orig = arg.get('original_posterior', 0)
                debi = arg.get('debiased_posterior', 0)
                print(f"   {symbol} {arg.get('argument_id', '')}: {orig:.3f} → {debi:.3f} ({change:+.1f}%)")
            
            return True
        else:
            print("ℹ️ No biases found")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 50)
    print("✅ Test passed!" if success else "❌ Test failed!")
















