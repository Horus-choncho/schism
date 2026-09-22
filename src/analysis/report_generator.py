"""
VibePad Schism Scientific Ledger Report Generator.

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

Generates GraphPad Prism 10 style HTML scientific ledger sheets for
Descriptive Statistics, One-Way ANOVA, Two-Way ANOVA, Kaplan-Meier Survival Analysis,
Tukey HSD Post-Hoc, and t-Tests.
"""

import math
import numpy as np
import pandas as pd
from src.data_engine.table_model import ScientificTableModel
from src.analysis.descriptive import DescriptiveStatsEngine
from src.analysis.anova_engine import AnovaEngine
from src.analysis.anova_two_way import TwoWayAnovaEngine
from src.analysis.survival_engine import KaplanMeierEngine
from src.analysis.t_test import TTestEngine


def get_p_asterisks(p_val: float) -> str:
    """Returns standard GraphPad Prism significance asterisks for a given p-value."""
    if p_val < 0.0001:
        return "****"
    elif p_val < 0.001:
        return "***"
    elif p_val < 0.01:
        return "**"
    elif p_val < 0.05:
        return "*"
    else:
        return "ns"


class ScientificReportGenerator:
    """Generates rich, high-contrast HTML ledger reports formatted for QTextBrowser."""

    STYLESHEET_HEADER = """
    <style>
        body {
            background-color: #252525;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            padding: 12px;
            font-size: 13px;
        }
        h2 {
            color: #38bdf8;
            border-bottom: 2px solid #0284c7;
            padding-bottom: 6px;
            margin-top: 0px;
            font-size: 18px;
        }
        h3 {
            color: #0284c7;
            margin-top: 18px;
            margin-bottom: 8px;
            font-size: 15px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin-top: 8px;
            margin-bottom: 16px;
            background-color: #1e1e1e;
            border: 1px solid #3d3d3d;
        }
        th {
            background-color: #333333;
            color: #38bdf8;
            font-weight: bold;
            text-align: left;
            padding: 8px 10px;
            border: 1px solid #444444;
            font-size: 12px;
        }
        td {
            padding: 7px 10px;
            border: 1px solid #333333;
            color: #e0e0e0;
            font-size: 12px;
        }
        tr:nth-child(even) {
            background-color: #282828;
        }
        .sig {
            color: #4ade80;
            font-weight: bold;
        }
        .ns {
            color: #9ca3af;
        }
        .summary-box {
            background-color: #1e293b;
            border: 1px solid #0284c7;
            border-radius: 6px;
            padding: 10px 14px;
            margin-bottom: 16px;
        }
    </style>
    """

    @classmethod
    def generate_master_report(cls, model: ScientificTableModel) -> str:
        """Generates a comprehensive scientific results ledger containing Descriptive Statistics,
        One-Way ANOVA with Tukey HSD post-hoc tests, Two-Way ANOVA, Kaplan-Meier Survival Analysis,
        and t-Test comparisons.
        """
        sheet_title = getattr(model, "sheet_name", getattr(model, "name", "Current Sheet"))
        html = [cls.STYLESHEET_HEADER]
        html.append(f"<h2>🔬 Scientific Results Ledger — {sheet_title}</h2>")

        if not hasattr(model, "_data_frame") or model._data_frame.empty:
            html.append("<p><i>No data available in active workspace model.</i></p>")
            return "".join(html)

        cols = list(model._data_frame.columns)
        groups_dict = {}
        for col in cols:
            vec = model.get_column_data(col)
            if vec.size > 0:
                groups_dict[col] = vec

        if not groups_dict:
            html.append("<p><i>No valid numeric vectors found for statistical calculation.</i></p>")
            return "".join(html)

        # 1. Descriptive Statistics Section
        html.append("<h3>📊 Descriptive Statistics & Summary Metrics</h3>")
        html.append("<table>")
        html.append("<tr><th>Column Name</th><th>N</th><th>Mean</th><th>Std Dev</th><th>SEM</th><th>95% CI Lower</th><th>95% CI Upper</th><th>Median</th><th>Min</th><th>Max</th></tr>")

        for col_name, vec in groups_dict.items():
            res = DescriptiveStatsEngine.calculate_descriptive_stats(vec)
            if res["success"]:
                m = res["results"]
                html.append(
                    f"<tr>"
                    f"<td><b>{col_name}</b></td>"
                    f"<td>{m['count']}</td>"
                    f"<td>{m['mean']:.4f}</td>"
                    f"<td>{m['std']:.4f}</td>"
                    f"<td>{m['sem']:.4f}</td>"
                    f"<td>{m['ci_95_lower']:.4f}</td>"
                    f"<td>{m['ci_95_upper']:.4f}</td>"
                    f"<td>{m['median']:.4f}</td>"
                    f"<td>{m['min']:.4f}</td>"
                    f"<td>{m['max']:.4f}</td>"
                    f"</tr>"
                )
        html.append("</table>")

        # 2. One-Way ANOVA & Tukey HSD Section
        if len(groups_dict) >= 2:
            anova_res = AnovaEngine.calculate_one_way_anova(groups_dict)
            if anova_res["success"]:
                r = anova_res["results"]
                p_val = r["p_value"]
                ast = get_p_asterisks(p_val)
                sig_cls = "sig" if p_val < 0.05 else "ns"

                html.append("<h3>📈 One-Way Analysis of Variance (ANOVA)</h3>")
                html.append("<div class='summary-box'>")
                html.append(f"<b>Overall F-Statistic:</b> {r['f_statistic']:.4f} &nbsp;&nbsp;|&nbsp;&nbsp; ")
                html.append(f"<b>P-Value:</b> {p_val:.5e} (<span class='{sig_cls}'>{ast}</span>) &nbsp;&nbsp;|&nbsp;&nbsp; ")
                html.append(f"<b>DF:</b> Between={r['df_between']}, Within={r['df_within']}")
                html.append("</div>")

                html.append("<table>")
                html.append("<tr><th>Source of Variation</th><th>Degrees of Freedom (DF)</th><th>Sum of Squares (SS)</th><th>Mean Square (MS)</th><th>F Statistic</th><th>P Value</th></tr>")
                html.append(f"<tr><td><b>Between Groups</b></td><td>{r['df_between']}</td><td>{r['ss_between']:.4f}</td><td>{r['ms_between']:.4f}</td><td>{r['f_statistic']:.4f}</td><td><span class='{sig_cls}'>{p_val:.5e} ({ast})</span></td></tr>")
                html.append(f"<tr><td><b>Within Groups (Residual)</b></td><td>{r['df_within']}</td><td>{r['ss_within']:.4f}</td><td>{r['ms_within']:.4f}</td><td>-</td><td>-</td></tr>")
                html.append(f"<tr><td><b>Total</b></td><td>{r['df_total']}</td><td>{r['ss_total']:.4f}</td><td>-</td><td>-</td><td>-</td></tr>")
                html.append("</table>")

                # Tukey HSD Post-hoc
                tukey_list = r.get("post_hoc_tukey", [])
                if tukey_list:
                    html.append("<h3>🔍 Post-Hoc Tukey HSD Multiple Comparisons</h3>")
                    html.append("<table>")
                    html.append("<tr><th>Pairwise Comparison</th><th>Mean Difference</th><th>95% CI Lower</th><th>95% CI Upper</th><th>P Value</th><th>Summary</th></tr>")
                    for t in tukey_list:
                        p_t = t["p_value"]
                        ast_t = get_p_asterisks(p_t)
                        cls_t = "sig" if t["significant"] else "ns"
                        html.append(
                            f"<tr>"
                            f"<td><b>{t['group1']} vs {t['group2']}</b></td>"
                            f"<td>{t['mean_difference']:.4f}</td>"
                            f"<td>{t['confidence_interval'][0]:.4f}</td>"
                            f"<td>{t['confidence_interval'][1]:.4f}</td>"
                            f"<td>{p_t:.5f}</td>"
                            f"<td><span class='{cls_t}'>{ast_t}</span></td>"
                            f"</tr>"
                        )
                    html.append("</table>")

        # 3. Two-Way ANOVA Section (If DataFrame contains at least 3 columns)
        if len(cols) >= 3:
            col_a, col_b, col_val = cols[0], cols[1], cols[2]
            anova_2w = TwoWayAnovaEngine.calculate_two_way_anova(model._data_frame, col_a, col_b, col_val)
            if anova_2w["success"]:
                r2 = anova_2w["results"]
                fa, fb, fab = r2["factor_a"], r2["factor_b"], r2["interaction"]
                res_err, tot = r2["residual"], r2["total"]

                html.append(f"<h3>📊 Two-Way Analysis of Variance ({fa['name']} x {fb['name']})</h3>")
                html.append("<table>")
                html.append("<tr><th>Source of Variation</th><th>DF</th><th>Sum of Squares (SS)</th><th>Mean Square (MS)</th><th>F Statistic</th><th>P Value</th></tr>")
                
                for factor_item in [fa, fb, fab]:
                    p_f = factor_item["p_value"]
                    ast_f = get_p_asterisks(p_f)
                    cls_f = "sig" if p_f < 0.05 else "ns"
                    html.append(
                        f"<tr>"
                        f"<td><b>{factor_item['name']}</b></td>"
                        f"<td>{factor_item['df']}</td>"
                        f"<td>{factor_item['ss']:.4f}</td>"
                        f"<td>{factor_item['ms']:.4f}</td>"
                        f"<td>{factor_item['f_statistic']:.4f}</td>"
                        f"<td><span class='{cls_f}'>{p_f:.5e} ({ast_f})</span></td>"
                        f"</tr>"
                    )

                html.append(f"<tr><td><b>Residual (Error)</b></td><td>{res_err['df']}</td><td>{res_err['ss']:.4f}</td><td>{res_err['ms']:.4f}</td><td>-</td><td>-</td></tr>")
                html.append(f"<tr><td><b>Total</b></td><td>{tot['df']}</td><td>{tot['ss']:.4f}</td><td>-</td><td>-</td><td>-</td></tr>")
                html.append("</table>")

        # 4. Kaplan-Meier Survival Analysis Section
        time_col = None
        event_col = None
        for c in cols:
            c_lower = str(c).lower()
            if "time" in c_lower or "day" in c_lower or "month" in c_lower or c_lower == "x":
                time_col = c
            elif "event" in c_lower or "status" in c_lower or "censored" in c_lower or "y1" in c_lower:
                event_col = c

        if time_col and event_col and time_col != event_col:
            t_data = model.get_column_data(time_col)
            e_data = model.get_column_data(event_col)
            min_len = min(len(t_data), len(e_data))
            if min_len >= 2:
                km_res = KaplanMeierEngine.calculate_kaplan_meier(t_data[:min_len], e_data[:min_len])
                if km_res["success"]:
                    km_sum = km_res["summary"]
                    km_rows = km_res["results"]["survival_table"]

                    html.append(f"<h3>⏳ Kaplan-Meier Survival Analysis ({time_col} vs {event_col})</h3>")
                    html.append("<div class='summary-box'>")
                    html.append(f"<b>Total Subjects (N):</b> {km_sum['n_total']} &nbsp;&nbsp;|&nbsp;&nbsp; ")
                    html.append(f"<b>Events:</b> {km_sum['total_events']} &nbsp;&nbsp;|&nbsp;&nbsp; ")
                    html.append(f"<b>Censored:</b> {km_sum['total_censored']} &nbsp;&nbsp;|&nbsp;&nbsp; ")
                    html.append(f"<b>Median Survival Time:</b> {km_sum['median_survival_time']}")
                    html.append("</div>")

                    html.append("<table>")
                    html.append("<tr><th>Time</th><th>At Risk</th><th>Events</th><th>Censored</th><th>Survival Probability S(t)</th><th>Std Error (Greenwood)</th><th>95% CI Lower</th><th>95% CI Upper</th><th>Cum. Hazard H(t)</th></tr>")

                    for r in km_rows:
                        hazard_str = f"{r['cum_hazard']:.4f}" if not math.isnan(r['cum_hazard']) else "-"
                        html.append(
                            f"<tr>"
                            f"<td><b>{r['time']:.2f}</b></td>"
                            f"<td>{r['at_risk']}</td>"
                            f"<td>{r['events']}</td>"
                            f"<td>{r['censored']}</td>"
                            f"<td>{r['survival_probability']:.4f}</td>"
                            f"<td>{r['std_error']:.4f}</td>"
                            f"<td>{r['ci_95_lower']:.4f}</td>"
                            f"<td>{r['ci_95_upper']:.4f}</td>"
                            f"<td>{hazard_str}</td>"
                            f"</tr>"
                        )
                    html.append("</table>")

        # 5. Pairwise t-Test Summary (if 2 numeric columns)
        numeric_cols = list(groups_dict.keys())
        if len(numeric_cols) == 2:
            col_a, col_b = numeric_cols[0], numeric_cols[1]
            t_res = TTestEngine.calculate_unpaired_t_test(groups_dict[col_a], groups_dict[col_b], equal_var=True)
            if t_res["success"]:
                tr = t_res["results"]
                p_t = tr["p_value"]
                ast_t = get_p_asterisks(p_t)
                cls_t = "sig" if p_t < 0.05 else "ns"

                html.append(f"<h3>📊 Two-Sample Unpaired t-Test ({col_a} vs {col_b})</h3>")
                html.append("<table>")
                html.append("<tr><th>Parameter</th><th>Value</th></tr>")
                html.append(f"<tr><td>Mean Difference ({col_a} - {col_b})</td><td>{tr['mean_difference']:.4f}</td></tr>")
                html.append(f"<tr><td>Standard Error of Difference</td><td>{tr['standard_error_difference']:.4f}</td></tr>")
                html.append(f"<tr><td>t Statistic</td><td>{tr['t_statistic']:.4f}</td></tr>")
                html.append(f"<tr><td>Degrees of Freedom (DF)</td><td>{tr['degrees_of_freedom']:.1f}</td></tr>")
                html.append(f"<tr><td>P Value (Two-tailed)</td><td><span class='{cls_t}'>{p_t:.5f} ({ast_t})</span></td></tr>")
                html.append(f"<tr><td>95% Confidence Interval</td><td>({tr['confidence_interval'][0]:.4f}, {tr['confidence_interval'][1]:.4f})</td></tr>")
                html.append("</table>")

        return "".join(html)
