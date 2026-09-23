"""
OpenPrism-Qt Bland-Altman Method Comparison Engine.

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

Implements Bland-Altman method comparison analysis including bias, SD,
95% limits of agreement (LoA), 95% confidence intervals, and proportional bias testing.
"""

import numpy as np
from scipy import stats


class BlandAltmanEngine:
    """Engine for Bland-Altman method agreement analysis."""

    @staticmethod
    def calculate_bland_altman(
        method1: np.ndarray, method2: np.ndarray, confidence_level: float = 0.95
    ) -> dict:
        """Calculates Bland-Altman agreement metrics between two measurement methods.

        Args:
            method1 (np.ndarray): First measurement vector (X).
            method2 (np.ndarray): Second measurement vector (Y).
            confidence_level (float): Confidence level for CIs (default 0.95).

        Returns:
            dict: Agreement metrics containing bias, SD, 95% limits of agreement, CIs,
                  proportional bias linear regression, and raw difference/mean vectors.
        """
        arr1 = np.asarray(method1, dtype=float)
        arr2 = np.asarray(method2, dtype=float)

        mask = ~np.isnan(arr1) & ~np.isinf(arr1) & ~np.isnan(arr2) & ~np.isinf(arr2)
        arr1 = arr1[mask]
        arr2 = arr2[mask]

        n = len(arr1)
        if n < 3:
            return {
                "success": False,
                "error": "Bland-Altman analysis requires at least 3 paired observations."
            }

        try:
            means = (arr1 + arr2) / 2.0
            diffs = arr1 - arr2  # Difference (Method 1 - Method 2)

            bias = float(np.mean(diffs))
            sd_bias = float(np.std(diffs, ddof=1))
            se_bias = float(sd_bias / np.sqrt(n)) if n > 0 else 0.0

            df = int(n - 1)
            alpha = 1.0 - confidence_level
            t_crit = float(stats.t.ppf(1.0 - alpha / 2.0, df=df)) if df > 0 else 1.96

            bias_ci95 = (float(bias - t_crit * se_bias), float(bias + t_crit * se_bias))

            # 95% Limits of Agreement (LoA)
            z_loa = 1.96
            lower_loa = float(bias - z_loa * sd_bias)
            upper_loa = float(bias + z_loa * sd_bias)

            # Standard error of 95% limits of agreement (Bland & Altman 1999: SE_LoA = s * sqrt(1/n + z^2 / (2(n-1))))
            se_loa = float(sd_bias * np.sqrt(1.0 / n + (z_loa ** 2) / (2.0 * (n - 1)))) if n > 1 else 0.0
            lower_loa_ci95 = (float(lower_loa - t_crit * se_loa), float(lower_loa + t_crit * se_loa))
            upper_loa_ci95 = (float(upper_loa - t_crit * se_loa), float(upper_loa + t_crit * se_loa))

            # Test for proportional bias (Linear regression of diffs vs means)
            lin_res = stats.linregress(means, diffs)
            prop_slope = float(lin_res.slope)
            prop_p_val = float(lin_res.pvalue)

            return {
                "success": True,
                "results": {
                    "n_pairs": n,
                    "bias": bias,
                    "sd_bias": sd_bias,
                    "se_bias": se_bias,
                    "bias_ci95": bias_ci95,
                    "lower_loa": lower_loa,
                    "upper_loa": upper_loa,
                    "lower_loa_ci95": lower_loa_ci95,
                    "upper_loa_ci95": upper_loa_ci95,
                    "proportional_bias": {
                        "slope": prop_slope,
                        "p_value": prop_p_val,
                        "has_proportional_bias": bool(prop_p_val < 0.05)
                    },
                    "means": means.tolist(),
                    "differences": diffs.tolist()
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Bland-Altman calculation failed: {str(e)}"}
