#!/usr/bin/env python3
"""
MT25018 - Graduate Systems PA02
Part D: Plot 3 - Cache Misses vs Message Size
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
print("MT25018 - Plot 3: Cache Misses vs Message Size")
print("=" * 60)

# ============================================================================
# HARDCODED DATA FROM CSV FILES
# ============================================================================

# L1 Cache Misses: MessageSize -> [thread1, thread2, thread4, thread8]
l1_misses_data = {
    'TwoCopy': {
        512: [23771328, 31988864, 54179328, 136452096],
        4096: [44551168, 91164672, 166903808, 273631232],
        16384: [74483712, 134459392, 260493312, 561885184],
        65536: [156820480, 300072960, 656113664, 941666304]
    },
    'OneCopy': {
        512: [17920000, 61097984, 103023616, 182100992],
        4096: [62771200, 117772288, 237477888, 586710016],
        16384: [220381184, 427096064, 807477248, 1109671936],
        65536: [384557056, 728868864, 1319116800, 1669746688]
    },
    'ZeroCopy': {
        512: [61038080, 111524864, 206301184, 293396480],
        4096: [11679744, 25976832, 114208768, 328573952],
        16384: [108863488, 278450176, 485511168, 472621056],
        65536: [284319744, 541908992, 928440320, 728989696]
    }
}

# LLC Cache Misses: MessageSize -> [thread1, thread2, thread4, thread8]
llc_misses_data = {
    'TwoCopy': {
        512: [25976, 7595, 48480, 60426],
        4096: [16627, 31637, 63200, 341959],
        16384: [7475, 15220, 29947, 154512],
        65536: [34019, 57294, 536321, 657565]
    },
    'OneCopy': {
        512: [19936, 17820, 59523, 181891],
        4096: [28669, 32671, 115625, 365891],
        16384: [29534, 31218, 155823, 1044974],
        65536: [14390, 30941, 397705, 2631778]
    },
    'ZeroCopy': {
        512: [12508, 7161, 24442, 21420],
        4096: [69300, 169616, 315041, 265015],
        16384: [117872, 107409, 190099, 793089],
        65536: [14476, 34519, 410261, 1161740]
    }
}

print(f"\nTotal experiments loaded: 48")
print(f"Implementations: TwoCopy, OneCopy, ZeroCopy")

# ============================================================================
# Plot 3: Cache Misses vs Message Size
# ============================================================================
print("\nGenerating plot...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

message_sizes_kb = [0.5, 4, 16, 64]  # KB

# L1 Cache Misses
for impl in ['TwoCopy', 'OneCopy', 'ZeroCopy']:
    avg_l1_misses = []
    for msg_size in [512, 4096, 16384, 65536]:
        avg_l1_misses.append(np.mean(l1_misses_data[impl][msg_size]) / 1e6)
    
    ax1.plot(message_sizes_kb, avg_l1_misses, marker='o', linewidth=2, 
            markersize=8, label=impl)

ax1.set_xlabel('Message Size (KB)', fontsize=12, fontweight='bold')
ax1.set_ylabel('L1 Cache Misses (Millions)', fontsize=12, fontweight='bold')
ax1.set_title('L1 Cache Misses vs Message Size', fontsize=13, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.set_xscale('log', base=2)

# LLC Cache Misses
for impl in ['TwoCopy', 'OneCopy', 'ZeroCopy']:
    avg_llc_misses = []
    for msg_size in [512, 4096, 16384, 65536]:
        avg_llc_misses.append(np.mean(llc_misses_data[impl][msg_size]) / 1e6)
    
    ax2.plot(message_sizes_kb, avg_llc_misses, marker='s', linewidth=2, 
            markersize=8, label=impl)

ax2.set_xlabel('Message Size (KB)', fontsize=12, fontweight='bold')
ax2.set_ylabel('LLC Cache Misses (Millions)', fontsize=12, fontweight='bold')
ax2.set_title('LLC Cache Misses vs Message Size', fontsize=13, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.set_xscale('log', base=2)

fig.suptitle('Cache Misses vs Message Size\n(Averaged across all thread counts)', 
             fontsize=14, fontweight='bold', y=1.00)

# Add system config
fig.text(0.02, 0.02, SYSTEM_CONFIG, fontsize=7, family='monospace', 
         verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()
output_file = f"{OUTPUT_DIR}/MT25018_Plot3_CacheMisses_vs_MessageSize.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\n✅ Plot saved: {output_file}")
plt.close()
