"""
OpenPrism-Qt Descriptive Statistics & Data Exploration Engine.
Licensed under GPLv3.

Calculates key summary metrics (Mean, SD, SEM, 95% CI, Median, Min, Max)
and D'Agostino & Pearson normality test according to GraphPad Prism 10 standards.
"""

import math
import numpy as np
import scipy.stats as stats
from typing import Union


class DescriptiveStatsEngine:
    """
    Data Exploration and Descriptive Statistics Engine.
    """

    @staticmethod
    def calculate_descriptive_stats(data_array: Union[list, np.ndarray]) -> dict:
        """
        Calculates comprehensive summary statistics for a 1D numerical dataset.

        Args:
            data_array: List or 1D numpy array of numerical values.

        Returns:
            Dict containing success boolean and calculated metrics:
                - count: Number of non-NaN observations (n)
                - mean: Arithmetic mean
                - std: Sample standard deviation (ddof=1)
                - sem: Standard error of the mean (std / sqrt(n))
                - median: 50th percentile
                - min: Minimum value
                - max: Maximum value
                - ci_95_lower: Lower bound of 95% confidence interval for mean
                - ci_95_upper: Upper bound of 95% confidence interval for mean
                - confidence_interval: Tuple (ci_95_lower, ci_95_upper)
        """
        try:
            arr = np.asarray(data_array, dtype=float)
            arr = arr[~np.isnan(arr) & ~np.isinf(arr)]

            n = len(arr)
            if n == 0:
                return {
                    "success": False,
                    "error": "Dataset contains no valid numeric observations."
                }

            mean_val = float(np.mean(arr))
            median_val = float(np.median(arr))
            min_val = float(np.min(arr))
            max_val = float(np.max(arr))

            if n > 1:
                std_val = float(np.std(arr, ddof=1))
                sem_val = float(std_val / math.sqrt(n))

                # 95% Confidence Interval of the Mean using Student's t distribution
                df = n - 1
                t_crit = float(stats.t.ppf(0.975, df))
                margin = t_crit * sem_val
                ci_lower = mean_val - margin
                ci_upper = mean_val + margin
            else:
                std_val = 0.0
                sem_val = 0.0
                ci_lower = mean_val
                ci_upper = mean_val

            return {
                "success": True,
                "results": {
                    "count": int(n),
                    "mean": mean_val,
                    "std": std_val,
                    "sem": sem_val,
                    "median": median_val,
                    "min": min_val,
                    "max": max_val,
                    "ci_95_lower": ci_lower,
                    "ci_95_upper": ci_upper,
                    "confidence_interval": (ci_lower, ci_upper)
                }
            }

        except Exception as exc:
            return {
                "success": False,
                "error": f"Failed to compute descriptive statistics: {str(exc)}"
            }

    @staticmethod
    def calculate_normality_test(data_array: Union[list, np.ndarray]) -> dict:
        """
        Evaluates D'Agostino & Pearson omnitest for normality (K^2 test).

        Args:
            data_array: List or 1D numpy array of numerical values.

        Returns:
            Dict containing success boolean, K^2 statistic, P-value, and normality conclusion (P >= 0.05).
        """
        try:
            arr = np.asarray(data_array, dtype=float)
            arr = arr[~np.isnan(arr) & ~np.isinf(arr)]

            n = len(arr)
            if n < 8:
                return {
                    "success": False,
                    "error": f"D'Agostino & Pearson normality test requires at least 8 observations (provided {n})."
                }

            stat_val, p_val = stats.normaltest(arr)

            return {
                "success": True,
                "results": {
                    "statistic": float(stat_val),
                    "p_value": float(p_val),
                    "is_normal": bool(p_val >= 0.05),
                    "count": int(n)
                }
            }

        except Exception as exc:
            return {
                "success": False,
                "error": f"Failed to compute normality test: {str(exc)}"
            }
