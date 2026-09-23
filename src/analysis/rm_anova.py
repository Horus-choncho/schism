"""
OpenPrism-Qt Repeated Measures ANOVA Engine.

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

Implements One-Way Repeated Measures (RM) ANOVA with Geisser-Greenhouse sphericity
correction matching GraphPad Prism 10 standards.
"""

from typing import Union, List, Dict
import numpy as np
import pandas as pd
from scipy import stats


class RepeatedMeasuresAnovaEngine:
    """Engine for One-Way Repeated Measures (RM) ANOVA."""

    @staticmethod
    def calculate_rm_anova(
        data: Union[pd.DataFrame, np.ndarray, List[np.ndarray], Dict[str, np.ndarray]],
        subject_col: str = None,
        condition_col: str = None,
        value_col: str = None
    ) -> dict:
        """Computes Repeated Measures ANOVA across multiple paired conditions/time points.

        Supports both wide format (rows = subjects, cols = conditions) and long format
        (DataFrame with subject_col, condition_col, value_col).

        Args:
            data: Wide format DataFrame/array/dict or long format DataFrame.
            subject_col (str, optional): Subject identifier column for long format.
            condition_col (str, optional): Treatment/Time condition column for long format.
            value_col (str, optional): Measurement value column for long format.

        Returns:
            dict: Summary table containing Sum of Squares, degrees of freedom, Mean Squares,
                  F-statistic, p-value, Geisser-Greenhouse epsilon, and adjusted p-value.
        """
        try:
            # Format parsing into matrix (N subjects x K conditions)
            matrix = None
            condition_names = []

            if isinstance(data, pd.DataFrame) and subject_col and condition_col and value_col:
                # Long format -> pivot to wide
                pivoted = data.pivot(index=subject_col, columns=condition_col, values=value_col)
                pivoted = pivoted.dropna(axis=0, how="any")
                condition_names = [str(c) for c in pivoted.columns]
                matrix = pivoted.to_numpy(dtype=float)

            elif isinstance(data, pd.DataFrame):
                # Wide format DataFrame
                df_clean = data.dropna(axis=0, how="any")
                # Filter non-numeric columns
                numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) < 2:
                    return {"success": False, "error": "RM-ANOVA requires at least 2 numeric condition columns."}
                condition_names = [str(c) for c in numeric_cols]
                matrix = df_clean[numeric_cols].to_numpy(dtype=float)

            elif isinstance(data, dict):
                names = list(data.keys())
                arrs = [np.asarray(data[k], dtype=float) for k in names]
                # Filter complete cases across columns
                min_len = min(len(a) for a in arrs)
                stack = np.column_stack([a[:min_len] for a in arrs])
                mask = ~np.isnan(stack).any(axis=1) & ~np.isinf(stack).any(axis=1)
                matrix = stack[mask]
                condition_names = [str(k) for k in names]

            elif isinstance(data, (np.ndarray, list)):
                mat = np.asarray(data, dtype=float)
                if mat.ndim == 2:
                    mask = ~np.isnan(mat).any(axis=1) & ~np.isinf(mat).any(axis=1)
                    matrix = mat[mask]
                    condition_names = [f"Condition {j+1}" for j in range(matrix.shape[1])]

            if matrix is None or matrix.size == 0 or matrix.ndim != 2:
                return {"success": False, "error": "Invalid or empty input matrix for RM-ANOVA."}

            n_subjects, n_conditions = matrix.shape
            if n_subjects < 2:
                return {"success": False, "error": "RM-ANOVA requires at least 2 subjects with complete data across all conditions."}
            if n_conditions < 2:
                return {"success": False, "error": "RM-ANOVA requires at least 2 repeated conditions/time points."}

            # Calculations
            grand_mean = float(np.mean(matrix))
            subject_means = np.mean(matrix, axis=1)
            condition_means = np.mean(matrix, axis=0)

            # Sum of Squares
            ss_total = float(np.sum((matrix - grand_mean) ** 2))
            ss_subject = float(n_conditions * np.sum((subject_means - grand_mean) ** 2))
            ss_within = float(ss_total - ss_subject)
            ss_treatment = float(n_subjects * np.sum((condition_means - grand_mean) ** 2))
            ss_error = float(max(0.0, ss_within - ss_treatment))

            # Degrees of Freedom
            df_total = n_subjects * n_conditions - 1
            df_subject = n_subjects - 1
            df_treatment = n_conditions - 1
            df_error = (n_subjects - 1) * (n_conditions - 1)

            ms_treatment = float(ss_treatment / df_treatment) if df_treatment > 0 else 0.0
            ms_error = float(ss_error / df_error) if df_error > 0 else 0.0
            ms_subject = float(ss_subject / df_subject) if df_subject > 0 else 0.0

            f_stat = float(ms_treatment / ms_error) if ms_error > 0 else 0.0
            p_val = float(stats.f.sf(f_stat, df_treatment, df_error)) if df_error > 0 else 1.0

            # Geisser-Greenhouse Sphericity Correction
            cov_matrix = np.cov(matrix, rowvar=False)
            if cov_matrix.ndim == 2 and cov_matrix.shape[0] > 1:
                cov_mean = np.mean(cov_matrix)
                row_means = np.mean(cov_matrix, axis=1)
                diag_mean = np.mean(np.diag(cov_matrix))

                num = (n_conditions * (diag_mean - cov_mean)) ** 2
                den_term1 = np.sum(cov_matrix ** 2)
                den_term2 = 2.0 * n_conditions * np.sum(row_means ** 2)
                den_term3 = (n_conditions ** 2) * (cov_mean ** 2)
                den = (n_conditions - 1) * (den_term1 - den_term2 + den_term3)

                gg_eps = float(num / den) if den > 0 else 1.0
                gg_eps = float(min(1.0, max(1.0 / (n_conditions - 1), gg_eps)))
            else:
                gg_eps = 1.0

            df_treat_gg = df_treatment * gg_eps
            df_err_gg = df_error * gg_eps
            p_val_gg = float(stats.f.sf(f_stat, df_treat_gg, df_err_gg)) if df_err_gg > 0 else p_val

            return {
                "success": True,
                "results": {
                    "treatment": {
                        "ss": ss_treatment,
                        "df": df_treatment,
                        "ms": ms_treatment,
                        "f_statistic": f_stat,
                        "p_value": p_val,
                        "geisser_greenhouse_epsilon": gg_eps,
                        "p_value_gg": p_val_gg
                    },
                    "subject": {
                        "ss": ss_subject,
                        "df": df_subject,
                        "ms": ms_subject
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
                    "n_subjects": n_subjects,
                    "n_conditions": n_conditions,
                    "condition_names": condition_names
                }
            }
        except Exception as e:
            return {"success": False, "error": f"RM-ANOVA calculation failed: {str(e)}"}
