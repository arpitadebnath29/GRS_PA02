# MT25018
# Graduate Systems PA02 - README

## Student Information
**Roll Number:** MT25018  
**Course:** CSE638 - Graduate Systems  
**Assignment:** PA02 - Analysis of Network I/O Primitives  
**Deadline:** February 7, 2026

---

## Assignment Overview

This assignment implements and compares three network I/O approaches:
1. **Two-Copy** (baseline using send()/recv())
2. **One-Copy** (using sendmsg() with iovec)
3. **Zero-Copy** (using sendmsg() with MSG_ZEROCOPY)

All implementations use multithreaded TCP client-server architecture with runtime-parameterized message sizes and thread counts.

---

## Files Included

### Source Code
- `MT25018_Part_A1_Server.c` - Two-copy server implementation
- `MT25018_Part_A1_Client.c` - Two-copy client implementation
- `MT25018_Part_A2_Server.c` - One-copy server implementation
- `MT25018_Part_A2_Client.c` - One-copy client implementation
- `MT25018_Part_A3_Server.c` - Zero-copy server implementation
- `MT25018_Part_A3_Client.c` - Zero-copy client implementation

### Build and Automation
- `Makefile` - Compilation targets for all implementations
- `MT25018_Part_C_run_experiments.sh` - Automated experiment runner with network namespace isolation

### Analysis and Visualization
- `MT25018_Plot1_Throughput_vs_MessageSize.py` - Throughput vs Message Size (hardcoded data)
- `MT25018_Plot2_Latency_vs_ThreadCount.py` - Latency vs Thread Count (hardcoded data)
- `MT25018_Plot3_CacheMisses_vs_MessageSize.py` - L1/LLC Cache Misses (hardcoded data)
- `MT25018_Plot4_CyclesPerByte_vs_MessageSize.py` - CPU Cycles per Byte (hardcoded data)
- `MT25018_Throughput_Metrics.csv` - Application-level throughput measurements
- `MT25018_Latency_Metrics.csv` - Latency measurements
- `MT25018_Perf_Metrics.csv` - perf stat hardware counters

### Documentation
- `README.md` - This file
- `MT25018_PA02_Report.pdf` - Complete report with diagrams and analysis

---

## Building the Code

### Prerequisites
```bash
sudo apt-get install gcc make linux-tools-$(uname -r)
pip3 install matplotlib numpy
```

### Compile All Implementations
```bash
make all
```

### Compile Individual Parts
```bash
make A1    # Two-copy only
make A2    # One-copy only
make A3    # Zero-copy only
```

### Clean Build
```bash
make clean
```

---

## Running Experiments

### Option 1: Automated Experiments (Recommended)
**IMPORTANT: Requires sudo for network namespace support**
```bash
sudo ./MT25018_Part_C_run_experiments.sh
```
This runs all experiments across 4 message sizes and 4 thread counts, with:
- Server and clients in **separate network namespaces**
- Automatic namespace setup and cleanup
- Full perf metrics collection
- Results saved to CSV files

The script automatically:
1. Creates `server_ns` (10.1.1.1) and `client_ns` (10.1.1.2) namespaces
2. Sets up veth pair for network isolation
3. Runs all 48 experiments
4. Cleans up namespaces when done

### Option 2: Manual Testing (Localhost)

**Terminal 1 (Server):**
```bash
./MT25018_Part_A1_Server 4096 4
```

**Terminal 2 (Client):**
```bash
./MT25018_Part_A1_Client 127.0.0.1 4096 10
```

Replace `A1` with `A2` or `A3` for other implementations.

---

## Implementation Details

### Part A1: Two-Copy Implementation
- Uses `send()` for server transmission
- Uses `recv()` for client reception
- Each of 8 message fields sent separately
- **Copies:** User→Kernel (send), Kernel→User (recv)

### Part A2: One-Copy Implementation
- Uses `sendmsg()` with `struct iovec` (scatter-gather I/O)
- Uses `recvmsg()` with `struct iovec`
- Eliminates intermediate buffer copy via pre-registered buffers
- Kernel directly accesses user buffers through iovec

### Part A3: Zero-Copy Implementation
- Uses `sendmsg()` with `MSG_ZEROCOPY` flag
- Requires kernel >= 4.14 and SO_ZEROCOPY socket option
- Page pinning + DMA for direct NIC access
- Graceful fallback if unsupported

---

## Generating Plots

**IMPORTANT: All plotting scripts use hardcoded data - no CSV files required!**

