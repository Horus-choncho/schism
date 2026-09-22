"""
OpenPrism-Qt Kaplan-Meier Survival Analysis Engine.

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

import math
import numpy as np
from typing import Dict, Any, Union, List


class KaplanMeierEngine:
    """Non-parametric Kaplan-Meier Survival Analysis Engine."""

    @staticmethod
    def calculate_kaplan_meier(
        time_data: Union[list, np.ndarray],
        event_data: Union[list, np.ndarray]
    ) -> Dict[str, Any]:
        """Computes non-parametric step-function survival probabilities over progressive time intervals.

        Mathematical Formulas:
            Product-Limit Survival Probability:
                S(t_k) = prod_{j <= k} (1 - d_j / n_j)
            where:
                n_j = number of subjects at risk just prior to time t_j
                d_j = number of observed events (failures) at time t_j
                c_j = number of right-censored observations at time t_j

            Greenwood's Formula for Variance & Standard Error:
                Var(S(t_k)) = S(t_k)^2 * sum_{j <= k} (d_j / (n_j * (n_j - d_j)))
                SE(S(t_k)) = sqrt(Var(S(t_k)))

            Cumulative Hazard Function:
                H(t_k) = -ln(S(t_k))

            95% Linear Confidence Interval:
                CI = max(0, min(1, S(t_k) +/- 1.96 * SE(S(t_k))))

        Args:
            time_data (Union[list, np.ndarray]): Numeric vector of follow-up times (T >= 0).
            event_data (Union[list, np.ndarray]): Binary vector indicating event occurrence
                (1 = event occurred, 0 = right-censored).

        Returns:
            Dict[str, Any]: Result payload containing step-function time points, at-risk counts,
                event counts, censored counts, survival probabilities, Greenwood standard errors,
                95% confidence interval bounds, cumulative hazards, and estimated median survival time.
        """
        t_arr = np.asarray(time_data, dtype=float)
        e_arr = np.asarray(event_data, dtype=float)

        # Pairwise complete-case validation
        mask = ~np.isnan(t_arr) & ~np.isinf(t_arr) & ~np.isnan(e_arr) & ~np.isinf(e_arr) & (t_arr >= 0)
        t_arr = t_arr[mask]
        e_arr = e_arr[mask]

        n_total = len(t_arr)
        if n_total < 1:
            return {"success": False, "error": "Survival analysis requires at least 1 valid observation."}

        try:
            # Sort observations primarily by time ascending, secondarily by event (censored 0 after event 1)
            sort_idx = np.lexsort((1 - e_arr, t_arr))
            t_sorted = t_arr[sort_idx]
            e_sorted = e_arr[sort_idx]

            unique_times = np.unique(t_sorted)

            table_rows = []
            cum_surv = 1.0
            greenwood_sum = 0.0
            at_risk = n_total
            median_survival = np.nan

            for t in unique_times:
                idx_at_t = np.where(t_sorted == t)[0]
                n_at_risk = at_risk
                events_at_t = int(np.sum(e_sorted[idx_at_t] == 1))
                censored_at_t = int(np.sum(e_sorted[idx_at_t] == 0))

                if events_at_t > 0:
                    cond_surv = 1.0 - (events_at_t / n_at_risk)
                    cum_surv *= cond_surv

                    # Greenwood variance summation term: d / (n * (n - d))
                    if n_at_risk > events_at_t:
                        greenwood_sum += events_at_t / (n_at_risk * (n_at_risk - events_at_t))

                std_err = cum_surv * math.sqrt(greenwood_sum) if greenwood_sum > 0 else 0.0

                # 95% Confidence Interval bounds (1.96 * SE)
                ci_margin = 1.96 * std_err
                ci_lower = max(0.0, float(cum_surv - ci_margin))
                ci_upper = min(1.0, float(cum_surv + ci_margin))

                # Cumulative hazard H(t) = -ln(S(t))
                cum_hazard = float(-math.log(max(1e-12, cum_surv))) if cum_surv > 0 else np.nan

                # Detect median survival time (first time point where S(t) <= 0.5)
                if np.isnan(median_survival) and cum_surv <= 0.5:
                    median_survival = float(t)

                table_rows.append({
                    "time": float(t),
                    "at_risk": int(n_at_risk),
                    "events": events_at_t,
                    "censored": censored_at_t,
                    "survival_probability": float(cum_surv),
                    "std_error": float(std_err),
                    "ci_95_lower": ci_lower,
                    "ci_95_upper": ci_upper,
                    "cum_hazard": cum_hazard
                })

                at_risk -= (events_at_t + censored_at_t)

            return {
                "success": True,
                "summary": {
                    "n_total": n_total,
                    "total_events": int(np.sum(e_sorted == 1)),
                    "total_censored": int(np.sum(e_sorted == 0)),
                    "median_survival_time": float(median_survival) if not np.isnan(median_survival) else "Undefined (> 50% survival)"
                },
                "results": {
                    "survival_table": table_rows
                }
            }
        except Exception as exc:
            return {"success": False, "error": f"Kaplan-Meier computation failed: {str(exc)}"}
