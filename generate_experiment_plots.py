import os
import pandas as pd
import matplotlib.pyplot as plt
from glob import glob

# Gruvbox dark theme manually set
plt.style.use('dark_background')
plt.rcParams.update({
    "axes.edgecolor": "#ebdbb2",
    "axes.labelcolor": "#ebdbb2",
    "xtick.color": "#ebdbb2",
    "ytick.color": "#ebdbb2",
    "text.color": "#ebdbb2",
    "figure.facecolor": "#282828",
    "axes.facecolor": "#3c3836",
    "savefig.facecolor": "#282828",
})

def plot_cdf(data, title, xlabel, ylabel, output_path):
    sorted_data = sorted(data)
    yvals = [i / len(sorted_data) for i in range(len(sorted_data))]
    plt.figure()
    plt.plot(sorted_data, yvals, marker='.')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.savefig(output_path)
    plt.close()

def plot_timeseries(x, y, title, xlabel, ylabel, output_path):
    plt.figure()
    plt.plot(x, y)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.savefig(output_path)
    plt.close()

def generate_all_plots():
    os.makedirs("plots", exist_ok=True)
    log_files = glob("logs/*.csv")
    for file in log_files:
        df = pd.read_csv(file)
        filename = os.path.basename(file)
        base = filename.replace(".csv", "")

        if "llm_metrics" in file and "duration_sec" in df.columns:
            plot_cdf(
                df["duration_sec"],
                f"LLM Latency CDF - {base}",
                "Duration (s)",
                "CDF",
                f"plots/{base}_cdf.png"
            )

        elif "comm_latency" in file and "latency_ms" in df.columns:
            plot_cdf(
                df["latency_ms"],
                f"Comms Latency CDF - {base}",
                "Latency (ms)",
                "CDF",
                f"plots/{base}_cdf.png"
            )

        elif "memory" in file and "timestamp" in df.columns:
            y_col = "rss_mb" if "rss_mb" in df.columns else "memory_mb"
            plot_timeseries(
                df["timestamp"],
                df[y_col],
                f"Memory Usage - {base}",
                "Time (s)",
                "Memory (MB)",
                f"plots/{base}_mem.png"
            )

if __name__ == "__main__":
    generate_all_plots()
