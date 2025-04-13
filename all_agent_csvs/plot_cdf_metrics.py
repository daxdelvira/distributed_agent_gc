import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Define roles and base path
roles = ["Editor", "Writer", "group_chat_manager"]
base_path = "/home/daxvdv/daxwork/projects/distributed_agent_gc/all_agent_csvs"  # Change this to the folder with the CSVs

def plot_cdf(data1, data2, label1, label2, column, xlabel, title, role):
    sorted1 = np.sort(data1[column])
    sorted2 = np.sort(data2[column])
    cdf1 = np.arange(1, len(sorted1)+1) / len(sorted1)
    cdf2 = np.arange(1, len(sorted2)+1) / len(sorted2)
    
    plt.figure(figsize=(10, 6))
    plt.plot(sorted1, cdf1, label=label1, linewidth=2)
    plt.plot(sorted2, cdf2, label=label2, linewidth=2)
    plt.xlabel(xlabel)
    plt.ylabel("Cumulative Probability")
    plt.title(f"{title} - {role}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

for role in roles:
    # Construct filenames
    normal_file = os.path.join(base_path, f"metrics_{role}.csv")
    state_file = os.path.join(base_path, f"metrics_{role.lower()}_state.csv")

    # Load data
    df_normal = pd.read_csv(normal_file)
    df_state = pd.read_csv(state_file)

    # Plot Duration CDF
    plot_cdf(df_normal, df_state,
             f"{role} (normal)", f"{role} (state traced)",
             column="duration_sec",
             xlabel="Duration (seconds)",
             title="CDF of Duration", role=role)

    # Plot Memory CDF
    plot_cdf(df_normal, df_state,
             f"{role} (normal)", f"{role} (state traced)",
             column="peak_memory_bytes",
             xlabel="Peak Memory (bytes)",
             title="CDF of Peak Memory Usage", role=role)
