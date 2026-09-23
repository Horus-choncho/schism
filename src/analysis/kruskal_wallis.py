"""
OpenPrism-Qt Kruskal-Wallis & Dunn's Post-Hoc Test Engine.

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

Implements Non-parametric Kruskal-Wallis One-Way ANOVA with Dunn's Multiple
Comparisons Post-Hoc Test matching GraphPad Prism 10 standards.
"""

from typing import List, Dict, Union
import numpy as np
from scipy import stats


class KruskalWallisEngine:
    """Engine for Kruskal-Wallis non-parametric one-way ANOVA and Dunn's post-hoc test."""

    @staticmethod
    def calculate_kruskal_wallis(
        groups: Union[List[np.ndarray], Dict[str, np.ndarray]]
    ) -> dict:
        """Computes Kruskal-Wallis H test and Dunn's post-hoc test across multiple groups.

        Args:
            groups (List[np.ndarray] or Dict[str, np.ndarray]): Group vectors of observations.

        Returns:
            dict: Summary dictionary containing H-statistic, p-value, df, group summaries,
                  and Dunn's post-hoc pairwise comparisons.
        """
        if isinstance(groups, dict):
            names = list(groups.keys())
            raw_data = list(groups.values())
        elif isinstance(groups, list):
            names = [f"Group {i+1}" for i in range(len(groups))]
            raw_data = groups
        else:
            return {"success": False, "error": "Groups must be a list or dictionary of arrays."}

        clean_groups = []
        clean_names = []
        for name, arr in zip(names, raw_data):
            vec = np.asarray(arr, dtype=float)
            vec = vec[~np.isnan(vec) & ~np.isinf(vec)]
            if len(vec) > 0:
                clean_groups.append(vec)
                clean_names.append(str(name))

        if len(clean_groups) < 2:
            return {
                "success": False,
                "error": "Kruskal-Wallis analysis requires at least 2 non-empty groups."
            }

        total_n = sum(len(g) for g in clean_groups)
        if total_n < 3:
            return {
                "success": False,
                "error": "Total observations across all groups must be at least 3."
            }

        try:
            # SciPy Kruskal-Wallis H-test
            stat, p_val = stats.kruskal(*clean_groups)
            h_stat = float(stat)
            p_value = float(p_val)
            df = len(clean_groups) - 1

            # Compute combined ranks for Dunn's test
            all_values = np.concatenate(clean_groups)
            all_ranks = stats.rankdata(all_values)

            # Assign ranks back to groups and calculate group mean ranks
            idx = 0
            group_summaries = []
            mean_ranks = []
            group_sizes = []

            for name, g in zip(clean_names, clean_groups):
                n_i = len(g)
                g_ranks = all_ranks[idx : idx + n_i]
                idx += n_i

                m_rank = float(np.mean(g_ranks))
                med = float(np.median(g))

                mean_ranks.append(m_rank)
                group_sizes.append(n_i)
                group_summaries.append({
                    "group": name,
                    "n": n_i,
                    "median": med,
                    "mean_rank": m_rank
                })

            # Dunn's post-hoc test
            # Tie correction factor C
            _, tie_counts = np.unique(all_values, return_counts=True)
            tie_sum = np.sum(tie_counts**3 - tie_counts)
            tie_correction = 1.0 - (tie_sum / (total_n**3 - total_n)) if total_n > 1 else 1.0
            if tie_correction <= 0:
                tie_correction = 1.0

            n_comparisons = (len(clean_groups) * (len(clean_groups) - 1)) // 2
            dunn_results = []

            for i in range(len(clean_groups)):
                for j in range(i + 1, len(clean_groups)):
                    n_i = group_sizes[i]
                    n_j = group_sizes[j]
                    diff = mean_ranks[i] - mean_ranks[j]

                    # Standard error of rank difference
                    se_ij = np.sqrt(
                        (total_n * (total_n + 1) / 12.0) * tie_correction * (1.0 / n_i + 1.0 / n_j)
                    )

                    z_stat = float(diff / se_ij) if se_ij > 0 else 0.0
                    p_unadj = float(2.0 * (1.0 - stats.norm.cdf(abs(z_stat))))
                    p_adj = min(1.0, p_unadj * n_comparisons)

                    dunn_results.append({
                        "group1": clean_names[i],
                        "group2": clean_names[j],
                        "rank_diff": float(diff),
                        "z_statistic": z_stat,
                        "p_value": p_unadj,
                        "p_adjusted_bonferroni": float(p_adj),
                        "significant": bool(p_adj < 0.05)
                    })

            return {
                "success": True,
                "results": {
                    "h_statistic": h_stat,
                    "p_value": p_value,
                    "degrees_of_freedom": df,
                    "n_groups": len(clean_groups),
                    "total_n": total_n,
                    "group_summaries": group_summaries,
                    "dunn_posthoc": dunn_results
                }
            }

        except Exception as e:
            return {"success": False, "error": f"Kruskal-Wallis calculation failed: {str(e)}"}
