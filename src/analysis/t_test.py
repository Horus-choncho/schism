"""
OpenPrism-Qt Comparative Hypotheses Engine (t-Tests & Nonparametric Tests).

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

Implements Student's t-test, Welch's t-test, Paired t-test, and Mann-Whitney U test
according to GraphPad Prism 10 standards.
"""

import math
import numpy as np
from scipy import stats


class TTestEngine:
    """Comparative hypothesis testing engine for two-group experimental designs."""

    @staticmethod
    def calculate_unpaired_t_test(group_a: np.ndarray, group_b: np.ndarray, equal_var: bool = True) -> dict:
        """Computes an independent unpaired t-test between two numeric experiment samples.

        Supports both Student's t-test (assuming equal variance, homoscedasticity)
        and Welch's t-test (assuming unequal variance, heteroscedasticity).

        Mathematical Formulas:
            Equal Variance (Student's t-test):
                Pooled Variance:
                    s_p^2 = ((n_A - 1)s_A^2 + (n_B - 1)s_B^2) / df
                Degrees of Freedom:
                    df = n_A + n_B - 2
                Standard Error of Difference:
                    SE_{diff} = sqrt(s_p^2 * (1/n_A + 1/n_B))

            Unequal Variance (Welch's t-test):
                Welch-Satterthwaite Degrees of Freedom:
                    df = (s_A^2/n_A + s_B^2/n_B)^2 / ((s_A^2/n_A)^2 / (n_A - 1) + (s_B^2/n_B)^2 / (n_B - 1))
                Standard Error of Difference:
                    SE_{diff} = sqrt(s_A^2/n_A + s_B^2/n_B)

            95% Confidence Interval of Mean Difference:
                CI = (mean_A - mean_B) +/- t_{critical, 0.975, df} * SE_{diff}

        Args:
            group_a (np.ndarray): Numeric observations for Group A.
            group_b (np.ndarray): Numeric observations for Group B.
            equal_var (bool, optional): If True, compute Student's t-test. If False, compute Welch's t-test.
                Defaults to True.

        Returns:
            dict: Summary dictionary containing:
                - 'success' (bool): True if computation succeeded.
                - 'summary' (dict): Sample statistics (mean, std, n) for each group.
                - 'results' (dict): Calculated t_statistic, p_value, degrees_of_freedom,
                  mean_difference, standard_error_difference, and 95% confidence_interval tuple.
        """
        arr_a = np.asarray(group_a, dtype=float)
        arr_b = np.asarray(group_b, dtype=float)
        # Filter out NaN and Infinite entries to ensure clean finite vector analysis
        arr_a = arr_a[~np.isnan(arr_a) & ~np.isinf(arr_a)]
        arr_b = arr_b[~np.isnan(arr_b) & ~np.isinf(arr_b)]

        if arr_a.size < 2 or arr_b.size < 2:
            return {"success": False, "error": "Each treatment group must contain at least 2 observations."}

        try:
            mean_a, mean_b = float(np.mean(arr_a)), float(np.mean(arr_b))
            # Sample standard deviation computed with Bessel's correction (ddof=1)
            std_a, std_b = float(np.std(arr_a, ddof=1)), float(np.std(arr_b, ddof=1))
            n_a, n_b = int(len(arr_a)), int(len(arr_b))

            mean_difference = mean_a - mean_b

            # SciPy independent t-test computation
            t_stat, p_val = stats.ttest_ind(arr_a, arr_b, equal_var=equal_var)

            if equal_var:
                # Student's t-test: Degrees of freedom = N_A + N_B - 2
                df = float(n_a + n_b - 2)
                # Pooled sample variance combining variance estimates weighted by degrees of freedom
                pooled_var = ((n_a - 1) * (std_a ** 2) + (n_b - 1) * (std_b ** 2)) / df
                se_diff = float(np.sqrt(pooled_var * (1.0 / n_a + 1.0 / n_b)))
            else:
                # Welch's t-test: Welch-Satterthwaite equation for effective degrees of freedom
                se_a_sq = (std_a ** 2) / n_a
                se_b_sq = (std_b ** 2) / n_b
                df = float(((se_a_sq + se_b_sq) ** 2) / (
                    (se_a_sq ** 2 / (n_a - 1)) + (se_b_sq ** 2 / (n_b - 1))
                ))
                se_diff = float(np.sqrt(se_a_sq + se_b_sq))

            # 95% Two-sided confidence interval calculation using Student's t-distribution quantile
            t_critical = float(stats.t.ppf(0.975, df))
            margin_of_error = t_critical * se_diff
            ci_lower = mean_difference - margin_of_error
            ci_upper = mean_difference + margin_of_error

            return {
                "success": True,
                "summary": {
                    "group_a": {"mean": mean_a, "std": std_a, "n": n_a},
                    "group_b": {"mean": mean_b, "std": std_b, "n": n_b}
                },
                "results": {
                    "t_statistic": float(t_stat),
                    "p_value": float(p_val),
                    "degrees_of_freedom": float(df),
                    "mean_difference": float(mean_difference),
                    "standard_error_difference": float(se_diff),
                    "confidence_interval": (float(ci_lower), float(ci_upper))
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Statistical computation failed: {str(e)}"}

    @staticmethod
    def calculate_welch_t_test(group_a: np.ndarray, group_b: np.ndarray) -> dict:
        """Computes Welch's t-test (independent sample t-test assuming unequal variance).

        Args:
            group_a (np.ndarray): Numeric observations for Group A.
            group_b (np.ndarray): Numeric observations for Group B.

        Returns:
            dict: Summary dictionary containing Welch's t-test metrics.
        """
        return TTestEngine.calculate_unpaired_t_test(group_a, group_b, equal_var=False)

    @staticmethod
    def calculate_paired_t_test(group_a: np.ndarray, group_b: np.ndarray) -> dict:
        """Computes a paired sample t-test for matched experimental observations.

        Mathematical Formulas:
            Pair Differences:
                D_i = A_i - B_i
            Mean Difference:
                mean(D) = 1/N * sum(D_i)
            Sample Standard Deviation of Differences (ddof=1):
                s_D = sqrt(1/(N-1) * sum((D_i - mean(D))^2))
            Standard Error of Mean Difference:
                SEM_D = s_D / sqrt(N)
            Degrees of Freedom:
                df = N - 1

        Args:
            group_a (np.ndarray): First vector of paired observations.
            group_b (np.ndarray): Second vector of paired observations.

        Returns:
            dict: Summary dictionary containing paired t-test results.
        """
        arr_a = np.asarray(group_a, dtype=float)
        arr_b = np.asarray(group_b, dtype=float)
        # Pairwise complete-case filtering (listwise deletion of missing pairs)
        mask = ~np.isnan(arr_a) & ~np.isinf(arr_a) & ~np.isnan(arr_b) & ~np.isinf(arr_b)
        arr_a = arr_a[mask]
        arr_b = arr_b[mask]

        n = len(arr_a)
        if n < 2:
            return {"success": False, "error": "Paired t-test requires at least 2 complete observation pairs."}

        try:
            # Pairwise differences vector
            diffs = arr_a - arr_b
            mean_diff = float(np.mean(diffs))
            std_diff = float(np.std(diffs, ddof=1))
            sem_diff = float(std_diff / math.sqrt(n))

            t_stat, p_val = stats.ttest_rel(arr_a, arr_b)
            df = float(n - 1)

            # 95% Confidence Interval for mean difference
            t_crit = float(stats.t.ppf(0.975, df))
            margin = t_crit * sem_diff
            ci_lower = mean_diff - margin
            ci_upper = mean_diff + margin

            return {
                "success": True,
                "summary": {
                    "group_a": {"mean": float(np.mean(arr_a)), "std": float(np.std(arr_a, ddof=1)), "n": n},
                    "group_b": {"mean": float(np.mean(arr_b)), "std": float(np.std(arr_b, ddof=1)), "n": n}
                },
                "results": {
                    "t_statistic": float(t_stat),
                    "p_value": float(p_val),
                    "degrees_of_freedom": float(df),
                    "mean_difference": mean_diff,
                    "std_difference": std_diff,
                    "sem_difference": sem_diff,
                    "confidence_interval": (float(ci_lower), float(ci_upper))
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Paired t-test computation failed: {str(e)}"}

    @staticmethod
    def calculate_mann_whitney_u_test(group_a: np.ndarray, group_b: np.ndarray) -> dict:
        """Computes the non-parametric Mann-Whitney U test (Wilcoxon rank-sum test).

        Used when data distributions do not follow a normal (Gaussian) distribution.
        Evaluates whether ranks of values in group_a differ systematically from group_b.

        Args:
            group_a (np.ndarray): Numeric observations for Group A.
            group_b (np.ndarray): Numeric observations for Group B.

        Returns:
            dict: Summary dictionary containing Mann-Whitney U statistic and asymptotic p-value.
        """
        arr_a = np.asarray(group_a, dtype=float)
        arr_b = np.asarray(group_b, dtype=float)
        arr_a = arr_a[~np.isnan(arr_a) & ~np.isinf(arr_a)]
        arr_b = arr_b[~np.isnan(arr_b) & ~np.isinf(arr_b)]

        n_a, n_b = len(arr_a), len(arr_b)
        if n_a < 1 or n_b < 1:
            return {"success": False, "error": "Each group must contain at least 1 observation for Mann-Whitney U test."}

        try:
            # Two-sided rank-sum non-parametric test
            u_stat, p_val = stats.mannwhitneyu(arr_a, arr_b, alternative="two-sided")
            median_a, median_b = float(np.median(arr_a)), float(np.median(arr_b))
            median_diff = median_a - median_b

            return {
                "success": True,
                "summary": {
                    "group_a": {"median": median_a, "n": n_a},
                    "group_b": {"median": median_b, "n": n_b}
                },
                "results": {
                    "u_statistic": float(u_stat),
                    "p_value": float(p_val),
                    "median_difference": float(median_diff)
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Mann-Whitney U test failed: {str(e)}"}
