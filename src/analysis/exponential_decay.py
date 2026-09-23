"""
OpenPrism-Qt Exponential Decay & Association Model Engine.

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

Implements One-Phase Exponential Association and Decay curve fitting using
SciPy non-linear least squares optimization matching GraphPad Prism 10 standards.
"""

import numpy as np
from scipy.optimize import curve_fit


def one_phase_decay(x, y0, plateau, k):
    """Exponential decay model equation: Y = (Y0 - Plateau) * exp(-K * X) + Plateau."""
    return (y0 - plateau) * np.exp(-k * x) + plateau


def one_phase_association(x, y0, plateau, k):
    """Exponential association model equation: Y = Y0 + (Plateau - Y0) * (1 - exp(-K * X))."""
    return y0 + (plateau - y0) * (1.0 - np.exp(-k * x))


class ExponentialDecayEngine:
    """Engine for one-phase exponential association and decay curve fitting."""

    @staticmethod
    def calculate_exponential_fit(
        x_data: np.ndarray, y_data: np.ndarray, model_type: str = "decay"
    ) -> dict:
        """Fits a one-phase exponential decay or association model to (X, Y) data.

        Args:
            x_data (np.ndarray): Independent variable data vector.
            y_data (np.ndarray): Dependent variable data vector.
            model_type (str): "decay" or "association". Defaults to "decay".

        Returns:
            dict: Model parameters (Y0, Plateau, K, Half-life, Span), standard errors, R^2,
                  and residual statistics.
        """
        arr_x = np.asarray(x_data, dtype=float)
        arr_y = np.asarray(y_data, dtype=float)

        mask = ~np.isnan(arr_x) & ~np.isinf(arr_x) & ~np.isnan(arr_y) & ~np.isinf(arr_y)
        arr_x = arr_x[mask]
        arr_y = arr_y[mask]

        n = len(arr_x)
        if n < 4:
            return {
                "success": False,
                "error": "Exponential fitting requires at least 4 valid observation pairs."
            }

        sort_idx = np.argsort(arr_x)
        arr_x = arr_x[sort_idx]
        arr_y = arr_y[sort_idx]

        model_type = model_type.lower()
        if model_type not in ["decay", "association"]:
            return {"success": False, "error": f"Unsupported model type '{model_type}'. Choose 'decay' or 'association'."}

        try:
            # Initial heuristic parameter estimations
            y0_init = float(arr_y[0])
            plateau_init = float(arr_y[-1])
            x_range = float(np.ptp(arr_x)) if np.ptp(arr_x) > 0 else 1.0
            k_init = 1.0 / (x_range / 2.0) if x_range > 0 else 0.1

            p0 = [y0_init, plateau_init, k_init]
            bounds = ([-np.inf, -np.inf, 0.0], [np.inf, np.inf, np.inf])
            fit_func = one_phase_decay if model_type == "decay" else one_phase_association

            popt, pcov = curve_fit(fit_func, arr_x, arr_y, p0=p0, bounds=bounds, maxfev=10000)

            y0_fit, plateau_fit, k_fit = float(popt[0]), float(popt[1]), float(popt[2])

            if pcov is not None and np.all(np.isfinite(pcov)):
                perr = np.sqrt(np.diag(pcov))
                y0_se, plateau_se, k_se = float(perr[0]), float(perr[1]), float(perr[2])
            else:
                y0_se, plateau_se, k_se = 0.0, 0.0, 0.0

            half_life = float(np.log(2.0) / k_fit) if k_fit > 0 else 0.0
            span = float(abs(y0_fit - plateau_fit))

            # Goodness-of-fit metrics
            y_pred = fit_func(arr_x, y0_fit, plateau_fit, k_fit)
            ss_res = float(np.sum((arr_y - y_pred) ** 2))
            ss_tot = float(np.sum((arr_y - np.mean(arr_y)) ** 2))
            r_squared = float(1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

            df = int(n - 3)
            std_err_est = float(np.sqrt(ss_res / df)) if df > 0 else 0.0

            return {
                "success": True,
                "results": {
                    "model_type": model_type,
                    "params": {
                        "y0": y0_fit,
                        "plateau": plateau_fit,
                        "k": k_fit,
                        "half_life": half_life,
                        "span": span
                    },
                    "param_se": {
                        "y0": y0_se,
                        "plateau": plateau_se,
                        "k": k_se
                    },
                    "r_squared": r_squared,
                    "ss_res": ss_res,
                    "std_err_estimate": std_err_est,
                    "degrees_of_freedom": df,
                    "n_observations": n
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Exponential curve fit failed: {str(e)}"}
