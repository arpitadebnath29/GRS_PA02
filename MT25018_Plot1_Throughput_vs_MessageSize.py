#!/usr/bin/env python3
"""
MT25018 - Graduate Systems PA02
Part D: Plot 1 - Throughput vs Message Size
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
print("MT25018 - Plot 1: Throughput vs Message Size")
print("=" * 60)

# ============================================================================
# HARDCODED DATA FROM CSV FILES
# ============================================================================

# Throughput data: Implementation -> MessageSize -> [thread1, thread2, thread4, thread8]
throughput_data = {
    'TwoCopy': {
        512: [1.14, 1.11, 1.10, 0.45],
        4096: [2.79, 2.74, 3.12, 2.42],
        16384: [5.13, 4.93, 4.81, 4.88],
        65536: [17.80, 16.37, 15.68, 11.84]
    },
    'OneCopy': {
        512: [5.44, 3.97, 3.29, 1.94],
        4096: [8.82, 8.11, 8.26, 6.62],
        16384: [30.61, 29.48, 22.12, 15.36],
        65536: [66.42, 62.95, 58.63, 23.73]
    },
    'ZeroCopy': {
        512: [1.11, 1.07, 0.82, 0.52],
        4096: [7.62, 7.09, 4.97, 3.30],
        16384: [21.31, 22.49, 11.93, 8.53],
        65536: [43.29, 42.14, 32.40, 21.42]
    }
}

print(f"\nTotal experiments loaded: 48")
print(f"Implementations: TwoCopy, OneCopy, ZeroCopy")

# ============================================================================
# Plot 1: Throughput vs Message Size
# ============================================================================
print("\nGenerating plot...")

fig, ax = plt.subplots(figsize=(10, 6))

message_sizes_kb = [0.5, 4, 16, 64]  # KB

for impl in ['TwoCopy', 'OneCopy', 'ZeroCopy']:
    # Average throughput across all thread counts for each message size
    avg_throughput = []
    for msg_size in [512, 4096, 16384, 65536]:
        avg_throughput.append(np.mean(throughput_data[impl][msg_size]))
    
    ax.plot(message_sizes_kb, avg_throughput, marker='o', linewidth=2, 
            markersize=8, label=impl)

ax.set_xlabel('Message Size (KB)', fontsize=12, fontweight='bold')
ax.set_ylabel('Throughput (Gbps)', fontsize=12, fontweight='bold')
ax.set_title('Throughput vs Message Size\n(Averaged across all thread counts)', 
             fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_xscale('log', base=2)

# Add system config as text
fig.text(0.02, 0.02, SYSTEM_CONFIG, fontsize=7, family='monospace', 
         verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()
output_file = f"{OUTPUT_DIR}/MT25018_Plot1_Throughput_vs_MessageSize.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\n✅ Plot saved: {output_file}")
plt.close()
