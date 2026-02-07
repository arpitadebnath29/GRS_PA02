#!/bin/bash
# MT25018 - Graduate Systems PA02
# Part C: Automated Experiment Script
# Runs experiments across message sizes and thread counts
# Collects perf stats and application-level metrics
# USES SEPARATE NETWORK NAMESPACES FOR CLIENT AND SERVER

set -e  # Exit on error

# Check if running as root (required for namespaces)
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run with sudo for network namespace support"
    echo "Usage: sudo $0"
    exit 1
fi

# Configuration
SERVER_NS="server_ns"
CLIENT_NS="client_ns"
VETH_SRV="veth_srv"
VETH_CLI="veth_cli"
SRV_IP="10.1.1.1"
CLI_IP="10.1.1.2"
SERVER_IP="$SRV_IP"  # Server IP in namespace
TEST_DURATION=10        # Duration for each client test in seconds
OUTPUT_DIR="experiment_results"
PERF_EVENTS="cycles,instructions,cache-misses,L1-dcache-load-misses,LLC-load-misses,context-switches"

# Experiment parameters
MESSAGE_SIZES=(512 4096 16384 65536)      # 512B, 4KB, 16KB, 64KB
THREAD_COUNTS=(1 2 4 8)                    # Number of concurrent clients
IMPLEMENTATIONS=("A1" "A2" "A3")
IMPL_NAMES=("TwoCopy" "OneCopy" "ZeroCopy")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "MT25018 Graduate Systems PA02"
echo "Automated Experiment Runner"
echo "WITH NETWORK NAMESPACE ISOLATION"
echo "=========================================="
echo ""

# Function to setup network namespaces
setup_namespaces() {
    echo "Setting up network namespaces..."
    
    # Delete existing namespaces if they exist
    ip netns del $SERVER_NS 2>/dev/null || true
    ip netns del $CLIENT_NS 2>/dev/null || true
    
    # Create namespaces
    ip netns add $SERVER_NS
    ip netns add $CLIENT_NS
    
    # Create veth pair
    ip link add $VETH_SRV type veth peer name $VETH_CLI
    
    # Move veth ends to namespaces
    ip link set $VETH_SRV netns $SERVER_NS
    ip link set $VETH_CLI netns $CLIENT_NS
    
    # Configure server namespace
    ip netns exec $SERVER_NS ip addr add ${SRV_IP}/24 dev $VETH_SRV
    ip netns exec $SERVER_NS ip link set $VETH_SRV up
    ip netns exec $SERVER_NS ip link set lo up
    
    # Configure client namespace
    ip netns exec $CLIENT_NS ip addr add ${CLI_IP}/24 dev $VETH_CLI
    ip netns exec $CLIENT_NS ip link set $VETH_CLI up
    ip netns exec $CLIENT_NS ip link set lo up
    
    echo -e "${GREEN}Network namespaces configured:${NC}"
    echo "  Server namespace: $SERVER_NS ($SRV_IP)"
    echo "  Client namespace: $CLIENT_NS ($CLI_IP)"
}

# Function to cleanup network namespaces
cleanup_namespaces() {
    echo "Cleaning up network namespaces..."
    ip netns del $SERVER_NS 2>/dev/null || true
    ip netns del $CLIENT_NS 2>/dev/null || true
}

# Cleanup any previous server processes and namespaces
echo "Cleaning up any previous processes and namespaces..."
pkill -f "MT25018_Part_A" 2>/dev/null || true
cleanup_namespaces
sleep 1

# Create output directory
mkdir -p "$OUTPUT_DIR"
echo -e "${GREEN}Created output directory: $OUTPUT_DIR${NC}"

# Compile all implementations
echo -e "\n${YELLOW}Compiling all implementations...${NC}"
make clean
make all

if [ $? -ne 0 ]; then
    echo -e "${RED}Compilation failed!${NC}"
    exit 1
fi
echo -e "${GREEN}Compilation successful!${NC}"

# Setup network namespaces once for all experiments
setup_namespaces

# Initialize CSV files with headers (in main directory)
echo "Implementation,MessageSize,ThreadCount,Throughput_Gbps,TotalBytes,TotalMessages,Duration_sec" > "MT25018_Throughput_Metrics.csv"
echo "Implementation,MessageSize,ThreadCount,Latency_us" > "MT25018_Latency_Metrics.csv"
echo "Implementation,MessageSize,ThreadCount,CPU_Cycles,CacheMisses,L1_Misses,LLC_Misses,ContextSwitches" > "MT25018_Perf_Metrics.csv"

echo -e "\n${YELLOW}Starting experiments...${NC}"
echo "This will take approximately $((${#MESSAGE_SIZES[@]} * ${#THREAD_COUNTS[@]} * ${#IMPLEMENTATIONS[@]} * ($TEST_DURATION + 5))) seconds"
echo ""

# Function to extract metric from perf output
extract_perf_metric() {
    local perf_file=$1
    local metric_name=$2
    
    # For hybrid CPUs (cpu_atom/cpu_core), sum both values
    local total=0
    
    # Search for lines containing the metric name
    while IFS= read -r line; do
        # Skip lines that say "not supported"
        if echo "$line" | grep -q "<not supported>"; then
            continue
        fi
        
        # Check if line contains the metric
        if echo "$line" | grep -q "$metric_name"; then
            # Extract the first number (remove commas and whitespace)
            local value=$(echo "$line" | awk '{print $1}' | tr -d ',' | tr -d ' ')
            
            # Add to total if it's a valid number
            if [[ "$value" =~ ^[0-9]+$ ]]; then
                total=$((total + value))
            fi
        fi
    done < "$perf_file"
    
    echo "$total"
}

