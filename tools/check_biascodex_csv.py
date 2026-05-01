import os
import csv

if __name__ == "__main__":
    # Resolve BiasCodexData.csv relative to repo layout (tools/ -> demo-site/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    csv_path = os.path.join(base_dir, 'demo-site', 'BiasCodexData.csv')
    biases = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 4 and row[2].strip() and row[3].strip():
                bias_id = row[2].strip()
                bias_text = row[3].strip()
                biases[bias_id] = bias_text
    valid_rows = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 4 and row[2].strip() and row[3].strip():
                valid_rows += 1
    print(f"Loaded {len(biases)} cognitive biases from CSV.")
    if valid_rows != len(biases):
        print(f"WARNING: Number of valid bias rows in CSV ({valid_rows}) does not match number loaded into dictionary ({len(biases)})")
    print("\nBiases loaded:")
    for bias_id, bias_text in biases.items():
        print(f"{bias_id}: {bias_text}") 