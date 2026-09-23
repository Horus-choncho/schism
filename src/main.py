"""
VibePad Schism Main Application Bootstrap.
Licensed under GPLv3.
"""

import sys
import os

# Guarantee the project root remains visible across all nested imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QToolBar, QSplitter,
    QStackedWidget, QTextBrowser
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence, QIcon

from src.data_engine.table_model import ScientificTableModel
from src.data_engine.file_handler import ScientificFileHandler
from src.ui.table_view import ScientificTableWidget
from src.ui.plot_canvas import ScientificPlotCanvas
from src.ui.navigation_tree import ScientificNavigationTree
from src.ui.mediator import WorkspaceMediator


GLOBAL_DARK_STYLESHEET = """
/* Master Dark Mode Application Theme */
QMainWindow, QDialog, QWidget {
    background-color: #2d2d2d;
    color: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
}

QLabel {
    color: #ffffff;
}

QMenuBar {
    background-color: #252525;
    color: #ffffff;
    border-bottom: 1px solid #3d3d3d;
}

QMenuBar::item {
    background-color: transparent;
    color: #ffffff;
    padding: 4px 8px;
}

QMenuBar::item:selected {
    background-color: #383838;
}

QMenu {
    background-color: #252525;
    color: #ffffff;
    border: 1px solid #3d3d3d;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px 6px 28px; /* Dedicated gutter for icons/emojis */
    color: #ffffff;
    border-radius: 2px;
}

QMenu::item:selected {
    background-color: #0284c7;
    color: #ffffff;
}

QToolBar {
    background-color: #252525;
    border-bottom: 1px solid #3d3d3d;
    spacing: 8px;
    padding: 2px 6px;
}

QToolButton {
    background-color: transparent;
    color: #ffffff;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 13px;
}

QToolButton:hover {
    background-color: #383838;
    border: 1px solid #4a4a4a;
}

QToolButton:pressed {
    background-color: #0284c7;
}

QSplitter::handle {
    background-color: #3d3d3d;
}

QSplitter::handle:hover {
    background-color: #0284c7;
}

QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 4px 8px;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
}

QComboBox {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 2px 8px;
    min-height: 24px;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #0284c7;
}

QPushButton {
    background-color: #3a3a3a;
    color: #ffffff;
    border: 1px solid #4f4f4f;
    border-radius: 4px;
    padding: 5px 12px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #4a4a4a;
    border-color: #606060;
}

QPushButton:pressed {
    background-color: #0284c7;
    border-color: #0284c7;
}

QPushButton:disabled {
    background-color: #262626;
    color: #666666;
    border-color: #333333;
}

QTreeWidget, QListWidget {
    background-color: #252525;
    color: #ffffff;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    outline: 0;
    padding: 2px;
}

QTreeWidget::item, QListWidget::item {
    height: 30px;
    padding: 4px 8px;
    margin: 1px 0px;
    color: #ffffff;
}

QTreeWidget::item:hover, QListWidget::item:hover {
    background-color: #383838;
    color: #ffffff;
}

QTreeWidget::item:selected, QListWidget::item:selected {
    background-color: #0284c7;
    color: #ffffff;
    font-weight: bold;
}
"""


class VibePadSchismMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VibePad Schism (Development Build)")
        logo_path = os.path.join(os.path.dirname(__file__), "ui", "logo.png")
        if not os.path.exists(logo_path):
            logo_path = "src/ui/logo.png"
        self.setWindowIcon(QIcon(logo_path))
        self.resize(1280, 800)
        self.current_filepath = None
        self.setStyleSheet(GLOBAL_DARK_STYLESHEET)
        self.init_interface_shell()

    def init_interface_shell(self):
        """Assembles the three-pane interface layout shell using QSplitter containers."""
        # 1. Initialize the master menu bar layout across the top layout boundary
        menubar = self.menuBar()
        file_menu = menubar.addMenu("📁  File")

        open_action = QAction("Open Workspace (.csv)...", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.trigger_open_file)
        file_menu.addAction(open_action)

        open_schism_action = QAction("📁  Open Schism Archive (.schism)...", self)
        open_schism_action.triggered.connect(self.trigger_open_schism_file)
        file_menu.addAction(open_schism_action)

        open_prism_action = QAction("📂  Open GraphPad Archive (.prism)...", self)
        open_prism_action.triggered.connect(self.trigger_open_prism_file)
        file_menu.addAction(open_prism_action)

        # Open Recent Sub-menu
        self.recent_menu = file_menu.addMenu("📂  Open Recent")
        self.update_recent_files_menu()

        file_menu.addSeparator()

        new_workspace_action = QAction("📄  Create New Workspace (.schism)", self)
        new_workspace_action.setShortcut(QKeySequence("Ctrl+N"))
        new_workspace_action.triggered.connect(lambda: self.mediator.create_new_workspace(self))
        file_menu.addAction(new_workspace_action)

        file_menu.addSeparator()

        quick_save_action = QAction("Save (Quick Save)", self)
        quick_save_action.setShortcut(QKeySequence.StandardKey.Save)
        quick_save_action.triggered.connect(self.trigger_quick_save)
        file_menu.addAction(quick_save_action)

        save_as_action = QAction("Save Workspace As...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self.trigger_save_file)
        file_menu.addAction(save_as_action)

        # 2. Add our statistical analysis toolbar strip
        self.toolbar = QToolBar("Analysis Tools", self)
        self.addToolBar(self.toolbar)

        analyze_action = QAction("🔬  Analyze Data...", self)
        analyze_action.setToolTip("Open GraphPad Prism style Analyze Data Hub")
        analyze_action.triggered.connect(self.trigger_open_analysis_hub)
        self.toolbar.addAction(analyze_action)

        self.toolbar.addSeparator()

        ttest_action = QAction("📊  Quick t-Test (Y1 vs Y2)", self)
        ttest_action.triggered.connect(self.trigger_workspace_t_test)
        self.toolbar.addAction(ttest_action)

        anova_action = QAction("📊  Run Two-Way ANOVA", self)
        anova_action.triggered.connect(self.trigger_two_way_anova)
        self.toolbar.addAction(anova_action)

        survival_action = QAction("⏳  Compute Kaplan-Meier Survival", self)
        survival_action.triggered.connect(self.trigger_kaplan_meier)
        self.toolbar.addAction(survival_action)

        # 3. Main container & layout setup
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_vertical_layout = QVBoxLayout(central_widget)
        main_vertical_layout.setContentsMargins(6, 6, 6, 6)

        # 4. Foundational data core layer
        self.data_model = ScientificTableModel(table_type="XY")

        # 5. Three-Pane Splitter & Stacked Viewpane Construction
        self.outer_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.inner_splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Build visual sub-widget structures
        self.nav_tree = ScientificNavigationTree(parent=self)
        self.table_widget = ScientificTableWidget(self.data_model, parent=self)
        self.plot_canvas = ScientificPlotCanvas(parent=self)

        # Scientific Results Ledger Sheet View (Panel 2)
        self.results_browser = QTextBrowser(self)
        self.results_browser.setReadOnly(True)
        self.results_browser.setOpenExternalLinks(True)
        self.results_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 10px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
        """)

        # Central Stacked Viewpane (Panel 1: Spreadsheet Table | Panel 2: Results Ledger Sheet)
        self.center_stack = QStackedWidget(self)
        self.center_stack.addWidget(self.table_widget)      # Index 0
        self.center_stack.addWidget(self.results_browser)   # Index 1

        # Assemble inner splitter (Center Stacked Pane | Right Plot Canvas)
        self.inner_splitter.addWidget(self.center_stack)
        self.inner_splitter.addWidget(self.plot_canvas)
        self.inner_splitter.setSizes([300, 700])
        self.inner_splitter.setCollapsible(0, True)
        self.inner_splitter.setCollapsible(1, True)

        # Assemble outer splitter (Left Tree Sidebar | Inner Splitter)
        self.outer_splitter.addWidget(self.nav_tree)
        self.outer_splitter.addWidget(self.inner_splitter)
        self.outer_splitter.setSizes([200, 1000])
        self.outer_splitter.setCollapsible(0, True)
        self.outer_splitter.setCollapsible(1, True)

        main_vertical_layout.addWidget(self.outer_splitter)

        # 6. Bind objects securely using our Mediator router
        self.mediator = WorkspaceMediator(
            model=self.data_model,
            table=self.table_widget,
            canvas=self.plot_canvas,
            tree=self.nav_tree,
            center_stack=self.center_stack,
            results_browser=self.results_browser
        )

        # 7. Populate initial workspace model in navigation tree
        self.nav_tree.populate_models([self.data_model])

    def update_recent_files_menu(self):
        """Dynamically populates the Open Recent sub-menu from ~/.config/vibepad_schism/recent_files.txt."""
        self.recent_menu.clear()
        recent_paths = ScientificFileHandler.get_recent_files()

        if not recent_paths:
            empty_action = QAction("No Recent Files", self)
            empty_action.setEnabled(False)
            self.recent_menu.addAction(empty_action)
            return

        for idx, path in enumerate(recent_paths):
            action = QAction(f"{idx + 1}. {path}", self)
            action.triggered.connect(lambda checked, p=path: self.mediator.open_recent_filepath(self, p))
            self.recent_menu.addAction(action)

    def trigger_quick_save(self):
        """Fires instant Quick Save macro (Ctrl+S) to cached path without confirmation dialogs."""
        if self.current_filepath:
            self.mediator.save_workspace_to_disk(self, filepath=self.current_filepath, silent=True)
        else:
            self.trigger_save_file()

    def trigger_open_schism_file(self):
        """Triggers loading a compressed .schism archive file."""
        self.mediator.load_schism_workspace(self)

    def trigger_open_analysis_hub(self):
        """Passes Analyze Data Hub requests straight up to the Mediator loop."""
        self.mediator.open_analysis_hub(self)

    def trigger_workspace_t_test(self):
        self.mediator.execute_workspace_t_test(self)

    def trigger_two_way_anova(self):
        self.mediator.execute_two_way_anova(self)

    def trigger_kaplan_meier(self):
        self.mediator.execute_kaplan_meier_survival(self)

    def trigger_save_file(self):
        """Passes save requests straight up to the Mediator loop."""
        self.mediator.save_workspace_to_disk(self)

    def trigger_open_file(self):
        """Passes load requests straight up to the Mediator loop."""
        self.mediator.load_workspace_from_disk(self)

    def trigger_open_prism_file(self):
        """Passes Prism archive open requests straight up to the Mediator loop."""
        self.mediator.load_prism_workspace(self)


def main():
    app = QApplication(sys.argv)
    logo_path = os.path.join(os.path.dirname(__file__), "ui", "logo.png")
    if not os.path.exists(logo_path):
        logo_path = "src/ui/logo.png"
    app.setWindowIcon(QIcon(logo_path))
    window = VibePadSchismMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
