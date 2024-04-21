# %%
import pandas as pd

# %%
df_baseline = pd.read_csv('planner_outputs_baseline.csv')
df_default = pd.read_csv('planner_outputs_first/default/planner_outputs_default.csv')
df_fullrand = pd.read_csv('planner_outputs_first/fullrand/planner_outputs_fullrand.csv')
df_weighted = pd.read_csv('planner_outputs_stateinfo.csv')

# %%
# Aggregate metrics by domain for each strategy


# Helper function to aggregate metrics
def aggregate_metrics(df):
    # We filter by 'SUCCESS' status to consider only solved problems
    df_success = df[df["status"] == "SUCCESS"]
    aggregated = (
        df_success.groupby("domain")
        .agg(
            total_solved=("problem", "count"),
            avg_evaluations=("evaluations", "mean"),
            avg_plan_length=("plan_length", "mean"),
            avg_plan_cost=("plan_cost", "mean"),
        )
        .reset_index()
    )
    return aggregated


# Aggregate metrics for each strategy
aggregated_weighted = aggregate_metrics(df_weighted)
aggregated_default = aggregate_metrics(df_default)
aggregated_fullrand = aggregate_metrics(df_fullrand)
aggregate_baseline = aggregate_metrics(df_baseline)

# Merge the aggregated metrics into a single DataFrame
# This involves some complex merging and renaming to prepare for the LaTeX table
merged_df = aggregated_default.merge(
    aggregated_fullrand, on="domain", suffixes=("_default", "_fullrand")
)
merged_df = merged_df.merge(aggregated_weighted, on="domain")
merged_df.rename(
    columns={
        "total_solved": "total_solved_weighted",
        "avg_evaluations": "avg_evaluations_weighted",
        "avg_plan_length": "avg_plan_length_weighted",
        "avg_plan_cost": "avg_plan_cost_weighted",
    },
    inplace=True,
)
merged_df = merged_df.merge(aggregate_baseline, on="domain")
merged_df.rename(
    columns={
        "total_solved": "total_solved_baseline",
        "avg_evaluations": "avg_evaluations_baseline",
        "avg_plan_length": "avg_plan_length_baseline",
        "avg_plan_cost": "avg_plan_cost_baseline",
    },
    inplace=True,
)

# Calculate the total row
total_row = pd.DataFrame(
    {
        "domain": ["Total"],
        "total_solved_default": [merged_df["total_solved_default"].sum()],
        "avg_evaluations_default": [merged_df["avg_evaluations_default"].mean()],
        "avg_plan_length_default": [merged_df["avg_plan_length_default"].mean()],
        "avg_plan_cost_default": [merged_df["avg_plan_cost_default"].mean()],
        "total_solved_fullrand": [merged_df["total_solved_fullrand"].sum()],
        "avg_evaluations_fullrand": [merged_df["avg_evaluations_fullrand"].mean()],
        "avg_plan_length_fullrand": [merged_df["avg_plan_length_fullrand"].mean()],
        "avg_plan_cost_fullrand": [merged_df["avg_plan_cost_fullrand"].mean()],
        "total_solved_weighted": [merged_df["total_solved_weighted"].sum()],
        "avg_evaluations_weighted": [merged_df["avg_evaluations_weighted"].mean()],
        "avg_plan_length_weighted": [merged_df["avg_plan_length_weighted"].mean()],
        "avg_plan_cost_weighted": [merged_df["avg_plan_cost_weighted"].mean()],
        "total_solved_baseline": [merged_df["total_solved_baseline"].sum()],
        "avg_evaluations_baseline": [merged_df["avg_evaluations_baseline"].mean()],
        "avg_plan_length_baseline": [merged_df["avg_plan_length_baseline"].mean()],
        "avg_plan_cost_baseline": [merged_df["avg_plan_cost_baseline"].mean()],
    }
)

# Append the total row to the merged_df
merged_with_total = pd.concat([merged_df, total_row], ignore_index=True)


# Highlight the best performance in each metric (bold)
def highlight_best_performance(row, metrics):
    for metric in metrics:
        best_value = (
            max(
                row[f"{metric}_default"],
                row[f"{metric}_fullrand"],
                row[f"{metric}_weighted"],
                row[f"{metric}_baseline"],
            )
            if metric == "total_solved"
            else min(
                row[f"{metric}_default"],
                row[f"{metric}_fullrand"],
                row[f"{metric}_weighted"],
                row[f"{metric}_baseline"],
            )
        )
        for strategy in ["default", "fullrand", "weighted", "baseline"]:
            if row[f"{metric}_{strategy}"] == best_value:
                row[f"{metric}_{strategy}"] = f"\\textbf{{{best_value:.2f}}}"
            else:
                row[f"{metric}_{strategy}"] = f'{row[f"{metric}_{strategy}"]:.2f}'
    return row


