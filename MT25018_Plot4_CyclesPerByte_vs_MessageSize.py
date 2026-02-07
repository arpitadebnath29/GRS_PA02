#!/usr/bin/env python3
"""
MT25018 - Graduate Systems PA02
Part D: Plot 4 - CPU Cycles per Byte Transferred
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
print("MT25018 - Plot 4: CPU Cycles per Byte Transferred")
print("=" * 60)

# ============================================================================
# HARDCODED DATA FROM CSV FILES
# ============================================================================

# CPU Cycles: MessageSize -> [thread1, thread2, thread4, thread8]
cpu_cycles_data = {
    'TwoCopy': {
        512: [13972770167, 28692780291, 54504495952, 81540568230],
        4096: [14927789872, 27973573322, 55917079158, 81560785563],
        16384: [14588386482, 28870177450, 56097193819, 81642950713],
        65536: [13180640500, 27113757114, 53342318579, 77603131070]
    },
    'OneCopy': {
        512: [11809235017, 27680433616, 51578599816, 73180988253],
        4096: [14701606062, 28605870004, 55678894567, 81028802022],
        16384: [14554223810, 28908480203, 55861261874, 76427318629],
        65536: [14211251729, 27901124531, 54124496627, 71226394006]
    },
    'ZeroCopy': {
        512: [10594026780, 21221102993, 38753910838, 58185920132],
        4096: [5407654129, 11434905885, 33417252100, 63604655080],
        16384: [9885214037, 23495098094, 43376364747, 51076658470],
        65536: [14686539779, 26415012426, 50977702631, 49914716310]
    }
}

# Total Bytes: MessageSize -> [thread1, thread2, thread4, thread8]
total_bytes_data = {
    'TwoCopy': {
        512: [285926400, 278128640, 275443200, 112805376],
        4096: [698077184, 686399488, 780300288, 606171136],
        16384: [1283325952, 1232699392, 1202814976, 1221083136],
        65536: [4452843520, 4094296064, 3921346560, 2961309696]
    },
    'OneCopy': {
        512: [1363700224, 992754688, 822206464, 485127168],
        4096: [2205921280, 2028077056, 2064793600, 1655984128],
        16384: [7654391808, 7372013568, 5535547392, 3851911168],
        65536: [16608919552, 15743713280, 14667546624, 5939855360]
    },
    'ZeroCopy': {
        512: [276479488, 266907136, 205555712, 129507840],
        4096: [1906024448, 1773109248, 1243619328, 825896960],
        16384: [5329567744, 5625315328, 2983428096, 2134966272],
        65536: [10826547200, 10538254336, 8103460864, 5373362176]
    }
}

print(f"\nTotal experiments loaded: 48")
print(f"Implementations: TwoCopy, OneCopy, ZeroCopy")

# ============================================================================
# Plot 4: CPU Cycles per Byte Transferred
# ============================================================================
print("\nGenerating plot...")

fig, ax = plt.subplots(figsize=(10, 6))

message_sizes_kb = [0.5, 4, 16, 64]  # KB

for impl in ['TwoCopy', 'OneCopy', 'ZeroCopy']:
    # Calculate cycles per byte for each config and average across thread counts
    cycles_per_byte = []
    for msg_size in [512, 4096, 16384, 65536]:
        cpb_values = []
        for i in range(4):  # 4 thread counts
            cycles = cpu_cycles_data[impl][msg_size][i]
            bytes_transferred = total_bytes_data[impl][msg_size][i]
            cpb_values.append(cycles / bytes_transferred)
        cycles_per_byte.append(np.mean(cpb_values))
    
    ax.plot(message_sizes_kb, cycles_per_byte, marker='d', linewidth=2, 
            markersize=8, label=impl)

ax.set_xlabel('Message Size (KB)', fontsize=12, fontweight='bold')
ax.set_ylabel('CPU Cycles per Byte', fontsize=12, fontweight='bold')
ax.set_title('CPU Cycles per Byte Transferred vs Message Size\n(Averaged across all thread counts)', 
             fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_xscale('log', base=2)

# Add system config
fig.text(0.02, 0.02, SYSTEM_CONFIG, fontsize=7, family='monospace', 
         verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()
output_file = f"{OUTPUT_DIR}/MT25018_Plot4_CyclesPerByte_vs_MessageSize.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\n✅ Plot saved: {output_file}")
plt.close()
