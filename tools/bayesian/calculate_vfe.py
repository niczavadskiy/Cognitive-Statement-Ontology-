#!/usr/bin/env python3
"""
Standalone script to calculate Variational Free Energy (VFE) for arguments in CSO file.

Usage:
    python calculate_vfe.py <input_file> [output_file]
    
If output_file is not specified, VFE metrics are added to input_file in-place.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List

# Add parent directory to path to import calculator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from argument_probability_calculator import ArgumentProbabilityCalculator


def calculate_vfe_for_file(input_file: str, output_file: str = None) -> Dict:
    """
    Calculate VFE metrics for all arguments in CSO file
    
    Args:
        input_file: Path to input CSO JSON file
        output_file: Path to output file (if None, overwrites input_file)
        
    Returns:
        Summary dictionary with calculation results
    """
    # Load CSO data
    with open(input_file, 'r', encoding='utf-8') as f:
        cso_data = json.load(f)
    
    # Initialize calculator
    calculator = ArgumentProbabilityCalculator()
    
    # Calculate probabilities and VFE
    updated_nodes, updated_edges = calculator.calculate_all_argument_probabilities(
        cso_data['nodes'], cso_data['edges']
    )
    
    # Update data
    cso_data['nodes'] = updated_nodes
    cso_data['edges'] = updated_edges
    
    # Prepare output file path
    if output_file is None:
        output_file = input_file
    
    # Save updated data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cso_data, f, ensure_ascii=False, indent=2)
    
    # Generate summary
    arguments_with_vfe = [
        node for node in updated_nodes 
        if node['type'] == 'argument' and 'vfe' in node
    ]
    
    # Get Total Predictability from calculator
    total_predictability = calculator.total_predictability if hasattr(calculator, 'total_predictability') else None
    
    summary = {
        'input_file': input_file,
        'output_file': output_file,
        'arguments_processed': len(arguments_with_vfe),
        'arguments': [
            {
                'id': arg['id'],
                'vfe': arg['vfe']['variational_free_energy'],
                'log_evidence': arg['vfe']['log_evidence'],
                'kl_divergence': arg['vfe']['kl_divergence'],
                'F_bar_k': arg['vfe'].get('F_bar_k', 0.0),
                'predictability_contribution': arg['vfe'].get('predictability_contribution', 0.0)
            }
            for arg in arguments_with_vfe
        ]
    }
    
    # Add Total Predictability if available
    if total_predictability:
        summary['total_predictability'] = total_predictability
    
    return summary


def main():
    """Main entry point for standalone script"""
    if len(sys.argv) < 2:
        print("Usage: python calculate_vfe.py <input_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    
    print(f"Calculating VFE for: {input_file}")
    
    try:
        summary = calculate_vfe_for_file(input_file, output_file)
        
        print(f"\n✅ VFE calculation complete!")
        print(f"   Arguments processed: {summary['arguments_processed']}")
        print(f"   Output saved to: {summary['output_file']}")
        
        print(f"\n📊 VFE Summary (sorted by VFE, lower is better):")
        sorted_args = sorted(summary['arguments'], key=lambda x: x['vfe'])
        for arg in sorted_args[:10]:  # Show top 10
            print(f"   {arg['id']}: VFE={arg['vfe']:.4f} "
                  f"(log_evidence={arg['log_evidence']:.4f}, "
                  f"KL={arg['kl_divergence']:.4f})")
        
        # Display Total Predictability if available
        if 'total_predictability' in summary:
            tp = summary['total_predictability']
            print(f"\n📈 TOTAL PREDICTABILITY: {tp['total_predictability']:.4f}")
            print(f"   Arguments: {tp['arguments_count']}")
            print(f"   Average contribution: {tp['average_contribution']:.4f}")
        
    except Exception as e:
        print(f"❌ Error calculating VFE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