# Metrics to highlight
metrics_to_highlight = [
    "total_solved",
    "avg_evaluations",
    "avg_plan_length",
    "avg_plan_cost",
]

# Apply highlighting
highlighted_df = merged_with_total.apply(
    lambda row: highlight_best_performance(row, metrics_to_highlight), axis=1
)

highlighted_df.head()

# %%
# Function to generate LaTeX table from the DataFrame
def generate_latex_table(df):

    # Generate mapping of domain names to ints, make sure its sorted
    domain_mapping = {domain: str(i) if not domain=='Total' else 'Total' for i, domain in enumerate(df["domain"].unique())}
    domain_num_mapping = {'recharging-robots-opt23-adl': 20,
        'freecell': 80,
        'miconic-fulladl': 151,
        'parking-opt11-strips': 20,
        'labyrinth-opt23-adl': 20,
        'logistics00': 28,
        'nomystery-opt11-strips': 20,
        'blocks': 35,
        'visitall-opt14-strips': 20,
        'parking-opt14-strips': 20,
        'Total': 414
    }
    
    # latex table for mapping domain names, their integer representation and the number of problems in each domain
    domain_mapping_table = pd.DataFrame.from_dict(domain_mapping, orient='index', columns=['Integer']).reset_index()
    domain_mapping_table['Domain'] = domain_mapping_table['index']
    domain_mapping_table['Problems'] = domain_mapping_table['Domain'].map(domain_num_mapping)
    # cast problems to int
    domain_mapping_table['Problems'] = domain_mapping_table['Problems'].astype(int)
    domain_mapping_table = domain_mapping_table[['Domain', 'Integer', 'Problems']].to_latex(index=False, column_format='llr', escape=False,
                            header=['Domain', 'Index', 'Problems'], 
                            caption='Mapping of domain names to integers and number of problems in each domain', 
                            label='tab:domain_mapping_table')
    
    # Custom adjustments for the table to fit the requested format
    domain_mapping_table = domain_mapping_table.replace('\\begin{table}\n', "\\begin{table}[H]\n\\centering\n\\footnotesize\n")
    domain_mapping_table = domain_mapping_table.replace('\\toprule', '\\hline')
    domain_mapping_table = domain_mapping_table.replace('\\midrule', '\\hline')
    domain_mapping_table = domain_mapping_table.replace('\\bottomrule', '\\hline')

    # Save domain mapping table to file
    with open('domain_mapping_table.tex', 'w') as f:
        f.write(domain_mapping_table)

    # Replace domain names with integers
    df["domain"] = df["domain"].map(domain_mapping)

    # Latex table for number of problems solved by each strategy
    caption = ("Number of problems solved by each strategy for each domain. "
                "The table lists the number of problems solved by each strategy for each domain, "
                "as well as the total number of problems solved by each strategy.")
    latex_str = df.to_latex(index=False, column_format='lrrrrrrrrrrrr', escape=False,
                            columns=['domain', 'total_solved_baseline', 'total_solved_default', 'total_solved_fullrand', 'total_solved_weighted'],
                            header=['Domain', 'Baseline', 'Default', 'Random', 'W-Random'],
                            caption=caption, label='tab:solved_table')
    
    # Custom adjustments for the table to fit the requested format
    latex_str = latex_str.replace('\\begin{table}\n', "\\begin{table}[H]\n\\centering\n\\footnotesize\n")
    latex_str = latex_str.replace('\\toprule', '\\hline')
    latex_str = latex_str.replace('\\midrule', '\\hline')
    latex_str = latex_str.replace('\\bottomrule', '\\hline')

    # Adding multicolumn labels for strategies
    strategy_labels = "\\hline\n\\multicolumn{1}{|c|}{} & \\multicolumn{4}{|c|}{Solved}\\\\ \\cline{2-5}\n"
    latex_str = latex_str.replace("\\begin{tabular}{lrrrrrrrrrrrr}", "\\begin{tabular}{|l|rrrr|}\n" + strategy_labels)
    
    with open('solved_table.tex', 'w') as f:
        f.write(latex_str)
    
    # Latex table for number of evaluations by each strategy
    caption = ("Number of evaluations by each strategy for each domain. "
                "The table lists the average number of evaluations by each strategy for each domain, "
                "as well as the total average number of evaluations by each strategy.")
    latex_str = df.to_latex(index=False, column_format='lrrrrrrrrrrrr', escape=False,
                            columns=['domain', 'avg_evaluations_baseline', 'avg_evaluations_default', 'avg_evaluations_fullrand', 'avg_evaluations_weighted'],
                            header=['Domain', 'Baseline', 'Default', 'Random', 'W-Random'],
                            caption=caption, label='tab:evaluations_table')
    
    # Custom adjustments for the table to fit the requested format
    latex_str = latex_str.replace('\\begin{table}\n', "\\begin{table}[H]\n\\centering\n\\footnotesize\n")
    latex_str = latex_str.replace('\\toprule', '\\hline')
    latex_str = latex_str.replace('\\midrule', '\\hline')
    latex_str = latex_str.replace('\\bottomrule', '\\hline')

    # Adding multicolumn labels for strategies
    strategy_labels = "\\hline\n\\multicolumn{1}{|c|}{} & \\multicolumn{4}{|c|}{Evaluations}\\\\ \\cline{2-5}\n"
    latex_str = latex_str.replace("\\begin{tabular}{lrrrrrrrrrrrr}", "\\begin{tabular}{|l|rrrr|}\n" + strategy_labels)

    with open('evaluations_table.tex', 'w') as f:
        f.write(latex_str)

    # Latex table for plan length by each strategy
    caption = ("Average plan length by each strategy for each domain. "
                "The table lists the average plan length by each strategy for each domain, "
                "as well as the total average plan length by each strategy.")
    latex_str = df.to_latex(index=False, column_format='lrrrrrrrrrrrr', escape=False,
                            columns=['domain', 'avg_plan_length_baseline', 'avg_plan_length_default', 'avg_plan_length_fullrand', 'avg_plan_length_weighted'],
                            header=['Domain', 'Baseline', 'Default', 'Random', 'W-Random'],
                            caption=caption, label='tab:plan_length_table')
    
    # Custom adjustments for the table to fit the requested format
    latex_str = latex_str.replace('\\begin{table}\n', "\\begin{table}[H]\n\\centering\n\\footnotesize\n")
    latex_str = latex_str.replace('\\toprule', '\\hline')
    latex_str = latex_str.replace('\\midrule', '\\hline')
    latex_str = latex_str.replace('\\bottomrule', '\\hline')

    # Adding multicolumn labels for strategies
    strategy_labels = "\\hline\n\\multicolumn{1}{|c|}{} & \\multicolumn{4}{|c|}{Plan Length}\\\\ \\cline{2-5}\n"
    latex_str = latex_str.replace("\\begin{tabular}{lrrrrrrrrrrrr}", "\\begin{tabular}{|l|rrrr|}\n" + strategy_labels)

    with open('plan_length_table.tex', 'w') as f:
        f.write(latex_str)

    # Latex table for plan cost by each strategy
    caption = ("Average plan cost by each strategy for each domain. "
                "The table lists the average plan cost by each strategy for each domain, "
                "as well as the total average plan cost by each strategy.")
    latex_str = df.to_latex(index=False, column_format='lrrrrrrrrrrrr', escape=False,
                            columns=['domain', 'avg_plan_cost_baseline', 'avg_plan_cost_default', 'avg_plan_cost_fullrand', 'avg_plan_cost_weighted'],
                            header=['Domain', 'Baseline', 'Default', 'Random', 'W-Random'],
                            caption=caption, label='tab:plan_cost_table')
    
    # Custom adjustments for the table to fit the requested format
    latex_str = latex_str.replace('\\begin{table}\n', "\\begin{table}[H]\n\\centering\n\\footnotesize\n")
    latex_str = latex_str.replace('\\toprule', '\\hline')
    latex_str = latex_str.replace('\\midrule', '\\hline')
    latex_str = latex_str.replace('\\bottomrule', '\\hline')
    
    # Adding multicolumn labels for strategies
    strategy_labels = "\\hline\n\\multicolumn{1}{|c|}{} & \\multicolumn{4}{|c|}{Plan Cost}\\\\ \\cline{2-5}\n"
    latex_str = latex_str.replace("\\begin{tabular}{lrrrrrrrrrrrr}", "\\begin{tabular}{|l|rrrr|}\n" + strategy_labels)

    with open('plan_cost_table.tex', 'w') as f:
        f.write(latex_str)

# # Generate LaTeX table
latex_table = generate_latex_table(highlighted_df)

# # Save LaTeX table to file
# with open('planner_outputs/planner_table.tex', 'w') as f:
#     f.write(latex_table)


# %%



