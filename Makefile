# MT25018
# Graduate Systems PA02 - Makefile
# Compiles all client/server implementations

CC = gcc
CFLAGS = -Wall -Wextra -pthread -O2
LDFLAGS = -pthread

# Target executables
A1_SERVER = MT25018_Part_A1_Server
A1_CLIENT = MT25018_Part_A1_Client
A2_SERVER = MT25018_Part_A2_Server
A2_CLIENT = MT25018_Part_A2_Client
A3_SERVER = MT25018_Part_A3_Server
A3_CLIENT = MT25018_Part_A3_Client

# All targets
ALL_TARGETS = $(A1_SERVER) $(A1_CLIENT) $(A2_SERVER) $(A2_CLIENT) $(A3_SERVER) $(A3_CLIENT)

# Default target - build all
all: $(ALL_TARGETS)
	@echo "=== Build Complete ==="
	@echo "Built all client/server implementations"

# Part A1: Two-Copy Implementation
A1: $(A1_SERVER) $(A1_CLIENT)
	@echo "Built Part A1 (Two-Copy)"

$(A1_SERVER): MT25018_Part_A1_Server.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

$(A1_CLIENT): MT25018_Part_A1_Client.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

# Part A2: One-Copy Implementation
A2: $(A2_SERVER) $(A2_CLIENT)
	@echo "Built Part A2 (One-Copy)"

$(A2_SERVER): MT25018_Part_A2_Server.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

$(A2_CLIENT): MT25018_Part_A2_Client.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

# Part A3: Zero-Copy Implementation
A3: $(A3_SERVER) $(A3_CLIENT)
	@echo "Built Part A3 (Zero-Copy)"

$(A3_SERVER): MT25018_Part_A3_Server.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

$(A3_CLIENT): MT25018_Part_A3_Client.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

# Clean all binaries
clean:
	rm -f $(ALL_TARGETS)
	rm -f *.o
	@echo "Cleaned all binaries"

# Clean data files and results
clean-data:
	rm -f MT25018_Part_C_*.csv
	rm -rf experiment_results plots
	@echo "Cleaned all data files and results"

# Clean everything
clean-all: clean clean-data
	@echo "Cleaned everything"

# Help target
help:
	@echo "MT25018 Graduate Systems PA02 - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  all        - Build all implementations (default)"
	@echo "  A1         - Build Part A1 (Two-Copy) only"
	@echo "  A2         - Build Part A2 (One-Copy) only"
	@echo "  A3         - Build Part A3 (Zero-Copy) only"
	@echo "  clean      - Remove all binaries"
	@echo "  clean-data - Remove CSV files and result directories"
	@echo "  clean-all  - Remove everything (binaries + data)"
	@echo "  help       - Show this help message"

.PHONY: all A1 A2 A3 clean clean-data clean-all help
