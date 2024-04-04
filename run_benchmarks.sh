#!/bin/bash

# Path to the root directory containing all benchmark folders
BENCHMARKS_ROOT_DIR="misc/tests/benchmarks"

# Get a count of problem files (excluding the domain file)
NUM_PROBLEMS=$(find $BENCHMARKS_ROOT_DIR -type f -name "*.pddl" | grep -v "domain.pddl" | wc -l)
# Initialize progress counter
COUNTER=0

# Iterate over all subdirectories in the benchmarks root directory
for BENCHMARK_DIR in $BENCHMARKS_ROOT_DIR/*; do
    # Check if it's a directory
    if [ -d "$BENCHMARK_DIR" ]; then
        # Domain file name (assumed to be located in the current benchmark folder)
        DOMAIN_FILE="domain.pddl"

        # Output directory for the current benchmark
        OUTPUT_DIR="planner_outputs/$(basename -- $BENCHMARK_DIR)"
        
        # Create the output directory if it doesn't exist
        mkdir -p $OUTPUT_DIR

        # Iterate over all PDDL problem files in the current benchmark directory
        for PROBLEM_FILE in $BENCHMARK_DIR/*.pddl; do
            # Skip the domain file
            if [ "$(basename -- $PROBLEM_FILE)" == "$DOMAIN_FILE" ]; then
                continue
            fi

            # Increment the progress counter
            ((COUNTER++))
            # Run Fast Downward on the current problem
            echo "Processing problem $COUNTER of $NUM_PROBLEMS: $(basename -- $PROBLEM_FILE)"

            python3 fast-downward.py \
                --overall-time-limit 5m \
                $BENCHMARK_DIR/$DOMAIN_FILE $PROBLEM_FILE \
                --evaluator "hff1=ff()" \
                --evaluator "hg=g()" \
                --search "eager(alt([epsilon_greedy(hff1, pref_only=false, epsilon=0.2, random_seed=-1), type_based([hff1,hg], random_seed=-1)], boost=0, decision=2, seed=42, probs=[0.2, 0.8]), preferred=[])" 
                # Equivalent to eager_greedy. See: https://www.fast-downward.org/Doc/SearchAlgorithm#Equivalent_statements_using_general_eager_search-1
                > $OUTPUT_DIR/$(basename -- $PROBLEM_FILE)_out

            mv sas_plan $OUTPUT_DIR/$(basename -- $PROBLEM_FILE)_sas_plan
            break
        done
    fi
    break
done
