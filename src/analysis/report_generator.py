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
    def _build_descriptive_table(cls, groups_dict: dict) -> str:
        """Helper to build standard Descriptive Statistics HTML table for a given dictionary of column vectors."""
        html = ["<div style='margin-top: 6px; margin-bottom: 4px; color: #38bdf8; font-weight: bold;'>📊 Descriptive Statistics Summary</div>"]
        html.append("<table>")
        html.append("<tr><th>Column Name</th><th>N</th><th>Mean</th><th>Std Dev</th><th>SEM</th><th>95% CI Lower</th><th>95% CI Upper</th></tr>")
        for col_name, vec in groups_dict.items():
            if vec is None or len(vec) == 0:
                continue
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
                    f"</tr>"
                )
        html.append("</table>")
        return "".join(html)

    @classmethod
    def format_t_test_report(cls, col_a: str, col_b: str, res: dict, group_a=None, group_b=None) -> str:
        """Formats Unpaired t-Test results into a GraphPad Prism style HTML block."""
        p_val = res.get("p_value", 1.0)
        ast = get_p_asterisks(p_val)
        sig_cls = "sig" if p_val < 0.05 else "ns"
        ci = res.get("confidence_interval", (0.0, 0.0))

        html = ["<div class='analysis-entry' style='margin-top: 20px; border-top: 1px solid #3d3d3d; padding-top: 10px;'>"]
        html.append(f"<h3>📊 Two-Sample Unpaired t-Test ({col_a} vs {col_b})</h3>")
        
        if group_a is not None and group_b is not None:
            html.append(cls._build_descriptive_table({col_a: group_a, col_b: group_b}))

        html.append("<div class='summary-box'>")
        html.append(f"<b>t-Statistic:</b> {res.get('t_statistic', 0.0):.4f} &nbsp;&nbsp;|&nbsp;&nbsp; ")
        html.append(f"<b>P-Value:</b> {p_val:.5f} (<span class='{sig_cls}'>{ast}</span>) &nbsp;&nbsp;|&nbsp;&nbsp; ")
        html.append(f"<b>Degrees of Freedom:</b> {res.get('degrees_of_freedom', 0.0):.1f}")
        html.append("</div>")

        html.append("<table>")
        html.append("<tr><th>Parameter</th><th>Value</th></tr>")
        html.append(f"<tr><td>Mean Difference ({col_a} - {col_b})</td><td>{res.get('mean_difference', 0.0):.4f}</td></tr>")
        html.append(f"<tr><td>Standard Error of Difference</td><td>{res.get('standard_error_difference', 0.0):.4f}</td></tr>")
        html.append(f"<tr><td>t Statistic</td><td>{res.get('t_statistic', 0.0):.4f}</td></tr>")
        html.append(f"<tr><td>Degrees of Freedom (DF)</td><td>{res.get('degrees_of_freedom', 0.0):.1f}</td></tr>")
        html.append(f"<tr><td>P Value (Two-tailed)</td><td><span class='{sig_cls}'>{p_val:.5f} ({ast})</span></td></tr>")
        html.append(f"<tr><td>95% Confidence Interval</td><td>({ci[0]:.4f}, {ci[1]:.4f})</td></tr>")
        html.append("</table>")
        html.append("</div>")
        return "".join(html)

    @classmethod
    def format_one_way_anova_report(cls, groups_dict: dict, r: dict) -> str:
        """Formats One-Way ANOVA and Tukey HSD results into a GraphPad Prism style HTML block."""
        p_val = r.get("p_value", 1.0)
        ast = get_p_asterisks(p_val)
        sig_cls = "sig" if p_val < 0.05 else "ns"

        html = ["<div class='analysis-entry' style='margin-top: 20px; border-top: 1px solid #3d3d3d; padding-top: 10px;'>"]
        html.append("<h3>📈 One-Way Analysis of Variance (ANOVA)</h3>")

        if groups_dict:
            html.append(cls._build_descriptive_table(groups_dict))

        html.append("<div class='summary-box'>")
        html.append(f"<b>Overall F-Statistic:</b> {r.get('f_statistic', 0.0):.4f} &nbsp;&nbsp;|&nbsp;&nbsp; ")
        html.append(f"<b>P-Value:</b> {p_val:.5e} (<span class='{sig_cls}'>{ast}</span>) &nbsp;&nbsp;|&nbsp;&nbsp; ")
        html.append(f"<b>DF:</b> Between={r.get('df_between', 0)}, Within={r.get('df_within', 0)}")
        html.append("</div>")

        html.append("<table>")
        html.append("<tr><th>Source of Variation</th><th>Degrees of Freedom (DF)</th><th>Sum of Squares (SS)</th><th>Mean Square (MS)</th><th>F Statistic</th><th>P Value</th></tr>")
        html.append(f"<tr><td><b>Between Groups</b></td><td>{r.get('df_between', 0)}</td><td>{r.get('ss_between', 0.0):.4f}</td><td>{r.get('ms_between', 0.0):.4f}</td><td>{r.get('f_statistic', 0.0):.4f}</td><td><span class='{sig_cls}'>{p_val:.5e} ({ast})</span></td></tr>")
        html.append(f"<tr><td><b>Within Groups (Residual)</b></td><td>{r.get('df_within', 0)}</td><td>{r.get('ss_within', 0.0):.4f}</td><td>{r.get('ms_within', 0.0):.4f}</td><td>-</td><td>-</td></tr>")
        html.append(f"<tr><td><b>Total</b></td><td>{r.get('df_total', 0)}</td><td>{r.get('ss_total', 0.0):.4f}</td><td>-</td><td>-</td><td>-</td></tr>")
        html.append("</table>")

        tukey_list = r.get("post_hoc_tukey", [])
        if tukey_list:
            html.append("<h3>🔍 Post-Hoc Tukey HSD Multiple Comparisons</h3>")
            html.append("<table>")
            html.append("<tr><th>Pairwise Comparison</th><th>Mean Difference</th><th>95% CI Lower</th><th>95% CI Upper</th><th>P Value</th><th>Summary</th></tr>")
            for t in tukey_list:
                p_t = t.get("p_value", 1.0)
                ast_t = get_p_asterisks(p_t)
                cls_t = "sig" if t.get("significant", False) else "ns"
                ci = t.get("confidence_interval", (0.0, 0.0))
                html.append(
                    f"<tr>"
                    f"<td><b>{t.get('group1', '')} vs {t.get('group2', '')}</b></td>"
                    f"<td>{t.get('mean_difference', 0.0):.4f}</td>"
                    f"<td>{ci[0]:.4f}</td>"
                    f"<td>{ci[1]:.4f}</td>"
                    f"<td>{p_t:.5f}</td>"
                    f"<td><span class='{cls_t}'>{ast_t}</span></td>"
                    f"</tr>"
                )
            html.append("</table>")
        html.append("</div>")
        return "".join(html)

    @classmethod
    def format_two_way_anova_report(cls, col_a: str, col_b: str, col_val: str, r2: dict, groups_dict: dict = None) -> str:
        """Formats Two-Way ANOVA results into a GraphPad Prism style HTML block."""
        fa, fb, fab = r2["factor_a"], r2["factor_b"], r2["interaction"]
        res_err, tot = r2["residual"], r2["total"]

        html = ["<div class='analysis-entry' style='margin-top: 20px; border-top: 1px solid #3d3d3d; padding-top: 10px;'>"]
        html.append(f"<h3>📊 Two-Way Analysis of Variance ({fa.get('name', col_a)} x {fb.get('name', col_b)})</h3>")

        if groups_dict:
            html.append(cls._build_descriptive_table(groups_dict))

        html.append("<table>")
        html.append("<tr><th>Source of Variation</th><th>DF</th><th>Sum of Squares (SS)</th><th>Mean Square (MS)</th><th>F Statistic</th><th>P Value</th></tr>")
        
        for factor_item in [fa, fb, fab]:
            p_f = factor_item.get("p_value", 1.0)
            ast_f = get_p_asterisks(p_f)
            cls_f = "sig" if p_f < 0.05 else "ns"
            html.append(
                f"<tr>"
                f"<td><b>{factor_item.get('name', '')}</b></td>"
                f"<td>{factor_item.get('df', 0)}</td>"
                f"<td>{factor_item.get('ss', 0.0):.4f}</td>"
                f"<td>{factor_item.get('ms', 0.0):.4f}</td>"
                f"<td>{factor_item.get('f_statistic', 0.0):.4f}</td>"
                f"<td><span class='{cls_f}'>{p_f:.5e} ({ast_f})</span></td>"
                f"</tr>"
            )

        html.append(f"<tr><td><b>Residual (Error)</b></td><td>{res_err.get('df', 0)}</td><td>{res_err.get('ss', 0.0):.4f}</td><td>{res_err.get('ms', 0.0):.4f}</td><td>-</td><td>-</td></tr>")
        html.append(f"<tr><td><b>Total</b></td><td>{tot.get('df', 0)}</td><td>{tot.get('ss', 0.0):.4f}</td><td>-</td><td>-</td><td>-</td></tr>")
        html.append("</table>")
        html.append("</div>")
        return "".join(html)

    @classmethod
    def format_kaplan_meier_report(cls, time_col: str, event_col: str, km_results: dict, km_sum: dict, groups_dict: dict = None) -> str:
        """Formats Kaplan-Meier Survival Analysis results into a GraphPad Prism style HTML block."""
        km_rows = km_results.get("survival_table", [])
        html = ["<div class='analysis-entry' style='margin-top: 20px; border-top: 1px solid #3d3d3d; padding-top: 10px;'>"]
        html.append(f"<h3>⏳ Kaplan-Meier Survival Analysis ({time_col} vs {event_col})</h3>")
        
        if groups_dict:
            html.append(cls._build_descriptive_table(groups_dict))

        html.append("<div class='summary-box'>")
        html.append(f"<b>Total Subjects (N):</b> {km_sum.get('n_total', 0)} &nbsp;&nbsp;|&nbsp;&nbsp; ")
        html.append(f"<b>Events:</b> {km_sum.get('total_events', 0)} &nbsp;&nbsp;|&nbsp;&nbsp; ")
        html.append(f"<b>Censored:</b> {km_sum.get('total_censored', 0)} &nbsp;&nbsp;|&nbsp;&nbsp; ")
        med_val = km_sum.get("median_survival_time", km_sum.get("median_survival", "Undefined"))
        html.append(f"<b>Median Survival Time:</b> {med_val}")
        html.append("</div>")

        html.append("<table>")
        html.append("<tr><th>Time</th><th>At Risk</th><th>Events</th><th>Censored</th><th>Survival Probability S(t)</th><th>Std Error (Greenwood)</th><th>95% CI Lower</th><th>95% CI Upper</th><th>Cum. Hazard H(t)</th></tr>")

        for r in km_rows:
            hazard_str = f"{r.get('cum_hazard', 0.0):.4f}" if ('cum_hazard' in r and not math.isnan(r['cum_hazard'])) else "-"
            html.append(
                f"<tr>"
                f"<td><b>{r.get('time', 0.0):.2f}</b></td>"
                f"<td>{r.get('at_risk', 0)}</td>"
                f"<td>{r.get('events', 0)}</td>"
                f"<td>{r.get('censored', 0)}</td>"
                f"<td>{r.get('survival_probability', 0.0):.4f}</td>"
                f"<td>{r.get('std_error', 0.0):.4f}</td>"
                f"<td>{r.get('ci_95_lower', 0.0):.4f}</td>"
                f"<td>{r.get('ci_95_upper', 0.0):.4f}</td>"
                f"<td>{hazard_str}</td>"
                f"</tr>"
            )
        html.append("</table>")
        html.append("</div>")
        return "".join(html)

    @classmethod
    def format_linear_regression_report(cls, x_col: str, y_col: str, r: dict, groups_dict: dict = None) -> str:
        """Formats Simple Linear Regression results into HTML block."""
        p_val = r.get("p_value", 1.0)
        ast = get_p_asterisks(p_val)
        sig_cls = "sig" if p_val < 0.05 else "ns"
        html = ["<div class='analysis-entry' style='margin-top: 20px; border-top: 1px solid #3d3d3d; padding-top: 10px;'>"]
        html.append(f"<h3>📈 Simple Linear Regression ({x_col} vs {y_col})</h3>")
        if groups_dict:
            html.append(cls._build_descriptive_table(groups_dict))
        html.append("<table>")
        html.append("<tr><th>Parameter</th><th>Value</th></tr>")
        html.append(f"<tr><td>Slope (Beta1)</td><td>{r.get('slope', 0.0):.4f} ± {r.get('slope_se', 0.0):.4f}</td></tr>")
        html.append(f"<tr><td>Intercept (Beta0)</td><td>{r.get('intercept', 0.0):.4f} ± {r.get('intercept_se', 0.0):.4f}</td></tr>")
        html.append(f"<tr><td>R-squared</td><td>{r.get('r_squared', 0.0):.4f}</td></tr>")
        html.append(f"<tr><td>P-value</td><td><span class='{sig_cls}'>{p_val:.5e} ({ast})</span></td></tr>")
        html.append("</table>")
        html.append("</div>")
        return "".join(html)

    @classmethod
    def format_kruskal_wallis_report(cls, groups_dict: dict, r: dict) -> str:
        """Formats Kruskal-Wallis non-parametric ANOVA results into HTML block."""
        p_val = r.get("p_value", 1.0)
        ast = get_p_asterisks(p_val)
        sig_cls = "sig" if p_val < 0.05 else "ns"
        html = ["<div class='analysis-entry' style='margin-top: 20px; border-top: 1px solid #3d3d3d; padding-top: 10px;'>"]
        html.append("<h3>📊 Kruskal-Wallis Non-Parametric Test</h3>")
        if groups_dict:
            html.append(cls._build_descriptive_table(groups_dict))
        html.append("<div class='summary-box'>")
        html.append(f"<b>H Statistic:</b> {r.get('h_statistic', 0.0):.4f} &nbsp;&nbsp;|&nbsp;&nbsp; ")
        html.append(f"<b>Degrees of Freedom:</b> {r.get('degrees_of_freedom', 0)} &nbsp;&nbsp;|&nbsp;&nbsp; ")
        html.append(f"<b>P-Value:</b> {p_val:.5e} (<span class='{sig_cls}'>{ast}</span>)")
        html.append("</div>")
        html.append("</div>")
        return "".join(html)

    @classmethod
    def format_exponential_report(cls, x_col: str, y_col: str, model_type: str, r_fit: dict, groups_dict: dict = None) -> str:
        """Formats Exponential Decay/Association curve fit results into HTML block."""
        params = r_fit.get("params", {})
        html = ["<div class='analysis-entry' style='margin-top: 20px; border-top: 1px solid #3d3d3d; padding-top: 10px;'>"]
        html.append(f"<h3>📈 One-Phase Exponential {model_type.capitalize()} ({x_col} vs {y_col})</h3>")
        if groups_dict:
            html.append(cls._build_descriptive_table(groups_dict))
        html.append("<table>")
        html.append("<tr><th>Parameter</th><th>Value</th></tr>")
        html.append(f"<tr><td>Y0</td><td>{params.get('y0', 0.0):.4f}</td></tr>")
        html.append(f"<tr><td>Plateau</td><td>{params.get('plateau', 0.0):.4f}</td></tr>")
        html.append(f"<tr><td>K</td><td>{params.get('k', 0.0):.4f}</td></tr>")
        html.append(f"<tr><td>Half-Life</td><td>{params.get('half_life', 0.0):.4f}</td></tr>")
        html.append(f"<tr><td>R-squared</td><td>{r_fit.get('r_squared', 0.0):.4f}</td></tr>")
        html.append("</table>")
        html.append("</div>")
        return "".join(html)

    @classmethod
    def format_michaelis_menten_report(cls, x_col: str, y_col: str, r: dict, groups_dict: dict = None) -> str:
        """Formats Michaelis-Menten kinetics results into HTML block."""
        vmax_ci = r.get("vmax_ci95", (0.0, 0.0))
        km_ci = r.get("km_ci95", (0.0, 0.0))
        html = ["<div class='analysis-entry' style='margin-top: 20px; border-top: 1px solid #3d3d3d; padding-top: 10px;'>"]
        html.append(f"<h3>🧪 Michaelis-Menten Enzyme Kinetics ({x_col} vs {y_col})</h3>")
        if groups_dict:
            html.append(cls._build_descriptive_table(groups_dict))
        html.append("<table>")
        html.append("<tr><th>Parameter</th><th>Value</th><th>95% CI</th></tr>")
        html.append(f"<tr><td>Vmax</td><td>{r.get('vmax', 0.0):.4f} ± {r.get('vmax_se', 0.0):.4f}</td><td>({vmax_ci[0]:.4f}, {vmax_ci[1]:.4f})</td></tr>")
        html.append(f"<tr><td>Km</td><td>{r.get('km', 0.0):.4f} ± {r.get('km_se', 0.0):.4f}</td><td>({km_ci[0]:.4f}, {km_ci[1]:.4f})</td></tr>")
        html.append(f"<tr><td>R-squared</td><td colspan='2'>{r.get('r_squared', 0.0):.4f}</td></tr>")
        html.append("</table>")
        html.append("</div>")
        return "".join(html)

    @classmethod
    def format_outliers_report(cls, col_name: str, res_outliers: dict, groups_dict: dict = None) -> str:
        """Formats Outlier Detection results into HTML block."""
        r_rout = res_outliers.get("rout", {})
        r_grubbs = res_outliers.get("grubbs", {})
        html = ["<div class='analysis-entry' style='margin-top: 20px; border-top: 1px solid #3d3d3d; padding-top: 10px;'>"]
        html.append(f"<h3>🔍 Outlier Detection Summary ({col_name})</h3>")
        if groups_dict:
            html.append(cls._build_descriptive_table(groups_dict))
        html.append("<table>")
        html.append("<tr><th>Method</th><th>Result / Outlier Count</th></tr>")
        html.append(f"<tr><td>ROUT (Q=1%)</td><td>{r_rout.get('outliers_count', 0)} outlier(s) detected</td></tr>")
        html.append(f"<tr><td>Grubbs Test</td><td>G = {r_grubbs.get('g_statistic', 0.0):.4f} (p = {r_grubbs.get('p_value', 1.0):.4f}), Outlier: {r_grubbs.get('is_outlier', False)}</td></tr>")
        html.append("</table>")
        html.append("</div>")
        return "".join(html)

    @classmethod
    def format_bland_altman_report(cls, col_a: str, col_b: str, r: dict, groups_dict: dict = None) -> str:
        """Formats Bland-Altman method comparison results into HTML block."""
        b_ci = r.get("bias_ci95", (0.0, 0.0))
        html = ["<div class='analysis-entry' style='margin-top: 20px; border-top: 1px solid #3d3d3d; padding-top: 10px;'>"]
        html.append(f"<h3>📐 Bland-Altman Method Comparison ({col_a} vs {col_b})</h3>")
        if groups_dict:
            html.append(cls._build_descriptive_table(groups_dict))
        html.append("<table>")
        html.append("<tr><th>Metric</th><th>Value</th></tr>")
        html.append(f"<tr><td>Bias (Mean Diff)</td><td>{r.get('bias', 0.0):.4f} ± {r.get('sd_bias', 0.0):.4f}</td></tr>")
        html.append(f"<tr><td>Bias 95% CI</td><td>({b_ci[0]:.4f}, {b_ci[1]:.4f})</td></tr>")
        html.append(f"<tr><td>Lower 95% LoA</td><td>{r.get('lower_loa', 0.0):.4f}</td></tr>")
        html.append(f"<tr><td>Upper 95% LoA</td><td>{r.get('upper_loa', 0.0):.4f}</td></tr>")
        html.append("</table>")
        html.append("</div>")
        return "".join(html)

    @classmethod
    def format_rm_anova_report(cls, selected_cols: list, r_full: dict, groups_dict: dict = None) -> str:
        """Formats Repeated Measures ANOVA results into HTML block."""
        r = r_full.get("treatment", {})
        p_val = r.get("p_value", 1.0)
        ast = get_p_asterisks(p_val)
        sig_cls = "sig" if p_val < 0.05 else "ns"
        html = ["<div class='analysis-entry' style='margin-top: 20px; border-top: 1px solid #3d3d3d; padding-top: 10px;'>"]
        html.append(f"<h3>🔄 Repeated Measures ANOVA ({', '.join(selected_cols)})</h3>")
        if groups_dict:
            html.append(cls._build_descriptive_table(groups_dict))
        html.append("<table>")
        html.append("<tr><th>Source</th><th>F Statistic</th><th>P Value</th><th>Geisser-Greenhouse Epsilon</th><th>GG Adjusted P</th></tr>")
        html.append(f"<tr><td>Treatment</td><td>{r.get('f_statistic', 0.0):.4f}</td><td><span class='{sig_cls}'>{p_val:.5e} ({ast})</span></td><td>{r.get('geisser_greenhouse_epsilon', 1.0):.4f}</td><td>{r.get('p_value_gg', p_val):.5e}</td></tr>")
        html.append("</table>")
        html.append("</div>")
        return "".join(html)

    @classmethod
    def format_roc_report(cls, col_true: str, col_score: str, r: dict, groups_dict: dict = None) -> str:
        """Formats ROC curve & AUC results into HTML block."""
        auc_ci = r.get("auc_ci95", (0.0, 0.0))
        p_val = r.get("p_value", 1.0)
        ast = get_p_asterisks(p_val)
        sig_cls = "sig" if p_val < 0.05 else "ns"
        html = ["<div class='analysis-entry' style='margin-top: 20px; border-top: 1px solid #3d3d3d; padding-top: 10px;'>"]
        html.append(f"<h3>📈 ROC Curve & AUC Analysis ({col_true} vs {col_score})</h3>")
        if groups_dict:
            html.append(cls._build_descriptive_table(groups_dict))
        html.append("<table>")
        html.append("<tr><th>Parameter</th><th>Value</th></tr>")
        html.append(f"<tr><td>Area Under Curve (AUC)</td><td>{r.get('auc', 0.0):.4f} ± {r.get('auc_se', 0.0):.4f}</td></tr>")
        html.append(f"<tr><td>AUC 95% CI</td><td>({auc_ci[0]:.4f}, {auc_ci[1]:.4f})</td></tr>")
        html.append(f"<tr><td>P-value (vs 0.5)</td><td><span class='{sig_cls}'>{p_val:.5e} ({ast})</span></td></tr>")
        html.append(f"<tr><td>Youden J Index</td><td>{r.get('youden_j', 0.0):.4f} (Optimal Cutoff: {r.get('optimal_threshold', '-')})</td></tr>")
        html.append("</table>")
        html.append("</div>")
        return "".join(html)

    @classmethod
    def format_logistic_regression_report(cls, col_x: str, col_y: str, r: dict, groups_dict: dict = None) -> str:
        """Formats Binary Logistic Regression results into HTML block."""
        or_ci = r.get("odds_ratio_ci95", (0.0, 0.0))
        p_val = r.get("p_value", 1.0)
        ast = get_p_asterisks(p_val)
        sig_cls = "sig" if p_val < 0.05 else "ns"
        html = ["<div class='analysis-entry' style='margin-top: 20px; border-top: 1px solid #3d3d3d; padding-top: 10px;'>"]
        html.append(f"<h3>📊 Binary Logistic Regression ({col_x} vs {col_y})</h3>")
        if groups_dict:
            html.append(cls._build_descriptive_table(groups_dict))
        html.append("<table>")
        html.append("<tr><th>Parameter</th><th>Value</th></tr>")
        html.append(f"<tr><td>Intercept</td><td>{r.get('intercept', 0.0):.4f}</td></tr>")
        html.append(f"<tr><td>Slope (Beta1)</td><td>{r.get('slope', 0.0):.4f} (p = <span class='{sig_cls}'>{p_val:.5e} ({ast})</span>)</td></tr>")
        html.append(f"<tr><td>Odds Ratio (OR)</td><td>{r.get('odds_ratio', 0.0):.4f} (95% CI: {or_ci[0]:.4f}, {or_ci[1]:.4f})</td></tr>")
        html.append(f"<tr><td>Pseudo R-squared</td><td>{r.get('pseudo_r2', 0.0):.4f}</td></tr>")
        html.append("</table>")
        html.append("</div>")
        return "".join(html)

    @classmethod
    def format_nested_anova_report(cls, cols: list, r_full: dict, groups_dict: dict = None) -> str:
        """Formats Hierarchical Nested ANOVA results into HTML block."""
        rg = r_full.get("group", {})
        rsub = r_full.get("subgroup_nested", {})
        p_g = rg.get("p_value", 1.0)
        p_sub = rsub.get("p_value", 1.0)
        html = ["<div class='analysis-entry' style='margin-top: 20px; border-top: 1px solid #3d3d3d; padding-top: 10px;'>"]
        html.append(f"<h3>🌳 Nested One-Way ANOVA ({', '.join(cols[:3])})</h3>")
        if groups_dict:
            html.append(cls._build_descriptive_table(groups_dict))
        html.append("<table>")
        html.append("<tr><th>Level</th><th>F Statistic</th><th>P Value</th></tr>")
        html.append(f"<tr><td>Top Group</td><td>{rg.get('f_statistic', 0.0):.4f}</td><td>{p_g:.5e}</td></tr>")
        html.append(f"<tr><td>Subgroup (Nested)</td><td>{rsub.get('f_statistic', 0.0):.4f}</td><td>{p_sub:.5e}</td></tr>")
        html.append("</table>")
        html.append("</div>")
        return "".join(html)

    @classmethod
    def generate_master_report(cls, model: ScientificTableModel) -> str:
        """Generates a dynamic scientific results ledger containing baseline Descriptive Statistics
        and chronologically appends all stored analysis results from model.analysis_history.
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

        if groups_dict:
            # 1. Baseline Descriptive Statistics Section
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
        else:
            html.append("<p><i>No valid numeric vectors found for statistical calculation.</i></p>")

        # 2. Append Chronological Dynamic Analysis History
        history = getattr(model, "analysis_history", [])
        if history:
            for entry in history:
                if isinstance(entry, dict):
                    block = entry.get("html_block") or entry.get("html", "")
                    ts = entry.get("timestamp", "")
                    anchor_id = entry.get("anchor_id", "")
                    # Inject HTML anchor so QTextBrowser.scrollToAnchor() can target this entry
                    if anchor_id:
                        html.append(f"<a id=\"{anchor_id}\"></a>")
                    if ts and ts not in block and "Executed" not in block:
                        ts_badge = f"<div style='color: #0284c7; font-size: 11px; font-weight: bold; margin-top: 16px; margin-bottom: -10px;'>⏱️ Executed: {ts}</div>"
                        html.append(ts_badge)
                    html.append(block)
                else:
                    html.append(str(entry))

        return "".join(html)
