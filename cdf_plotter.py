import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os

# Helper to compute CDF
def compute_cdf(data):
    sorted_data = np.sort(data)
    cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    return sorted_data, cdf

# File patterns
writer_files = sorted(glob.glob("writer_metrics_state_traced_export_*.csv"))
agent_files = sorted(glob.glob("editor_metrics_state_traced_export_*.csv"))

# Group files by variable count
def group_by_var_count(file_list):
    grouped = {}
    for f in file_list:
        name = os.path.basename(f)
        for count in ["1var", "10var", "50var"]:
            if count in name:
                grouped[count] = grouped.get(count, []) + [f]
    return grouped

writer_grouped = group_by_var_count(writer_files)
agent_grouped = group_by_var_count(agent_files)

# Load and concatenate data per variable count
def load_concat(files):
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

# Plot CDFs
def plot_cdf_fixed(grouped_data, metric, title, filename, convert_memory=False, function_filter=None):
    plt.figure(figsize=(10, 6))
    for var_count, files in grouped_data.items():
        df = load_concat(files)

        # Optional function filter
        if function_filter is not None and "function" in df.columns:
            df = df[df["function"] == function_filter]

        if metric in df.columns:
            values = df[metric].dropna()
            if convert_memory:
                values = values / (1024 * 1024)  # Convert bytes to MB
            x, y = compute_cdf(values)
            plt.plot(x, y, label=var_count)
    plt.xlabel("Memory (MB)" if convert_memory else metric)
    plt.ylabel("CDF")
    plt.title(title + (f" ({function_filter})" if function_filter else ""))
    plt.legend(title="Variable Count")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

# Example usage with function filter
plot_cdf_fixed(writer_grouped, "peak_memory_bytes", "Writer Agent Memory Usage CDF", "writer_memory_cdf_generate.png", convert_memory=True, function_filter="generate")
plot_cdf_fixed(writer_grouped, "duration_sec", "Writer Agent Duration CDF", "writer_duration_cdf_generate.png", function_filter="generate")
plot_cdf_fixed(agent_grouped, "peak_memory_bytes", "Editor Agent Memory Usage CDF", "editor_memory_cdf_generate.png", convert_memory=True, function_filter="generate")
plot_cdf_fixed(agent_grouped, "duration_sec", "Editor Agent Duration CDF", "editor_duration_cdf_generate.png", function_filter="generate")
