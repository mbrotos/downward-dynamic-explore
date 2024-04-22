#!/bin/bash
PROBLEM_FILE=$1
WORKING_DIR=$(dirname "$0")
BENCHMARK_DIR=$(dirname "$PROBLEM_FILE")
DOMAIN_FILE="$BENCHMARK_DIR/domain.pddl"
OUTPUT_DIR="planner_outputs/$(basename -- $BENCHMARK_DIR)"
mkdir -p $OUTPUT_DIR

# Create a unique temporary directory for this instance
TMP_DIR=$(mktemp -d)
echo "Processing in temporary directory: $TMP_DIR"

# Ensure cleanup of temporary directory on exit
trap 'rm -rf "$TMP_DIR"' EXIT

# Copy domain and problem files to temporary directory
cp "$DOMAIN_FILE" "$TMP_DIR"
cp "$PROBLEM_FILE" "$TMP_DIR"

# Change to temporary directory
pushd "$TMP_DIR"

# Run the planner
echo "Processing: $(basename -- $PROBLEM_FILE)"
python3 $WORKING_DIR/fast-downward.py \
    --overall-time-limit 5m \
    $(basename -- $DOMAIN_FILE) $(basename -- $PROBLEM_FILE) \
    --evaluator "hff1=ff()" \
    --evaluator "hg=g()" \
    --search "eager(alt([epsilon_greedy(hff1, pref_only=false, epsilon=1.0, random_seed=-1), type_based([hff1,hg], random_seed=-1)], boost=0, decision=2, seed=42, probs=[0.5, 0.5]), preferred=[])" \
    > $(basename -- $PROBLEM_FILE)_out

# Check if sas_plan exists before moving it
if [ -f sas_plan ]; then
    mv sas_plan $WORKING_DIR/$OUTPUT_DIR/$(basename -- $PROBLEM_FILE)_sas_plan
fi

# Move output file to permanent directory
mv $(basename -- $PROBLEM_FILE)_out $WORKING_DIR/$OUTPUT_DIR

# Return to original directory and remove temporary one
popd


# Run Setup:
# find path_to_benchmarks/misc/tests/benchmarks -type f -name "*.pddl" | grep -v "domain.pddl" > problem_files.txt

# Run:
# cat problem_files.txt | parallel --bar ./process_problem.sh {}