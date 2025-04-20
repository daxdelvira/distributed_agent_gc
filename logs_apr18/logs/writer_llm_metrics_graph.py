import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Get all matching Editor llm_metrics files from 0418 in the current directory
editor_llm_files = [
    f for f in os.listdir(".")
    if f.startswith("Writer") and "llm_metrics" in f and "418" in f
]

# Load and combine data
combined_df = pd.concat([pd.read_csv(f) for f in editor_llm_files], ignore_index=True)

# Find the latency/duration column
latency_col = next((col for col in combined_df.columns if 'latency' in col.lower() or 'duration' in col.lower()), None)
if latency_col is None:
    raise ValueError("No latency or duration column found in the input files.")

# Compute the CDF
latencies = combined_df[latency_col].dropna().sample(n=21, random_state=42)
latencies = np.sort(latencies)

latencies = latencies[:-1]  # drop the single largest value
cdf = np.arange(1, len(latencies) + 1) / len(latencies)

# Plot
plt.figure(figsize=(10, 6))
plt.plot(latencies, cdf)

# Title with count
plt.title(f"CDF of Writer LLM Metrics Latencies (0418)\nN = {len(latencies)} data points")
plt.xlabel("Latency (s)")
plt.ylabel("CDF")
plt.grid(True)

# Optional: Add N as a label inside the plot
plt.text(0.95, 0.05, f"N = {len(latencies)}", transform=plt.gca().transAxes,
         fontsize=12, verticalalignment='bottom', horizontalalignment='right',
         bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'))

plt.tight_layout()
plt.show()

