"""
OpenPrism-Qt Outliers Detection Engine (ROUT & Grubbs Tests).

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

Implements ROUT (Q=1%) false discovery rate outlier detection and Grubbs'
extreme studentized deviate test matching GraphPad Prism 10 standards.
"""

from typing import Optional
import numpy as np
from scipy import stats


class OutliersEngine:
    """Engine for outlier identification using ROUT (Q=1%) and Grubbs tests."""

    @staticmethod
    def detect_outliers(
        data: np.ndarray, q_threshold: float = 0.01, alpha: float = 0.05
    ) -> dict:
        """Detects outliers using ROUT (False Discovery Rate) and Grubbs' ESD test.

        Args:
            data (np.ndarray): Input 1D numerical data array.
            q_threshold (float): ROUT false discovery rate threshold (Q=1% by default).
            alpha (float): Significance level for Grubbs test (default 0.05).

        Returns:
            dict: Detection results containing separate ROUT and Grubbs diagnostics.
        """
        arr = np.asarray(data, dtype=float)
        mask = ~np.isnan(arr) & ~np.isinf(arr)
        clean_arr = arr[mask]
        original_indices = np.where(mask)[0]

        n = len(clean_arr)
        if n < 3:
            return {
                "success": False,
                "error": "Outlier detection requires at least 3 valid observations."
            }

        rout_res = OutliersEngine._rout_detection(clean_arr, original_indices, q_threshold)
        grubbs_res = OutliersEngine._grubbs_detection(clean_arr, original_indices, alpha)

        return {
            "success": True,
            "results": {
                "rout": rout_res,
                "grubbs": grubbs_res
            }
        }

    @staticmethod
    def _rout_detection(
        arr: np.ndarray, original_indices: np.ndarray, q_threshold: float
    ) -> dict:
        """Computes ROUT outlier identification using robust standard deviation and FDR."""
        n = len(arr)
        med = float(np.median(arr))
        mad = float(np.median(np.abs(arr - med)))

        # Robust standard deviation: s_rob = 1.4826 * MAD
        s_rob = 1.4826 * mad
        if s_rob == 0:
            s_rob = float(np.std(arr, ddof=1)) if np.std(arr, ddof=1) > 0 else 1e-12

        abs_diffs = np.abs(arr - med)
        t_stats = abs_diffs / s_rob
        df = max(1, n - 1)

        p_vals = 2.0 * (1.0 - stats.t.cdf(t_stats, df=df))

        # Benjamini-Hochberg FDR procedure
        sorted_order = np.argsort(p_vals)
        sorted_p = p_vals[sorted_order]

        q_crit = (np.arange(1, n + 1) / float(n)) * q_threshold
        passed = sorted_p <= q_crit

        outlier_sorted_idx = np.where(passed)[0]
        if len(outlier_sorted_idx) > 0:
            max_k = np.max(outlier_sorted_idx)
            is_outlier_sorted = np.arange(n) <= max_k
            outlier_mask_in_arr = np.zeros(n, dtype=bool)
            outlier_mask_in_arr[sorted_order[is_outlier_sorted]] = True
        else:
            outlier_mask_in_arr = np.zeros(n, dtype=bool)

        outlier_indices = original_indices[outlier_mask_in_arr].tolist()
        outlier_values = arr[outlier_mask_in_arr].tolist()
        cleaned = arr[~outlier_mask_in_arr]

        return {
            "q_threshold": q_threshold,
            "outliers_count": len(outlier_indices),
            "outlier_indices": outlier_indices,
            "outlier_values": outlier_values,
            "clean_data": cleaned
        }

    @staticmethod
    def _grubbs_detection(
        arr: np.ndarray, original_indices: np.ndarray, alpha: float
    ) -> dict:
        """Computes Grubbs' test for a single extreme outlier."""
        n = len(arr)
        mean = float(np.mean(arr))
        std = float(np.std(arr, ddof=1))

        if std == 0:
            return {
                "alpha": alpha,
                "g_statistic": 0.0,
                "g_critical": 0.0,
                "p_value": 1.0,
                "is_outlier": False,
                "outlier_index": None,
                "outlier_value": None,
                "clean_data": arr
            }

        diffs = np.abs(arr - mean)
        max_idx = int(np.argmax(diffs))
        g_stat = float(diffs[max_idx] / std)

        # Critical value calculation
        df = n - 2
        t_crit = float(stats.t.ppf(1.0 - alpha / (2.0 * n), df=df))
        g_crit = float(((n - 1) / np.sqrt(n)) * np.sqrt(t_crit**2 / (n - 2 + t_crit**2)))

        # P-value for Grubbs test
        denom = n - 1.0 - g_stat**2
        if denom > 0:
            t_val = np.sqrt((df * g_stat**2) / denom)
            p_val = min(1.0, float(n * 2.0 * (1.0 - stats.t.cdf(t_val, df=df))))
        else:
            p_val = 0.0

        is_outlier = bool(g_stat > g_crit)
        outlier_orig_idx = int(original_indices[max_idx]) if is_outlier else None
        outlier_val = float(arr[max_idx]) if is_outlier else None

        if is_outlier:
            cleaned = np.delete(arr, max_idx)
        else:
            cleaned = arr

        return {
            "alpha": alpha,
            "g_statistic": g_stat,
            "g_critical": g_crit,
            "p_value": p_val,
            "is_outlier": is_outlier,
            "outlier_index": outlier_orig_idx,
            "outlier_value": outlier_val,
            "clean_data": cleaned
        }
