"""
OpenPrism-Qt Contingency Table Analysis Engine (Chi-Square & Fisher's Exact Tests).

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

Implements Pearson's Chi-Square Test, Yates' Continuity Correction, and Fisher's Exact Test
with Woolf's 95% Confidence Interval for Odds Ratios according to GraphPad Prism 10 standards.
"""

import math
import numpy as np
from scipy import stats


class ContingencyEngine:
    """Statistical analysis engine for contingency table counts (categorical independence)."""

    @staticmethod
    def calculate_contingency_analysis(observed_matrix: np.ndarray) -> dict:
        """Computes Pearson's Chi-square test, Yates' correction, and Fisher's exact test.

        Mathematical Formulas:
            Expected Frequencies (E_ij):
                E_ij = (Row_i_Sum * Col_j_Sum) / N_total

            Pearson's Chi-Square Test:
                chi^2 = sum_i sum_j ((O_ij - E_ij)^2 / E_ij)
                df = (R - 1) * (C - 1)

            Yates' Continuity Correction (2x2 tables):
                chi^2_yates = sum_i sum_j ((|O_ij - E_ij| - 0.5)^2 / E_ij)

            Fisher's Exact Test (2x2 tables):
                Hypergeometric exact probability p for matrix [[a, b], [c, d]]
                Odds Ratio (OR) = (a * d) / (b * c)
                Woolf 95% Confidence Interval for OR:
                    SE(ln(OR)) = sqrt(1/a + 1/b + 1/c + 1/d)  (Haldane-Anscombe +0.5 correction if 0 cell)
                    CI = exp(ln(OR) +/- 1.96 * SE(ln(OR)))

        Args:
            observed_matrix (np.ndarray or list[list[int]]): 2D contingency matrix of non-negative cell counts.

        Returns:
            dict: Summary dictionary containing:
                - 'success' (bool): True if computation succeeded.
                - 'contingency_table' (list[list[int]]): Original observed cell matrix.
                - 'expected_table' (list[list[float]]): Calculated expected frequencies matrix.
                - 'chi_square' (dict): Uncorrected and Yates-corrected chi-square statistics and p-values.
                - 'fisher_exact' (dict, optional): Fisher's exact test odds ratio, p-value, and 95% CI (for 2x2).
        """
        try:
            obs = np.asarray(observed_matrix, dtype=float)
        except Exception as e:
            return {"success": False, "error": f"Invalid contingency matrix format: {str(e)}"}

        if obs.ndim != 2:
            return {"success": False, "error": "Contingency table must be a 2-dimensional matrix."}

        rows, cols = obs.shape
        if rows < 2 or cols < 2:
            return {"success": False, "error": "Contingency table must have at least 2 rows and 2 columns."}

        if np.any(np.isnan(obs)) or np.any(np.isinf(obs)) or np.any(obs < 0):
            return {"success": False, "error": "Contingency table cells must contain finite, non-negative numbers."}

        total_observations = float(np.sum(obs))
        if total_observations <= 0:
            return {"success": False, "error": "Contingency table grand total must be greater than zero."}

        try:
            # --- 1. Pearson's Chi-Square Test (Uncorrected) ---
            chi2_uncorrected, p_uncorrected, df, expected = stats.chi2_contingency(obs, correction=False)

            is_2x2 = (rows == 2 and cols == 2)
            yates_stat = None
            yates_p = None
            fisher_results = None

            if is_2x2:
                # --- 2. Yates' Continuity Correction ---
                yates_stat_val, yates_p_val, _, _ = stats.chi2_contingency(obs, correction=True)
                yates_stat = float(yates_stat_val)
                yates_p = float(yates_p_val)

                # --- 3. Fisher's Exact Test & Odds Ratio ---
                int_obs = obs.astype(int)
                fisher_res = stats.fisher_exact(int_obs, alternative="two-sided")
                fisher_p = float(fisher_res.pvalue)

                a, b = float(obs[0, 0]), float(obs[0, 1])
                c, d = float(obs[1, 0]), float(obs[1, 1])

                if b * c != 0:
                    or_point = (a * d) / (b * c)
                else:
                    or_point = float("inf") if (a * d) > 0 else 0.0

                # Woolf 95% Confidence Interval with Haldane-Anscombe zero-cell adjustment
                if a == 0 or b == 0 or c == 0 or d == 0:
                    a_adj, b_adj, c_adj, d_adj = a + 0.5, b + 0.5, c + 0.5, d + 0.5
                    or_calc = (a_adj * d_adj) / (b_adj * c_adj)
                    se_ln_or = math.sqrt(1.0 / a_adj + 1.0 / b_adj + 1.0 / c_adj + 1.0 / d_adj)
                else:
                    or_calc = or_point
                    se_ln_or = math.sqrt(1.0 / a + 1.0 / b + 1.0 / c + 1.0 / d)

                if or_calc > 0 and not math.isinf(or_calc):
                    ln_or = math.log(or_calc)
                    or_ci_lower = float(math.exp(ln_or - 1.96 * se_ln_or))
                    or_ci_upper = float(math.exp(ln_or + 1.96 * se_ln_or))
                else:
                    or_ci_lower, or_ci_upper = 0.0, float("inf")

                fisher_results = {
                    "odds_ratio": float(or_point),
                    "p_value": fisher_p,
                    "odds_ratio_ci95": (or_ci_lower, or_ci_upper)
                }

            return {
                "success": True,
                "contingency_table": obs.astype(int).tolist(),
                "expected_table": expected.tolist(),
                "chi_square": {
                    "statistic": float(chi2_uncorrected),
                    "p_value": float(p_uncorrected),
                    "degrees_of_freedom": int(df),
                    "yates_corrected_stat": yates_stat,
                    "yates_p_value": yates_p
                },
                "fisher_exact": fisher_results
            }
        except Exception as e:
            return {"success": False, "error": f"Contingency table analysis failed: {str(e)}"}
