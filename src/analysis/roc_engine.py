"""
OpenPrism-Qt Receiver Operating Characteristic (ROC) Engine.

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

Implements ROC curve generation, AUC calculation with Hanley & McNeil standard error,
Wilson score 95% confidence intervals, and Youden J index optimal threshold selection.
"""

from typing import Tuple
import numpy as np
from scipy import stats


class RocEngine:
    """Engine for Receiver Operating Characteristic (ROC) curve analysis."""

    @staticmethod
    def _wilson_score_ci(p: float, n: int, z: float = 1.959963) -> Tuple[float, float]:
        """Calculates Wilson score 95% confidence interval for a proportion p with sample size n."""
        if n == 0:
            return (0.0, 1.0)
        denom = 1.0 + (z**2) / n
        center = (p + (z**2) / (2.0 * n)) / denom
        margin = (z / denom) * np.sqrt((p * (1.0 - p)) / n + (z**2) / (4.0 * (n**2)))
        lower = max(0.0, float(center - margin))
        upper = min(1.0, float(center + margin))
        return (lower, upper)

    @staticmethod
    def calculate_roc_analysis(
        y_true: np.ndarray, y_score: np.ndarray, confidence_level: float = 0.95
    ) -> dict:
        """Computes ROC curve, AUC, sensitivity/specificity coordinates, Wilson score CIs, and Youden J.

        Args:
            y_true (np.ndarray): Binary ground truth labels (0 or 1).
            y_score (np.ndarray): Continuous classification score / probability.
            confidence_level (float): Confidence level for AUC & Wilson score CIs.

        Returns:
            dict: Summary metrics containing AUC, SE(AUC), 95% CI, p-value, Youden J index,
                  optimal threshold, and full ROC coordinate table.
        """
        arr_true = np.asarray(y_true, dtype=float)
        arr_score = np.asarray(y_score, dtype=float)

        mask = (
            ~np.isnan(arr_true)
            & ~np.isinf(arr_true)
            & ~np.isnan(arr_score)
            & ~np.isinf(arr_score)
        )
        arr_true = arr_true[mask]
        arr_score = arr_score[mask]

        if len(arr_true) < 3:
            return {
                "success": False,
                "error": "ROC analysis requires at least 3 valid observations."
            }

        unique_labels = np.unique(arr_true)
        if not np.array_equal(np.sort(unique_labels), np.array([0.0, 1.0])):
            if len(unique_labels) != 2:
                return {
                    "success": False,
                    "error": "ROC analysis requires binary ground truth labels (0 and 1)."
                }

        n_pos = int(np.sum(arr_true == 1.0))
        n_neg = int(np.sum(arr_true == 0.0))

        if n_pos == 0 or n_neg == 0:
            return {
                "success": False,
                "error": "ROC analysis requires at least one positive and one negative observation."
            }

        try:
            # Generate threshold list
            thresholds = np.unique(arr_score)
            thresholds = np.sort(thresholds)[::-1]  # Descending
            # Include boundary infinity threshold
            thresholds = np.concatenate([[np.inf], thresholds, [-np.inf]])

            roc_table = []
            fpr_list = []
            tpr_list = []

            alpha = 1.0 - confidence_level
            z_crit = float(stats.norm.ppf(1.0 - alpha / 2.0))

            best_j = -1.0
            opt_thresh = float(thresholds[0])
            opt_sens = 0.0
            opt_spec = 0.0

            for t in thresholds:
                preds = (arr_score >= t)
                tp = int(np.sum(preds & (arr_true == 1.0)))
                fp = int(np.sum(preds & (arr_true == 0.0)))
                tn = n_neg - fp
                fn = n_pos - tp

                tpr = float(tp / n_pos) if n_pos > 0 else 0.0
                fpr = float(fp / n_neg) if n_neg > 0 else 0.0
                sens = tpr
                spec = float(tn / n_neg) if n_neg > 0 else 0.0

                sens_ci = RocEngine._wilson_score_ci(sens, n_pos, z_crit)
                spec_ci = RocEngine._wilson_score_ci(spec, n_neg, z_crit)

                fpr_list.append(fpr)
                tpr_list.append(tpr)

                j_index = sens + spec - 1.0
                if j_index > best_j:
                    best_j = j_index
                    opt_thresh = float(t)
                    opt_sens = sens
                    opt_spec = spec

                roc_table.append({
                    "threshold": float(t) if not np.isinf(t) else ("+inf" if t > 0 else "-inf"),
                    "fpr": fpr,
                    "tpr": tpr,
                    "sensitivity": sens,
                    "sensitivity_ci95": sens_ci,
                    "specificity": spec,
                    "specificity_ci95": spec_ci
                })

            # Calculate AUC using trapezoidal rule
            # Sort FPR and TPR for integration
            sorted_indices = np.argsort(fpr_list)
            fpr_sorted = np.array(fpr_list)[sorted_indices]
            tpr_sorted = np.array(tpr_list)[sorted_indices]
            
            if hasattr(np, "trapezoid"):
                auc = float(np.trapezoid(tpr_sorted, fpr_sorted))
            else:
                from scipy.integrate import trapezoid
                auc = float(trapezoid(tpr_sorted, fpr_sorted))

            # Hanley & McNeil (1982) Standard Error of AUC
            q1 = auc / (2.0 - auc) if (2.0 - auc) != 0 else 0.0
            q2 = (2.0 * (auc ** 2)) / (1.0 + auc) if (1.0 + auc) != 0 else 0.0

            num_se = auc * (1.0 - auc) + (n_pos - 1) * (q1 - auc**2) + (n_neg - 1) * (q2 - auc**2)
            den_se = n_pos * n_neg
            auc_se = float(np.sqrt(num_se / den_se)) if den_se > 0 and num_se > 0 else 0.0

            auc_ci95 = (
                max(0.0, float(auc - z_crit * auc_se)),
                min(1.0, float(auc + z_crit * auc_se))
            )

            # P-value testing AUC = 0.5
            if auc_se > 0:
                z_auc = float(abs(auc - 0.5) / auc_se)
                p_val = float(2.0 * (1.0 - stats.norm.cdf(z_auc)))
            else:
                # When AUC standard error is zero (e.g., perfect classification AUC = 1.0)
                p_val = 0.0 if abs(auc - 0.5) > 1e-6 else 1.0

            return {
                "success": True,
                "results": {
                    "auc": auc,
                    "auc_se": auc_se,
                    "auc_ci95": auc_ci95,
                    "p_value": p_val,
                    "youden_j": float(best_j),
                    "optimal_threshold": opt_thresh,
                    "optimal_sensitivity": opt_sens,
                    "optimal_specificity": opt_spec,
                    "n_positive": n_pos,
                    "n_negative": n_neg,
                    "roc_table": roc_table
                }
            }
        except Exception as e:
            return {"success": False, "error": f"ROC calculation failed: {str(e)}"}
