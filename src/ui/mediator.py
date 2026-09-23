"""
VibePad Schism Core Component Mediator.

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

import os
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QTableWidgetItem, QInputDialog
from src.data_engine.table_model import ScientificTableModel
from src.ui.table_view import ScientificTableWidget
from src.ui.plot_canvas import ScientificPlotCanvas
from src.analysis.curve_fitting import CurveFittingEngine, dose_response_model
from src.analysis.t_test import TTestEngine
from src.analysis.anova_engine import AnovaEngine
from src.analysis.anova_two_way import TwoWayAnovaEngine
from src.analysis.survival_engine import KaplanMeierEngine
from src.analysis.kruskal_wallis import KruskalWallisEngine
from src.analysis.exponential_decay import ExponentialDecayEngine, one_phase_decay, one_phase_association
from src.analysis.michaelis_menten import MichaelisMentenEngine, michaelis_menten_model
from src.analysis.outliers_engine import OutliersEngine
from src.analysis.bland_altman import BlandAltmanEngine
from src.analysis.rm_anova import RepeatedMeasuresAnovaEngine
from src.analysis.roc_engine import RocEngine
from src.analysis.logistic_regression import LogisticRegressionEngine
from src.analysis.nested_anova import NestedAnovaEngine
from src.analysis.linear_regression import LinearRegressionEngine
from src.analysis.one_sample_test import OneSampleTestEngine
from src.data_engine.file_handler import ScientificFileHandler
from src.data_engine.prism_parser import PrismParser, PrismParseError

from src.ui.navigation_tree import ScientificNavigationTree
from src.ui.analyze_dialog import AnalyzeDataDialog
from src.analysis.report_generator import ScientificReportGenerator


class WorkspaceMediator:
    """Core Event Mediator coordinating interactions between UI views and backend scientific engines.

    Decouples `ScientificTableWidget`, `ScientificPlotCanvas`, `ScientificNavigationTree`, and
    `QTextBrowser` results views, routing data updates, sheet model switching, statistical hypothesis
    testing execution, real-time curve fitting triggers, and disk workspace persistence.
    """

    def __init__(
        self,
        model: ScientificTableModel,
        table: ScientificTableWidget,
        canvas: ScientificPlotCanvas,
        tree: ScientificNavigationTree = None,
        center_stack = None,
        results_browser = None
    ) -> None:
        """Initializes the component event mediator and links UI signals.

        Args:
            model (ScientificTableModel): Active spreadsheet data model.
            table (ScientificTableWidget): Spreadsheet table grid widget.
            canvas (ScientificPlotCanvas): Real-time plot canvas widget.
            tree (ScientificNavigationTree, optional): Sidebar navigation tree widget. Defaults to None.
            center_stack (QStackedWidget, optional): Central stacked workspace pane widget. Defaults to None.
            results_browser (QTextBrowser, optional): HTML results ledger browser widget. Defaults to None.
        """
        self.model = model
        self.table = table
        self.canvas = canvas
        self.tree = tree
        self.center_stack = center_stack
        self.results_browser = results_browser

        # Connect spreadsheet grid update signal to mediator data synchronization slot
        self.table.cellChanged.connect(self.sync_data_to_visualization)
        if hasattr(self.table, "column_header_renamed"):
            self.table.column_header_renamed.connect(self.handle_column_header_renamed)

        # Connect sidebar navigation tree selection signals
        if self.tree:
            self.tree.sheet_selected.connect(self.display_sheet_model)
            if hasattr(self.tree, "navigation_selected"):
                self.tree.navigation_selected.connect(self.handle_navigation_selected)

    def handle_column_header_renamed(self, col_idx: int, old_name: str, new_name: str) -> None:
        """Re-syncs visualization canvas and HTML results browser when a column header label is modified.

        Args:
            col_idx (int): Column index renamed.
            old_name (str): Previous column title string.
            new_name (str): Updated column title string.
        """
        self.sync_data_to_visualization()
        if self.results_browser and self.center_stack and self.center_stack.currentIndex() == 1:
            report_html = ScientificReportGenerator.generate_master_report(self.model)
            self.results_browser.setHtml(report_html)

    def handle_navigation_selected(
        self, 
        target_model: ScientificTableModel, 
        node_type: str = "table", 
        sub_type: str = "xy"
    ) -> None:
        """Routes sidebar tree selection events to the appropriate workspace pane.

        Args:
            target_model (ScientificTableModel): Target sheet data model.
            node_type (str, optional): Selected node type ('table', 'results', 'graph'). Defaults to "table".
            sub_type (str, optional): Graph subtype ('xy', 'bar_chart', 'box_plot'). Defaults to "xy".
        """
        if not target_model:
            return

        if node_type == "table":
            if self.center_stack:
                self.center_stack.setCurrentIndex(0)
            self.display_sheet_model(target_model)

        elif node_type == "results":
            if self.center_stack:
                self.center_stack.setCurrentIndex(1)
            if self.results_browser:
                report_html = ScientificReportGenerator.generate_master_report(target_model)
                self.results_browser.setHtml(report_html)

        elif node_type == "graph":
            if self.center_stack:
                self.center_stack.setCurrentIndex(0)
            self.display_sheet_model(target_model)
            if sub_type == "bar_chart":
                self.canvas.render_grouped_bar_chart(target_model)
            else:
                self.sync_data_to_visualization()

    def _show_info(self, parent_window, title: str, message: str):
        if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
            return QMessageBox.StandardButton.Ok
        return QMessageBox.information(parent_window, title, message)

    def _show_warning(self, parent_window, title: str, message: str):
        if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
            return QMessageBox.StandardButton.Ok
        return QMessageBox.warning(parent_window, title, message)

    def _show_critical(self, parent_window, title: str, message: str):
        if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
            return QMessageBox.StandardButton.Ok
        return QMessageBox.critical(parent_window, title, message)

    def _update_results_ledger_and_tree(self) -> None:
        """Updates HTML results browser, switches central stacked pane to index 1,
        and synchronizes navigation tree to active sheet's Results Ledger node.
        """
        report_html = ScientificReportGenerator.generate_master_report(self.model)
        if self.results_browser:
            self.results_browser.setHtml(report_html)
        if self.center_stack:
            self.center_stack.setCurrentIndex(1)
        if self.tree and hasattr(self.tree, "select_results_node"):
            self.tree.select_results_node(self.model)

    def open_analysis_hub(self, parent_window) -> None:
        """Launches GraphPad Prism 10 style 'Analyze Data' dialog modally.

        Executes selected statistical tests or regressions on checked data set columns.

        Args:
            parent_window (QWidget): Main application window reference.
        """
        dialog = AnalyzeDataDialog(model=self.model, parent=parent_window)
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            analysis_name = dialog.get_selected_analysis_name()
            selected_cols = dialog.get_selected_column_names()

            if not analysis_name:
                self._show_warning(parent_window, "⚠️ Selection Required", "Please select an analysis from the list.")
                return

            if not selected_cols:
                self._show_warning(parent_window, "⚠️ Selection Required", "Please select at least one data set column to analyze.")
                return

            analysis_lower = analysis_name.lower()

            # Condition 1: Unpaired t tests and non-parametric comparisons
            if "t test" in analysis_lower or "t tests" in analysis_lower:
                if len(selected_cols) != 2:
                    self._show_warning(
                        parent_window,
                        "⚠️ Selection Error",
                        f"Unpaired t-test requires exactly 2 data set columns selected (you checked {len(selected_cols)})."
                    )
                    return

                col_a, col_b = selected_cols[0], selected_cols[1]
                group_a = self.model.get_column_data(col_a)
                group_b = self.model.get_column_data(col_b)

                if group_a.size < 2 or group_b.size < 2:
                    self._show_warning(
                        parent_window,
                        "⚠️ Insufficient Data",
                        f"Columns '{col_a}' and '{col_b}' must both contain at least 2 observations."
                    )
                    return

                analysis = TTestEngine.calculate_unpaired_t_test(group_a, group_b, equal_var=True)
                if not analysis["success"]:
                    self._show_critical(parent_window, "❌ Math Exception", analysis["error"])
                    return

                res = analysis["results"]
                summary_msg = (
                    f"📊 Unpaired t-Test Results ({col_a} vs {col_b})\n"
                    f"-----------------------------------------\n"
                    f"• Mean Difference: {res['mean_difference']:.4f}\n"
                    f"• Standard Error: {res['standard_error_difference']:.4f}\n"
                    f"• Degrees of Freedom: {res['degrees_of_freedom']:.1f}\n\n"
                    f"📈 Test Performance Significance\n"
                    f"-----------------------------------------\n"
                    f"• Calculated t-statistic: {res['t_statistic']:.4f}\n"
                    f"• Two-tailed P-value: {res['p_value']:.5f}\n"
                    f"• 95% Confidence Interval: ({res['confidence_interval'][0]:.4f}, {res['confidence_interval'][1]:.4f})\n\n"
                    f"ℹ️ Outcome: {'Statistically Significant (P < 0.05)' if res['p_value'] < 0.05 else 'Not Statistically Significant (P >= 0.05)'}"
                )
                self._show_info(parent_window, f"🔬 Analysis Results — {analysis_name}", summary_msg)
                self._update_results_ledger_and_tree()
                self.canvas.render_grouped_bar_chart(self.model)

            # Condition 2: One-Way ANOVA
            elif "one-way" in analysis_lower or "one way" in analysis_lower:
                groups_dict = {col: self.model.get_column_data(col) for col in selected_cols}
                analysis = AnovaEngine.calculate_one_way_anova(groups_dict)
                if not analysis["success"]:
                    self._show_critical(parent_window, "❌ Math Exception", analysis["error"])
                    return
                r = analysis["results"]
                msg = (
                    f"📊 One-Way ANOVA Results\n"
                    f"-----------------------------------------\n"
                    f"• F Statistic: {r['f_statistic']:.4f}\n"
                    f"• P-value: {r['p_value']:.5e}\n"
                    f"• DF Between: {r['df_between']}, Within: {r['df_within']}\n"
                )
                self._show_info(parent_window, "🔬 One-Way ANOVA", msg)
                self._update_results_ledger_and_tree()
                self.canvas.render_grouped_bar_chart(self.model)

            # Condition 3: Two-Way ANOVA
            elif "two-way" in analysis_lower or "two way" in analysis_lower:
                self.execute_two_way_anova(parent_window)

            # Condition 4: Kaplan-Meier Survival
            elif "survival" in analysis_lower or "kaplan" in analysis_lower:
                self.execute_kaplan_meier_survival(parent_window)

            # Condition 5: Simple Linear Regression
            elif "linear regression" in analysis_lower:
                all_cols = list(self.model._data_frame.columns)
                x_col = all_cols[0]
                x_vec = self.model.get_column_data(x_col)
                y_vec = self.model.get_column_data(selected_cols[0])
                analysis = LinearRegressionEngine.calculate_linear_regression(x_vec, y_vec)
                if not analysis["success"]:
                    self._show_critical(parent_window, "❌ Math Exception", analysis["error"])
                    return
                r = analysis["results"]
                msg = (
                    f"📈 Simple Linear Regression\n"
                    f"-----------------------------------------\n"
                    f"• Slope (Beta1): {r['slope']:.4f} ± {r['slope_se']:.4f}\n"
                    f"• Intercept (Beta0): {r['intercept']:.4f} ± {r['intercept_se']:.4f}\n"
                    f"• R-squared: {r['r_squared']:.4f}\n"
                    f"• P-value: {r['p_value']:.5e}\n"
                )
                self._show_info(parent_window, "🔬 Linear Regression", msg)
                fit_curve_y = r["slope"] * x_vec + r["intercept"]
                self.canvas.refresh_plot(x_vec, {selected_cols[0]: y_vec}, fit_curve_y=fit_curve_y)
                self._update_results_ledger_and_tree()

            # Condition 6: Kruskal-Wallis & Dunn's post-hoc
            elif "kruskal" in analysis_lower or "dunn" in analysis_lower:
                groups_dict = {col: self.model.get_column_data(col) for col in selected_cols}
                analysis = KruskalWallisEngine.calculate_kruskal_wallis(groups_dict)
                if not analysis["success"]:
                    self._show_critical(parent_window, "❌ Math Exception", analysis["error"])
                    return
                r = analysis["results"]
                msg = (
                    f"📊 Kruskal-Wallis Test Results\n"
                    f"-----------------------------------------\n"
                    f"• H Statistic: {r['h_statistic']:.4f}\n"
                    f"• Degrees of Freedom: {r['degrees_of_freedom']}\n"
                    f"• P-value: {r['p_value']:.5e}\n"
                    f"• Total N: {r['total_n']}\n"
                )
                self._show_info(parent_window, "🔬 Kruskal-Wallis ANOVA", msg)
                self._update_results_ledger_and_tree()
                self.canvas.render_grouped_bar_chart(self.model)

            # Condition 7: One-phase exponential decay / association
            elif "exponential" in analysis_lower or "decay" in analysis_lower:
                all_cols = list(self.model._data_frame.columns)
                x_col = all_cols[0]
                x_vec = self.model.get_column_data(x_col)
                y_vec = self.model.get_column_data(selected_cols[0])
                model_type = "association" if "association" in analysis_lower or "growth" in analysis_lower else "decay"
                analysis = ExponentialDecayEngine.calculate_exponential_fit(x_vec, y_vec, model_type=model_type)
                if not analysis["success"]:
                    self._show_critical(parent_window, "❌ Math Exception", analysis["error"])
                    return
                r = analysis["results"]["params"]
                msg = (
                    f"📈 Exponential {model_type.capitalize()} Fit\n"
                    f"-----------------------------------------\n"
                    f"• Y0: {r['y0']:.4f}\n"
                    f"• Plateau: {r['plateau']:.4f}\n"
                    f"• K: {r['k']:.4f}\n"
                    f"• Half-Life: {r['half_life']:.4f}\n"
                    f"• R-squared: {analysis['results']['r_squared']:.4f}\n"
                )
                self._show_info(parent_window, f"🔬 Exponential {model_type.capitalize()}", msg)
                fit_func = one_phase_association if model_type == "association" else one_phase_decay
                fit_curve_y = fit_func(x_vec, r['y0'], r['plateau'], r['k'])
                self.canvas.refresh_plot(x_vec, {selected_cols[0]: y_vec}, fit_curve_y=fit_curve_y)
                self._update_results_ledger_and_tree()

            # Condition 8: Michaelis-Menten enzyme kinetics
            elif "michaelis" in analysis_lower or "menten" in analysis_lower or "kinetics" in analysis_lower:
                all_cols = list(self.model._data_frame.columns)
                x_col = all_cols[0]
                s_vec = self.model.get_column_data(x_col)
                v_vec = self.model.get_column_data(selected_cols[0])
                analysis = MichaelisMentenEngine.calculate_michaelis_menten(s_vec, v_vec)
                if not analysis["success"]:
                    self._show_critical(parent_window, "❌ Math Exception", analysis["error"])
                    return
                r = analysis["results"]
                msg = (
                    f"🧪 Michaelis-Menten Kinetics\n"
                    f"-----------------------------------------\n"
                    f"• Vmax: {r['vmax']:.4f} ± {r['vmax_se']:.4f}\n"
                    f"• Km: {r['km']:.4f} ± {r['km_se']:.4f}\n"
                    f"• Vmax 95% CI: ({r['vmax_ci95'][0]:.4f}, {r['vmax_ci95'][1]:.4f})\n"
                    f"• Km 95% CI: ({r['km_ci95'][0]:.4f}, {r['km_ci95'][1]:.4f})\n"
                    f"• R-squared: {r['r_squared']:.4f}\n"
                )
                self._show_info(parent_window, "🔬 Michaelis-Menten Kinetics", msg)
                fit_curve_y = michaelis_menten_model(s_vec, r['vmax'], r['km'])
                self.canvas.refresh_plot(s_vec, {selected_cols[0]: v_vec}, fit_curve_y=fit_curve_y)
                self._update_results_ledger_and_tree()

            # Condition 9: ROUT & Grubbs outlier detection
            elif "outlier" in analysis_lower or "rout" in analysis_lower or "grubbs" in analysis_lower:
                y_vec = self.model.get_column_data(selected_cols[0])
                analysis = OutliersEngine.detect_outliers(y_vec)
                if not analysis["success"]:
                    self._show_critical(parent_window, "❌ Math Exception", analysis["error"])
                    return
                r_rout = analysis["results"]["rout"]
                r_grubbs = analysis["results"]["grubbs"]
                msg = (
                    f"🔍 Outlier Detection Summary ({selected_cols[0]})\n"
                    f"-----------------------------------------\n"
                    f"• ROUT (Q=1%): {r_rout['outliers_count']} outlier(s) detected\n"
                    f"• Grubbs Test: G = {r_grubbs['g_statistic']:.4f} (p = {r_grubbs['p_value']:.4f}), Outlier: {r_grubbs['is_outlier']}\n"
                )
                self._show_info(parent_window, "🔬 Outlier Detection", msg)
                self._update_results_ledger_and_tree()
                self.canvas.render_box_plot(self.model)

            # Condition 10: Bland-Altman method comparison
            elif "bland" in analysis_lower or "altman" in analysis_lower:
                if len(selected_cols) < 2:
                    self._show_warning(parent_window, "⚠️ Selection Error", "Bland-Altman analysis requires 2 selected method columns.")
                    return
                m1 = self.model.get_column_data(selected_cols[0])
                m2 = self.model.get_column_data(selected_cols[1])
                analysis = BlandAltmanEngine.calculate_bland_altman(m1, m2)
                if not analysis["success"]:
                    self._show_critical(parent_window, "❌ Math Exception", analysis["error"])
                    return
                r = analysis["results"]
                msg = (
                    f"📐 Bland-Altman Method Comparison\n"
                    f"-----------------------------------------\n"
                    f"• Bias (Mean Diff): {r['bias']:.4f} ± {r['sd_bias']:.4f}\n"
                    f"• Bias 95% CI: ({r['bias_ci95'][0]:.4f}, {r['bias_ci95'][1]:.4f})\n"
                    f"• Lower 95% LoA: {r['lower_loa']:.4f}\n"
                    f"• Upper 95% LoA: {r['upper_loa']:.4f}\n"
                )
                self._show_info(parent_window, "🔬 Bland-Altman Analysis", msg)
                self._update_results_ledger_and_tree()
                self.sync_data_to_visualization()

            # Condition 11: Repeated Measures ANOVA
            elif "repeated" in analysis_lower or "rm_anova" in analysis_lower or "rm anova" in analysis_lower:
                sub_df = self.model._data_frame[selected_cols]
                analysis = RepeatedMeasuresAnovaEngine.calculate_rm_anova(sub_df)
                if not analysis["success"]:
                    self._show_critical(parent_window, "❌ Math Exception", analysis["error"])
                    return
                r = analysis["results"]["treatment"]
                msg = (
                    f"🔄 Repeated Measures ANOVA\n"
                    f"-----------------------------------------\n"
                    f"• Treatment F: {r['f_statistic']:.4f}, p = {r['p_value']:.5e}\n"
                    f"• Geisser-Greenhouse Epsilon: {r['geisser_greenhouse_epsilon']:.4f}\n"
                    f"• Adjusted p (GG): {r['p_value_gg']:.5e}\n"
                )
                self._show_info(parent_window, "🔬 RM-ANOVA Results", msg)
                self._update_results_ledger_and_tree()
                self.canvas.render_grouped_bar_chart(self.model)

            # Condition 12: ROC curve and AUC analysis
            elif "roc" in analysis_lower or "auc" in analysis_lower:
                if len(selected_cols) < 2:
                    self._show_warning(parent_window, "⚠️ Selection Error", "ROC analysis requires 2 columns (Binary Outcome, Score).")
                    return
                y_true = self.model.get_column_data(selected_cols[0])
                y_score = self.model.get_column_data(selected_cols[1])
                analysis = RocEngine.calculate_roc_analysis(y_true, y_score)
                if not analysis["success"]:
                    self._show_critical(parent_window, "❌ Math Exception", analysis["error"])
                    return
                r = analysis["results"]
                msg = (
                    f"📈 ROC Curve & AUC Analysis\n"
                    f"-----------------------------------------\n"
                    f"• Area Under Curve (AUC): {r['auc']:.4f} ± {r['auc_se']:.4f}\n"
                    f"• AUC 95% CI: ({r['auc_ci95'][0]:.4f}, {r['auc_ci95'][1]:.4f})\n"
                    f"• P-value (vs 0.5): {r['p_value']:.5e}\n"
                    f"• Youden J Index: {r['youden_j']:.4f} (Optimal Threshold: {r['optimal_threshold']})\n"
                )
                self._show_info(parent_window, "🔬 ROC Curve Analysis", msg)
                self._update_results_ledger_and_tree()
                self.sync_data_to_visualization()

            # Condition 13: Simple binary logistic regression
            elif "logistic" in analysis_lower:
                if len(selected_cols) < 2:
                    self._show_warning(parent_window, "⚠️ Selection Error", "Logistic regression requires 2 columns (Predictor X, Binary Y).")
                    return
                x_vec = self.model.get_column_data(selected_cols[0])
                y_vec = self.model.get_column_data(selected_cols[1])
                analysis = LogisticRegressionEngine.calculate_logistic_regression(x_vec, y_vec)
                if not analysis["success"]:
                    self._show_critical(parent_window, "❌ Math Exception", analysis["error"])
                    return
                r = analysis["results"]
                msg = (
                    f"📊 Binary Logistic Regression\n"
                    f"-----------------------------------------\n"
                    f"• Intercept: {r['intercept']:.4f}\n"
                    f"• Slope (Beta1): {r['slope']:.4f} (p = {r['p_value']:.5e})\n"
                    f"• Odds Ratio (OR): {r['odds_ratio']:.4f}\n"
                    f"• OR 95% CI: ({r['odds_ratio_ci95'][0]:.4f}, {r['odds_ratio_ci95'][1]:.4f})\n"
                    f"• Pseudo R-squared: {r['pseudo_r2']:.4f}\n"
                )
                self._show_info(parent_window, "🔬 Logistic Regression", msg)
                self._update_results_ledger_and_tree()
                self.sync_data_to_visualization()

            # Condition 14: Nested one-way ANOVA
            elif "nested" in analysis_lower:
                cols = list(self.model._data_frame.columns)
                if len(cols) < 3:
                    self._show_warning(parent_window, "⚠️ Selection Error", "Nested ANOVA requires 3 columns (Group, Subgroup, Value).")
                    return
                analysis = NestedAnovaEngine.calculate_nested_anova(self.model._data_frame, cols[0], cols[1], cols[2])
                if not analysis["success"]:
                    self._show_critical(parent_window, "❌ Math Exception", analysis["error"])
                    return
                rg = analysis["results"]["group"]
                rsub = analysis["results"]["subgroup_nested"]
                msg = (
                    f"🌳 Nested One-Way ANOVA\n"
                    f"-----------------------------------------\n"
                    f"• Top Group F: {rg['f_statistic']:.4f} (p = {rg['p_value']:.5e})\n"
                    f"• Subgroup (Nested) F: {rsub['f_statistic']:.4f} (p = {rsub['p_value']:.5e})\n"
                )
                self._show_info(parent_window, "🔬 Nested ANOVA", msg)
                self._update_results_ledger_and_tree()
                self.canvas.render_grouped_bar_chart(self.model)

            # Condition 15: Non-linear regression curve fitting
            elif "nonlinear" in analysis_lower or "curve fit" in analysis_lower or "regression" in analysis_lower:
                self.sync_data_to_visualization()
                self._update_results_ledger_and_tree()
                self._show_info(
                    parent_window,
                    "📈 Curve Fitting Executed",
                    f"Nonlinear regression curve fitting updated for data sets: {', '.join(selected_cols)}"
                )

            # Fallback for other analytical options
            else:
                self._update_results_ledger_and_tree()
                self.canvas.render_grouped_bar_chart(self.model)
                self._show_info(
                    parent_window,
                    f"🔬 Analysis Selected: {analysis_name}",
                    f"Selected analysis '{analysis_name}' on data sets: {', '.join(selected_cols)}"
                )

    def display_sheet_model(self, target_model: ScientificTableModel) -> None:
        """Swaps active workspace dataset to target_model and populates table grid items.

        SIGNAL UNHOOKING RATIONALE:
            Disconnects `cellChanged` signal before clearing and populating table cells,
            and reconnects it after population. This prevents event cascades during bulk table updates.

        Args:
            target_model (ScientificTableModel): Model instance to render.
        """
        if not target_model:
            return

        self.model.table_type = target_model.table_type
        self.model.sheet_name = getattr(target_model, "sheet_name", "Selected Sheet")
        self.model.name = getattr(target_model, "name", self.model.sheet_name)
        self.model._data_frame = target_model._data_frame

        # Disconnect cell update signal to prevent recursive cellChanged cascades during bulk item insertion
        try:
            self.table.cellChanged.disconnect(self.sync_data_to_visualization)
        except (TypeError, RuntimeError):
            pass

        self.table.clearContents()

        cols = list(self.model._data_frame.columns)
        self.table.setRowCount(len(self.model._data_frame) + 50)
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)

        # Map DataFrame values into table grid items
        for row in self.model._data_frame.index:
            for col_idx, col_name in enumerate(cols):
                val = self.model._data_frame.at[row, col_name]
                if pd.isna(val) or str(val).lower() == "nan":
                    continue
                self.table.setItem(row, col_idx, QTableWidgetItem(str(val)))

        # Reconnect cell update signal and refresh canvas visualization
        self.table.cellChanged.connect(self.sync_data_to_visualization)
        self.sync_data_to_visualization()

    def sync_data_to_visualization(self, row: int = None, column: int = None) -> None:
        """Extracts data vectors for all columns, executes non-linear regression, and updates plot canvas.

        Args:
            row (int, optional): Edited row index. Defaults to None.
            column (int, optional): Edited column index. Defaults to None.
        """
        if not hasattr(self.model, "_data_frame") or self.model._data_frame.empty:
            return

        all_cols = list(self.model._data_frame.columns)
        x_col = None
        for c in all_cols:
            if str(c).upper() == "X":
                x_col = c
                break

        if not x_col:
            x_col = all_cols[0]

        x_data = self.model.get_column_data(x_col)
        if x_data.size < 1:
            return

        y_datasets_dict = {}
        for c in all_cols:
            if c != x_col:
                y_vec = self.model.get_column_data(c)
                if y_vec.size == x_data.size:
                    y_datasets_dict[c] = y_vec

        if not y_datasets_dict:
            return

        # Perform real-time 4-parameter logistic curve fitting on primary Y column
        fit_curve_y = None
        primary_y_col = "Y1" if "Y1" in y_datasets_dict else list(y_datasets_dict.keys())[0]
        y_primary = y_datasets_dict[primary_y_col]

        if x_data.size >= 3 and y_primary.size == x_data.size:
            fit_result = CurveFittingEngine.fit_dose_response(x_data, y_primary)
            if fit_result["success"]:
                params = fit_result["params"]
                fit_curve_y = dose_response_model(
                    x_data, 
                    params["bottom"], 
                    params["top"], 
                    params["log_ec50"]
                )

        # Update plot canvas axis titles dynamically from active model column headers
        y_title_str = ", ".join([str(k) for k in y_datasets_dict.keys()]) if y_datasets_dict else "Dependent Variable (Y-Axis)"
        self.canvas.set_axis_titles(x_title=str(x_col), y_title=y_title_str)

        # Update plot canvas graphics items
        self.canvas.refresh_plot(x_data, y_datasets_dict, fit_curve_y=fit_curve_y)

    def execute_workspace_t_test(self, parent_window) -> None:
        """Extracts replicate datasets (Y1 vs Y2) and computes independent t-test statistics.

        Args:
            parent_window (QWidget): Main window reference for dialog parenting.
        """
        group_a = self.model.get_column_data("Y1")
        group_b = self.model.get_column_data("Y2")

        if group_a.size < 2 or group_b.size < 2:
            self._show_warning(
                parent_window, 
                "⚠️ Insufficient Vectors", 
                "To compute an unpaired t-test, columns Y1 and Y2 must both contain at least 2 observations."
            )
            return

        analysis = TTestEngine.calculate_unpaired_t_test(group_a, group_b, equal_var=True)

        if not analysis["success"]:
            self._show_critical(parent_window, "❌ Math Exception", analysis["error"])
            return

        res = analysis["results"]
        summary_msg = (
            f"📊 Unpaired t-Test Summary Metrics\n"
            f"-----------------------------------------\n"
            f"• Mean Difference: {res['mean_difference']:.4f}\n"
            f"• Standard Error: {res['standard_error_difference']:.4f}\n"
            f"• Degrees of Freedom: {res['degrees_of_freedom']:.1f}\n\n"
            f"📈 Test Performance Significance\n"
            f"-----------------------------------------\n"
            f"• Calculated t-statistic: {res['t_statistic']:.4f}\n"
            f"• Two-tailed P-value: {res['p_value']:.5f}\n"
            f"• 95% Confidence Interval: ({res['confidence_interval'][0]:.4f}, {res['confidence_interval'][1]:.4f})\n\n"
            f"ℹ️ Outcome: {'Statistically Significant (P < 0.05)' if res['p_value'] < 0.05 else 'Not Statistically Significant (P >= 0.05)'}"
        )
        self._show_info(parent_window, "🔬 Analysis Results", summary_msg)
        self._update_results_ledger_and_tree()
        self.canvas.render_grouped_bar_chart(self.model)

    def execute_two_way_anova(self, parent_window) -> None:
        """Executes Two-Way ANOVA analysis on the active spreadsheet model if >= 3 columns exist.

        Args:
            parent_window (QWidget): Main window reference for dialog parenting.
        """
        cols = list(self.model._data_frame.columns)
        if len(cols) < 3:
            self._show_warning(
                parent_window,
                "⚠️ Insufficient Columns",
                "Two-Way ANOVA requires at least 3 columns (Factor A, Factor B, Value)."
            )
            return

        col_a, col_b, col_val = cols[0], cols[1], cols[2]
        analysis = TwoWayAnovaEngine.calculate_two_way_anova(
            self.model._data_frame, col_a, col_b, col_val
        )

        if not analysis["success"]:
            self._show_critical(parent_window, "❌ Math Exception", analysis["error"])
            return

        r = analysis["results"]
        fa, fb, fab = r["factor_a"], r["factor_b"], r["interaction"]
        summary_msg = (
            f"📊 Two-Way ANOVA Summary ({col_a} x {col_b})\n"
            f"-----------------------------------------\n"
            f"• Factor A ({col_a}): F = {fa['f_statistic']:.4f}, p = {fa['p_value']:.5e}\n"
            f"• Factor B ({col_b}): F = {fb['f_statistic']:.4f}, p = {fb['p_value']:.5e}\n"
            f"• Interaction ({col_a} x {col_b}): F = {fab['f_statistic']:.4f}, p = {fab['p_value']:.5e}\n"
        )
        self._show_info(parent_window, "🔬 Two-Way ANOVA Results", summary_msg)
        self._update_results_ledger_and_tree()
        self.canvas.render_grouped_bar_chart(self.model)

    def execute_kaplan_meier_survival(self, parent_window) -> None:
        """Executes Kaplan-Meier Survival Analysis on the active spreadsheet model.

        Args:
            parent_window (QWidget): Main window reference for dialog parenting.
        """
        cols = list(self.model._data_frame.columns)
        time_col = None
        event_col = None
        for c in cols:
            c_lower = str(c).lower()
            if "time" in c_lower or "day" in c_lower or "month" in c_lower or c_lower == "x":
                time_col = c
            elif "event" in c_lower or "status" in c_lower or "censored" in c_lower or "y1" in c_lower:
                event_col = c

        if time_col is None and len(cols) > 0:
            time_col = cols[0]
        if event_col is None and len(cols) > 1:
            event_col = cols[1]

        if not time_col or not event_col:
            self._show_warning(
                parent_window,
                "⚠️ Insufficient Columns",
                "Kaplan-Meier survival analysis requires Time and Event columns."
            )
            return

        time_data = self.model.get_column_data(time_col)
        event_data = self.model.get_column_data(event_col)

        analysis = KaplanMeierEngine.calculate_kaplan_meier(time_data, event_data)

        if not analysis["success"]:
            self._show_critical(parent_window, "❌ Math Exception", analysis["error"])
            return

        summary = analysis["summary"]
        median_val = summary.get("median_survival", np.nan)
        median_str = f"{median_val:.2f}" if (median_val is not None and not np.isnan(median_val)) else "Undefined"
        summary_msg = (
            f"⏳ Kaplan-Meier Survival Analysis Summary\n"
            f"-----------------------------------------\n"
            f"• Total Subjects: {summary['n_total']}\n"
            f"• Total Events: {summary['total_events']}\n"
            f"• Total Censored: {summary['total_censored']}\n"
            f"• Estimated Median Survival Time: {median_str}\n"
        )
        self._show_info(parent_window, "🔬 Kaplan-Meier Results", summary_msg)
        self._update_results_ledger_and_tree()
        self.canvas.render_kaplan_meier_survival(analysis["results"])

    def save_workspace_to_disk(self, parent_window, filepath: str = None, silent: bool = False) -> None:
        """Exports workspace models to CSV or compressed .schism archive format.

        Args:
            parent_window (QWidget): Main window parent.
            filepath (str, optional): Target file path. If None, launches QFileDialog. Defaults to None.
            silent (bool, optional): If True, suppresses success/error popups. Defaults to False.
        """
        if not filepath:
            filepath, selected_filter = QFileDialog.getSaveFileName(
                parent_window,
                "Save Matrix Data Workspace",
                "",
                "VibePad Schism Workspace (*.schism);;CSV Spreadsheet (*.csv)"
            )
            if not filepath:
                return

            if "schism" in selected_filter.lower() and not filepath.lower().endswith(".schism"):
                filepath += ".schism"

        if not filepath:
            return

        all_models = [self.model]
        if self.tree:
            # Extract models from root table tree items if available
            tree_models = []
            for i in range(self.tree.root_tables.childCount()):
                m = self.tree.root_tables.child(i).data(0, self.tree.MODEL_ROLE)
                if m:
                    tree_models.append(m)
            if tree_models:
                all_models = tree_models

        if filepath.lower().endswith(".schism"):
            status = ScientificFileHandler.export_to_schism(all_models, filepath, self.canvas.style_map)
        else:
            status = ScientificFileHandler.export_to_csv(self.model, filepath)

        if status:
            if hasattr(parent_window, "current_filepath"):
                parent_window.current_filepath = filepath
            if hasattr(parent_window, "update_recent_files_menu"):
                parent_window.update_recent_files_menu()

            if not silent:
                self._show_info(parent_window, "💾 Success", f"Workspace dataset successfully saved to:\n{filepath}")
        else:
            if not silent:
                self._show_critical(parent_window, "❌ Error", "Failed to write data safely to local disk path.")

    def load_workspace_from_disk(self, parent_window) -> None:
        """Triggers a native file open dialog to load CSV spreadsheets or Schism archives.

        Args:
            parent_window (QWidget): Main window reference.
        """
        filepath, _ = QFileDialog.getOpenFileName(
            parent_window,
            "Open Experimental Spreadsheet",
            "",
            "VibePad Schism Workspace (*.schism);;CSV Spreadsheet (*.csv)"
        )
        if filepath:
            self.open_recent_filepath(parent_window, filepath)

    def load_schism_workspace(self, parent_window, filepath: str = None) -> None:
        """Loads a compressed .schism archive format file, restoring multi-sheet models.

        Args:
            parent_window (QWidget): Main window reference.
            filepath (str, optional): Target .schism archive file path. Defaults to None.
        """
        if not filepath:
            filepath, _ = QFileDialog.getOpenFileName(
                parent_window,
                "Open Schism Archive",
                "",
                "VibePad Schism Workspace (*.schism);;CSV Spreadsheet (*.csv)"
            )
        if not filepath:
            return

        models = ScientificFileHandler.import_from_schism(filepath)
        if not models:
            self._show_warning(parent_window, "⚠️ Load Error", f"Failed to load .schism archive:\n{filepath}")
            return

        if hasattr(parent_window, "current_filepath"):
            parent_window.current_filepath = filepath
        if hasattr(parent_window, "update_recent_files_menu"):
            parent_window.update_recent_files_menu()

        if self.tree:
            self.tree.populate_models(models)
        else:
            self.display_sheet_model(models[0])

        self._show_info(parent_window, "📂 Schism Archive Loaded", f"Successfully loaded {len(models)} sheet(s) from archive.")

    def open_recent_filepath(self, parent_window, filepath: str) -> None:
        """Opens a file path from the recent files menu, routing by extension (.schism, .prism, .csv).

        Args:
            parent_window (QWidget): Main window reference.
            filepath (str): Absolute file path to open.
        """
        if not os.path.exists(filepath):
            self._show_warning(
                parent_window,
                "⚠️ File Not Found",
                f"The requested file path could not be found on disk:\n{filepath}"
            )
            return

        if filepath.lower().endswith(".schism"):
            self.load_schism_workspace(parent_window, filepath=filepath)
        elif filepath.lower().endswith(".prism"):
            # Load Prism workspace archive from path
            try:
                models = PrismParser.parse(filepath)
                if models:
                    if hasattr(parent_window, "current_filepath"):
                        parent_window.current_filepath = filepath
                    if hasattr(parent_window, "update_recent_files_menu"):
                        parent_window.update_recent_files_menu()
                    if self.tree:
                        self.tree.populate_models(models)
                    else:
                        self.display_sheet_model(models[0])
            except Exception as exc:
                self._show_critical(parent_window, "❌ Error", f"Failed to open Prism archive:\n{str(exc)}")
        else:
            loaded_model = ScientificFileHandler.import_from_csv(filepath, table_type="XY")
            if hasattr(parent_window, "current_filepath"):
                parent_window.current_filepath = filepath
            if hasattr(parent_window, "update_recent_files_menu"):
                parent_window.update_recent_files_menu()
            if self.tree:
                self.tree.populate_models([loaded_model])
            else:
                self.display_sheet_model(loaded_model)

    def load_prism_workspace(self, parent_window) -> None:
        """Loads a native GraphPad Prism 10 (.prism) archive file.

        Populates all extracted sheet models into the navigation tree pane.

        Args:
            parent_window (QWidget): Main application window parent.
        """
        filepath, _ = QFileDialog.getOpenFileName(
            parent_window,
            "Open GraphPad Prism Archive",
            "",
            "GraphPad Prism Archives (*.prism)"
        )
        if not filepath:
            return

        try:
            models = PrismParser.parse(filepath)
        except PrismParseError as exc:
            self._show_warning(
                parent_window,
                "⚠️ Parse Error",
                f"Failed to parse Prism archive:\n{str(exc)}"
            )
            return
        except Exception as exc:
            self._show_critical(
                parent_window,
                "❌ Error",
                f"Unexpected error reading file:\n{str(exc)}"
            )
            return

        if not models:
            self._show_warning(
                parent_window,
                "⚠️ Empty Archive",
                "The selected Prism archive does not contain any valid data sheets."
            )
            return

        if self.tree:
            self.tree.populate_models(models)
        else:
            if len(models) == 1:
                target_model = models[0]
            else:
                sheet_names = [
                    getattr(m, "sheet_name", getattr(m, "name", f"Sheet {i+1}"))
                    for i, m in enumerate(models)
                ]
                selected_name, ok = QInputDialog.getItem(
                    parent_window,
                    "Select Prism Sheet",
                    "Multiple sheets detected in archive. Choose a sheet to load:",
                    sheet_names,
                    0,
                    False
                )
                if not ok or not selected_name:
                    return
                selected_idx = sheet_names.index(selected_name)
                target_model = models[selected_idx]
            self.display_sheet_model(target_model)

        self._show_info(
            parent_window,
            "📂 Prism Archive Loaded",
            f"Successfully loaded {len(models)} sheet(s) from Prism archive."
        )
