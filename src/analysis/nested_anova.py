"""
OpenPrism-Qt Nested One-Way ANOVA Engine.

Copyright (C) 2026 OpenPrism-Qt Team
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Implements Hierarchical Nested One-Way ANOVA (Group -> Subgroup -> Replicate)
matching GraphPad Prism 10 standards.
"""

from typing import Union, List, Dict
import numpy as np
import pandas as pd
from scipy import stats


class NestedAnovaEngine:
    """Engine for Hierarchical Nested One-Way ANOVA analysis."""

    @staticmethod
    def calculate_nested_anova(
        df: pd.DataFrame,
        group_col: str,
        subgroup_col: str,
        value_col: str
    ) -> dict:
        """Computes hierarchical Nested One-Way ANOVA model.

        Evaluates top-level Group effect against Subgroup variance, and Subgroup
        nested effect against Residual Error variance.

        Args:
            df (pd.DataFrame): Input dataframe containing hierarchical data.
            group_col (str): Column name for top-level main group factor.
            subgroup_col (str): Column name for subgroup factor nested within group.
            value_col (str): Column name for numerical response variable.

        Returns:
            dict: Summary table containing SS, df, MS, F-statistics, and p-values.
        """
        if df is None or df.empty:
            return {"success": False, "error": "Input DataFrame is empty or invalid."}

        for col in [group_col, subgroup_col, value_col]:
            if col not in df.columns:
                return {"success": False, "error": f"Column '{col}' not found in DataFrame."}

        clean_df = df[[group_col, subgroup_col, value_col]].dropna().copy()
        clean_df[value_col] = pd.to_numeric(clean_df[value_col], errors="coerce")
        clean_df = clean_df.dropna(subset=[value_col])

        N = len(clean_df)
        if N < 4:
            return {"success": False, "error": "Nested ANOVA requires at least 4 valid observation replicates."}

        groups = clean_df[group_col].unique()
        a = len(groups)
        if a < 2:
            return {"success": False, "error": "Nested ANOVA requires at least 2 top-level groups."}

        try:
            grand_mean = float(clean_df[value_col].mean())

            # Group means & counts
            group_means = clean_df.groupby(group_col)[value_col].mean().to_dict()
            group_counts = clean_df.groupby(group_col)[value_col].count().to_dict()

            # Subgroup means & counts
            subgroup_means = clean_df.groupby([group_col, subgroup_col])[value_col].mean().to_dict()
            subgroup_counts = clean_df.groupby([group_col, subgroup_col])[value_col].count().to_dict()

            total_subgroups = len(subgroup_means)

            # 1. Total SS
            ss_total = float(np.sum((clean_df[value_col].to_numpy() - grand_mean) ** 2))
            df_total = N - 1

            # 2. Group SS
            ss_group = 0.0
            for g_name, g_mean in group_means.items():
                n_g = group_counts[g_name]
                ss_group += n_g * ((g_mean - grand_mean) ** 2)
            ss_group = float(ss_group)
            df_group = a - 1

            # 3. Subgroup nested in Group SS
            ss_subgroup = 0.0
            for (g_name, sub_name), sub_mean in subgroup_means.items():
                g_mean = group_means[g_name]
                n_sub = subgroup_counts[(g_name, sub_name)]
                ss_subgroup += n_sub * ((sub_mean - g_mean) ** 2)
            ss_subgroup = float(ss_subgroup)
            df_subgroup = total_subgroups - a

            # 4. Error SS
            ss_error = 0.0
            for idx, row in clean_df.iterrows():
                g_val = row[group_col]
                sub_val = row[subgroup_col]
                y_val = row[value_col]
                sub_mean = subgroup_means[(g_val, sub_val)]
                ss_error += (y_val - sub_mean) ** 2
            ss_error = float(ss_error)
            df_error = N - total_subgroups

            if df_group <= 0 or df_subgroup <= 0 or df_error <= 0:
                return {"success": False, "error": "Insufficient degrees of freedom for nested ANOVA levels."}

            # Mean Squares
            ms_group = float(ss_group / df_group)
            ms_subgroup = float(ss_subgroup / df_subgroup)
            ms_error = float(ss_error / df_error)

            # Group F-test (Group MS vs Subgroup MS)
            f_group = float(ms_group / ms_subgroup) if ms_subgroup > 0 else 0.0
            p_group = float(stats.f.sf(f_group, df_group, df_subgroup))

            # Subgroup F-test (Subgroup MS vs Error MS)
            f_subgroup = float(ms_subgroup / ms_error) if ms_error > 0 else 0.0
            p_subgroup = float(stats.f.sf(f_subgroup, df_subgroup, df_error))

            return {
                "success": True,
                "results": {
                    "group": {
                        "ss": ss_group,
                        "df": df_group,
                        "ms": ms_group,
                        "f_statistic": f_group,
                        "p_value": p_group
                    },
                    "subgroup_nested": {
                        "ss": ss_subgroup,
                        "df": df_subgroup,
                        "ms": ms_subgroup,
                        "f_statistic": f_subgroup,
                        "p_value": p_subgroup
                    },
                    "error": {
                        "ss": ss_error,
                        "df": df_error,
                        "ms": ms_error
                    },
                    "total": {
                        "ss": ss_total,
                        "df": df_total
                    },
                    "n_groups": a,
                    "n_subgroups": total_subgroups,
                    "n_observations": N
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Nested ANOVA calculation failed: {str(e)}"}
