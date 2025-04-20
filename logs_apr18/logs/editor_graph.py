import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Get all matching editor comm latency files from 0418 in the current directory
editor_files = [
    f for f in os.listdir(".")
    if f.startswith("Editor") and "comm_latency" in f and "418" in f
]

# Load and combine data
combined_df = pd.concat([pd.read_csv(f) for f in editor_files], ignore_index=True)

# Find the latency/duration column
latency_col = next((col for col in combined_df.columns if 'latency' in col.lower() or 'duration' in col.lower()), None)
if latency_col is None:
    raise ValueError("No latency or duration column found in the input files.")

# Compute the CDF
latencies = np.sort(combined_df[latency_col].dropna())
cdf = np.arange(1, len(latencies) + 1) / len(latencies)

# Plot
plt.figure(figsize=(10, 6))
plt.plot(latencies, cdf)
plt.title("CDF of Editor Agent Comm Latencies (0418)")
plt.xlabel("Latency (ms)")
plt.ylabel("CDF")
plt.grid(True)
plt.text(0.95, 0.05, f"N = {len(latencies)}", transform=plt.gca().transAxes,
         fontsize=12, verticalalignment='bottom', horizontalalignment='right',
         bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'))
plt.tight_layout()
plt.show()

