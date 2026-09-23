"""
OpenPrism-Qt One-Sample Hypothesis Engine (One-Sample t-Test & Wilcoxon Signed-Rank Test).

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

Implements One-Sample t-test and Wilcoxon signed-rank test against a hypothetical mean
according to GraphPad Prism 10 standards.
"""

import math
import numpy as np
from scipy import stats


class OneSampleTestEngine:
    """Hypothesis testing engine for single-sample comparative experimental designs."""

    @staticmethod
    def calculate_one_sample_test(sample_data: np.ndarray, mu_0: float = 0.0) -> dict:
        """Computes a One-Sample t-test and Wilcoxon signed-rank test against a reference mean.

        Mathematical Formulas:
            One-Sample t-Test:
                Sample Mean:
                    mean = 1/N * sum(y_i)
                Sample Standard Deviation (ddof=1):
                    s = sqrt(1/(N-1) * sum((y_i - mean)^2))
                Standard Error of Mean:
                    SEM = s / sqrt(N)
                t-Statistic:
                    t = (mean - mu_0) / SEM
                Degrees of Freedom:
                    df = N - 1
                95% Confidence Interval for Mean Difference:
                    CI = (mean - mu_0) +/- t_{critical, 0.975, df} * SEM

            Wilcoxon Signed-Rank Test:
                Differences:
                    D_i = y_i - mu_0
                Signed-Rank Statistic (W):
                    Sum of ranks of positive differences D_i > 0

        Args:
            sample_data (np.ndarray): Numeric observation sample vector.
            mu_0 (float, optional): Hypothetical reference value. Defaults to 0.0.

        Returns:
            dict: Summary dictionary containing:
                - 'success' (bool): True if computation succeeded.
                - 'summary' (dict): Sample size (n), mean, std, sem, median, and hypothetical value.
                - 'parametric' (dict): Calculated t_statistic, degrees_of_freedom, p_value,
                  mean_difference, sem_difference, and 95% ci95_difference tuple.
                - 'nonparametric' (dict): Calculated w_statistic, p_value, and median_difference.
        """
        arr = np.asarray(sample_data, dtype=float)
        # Filter out NaN and Infinite entries
        arr = arr[~np.isnan(arr) & ~np.isinf(arr)]

        n = len(arr)
        if n < 2:
            return {
                "success": False,
                "error": "One-sample hypothesis test requires at least 2 valid observations."
            }

        try:
            mean_y = float(np.mean(arr))
            std_y = float(np.std(arr, ddof=1))
            sem_y = float(std_y / math.sqrt(n))
            median_y = float(np.median(arr))
            mean_diff = mean_y - float(mu_0)
            median_diff = median_y - float(mu_0)

            # --- 1. One-Sample t-Test ---
            t_res = stats.ttest_1samp(arr, popmean=mu_0)
            df = float(n - 1)

            t_crit = float(stats.t.ppf(0.975, df))
            margin = t_crit * sem_y
            ci_lower = mean_diff - margin
            ci_upper = mean_diff + margin

            parametric_results = {
                "t_statistic": float(t_res.statistic),
                "degrees_of_freedom": df,
                "p_value": float(t_res.pvalue),
                "mean_difference": float(mean_diff),
                "sem_difference": float(sem_y),
                "ci95_difference": (float(ci_lower), float(ci_upper))
            }

            # --- 2. Wilcoxon Signed-Rank Test ---
            diffs = arr - float(mu_0)
            if np.all(diffs == 0):
                # Edge case: All observations are exactly equal to mu_0
                nonparametric_results = {
                    "w_statistic": 0.0,
                    "p_value": 1.0,
                    "median_difference": 0.0
                }
            else:
                try:
                    w_res = stats.wilcoxon(diffs, zero_method="pratt", correction=True)
                    nonparametric_results = {
                        "w_statistic": float(w_res.statistic),
                        "p_value": float(w_res.pvalue),
                        "median_difference": float(median_diff)
                    }
                except Exception:
                    # Fallback if zero differences leave no ranks
                    nonparametric_results = {
                        "w_statistic": 0.0,
                        "p_value": 1.0,
                        "median_difference": float(median_diff)
                    }

            return {
                "success": True,
                "summary": {
                    "n": int(n),
                    "mean": mean_y,
                    "std": std_y,
                    "sem": sem_y,
                    "median": median_y,
                    "hypothetical_value": float(mu_0)
                },
                "parametric": parametric_results,
                "nonparametric": nonparametric_results
            }
        except Exception as e:
            return {"success": False, "error": f"One-sample hypothesis test failed: {str(e)}"}
