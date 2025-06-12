"""
Cognitive Ontology Graph Visualization Tool

This tool creates various visualizations of cognitive ontology data using Graphviz.

Object Types and Their Relationships:
1. Statements (Утверждения):
   - Can connect to all other types of objects
   - Can connect to other statements
   - Represented as colored rectangles based on credibility

2. Cognitive Biases (Биасы):
   - Can connect to statements
   - Can connect to other biases
   - Represented as hexagons
   - In bias notation, connections between biases show:
     * Number of shared statements
     * Number of direct bias-to-bias connections
     * Total sum of both types of connections

3. Arguments (Аргументы):
   - Can only connect to statements
   - Represented as purple circles

4. Quotations (Цитаты):
   - Can only connect to statements
   - Represented as text nodes

Notation Types:
- Hierarchical: Traditional tree-like structure
- Context: Biases as columns, statements spanning columns, citations in rightmost column
- Bias: Each bias as a colored block containing its statements, with weighted connections showing both statement and bias relationships
- Sequential: Linear arrangement with random vertical distribution
"""

import json
import graphviz
import sys
import random
import math
import os
from typing import Dict, List, Set

def load_data(file_path: str) -> Dict:
    """Load data from a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_bias_color(index: int) -> str:
    """Get color for bias based on its index, cycling through 12 colors."""
    colors = [
        '#FFE4E1',  # Misty Rose
        '#E6E6FA',  # Lavender
        '#F0FFF0',  # Honeydew
        '#FFF0F5',  # Lavender Blush
        '#F0F8FF',  # Alice Blue
        '#FFFACD',  # Lemon Chiffon
        '#E0FFFF',  # Light Cyan
        '#F5F5DC',  # Beige
        '#FFEFD5',  # Peach Puff
        '#F0E68C',  # Khaki
        '#E6E6FA',  # Light Steel Blue
        '#FFDAB9'   # Peach
    ]
    return colors[index % len(colors)]

def create_context_oriented_graph(data: Dict) -> graphviz.Digraph:
    """Create a context-oriented graph visualization."""
    dot = graphviz.Digraph('Cognitive Ontology', format='png', engine='neato')
    
    # Set graph attributes
    dot.attr(overlap='false')
    dot.attr(splines='line')
    dot.attr(sep='+12')
    
    # Set node styles
    dot.attr('node', shape='box', style='rounded')  # Box shape for statements
    dot.attr('edge', style='dotted', dir='none')  # Dotted lines without arrows
    
    # Create dictionaries for quick lookup
    nodes = {node['id']: node for node in data['nodes']}
    edges = data['edges']
    
    # Find all biases and statements
    biases = [node for node in data['nodes'] if node['type'] == 'cognitive_bias']
    statements = [node for node in data['nodes'] if node['type'] == 'statement']
    
    # Create a mapping of statements to their connected biases
    statement_bias_map = {}
    for edge in edges:
        if edge['from'] in [b['id'] for b in biases] and edge['to'] in [s['id'] for s in statements]:
            if edge['to'] not in statement_bias_map:
                statement_bias_map[edge['to']] = []
            statement_bias_map[edge['to']].append(edge['from'])
    
    # Check if there are any statements without bias connections
    has_no_bias_statements = any(statement['id'] not in statement_bias_map for statement in statements)
    
    # Calculate total width for biases (excluding context)
    total_width = 20  # Total width of the graph
    context_width = 3  # Width of context box
    context_offset = 8  # Offset for context box
    no_bias_width = 3 if has_no_bias_statements else 0  # Width of "No Cognitive Biases" column
    bias_width = (total_width - context_width - context_offset - no_bias_width - 2) / (len(biases) if biases else 1)
    
    # Create "No Cognitive Biases" column only if needed
    if has_no_bias_statements:
        with dot.subgraph(name='cluster_no_bias') as s:
            s.attr(style='filled')
            s.attr(bgcolor='#E0E0E0')  # Light gray color
            s.attr(label='')
            s.attr(margin='0')
            s.attr(padding='0')
            s.attr(rank='same')
            # Add the column title
            s.node('no_bias_title', 'No Cognitive Biases', shape='none', pos=f'0,0!')
            # Add an invisible node at the bottom to extend the color
            bottom_y = -(len(statements) + 1) * 2
            s.node('bottom_no_bias', '', shape='none', style='invis', pos=f'0,{bottom_y}!')
            # Connect title to bottom node to create the column
            s.edge('no_bias_title', 'bottom_no_bias', style='invis')
    
    # Create background subgraphs for each bias column
    for i, bias in enumerate(biases):
        x = no_bias_width + 1 + (i * bias_width)  # Offset by no_bias_width + gap
        y = 0
        
        # Create a background subgraph for each bias column
        with dot.subgraph(name=f'cluster_{bias["id"]}') as s:
            s.attr(style='filled')
            s.attr(bgcolor=get_bias_color(i))
            s.attr(label='')
            s.attr(margin='0')
            s.attr(padding='0')
            s.attr(rank='same')
            # Add the bias node
            s.node(bias['id'], bias['text'], shape='none', pos=f'{x},{y}!')
            # Add an invisible node at the bottom to extend the color
            bottom_y = -(len(statements) + 1) * 2
            s.node(f'bottom_{bias["id"]}', '', shape='none', style='invis', pos=f'{x},{bottom_y}!')
            # Connect bias to bottom node to create the column
            s.edge(bias['id'], f'bottom_{bias["id"]}', style='invis')
    
    # Position statements
    for i, statement in enumerate(statements):
        connected_biases = statement_bias_map.get(statement['id'], [])
        y = -(i + 1) * 2  # Each statement on its own row
        
        if not connected_biases and has_no_bias_statements:
            # Place in "No Cognitive Biases" column
            dot.node(statement['id'], statement['text'],
                    pos=f'0,{y}!',
                    width='2',
                    style='filled',
                    fillcolor='white')
        elif len(connected_biases) > 1:
            # For statements connected to multiple biases, create separate nodes in each column
            prev_node = None
            # Sort biases by their position to ensure rightmost is last
            sorted_biases = sorted(connected_biases, 
                                 key=lambda b: biases.index(nodes[b]))
            
            for bias_id in sorted_biases:
                bias_index = biases.index(nodes[bias_id])
                x = no_bias_width + 1 + (bias_index * bias_width)
                
                # Create node ID specific to this bias column
                node_id = f"{statement['id']}_{bias_id}"
                
                # If this is the last bias column, show the text
                if bias_id == sorted_biases[-1]:
                    dot.node(node_id, statement['text'],
                            pos=f'{x},{y}!',
                            width='2',
                            style='filled',
                            fillcolor='white')
                else:
                    # For other columns, create an empty node
                    dot.node(node_id, '',
                            pos=f'{x},{y}!',
                            width='2',
                            height='0.6',
                            style='filled',
                            fillcolor='white')
                
                # Connect to previous node if it exists
                if prev_node is not None:
                    dot.edge(prev_node, node_id, style='dotted')
                
                prev_node = node_id
        else:
            # For statements connected to single bias
            bias_index = biases.index(nodes[connected_biases[0]])
            x = no_bias_width + 1 + (bias_index * bias_width)
            dot.node(statement['id'], statement['text'], 
                    pos=f'{x},{y}!',
                    width='2',
                    style='filled',
                    fillcolor='white')
    
    # Create context subgraph
    with dot.subgraph(name='cluster_context') as s:
        s.attr(label='')  # Remove label from inside
        s.attr(style='rounded')
        s.attr(bgcolor='white')
        
        # Add CONTEXT label as a separate node above the block
        context_x = total_width - context_width/2 - context_offset
        s.node('context_label', 'CONTEXT', 
               shape='none', 
               pos=f'{context_x},1!',
               fontsize='14',
               fontname='Arial Bold')
        
        # Get all citations
        citations = [nodes[edge['from']] for edge in edges if nodes[edge['from']]['type'] == 'quotation']
        
        # Calculate context box height based on number of citations
        context_height = len(statements) * 2 + 2  # Base height
        header_space = 1  # Space needed for header
        
        # Calculate vertical spacing between citations
        total_available_height = context_height - header_space
        citation_spacing = total_available_height / (len(citations) + 1)
        
        # Position citations inside the box
        for i, quote in enumerate(citations):
            # Calculate y position with even spacing
            y = -(header_space + (i + 1) * citation_spacing)
            
            # Check for collision with header
            if y > -header_space:
                # If collision detected, increase context height
                context_height += 1
                citation_spacing = (context_height - header_space) / (len(citations) + 1)
                y = -(header_space + (i + 1) * citation_spacing)
            
            s.node(quote['id'], quote['text'], 
                  shape='none', 
                  pos=f'{context_x},{y}!')
    
    # Add edges between statements and citations
    for edge in edges:
        if nodes[edge['from']]['type'] == 'quotation' and edge['to'] in [s['id'] for s in statements]:
            # Find the rightmost node for this statement
            statement = edge['to']
            connected_biases = statement_bias_map.get(statement, [])
            if len(connected_biases) > 1:
                # Use the last node (rightmost)
                last_bias = sorted(connected_biases, 
                                 key=lambda b: biases.index(nodes[b]))[-1]
                target_node = f"{statement}_{last_bias}"
            else:
                target_node = statement
            dot.edge(target_node, edge['from'])
    
    return dot

def create_hierarchical_graph(data: Dict) -> graphviz.Digraph:
    """Create a hierarchical graph visualization."""
    dot = graphviz.Digraph('Cognitive Ontology', format='png', engine='neato')
    
    # Set graph attributes
    dot.attr(overlap='false')
    dot.attr(splines='line')
    dot.attr(sep='+12')
    
    # Set node styles
    dot.attr('node', shape='box', style='rounded')  # Box shape for statements
    dot.attr('edge', style='dotted', dir='none')  # Dotted lines without arrows
    
    # Create dictionaries for quick lookup
    nodes = {node['id']: node for node in data['nodes']}
    edges = data['edges']
    
    # Find all biases and statements
    biases = [node for node in data['nodes'] if node['type'] == 'cognitive_bias']
    statements = [node for node in data['nodes'] if node['type'] == 'statement']
    
    # Create a mapping of statements to their connected biases
    statement_bias_map = {}
    for edge in edges:
        if edge['from'] in [b['id'] for b in biases] and edge['to'] in [s['id'] for s in statements]:
            if edge['to'] not in statement_bias_map:
                statement_bias_map[edge['to']] = []
            statement_bias_map[edge['to']].append(edge['from'])
    
    # Calculate total width for biases (excluding context)
    total_width = 20  # Total width of the graph
    context_width = 3  # Width of context box
    context_offset = 8  # Offset for context box
    bias_width = total_width - context_width - context_offset - 1  # Added gap between biases and context
    
    # Create background subgraphs for each bias column
    for i, bias in enumerate(biases):
        x = (i * bias_width) / (len(biases) - 1) if len(biases) > 1 else bias_width / 2
        y = 0
        
        # Create a background subgraph for each bias column
        with dot.subgraph(name=f'cluster_{bias["id"]}') as s:
            s.attr(style='filled')
            s.attr(bgcolor=get_bias_color(i))
            s.attr(label='')
            s.attr(margin='0')
            s.attr(padding='0')
            s.attr(rank='same')
            # Add the bias node
            s.node(bias['id'], bias['text'], shape='none', pos=f'{x},{y}!')
            # Add an invisible node at the bottom to extend the color
            bottom_y = -(len(statements) + 1) * 2
            s.node(f'bottom_{bias["id"]}', '', shape='none', style='invis', pos=f'{x},{bottom_y}!')
            # Connect bias to bottom node to create the column
            s.edge(bias['id'], f'bottom_{bias["id"]}', style='invis')
    
    # Position statements
    for i, statement in enumerate(statements):
        connected_biases = statement_bias_map.get(statement['id'], [])
        y = -(i + 1) * 2  # Each statement on its own row
        
        if len(connected_biases) > 1:
            # For statements connected to multiple biases
            bias_positions = []
            for bias_id in connected_biases:
                bias_index = biases.index(nodes[bias_id])
                x = (bias_index * bias_width) / (len(biases) - 1) if len(biases) > 1 else bias_width / 2
                bias_positions.append(x)
            
            # Calculate center position and width
            min_x = min(bias_positions)
            max_x = max(bias_positions)
            center_x = (min_x + max_x) / 2
            width = (max_x - min_x) + 2  # Add padding
            
            dot.node(statement['id'], statement['text'], 
                    pos=f'{center_x},{y}!',
                    width=str(width),
                    style='filled',
                    fillcolor='white')  # White background for statements
        else:
            # For statements connected to single bias
            bias_index = biases.index(nodes[connected_biases[0]])
            x = (bias_index * bias_width) / (len(biases) - 1) if len(biases) > 1 else bias_width / 2
            dot.node(statement['id'], statement['text'], 
                    pos=f'{x},{y}!',
                    width='2',
                    style='filled',
                    fillcolor='white')  # White background for statements
    
    # Create context subgraph
    with dot.subgraph(name='cluster_context') as s:
        s.attr(label='')  # Remove label from inside
        s.attr(style='rounded')
        s.attr(bgcolor='white')
        
        # Add CONTEXT label as a separate node above the block
        context_x = total_width - context_width/2 - context_offset
        s.node('context_label', 'CONTEXT', 
               shape='none', 
               pos=f'{context_x},1!',
               fontsize='14',
               fontname='Arial Bold')
        
        # Get all citations
        citations = [nodes[edge['from']] for edge in edges if nodes[edge['from']]['type'] == 'quotation']
        
        # Calculate context box height based on number of citations
        context_height = len(statements) * 2 + 2  # Base height
        header_space = 1  # Space needed for header
        
        # Calculate vertical spacing between citations
        total_available_height = context_height - header_space
        citation_spacing = total_available_height / (len(citations) + 1)  # +1 for even distribution
        
        # Position citations inside the box
        for i, quote in enumerate(citations):
            # Calculate y position with even spacing
            y = -(header_space + (i + 1) * citation_spacing)
            
            # Check for collision with header
            if y > -header_space:
                # If collision detected, increase context height
                context_height += 1
                citation_spacing = (context_height - header_space) / (len(citations) + 1)
                y = -(header_space + (i + 1) * citation_spacing)
            
            s.node(quote['id'], quote['text'], 
                  shape='none', 
                  pos=f'{context_x},{y}!')
    
    # Add edges between statements and citations
    for edge in edges:
        if nodes[edge['from']]['type'] == 'quotation' and edge['to'] in [s['id'] for s in statements]:
            dot.edge(edge['to'], edge['from'])
    
    return dot

def create_bias_oriented_graph(data: Dict) -> graphviz.Digraph:
    """Create a bias-oriented graph visualization.
    
    Each bias is represented as a colored block containing its statements.
    Connections between biases show the total number of relationships:
    - Shared statements
    - Direct bias-to-bias connections
    """
    dot = graphviz.Digraph('Cognitive Ontology', format='png', engine='neato')
    
    # Set graph attributes
    dot.attr(overlap='false')
    dot.attr(splines='line')
    dot.attr(sep='+12')
    
    # Set node styles
    dot.attr('node', shape='box', style='rounded')
    dot.attr('edge', style='dotted', dir='none')
    
    # Create dictionaries for quick lookup
    nodes = {node['id']: node for node in data['nodes']}
    edges = data['edges']
    
    # Find all biases and statements
    biases = [node for node in data['nodes'] if node['type'] == 'cognitive_bias']
    statements = [node for node in data['nodes'] if node['type'] == 'statement']
    
    # Create a mapping of statements to their connected biases
    statement_bias_map = {}
    for edge in edges:
        if edge['from'] in [b['id'] for b in biases] and edge['to'] in [s['id'] for s in statements]:
            if edge['to'] not in statement_bias_map:
                statement_bias_map[edge['to']] = []
            statement_bias_map[edge['to']].append(edge['from'])
    
    # Calculate connection weights between biases
    bias_connections = {}  # For shared statements
    direct_bias_connections = {}  # For direct bias-to-bias connections
    
    # Calculate shared statements
    for statement in statements:
        connected_biases = statement_bias_map.get(statement['id'], [])
        if len(connected_biases) > 1:
            for i in range(len(connected_biases)):
                for j in range(i + 1, len(connected_biases)):
                    pair = tuple(sorted([connected_biases[i], connected_biases[j]]))
                    bias_connections[pair] = bias_connections.get(pair, 0) + 1
    
    # Calculate direct bias-to-bias connections
    for edge in edges:
        if (nodes[edge['from']]['type'] == 'cognitive_bias' and 
            nodes[edge['to']]['type'] == 'cognitive_bias'):
            pair = tuple(sorted([edge['from'], edge['to']]))
            direct_bias_connections[pair] = direct_bias_connections.get(pair, 0) + 1
    
    # Calculate total connections (sum of both types)
    total_connections = {}
    for pair in set(list(bias_connections.keys()) + list(direct_bias_connections.keys())):
        total_connections[pair] = (
            bias_connections.get(pair, 0) + 
            direct_bias_connections.get(pair, 0)
        )
    
    # Calculate optimal block sizes based on content
    block_sizes = {}
    for bias in biases:
        bias_statements = [s for s in statements if bias['id'] in statement_bias_map.get(s['id'], [])]
        # Calculate minimum width needed for content
        title_width = len(bias['text']) * 0.1  # Approximate width based on text length
        content_width = max(title_width, 3)  # Minimum width of 3 units
        content_height = 1 + (len(bias_statements) * 0.8)  # Title + statements
        # Make blocks more compact
        block_width = content_width * 0.4  # Reduced from 1.8
        block_height = content_height * 0.4  # Reduced from 1.8
        block_sizes[bias['id']] = (block_width, block_height)
    
    # Calculate grid positions for blocks
    n = len(biases)
    grid_size = math.ceil(math.sqrt(n))
    min_block_spacing = 3  # Minimum space between blocks
    
    # Calculate grid positions
    bias_positions = {}
    for i, bias in enumerate(biases):
        row = i // grid_size
        col = i % grid_size
        block_width, block_height = block_sizes[bias['id']]
        x = (col - grid_size/2) * (block_width + min_block_spacing)
        y = (row - grid_size/2) * (block_height + min_block_spacing)
        bias_positions[bias['id']] = (x, y)
    
    # Create bias subgraphs with statements
    for i, bias in enumerate(biases):
        bias_statements = [s for s in statements if bias['id'] in statement_bias_map.get(s['id'], [])]
        block_width, block_height = block_sizes[bias['id']]
        
        with dot.subgraph(name=f'cluster_{bias["id"]}') as s:
            s.attr(style='filled')
            s.attr(bgcolor=get_bias_color(i))
            s.attr(label='')
            s.attr(fontsize='14')
            s.attr(fontname='Arial Bold')
            
            # Add bias title node
            x, y = bias_positions[bias['id']]
            s.node(f'title_{bias["id"]}', 
                  bias['text'],
                  pos=f'{x},{y}!',
                  shape='box',
                  style='filled',
                  fillcolor=get_bias_color(i),
                  fontname='Arial Bold',
                  fontsize='80',
                  width=str(block_width),
                  height='0.6')
            
            # Add statements below the title
            for j, statement in enumerate(bias_statements):
                statement_y = y - 1.2 - (j * 0.8)
                s.node(f'{bias["id"]}_{statement["id"]}',
                      statement['text'],
                      pos=f'{x-1.4},{statement_y}!',
                      shape='box',
                      style='filled',
                      fillcolor='white',
                      width=str(block_width - 0.2),
                      height='0.7',
                      fontsize='70')
            
            # Add invisible nodes at all edges of the block for connections
            s.node(f'edge_top_{bias["id"]}', '', pos=f'{x},{y+block_height/2}!', shape='point', style='invis')
            s.node(f'edge_bottom_{bias["id"]}', '', pos=f'{x},{y-block_height/2}!', shape='point', style='invis')
            s.node(f'edge_left_{bias["id"]}', '', pos=f'{x-block_width/2},{y}!', shape='point', style='invis')
            s.node(f'edge_right_{bias["id"]}', '', pos=f'{x+block_width/2},{y}!', shape='point', style='invis')
    
    # Add edges between biases that share statements or have direct connections
    for (bias1, bias2), total_weight in total_connections.items():
        x1, y1 = bias_positions[bias1]
        x2, y2 = bias_positions[bias2]
        
        # Determine which edges are closest
        dx = x2 - x1
        dy = y2 - y1
        
        # Choose edge nodes based on relative positions
        if abs(dx) > abs(dy):
            # Horizontal connection
            edge1 = f'edge_right_{bias1}' if dx > 0 else f'edge_left_{bias1}'
            edge2 = f'edge_left_{bias2}' if dx > 0 else f'edge_right_{bias2}'
            # Calculate label position
            label_x = (x1 + x2) / 2
            label_y = max(y1, y2) + 0.8
        else:
            # Vertical connection
            edge1 = f'edge_top_{bias1}' if dy > 0 else f'edge_bottom_{bias1}'
            edge2 = f'edge_bottom_{bias2}' if dy > 0 else f'edge_top_{bias2}'
            # Calculate label position
            label_x = max(x1, x2) + 0.8
            label_y = (y1 + y2) / 2
        
        # Add edge with total weight label
        dot.edge(edge1, edge2, 
                label=str(total_weight), 
                fontsize='60',
                penwidth='2.0')
    
    return dot

def wrap_text(text: str, max_width: int = 20) -> str:
    """Wrap text to fit within max_width characters."""
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 <= max_width:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)

def calculate_node_dimensions(text: str, max_width: int = 20) -> tuple:
    """Calculate node dimensions based on wrapped text."""
    wrapped_text = wrap_text(text, max_width)
    lines = wrapped_text.split('\n')
    width = max(len(line) for line in lines) * 0.1  # Approximate width per character
    height = len(lines) * 0.3  # Approximate height per line
    
    # Make node more square-like
    if width > height * 2:
        # If too wide, increase height by adding more line breaks
        wrapped_text = wrap_text(text, max_width // 2)
        lines = wrapped_text.split('\n')
        width = max(len(line) for line in lines) * 0.1
        height = len(lines) * 0.3
    
    return width, height, wrapped_text

def check_text_overlap(pos1: dict, pos2: dict, padding: float = 0.5) -> bool:
    """Check if two nodes' text areas overlap."""
    # Calculate text area boundaries
    x1_min = pos1['x'] - padding
    x1_max = pos1['x'] + pos1['width'] + padding
    y1_min = pos1['y'] - pos1['height']/2 - padding
    y1_max = pos1['y'] + pos1['height']/2 + padding
    
    x2_min = pos2['x'] - padding
    x2_max = pos2['x'] + pos2['width'] + padding
    y2_min = pos2['y'] - pos2['height']/2 - padding
    y2_max = pos2['y'] + pos2['height']/2 + padding
    
    # Check for overlap
    return not (x1_max < x2_min or x2_max < x1_min or y1_max < y2_min or y2_max < y1_min)

