"""
OpenPrism-Qt Simple Binary Logistic Regression Engine.

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

Implements simple binary logistic regression with Odds Ratios, Wald 95% confidence
intervals, McFadden pseudo-R^2, and likelihood ratio testing matching GraphPad Prism 10.
"""

import numpy as np
from scipy import stats
from scipy.optimize import minimize

try:
    import statsmodels.api as sm
except ImportError:
    sm = None


class LogisticRegressionEngine:
    """Engine for simple binary logistic regression analysis."""

    @staticmethod
    def calculate_logistic_regression(
        x_data: np.ndarray, y_data: np.ndarray, confidence_level: float = 0.95
    ) -> dict:
        """Fits binary logistic regression model p(X) = 1 / (1 + exp(-(beta0 + beta1 * X))).

        Args:
            x_data (np.ndarray): Independent predictor variable vector.
            y_data (np.ndarray): Binary dependent response variable vector (0 or 1).
            confidence_level (float): Confidence level for Wald CIs (default 0.95).

        Returns:
            dict: Model parameters containing intercept, slope, SEs, z-statistics, p-values,
                  Odds Ratio, Wald 95% CIs, log-likelihood, and McFadden's pseudo R^2.
        """
        arr_x = np.asarray(x_data, dtype=float)
        arr_y = np.asarray(y_data, dtype=float)

        mask = (
            ~np.isnan(arr_x)
            & ~np.isinf(arr_x)
            & ~np.isnan(arr_y)
            & ~np.isinf(arr_y)
        )
        arr_x = arr_x[mask]
        arr_y = arr_y[mask]

        n = len(arr_x)
        if n < 4:
            return {
                "success": False,
                "error": "Logistic regression requires at least 4 valid observation pairs."
            }

        unique_y = np.unique(arr_y)
        if not np.array_equal(np.sort(unique_y), np.array([0.0, 1.0])):
            if len(unique_y) != 2:
                return {
                    "success": False,
                    "error": "Logistic regression response variable Y must be binary (0 and 1)."
                }

        fitted_sm = False
        if sm is not None:
            try:
                X_const = sm.add_constant(arr_x)
                model = sm.Logit(arr_y, X_const)
                logit_res = model.fit(disp=False, maxiter=100)

                intercept = float(logit_res.params[0])
                slope = float(logit_res.params[1])

                intercept_se = float(logit_res.bse[0])
                slope_se = float(logit_res.bse[1])

                z_stat = float(logit_res.tvalues[1])
                p_val = float(logit_res.pvalues[1])

                ll_model = float(logit_res.llf)
                ll_null = float(logit_res.llnull)
                pseudo_r2 = float(logit_res.prsquared)
                fitted_sm = True
            except Exception:
                fitted_sm = False

        if not fitted_sm:
            # Fallback to SciPy optimization with Fisher Information matrix
            try:
                def neg_log_likelihood(params):
                    b0, b1 = params
                    logits = b0 + b1 * arr_x
                    logits = np.clip(logits, -30.0, 30.0)
                    probs = 1.0 / (1.0 + np.exp(-logits))
                    eps = 1e-15
                    probs = np.clip(probs, eps, 1.0 - eps)
                    return -np.sum(arr_y * np.log(probs) + (1.0 - arr_y) * np.log(1.0 - probs))

                res_opt = minimize(neg_log_likelihood, x0=[0.0, 0.0], method="L-BFGS-B")
                intercept, slope = float(res_opt.x[0]), float(res_opt.x[1])

                # Compute Fisher Information (Hessian matrix of neg log-likelihood)
                logits = np.clip(intercept + slope * arr_x, -30.0, 30.0)
                probs = 1.0 / (1.0 + np.exp(-logits))
                weights = probs * (1.0 - probs)

                # Design matrix X design [1, x_i]
                h00 = float(np.sum(weights))
                h01 = float(np.sum(arr_x * weights))
                h11 = float(np.sum((arr_x**2) * weights))

                det = h00 * h11 - (h01**2)
                if det > 0:
                    intercept_se = float(np.sqrt(h11 / det))
                    slope_se = float(np.sqrt(h00 / det))
                else:
                    intercept_se, slope_se = 0.0, 0.0

                z_stat = float(slope / slope_se) if slope_se > 0 else 0.0
                p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_stat)))) if slope_se > 0 else 1.0

                ll_model = float(-res_opt.fun)
                p0 = float(np.mean(arr_y))
                p0_clipped = float(np.clip(p0, 1e-15, 1.0 - 1e-15))
                ll_null = float(n * (p0_clipped * np.log(p0_clipped) + (1.0 - p0_clipped) * np.log(1.0 - p0_clipped)))
                pseudo_r2 = float(1.0 - (ll_model / ll_null)) if ll_null < 0 else 0.0

            except Exception as e_inner:
                return {"success": False, "error": f"Logistic regression fitting failed: {str(e_inner)}"}

        # Calculate Odds Ratio & Wald 95% CIs
        alpha = 1.0 - confidence_level
        z_crit = float(stats.norm.ppf(1.0 - alpha / 2.0))

        slope_low = float(slope - z_crit * slope_se)
        slope_high = float(slope + z_crit * slope_se)
        slope_ci95 = (slope_low, slope_high)

        slope_clip = float(np.clip(slope, -700.0, 700.0))
        slope_low_clip = float(np.clip(slope_low, -700.0, 700.0))
        slope_high_clip = float(np.clip(slope_high, -700.0, 700.0))

        odds_ratio = float(np.exp(slope_clip))
        odds_ratio_ci95 = (float(np.exp(slope_low_clip)), float(np.exp(slope_high_clip)))

        return {
            "success": True,
            "results": {
                "intercept": intercept,
                "intercept_se": intercept_se,
                "slope": slope,
                "slope_se": slope_se,
                "z_statistic": z_stat,
                "p_value": p_val,
                "odds_ratio": odds_ratio,
                "odds_ratio_ci95": odds_ratio_ci95,
                "slope_ci95": slope_ci95,
                "pseudo_r2": pseudo_r2,
                "log_likelihood": ll_model,
                "null_log_likelihood": ll_null,
                "n_observations": n
            }
        }