# Function to run a single experiment
run_experiment() {
    local impl=$1
    local impl_name=$2
    local msg_size=$3
    local thread_count=$4
    
    echo -e "${YELLOW}Running: $impl_name | MsgSize=$msg_size | Threads=$thread_count${NC}"
    
    # Get absolute paths
    local server_bin="$(pwd)/MT25018_Part_${impl}_Server"
    local client_bin="$(pwd)/MT25018_Part_${impl}_Client"
    local perf_output="$(pwd)/$OUTPUT_DIR/perf_${impl_name}_${msg_size}_${thread_count}.txt"
    local client_output="$(pwd)/$OUTPUT_DIR/client_${impl_name}_${msg_size}_${thread_count}.txt"
    
    # Start server with perf in server namespace
    ip netns exec $SERVER_NS perf stat -e "$PERF_EVENTS" -o "$perf_output" \
        "$server_bin" "$msg_size" "$thread_count" > /dev/null 2>&1 &
    local server_pid=$!
    
    # Give server time to start
    sleep 2
    
    # Check if server is running
    if ! kill -0 $server_pid 2>/dev/null; then
        echo -e "${RED}Server failed to start!${NC}"
        return 1
    fi
    
    # Start clients in client namespace
    local client_pids=()
    for ((i=1; i<=thread_count; i++)); do
        ip netns exec $CLIENT_NS "$client_bin" "$SERVER_IP" "$msg_size" "$TEST_DURATION" \
            > "${client_output}_${i}.txt" 2>&1 &
        client_pids+=($!)
    done
    
    # Wait for all clients to complete
    for pid in "${client_pids[@]}"; do
        wait $pid
    done
    
    # Give server time to flush stats
    sleep 2
    
    # Stop server
    kill -SIGTERM $server_pid 2>/dev/null || true
    wait $server_pid 2>/dev/null || true
    
    # Extract application-level metrics from first client
    local throughput=$(grep "Throughput:" "${client_output}_1.txt" | awk '{print $2}')
    local latency=$(grep "Average latency:" "${client_output}_1.txt" | awk '{print $3}')
    local total_bytes=$(grep "Total bytes received:" "${client_output}_1.txt" | awk '{print $4}')
    local total_msgs=$(grep "Total messages received:" "${client_output}_1.txt" | awk '{print $4}')
    local duration=$(grep "Elapsed time:" "${client_output}_1.txt" | awk '{print $3}')
    
    # Handle missing latency (set default)
    if [ -z "$latency" ]; then
        latency="0.0"
    fi
    
    # Extract perf metrics
    local cpu_cycles=$(extract_perf_metric "$perf_output" "cycles")
    local instructions=$(extract_perf_metric "$perf_output" "instructions")
    local cache_misses=$(extract_perf_metric "$perf_output" "cache-misses")
    local l1_misses=$(extract_perf_metric "$perf_output" "L1-dcache-load-misses")
    local llc_misses=$(extract_perf_metric "$perf_output" "LLC-load-misses")
    local ctx_switches=$(extract_perf_metric "$perf_output" "context-switches")
    
    # Write to 3 separate CSV files
    echo "$impl_name,$msg_size,$thread_count,$throughput,$total_bytes,$total_msgs,$duration" \
        >> "MT25018_Throughput_Metrics.csv"
    
    echo "$impl_name,$msg_size,$thread_count,$latency" \
        >> "MT25018_Latency_Metrics.csv"
    
    echo "$impl_name,$msg_size,$thread_count,$cpu_cycles,$cache_misses,$l1_misses,$llc_misses,$ctx_switches" \
        >> "MT25018_Perf_Metrics.csv"
    
    # Display collected metrics
    echo -e "${GREEN}Metrics Collected:${NC}"
    echo "  Application-level:"
    echo "    - Throughput: ${throughput} Gbps"
    echo "    - Latency: ${latency} us"
    echo "  perf stat:"
    echo "    - CPU Cycles: ${cpu_cycles}"
    echo "    - L1 Cache Misses: ${l1_misses}"
    echo "    - LLC Cache Misses: ${llc_misses}"
    echo "    - Context Switches: ${ctx_switches}"
    
    echo -e "${GREEN}[OK] Completed${NC}"
    echo ""
}

# Run all experiments
for impl_idx in "${!IMPLEMENTATIONS[@]}"; do
    impl="${IMPLEMENTATIONS[$impl_idx]}"
    impl_name="${IMPL_NAMES[$impl_idx]}"
    
    echo -e "\n${GREEN}========== Testing $impl_name Implementation ==========${NC}\n"
    
    for msg_size in "${MESSAGE_SIZES[@]}"; do
        for thread_count in "${THREAD_COUNTS[@]}"; do
            run_experiment "$impl" "$impl_name" "$msg_size" "$thread_count"
        done
    done
done

echo -e "\n${GREEN}=========================================="
echo "All experiments completed!"

# Cleanup network namespaces
cleanup_namespaces

echo -e "${GREEN}Network namespaces cleaned up.${NC}"

# Generate plots automatically
echo -e "\n${YELLOW}Generating plots...${NC}"
python3 MT25018_Plot1_Throughput_vs_MessageSize.py
python3 MT25018_Plot2_Latency_vs_ThreadCount.py
python3 MT25018_Plot3_CacheMisses_vs_MessageSize.py
python3 MT25018_Plot4_CyclesPerByte_vs_MessageSize.py

echo -e "\n${GREEN}=========================================="
echo "All plots generated successfully!"
