import pandas as pd
import os
import re
import argparse

arg_parser = argparse.ArgumentParser(description="Parse plan log files")
arg_parser.add_argument("--log_dir", help="Directory containing plan log files")
arg_parser.add_argument("--output_path", help="Directory to save parsed data")
arg_parser.add_argument("--planner", help="Planner used to generate the plan log files")

# See: https://www.fast-downward.org/ExitCodes
search_status = {
    -1.0: None,
    0: "SUCCESS",
    1: "SEARCH_PLAN_FOUND_AND_OUT_OF_MEMORY",
    2: "SEARCH_PLAN_FOUND_AND_OUT_OF_TIME",
    3: "SEARCH_PLAN_FOUND_AND_OUT_OF_MEMORY_AND_TIME",
    10: "TRANSLATE_UNSOLVABLE",
    11: "SEARCH_UNSOLVABLE",
    12: "SEARCH_UNSOLVED_INCOMPLETE",
    20: "TRANSLATE_OUT_OF_MEMORY",
    21: "TRANSLATE_OUT_OF_TIME",
    22: "SEARCH_OUT_OF_MEMORY",
    23: "SEARCH_OUT_OF_TIME",
    24: "SEARCH_OUT_OF_MEMORY_AND_TIME",
    30: "TRANSLATE_CRITICAL_ERROR",
    31: "TRANSLATE_INPUT_ERROR",
    32: "SEARCH_CRITICAL_ERROR",
    33: "SEARCH_INPUT_ERROR",
    34: "SEARCH_UNSUPPORTED",
    35: "DRIVER_CRITICAL_ERROR",
    36: "DRIVER_INPUT_ERROR",
    37: "DRIVER_UNSUPPORTED",
}

headers = [
    "domain",
    "problem",
    "planner",
    "planner_time",
    "peak_memory",
    "plan_cost",
    "plan_length",
    "status",
    "exit_code",
    "evaluations",
]


def extractStats(pddl_out_path, domain, problem, planner):
    to_float = lambda x, g=1: -1.0 if x is None else float(x.group(g))
    to_int = lambda x, g=1: -1 if x is None else int(x.group(g))
    time, memory, cost, length, status, exit_code = [None] * 6

    with open(pddl_out_path) as f:
        planner_log = f.read()
        time = to_float(re.search(r"Planner time: (\d+\.\d+)s", planner_log))
        memory = to_int(re.search(r"\nPeak memory: (\d+)", planner_log))
        cost = to_float(re.search(r"Plan cost: (\d+\.?\d*)", planner_log))
        length = to_int(re.search(r"Plan length: (\d+)", planner_log))
        exit_code = to_int(re.search(r"search exit code: (\d+)", planner_log))
        status = search_status[exit_code]
        evaluations = to_int(re.search(r"Evaluations: (\d+)", planner_log))

    return [domain, problem, planner, time, memory, cost, length, status, exit_code, evaluations]


def main():
    args = arg_parser.parse_args()
    plan_out_path = os.path.abspath(args.log_dir)
    data = []
    planner = args.planner
    for folder in os.listdir(plan_out_path):
        if not os.path.isdir(os.path.join(plan_out_path, folder)):
            continue
        for file in os.listdir(os.path.join(plan_out_path, folder)):
            if file.endswith(".pddl_out"):
                file_path = os.path.join(plan_out_path, folder, file)
                stats = extractStats(file_path, folder, file, planner)
                data.append(stats)

    df = pd.DataFrame(data, columns=headers)
    df.to_csv(args.output_path, index=False)
    print("Parsed plan log saved to:", args.output_path)
    print(df.info())


if __name__ == "__main__":
    main()

# Run the script with the following commands:

"""
python parse_plan_log.py --log_dir planner_outputs_baseline --output_path ./planner_outputs_baseline.csv --planner baseline
python parse_plan_log.py --log_dir planner_outputs_default --output_path ./planner_outputs_default.csv --planner default
python parse_plan_log.py --log_dir planner_outputs_random --output_path ./planner_outputs_random.csv --planner random
python parse_plan_log.py --log_dir planner_outputs_stateinfo --output_path ./planner_outputs_stateinfo.csv --planner stateinfo
"""