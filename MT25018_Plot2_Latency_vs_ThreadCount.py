#!/usr/bin/env python3
"""
MT25018 - Graduate Systems PA02
Part D: Plot 2 - Latency vs Thread Count
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import platform
import subprocess

# Output directory
OUTPUT_DIR = "plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Get system configuration
def get_system_config():
    try:
        cpu_info = subprocess.check_output("lscpu | grep 'Model name' | cut -d ':' -f2", shell=True).decode().strip()
    except:
        cpu_info = platform.processor()
    
    try:
        mem_info = subprocess.check_output("free -h | grep Mem | awk '{print $2}'", shell=True).decode().strip()
    except:
        mem_info = "Unknown"
    
    kernel_version = platform.release()
    
    return f"CPU: {cpu_info}\nRAM: {mem_info}\nKernel: {kernel_version}"

SYSTEM_CONFIG = get_system_config() + "\nUbuntu 24.04.3 LTS (x86_64) | Intel i5-12450H (12th Gen) | 16 GB RAM | Intel UHD Graphics"

print("=" * 60)
print("MT25018 - Plot 2: Latency vs Thread Count")
print("=" * 60)

# ============================================================================
# HARDCODED DATA FROM CSV FILES
# ============================================================================

# Latency data: ThreadCount -> [512B, 4KB, 16KB, 64KB]
latency_data = {
    'TwoCopy': {
        1: [3.59, 11.53, 25.39, 29.59],
        2: [3.65, 11.83, 26.61, 31.87],
        4: [3.67, 10.43, 26.64, 33.24],
        8: [10.22, 12.06, 29.82, 41.44]
    },
    'OneCopy': {
        1: [0.72, 3.44, 4.18, 7.85],
        2: [1.01, 3.80, 3.90, 8.29],
        4: [1.21, 3.93, 5.51, 8.85],
        8: [2.34, 5.34, 9.52, 21.34]
    },
    'ZeroCopy': {
        1: [3.69, 4.45, 6.11, 12.19],
        2: [3.81, 4.59, 5.76, 12.37],
        4: [4.95, 6.58, 10.90, 15.99],
        8: [7.53, 8.67, 15.72, 24.24]
    }
}

print(f"\nTotal experiments loaded: 48")
print(f"Implementations: TwoCopy, OneCopy, ZeroCopy")

# ============================================================================
# Plot 2: Latency vs Thread Count
# ============================================================================
print("\nGenerating plot...")

fig, ax = plt.subplots(figsize=(10, 6))

thread_counts = [1, 2, 4, 8]

for impl in ['TwoCopy', 'OneCopy', 'ZeroCopy']:
    # Average latency across all message sizes for each thread count
    avg_latency = []
    for threads in thread_counts:
        avg_latency.append(np.mean(latency_data[impl][threads]))
    
    ax.plot(thread_counts, avg_latency, marker='s', linewidth=2, 
            markersize=8, label=impl)

ax.set_xlabel('Thread Count', fontsize=12, fontweight='bold')
ax.set_ylabel('Average Latency (μs)', fontsize=12, fontweight='bold')
ax.set_title('Latency vs Thread Count\n(Averaged across all message sizes)', 
             fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_xticks([1, 2, 4, 8])

# Add system config
fig.text(0.02, 0.02, SYSTEM_CONFIG, fontsize=7, family='monospace', 
         verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()
output_file = f"{OUTPUT_DIR}/MT25018_Plot2_Latency_vs_ThreadCount.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\n✅ Plot saved: {output_file}")
plt.close()
