# %%
import pandas as pd

# %%
df_default = pd.read_csv('planner_outputs/default/planner_outputs_default.csv')
df_weighted = pd.read_csv('planner_outputs/weighted/planner_outputs_weighted.csv')
df_fullrand = pd.read_csv('planner_outputs/fullrand/planner_outputs_fullrand.csv')

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
            )
            if metric == "total_solved"
            else min(
                row[f"{metric}_default"],
                row[f"{metric}_fullrand"],
                row[f"{metric}_weighted"],
            )
        )
        for strategy in ["default", "fullrand", "weighted"]:
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
    caption = ("Comparative analysis of alternation strategies across different domains with FF Heuristic. "
               "The table presents aggregated statistics for problems solved using Default, Fully Random, "
               "and Weighted Random (80:20 ratio between hg-Type-Based and Epsilon Greedy open lists) alternation strategies. Metrics include total problems solved, average evaluations, "
               "average plan length, and average plan cost. The best performance in each metric is highlighted in bold.")
    
    latex_str = df.to_latex(index=False, column_format='lrrrrrrrrrrrr', escape=False,
                            columns=['domain', 'total_solved_default', 'avg_evaluations_default', 'avg_plan_length_default', 'avg_plan_cost_default',
                                     'total_solved_fullrand', 'avg_evaluations_fullrand', 'avg_plan_length_fullrand', 'avg_plan_cost_fullrand',
                                     'total_solved_weighted', 'avg_evaluations_weighted', 'avg_plan_length_weighted', 'avg_plan_cost_weighted'],
                            header=['Domain', 'Solved', 'Evaluations', 'Plan Length', 'Plan Cost',
                                    'Solved', 'Evaluations', 'Plan Length', 'Plan Cost',
                                    'Solved', 'Evaluations', 'Plan Length', 'Plan Cost'],
                            multirow=True, multicolumn=True,
                            multicolumn_format='c|', caption=caption, label='tab:planner_table')
    
    # Custom adjustments for the table to fit the requested format
    latex_str = latex_str.replace('\\begin{table}\n', "\\begin{table}[ht]\n\\centering\n\\footnotesize\n")
    latex_str = latex_str.replace('\\toprule', '\\hline')
    latex_str = latex_str.replace('\\midrule', '\\hline')
    latex_str = latex_str.replace('\\bottomrule', '\\hline')
    
    # Adding multicolumn labels for strategies
    strategy_labels = "\\hline\n\\multicolumn{1}{|c|}{} & \\multicolumn{4}{|c|}{Default} & \\multicolumn{4}{|c|}{Fully Random} & \\multicolumn{4}{|c|}{Weighted Random}\\\\ \\cline{2-13}\n"
    latex_str = latex_str.replace("\\begin{tabular}{lrrrrrrrrrrrr}", "\\begin{tabular}{|l|rrrr|rrrr|rrrr|}\n" + strategy_labels)
    return latex_str

# Generate LaTeX table
latex_table = generate_latex_table(highlighted_df)

# Save LaTeX table to file
with open('planner_outputs/planner_table.tex', 'w') as f:
    f.write(latex_table)


# %%