Generate plots individually:
```bash
python3 MT25018_Plot1_Throughput_vs_MessageSize.py
python3 MT25018_Plot2_Latency_vs_ThreadCount.py
python3 MT25018_Plot3_CacheMisses_vs_MessageSize.py
python3 MT25018_Plot4_CyclesPerByte_vs_MessageSize.py
```

**Note:** All experimental data is hardcoded as arrays within each Python script. The scripts do NOT read from CSV files. This ensures plots can be generated during demo without dependency on CSV files.

Plots saved in `plots/` directory:
- Throughput vs Message Size
- Latency vs Thread Count
- Cache Misses vs Message Size (L1 and LLC)
- CPU Cycles per Byte

---

## Experiment Parameters

| Parameter | Values |
|-----------|--------|
| Message Sizes | 512B, 4KB, 16KB, 64KB |
| Thread Counts | 1, 2, 4, 8 |
| Test Duration | 10 seconds per configuration |
| Total Experiments | 48 (3 implementations × 4 sizes × 4 threads) |

---

## Metrics Collected

### Application-Level
- Throughput (Gbps)
- Latency (µs)
- Total bytes transferred
- Total messages transferred

### Hardware Counters (perf stat)
- CPU cycles
- Instructions executed
- Cache misses (L1, LLC)
- Context switches

---

## System Requirements

### Network Setup
**IMPORTANT:** Client and server must run in **separate network namespaces** (VMs will not work).

Use the provided `MT25018_setup_namespaces.sh` script which:
- Creates `server_ns` and `client_ns` namespaces
- Sets up veth pair with IPs 10.1.1.1/24 and 10.1.1.2/24
- Runs server in server_ns, clients in client_ns
- Automatically cleans up after completion

### Software
- Linux kernel >= 4.14 (for MSG_ZEROCOPY support)
- GCC compiler
- perf tools
- Python 3 with matplotlib and numpy

---

## Results Location

After running experiments:
```
experiment_results/
├── MT25018_Part_B_Application_Metrics.csv
├── MT25018_Part_B_Perf_Metrics.csv
└── [individual log files]

plots/
├── MT25018_Part_D_Throughput_vs_MessageSize.png
├── MT25018_Part_D_Latency_vs_ThreadCount.png
├── MT25018_Part_D_CacheMisses_vs_MessageSize.png
├── MT25018_Part_D_CPUCycles_per_Byte.png
└── MT25018_Part_D_Throughput_Comparison_All.png
```

---

## Part E: Analysis Questions

The report (`MT25018_Part_E_Report.pdf`) includes detailed analysis for:

1. Why zero-copy doesn't always give best throughput
2. Which cache level shows most reduction in misses
3. Thread count interaction with cache contention
4. Crossover point: one-copy vs two-copy
5. Crossover point: zero-copy vs two-copy
6. Unexpected result with OS/hardware explanation

---

## AI Usage Declaration

This implementation uses AI assistance (GitHub Copilot). Detailed declaration including:
- Specific components generated
- Prompts used
- Understanding verification

See report for complete AI usage declaration.

---

## GitHub Repository

**Public Repository:** [Your GitHub URL]

Folder structure: `GRS_PA02/` containing all source files, scripts, CSV data, and documentation.

---

## Submission Checklist

- [x] All files follow MT25018_Part naming convention
- [x] Makefile has roll number comment at top
- [x] README has roll number comment at top
- [x] Code is modular and well-commented
- [x] Message structure with 8 heap-allocated fields
- [x] Runtime parameterization working
- [x] Multithreading implemented correctly
- [x] perf integration complete
- [x] CSV output with encoded filenames
- [x] Matplotlib plots with hardcoded data
- [x] No binary executables in submission
- [x] No separate plot PNG/JPEG files
- [x] Report includes all analysis and AI declaration

---

## Troubleshooting

**Issue:** perf command not found  
**Solution:** `sudo apt-get install linux-tools-$(uname -r)`

**Issue:** Permission denied for perf  
**Solution:** `sudo sysctl -w kernel.perf_event_paranoid=-1`

**Issue:** MSG_ZEROCOPY not supported  
**Solution:** Check kernel version (`uname -r`), requires >= 4.14

**Issue:** Address already in use  
**Solution:** Wait 60 seconds between runs or change PORT in source

---

## Contact

**Student:** MT25018  
**Course:** CSE638 - Graduate Systems  
**Instructor:** [Instructor Name]

---

**Last Updated:** February 1, 2026
