"""
VibePad Schism GraphPad Prism 10 Style "Analyze Data" Dialog.
Licensed under GPLv3.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QListWidget, QListWidgetItem, QPushButton, QDialogButtonBox, QSplitter,
    QWidget, QLineEdit
)
from PyQt6.QtCore import Qt
from src.data_engine.table_model import ScientificTableModel


class AnalyzeDataDialog(QDialog):
    """
    Modal dialog mimicking GraphPad Prism 10's 'Analyze Data' hub workflow.
    Left Pane: Categorized tree of scientific analyses.
    Right Pane: Checkbox list of available data sets / columns.
    """
    def __init__(self, model: ScientificTableModel = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Analyze Data")
        self.resize(750, 500)
        self.model = model

        self.init_ui()
        if self.model:
            self.populate_columns(self.model)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Top banner label
        top_bar = QHBoxLayout()
        use_label = QLabel("<b>Use:</b> Built-in analysis")
        use_label.setStyleSheet("font-size: 13px; color: #e0e0e0;")
        top_bar.addWidget(use_label)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Main Horizontal Splitter (Left: Which Analysis? | Right: Data sets)
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # --- Left Pane: Which Analysis? ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_label = QLabel("<b>Which analysis?</b>")
        left_label.setStyleSheet("font-size: 13px; color: #ffffff;")
        left_layout.addWidget(left_label)

        # Search filter
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search analysis...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #0284c7;
            }
        """)
        self.search_input.textChanged.connect(self.filter_tree)
        left_layout.addWidget(self.search_input)

        # Analysis Category Tree
        self.analysis_tree = QTreeWidget()
        self.analysis_tree.setHeaderHidden(True)
        self.analysis_tree.setAnimated(True)
        self.analysis_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 12px;
                padding: 4px;
            }
            QTreeWidget::item {
                height: 24px;
                border-radius: 3px;
                padding-left: 4px;
                color: #ffffff;
            }
            QTreeWidget::item:hover {
                background-color: #383838;
                color: #ffffff;
            }
            QTreeWidget::item:selected {
                background-color: #0284c7;
                color: #ffffff;
                font-weight: bold;
            }
        """)
        self.populate_analyses_tree()
        left_layout.addWidget(self.analysis_tree)

        self.splitter.addWidget(left_widget)

        # --- Right Pane: Which Data Sets? ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_label = QLabel("<b>Analyze which data sets?</b>")
        right_label.setStyleSheet("font-size: 13px; color: #ffffff;")
        right_layout.addWidget(right_label)

        table_display_name = getattr(self.model, "sheet_name", "Current Data Table") if self.model else "Data Table"
        self.table_name_label = QLabel(f"<b>Table:</b> {table_display_name}")
        self.table_name_label.setStyleSheet("font-size: 12px; color: #cbd5e1;")
        right_layout.addWidget(self.table_name_label)

        # Checkbox Column List
        self.column_list = QListWidget()
        self.column_list.setStyleSheet("""
            QListWidget {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                font-size: 12px;
                padding: 4px;
            }
            QListWidget::item {
                height: 26px;
                padding-left: 4px;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #383838;
                color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #0284c7;
                color: #ffffff;
            }
        """)
        right_layout.addWidget(self.column_list)

        # Select All / Deselect All Buttons
        btn_select_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setFixedHeight(28)
        self.select_all_btn.clicked.connect(self.select_all_columns)
        btn_select_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.setFixedHeight(28)
        self.deselect_all_btn.clicked.connect(self.deselect_all_columns)
        btn_select_layout.addWidget(self.deselect_all_btn)

        right_layout.addLayout(btn_select_layout)

        self.splitter.addWidget(right_widget)
        self.splitter.setSizes([420, 330])

        layout.addWidget(self.splitter)

        # Bottom QDialogButtonBox (OK / Cancel)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def populate_analyses_tree(self):
        """Populates the analysis categories matching Prism 10 structure."""
        self.analysis_tree.clear()

        # 1. Transform, Normalize...
        cat_transform = QTreeWidgetItem(self.analysis_tree, ["Transform, Normalize..."])
        QTreeWidgetItem(cat_transform, ["Transform"])
        QTreeWidgetItem(cat_transform, ["Transform concentrations (X)"])
        QTreeWidgetItem(cat_transform, ["Normalize"])
        QTreeWidgetItem(cat_transform, ["Prune rows"])
        QTreeWidgetItem(cat_transform, ["Remove baseline and column math"])

        # 2. XY analyses
        cat_xy = QTreeWidgetItem(self.analysis_tree, ["XY analyses"])
        QTreeWidgetItem(cat_xy, ["Nonlinear regression (curve fit)"])
        QTreeWidgetItem(cat_xy, ["Simple linear regression"])
        QTreeWidgetItem(cat_xy, ["Simple logistic regression"])
        QTreeWidgetItem(cat_xy, ["Fit spline/LOWESS"])
        QTreeWidgetItem(cat_xy, ["Smooth, differentiate or integrate curve"])
        QTreeWidgetItem(cat_xy, ["Area under curve"])
        QTreeWidgetItem(cat_xy, ["Deming (Model II) linear regression"])

        # 3. Column analyses
        cat_col = QTreeWidgetItem(self.analysis_tree, ["Column analyses"])
        QTreeWidgetItem(cat_col, ["t tests (and nonparametric tests)"])
        QTreeWidgetItem(cat_col, ["One-way ANOVA (and nonparametric tests)"])
        QTreeWidgetItem(cat_col, ["One sample t and Wilcoxon test"])
        QTreeWidgetItem(cat_col, ["Descriptive statistics"])
        QTreeWidgetItem(cat_col, ["Normality and Lognormality Tests"])
        QTreeWidgetItem(cat_col, ["Frequency distribution"])

        # 4. Grouped analyses
        cat_grp = QTreeWidgetItem(self.analysis_tree, ["Grouped analyses"])
        QTreeWidgetItem(cat_grp, ["Two-way ANOVA (or mixed model)"])
        QTreeWidgetItem(cat_grp, ["Three-way ANOVA (or mixed model)"])
        QTreeWidgetItem(cat_grp, ["Row statistics"])
        QTreeWidgetItem(cat_grp, ["Multiple t tests (and nonparametric tests)"])

        # Expand key categories
        for cat in [cat_transform, cat_xy, cat_col, cat_grp]:
            font = cat.font(0)
            font.setBold(True)
            cat.setFont(0, font)
            cat.setExpanded(True)

        # Select "t tests (and nonparametric tests)" by default
        child_ttest = cat_col.child(0)
        if child_ttest:
            self.analysis_tree.setCurrentItem(child_ttest)

    def filter_tree(self, text: str):
        """Filters tree items based on search input."""
        query = text.strip().lower()
        for i in range(self.analysis_tree.topLevelItemCount()):
            top = self.analysis_tree.topLevelItem(i)
            top_match = False
            for j in range(top.childCount()):
                child = top.child(j)
                if not query or query in child.text(0).lower():
                    child.setHidden(False)
                    top_match = True
                else:
                    child.setHidden(True)
            top.setHidden(not top_match)

    def populate_columns(self, model: ScientificTableModel):
        """Populates checked data set column list from ScientificTableModel."""
        self.column_list.clear()
        if not hasattr(model, "_data_frame") or model._data_frame.empty:
            return

        cols = list(model._data_frame.columns)

        letter_idx = 0
        for col_name in cols:
            # Skip X column by default if X is independent variable
            if str(col_name).upper() == "X":
                continue

            prefix = chr(ord('A') + letter_idx)
            letter_idx += 1
            display_text = f"{prefix}:{col_name}"

            item = QListWidgetItem(display_text, self.column_list)
            item.setData(Qt.ItemDataRole.UserRole, col_name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)

    def select_all_columns(self):
        for i in range(self.column_list.count()):
            self.column_list.item(i).setCheckState(Qt.CheckState.Checked)

    def deselect_all_columns(self):
        for i in range(self.column_list.count()):
            self.column_list.item(i).setCheckState(Qt.CheckState.Unchecked)

    def get_selected_analysis_name(self) -> str:
        """Returns the name string of the selected analysis item."""
        current = self.analysis_tree.currentItem()
        if current:
            return current.text(0)
        return ""

    def get_selected_column_names(self) -> list:
        """Returns a list of raw column name strings that are currently checked."""
        selected = []
        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                col_name = item.data(Qt.ItemDataRole.UserRole)
                selected.append(col_name)
        return selected