def adjust_canvas_size(positions: list, min_size: float = 20.0) -> float:
    """Calculate required canvas size based on node positions."""
    max_x = max(pos['x'] + pos['width'] for pos in positions)
    max_y = max(abs(pos['y']) + pos['height']/2 for pos in positions)
    return max(min_size, max(max_x, max_y) + 4)  # Add padding

def create_sequential_graph(data: Dict) -> graphviz.Digraph:
    """Create a sequential graph visualization showing statements, biases, and arguments.
    
    The graph shows relationships between different types of objects:
    - Statements can connect to all other types and to other statements
    - Biases can connect to statements and other biases
    - Arguments can only connect to statements
    - Quotations can only connect to statements
    """
    dot = graphviz.Digraph('Cognitive Ontology', format='png', engine='dot')
    
    # Set graph attributes
    dot.attr(rankdir='LR')  # Left to right direction
    dot.attr(splines='line')
    dot.attr(sep='+5')  # Reduced separation
    dot.attr(size='20,20')  # Initial square canvas
    dot.attr(ratio='fill')
    
    # Set node styles
    dot.attr('node', shape='box', style='rounded')
    dot.attr('edge', style='solid', dir='forward')
    
    # Create dictionaries for quick lookup
    nodes = {node['id']: node for node in data['nodes'] if node['type'] != 'quotation'}  # Exclude quotations
    edges = [edge for edge in data['edges'] 
             if edge['from'] in nodes and edge['to'] in nodes]  # Only include edges between non-quotation nodes
    
    # Define colors
    colors = {
        'green': '#5cb85c',
        'yellow': '#f0ad4e',
        'red': '#d9534f',
        'gray': '#9e9e9e',
        'argument': '#b19cd9',  # Purple
        'cognitive_bias': '#f28e8c'
    }
    
    # Separate nodes by type
    statements = [n for n in nodes.values() if n['type'] == 'statement']
    biases = [n for n in nodes.values() if n['type'] == 'cognitive_bias']
    arguments = [n for n in nodes.values() if n['type'] == 'argument']
    
    # Layout parameters
    min_gap = 2.5  # Initial minimal gap between objects
    y_range = 8.0  # Initial range for random Y positions
    y_args = -8    # Initial Y for arguments
    max_attempts = 20  # Maximum attempts to find non-overlapping position
    
    # Place all main objects (statements + biases) in a row with random Y positions
    main_nodes = statements + biases
    main_nodes.sort(key=lambda n: n['id'])  # Consistent order
    node_positions = {}
    current_x = 0
    
    # Generate random Y positions for main nodes
    used_y_positions = set()
    for node in main_nodes:
        # Calculate dimensions and wrap text
        width, height, wrapped_text = calculate_node_dimensions(node['text'])
        
        # Try to find a non-overlapping Y position
        y_pos = 0
        overlap_found = True
        attempts = 0
        
        while overlap_found and attempts < max_attempts:
            y_pos = random.uniform(-y_range/2, y_range/2)
            overlap_found = False
            
            # Check overlap with existing nodes
            for existing_pos in node_positions.values():
                if check_text_overlap(
                    {'x': current_x, 'y': y_pos, 'width': width, 'height': height},
                    existing_pos
                ):
                    overlap_found = True
                    break
            
            attempts += 1
        
        # If still overlapping, increase y_range and try again
        if overlap_found:
            y_range *= 1.5
            y_pos = random.uniform(-y_range/2, y_range/2)
        
        used_y_positions.add(y_pos)
        node_positions[node['id']] = {
            'x': current_x,
            'y': y_pos,
            'width': width,
            'height': height,
            'text': wrapped_text
        }
        current_x += width + min_gap
    
    # Place arguments at the bottom with random X positions
    arg_positions = {}
    for arg in arguments:
        # Calculate dimensions and wrap text
        width, height, wrapped_text = calculate_node_dimensions(arg['text'], max_width=15)
        
        # Find all nodes this argument connects to
        connected = [e['to'] for e in edges if e['from'] == arg['id']]
        if connected:
            # Calculate average X position of connected nodes
            avg_x = sum(node_positions[c]['x'] + node_positions[c]['width']/2 for c in connected if c in node_positions) / len(connected)
            # Add some random offset
            x_pos = avg_x + random.uniform(-2.0, 2.0)
        else:
            x_pos = current_x + random.uniform(-2.0, 2.0)
        
        # Check if argument position overlaps with any existing node
        overlap_found = True
        attempts = 0
        while overlap_found and attempts < max_attempts:
            overlap_found = False
            for existing_pos in list(node_positions.values()) + list(arg_positions.values()):
                if check_text_overlap(
                    {'x': x_pos, 'y': y_args, 'width': width, 'height': height},
                    existing_pos
                ):
                    overlap_found = True
                    x_pos += width  # Move to the right
                    break
            attempts += 1
        
        arg_positions[arg['id']] = {
            'x': x_pos,
            'y': y_args,
            'width': width,
            'height': height,
            'text': wrapped_text
        }
    
    # Add nodes with calculated positions
    for node in main_nodes:
        pos = node_positions[node['id']]
        if node['type'] == 'statement':
            color = colors.get(node.get('credibility', 'gray'), colors['gray'])
            dot.node(node['id'], 
                    pos['text'],
                    shape='box',
                    style='filled',
                    fillcolor=color,
                    fontsize='60',
                    pos=f"{pos['x']},{pos['y']}!",
                    width=str(pos['width']),
                    height=str(pos['height']))
        elif node['type'] == 'cognitive_bias':
            dot.node(node['id'],
                    pos['text'],
                    shape='hexagon',
                    style='filled',
                    fillcolor=colors['cognitive_bias'],
                    fontsize='60',
                    pos=f"{pos['x']},{pos['y']}!",
                    width=str(pos['width']),
                    height=str(pos['height']))
    
    for arg in arguments:
        pos = arg_positions[arg['id']]
        dot.node(arg['id'],
                pos['text'],
                shape='circle',
                style='filled',
                fillcolor=colors['argument'],
                fontsize='60',
                fixedsize='true',
                width=str(max(pos['width'], pos['height'])),
                height=str(max(pos['width'], pos['height'])),
                margin='0.1',
                pos=f"{pos['x']},{pos['y']}!")
    
    # Add edges
    for edge in edges:
        dot.edge(edge['from'], 
                edge['to'],
                fontsize='50')
    
    # Calculate and set final canvas size
    all_positions = list(node_positions.values()) + list(arg_positions.values())
    canvas_size = adjust_canvas_size(all_positions)
    dot.attr(size=f"{canvas_size},{canvas_size}")  # Square canvas
    
    return dot

