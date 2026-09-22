"""
OpenPrism-Qt Analytical Curve Fitting Engine.

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
from scipy.optimize import curve_fit


def dose_response_model(x: np.ndarray, bottom: float, top: float, log_ec50: float) -> np.ndarray:
    """Standard GraphPad Prism Hill equation for non-linear Dose-Response curves.

    Mathematical Formula:
        Y = Bottom + (Top - Bottom) / (1 + 10^(LogEC50 - X))

    where X is log(concentration), Bottom is the minimum asymptotic response,
    Top is the maximum asymptotic response, and LogEC50 is the log concentration
    producing a half-maximal response.

    Args:
        x (np.ndarray): Vector of independent variable values (log concentration).
        bottom (float): Minimum asymptote (baseline Y value at low concentrations).
        top (float): Maximum asymptote (plateau Y value at high concentrations).
        log_ec50 (float): Logarithm (base 10) of the EC50 concentration parameter.

    Returns:
        np.ndarray: Predicted Y values evaluated along the sigmoid curve.
    """
    # Evaluate 4-parameter logistic (4PL) sigmoid equation with fixed unit Hill slope (h = 1.0)
    exponent = np.clip(log_ec50 - x, -20, 20)
    return bottom + (top - bottom) / (1 + 10**exponent)


class CurveFittingEngine:
    """Analytical non-linear regression engine using Levenberg-Marquardt least squares optimization."""

    @staticmethod
    def fit_dose_response(x_data: np.ndarray, y_data: np.ndarray) -> dict:
        """Fits experimental data vectors to the standard four-parameter dose-response curve safely.

        Performs non-linear least squares optimization via scipy.optimize.curve_fit.
        Derives standard errors of estimated parameters from the diagonal of the covariance matrix:
            SE(theta_i) = sqrt(C_{i,i})

        Args:
            x_data (np.ndarray): 1D array of independent variable observations (X coordinates).
            y_data (np.ndarray): 1D array of dependent variable observations (Y coordinates).

        Returns:
            dict: Result payload containing:
                - 'success' (bool): True if convergence was achieved, False otherwise.
                - 'params' (dict): Optimal fit parameters ('bottom', 'top', 'log_ec50', 'ec50').
                - 'errors' (dict): Asymptotic standard errors ('bottom_err', 'top_err', 'log_ec50_err').
                - 'error' (str): Descriptive message if optimization fails or data is insufficient.
        """
        # Minimum requirement of 3 observations to fit 3 free parameters (bottom, top, log_ec50)
        # to ensure at least 1 degree of freedom (N - K = 3 - 3 = 0, minimum 3 points for parameter resolution).
        if len(x_data) < 3 or len(y_data) < 3 or len(x_data) != len(y_data):
            return {"success": False, "error": "Insufficient or mismatched data vectors"}

        try:
            # Generate empirical initial parameter guesses [bottom, top, log_ec50]:
            # - bottom ~ min(Y)
            # - top ~ max(Y)
            # - log_ec50 ~ mean(X) as a robust midpoint guess
            initial_guesses = [np.min(y_data), np.max(y_data), np.mean(x_data)]
            
            # Execute non-linear least squares fit (Levenberg-Marquardt / Trust Region Reflective algorithm)
            popt, pcov = curve_fit(dose_response_model, x_data, y_data, p0=initial_guesses, maxfev=5000)
            
            # Standard errors of parameter estimates are computed as the square root of diagonal
            # covariance elements: SE = sqrt(diag(pcov))
            perr = np.sqrt(np.diag(pcov))
            
            log_ec50_val = float(popt[2])
            if log_ec50_val > 20:
                ec50_val = float(10**20)
            else:
                try:
                    ec50_val = float(10**log_ec50_val)
                except (OverflowError, FloatingPointError):
                    ec50_val = float(10**20)

            return {
                "success": True,
                "params": {
                    "bottom": float(popt[0]),
                    "top": float(popt[1]),
                    "log_ec50": log_ec50_val,
                    "ec50": ec50_val  # Convert log(EC50) parameter back to absolute concentration scale with overflow protection
                },
                "errors": {
                    "bottom_err": float(perr[0]),
                    "top_err": float(perr[1]),
                    "log_ec50_err": float(perr[2])
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Optimization fitting failed: {str(e)}"}
