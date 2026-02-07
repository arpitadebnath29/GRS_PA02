# MT25018 - Graduate Systems PA02
## Analysis of Network I/O Primitives

**Student:** Arpita Debnath (MT25018) | **Course:** CSE638 | **Deadline:** February 7, 2026

**GitHub Repository:** https://github.com/arpitadebnath29/GRS_PA02

---

## Overview

Comparison of three network I/O approaches:
- **TwoCopy:** send()/recv() - 8 separate syscalls per message
- **OneCopy:** sendmsg()/recvmsg() with iovec - 1 syscall per message
- **ZeroCopy:** MSG_ZEROCOPY - page pinning + DMA

All implementations use multithreaded TCP with network namespace isolation.

---

## Files

**Source Code (6 files):**
- `MT25018_Part_A1_{Server,Client}.c` - TwoCopy implementation
- `MT25018_Part_A2_{Server,Client}.c` - OneCopy implementation  
- `MT25018_Part_A3_{Server,Client}.c` - ZeroCopy implementation

**Scripts (5 files):**
- `MT25018_Part_C_run_experiments.sh` - Automated experiment runner
- `MT25018_Plot{1-4}_*.py` - Plotting scripts with hardcoded data

**Data (3 files):**
- `MT25018_{Throughput,Latency,Perf}_Metrics.csv` - Experimental results

**Build:**
- `Makefile`, `README.md`

**Report:**
- `MT25018_Report.pdf` - Complete analysis with diagrams

---

## Quick Start

### Build
```bash
make all
```

### Run Experiments (Requires sudo)
```bash
sudo ./MT25018_Part_C_run_experiments.sh
```
Creates network namespaces (server_ns: 10.1.1.1, client_ns: 10.1.1.2), runs 48 experiments (3 implementations × 4 sizes × 4 threads), collects metrics, **generates all plots automatically**, and cleans up.

### Generate Plots Manually (Optional)
If you want to regenerate plots separately:
```bash
python3 MT25018_Plot1_Throughput_vs_MessageSize.py
python3 MT25018_Plot2_Latency_vs_ThreadCount.py
python3 MT25018_Plot3_CacheMisses_vs_MessageSize.py
python3 MT25018_Plot4_CyclesPerByte_vs_MessageSize.py
```
**Note:** Plots use hardcoded data from scripts, not CSV files.

---

## Manual Testing

**Server (Terminal 1):**
```bash
./MT25018_Part_A1_Server 4096 4
```

**Client (Terminal 2):**
```bash
./MT25018_Part_A1_Client 127.0.0.1 4096 2
```

---

## Key Results

| Implementation | 512B | 4KB | 16KB | 64KB |
|---|---|---|---|---|
| **TwoCopy** | 1.14 Gbps | 2.79 Gbps | 5.13 Gbps | 17.80 Gbps |
| **OneCopy** | 5.44 Gbps | 8.82 Gbps | 30.61 Gbps | 66.42 Gbps |
| **ZeroCopy** | 1.11 Gbps | 7.62 Gbps | 21.31 Gbps | 43.29 Gbps |

**Key Findings:**
- OneCopy wins at all sizes (4.8-6× faster than TwoCopy)
- ZeroCopy slower than TwoCopy at 512B (setup overhead)
- ZeroCopy beats TwoCopy at 4KB+ (DMA benefits)
- Thread scaling degrades at 8 threads (cache contention)

---

## Requirements

- Linux kernel ≥ 4.14
- gcc, make, perf, python3 (matplotlib, numpy)
- Network namespaces (requires sudo)

---

## Metrics Collected

**Application:** Throughput (Gbps), Latency (μs)  
**Hardware:** CPU cycles, L1/LLC cache misses, context switches

---
