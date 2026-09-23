"""
OpenPrism-Qt Michaelis-Menten Enzyme Kinetics Engine.

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

Implements Michaelis-Menten enzyme kinetics parameter estimation (Vmax, Km)
using non-linear least squares optimization matching GraphPad Prism 10 standards.
"""

import numpy as np
from scipy import stats
from scipy.optimize import curve_fit


def michaelis_menten_model(substrate, vmax, km):
    """Michaelis-Menten kinetics equation: V = (Vmax * [S]) / (Km + [S])."""
    return (vmax * substrate) / (km + substrate)


class MichaelisMentenEngine:
    """Engine for Michaelis-Menten enzyme kinetics analysis."""

    @staticmethod
    def calculate_michaelis_menten(
        substrate: np.ndarray, velocity: np.ndarray
    ) -> dict:
        """Fits Michaelis-Menten kinetics model to substrate concentration and reaction velocity data.

        Args:
            substrate (np.ndarray): Substrate concentrations [S].
            velocity (np.ndarray): Initial reaction velocities V.

        Returns:
            dict: Model metrics containing Vmax, Km, standard errors, 95% CIs, R^2, and residual statistics.
        """
        arr_s = np.asarray(substrate, dtype=float)
        arr_v = np.asarray(velocity, dtype=float)

        mask = (
            ~np.isnan(arr_s)
            & ~np.isinf(arr_s)
            & ~np.isnan(arr_v)
            & ~np.isinf(arr_v)
            & (arr_s >= 0)
        )
        arr_s = arr_s[mask]
        arr_v = arr_v[mask]

        n = len(arr_s)
        if n < 3:
            return {
                "success": False,
                "error": "Michaelis-Menten fitting requires at least 3 valid observations."
            }

        sort_idx = np.argsort(arr_s)
        arr_s = arr_s[sort_idx]
        arr_v = arr_v[sort_idx]

        try:
            # Heuristic initial parameter estimations
            vmax_init = float(np.max(arr_v)) if np.max(arr_v) > 0 else 1.0
            half_vmax = vmax_init / 2.0

            # Find substrate conc closest to half Vmax
            idx_closest = np.argmin(np.abs(arr_v - half_vmax))
            km_init = float(arr_s[idx_closest]) if arr_s[idx_closest] > 0 else float(np.median(arr_s))
            if km_init <= 0:
                km_init = 1.0

            p0 = [vmax_init, km_init]
            bounds = ([0.0, 1e-12], [np.inf, np.inf])

            popt, pcov = curve_fit(
                michaelis_menten_model, arr_s, arr_v, p0=p0, bounds=bounds, maxfev=10000
            )

            vmax_fit, km_fit = float(popt[0]), float(popt[1])

            if pcov is not None and np.all(np.isfinite(pcov)):
                perr = np.sqrt(np.diag(pcov))
                vmax_se, km_se = float(perr[0]), float(perr[1])
            else:
                vmax_se, km_se = 0.0, 0.0

            df = int(n - 2)
            t_crit = float(stats.t.ppf(0.975, df)) if df > 0 else 1.96
            vmax_ci95 = (float(vmax_fit - t_crit * vmax_se), float(vmax_fit + t_crit * vmax_se))
            km_ci95 = (float(km_fit - t_crit * km_se), float(km_fit + t_crit * km_se))

            # Goodness of fit
            v_pred = michaelis_menten_model(arr_s, vmax_fit, km_fit)
            ss_res = float(np.sum((arr_v - v_pred) ** 2))
            ss_tot = float(np.sum((arr_v - np.mean(arr_v)) ** 2))
            r_squared = float(1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0
            std_err_est = float(np.sqrt(ss_res / df)) if df > 0 else 0.0

            return {
                "success": True,
                "results": {
                    "vmax": vmax_fit,
                    "km": km_fit,
                    "vmax_se": vmax_se,
                    "km_se": km_se,
                    "vmax_ci95": vmax_ci95,
                    "km_ci95": km_ci95,
                    "r_squared": r_squared,
                    "ss_res": ss_res,
                    "std_err_estimate": std_err_est,
                    "degrees_of_freedom": df,
                    "n_observations": n
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Michaelis-Menten fit failed: {str(e)}"}
