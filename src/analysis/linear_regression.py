"""
OpenPrism-Qt Linear Regression & Linearity Analysis Engine.

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

Implements Simple Linear Regression with 95% Confidence Intervals
and Wald-Wolfowitz Runs Test for Linearity matching GraphPad Prism 10 standards.
"""

import math
import numpy as np
from scipy import stats


class LinearRegressionEngine:
    """Engine for performing simple linear regression and departure-from-linearity testing."""

    @staticmethod
    def calculate_linear_regression(x_data: np.ndarray, y_data: np.ndarray) -> dict:
        """Computes simple linear regression (Y = slope * X + intercept) between X and Y.

        Calculates slope, intercept, standard errors, 95% confidence intervals,
        goodness-of-fit (R-squared), residual variance, and the Wald-Wolfowitz
        runs test to evaluate departure from linearity.

        Args:
            x_data (np.ndarray): Independent variable observations.
            y_data (np.ndarray): Dependent variable observations.

        Returns:
            dict: Summary dictionary containing:
                - 'success' (bool): True if computation succeeded.
                - 'results' (dict): Slope, intercept, SEs, 95% CIs, R^2, r, p-value,
                  residual std error, degrees of freedom, and runs test metrics.
        """
        arr_x = np.asarray(x_data, dtype=float)
        arr_y = np.asarray(y_data, dtype=float)

        # Pairwise complete-case filtering
        mask = ~np.isnan(arr_x) & ~np.isinf(arr_x) & ~np.isnan(arr_y) & ~np.isinf(arr_y)
        arr_x = arr_x[mask]
        arr_y = arr_y[mask]

        n = len(arr_x)
        if n < 3:
            return {
                "success": False,
                "error": "Linear regression requires at least 3 valid observation pairs."
            }

        try:
            lin = stats.linregress(arr_x, arr_y)
            slope = float(lin.slope)
            intercept = float(lin.intercept)
            r_value = float(lin.rvalue)
            p_value = float(lin.pvalue)
            slope_se = float(lin.stderr)
            intercept_se = float(lin.intercept_stderr)

            df = int(n - 2)
            r_squared = float(r_value ** 2)

            # Compute residual standard error s_{y|x}
            y_pred = slope * arr_x + intercept
            residuals = arr_y - y_pred
            ss_res = float(np.sum(residuals ** 2))
            std_err_estimate = float(np.sqrt(ss_res / df)) if df > 0 else 0.0

            # 95% Confidence Intervals for Slope and Intercept using Student's t distribution
            t_crit = float(stats.t.ppf(0.975, df)) if df > 0 else 0.0
            slope_ci95 = (float(slope - t_crit * slope_se), float(slope + t_crit * slope_se))
            intercept_ci95 = (float(intercept - t_crit * intercept_se), float(intercept + t_crit * intercept_se))

            # Wald-Wolfowitz Runs Test for Linearity
            runs_results = LinearRegressionEngine._calculate_runs_test(residuals)

            return {
                "success": True,
                "results": {
                    "slope": slope,
                    "intercept": intercept,
                    "slope_se": slope_se,
                    "intercept_se": intercept_se,
                    "slope_ci95": slope_ci95,
                    "intercept_ci95": intercept_ci95,
                    "r_squared": r_squared,
                    "r_value": r_value,
                    "p_value": p_value,
                    "std_err_estimate": std_err_estimate,
                    "degrees_of_freedom": df,
                    "n_observations": n,
                    "runs_test": runs_results
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Linear regression calculation failed: {str(e)}"}

    @staticmethod
    def _calculate_runs_test(residuals: np.ndarray) -> dict:
        """Computes the Wald-Wolfowitz runs test on regression residuals.

        Tests whether residuals systematically deviate from linearity by examining
        the number of runs of positive and negative residuals.

        Args:
            residuals (np.ndarray): Vector of regression residuals (Y_observed - Y_fitted).

        Returns:
            dict: Runs test statistics including runs count, expected runs, Z statistic,
                  p-value, and a boolean flag `is_linear` (p >= 0.05).
        """
        # Dichotomize non-zero residuals into +1 and -1
        signs = np.sign(residuals)
        signs = signs[signs != 0]

        if len(signs) < 2:
            return {
                "runs_count": 0,
                "n_positive": int(np.sum(residuals > 0)),
                "n_negative": int(np.sum(residuals < 0)),
                "expected_runs": 0.0,
                "z_statistic": 0.0,
                "p_value": 1.0,
                "is_linear": True
            }

        n1 = int(np.sum(signs > 0))  # Positive residual count
        n2 = int(np.sum(signs < 0))  # Negative residual count
        n_total = n1 + n2

        if n1 == 0 or n2 == 0:
            return {
                "runs_count": 1,
                "n_positive": n1,
                "n_negative": n2,
                "expected_runs": 1.0,
                "z_statistic": 0.0,
                "p_value": 1.0,
                "is_linear": True
            }

        # Count runs (contiguous blocks of same sign)
        runs_count = int(np.sum(signs[:-1] != signs[1:]) + 1)

        # Expected runs and variance under null hypothesis
        exp_runs = float(1.0 + (2.0 * n1 * n2) / n_total)
        var_runs_num = 2.0 * n1 * n2 * (2.0 * n1 * n2 - n_total)
        var_runs_den = (n_total ** 2) * (n_total - 1)
        var_runs = float(var_runs_num / var_runs_den) if var_runs_den > 0 else 0.0

        if var_runs > 0:
            # Standard normal approximation with continuity correction
            dev = runs_count - exp_runs
            z_stat = float(dev / np.sqrt(var_runs))
            p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_stat))))
        else:
            z_stat = 0.0
            p_val = 1.0

        return {
            "runs_count": runs_count,
            "n_positive": n1,
            "n_negative": n2,
            "expected_runs": exp_runs,
            "z_statistic": z_stat,
            "p_value": p_val,
            "is_linear": bool(p_val >= 0.05)
        }
