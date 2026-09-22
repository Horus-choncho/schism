"""
OpenPrism-Qt Analysis of Variance (ANOVA) Engine.
Licensed under GPLv3.

Implements One-Way ANOVA, Two-Way ANOVA, and Tukey's HSD post-hoc multiple
comparison maps following GraphPad Prism 10 standards.
"""

import math
import numpy as np
import pandas as pd
import scipy.stats as stats
from typing import Dict, Union, List


class AnovaEngine:
    """
    Analysis of Variance (ANOVA) and Post-Hoc Comparison Engine.
    """

    @staticmethod
    def calculate_one_way_anova(groups_dict: Dict[str, Union[list, np.ndarray]]) -> dict:
        """
        Calculates One-Way Analysis of Variance (ANOVA) and Tukey's HSD post-hoc tests.

        Args:
            groups_dict: Dict mapping group name (str) -> 1D numeric array/list.

        Returns:
            Dict containing ANOVA statistics (F, P, DFs, SS, MS) and post-hoc pairwise comparisons.
        """
        if not isinstance(groups_dict, dict) or len(groups_dict) < 2:
            return {
                "success": False,
                "error": "One-Way ANOVA requires at least 2 comparison groups."
            }

        cleaned_groups = {}
        group_names = []
        arrays = []

        for name, data in groups_dict.items():
            arr = np.asarray(data, dtype=float)
            arr = arr[~np.isnan(arr) & ~np.isinf(arr)]
            if len(arr) < 1:
                continue
            cleaned_groups[name] = arr
            group_names.append(str(name))
            arrays.append(arr)

        num_groups = len(arrays)
        if num_groups < 2:
            return {
                "success": False,
                "error": "At least 2 non-empty groups are required for One-Way ANOVA."
            }

        try:
            # 1. Overall One-Way ANOVA F-test
            f_stat, p_val = stats.f_oneway(*arrays)

            # 2. Explicit Sum of Squares & Degrees of Freedom
            all_vals = np.concatenate(arrays)
            n_total = len(all_vals)
            grand_mean = float(np.mean(all_vals))

            ss_total = float(np.sum((all_vals - grand_mean) ** 2))
            df_total = int(n_total - 1)

            ss_between = 0.0
            for arr in arrays:
                group_mean = float(np.mean(arr))
                ss_between += len(arr) * ((group_mean - grand_mean) ** 2)

            df_between = int(num_groups - 1)
            ss_within = float(ss_total - ss_between)
            df_within = int(n_total - num_groups)

            ms_between = ss_between / df_between if df_between > 0 else 0.0
            ms_within = ss_within / df_within if df_within > 0 else 0.0

            # 3. Post-hoc Tukey HSD Pairwise Comparisons
            post_hoc_results = []
            if num_groups >= 2 and all(len(a) >= 1 for a in arrays):
                try:
                    tukey_res = stats.tukey_hsd(*arrays)
                    ci_obj = tukey_res.confidence_interval(confidence_level=0.95)
                    for i in range(num_groups):
                        for j in range(i + 1, num_groups):
                            stat = float(tukey_res.statistic[i, j])
                            p_tukey = float(tukey_res.pvalue[i, j])
                            ci_low = float(ci_obj.low[i, j])
                            ci_high = float(ci_obj.high[i, j])
                            post_hoc_results.append({
                                "group1": group_names[i],
                                "group2": group_names[j],
                                "mean_difference": stat,
                                "p_value": p_tukey,
                                "confidence_interval": (ci_low, ci_high),
                                "significant": bool(p_tukey < 0.05)
                            })
                except Exception:
                    pass

            return {
                "success": True,
                "summary": {
                    "num_groups": num_groups,
                    "n_total": n_total,
                    "group_means": {name: float(np.mean(arr)) for name, arr in cleaned_groups.items()}
                },
                "results": {
                    "f_statistic": float(f_stat),
                    "p_value": float(p_val),
                    "df_between": df_between,
                    "df_within": df_within,
                    "df_total": df_total,
                    "ss_between": float(ss_between),
                    "ss_within": float(ss_within),
                    "ss_total": float(ss_total),
                    "ms_between": float(ms_between),
                    "ms_within": float(ms_within),
                    "post_hoc_tukey": post_hoc_results
                }
            }
        except Exception as exc:
            return {
                "success": False,
                "error": f"One-Way ANOVA computation failed: {str(exc)}"
            }

    @staticmethod
    def calculate_two_way_anova(
        df: pd.DataFrame,
        factor_a_col: str,
        factor_b_col: str,
        value_col: str
    ) -> dict:
        """
        Calculates Two-Way Analysis of Variance (Two-Way ANOVA) with Interaction.

        Args:
            df: DataFrame containing the data.
            factor_a_col: Column name for Factor A (row factor).
            factor_b_col: Column name for Factor B (column factor).
            value_col: Column name for measurement values.

        Returns:
            Dict containing Two-Way ANOVA table metrics for Factor A, Factor B, Interaction, and Residual Error.
        """
        if not isinstance(df, pd.DataFrame) or df.empty:
            return {"success": False, "error": "Input DataFrame is empty."}

        for col in [factor_a_col, factor_b_col, value_col]:
            if col not in df.columns:
                return {"success": False, "error": f"Missing required column '{col}' in DataFrame."}

        try:
            clean_df = df[[factor_a_col, factor_b_col, value_col]].dropna().copy()
            clean_df[value_col] = pd.to_numeric(clean_df[value_col], errors="coerce")
            clean_df = clean_df.dropna()

            N = len(clean_df)
            if N < 4:
                return {"success": False, "error": "Two-Way ANOVA requires at least 4 observations."}

            grand_mean = float(clean_df[value_col].mean())
            ss_total = float(((clean_df[value_col] - grand_mean) ** 2).sum())
            df_total = N - 1

            # Factor A
            a_means = clean_df.groupby(factor_a_col)[value_col].mean()
            a_counts = clean_df.groupby(factor_a_col)[value_col].count()
            ss_a = float((a_counts * ((a_means - grand_mean) ** 2)).sum())
            df_a = len(a_means) - 1

            # Factor B
            b_means = clean_df.groupby(factor_b_col)[value_col].mean()
            b_counts = clean_df.groupby(factor_b_col)[value_col].count()
            ss_b = float((b_counts * ((b_means - grand_mean) ** 2)).sum())
            df_b = len(b_means) - 1

            # Cells (Interaction)
            ab_means = clean_df.groupby([factor_a_col, factor_b_col])[value_col].mean()
            ab_counts = clean_df.groupby([factor_a_col, factor_b_col])[value_col].count()

            ss_cells = 0.0
            for (fa, fb), cell_mean in ab_means.items():
                c_cnt = ab_counts[(fa, fb)]
                ss_cells += float(c_cnt * ((cell_mean - grand_mean) ** 2))

            ss_ab = float(ss_cells - ss_a - ss_b)
            df_ab = df_a * df_b

            # Residual Error
            ss_error = float(ss_total - ss_cells)
            df_error = N - len(ab_means)

            if df_a <= 0 or df_b <= 0 or df_error <= 0:
                return {"success": False, "error": "Insufficient degrees of freedom for Two-Way ANOVA."}

            ms_a = ss_a / df_a
            ms_b = ss_b / df_b
            ms_ab = ss_ab / df_ab if df_ab > 0 else 0.0
            ms_error = ss_error / df_error

            f_a = ms_a / ms_error
            f_b = ms_b / ms_error
            f_ab = ms_ab / ms_error if df_ab > 0 else 0.0

            p_a = float(stats.f.sf(f_a, df_a, df_error))
            p_b = float(stats.f.sf(f_b, df_b, df_error))
            p_ab = float(stats.f.sf(f_ab, df_ab, df_error)) if df_ab > 0 else 1.0

            return {
                "success": True,
                "summary": {
                    "n_total": N,
                    "factor_a_levels": list(a_means.index),
                    "factor_b_levels": list(b_means.index)
                },
                "results": {
                    "factor_a": {
                        "name": factor_a_col,
                        "ss": ss_a,
                        "df": df_a,
                        "ms": ms_a,
                        "f_statistic": float(f_a),
                        "p_value": p_a
                    },
                    "factor_b": {
                        "name": factor_b_col,
                        "ss": ss_b,
                        "df": df_b,
                        "ms": ms_b,
                        "f_statistic": float(f_b),
                        "p_value": p_b
                    },
                    "interaction": {
                        "name": f"{factor_a_col} x {factor_b_col}",
                        "ss": ss_ab,
                        "df": df_ab,
                        "ms": ms_ab,
                        "f_statistic": float(f_ab),
                        "p_value": p_ab
                    },
                    "residual": {
                        "ss": ss_error,
                        "df": df_error,
                        "ms": ms_error
                    },
                    "total": {
                        "ss": ss_total,
                        "df": df_total
                    }
                }
            }
        except Exception as exc:
            return {
                "success": False,
                "error": f"Two-Way ANOVA computation failed: {str(exc)}"
            }
