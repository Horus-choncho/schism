"""
OpenPrism-Qt Two-Way Analysis of Variance (ANOVA) Engine.

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
"""

import numpy as np
import pandas as pd
import scipy.stats as stats
from typing import Dict, Any


class TwoWayAnovaEngine:
    """Analytical engine for Two-Way Analysis of Variance (ANOVA) with Interaction."""

    @staticmethod
    def calculate_two_way_anova(
        df: pd.DataFrame,
        factor_a_col: str,
        factor_b_col: str,
        value_col: str
    ) -> Dict[str, Any]:
        """Calculates Two-Way ANOVA table for Factor A, Factor B, and Interaction (A x B).

        Attempts to fit an OLS model via statsmodels.api.stats.anova_lm if available,
        falling back seamlessly to explicit sum-of-squares calculation routines.

        Mathematical Formulas:
            Grand Mean: bar{Y} = 1/N * sum(Y_ijk)
            SS_Total = sum((Y_ijk - bar{Y})^2)
            SS_A = sum(n_i * (bar{Y}_i. - bar{Y})^2)
            SS_B = sum(n_j * (bar{Y}_.j - bar{Y})^2)
            SS_Cells = sum(n_ij * (bar{Y}_ij - bar{Y})^2)
            SS_Interaction (A x B) = SS_Cells - SS_A - SS_B
            SS_Residual (Error) = SS_Total - SS_Cells

            F_A = MS_A / MS_Error,  F_B = MS_B / MS_Error,  F_AB = MS_AB / MS_Error

        Args:
            df (pd.DataFrame): Input DataFrame containing observations.
            factor_a_col (str): Column title for Factor A (Row factor).
            factor_b_col (str): Column title for Factor B (Column factor).
            value_col (str): Column title for continuous measurement values.

        Returns:
            Dict[str, Any]: Results payload containing Factor A, Factor B, Interaction,
                Residual Error, and Total degrees of freedom, sum of squares, mean squares,
                F-statistics, and two-tailed p-values.
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
                return {"success": False, "error": "Two-Way ANOVA requires at least 4 valid observations."}

            # Attempt statsmodels.api.stats.anova_lm OLS calculation
            try:
                import statsmodels.api as sm
                from statsmodels.formula.api import ols

                # Build formula replacing special characters for statsmodels formula parser
                clean_formula_df = clean_df.rename(columns={
                    factor_a_col: "FactorA",
                    factor_b_col: "FactorB",
                    value_col: "Value"
                })
                model = ols("Value ~ C(FactorA) * C(FactorB)", data=clean_formula_df).fit()
                anova_table = sm.stats.anova_lm(model, typ=2)

                ss_a = float(anova_table.loc["C(FactorA)", "sum_sq"])
                df_a = int(anova_table.loc["C(FactorA)", "df"])
                f_a = float(anova_table.loc["C(FactorA)", "F"])
                p_a = float(anova_table.loc["C(FactorA)", "PR(>F)"])

                ss_b = float(anova_table.loc["C(FactorB)", "sum_sq"])
                df_b = int(anova_table.loc["C(FactorB)", "df"])
                f_b = float(anova_table.loc["C(FactorB)", "F"])
                p_b = float(anova_table.loc["C(FactorB)", "PR(>F)"])

                ss_ab = float(anova_table.loc["C(FactorA):C(FactorB)", "sum_sq"])
                df_ab = int(anova_table.loc["C(FactorA):C(FactorB)", "df"])
                f_ab = float(anova_table.loc["C(FactorA):C(FactorB)", "F"])
                p_ab = float(anova_table.loc["C(FactorA):C(FactorB)", "PR(>F)"])

                ss_err = float(anova_table.loc["Residual", "sum_sq"])
                df_err = int(anova_table.loc["Residual", "df"])
                ms_err = ss_err / df_err if df_err > 0 else 0.0

                ms_a = ss_a / df_a if df_a > 0 else 0.0
                ms_b = ss_b / df_b if df_b > 0 else 0.0
                ms_ab = ss_ab / df_ab if df_ab > 0 else 0.0

                ss_total = ss_a + ss_b + ss_ab + ss_err
                df_total = df_a + df_b + df_ab + df_err

                return {
                    "success": True,
                    "engine": "statsmodels",
                    "summary": {
                        "n_total": N,
                        "factor_a_name": factor_a_col,
                        "factor_b_name": factor_b_col
                    },
                    "results": {
                        "factor_a": {
                            "name": factor_a_col,
                            "ss": ss_a,
                            "df": df_a,
                            "ms": ms_a,
                            "f_statistic": f_a,
                            "p_value": p_a
                        },
                        "factor_b": {
                            "name": factor_b_col,
                            "ss": ss_b,
                            "df": df_b,
                            "ms": ms_b,
                            "f_statistic": f_b,
                            "p_value": p_b
                        },
                        "interaction": {
                            "name": f"{factor_a_col} x {factor_b_col}",
                            "ss": ss_ab,
                            "df": df_ab,
                            "ms": ms_ab,
                            "f_statistic": f_ab,
                            "p_value": p_ab
                        },
                        "residual": {
                            "ss": ss_err,
                            "df": df_err,
                            "ms": ms_err
                        },
                        "total": {
                            "ss": ss_total,
                            "df": df_total
                        }
                    }
                }
            except Exception:
                # Fallback to pure SciPy / NumPy sum of squares matrix calculations
                pass

            # SciPy / NumPy direct sum of squares calculation
            grand_mean = float(clean_df[value_col].mean())
            ss_total = float(((clean_df[value_col] - grand_mean) ** 2).sum())
            df_total = N - 1

            a_means = clean_df.groupby(factor_a_col)[value_col].mean()
            a_counts = clean_df.groupby(factor_a_col)[value_col].count()
            ss_a = float((a_counts * ((a_means - grand_mean) ** 2)).sum())
            df_a = len(a_means) - 1

            b_means = clean_df.groupby(factor_b_col)[value_col].mean()
            b_counts = clean_df.groupby(factor_b_col)[value_col].count()
            ss_b = float((b_counts * ((b_means - grand_mean) ** 2)).sum())
            df_b = len(b_means) - 1

            ab_means = clean_df.groupby([factor_a_col, factor_b_col])[value_col].mean()
            ab_counts = clean_df.groupby([factor_a_col, factor_b_col])[value_col].count()

            ss_cells = 0.0
            for (fa, fb), cell_mean in ab_means.items():
                c_cnt = ab_counts[(fa, fb)]
                ss_cells += float(c_cnt * ((cell_mean - grand_mean) ** 2))

            ss_ab = float(ss_cells - ss_a - ss_b)
            df_ab = df_a * df_b

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
                "engine": "scipy_fallback",
                "summary": {
                    "n_total": N,
                    "factor_a_name": factor_a_col,
                    "factor_b_name": factor_b_col
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
            return {"success": False, "error": f"Two-Way ANOVA calculation failed: {str(exc)}"}