def render_graph(input_file, notation_type='hierarchical'):
    """
    Render a graph visualization from a JSON file.
    
    Args:
        input_file (str): Path to the input JSON file
        notation_type (str): Type of notation to use ('hierarchical', 'context', 'bias', or 'sequential')
    """
    # Load data
    data = load_data(input_file)
    
    # Create graph based on notation type
    if notation_type == 'hierarchical':
        G = create_hierarchical_graph(data)
    elif notation_type == 'context':
        G = create_context_oriented_graph(data)
    elif notation_type == 'bias':
        G = create_bias_oriented_graph(data)
    elif notation_type == 'sequential':
        G = create_sequential_graph(data)
    else:
        raise ValueError(f"Unknown notation type: {notation_type}")
    
    # Create visualisations directory if it doesn't exist
    visualisations_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'visualisations')
    os.makedirs(visualisations_dir, exist_ok=True)
    
    # Generate output filename based on input filename and notation type
    input_filename = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(visualisations_dir, f"{input_filename}_{notation_type}")
    
    # Render graph
    G.render(output_file, cleanup=True)
    print(f"Graph rendered to {output_file}.png")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python render_graph.py <input_file> [notation_type]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    notation_type = sys.argv[2] if len(sys.argv) > 2 else 'hierarchical'
    
    render_graph(input_file, notation_type) 