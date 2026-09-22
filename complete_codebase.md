# VibePad Schism Absolute Source Tree Codebase Blueprint
Generated for Gemini Notebook parsing.

## File Path: secure_guard.py
```python
#!/usr/bin/env python3
import sys
import re
import tokenize

# Blocklist of highly dangerous keywords, system hooks, and obfuscation patterns
BANNED_PATTERNS = [
    r"sudo\b",                  # Privilege escalation
    r"os\.system\b",            # Arbitrary shell execution
    r"subprocess\.Popen\b",     # Raw process spawning
    r"subprocess\.run\b",       # Raw process spawning
    r"__import__\(['\"]os['\"]\)", # Obfuscated imports
    r"eval\(",                  # Dynamic code execution
    r"(?<!\.)\bexec\(",         # Precise built-in exec function detection (ignores .exec())
    r"base64\.b64decode",       # Payload obfuscation prevention
    r"requests\.(get|post)",    # Prevent unauthorized exfiltration of your data
    r"urllib\.request",         # Alternative network exfiltration vectors
    r"socket\.",                # Raw TCP/UDP socket hooks
    r"chmod\b",                 # Unauthorized file permission adjustments
]

def scan_file(filepath):
    print(f"🔍 [Security Guard] Auditing file: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Regex check for hard blocklists
    for pattern in BANNED_PATTERNS:
        match = re.search(pattern, content)
        if match:
            print(f"❌ [CRITICAL SECURITY ALERT] Banned execution sequence detected: '{match.group()}'")
            return False

    # 2. Tokenizer check to look for obfuscated unicode injection attacks
    try:
        with open(filepath, "rb") as f:
            tokens = list(tokenize.tokenize(f.readline))
            for token in tokens:
                # Check for bidirectional unicode characters (used to trick human eyes in code)
                if token.type == tokenize.COMMENT or token.type == tokenize.STRING:
                    if any(c in token.string for c in ["\u202a", "\u202b", "\u202c", "\u202d", "\u202e"]):
                        print("❌ [CRITICAL SECURITY ALERT] Hidden bidirectional unicode injection detected in string/comment!")
                        return False
    except Exception as e:
        print(f"⚠️ [Warning] Parsing token safety failed: {e}")
        return False

    print("✅ [Security Guard] File cleared. No structural anomalies or backdoor triggers found.")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python secure_guard.py <path_to_source_file>")
        sys.exit(1)
        
    success = scan_file(sys.argv[1])
    sys.exit(0 if success else 1)

```

## File Path: src/main.py
```python
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
    padding-left: 6px;
    padding-right: 6px;
}

QMenu::item {
    padding: 6px 20px;
    padding-left: 6px;
    padding-right: 6px;
    color: #ffffff;
}

QMenu::item:selected {
    background-color: #0284c7;
    color: #ffffff;
}

QToolBar {
    background-color: #252525;
    border-bottom: 1px solid #3d3d3d;
    spacing: 6px;
    padding: 3px;
    padding-left: 6px;
    padding-right: 6px;
}

QToolButton {
    background-color: transparent;
    color: #ffffff;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 8px;
    padding-left: 6px;
    padding-right: 6px;
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

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 4px 8px;
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
    padding-left: 6px;
    padding-right: 6px;
}

QTreeWidget::item, QListWidget::item {
    height: 26px;
    padding-left: 6px;
    padding-right: 6px;
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
        file_menu = menubar.addMenu("📁 File")

        open_action = QAction("Open Workspace (.csv)...", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.trigger_open_file)
        file_menu.addAction(open_action)

        open_schism_action = QAction("📁 Open Schism Archive (.schism)...", self)
        open_schism_action.triggered.connect(self.trigger_open_schism_file)
        file_menu.addAction(open_schism_action)

        open_prism_action = QAction("📂 Open GraphPad Archive (.prism)...", self)
        open_prism_action.triggered.connect(self.trigger_open_prism_file)
        file_menu.addAction(open_prism_action)

        # Open Recent Sub-menu
        self.recent_menu = file_menu.addMenu("📂 Open Recent")
        self.update_recent_files_menu()

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

        analyze_action = QAction("🔬 Analyze Data...", self)
        analyze_action.setToolTip("Open GraphPad Prism style Analyze Data Hub")
        analyze_action.triggered.connect(self.trigger_open_analysis_hub)
        self.toolbar.addAction(analyze_action)

        self.toolbar.addSeparator()

        ttest_action = QAction("📊 Quick t-Test (Y1 vs Y2)", self)
        ttest_action.triggered.connect(self.trigger_workspace_t_test)
        self.toolbar.addAction(ttest_action)

        anova_action = QAction("📊 Run Two-Way ANOVA", self)
        anova_action.triggered.connect(self.trigger_two_way_anova)
        self.toolbar.addAction(anova_action)

        survival_action = QAction("⏳ Compute Kaplan-Meier Survival", self)
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
        self.inner_splitter.setSizes([520, 480])

        # Assemble outer splitter (Left Tree Sidebar | Inner Splitter)
        self.outer_splitter.addWidget(self.nav_tree)
        self.outer_splitter.addWidget(self.inner_splitter)
        self.outer_splitter.setSizes([240, 1000])

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

```

## File Path: src/data_engine/table_model.py
```python
"""
OpenPrism-Qt Scientific Data Engine Model.

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

import numpy as np
import pandas as pd


class ScientificTableModel:
    """Isolated storage grid for structured scientific data and tabular replicates.

    Manages pandas DataFrames configured for GraphPad Prism-style data layouts
    (e.g., XY format with one independent X column and multiple replicate Y columns,
    or discrete Columnar/Grouped layouts).

    Attributes:
        table_type (str): Format specification for the dataset ('XY', 'Columnar', 'Grouped').
        sheet_name (str): Identifier name for the sheet workspace.
        name (str): Display name for tree navigation linking.
        _data_frame (pd.DataFrame): Internal tabular storage matrix.
    """

    def __init__(self, table_type: str = "XY", sheet_name: str = "Data Table 1") -> None:
        """Initializes an isolated storage grid for structured scientific data.

        Args:
            table_type (str, optional): The tabular data layout type ('XY', 'Columnar', 'Grouped').
                Defaults to "XY".
            sheet_name (str, optional): Label for the data sheet instance.
                Defaults to "Data Table 1".
        """
        self.table_type = table_type
        self.sheet_name = sheet_name
        self.name = sheet_name
        self._data_frame = pd.DataFrame()
        self.clear_table()

    def clear_table(self) -> None:
        """Resets the data frame to its base structural format safely."""
        if self.table_type == "XY":
            # GraphPad Prism style XY layout: One independent variable (X) column,
            # and multiple replication channels (Y1, Y2, Y3) for experimental replicates.
            self._data_frame = pd.DataFrame(columns=["X", "Y1", "Y2", "Y3"])
        else:
            # Fallback baseline columns for generic columnar or grouped data entry.
            self._data_frame = pd.DataFrame(columns=["A", "B", "C"])

    def set_value(self, row: int, column_name: str, value: float) -> None:
        """Safely inputs a floating point numeric value into the structural grid.

        Dynamically expands row boundaries when an out-of-range index is targeted.

        Args:
            row (int): Zero-based row index location.
            column_name (str): Target column header string.
            value (float): Numeric scalar to insert into the matrix.

        Raises:
            ValueError: Silently caught if input value cannot be cast to a float,
                preserving mathematical matrix hygiene.
        """
        try:
            # Ensure index bounds exist gracefully by padding missing rows with NaN values.
            if row not in self._data_frame.index:
                for r in range(len(self._data_frame), row + 1):
                    # Pad out new rows with NaNs to maintain uniform array shapes
                    self._data_frame.loc[r] = [np.nan] * len(self._data_frame.columns)
            
            if column_name in self._data_frame.columns:
                self._data_frame.at[row, column_name] = float(value)
        except ValueError:
            # Silently discard non-numeric values to prevent corrupted matrix calculations downstream
            pass

    def get_column_data(self, column_name: str) -> np.ndarray:
        """Extracts an isolated 1D numpy array representing a single experimental variant.

        Drops missing (NaN) values to isolate pure numeric vectors for downstream
        statistical computations and plotting.

        Args:
            column_name (str): Target column header label to extract.

        Returns:
            np.ndarray: 1D NumPy array of float64 data values, excluding NaNs.
        """
        if column_name in self._data_frame.columns:
            # Drop NaN values so downstream statistical functions (e.g. t-tests, regressions)
            # act exclusively on complete numeric observations.
            return self._data_frame[column_name].dropna().to_numpy(dtype=float)
        return np.array([], dtype=float)

    def get_summary_statistics(self, column_name: str) -> dict:
        """Calculates baseline analytical markers for descriptive statistics summaries.

        Uses Bessel's correction (ddof=1) to estimate unbiased sample standard deviation:
        s = sqrt(1/(N-1) * sum((x_i - mean)^2)).

        Args:
            column_name (str): Column header label to analyze.

        Returns:
            dict: Dictionary containing calculated metrics:
                - 'mean' (float): Arithmetic sample mean, or NaN if empty.
                - 'std' (float): Unbiased sample standard deviation (ddof=1), or NaN/0.0.
                - 'count' (int): Total number of non-NaN observations.
        """
        data = self.get_column_data(column_name)
        if data.size == 0:
            return {"mean": np.nan, "std": np.nan, "count": 0}
        
        # Calculate sample standard deviation using ddof=1 (Bessel's correction)
        # to ensure an unbiased estimator of variance for finite sample sizes N > 1.
        return {
            "mean": float(np.mean(data)),
            "std": float(np.std(data, ddof=1)) if len(data) > 1 else 0.0,
            "count": int(len(data))
        }

    def rename_column(self, old_name: str, new_name: str) -> bool:
        """Renames a column header string in the underlying DataFrame while preserving data.

        Args:
            old_name (str): Existing column header label.
            new_name (str): New desired header label string.

        Returns:
            bool: True if rename succeeded, False if old_name doesn't exist or new_name is invalid.
        """
        if old_name in self._data_frame.columns and new_name and new_name.strip():
            self._data_frame.rename(columns={old_name: new_name.strip()}, inplace=True)
            return True
        return False

```

## File Path: src/data_engine/file_handler.py
```python
"""
VibePad Schism Scientific File Processing Controller.

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

import io
import json
import os
import zipfile
from typing import List, Optional, Union
import pandas as pd
from src.data_engine.table_model import ScientificTableModel


class ScientificFileHandler:
    """File processing controller for CSV import/export, .schism archive archives, and history tracking.

    Manages persistent recent files vectors in ~/.config/vibepad_schism/recent_files.txt,
    CSV serialization/deserialization, and ZIP-compressed .schism archive containers
    with embedded JSON metadata manifests and dataset CSV streams.

    Attributes:
        RECENT_FILES_PATH (str): Absolute file system path to the recent files text log.
    """

    RECENT_FILES_PATH: str = os.path.expanduser("~/.config/vibepad_schism/recent_files.txt")

    @staticmethod
    def get_recent_files() -> List[str]:
        """Retrieves the list of up to 5 valid recent file paths from local configuration storage.

        Reads lines from RECENT_FILES_PATH and filters out paths that no longer exist on disk.

        Returns:
            List[str]: Up to 5 existing absolute file paths sorted from most to least recent.
        """
        path = ScientificFileHandler.RECENT_FILES_PATH
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            # Filter out non-existent paths to maintain valid file references in UI menus
            valid_paths = [p for p in lines if os.path.exists(p)]
            return valid_paths[:5]
        except Exception:
            return []

    @staticmethod
    def add_recent_file(filepath: str) -> None:
        """Adds or promotes a file path in the recent files history vector.

        Maintains a maximum queue size of 5 absolute file paths, saving updates to disk.

        Args:
            filepath (str): Target file system path to record in history.
        """
        if not filepath or not isinstance(filepath, str):
            return
        abs_path = os.path.abspath(filepath)
        recent = ScientificFileHandler.get_recent_files()
        # Move path to top of recent list if previously present
        if abs_path in recent:
            recent.remove(abs_path)
        recent.insert(0, abs_path)
        recent = recent[:5]

        try:
            os.makedirs(os.path.dirname(ScientificFileHandler.RECENT_FILES_PATH), exist_ok=True)
            with open(ScientificFileHandler.RECENT_FILES_PATH, "w", encoding="utf-8") as f:
                f.write("\n".join(recent) + "\n")
        except Exception:
            pass

    @staticmethod
    def export_to_csv(model: ScientificTableModel, filepath: str) -> bool:
        """Safely exports tabular structural vectors to an open-source standard CSV format.

        Guarantees local environment isolation without spawning subprocess calls.

        Args:
            model (ScientificTableModel): Target table data model to export.
            filepath (str): Output destination path on local filesystem.

        Returns:
            bool: True if export succeeded without exception, False otherwise.
        """
        try:
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                
            # Serialize DataFrame to CSV, replacing NaN values with explicit 'NaN' representation
            model._data_frame.to_csv(filepath, index=False, na_rep="NaN")
            ScientificFileHandler.add_recent_file(filepath)
            return True
        except Exception:
            return False

    @staticmethod
    def import_from_csv(filepath: str, table_type: str = "XY") -> ScientificTableModel:
        """Parses a local experimental CSV spreadsheet into a ScientificTableModel data matrix.

        Args:
            filepath (str): Input CSV file path on disk.
            table_type (str, optional): Target table schema ('XY', 'Columnar', 'Grouped').
                Defaults to "XY".

        Returns:
            ScientificTableModel: Populated table model, or a fresh default model if file missing/corrupt.
        """
        new_model = ScientificTableModel(table_type=table_type)
        if not os.path.exists(filepath):
            return new_model

        try:
            # Parse CSV preserving NA values as floating NaNs for scientific calculation integrity
            parsed_df = pd.read_csv(filepath, keep_default_na=True)
            new_model._data_frame = parsed_df
            ScientificFileHandler.add_recent_file(filepath)
            return new_model
        except Exception:
            return new_model

    @staticmethod
    def export_to_schism(
        models: Union[ScientificTableModel, List[ScientificTableModel]], 
        filepath: str, 
        style_map: Optional[dict] = None
    ) -> bool:
        """Aggregates multi-sheet models and visual settings into a compressed .schism zip archive.

        Builds a manifest.json tracking sheet indices, titles, table schemas, and style mappings,
        storing each sheet's DataFrame as a distinct CSV file entry inside the zip archive.

        Args:
            models (Union[ScientificTableModel, List[ScientificTableModel]]): Single model or list of models.
            filepath (str): Output file path ending in .schism.
            style_map (Optional[dict], optional): Plot canvas visual formatting dictionary.
                Defaults to None.

        Returns:
            bool: True if export archive was created successfully, False on error.
        """
        try:
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            if not isinstance(models, list):
                models = [models]

            # Construct root manifest metadata document summarizing archive contents and style properties
            manifest = {
                "format": "schism_archive",
                "version": "1.0",
                "created_by": "VibePad Schism",
                "style_map": style_map if style_map else {},
                "sheets": []
            }

            # Write compressed ZIP archive containing manifest.json and individual CSV data buffers
            with zipfile.ZipFile(filepath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for idx, model in enumerate(models):
                    sheet_name = getattr(model, "sheet_name", getattr(model, "name", f"Sheet {idx+1}"))
                    csv_filename = f"sheet_{idx}.csv"
                    
                    manifest["sheets"].append({
                        "index": idx,
                        "sheet_name": sheet_name,
                        "table_type": getattr(model, "table_type", "XY"),
                        "csv_filename": csv_filename
                    })

                    # Write sheet DataFrame into in-memory CSV buffer to avoid transient disk files
                    csv_buffer = io.StringIO()
                    model._data_frame.to_csv(csv_buffer, index=False, na_rep="NaN")
                    zf.writestr(csv_filename, csv_buffer.getvalue())

                # Embed manifest manifest.json into archive root
                zf.writestr("manifest.json", json.dumps(manifest, indent=2))

            ScientificFileHandler.add_recent_file(filepath)
            return True
        except Exception:
            return False

    @staticmethod
    def import_from_schism(filepath: str) -> List[ScientificTableModel]:
        """Parses a compressed .schism zip archive, restoring all ScientificTableModel instances.

        Reads manifest.json to extract sheet schemas and titles, unzipping each sheet's CSV data.

        Args:
            filepath (str): Input .schism zip archive file path.

        Returns:
            List[ScientificTableModel]: List of restored table models, or empty list on failure.
        """
        if not os.path.exists(filepath):
            return []

        try:
            models = []
            with zipfile.ZipFile(filepath, "r") as zf:
                if "manifest.json" not in zf.namelist():
                    return []

                # Deserialize manifest JSON to reconstruct multi-sheet workspace structure
                manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
                sheets_info = manifest_data.get("sheets", [])

                for sheet in sheets_info:
                    sheet_name = sheet.get("sheet_name", "Data Sheet")
                    table_type = sheet.get("table_type", "XY")
                    csv_filename = sheet.get("csv_filename", "")

                    model = ScientificTableModel(table_type=table_type, sheet_name=sheet_name)
                    if csv_filename in zf.namelist():
                        csv_content = zf.read(csv_filename).decode("utf-8")
                        df = pd.read_csv(io.StringIO(csv_content), keep_default_na=True)
                        model._data_frame = df
                    models.append(model)

            ScientificFileHandler.add_recent_file(filepath)
            return models
        except Exception:
            return []

```

## File Path: src/data_engine/prism_parser.py
```python
"""
OpenPrism-Qt — Native GraphPad Prism 10 File Parser.
Licensed under GPLv3.

Treats .prism files as standard ZIP archives and extracts structured
experimental data into ScientificTableModel objects using only Python
built-in libraries: zipfile, json, io, dataclasses.

Expected internal ZIP layout:
    document.json               — Top-level manifest (title, version, sheet/table refs)
    data/sheets/<id>.json       — One descriptor per data sheet
    data/tables/<id>.json       — Column-oriented numeric data per table

No external dependencies. No shell execution. No privilege escalation.
Fully compliant with the No-Sudo-Strict-Local security policy.
"""

import io
import json
import os
import zipfile
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from src.data_engine.table_model import ScientificTableModel


__all__ = ["PrismParser", "PrismParseError"]


# ---------------------------------------------------------------------------
# Custom Exception
# ---------------------------------------------------------------------------

class PrismParseError(Exception):
    """
    Raised when a .prism archive is structurally invalid, missing required
    entries, or contains corrupt JSON payloads that block parsing entirely.
    """


# ---------------------------------------------------------------------------
# Intermediate Data Structures
# ---------------------------------------------------------------------------

@dataclass
class _PrismDocumentManifest:
    """
    Parsed representation of document.json.

    Attributes:
        title:      Human-readable document title.
        version:    Prism format version string (e.g. "10.0").
        sheet_ids:  Ordered list of sheet identifiers declared by the manifest.
        table_ids:  Ordered list of table identifiers declared by the manifest.
        raw_sheets: Raw sheet definitions from document.json (dicts or IDs).
    """
    title: str
    version: str
    sheet_ids: list = field(default_factory=list)
    table_ids: list = field(default_factory=list)
    raw_sheets: list = field(default_factory=list)


@dataclass
class _PrismSheetDescriptor:
    """
    Parsed representation of a single data/sheets/<id>.json entry.

    Attributes:
        sheet_id:        Unique sheet identifier string.
        name:            Display name of the sheet.
        table_type:      One of "XY", "Columnar", or "Grouped".
        linked_table_id: ID of the corresponding data/tables/ entry.
    """
    sheet_id: str
    name: str
    table_type: str
    linked_table_id: str


@dataclass
class _PrismTableData:
    """
    Parsed representation of a single data/tables/<id>.json entry.

    Attributes:
        table_id: Unique table identifier string.
        name:     Display name of the table.
        columns:  Ordered list of column header strings (e.g. ["X", "Y1", "Y2"]).
        rows:     Row-major data matrix. Each inner list contains one value per
                  column; JSON null values are preserved as Python None and
                  later mapped to np.nan in the model.
    """
    table_id: str
    name: str
    columns: list
    rows: list


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class PrismParser:
    """
    Parses native GraphPad Prism 10 .prism files into ScientificTableModel objects.

    Usage
    -----
    >>> models = PrismParser.parse("/path/to/experiment.prism")
    >>> first_model = models[0]

    Each returned ScientificTableModel corresponds to one data sheet inside the
    archive. Sheets are ordered by the sequence declared in document.json.

    Security guarantees
    -------------------
    - All ZIP member content is read into memory via ``ZipFile.read()`` —
      nothing is ever extracted to the local filesystem.
    - Every member path is sanitized against ZIP-slip directory traversal
      (``..`` components) before it is accessed.
    - Only the built-in ``zipfile``, ``json``, and ``io`` standard-library
      modules are used. No subprocess, no socket, no eval, no exec.
    """

    # Fixed internal paths within the ZIP archive
    _MANIFEST_PATH  = "document.json"
    _SETS_PREFIX    = "data/sets/"
    _SHEETS_PREFIX  = "data/sheets/"
    _TABLES_PREFIX  = "data/tables/"

    # Table types understood by ScientificTableModel
    _SUPPORTED_TABLE_TYPES = frozenset({"XY", "Columnar", "Grouped"})
    _DEFAULT_TABLE_TYPE    = "XY"

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    @staticmethod
    def parse(filepath: str) -> list:
        """
        Opens a .prism ZIP archive and returns a list of ScientificTableModel
        instances — one per valid, fully-linked data sheet in the archive.

        Args:
            filepath: Path to the .prism file (absolute or relative to CWD).

        Returns:
            List of ``ScientificTableModel`` instances, ordered by the sheet
            sequence declared in ``document.json``. Returns an empty list when
            the archive contains no valid sheet/table pairings.

        Raises:
            FileNotFoundError: The target path does not exist.
            PrismParseError:   The archive is corrupt, not a ZIP, or is missing
                               the required ``document.json`` entry.
        """
        return PrismParser(filepath)._run()

    # -----------------------------------------------------------------------
    # Internal Orchestration
    # -----------------------------------------------------------------------

    def __init__(self, filepath: str):
        self._filepath = filepath

    def _run(self) -> list:
        """
        Full two-pass parse pipeline:
          1. Open & validate the ZIP archive.
          2. Sanitize member paths (ZIP-slip guard).
          3. Pass 1: Parse document.json manifest for master sheet definitions.
          4. Read all data/sets/*.json, data/sheets/*.json, and data/tables/*.json payloads.
          5. Pass 2: Re-assemble target dataset arrays into unified multi-column ScientificTableModel instances.
        """
        # Step 1 — Open archive
        try:
            archive_handle = zipfile.ZipFile(self._filepath, mode="r")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Prism file not found: {self._filepath}"
            )
        except zipfile.BadZipFile as exc:
            raise PrismParseError(
                f"Not a valid Prism archive (bad ZIP): {self._filepath}"
            ) from exc

        with archive_handle as archive:
            # Step 2 — Sanitize paths
            safe_members = _sanitize_member_paths(archive)

            # Step 3 — Pass 1: Parse document.json manifest
            manifest = self._parse_manifest(archive, safe_members)

            # Step 4 — Read all set, sheet, and table JSON definitions into RAM
            sets_data = self._read_all_sets_data(archive, safe_members)
            sheets_data = self._read_all_sheets_data(archive, safe_members)
            tables_data = self._read_all_tables_data(archive, safe_members)

            # Step 5 — Pass 2: Re-assemble sheets into unified ScientificTableModel workspace instances
            models = self._assemble_sheets_into_models(manifest, sheets_data, sets_data, tables_data)

        return models

    # -----------------------------------------------------------------------
    # Parse Stages
    # -----------------------------------------------------------------------

    def _parse_manifest(
        self,
        archive: zipfile.ZipFile,
        safe_members: set,
    ) -> "_PrismDocumentManifest":
        """
        Reads and validates ``document.json`` from the archive root.

        Expected JSON structure::

            {
                "title":   "Experiment Title",
                "version": "10.0",
                "sheets":  ["sheet_0", "sheet_1"],
                "tables":  ["table_0", "table_1"]
            }

        Args:
            archive:      Open ZipFile handle (read mode).
            safe_members: Set of sanitized member path strings.

        Returns:
            Populated ``_PrismDocumentManifest`` dataclass.

        Raises:
            PrismParseError: If document.json is absent or unparseable.
        """
        manifest_path = None
        for m in safe_members:
            norm_entry = os.path.normpath(m.replace("\\", "/")).replace("\\", "/")
            if "document.json" in norm_entry:
                manifest_path = m
                break

        if not manifest_path:
            raise PrismParseError(
                "Archive is missing the required 'document.json' manifest. "
                f"File: {self._filepath}"
            )

        data = _read_json_member(archive, manifest_path)
        if data is None:
            raise PrismParseError(
                "'document.json' exists but could not be parsed as valid JSON. "
                f"File: {self._filepath}"
            )

        raw_sheets_obj = data.get("sheets", data.get("sets", {}))
        attr_map = data.get("sheetAttributesMap", {})
        raw_sheets = []
        sheet_ids = []

        if isinstance(raw_sheets_obj, dict):
            for category_or_id, item in raw_sheets_obj.items():
                if isinstance(item, list):
                    for s_uuid in item:
                        if isinstance(s_uuid, str):
                            s_id_str = s_uuid.strip()
                            sheet_ids.append(s_id_str)
                            title = (
                                attr_map.get(s_id_str, {}).get("title")
                                or attr_map.get(s_id_str, {}).get("name")
                                or s_id_str
                            )
                            raw_sheets.append({"id": s_id_str, "name": title, "category": category_or_id})
                        elif isinstance(s_uuid, dict):
                            raw_sheets.append(s_uuid)
                elif isinstance(item, dict):
                    meta_dict = dict(item)
                    s_id_str = str(meta_dict.get("id", meta_dict.get("uid", category_or_id))).strip()
                    sheet_ids.append(s_id_str)
                    page_name = (
                        meta_dict.get("name")
                        or meta_dict.get("title")
                        or meta_dict.get("label")
                        or attr_map.get(s_id_str, {}).get("title")
                        or s_id_str
                    )
                    meta_dict["id"] = s_id_str
                    meta_dict["name"] = str(page_name).strip()
                    raw_sheets.append(meta_dict)
                elif isinstance(item, str):
                    s_id_str = str(item).strip()
                    sheet_ids.append(s_id_str)
                    title = (
                        attr_map.get(s_id_str, {}).get("title")
                        or attr_map.get(s_id_str, {}).get("name")
                        or s_id_str
                    )
                    raw_sheets.append({"id": s_id_str, "name": title, "category": category_or_id})
        elif isinstance(raw_sheets_obj, list):
            for item in raw_sheets_obj:
                if isinstance(item, str):
                    s_id_str = item.strip()
                    sheet_ids.append(s_id_str)
                    title = (
                        attr_map.get(s_id_str, {}).get("title")
                        or attr_map.get(s_id_str, {}).get("name")
                        or s_id_str
                    )
                    raw_sheets.append({"id": s_id_str, "name": title})
                elif isinstance(item, dict):
                    s_id_str = str(item.get("id", item.get("uid", ""))).strip()
                    if s_id_str:
                        sheet_ids.append(s_id_str)
                    page_name = (
                        item.get("name")
                        or item.get("title")
                        or item.get("label")
                        or attr_map.get(s_id_str, {}).get("title")
                        or s_id_str
                    )
                    meta = dict(item)
                    meta["id"] = s_id_str or meta.get("id", "sheet")
                    meta["name"] = str(page_name).strip()
                    raw_sheets.append(meta)

        tables_obj = data.get("tables", [])
        if isinstance(tables_obj, dict):
            table_ids = [str(k) for k in tables_obj.keys()]
        elif isinstance(tables_obj, list):
            table_ids = [str(t) for t in tables_obj if isinstance(t, str)]
        else:
            table_ids = []

        return _PrismDocumentManifest(
            title      = str(data.get("title",   "Untitled Prism Document")),
            version    = str(data.get("version", "unknown")),
            sheet_ids  = sheet_ids,
            table_ids  = table_ids,
            raw_sheets = raw_sheets,
        )

    def _read_all_sets_data(self, archive: zipfile.ZipFile, safe_members: set) -> dict:
        sets_data = {}
        for entry in sorted(safe_members):
            norm_entry = os.path.normpath(entry.replace("\\", "/")).replace("\\", "/")
            if "data" in norm_entry and "sets" in norm_entry and entry.endswith(".json"):
                data = _read_json_member(archive, entry)
                if isinstance(data, dict):
                    set_id = str(data.get("uid", data.get("id", os.path.splitext(os.path.basename(entry))[0]))).strip()
                    sets_data[set_id] = data
        return sets_data

    def _read_all_sheets_data(self, archive: zipfile.ZipFile, safe_members: set) -> dict:
        sheets_data = {}
        for entry in sorted(safe_members):
            norm_entry = os.path.normpath(entry.replace("\\", "/")).replace("\\", "/")
            if "data" in norm_entry and "sheets" in norm_entry and entry.endswith(".json"):
                data = _read_json_member(archive, entry)
                if isinstance(data, dict):
                    sheet_id = str(data.get("uid", data.get("id", ""))).strip()
                    if not sheet_id:
                        if norm_entry.endswith("/sheet.json"):
                            sheet_id = os.path.basename(os.path.dirname(norm_entry)).strip()
                        else:
                            sheet_id = os.path.splitext(os.path.basename(entry))[0].strip()
                    sheets_data[sheet_id] = data
        return sheets_data

    def _read_all_tables_data(self, archive: zipfile.ZipFile, safe_members: set) -> dict:
        tables_data = {}
        for entry in sorted(safe_members):
            norm_entry = os.path.normpath(entry.replace("\\", "/")).replace("\\", "/")
            if "data" in norm_entry and "tables" in norm_entry:
                if entry.endswith("data.csv"):
                    try:
                        raw_bytes = archive.read(entry)
                        text = raw_bytes.decode("utf-8", errors="ignore")
                        import csv
                        reader = csv.reader(io.StringIO(text))
                        rows = [r for r in reader if r]
                        parent_id = os.path.basename(os.path.dirname(norm_entry)).strip()
                        tables_data[parent_id] = {
                            "id": parent_id,
                            "type": "csv_table",
                            "csv_rows": rows
                        }
                    except Exception:
                        pass
                elif entry.endswith(".json"):
                    data = _read_json_member(archive, entry)
                    if isinstance(data, dict):
                        table_id = str(data.get("uid", data.get("id", ""))).strip()
                        if not table_id:
                            table_id = os.path.basename(os.path.dirname(norm_entry)).strip() if norm_entry.endswith(".json") else os.path.splitext(os.path.basename(entry))[0].strip()
                        tables_data[table_id] = data
        return tables_data

    def _assemble_sheets_into_models(
        self,
        manifest: "_PrismDocumentManifest",
        sheets_data: dict,
        sets_data: dict,
        tables_data: dict,
    ) -> list:
        sheet_defs = []

        # Pass 1: Parse master document.json structural sheet definitions
        if manifest.raw_sheets:
            for item in manifest.raw_sheets:
                if isinstance(item, dict):
                    s_id = str(item.get("id", item.get("uid", ""))).strip()
                    full_dict = dict(item)
                    if s_id in sheets_data:
                        for k, v in sheets_data[s_id].items():
                            if k not in full_dict or (full_dict[k] == s_id and v != s_id):
                                full_dict[k] = v
                    elif s_id in sets_data:
                        for k, v in sets_data[s_id].items():
                            if k not in full_dict or (full_dict[k] == s_id and v != s_id):
                                full_dict[k] = v
                    sheet_defs.append(full_dict)
                elif isinstance(item, str):
                    s_id = item.strip()
                    if s_id in sheets_data:
                        sheet_defs.append(sheets_data[s_id])
                    elif s_id in sets_data:
                        sheet_defs.append(sets_data[s_id])
                    else:
                        sheet_defs.append({"id": s_id, "name": s_id})

        # Fallback to data/sheets/*.json descriptors
        if not sheet_defs and sheets_data:
            for s_id, s_dict in sheets_data.items():
                sheet_defs.append(s_dict)

        # Fallback to data/sets/*.json if no explicit sheets were declared
        if not sheet_defs and sets_data:
            grouped_sets = {}
            for set_id, s_data in sets_data.items():
                parent_name = str(s_data.get("sheet_name", s_data.get("name", s_data.get("title", set_id)))).strip()
                if parent_name not in grouped_sets:
                    grouped_sets[parent_name] = []
                grouped_sets[parent_name].append(s_data)

            for p_name, s_list in grouped_sets.items():
                sheet_defs.append({
                    "id": p_name,
                    "name": p_name,
                    "type": s_list[0].get("type", s_list[0].get("table_type", self._DEFAULT_TABLE_TYPE)),
                    "inline_sets": s_list
                })

        if not sheet_defs:
            return []

        models = []
        for s_def in sheet_defs:
            s_id = str(s_def.get("id", s_def.get("uid", ""))).strip()
            s_name = str(s_def.get("name", s_def.get("title", s_def.get("label", s_id or "Untitled Sheet")))).strip()
            raw_type = str(s_def.get("type", s_def.get("table_type", self._DEFAULT_TABLE_TYPE))).strip()
            table_type = raw_type if raw_type in self._SUPPORTED_TABLE_TYPES else self._DEFAULT_TABLE_TYPE

            model = ScientificTableModel(table_type=table_type)
            # Expose ONLY the true human-readable sheet title string (e.g., "siDuox2" or "nM")
            model.sheet_name = s_name
            model.name = s_name
            model_columns = list(model._data_frame.columns)

            target_datasets = []

            # Add inline sets if present
            if "inline_sets" in s_def and isinstance(s_def["inline_sets"], list):
                target_datasets.extend(s_def["inline_sets"])

            # Inspect table subdict if present (GraphPad Prism 10 format)
            table_subdict = s_def.get("table", {})
            if isinstance(table_subdict, dict):
                t_uid = str(table_subdict.get("uid", "")).strip()
                if t_uid and t_uid in tables_data and tables_data[t_uid] not in target_datasets:
                    target_datasets.append(tables_data[t_uid])
                
                x_ds = str(table_subdict.get("xDataSet", "")).strip()
                if x_ds and x_ds in sets_data and sets_data[x_ds] not in target_datasets:
                    target_datasets.append(sets_data[x_ds])
                
                ds_list = table_subdict.get("dataSets", [])
                if isinstance(ds_list, list):
                    for ds_id in ds_list:
                        ds_str = str(ds_id).strip()
                        if ds_str in sets_data and sets_data[ds_str] not in target_datasets:
                            target_datasets.append(sets_data[ds_str])

            # Query internal column / set / table structural link maps embedded in sheet metadata
            linked_keys = []
            for link_prop in ["sets", "linked_sets", "set_ids", "setIds", "dataSets", "datasets", "columns", "tables", "linked_tables"]:
                val = s_def.get(link_prop)
                if isinstance(val, list):
                    for v in val:
                        if isinstance(v, str):
                            linked_keys.append(v)
                        elif isinstance(v, dict) and "id" in v:
                            linked_keys.append(str(v["id"]))
                elif isinstance(val, str):
                    linked_keys.append(val)

            for single_prop in ["table", "linked_table", "table_id", "tableId", "data_table"]:
                val = s_def.get(single_prop)
                if isinstance(val, str) and val:
                    linked_keys.append(val)

            for k_str in linked_keys:
                if k_str in sets_data and sets_data[k_str] not in target_datasets:
                    target_datasets.append(sets_data[k_str])
                if k_str in tables_data and tables_data[k_str] not in target_datasets:
                    target_datasets.append(tables_data[k_str])
                if k_str in sheets_data and sheets_data[k_str] not in target_datasets:
                    target_datasets.append(sheets_data[k_str])

            if s_id in sets_data and sets_data[s_id] not in target_datasets:
                target_datasets.append(sets_data[s_id])

            if s_id in tables_data and tables_data[s_id] not in target_datasets:
                target_datasets.append(tables_data[s_id])

            # If no target datasets linked yet, check sets matching s_id / s_name
            if not target_datasets and sets_data:
                for set_id, s_data in sets_data.items():
                    if s_data.get("sheet_id") == s_id or s_data.get("sheet_name") == s_name:
                        target_datasets.append(s_data)

            # Fallback to all sets_data if still unlinked
            if not target_datasets and sets_data:
                target_datasets = list(sets_data.values())

            # Pass 2: Re-assemble target arrays into a single unified multi-column model
            has_data = self._bind_datasets_to_model(model, target_datasets, model_columns)

            if has_data:
                models.append(model)

        return models

    def _bind_datasets_to_model(self, model: ScientificTableModel, datasets: list, model_columns: list) -> bool:
        """
        Re-assembles individual target arrays from datasets into a single unified multi-column model.
        Returns True if any data values were successfully populated.
        """
        if not datasets:
            return False

        has_data = False
        current_y_idx = 1

        for data in datasets:
            if not isinstance(data, dict):
                continue

            # Case 0: CSV table dataset (Prism 10 data/tables/<uuid>/data.csv)
            if data.get("type") == "csv_table" and "csv_rows" in data and isinstance(data["csv_rows"], list):
                for row_idx, raw_vals in enumerate(data["csv_rows"]):
                    if not isinstance(raw_vals, list):
                        continue
                    col_idx = 0
                    for val_str in raw_vals:
                        val_str = str(val_str).strip()
                        if not val_str:
                            col_idx += 1
                            continue
                        try:
                            val_num = float(val_str)
                            if not _is_nan_or_inf(val_num):
                                target_col = model_columns[col_idx] if col_idx < len(model_columns) else f"Y{col_idx}"
                                model.set_value(row_idx, target_col, val_num)
                                has_data = True
                        except ValueError:
                            pass
                        col_idx += 1

            # Case 1: Standard matrix layout with 'columns' and 'rows'
            if "columns" in data and "rows" in data and isinstance(data["columns"], list) and isinstance(data["rows"], list):
                prism_cols = [str(c) for c in data["columns"]]
                binding = _resolve_column_binding(prism_cols, model_columns)
                for row_idx, row_vals in enumerate(data["rows"]):
                    if not isinstance(row_vals, list):
                        continue
                    for prism_idx, model_col in binding.items():
                        if prism_idx < len(row_vals):
                            val = row_vals[prism_idx]
                            if isinstance(val, (int, float)) and not _is_nan_or_inf(val):
                                model.set_value(row_idx, model_col, float(val))
                                has_data = True

            # Case 2: Column objects list [{'name': '...', 'values': [...]}]
            elif "columns" in data and isinstance(data["columns"], list) and len(data["columns"]) > 0 and isinstance(data["columns"][0], dict):
                prism_cols = [str(c.get("name", c.get("id", ""))) for c in data["columns"]]
                binding = _resolve_column_binding(prism_cols, model_columns)
                for prism_idx, col_dict in enumerate(data["columns"]):
                    if prism_idx in binding:
                        target_col = binding[prism_idx]
                        values = col_dict.get("values", col_dict.get("data", []))
                        if isinstance(values, list):
                            for row_idx, val in enumerate(values):
                                if isinstance(val, (int, float)) and not _is_nan_or_inf(val):
                                    model.set_value(row_idx, target_col, float(val))
                                    has_data = True

            # Case 3: Coordinate / replicate vectors ('x', 'y', 'y1', 'y2', 'values')
            else:
                x_vec = data.get("x", data.get("X", data.get("x_values", [])))
                if isinstance(x_vec, list) and len(x_vec) > 0:
                    for r_idx, val in enumerate(x_vec):
                        if isinstance(val, (int, float)) and not _is_nan_or_inf(val):
                            model.set_value(r_idx, "X", float(val))
                            has_data = True

                y_keys = [k for k in ["y", "y1", "Y", "Y1", "y2", "Y2", "y3", "Y3", "values"] if k in data and isinstance(data[k], list)]
                if y_keys:
                    for y_key in y_keys:
                        vec = data[y_key]
                        if not isinstance(vec, list) or len(vec) == 0:
                            continue

                        if y_key.upper() in ["Y", "Y1", "VALUES"]:
                            target_col = f"Y{current_y_idx}"
                            current_y_idx += 1
                        elif y_key.upper() in model_columns:
                            target_col = y_key.upper()
                        else:
                            target_col = f"Y{current_y_idx}"
                            current_y_idx += 1

                        if target_col in model_columns:
                            for r_idx, val in enumerate(vec):
                                if isinstance(val, (int, float)) and not _is_nan_or_inf(val):
                                    model.set_value(r_idx, target_col, float(val))
                                    has_data = True

        return has_data


# ---------------------------------------------------------------------------
# Module-Level Helpers
# ---------------------------------------------------------------------------

def _sanitize_member_paths(archive: zipfile.ZipFile) -> set:
    """
    Returns a set of all archive member paths that pass a ZIP-slip safety check.

    Each path is:
        - Evaluated with os.path.normpath to verify safety.
        - Rejected if any path component equals ``..``.
        - Filtered to skip macOS metadata entries (__MACOSX).

    Args:
        archive: Open ZipFile handle (read mode).

    Returns:
        Set of safe member path strings.
    """
    safe = set()
    for info in archive.infolist():
        raw_name = info.filename
        norm = os.path.normpath(raw_name.replace("\\", "/")).replace("\\", "/")
        parts = norm.split("/")
        raw_parts = raw_name.replace("\\", "/").split("/")
        if ".." in parts or ".." in raw_parts or raw_name.startswith("__MACOSX"):
            # Reject ZIP-slip traversal attempt silently
            continue
        safe.add(raw_name)
    return safe


def _read_json_member(archive: zipfile.ZipFile, member_path: str) -> Optional[dict]:
    """
    Reads a single ZIP member entirely into memory and parses it as UTF-8 JSON.
    Supports cross-platform slash fallbacks and direct ZipInfo resolution.

    Data flow:
        ZipFile.read()  →  bytes in RAM
        io.BytesIO      →  in-memory byte stream (never touches the filesystem)
        io.TextIOWrapper→  UTF-8 character decoding layer
        json.loads()    →  Python dict

    Args:
        archive:     Open ZipFile handle (read mode).
        member_path: Member path string.

    Returns:
        Parsed dict, or ``None`` on any read or parse failure.
    """
    try:
        try:
            raw_bytes = archive.read(member_path)
        except KeyError:
            # Fallback: find member by normalized match if slashes differ in archive index
            target_norm = os.path.normpath(member_path.replace("\\", "/")).replace("\\", "/")
            matched_info = None
            for info in archive.infolist():
                if os.path.normpath(info.filename.replace("\\", "/")).replace("\\", "/") == target_norm:
                    matched_info = info
                    break
            if matched_info:
                raw_bytes = archive.read(matched_info)
            else:
                return None

        text = io.TextIOWrapper(io.BytesIO(raw_bytes), encoding="utf-8").read()
        return json.loads(text)
    except (KeyError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _resolve_column_binding(prism_columns: list, model_columns: list) -> dict:
    """
    Builds a mapping from Prism column index to ScientificTableModel column name.

    Resolution passes:
        Pass 1 — Exact name match:
            If a Prism column header exactly matches a model schema column name
            (e.g. "X" → "X", "Y1" → "Y1"), it is bound directly by name.
            Matched model columns are removed from the fallback pool.

        Pass 2 — Positional fallback:
            Remaining unmatched Prism columns are assigned to the next available
            model column in schema declaration order.

        Excess Prism columns are silently ignored once the model schema is full.

    Args:
        prism_columns: Ordered Prism column headers from the table JSON.
        model_columns: Ordered model schema column names (e.g. ["X","Y1","Y2","Y3"]).

    Returns:
        Dict mapping prism_column_index (int) → model_column_name (str).

    Examples:
        Prism ["X", "Y1", "Response"] + Model ["X", "Y1", "Y2", "Y3"]
            → {0: "X", 1: "Y1", 2: "Y2"}   (index 2 falls through positionally)

        Prism ["Dose", "Mean", "SEM"] + Model ["X", "Y1", "Y2", "Y3"]
            → {0: "X", 1: "Y1", 2: "Y2"}   (all positional — no exact matches)
    """
    binding: dict = {}
    unbound_pool  = list(model_columns)  # Mutable copy for positional fallback

    # Pass 1: exact name matches
    for prism_idx, prism_col in enumerate(prism_columns):
        if prism_col in unbound_pool:
            binding[prism_idx] = prism_col
            unbound_pool.remove(prism_col)

    # Pass 2: positional fallback for remaining columns
    fallback = iter(unbound_pool)
    for prism_idx, _ in enumerate(prism_columns):
        if prism_idx in binding:
            continue
        target = next(fallback, None)
        if target is None:
            break  # Model schema exhausted
        binding[prism_idx] = target

    return binding


def _is_nan_or_inf(value: float) -> bool:
    """
    Returns True if a float value is NaN or infinite.
    Used to guard against injecting mathematical poison values into the model.

    Args:
        value: The float to test.

    Returns:
        True if value is NaN or ±Inf, False otherwise.
    """
    import math
    return math.isnan(value) or math.isinf(value)

```

## File Path: src/analysis/curve_fitting.py
```python
"""
OpenPrism-Qt Analytical Curve Fitting Engine.

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

import numpy as np
from scipy.optimize import curve_fit


def dose_response_model(x: np.ndarray, bottom: float, top: float, log_ec50: float) -> np.ndarray:
    """Standard GraphPad Prism Hill equation for non-linear Dose-Response curves.

    Mathematical Formula:
        Y = Bottom + (Top - Bottom) / (1 + 10^(LogEC50 - X))

    where X is log(concentration), Bottom is the minimum asymptotic response,
    Top is the maximum asymptotic response, and LogEC50 is the log concentration
    producing a half-maximal response.

    Args:
        x (np.ndarray): Vector of independent variable values (log concentration).
        bottom (float): Minimum asymptote (baseline Y value at low concentrations).
        top (float): Maximum asymptote (plateau Y value at high concentrations).
        log_ec50 (float): Logarithm (base 10) of the EC50 concentration parameter.

    Returns:
        np.ndarray: Predicted Y values evaluated along the sigmoid curve.
    """
    # Evaluate 4-parameter logistic (4PL) sigmoid equation with fixed unit Hill slope (h = 1.0)
    exponent = np.clip(log_ec50 - x, -20, 20)
    return bottom + (top - bottom) / (1 + 10**exponent)


class CurveFittingEngine:
    """Analytical non-linear regression engine using Levenberg-Marquardt least squares optimization."""

    @staticmethod
    def fit_dose_response(x_data: np.ndarray, y_data: np.ndarray) -> dict:
        """Fits experimental data vectors to the standard four-parameter dose-response curve safely.

        Performs non-linear least squares optimization via scipy.optimize.curve_fit.
        Derives standard errors of estimated parameters from the diagonal of the covariance matrix:
            SE(theta_i) = sqrt(C_{i,i})

        Args:
            x_data (np.ndarray): 1D array of independent variable observations (X coordinates).
            y_data (np.ndarray): 1D array of dependent variable observations (Y coordinates).

        Returns:
            dict: Result payload containing:
                - 'success' (bool): True if convergence was achieved, False otherwise.
                - 'params' (dict): Optimal fit parameters ('bottom', 'top', 'log_ec50', 'ec50').
                - 'errors' (dict): Asymptotic standard errors ('bottom_err', 'top_err', 'log_ec50_err').
                - 'error' (str): Descriptive message if optimization fails or data is insufficient.
        """
        # Minimum requirement of 3 observations to fit 3 free parameters (bottom, top, log_ec50)
        # to ensure at least 1 degree of freedom (N - K = 3 - 3 = 0, minimum 3 points for parameter resolution).
        if len(x_data) < 3 or len(y_data) < 3 or len(x_data) != len(y_data):
            return {"success": False, "error": "Insufficient or mismatched data vectors"}

        try:
            # Generate empirical initial parameter guesses [bottom, top, log_ec50]:
            # - bottom ~ min(Y)
            # - top ~ max(Y)
            # - log_ec50 ~ mean(X) as a robust midpoint guess
            initial_guesses = [np.min(y_data), np.max(y_data), np.mean(x_data)]
            
            # Execute non-linear least squares fit (Levenberg-Marquardt / Trust Region Reflective algorithm)
            popt, pcov = curve_fit(dose_response_model, x_data, y_data, p0=initial_guesses, maxfev=5000)
            
            # Standard errors of parameter estimates are computed as the square root of diagonal
            # covariance elements: SE = sqrt(diag(pcov))
            perr = np.sqrt(np.diag(pcov))
            
            log_ec50_val = float(popt[2])
            if log_ec50_val > 20:
                ec50_val = float(10**20)
            else:
                try:
                    ec50_val = float(10**log_ec50_val)
                except (OverflowError, FloatingPointError):
                    ec50_val = float(10**20)

            return {
                "success": True,
                "params": {
                    "bottom": float(popt[0]),
                    "top": float(popt[1]),
                    "log_ec50": log_ec50_val,
                    "ec50": ec50_val  # Convert log(EC50) parameter back to absolute concentration scale with overflow protection
                },
                "errors": {
                    "bottom_err": float(perr[0]),
                    "top_err": float(perr[1]),
                    "log_ec50_err": float(perr[2])
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Optimization fitting failed: {str(e)}"}

```

## File Path: src/analysis/t_test.py
```python
"""
OpenPrism-Qt Comparative Hypotheses Engine (t-Tests & Nonparametric Tests).

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

Implements Student's t-test, Welch's t-test, Paired t-test, and Mann-Whitney U test
according to GraphPad Prism 10 standards.
"""

import math
import numpy as np
from scipy import stats


class TTestEngine:
    """Comparative hypothesis testing engine for two-group experimental designs."""

    @staticmethod
    def calculate_unpaired_t_test(group_a: np.ndarray, group_b: np.ndarray, equal_var: bool = True) -> dict:
        """Computes an independent unpaired t-test between two numeric experiment samples.

        Supports both Student's t-test (assuming equal variance, homoscedasticity)
        and Welch's t-test (assuming unequal variance, heteroscedasticity).

        Mathematical Formulas:
            Equal Variance (Student's t-test):
                Pooled Variance:
                    s_p^2 = ((n_A - 1)s_A^2 + (n_B - 1)s_B^2) / df
                Degrees of Freedom:
                    df = n_A + n_B - 2
                Standard Error of Difference:
                    SE_{diff} = sqrt(s_p^2 * (1/n_A + 1/n_B))

            Unequal Variance (Welch's t-test):
                Welch-Satterthwaite Degrees of Freedom:
                    df = (s_A^2/n_A + s_B^2/n_B)^2 / ((s_A^2/n_A)^2 / (n_A - 1) + (s_B^2/n_B)^2 / (n_B - 1))
                Standard Error of Difference:
                    SE_{diff} = sqrt(s_A^2/n_A + s_B^2/n_B)

            95% Confidence Interval of Mean Difference:
                CI = (mean_A - mean_B) +/- t_{critical, 0.975, df} * SE_{diff}

        Args:
            group_a (np.ndarray): Numeric observations for Group A.
            group_b (np.ndarray): Numeric observations for Group B.
            equal_var (bool, optional): If True, compute Student's t-test. If False, compute Welch's t-test.
                Defaults to True.

        Returns:
            dict: Summary dictionary containing:
                - 'success' (bool): True if computation succeeded.
                - 'summary' (dict): Sample statistics (mean, std, n) for each group.
                - 'results' (dict): Calculated t_statistic, p_value, degrees_of_freedom,
                  mean_difference, standard_error_difference, and 95% confidence_interval tuple.
        """
        arr_a = np.asarray(group_a, dtype=float)
        arr_b = np.asarray(group_b, dtype=float)
        # Filter out NaN and Infinite entries to ensure clean finite vector analysis
        arr_a = arr_a[~np.isnan(arr_a) & ~np.isinf(arr_a)]
        arr_b = arr_b[~np.isnan(arr_b) & ~np.isinf(arr_b)]

        if arr_a.size < 2 or arr_b.size < 2:
            return {"success": False, "error": "Each treatment group must contain at least 2 observations."}

        try:
            mean_a, mean_b = float(np.mean(arr_a)), float(np.mean(arr_b))
            # Sample standard deviation computed with Bessel's correction (ddof=1)
            std_a, std_b = float(np.std(arr_a, ddof=1)), float(np.std(arr_b, ddof=1))
            n_a, n_b = int(len(arr_a)), int(len(arr_b))

            mean_difference = mean_a - mean_b

            # SciPy independent t-test computation
            t_stat, p_val = stats.ttest_ind(arr_a, arr_b, equal_var=equal_var)

            if equal_var:
                # Student's t-test: Degrees of freedom = N_A + N_B - 2
                df = float(n_a + n_b - 2)
                # Pooled sample variance combining variance estimates weighted by degrees of freedom
                pooled_var = ((n_a - 1) * (std_a ** 2) + (n_b - 1) * (std_b ** 2)) / df
                se_diff = float(np.sqrt(pooled_var * (1.0 / n_a + 1.0 / n_b)))
            else:
                # Welch's t-test: Welch-Satterthwaite equation for effective degrees of freedom
                se_a_sq = (std_a ** 2) / n_a
                se_b_sq = (std_b ** 2) / n_b
                df = float(((se_a_sq + se_b_sq) ** 2) / (
                    (se_a_sq ** 2 / (n_a - 1)) + (se_b_sq ** 2 / (n_b - 1))
                ))
                se_diff = float(np.sqrt(se_a_sq + se_b_sq))

            # 95% Two-sided confidence interval calculation using Student's t-distribution quantile
            t_critical = float(stats.t.ppf(0.975, df))
            margin_of_error = t_critical * se_diff
            ci_lower = mean_difference - margin_of_error
            ci_upper = mean_difference + margin_of_error

            return {
                "success": True,
                "summary": {
                    "group_a": {"mean": mean_a, "std": std_a, "n": n_a},
                    "group_b": {"mean": mean_b, "std": std_b, "n": n_b}
                },
                "results": {
                    "t_statistic": float(t_stat),
                    "p_value": float(p_val),
                    "degrees_of_freedom": float(df),
                    "mean_difference": float(mean_difference),
                    "standard_error_difference": float(se_diff),
                    "confidence_interval": (float(ci_lower), float(ci_upper))
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Statistical computation failed: {str(e)}"}

    @staticmethod
    def calculate_welch_t_test(group_a: np.ndarray, group_b: np.ndarray) -> dict:
        """Computes Welch's t-test (independent sample t-test assuming unequal variance).

        Args:
            group_a (np.ndarray): Numeric observations for Group A.
            group_b (np.ndarray): Numeric observations for Group B.

        Returns:
            dict: Summary dictionary containing Welch's t-test metrics.
        """
        return TTestEngine.calculate_unpaired_t_test(group_a, group_b, equal_var=False)

    @staticmethod
    def calculate_paired_t_test(group_a: np.ndarray, group_b: np.ndarray) -> dict:
        """Computes a paired sample t-test for matched experimental observations.

        Mathematical Formulas:
            Pair Differences:
                D_i = A_i - B_i
            Mean Difference:
                mean(D) = 1/N * sum(D_i)
            Sample Standard Deviation of Differences (ddof=1):
                s_D = sqrt(1/(N-1) * sum((D_i - mean(D))^2))
            Standard Error of Mean Difference:
                SEM_D = s_D / sqrt(N)
            Degrees of Freedom:
                df = N - 1

        Args:
            group_a (np.ndarray): First vector of paired observations.
            group_b (np.ndarray): Second vector of paired observations.

        Returns:
            dict: Summary dictionary containing paired t-test results.
        """
        arr_a = np.asarray(group_a, dtype=float)
        arr_b = np.asarray(group_b, dtype=float)
        # Pairwise complete-case filtering (listwise deletion of missing pairs)
        mask = ~np.isnan(arr_a) & ~np.isinf(arr_a) & ~np.isnan(arr_b) & ~np.isinf(arr_b)
        arr_a = arr_a[mask]
        arr_b = arr_b[mask]

        n = len(arr_a)
        if n < 2:
            return {"success": False, "error": "Paired t-test requires at least 2 complete observation pairs."}

        try:
            # Pairwise differences vector
            diffs = arr_a - arr_b
            mean_diff = float(np.mean(diffs))
            std_diff = float(np.std(diffs, ddof=1))
            sem_diff = float(std_diff / math.sqrt(n))

            t_stat, p_val = stats.ttest_rel(arr_a, arr_b)
            df = float(n - 1)

            # 95% Confidence Interval for mean difference
            t_crit = float(stats.t.ppf(0.975, df))
            margin = t_crit * sem_diff
            ci_lower = mean_diff - margin
            ci_upper = mean_diff + margin

            return {
                "success": True,
                "summary": {
                    "group_a": {"mean": float(np.mean(arr_a)), "std": float(np.std(arr_a, ddof=1)), "n": n},
                    "group_b": {"mean": float(np.mean(arr_b)), "std": float(np.std(arr_b, ddof=1)), "n": n}
                },
                "results": {
                    "t_statistic": float(t_stat),
                    "p_value": float(p_val),
                    "degrees_of_freedom": float(df),
                    "mean_difference": mean_diff,
                    "std_difference": std_diff,
                    "sem_difference": sem_diff,
                    "confidence_interval": (float(ci_lower), float(ci_upper))
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Paired t-test computation failed: {str(e)}"}

    @staticmethod
    def calculate_mann_whitney_u_test(group_a: np.ndarray, group_b: np.ndarray) -> dict:
        """Computes the non-parametric Mann-Whitney U test (Wilcoxon rank-sum test).

        Used when data distributions do not follow a normal (Gaussian) distribution.
        Evaluates whether ranks of values in group_a differ systematically from group_b.

        Args:
            group_a (np.ndarray): Numeric observations for Group A.
            group_b (np.ndarray): Numeric observations for Group B.

        Returns:
            dict: Summary dictionary containing Mann-Whitney U statistic and asymptotic p-value.
        """
        arr_a = np.asarray(group_a, dtype=float)
        arr_b = np.asarray(group_b, dtype=float)
        arr_a = arr_a[~np.isnan(arr_a) & ~np.isinf(arr_a)]
        arr_b = arr_b[~np.isnan(arr_b) & ~np.isinf(arr_b)]

        n_a, n_b = len(arr_a), len(arr_b)
        if n_a < 1 or n_b < 1:
            return {"success": False, "error": "Each group must contain at least 1 observation for Mann-Whitney U test."}

        try:
            # Two-sided rank-sum non-parametric test
            u_stat, p_val = stats.mannwhitneyu(arr_a, arr_b, alternative="two-sided")
            median_a, median_b = float(np.median(arr_a)), float(np.median(arr_b))
            median_diff = median_a - median_b

            return {
                "success": True,
                "summary": {
                    "group_a": {"median": median_a, "n": n_a},
                    "group_b": {"median": median_b, "n": n_b}
                },
                "results": {
                    "u_statistic": float(u_stat),
                    "p_value": float(p_val),
                    "median_difference": float(median_diff)
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Mann-Whitney U test failed: {str(e)}"}

```

## File Path: src/analysis/anova_two_way.py
```python
"""
OpenPrism-Qt Two-Way Analysis of Variance (ANOVA) Engine.

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

import numpy as np
import pandas as pd
import scipy.stats as stats
from typing import Dict, Any


class TwoWayAnovaEngine:
    """Analytical engine for Two-Way Analysis of Variance (ANOVA) with Interaction."""

    @staticmethod
    def calculate_two_way_anova(
        df: pd.DataFrame,
        factor_a_col: str,
        factor_b_col: str,
        value_col: str
    ) -> Dict[str, Any]:
        """Calculates Two-Way ANOVA table for Factor A, Factor B, and Interaction (A x B).

        Attempts to fit an OLS model via statsmodels.api.stats.anova_lm if available,
        falling back seamlessly to explicit sum-of-squares calculation routines.

        Mathematical Formulas:
            Grand Mean: bar{Y} = 1/N * sum(Y_ijk)
            SS_Total = sum((Y_ijk - bar{Y})^2)
            SS_A = sum(n_i * (bar{Y}_i. - bar{Y})^2)
            SS_B = sum(n_j * (bar{Y}_.j - bar{Y})^2)
            SS_Cells = sum(n_ij * (bar{Y}_ij - bar{Y})^2)
            SS_Interaction (A x B) = SS_Cells - SS_A - SS_B
            SS_Residual (Error) = SS_Total - SS_Cells

            F_A = MS_A / MS_Error,  F_B = MS_B / MS_Error,  F_AB = MS_AB / MS_Error

        Args:
            df (pd.DataFrame): Input DataFrame containing observations.
            factor_a_col (str): Column title for Factor A (Row factor).
            factor_b_col (str): Column title for Factor B (Column factor).
            value_col (str): Column title for continuous measurement values.

        Returns:
            Dict[str, Any]: Results payload containing Factor A, Factor B, Interaction,
                Residual Error, and Total degrees of freedom, sum of squares, mean squares,
                F-statistics, and two-tailed p-values.
        """
        if not isinstance(df, pd.DataFrame) or df.empty:
            return {"success": False, "error": "Input DataFrame is empty."}

        for col in [factor_a_col, factor_b_col, value_col]:
            if col not in df.columns:
                return {"success": False, "error": f"Missing required column '{col}' in DataFrame."}

        try:
            clean_df = df[[factor_a_col, factor_b_col, value_col]].dropna().copy()
            clean_df[value_col] = pd.to_numeric(clean_df[value_col], errors="coerce")
            clean_df = clean_df.dropna()

            N = len(clean_df)
            if N < 4:
                return {"success": False, "error": "Two-Way ANOVA requires at least 4 valid observations."}

            # Attempt statsmodels.api.stats.anova_lm OLS calculation
            try:
                import statsmodels.api as sm
                from statsmodels.formula.api import ols

                # Build formula replacing special characters for statsmodels formula parser
                clean_formula_df = clean_df.rename(columns={
                    factor_a_col: "FactorA",
                    factor_b_col: "FactorB",
                    value_col: "Value"
                })
                model = ols("Value ~ C(FactorA) * C(FactorB)", data=clean_formula_df).fit()
                anova_table = sm.stats.anova_lm(model, typ=2)

                ss_a = float(anova_table.loc["C(FactorA)", "sum_sq"])
                df_a = int(anova_table.loc["C(FactorA)", "df"])
                f_a = float(anova_table.loc["C(FactorA)", "F"])
                p_a = float(anova_table.loc["C(FactorA)", "PR(>F)"])

                ss_b = float(anova_table.loc["C(FactorB)", "sum_sq"])
                df_b = int(anova_table.loc["C(FactorB)", "df"])
                f_b = float(anova_table.loc["C(FactorB)", "F"])
                p_b = float(anova_table.loc["C(FactorB)", "PR(>F)"])

                ss_ab = float(anova_table.loc["C(FactorA):C(FactorB)", "sum_sq"])
                df_ab = int(anova_table.loc["C(FactorA):C(FactorB)", "df"])
                f_ab = float(anova_table.loc["C(FactorA):C(FactorB)", "F"])
                p_ab = float(anova_table.loc["C(FactorA):C(FactorB)", "PR(>F)"])

                ss_err = float(anova_table.loc["Residual", "sum_sq"])
                df_err = int(anova_table.loc["Residual", "df"])
                ms_err = ss_err / df_err if df_err > 0 else 0.0

                ms_a = ss_a / df_a if df_a > 0 else 0.0
                ms_b = ss_b / df_b if df_b > 0 else 0.0
                ms_ab = ss_ab / df_ab if df_ab > 0 else 0.0

                ss_total = ss_a + ss_b + ss_ab + ss_err
                df_total = df_a + df_b + df_ab + df_err

                return {
                    "success": True,
                    "engine": "statsmodels",
                    "summary": {
                        "n_total": N,
                        "factor_a_name": factor_a_col,
                        "factor_b_name": factor_b_col
                    },
                    "results": {
                        "factor_a": {
                            "name": factor_a_col,
                            "ss": ss_a,
                            "df": df_a,
                            "ms": ms_a,
                            "f_statistic": f_a,
                            "p_value": p_a
                        },
                        "factor_b": {
                            "name": factor_b_col,
                            "ss": ss_b,
                            "df": df_b,
                            "ms": ms_b,
                            "f_statistic": f_b,
                            "p_value": p_b
                        },
                        "interaction": {
                            "name": f"{factor_a_col} x {factor_b_col}",
                            "ss": ss_ab,
                            "df": df_ab,
                            "ms": ms_ab,
                            "f_statistic": f_ab,
                            "p_value": p_ab
                        },
                        "residual": {
                            "ss": ss_err,
                            "df": df_err,
                            "ms": ms_err
                        },
                        "total": {
                            "ss": ss_total,
                            "df": df_total
                        }
                    }
                }
            except Exception:
                # Fallback to pure SciPy / NumPy sum of squares matrix calculations
                pass

            # SciPy / NumPy direct sum of squares calculation
            grand_mean = float(clean_df[value_col].mean())
            ss_total = float(((clean_df[value_col] - grand_mean) ** 2).sum())
            df_total = N - 1

            a_means = clean_df.groupby(factor_a_col)[value_col].mean()
            a_counts = clean_df.groupby(factor_a_col)[value_col].count()
            ss_a = float((a_counts * ((a_means - grand_mean) ** 2)).sum())
            df_a = len(a_means) - 1

            b_means = clean_df.groupby(factor_b_col)[value_col].mean()
            b_counts = clean_df.groupby(factor_b_col)[value_col].count()
            ss_b = float((b_counts * ((b_means - grand_mean) ** 2)).sum())
            df_b = len(b_means) - 1

            ab_means = clean_df.groupby([factor_a_col, factor_b_col])[value_col].mean()
            ab_counts = clean_df.groupby([factor_a_col, factor_b_col])[value_col].count()

            ss_cells = 0.0
            for (fa, fb), cell_mean in ab_means.items():
                c_cnt = ab_counts[(fa, fb)]
                ss_cells += float(c_cnt * ((cell_mean - grand_mean) ** 2))

            ss_ab = float(ss_cells - ss_a - ss_b)
            df_ab = df_a * df_b

            ss_error = float(ss_total - ss_cells)
            df_error = N - len(ab_means)

            if df_a <= 0 or df_b <= 0 or df_error <= 0:
                return {"success": False, "error": "Insufficient degrees of freedom for Two-Way ANOVA."}

            ms_a = ss_a / df_a
            ms_b = ss_b / df_b
            ms_ab = ss_ab / df_ab if df_ab > 0 else 0.0
            ms_error = ss_error / df_error

            f_a = ms_a / ms_error
            f_b = ms_b / ms_error
            f_ab = ms_ab / ms_error if df_ab > 0 else 0.0

            p_a = float(stats.f.sf(f_a, df_a, df_error))
            p_b = float(stats.f.sf(f_b, df_b, df_error))
            p_ab = float(stats.f.sf(f_ab, df_ab, df_error)) if df_ab > 0 else 1.0

            return {
                "success": True,
                "engine": "scipy_fallback",
                "summary": {
                    "n_total": N,
                    "factor_a_name": factor_a_col,
                    "factor_b_name": factor_b_col
                },
                "results": {
                    "factor_a": {
                        "name": factor_a_col,
                        "ss": ss_a,
                        "df": df_a,
                        "ms": ms_a,
                        "f_statistic": float(f_a),
                        "p_value": p_a
                    },
                    "factor_b": {
                        "name": factor_b_col,
                        "ss": ss_b,
                        "df": df_b,
                        "ms": ms_b,
                        "f_statistic": float(f_b),
                        "p_value": p_b
                    },
                    "interaction": {
                        "name": f"{factor_a_col} x {factor_b_col}",
                        "ss": ss_ab,
                        "df": df_ab,
                        "ms": ms_ab,
                        "f_statistic": float(f_ab),
                        "p_value": p_ab
                    },
                    "residual": {
                        "ss": ss_error,
                        "df": df_error,
                        "ms": ms_error
                    },
                    "total": {
                        "ss": ss_total,
                        "df": df_total
                    }
                }
            }
        except Exception as exc:
            return {"success": False, "error": f"Two-Way ANOVA calculation failed: {str(exc)}"}

```

## File Path: src/analysis/survival_engine.py
```python
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

```

## File Path: src/ui/table_view.py
```python
"""
VibePad Schism Interactive Data Grid Layer.

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

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QInputDialog
from PyQt6.QtCore import pyqtSignal
from src.data_engine.table_model import ScientificTableModel


class ScientificTableWidget(QTableWidget):
    """Interactive Qt table widget synchronized with an underlying ScientificTableModel data matrix.

    Provides high-contrast GraphPad Prism-style spreadsheet grid styling, dynamic cell entry
    validation, column header double-click renaming, and signal decoupling to prevent recursive feedback cascades.

    Signals:
        column_header_renamed (int, str, str): Emitted when a header is renamed.
            Args: (column_index, old_header_name, new_header_name)
    """

    column_header_renamed = pyqtSignal(int, str, str)  # (column_index, old_name, new_name)

    def __init__(self, model: ScientificTableModel, parent=None) -> None:
        """Initializes an interactive on-screen grid synchronized with a data engine matrix.

        Args:
            model (ScientificTableModel): Underlying scientific data model.
            parent (QWidget, optional): Qt parent widget reference. Defaults to None.
        """
        super().__init__(parent)
        self.data_model = model
        self.init_grid()

    def init_grid(self) -> None:
        """Sets up the initial grid boundaries, loads header labels, and links cell event slots."""
        # Query our data model's default structure to define column dimensions
        columns = list(self.data_model._data_frame.columns)
        
        self.setColumnCount(len(columns))
        self.setRowCount(50)  # Provide 50 default empty rows for spreadsheet entry
        self.setHorizontalHeaderLabels(columns)

        self.apply_stylesheet()

        # Connect cell interactions to custom backend update trigger slot
        self.cellChanged.connect(self.handle_cell_edited)

        # Connect double click on column header to trigger interactive rename dialog
        self.horizontalHeader().sectionDoubleClicked.connect(self.handle_header_double_clicked)

    def handle_header_double_clicked(self, logical_index: int) -> None:
        """Spawns an edit dialog to rename column headers and updates data model mapping.

        Args:
            logical_index (int): Zero-based column index of double-clicked header.
        """
        header_item = self.horizontalHeaderItem(logical_index)
        old_name = header_item.text() if header_item else f"Col{logical_index+1}"
        
        new_name, ok = QInputDialog.getText(
            self,
            "Edit Column Header Label",
            f"Enter new variable label for Column {logical_index + 1}:",
            text=old_name
        )
        if ok and new_name and new_name.strip() and new_name.strip() != old_name:
            clean_name = new_name.strip()
            self.data_model.rename_column(old_name, clean_name)
            self.setHorizontalHeaderItem(logical_index, QTableWidgetItem(clean_name))
            self.column_header_renamed.emit(logical_index, old_name, clean_name)

    def apply_stylesheet(self) -> None:
        """Applies GraphPad Prism-style high contrast spreadsheet grid styling stylesheet rules."""
        self.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                color: #000000;
                gridline-color: #d0d0d0;
                selection-background-color: #b3d8ff;
                selection-color: #000000;
                border: 1px solid #3d3d3d;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace, sans-serif;
                font-size: 12px;
            }
            QTableWidget::item {
                background-color: #ffffff;
                color: #000000;
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #b3d8ff;
                color: #000000;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                color: #000000;
                font-weight: bold;
                border: 1px solid #c0c0c0;
                padding: 4px;
            }
            QTableCornerButton::section {
                background-color: #e0e0e0;
                border: 1px solid #c0c0c0;
            }
            QTableWidget QLineEdit {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #0284c7;
                selection-color: #ffffff;
            }
        """)

    def handle_cell_edited(self, row: int, column: int) -> None:
        """Triggered automatically when a user edits a cell value in the spreadsheet.

        SIGNAL DECOUPLING RATIONALE:
            Disconnects the `cellChanged` signal before updating internal model data or clearing cell
            text, then reconnects `cellChanged` immediately afterwards. This temporary unhooking
            prevents recursive call loops (infinite event recursion) where programmatically altering a
            cell item causes Qt to re-fire `cellChanged`.

        Args:
            row (int): Zero-based row coordinate of edited cell.
            column (int): Zero-based column coordinate of edited cell.
        """
        item = self.item(row, column)
        if not item or not item.text().strip():
            return

        column_name = self.horizontalHeaderItem(column).text()
        raw_text = item.text()

        try:
            # Parse user input to floating-point value for scientific dataset validation
            numeric_value = float(raw_text)
            
            # Temporarily disconnect listener to decouple UI cell updates from signal cascades
            self.cellChanged.disconnect(self.handle_cell_edited)
            
            self.data_model.set_value(row, column_name, numeric_value)
            
            # Reconnect the signal listener after safe data insertion
            self.cellChanged.connect(self.handle_cell_edited)
        except ValueError:
            # If entry is not a valid number, erase it visually to preserve mathematical data hygiene
            item.setText("")

```

## File Path: src/ui/plot_canvas.py
```python
"""
VibePad Schism Real-Time Scientific Plot Canvas.

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
import pyqtgraph as pg
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QToolBar, QDialog, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QSpinBox, QColorDialog, QDialogButtonBox, QMessageBox,
    QFileDialog, QInputDialog, QGraphicsItem, QHBoxLayout, QCheckBox, QLabel
)
from PyQt6.QtGui import QPainter, QPdfWriter, QPageSize, QAction, QColor
from PyQt6.QtCore import Qt, QRect, QRectF


class SchismTextItem(pg.TextItem):
    """Custom pyqtgraph TextItem with unconstrained ViewBox bounds and interactive double-click dialog.

    Overrides `dataBounds` to return `(None, None)`, ensuring ViewBox auto-range scaling algorithms
    ignore text annotations so dragging labels into margins does not cause graph jumps or zoom resets.

    Attributes:
        parent_canvas (ScientificPlotCanvas, optional): Parent canvas reference.
        angle (float): Rotation angle in degrees (-360 to 360).
    """

    def __init__(
        self, 
        text: str = "Double-click to edit", 
        anchor: tuple = (0.5, 0.5), 
        parent_canvas: QWidget = None, 
        color: tuple = (30, 41, 59)
    ) -> None:
        """Initializes a draggable, non-clipping text annotation graphics item.

        Args:
            text (str, optional): Default annotation label string. Defaults to "Double-click to edit".
            anchor (tuple, optional): (x, y) relative text anchor point. Defaults to (0.5, 0.5).
            parent_canvas (QWidget, optional): Canvas container. Defaults to None.
            color (tuple, optional): RGB color tuple. Defaults to (30, 41, 59).
        """
        super().__init__(text=text, anchor=anchor, color=color)
        self.parent_canvas = parent_canvas
        self.angle = 0
        self.setZValue(100)  # Render on top of grid lines, axis ticks, and plot borders (Z=100)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsToShape, False)

    def dataBounds(self, ax: int, frac: float = 1.0, orthoRange: tuple = None) -> tuple:
        """Overrides data bounds calculation to return (None, None).

        VIEWBOX RATIONALE:
            By returning (None, None), pyqtgraph's ViewBox auto-range algorithm excludes this text item
            when computing bounding boxes for graph datasets. This allows annotations to be placed in
            the plot margins (GraphPad style) without expanding axis limits or causing graph jumps.

        Args:
            ax (int): Axis index (0 for X, 1 for Y).
            frac (float, optional): Fraction of data range to include. Defaults to 1.0.
            orthoRange (tuple, optional): Orthogonal range constraint. Defaults to None.

        Returns:
            tuple: Always (None, None) to disable data-bounding for text items.
        """
        return (None, None)

    def mouseDoubleClickEvent(self, ev) -> None:
        """Intercepts double-click events to launch the interactive TextEditDialog.

        Args:
            ev (QGraphicsSceneMouseEvent): Mouse double-click event payload.
        """
        if ev.button() == Qt.MouseButton.LeftButton:
            dialog = TextEditDialog(self, parent=self.parent_canvas)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                dialog.apply_to_item()
            ev.accept()
        else:
            super().mouseDoubleClickEvent(ev)


class TextEditDialog(QDialog):
    """Dialog for customizing text annotations (string, font size, rotation angle, color, and deletion)."""

    def __init__(self, text_item: SchismTextItem, parent=None) -> None:
        """Initializes the annotation properties edit modal.

        Args:
            text_item (SchismTextItem): Target text item to edit.
            parent (QWidget, optional): Parent Qt widget. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Edit Text Annotation")
        self.resize(360, 260)
        self.text_item = text_item

        self.current_text = text_item.toPlainText()
        self.current_angle = getattr(text_item, "angle", 0)
        self.current_font_size = text_item.textItem.font().pointSize()
        if self.current_font_size <= 0:
            self.current_font_size = 12

        color_val = text_item.color
        if isinstance(color_val, QColor):
            self.current_color = color_val.name()
        elif isinstance(color_val, (tuple, list)):
            self.current_color = QColor(*color_val[:3]).name()
        else:
            self.current_color = "#1e293b"

        self.deleted = False
        self.init_ui()

    def init_ui(self) -> None:
        """Constructs form layout fields for annotation editing."""
        layout = QVBoxLayout(self)
        grid = QFormLayout()

        # Text String Edit
        self.text_edit = QLineEdit(self.current_text)
        grid.addRow("Annotation Text:", self.text_edit)

        # Font Size Spinbox
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 72)
        self.font_size_spin.setValue(self.current_font_size)
        grid.addRow("Font Size (pt):", self.font_size_spin)

        # Rotation Angle (-360 to 360 degrees)
        self.angle_spin = QSpinBox()
        self.angle_spin.setRange(-360, 360)
        self.angle_spin.setValue(int(self.current_angle))
        self.angle_spin.setSuffix("°")
        grid.addRow("Angle (degrees):", self.angle_spin)

        # Text Color Picker Button
        self.color_btn = QPushButton()
        self.update_color_button()
        self.color_btn.clicked.connect(self.choose_color)
        grid.addRow("Text Color:", self.color_btn)

        layout.addLayout(grid)

        # Bottom Action Strip
        btn_layout = QHBoxLayout()

        self.delete_btn = QPushButton("🗑️ Delete Annotation")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: #ffffff;
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        self.delete_btn.clicked.connect(self.on_delete)
        btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        btn_layout.addWidget(btn_box)

        layout.addLayout(btn_layout)

    def update_color_button(self) -> None:
        """Refreshes color picker button background and dynamic text contrast."""
        self.color_btn.setText(self.current_color)
        c = QColor(self.current_color)
        # Compute perceived luminance: (299*R + 587*G + 114*B) / 1000
        is_dark = (c.red() * 299 + c.green() * 587 + c.blue() * 114) / 1000 < 128
        fg = "#ffffff" if is_dark else "#000000"
        self.color_btn.setStyleSheet(
            f"background-color: {self.current_color}; color: {fg}; font-weight: bold; border-radius: 4px; padding: 4px;"
        )

    def choose_color(self) -> None:
        """Spawns QColorDialog color selection tool."""
        color = QColorDialog.getColor(QColor(self.current_color), self, "Select Text Color")
        if color.isValid():
            self.current_color = color.name()
            self.update_color_button()

    def on_delete(self) -> None:
        """Flags item for deletion and closes dialog with Accepted result."""
        self.deleted = True
        self.accept()

    def apply_to_item(self) -> None:
        """Applies configured text, rotation angle, font size, and color back to the target item."""
        if self.deleted:
            if self.text_item.parent_canvas and hasattr(self.text_item.parent_canvas, "plot_widget"):
                self.text_item.parent_canvas.plot_widget.removeItem(self.text_item)
            return

        self.text_item.setText(self.text_edit.text())

        angle_val = self.angle_spin.value()
        self.text_item.angle = angle_val
        self.text_item.setAngle(angle_val)

        font = self.text_item.textItem.font()
        font.setPointSize(self.font_size_spin.value())
        self.text_item.setFont(font)

        self.text_item.setColor(QColor(self.current_color))


class FormatGraphDialog(QDialog):
    """Dialog for customizing plot series visual properties (Color, Symbol, Line Style, Sizes)."""

    def __init__(self, column_name: str, style_dict: dict, parent=None) -> None:
        """Initializes the series formatting configuration dialog.

        Args:
            column_name (str): Column series header name.
            style_dict (dict): Dictionary of current visual style attributes.
            parent (QWidget, optional): Parent Qt widget. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle(f"Format Series: {column_name}")
        self.resize(340, 240)
        self.column_name = column_name
        self.current_color = style_dict.get("color", "#0072BD")
        self.current_symbol = style_dict.get("symbol", "o")
        self.current_line_style = style_dict.get("line_style", "Solid")
        self.current_symbol_size = style_dict.get("symbol_size", 10)
        self.current_line_width = style_dict.get("line_width", 2)

        self.init_ui()

    def init_ui(self) -> None:
        """Constructs form controls for series styling."""
        layout = QVBoxLayout(self)
        grid = QFormLayout()

        # Color Picker Button
        self.color_btn = QPushButton()
        self.update_color_button()
        self.color_btn.clicked.connect(self.choose_color)
        grid.addRow("Series Color:", self.color_btn)

        # Symbol Selector Dropdown
        self.symbol_combo = QComboBox()
        self.symbols = [
            ("Circle (o)", "o"),
            ("Square (s)", "s"),
            ("Triangle (t)", "t"),
            ("Diamond (d)", "d"),
            ("Star (star)", "star"),
            ("Pentagon (p)", "p"),
            ("Hexagon (h)", "h"),
            ("None", None)
        ]
        for label, val in self.symbols:
            self.symbol_combo.addItem(label, val)
            if val == self.current_symbol:
                self.symbol_combo.setCurrentIndex(self.symbol_combo.count() - 1)
        grid.addRow("Plot Symbol:", self.symbol_combo)

        # Symbol Size Spinbox
        self.symbol_size_spin = QSpinBox()
        self.symbol_size_spin.setRange(4, 30)
        self.symbol_size_spin.setValue(int(self.current_symbol_size))
        grid.addRow("Symbol Size:", self.symbol_size_spin)

        # Line Style Dropdown
        self.line_style_combo = QComboBox()
        self.line_styles = ["Solid", "Dash", "Dot", "DashDot", "None"]
        self.line_style_combo.addItems(self.line_styles)
        if self.current_line_style in self.line_styles:
            self.line_style_combo.setCurrentText(self.current_line_style)
        grid.addRow("Line Style:", self.line_style_combo)

        # Line Width Spinbox
        self.line_width_spin = QSpinBox()
        self.line_width_spin.setRange(1, 10)
        self.line_width_spin.setValue(int(self.current_line_width))
        grid.addRow("Line Width:", self.line_width_spin)

        layout.addLayout(grid)

        # OK / Cancel Dialog Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def update_color_button(self) -> None:
        """Updates color preview button stylesheet."""
        self.color_btn.setText(self.current_color)
        is_dark = self.is_dark_color(self.current_color)
        fg = "#ffffff" if is_dark else "#000000"
        self.color_btn.setStyleSheet(
            f"background-color: {self.current_color}; color: {fg}; font-weight: bold; border-radius: 4px; padding: 4px;"
        )

    def is_dark_color(self, hex_color: str) -> bool:
        """Determines whether a hex color is dark based on ITU-R BT.601 luminance.

        Args:
            hex_color (str): Hex color code string (e.g. '#0072BD').

        Returns:
            bool: True if perceived luminance < 128, False otherwise.
        """
        try:
            c = QColor(hex_color)
            return (c.red() * 299 + c.green() * 587 + c.blue() * 114) / 1000 < 128
        except Exception:
            return False

    def choose_color(self) -> None:
        """Spawns QColorDialog to pick series color."""
        color = QColorDialog.getColor(QColor(self.current_color), self, f"Select Color for {self.column_name}")
        if color.isValid():
            self.current_color = color.name()
            self.update_color_button()

    def get_style_dict(self) -> dict:
        """Returns the formatted style properties dictionary.

        Returns:
            dict: Style properties dictionary containing 'color', 'symbol', 'symbol_size', 'line_style', 'line_width'.
        """
        return {
            "color": self.current_color,
            "symbol": self.symbol_combo.currentData(),
            "symbol_size": self.symbol_size_spin.value(),
            "line_style": self.line_style_combo.currentText(),
            "line_width": self.line_width_spin.value()
        }


class ClickablePlotDataItem(pg.PlotDataItem):
    """PlotDataItem subclass that triggers series formatting dialog on click or double-click events."""

    def __init__(self, col_name: str, on_double_click: callable, *args, **kwargs) -> None:
        """Initializes a clickable series plot item.

        Args:
            col_name (str): Associated dataset column name.
            on_double_click (callable): Callback function invoked when item is double-clicked.
        """
        super().__init__(*args, **kwargs)
        self.col_name = col_name
        self.on_double_click = on_double_click
        self.sigClicked.connect(self._on_sig_clicked)

    def _on_sig_clicked(self, item, ev) -> None:
        if self.on_double_click:
            self.on_double_click(self.col_name)

    def mouseDoubleClickEvent(self, ev) -> None:
        if self.on_double_click:
            self.on_double_click(self.col_name)
        ev.accept()


class ScientificPlotCanvas(QWidget):
    """Real-time pyqtgraph scientific plot canvas supporting XY scatter, Bar Charts, and Box Plots."""

    def __init__(self, parent=None) -> None:
        """Initializes the scientific plot canvas widget.

        Args:
            parent (QWidget, optional): Qt parent container. Defaults to None.
        """
        super().__init__(parent)
        self.style_map = {}
        self._last_x_data = np.array([], dtype=float)
        self._last_y_datasets_dict = {}
        self._last_fit_curve_y = None
        self._last_active_model = None
        self._updating_controls = False
        self.init_canvas()

    def init_canvas(self) -> None:
        """Configures canvas toolbars, pyqtgraph PlotWidget, and scientific axis layout properties."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Primary Action Toolbar Strip ---
        self.toolbar = QToolBar("Plot Tools", self)
        self.toolbar.setFixedHeight(32)

        # Add Text Annotation Action
        add_text_action = QAction("➕ Add Text (T)", self)
        add_text_action.setToolTip("Add draggable text annotation to graph canvas")
        add_text_action.triggered.connect(self.add_text_annotation)
        self.toolbar.addAction(add_text_action)

        self.toolbar.addSeparator()

        # Export Plot Action
        export_action = QAction("📤 Export Plot...", self)
        export_action.setToolTip("Save plot as PNG image or PDF document")
        export_action.triggered.connect(self.export_plot)
        self.toolbar.addAction(export_action)

        layout.addWidget(self.toolbar)

        # --- Secondary Plot Configuration Control Toolbar ---
        self.controls_toolbar = QToolBar("Plot Configuration", self)
        self.controls_toolbar.setFixedHeight(34)
        self.controls_toolbar.setStyleSheet("background-color: #252525; border-bottom: 1px solid #3d3d3d;")

        type_label = QLabel(" 📈 Plot Type: ", self)
        type_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        self.controls_toolbar.addWidget(type_label)

        self.plot_type_combo = QComboBox(self)
        self.plot_type_combo.addItems(["XY Line Scatter", "Bar Chart", "Box Plot"])
        self.controls_toolbar.addWidget(self.plot_type_combo)

        self.controls_toolbar.addSeparator()

        self.show_error_bars_cb = QCheckBox("Display Error Bars", self)
        self.show_error_bars_cb.setChecked(True)
        self.show_error_bars_cb.setStyleSheet("color: #ffffff; margin-left: 6px;")
        self.controls_toolbar.addWidget(self.show_error_bars_cb)

        self.controls_toolbar.addSeparator()

        sd_label = QLabel(" SD Multiplier: ", self)
        sd_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        self.controls_toolbar.addWidget(sd_label)

        self.sd_multiplier_spin = QSpinBox(self)
        self.sd_multiplier_spin.setRange(1, 5)
        self.sd_multiplier_spin.setValue(1)
        self.controls_toolbar.addWidget(self.sd_multiplier_spin)

        self.plot_type_combo.currentTextChanged.connect(self._on_plot_controls_changed)
        self.show_error_bars_cb.toggled.connect(self._on_plot_controls_changed)
        self.sd_multiplier_spin.valueChanged.connect(self._on_plot_controls_changed)

        layout.addWidget(self.controls_toolbar)

        # Create pyqtgraph PlotWidget element with high-contrast white background
        self.plot_widget = pg.PlotWidget(title="🔬 Experimental Analysis Workspace")
        self.plot_widget.setBackground('w')  # High-contrast white canvas background

        # Disable ViewBox clipping to allow dragging annotations into axis margins without truncation
        self.plot_widget.plotItem.setClipToView(False)
        view_box = self.plot_widget.plotItem.getViewBox()
        view_box.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape, False)
        view_box.setDefaultPadding(0.05)

        # Configure crisp scientific axis labels and grid styling
        self.plot_widget.setLabel('bottom', 'Independent Variable (X-Axis)', colors='k')
        self.plot_widget.setLabel('left', 'Dependent Variable (Y-Axis)', colors='k')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.15)

        layout.addWidget(self.plot_widget)

    def reset_axis_ticks(self) -> None:
        """Clears custom category string tick mappings from axes, resetting to pure continuous linear scale."""
        self.plot_widget.getAxis('bottom').setTicks(None)
        self.plot_widget.getAxis('left').setTicks(None)

    def _on_plot_controls_changed(self) -> None:
        """Slot invoked when user toggles plot type, error bar checkbox, or SD multiplier spinbox."""
        if self._updating_controls:
            return
        plot_type = self.plot_type_combo.currentText()

        # Always reset custom axis string mappings before switching graph types
        self.reset_axis_ticks()

        if self._last_active_model:
            if plot_type == "Bar Chart":
                self.render_grouped_bar_chart(self._last_active_model)
            elif plot_type == "Box Plot":
                self.render_box_plot(self._last_active_model)
            elif plot_type == "XY Line Scatter":
                self.replot_current()
        else:
            self.replot_current()

    def add_text_annotation(self) -> None:
        """Spawns a SchismTextItem annotation centered in the active plot view coordinates."""
        view_box = self.plot_widget.plotItem.getViewBox()
        rect = view_box.viewRect()
        center_x = rect.center().x()
        center_y = rect.center().y()

        text_item = SchismTextItem(
            text="Double-click to edit",
            anchor=(0.5, 0.5),
            parent_canvas=self,
            color=(30, 41, 59)
        )
        text_item.setZValue(100)
        text_item.setPos(center_x, center_y)
        self.plot_widget.addItem(text_item)

    def open_format_dialog(self, column_name: str) -> None:
        """Opens FormatGraphDialog for the specified column dataset series."""
        style = self.style_map.get(column_name, {})
        dialog = FormatGraphDialog(column_name, style, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.style_map[column_name] = dialog.get_style_dict()
            self.replot_current()

    def replot_current(self) -> None:
        """Re-renders current dataset vectors with updated style_map formatting."""
        if self._last_x_data.size > 0 and self._last_y_datasets_dict:
            self.refresh_plot(self._last_x_data, self._last_y_datasets_dict, self._last_fit_curve_y)

    def _create_pen(self, color_hex: str, line_style: str, line_width: int) -> pg.mkPen:
        """Factory method to construct QPen style instances for pyqtgraph rendering."""
        if line_style == "None":
            return pg.mkPen(None)
        
        style_map = {
            "Solid": Qt.PenStyle.SolidLine,
            "Dash": Qt.PenStyle.DashLine,
            "Dot": Qt.PenStyle.DotLine,
            "DashDot": Qt.PenStyle.DashDotLine
        }
        qt_style = style_map.get(line_style, Qt.PenStyle.SolidLine)
        return pg.mkPen(color=color_hex, width=line_width, style=qt_style)

    def refresh_plot(self, x_data: np.ndarray, y_datasets_dict: dict, fit_curve_y: np.ndarray = None) -> None:
        """Refreshes plots with updated coordinate vectors while preserving text annotations.

        Args:
            x_data (np.ndarray): Vector of X-axis numeric coordinates.
            y_datasets_dict (dict): Dictionary mapping column titles to 1D Y-data NumPy arrays.
            fit_curve_y (np.ndarray, optional): Fitted regression Y values. Defaults to None.
        """
        self._last_x_data = x_data
        self._last_fit_curve_y = fit_curve_y

        # Reset bottom axis ticks to continuous linear numeric scale
        self.reset_axis_ticks()

        # Handle 1D array fallback
        if isinstance(y_datasets_dict, np.ndarray):
            y_datasets_dict = {"Y1": y_datasets_dict}
        elif not isinstance(y_datasets_dict, dict):
            y_datasets_dict = {}

        self._last_y_datasets_dict = y_datasets_dict

        # Clear obsolete plot items while explicitly preserving SchismTextItem / TextItem annotations
        for item in list(self.plot_widget.items()):
            if not isinstance(item, (pg.TextItem, SchismTextItem, pg.AxisItem, pg.ViewBox)):
                try:
                    self.plot_widget.removeItem(item)
                except Exception:
                    pass

        if x_data.size < 1 or not y_datasets_dict:
            return

        default_colors = ["#0072BD", "#D95319", "#EDB120", "#7E2F8E", "#77AC30", "#4DBEEE", "#A2142F"]
        default_symbols = ['o', 's', 't', 'd', 'star', 'p', 'h']

        for idx, (col_name, y_vec) in enumerate(y_datasets_dict.items()):
            if not isinstance(y_vec, np.ndarray) or y_vec.size != x_data.size:
                continue

            if col_name not in self.style_map:
                color = default_colors[idx % len(default_colors)]
                symbol = default_symbols[idx % len(default_symbols)]
                self.style_map[col_name] = {
                    "color": color,
                    "symbol": symbol,
                    "symbol_size": 10,
                    "line_style": "Solid",
                    "line_width": 2
                }

            style = self.style_map[col_name]
            pen = self._create_pen(
                style.get("color", "#0072BD"),
                style.get("line_style", "Solid"),
                style.get("line_width", 2)
            )

            symbol = style.get("symbol", "o")
            symbol_size = style.get("symbol_size", 10)
            symbol_brush = pg.mkBrush(style.get("color", "#0072BD"))

            plot_item = ClickablePlotDataItem(
                col_name=col_name,
                on_double_click=self.open_format_dialog,
                x=x_data,
                y=y_vec,
                pen=pen,
                symbol=symbol,
                symbolSize=symbol_size,
                symbolBrush=symbol_brush,
                symbolPen=pg.mkPen('k', width=1),
                clickable=True
            )
            self.plot_widget.addItem(plot_item)

        # Render optional non-linear regression curve overlay
        if fit_curve_y is not None and fit_curve_y.size == x_data.size:
            fit_curve_item = pg.PlotDataItem(
                x=x_data, y=fit_curve_y,
                pen=pg.mkPen(217, 83, 25, 255, width=2)
            )
            self.plot_widget.addItem(fit_curve_item)

    def render_grouped_bar_chart(self, model) -> None:
        """Renders a GraphPad Prism-style grouped vertical bar chart (pg.BarGraphItem).

        Calculates group offsets and error whiskers (Mean +/- multiplier * SD) using
        solid black styling (#000000) for error bars.

        Args:
            model (ScientificTableModel): Target table data model to render.
        """
        self._last_active_model = model
        self._updating_controls = True
        self.plot_type_combo.setCurrentText("Bar Chart")
        self._updating_controls = False

        self.reset_axis_ticks()

        # Clear existing plot graphics items (retaining text annotations)
        for item in list(self.plot_widget.items()):
            if not isinstance(item, (pg.TextItem, SchismTextItem, pg.AxisItem, pg.ViewBox)):
                try:
                    self.plot_widget.removeItem(item)
                except Exception:
                    pass

        if not hasattr(model, "_data_frame") or model._data_frame.empty:
            return

        cols = list(model._data_frame.columns)
        x_col = None
        for c in cols:
            if str(c).upper() == "X":
                x_col = c
                break

        if x_col:
            categories = model.get_column_data(x_col)
            y_cols = [c for c in cols if c != x_col]
        else:
            categories = np.array([f"Group {i+1}" for i in range(len(model._data_frame))])
            y_cols = cols

        if not y_cols:
            return

        num_categories = len(categories)
        num_series = len(y_cols)
        if num_categories == 0 or num_series == 0:
            return

        default_colors = ["#0284c7", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6"]

        # Calculate category spacing coordinates and bar width offsets: W_bar = W_group / N_series
        group_width = 0.8
        bar_width = group_width / max(1, num_series)
        category_positions = np.arange(num_categories, dtype=float) * 1.5

        ticks = []
        for cat_idx, cat_val in enumerate(categories):
            ticks.append((category_positions[cat_idx], str(cat_val)))

        ax = self.plot_widget.getAxis('bottom')
        ax.setTicks([ticks])

        sd_mult = self.sd_multiplier_spin.value()
        show_err = self.show_error_bars_cb.isChecked()

        for series_idx, col_name in enumerate(y_cols):
            data_vec = model.get_column_data(col_name)
            if data_vec.size == 0:
                continue

            if data_vec.size == num_categories:
                means = data_vec
                std_val = float(np.std(data_vec, ddof=1)) if data_vec.size > 1 else 0.0
                errors = np.full(num_categories, std_val * sd_mult)
            else:
                mean_val = float(np.mean(data_vec))
                std_val = float(np.std(data_vec, ddof=1)) if data_vec.size > 1 else 0.0
                err_val = float(std_val * sd_mult)
                means = np.full(num_categories, mean_val)
                errors = np.full(num_categories, err_val)

            # Compute horizontal bar coordinate offsets relative to category center
            offset = - (group_width / 2.0) + (series_idx + 0.5) * bar_width
            x_pos = category_positions + offset

            color = default_colors[series_idx % len(default_colors)]
            brush = pg.mkBrush(color)
            pen = pg.mkPen('#000000', width=1.5)

            # 1. Add BarGraphItem for column series
            bg = pg.BarGraphItem(
                x=x_pos,
                height=means,
                width=bar_width * 0.9,
                brush=brush,
                pen=pen
            )
            self.plot_widget.addItem(bg)

            # 2. Add ErrorBarItem whiskers in high-contrast solid black (#000000)
            if show_err and np.any(errors > 0):
                err = pg.ErrorBarItem(
                    x=x_pos,
                    y=means,
                    top=errors,
                    bottom=errors,
                    beam=bar_width * 0.3,
                    pen=pg.mkPen('#000000', width=1.5)
                )
                self.plot_widget.addItem(err)

        self.plot_widget.setLabel('left', f'Result (Mean ± {sd_mult}x SD)', colors='k')
        self.plot_widget.setLabel('bottom', x_col if x_col else 'Categories / Datasets', colors='k')

    def render_box_plot(self, model) -> None:
        """Renders a scientific Box Plot (Median, IQR, Whiskers) using pg.BarGraphItem and pg.ErrorBarItem.

        Args:
            model (ScientificTableModel): Data model containing column distributions.
        """
        self._last_active_model = model
        self._updating_controls = True
        self.plot_type_combo.setCurrentText("Box Plot")
        self._updating_controls = False

        self.reset_axis_ticks()

        for item in list(self.plot_widget.items()):
            if not isinstance(item, (pg.TextItem, SchismTextItem, pg.AxisItem, pg.ViewBox)):
                try:
                    self.plot_widget.removeItem(item)
                except Exception:
                    pass

        if not hasattr(model, "_data_frame") or model._data_frame.empty:
            return

        cols = list(model._data_frame.columns)
        y_cols = [c for c in cols if str(c).upper() != "X"]
        if not y_cols:
            y_cols = cols

        num_series = len(y_cols)
        if num_series == 0:
            return

        default_colors = ["#0284c7", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6"]
        positions = np.arange(num_series, dtype=float) * 1.5

        ticks = [(positions[idx], str(col_name)) for idx, col_name in enumerate(y_cols)]
        ax = self.plot_widget.getAxis('bottom')
        ax.setTicks([ticks])

        sd_mult = self.sd_multiplier_spin.value()
        show_err = self.show_error_bars_cb.isChecked()

        for idx, col_name in enumerate(y_cols):
            data_vec = model.get_column_data(col_name)
            if data_vec.size == 0:
                continue

            # Calculate 25th percentile (Q1), Median (Q2), 75th percentile (Q3), and Interquartile Range (IQR)
            q25 = float(np.percentile(data_vec, 25)) if data_vec.size > 1 else float(data_vec[0])
            q50 = float(np.median(data_vec))
            q75 = float(np.percentile(data_vec, 75)) if data_vec.size > 1 else float(data_vec[0])
            iqr = q75 - q25

            color = default_colors[idx % len(default_colors)]
            x_p = positions[idx]

            # Render IQR box container spanning Q25 to Q75
            bg = pg.BarGraphItem(
                x=[x_p],
                height=[iqr if iqr > 0 else 0.1],
                y0=[q25],
                width=0.5,
                brush=pg.mkBrush(color),
                pen=pg.mkPen('#000000', width=1.5)
            )
            self.plot_widget.addItem(bg)

            # Render solid black line at Median (Q50) location
            med_line = pg.PlotDataItem(
                x=[x_p - 0.25, x_p + 0.25],
                y=[q50, q50],
                pen=pg.mkPen('#000000', width=2.5)
            )
            self.plot_widget.addItem(med_line)

            # Render whisker bounds (SD * multiplier)
            if show_err:
                std_val = float(np.std(data_vec, ddof=1)) if data_vec.size > 1 else 0.0
                err_delta = std_val * sd_mult
                err = pg.ErrorBarItem(
                    x=np.array([x_p]),
                    y=np.array([q50]),
                    top=np.array([err_delta]),
                    bottom=np.array([err_delta]),
                    beam=0.3,
                    pen=pg.mkPen('#000000', width=1.5)
                )
                self.plot_widget.addItem(err)

        self.plot_widget.setLabel('left', f'Distribution (Median / IQR ± {sd_mult}x SD)', colors='k')
        self.plot_widget.setLabel('bottom', 'Experimental Variables / Columns', colors='k')

    # -------------------------------------------------------------------------
    # Export Pipeline
    # -------------------------------------------------------------------------

    def export_plot(self) -> None:
        """Launches a native save file dialog to export the active plot view as PNG or PDF."""
        filepath, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Plot",
            "plot_export",
            "PNG Image (*.png);;PDF Document (*.pdf)"
        )

        if not filepath:
            return

        try:
            if selected_filter == "PNG Image (*.png)":
                if not filepath.lower().endswith(".png"):
                    filepath += ".png"
                self._export_as_png(filepath)

            elif selected_filter == "PDF Document (*.pdf)":
                if not filepath.lower().endswith(".pdf"):
                    filepath += ".pdf"
                self._export_as_pdf(filepath)

            QMessageBox.information(
                self,
                "✅ Export Successful",
                f"Plot saved successfully to:\n{filepath}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "❌ Export Failed",
                f"Could not write export file:\n{str(e)}"
            )

    def _export_as_png(self, filepath: str) -> None:
        """Exports the active PlotItem scene as a high-resolution 1920px PNG image."""
        from pyqtgraph.exporters import ImageExporter
        exporter = ImageExporter(self.plot_widget.plotItem)
        exporter.parameters()['width'] = 1920
        exporter.export(filepath)

    def _export_as_pdf(self, filepath: str) -> None:
        """Renders the active plot view into a vector-graphics A4 PDF document via QPdfWriter."""
        writer = QPdfWriter(filepath)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setResolution(300)

        painter = QPainter(writer)

        plot_item = self.plot_widget.getPlotItem()
        plot_item.setClipToView(True)

        try:
            target_rect = QRectF(10, 10, writer.width() - 20, writer.height() - 20)
            source_rect = QRect(0, 0, self.plot_widget.width(), self.plot_widget.height())
            self.plot_widget.render(painter, target_rect, source_rect)
        finally:
            plot_item.setClipToView(False)
            painter.end()

```

## File Path: src/ui/mediator.py
```python
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
from src.analysis.anova_two_way import TwoWayAnovaEngine
from src.analysis.survival_engine import KaplanMeierEngine
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
                QMessageBox.warning(parent_window, "⚠️ Selection Required", "Please select an analysis from the list.")
                return

            if not selected_cols:
                QMessageBox.warning(parent_window, "⚠️ Selection Required", "Please select at least one data set column to analyze.")
                return

            analysis_lower = analysis_name.lower()

            # Condition 1: Unpaired t tests and non-parametric comparisons
            if "t test" in analysis_lower or "t tests" in analysis_lower:
                if len(selected_cols) != 2:
                    QMessageBox.warning(
                        parent_window,
                        "⚠️ Selection Error",
                        f"Unpaired t-test requires exactly 2 data set columns selected (you checked {len(selected_cols)})."
                    )
                    return

                col_a, col_b = selected_cols[0], selected_cols[1]
                group_a = self.model.get_column_data(col_a)
                group_b = self.model.get_column_data(col_b)

                if group_a.size < 2 or group_b.size < 2:
                    QMessageBox.warning(
                        parent_window,
                        "⚠️ Insufficient Data",
                        f"Columns '{col_a}' and '{col_b}' must both contain at least 2 observations."
                    )
                    return

                analysis = TTestEngine.calculate_unpaired_t_test(group_a, group_b, equal_var=True)
                if not analysis["success"]:
                    QMessageBox.critical(parent_window, "❌ Math Exception", analysis["error"])
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
                QMessageBox.information(parent_window, f"🔬 Analysis Results — {analysis_name}", summary_msg)

            # Condition 2: Non-linear regression curve fitting
            elif "nonlinear" in analysis_lower or "curve fit" in analysis_lower or "regression" in analysis_lower:
                self.sync_data_to_visualization()
                QMessageBox.information(
                    parent_window,
                    "📈 Curve Fitting Executed",
                    f"Nonlinear regression curve fitting updated for data sets: {', '.join(selected_cols)}"
                )

            # Fallback for other analytical options
            else:
                QMessageBox.information(
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
            QMessageBox.warning(
                parent_window, 
                "⚠️ Insufficient Vectors", 
                "To compute an unpaired t-test, columns Y1 and Y2 must both contain at least 2 observations."
            )
            return

        analysis = TTestEngine.calculate_unpaired_t_test(group_a, group_b, equal_var=True)

        if not analysis["success"]:
            QMessageBox.critical(parent_window, "❌ Math Exception", analysis["error"])
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
        QMessageBox.information(parent_window, "🔬 Analysis Results", summary_msg)

    def execute_two_way_anova(self, parent_window) -> None:
        """Executes Two-Way ANOVA analysis on the active spreadsheet model if >= 3 columns exist.

        Args:
            parent_window (QWidget): Main window reference for dialog parenting.
        """
        cols = list(self.model._data_frame.columns)
        if len(cols) < 3:
            QMessageBox.warning(
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
            QMessageBox.critical(parent_window, "❌ Math Exception", analysis["error"])
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
        QMessageBox.information(parent_window, "🔬 Two-Way ANOVA Results", summary_msg)

        if self.center_stack:
            self.center_stack.setCurrentIndex(1)
        if self.results_browser:
            report_html = ScientificReportGenerator.generate_master_report(self.model)
            self.results_browser.setHtml(report_html)

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
            QMessageBox.warning(
                parent_window,
                "⚠️ Insufficient Columns",
                "Kaplan-Meier survival analysis requires Time and Event columns."
            )
            return

        time_data = self.model.get_column_data(time_col)
        event_data = self.model.get_column_data(event_col)

        analysis = KaplanMeierEngine.calculate_kaplan_meier(time_data, event_data)

        if not analysis["success"]:
            QMessageBox.critical(parent_window, "❌ Math Exception", analysis["error"])
            return

        summary = analysis["summary"]
        median_val = summary.get("median_survival", np.nan)
        median_str = f"{median_val:.2f}" if median_val is not None and not np.isnan(median_val) else "Undefined"
        summary_msg = (
            f"⏳ Kaplan-Meier Survival Analysis Summary\n"
            f"-----------------------------------------\n"
            f"• Total Subjects: {summary['n_total']}\n"
            f"• Total Events: {summary['total_events']}\n"
            f"• Total Censored: {summary['total_censored']}\n"
            f"• Estimated Median Survival Time: {median_str}\n"
        )
        QMessageBox.information(parent_window, "🔬 Kaplan-Meier Results", summary_msg)

        if self.center_stack:
            self.center_stack.setCurrentIndex(1)
        if self.results_browser:
            report_html = ScientificReportGenerator.generate_master_report(self.model)
            self.results_browser.setHtml(report_html)

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
                QMessageBox.information(parent_window, "💾 Success", f"Workspace dataset successfully saved to:\n{filepath}")
        else:
            if not silent:
                QMessageBox.critical(parent_window, "❌ Error", "Failed to write data safely to local disk path.")

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
            QMessageBox.warning(parent_window, "⚠️ Load Error", f"Failed to load .schism archive:\n{filepath}")
            return

        if hasattr(parent_window, "current_filepath"):
            parent_window.current_filepath = filepath
        if hasattr(parent_window, "update_recent_files_menu"):
            parent_window.update_recent_files_menu()

        if self.tree:
            self.tree.populate_models(models)
        else:
            self.display_sheet_model(models[0])

        QMessageBox.information(parent_window, "📂 Schism Archive Loaded", f"Successfully loaded {len(models)} sheet(s) from archive.")

    def open_recent_filepath(self, parent_window, filepath: str) -> None:
        """Opens a file path from the recent files menu, routing by extension (.schism, .prism, .csv).

        Args:
            parent_window (QWidget): Main window reference.
            filepath (str): Absolute file path to open.
        """
        if not os.path.exists(filepath):
            QMessageBox.warning(
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
                QMessageBox.critical(parent_window, "❌ Error", f"Failed to open Prism archive:\n{str(exc)}")
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
            QMessageBox.warning(
                parent_window,
                "⚠️ Parse Error",
                f"Failed to parse Prism archive:\n{str(exc)}"
            )
            return
        except Exception as exc:
            QMessageBox.critical(
                parent_window,
                "❌ Error",
                f"Unexpected error reading file:\n{str(exc)}"
            )
            return

        if not models:
            QMessageBox.warning(
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

        QMessageBox.information(
            parent_window,
            "📂 Prism Archive Loaded",
            f"Successfully loaded {len(models)} sheet(s) from Prism archive."
        )

```

## File Path: tests/test_math_engine.py
```python
import io
import json
import tempfile
import unittest
import zipfile
import numpy as np
import os
import sys

# Ensure the root directory is on the path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data_engine.table_model import ScientificTableModel
from src.analysis.curve_fitting import CurveFittingEngine, dose_response_model
from src.analysis.t_test import TTestEngine
from src.data_engine.file_handler import ScientificFileHandler
from src.data_engine.prism_parser import PrismParser, PrismParseError


class TestScientificMathEngine(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        import sys
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.quit()

    def setUp(self):
        """Instantiate a clean model before each individual unit test running."""
        self.model = ScientificTableModel(table_type="XY")

    def test_initial_columns(self):
        """Verify the data engine layout defaults cleanly to standard GraphPad XY structure."""
        expected_columns = ["X", "Y1", "Y2", "Y3"]
        self.assertEqual(list(self.model._data_frame.columns), expected_columns)

    def test_safe_value_insertion_and_padding(self):
        """Verify the data matrix builds out index frames safely without throwing index boundary leaks."""
        self.model.set_value(row=2, column_name="Y1", value=15.5)
        
        # Verify the structure auto-padded rows 0 and 1 with NaN values safely
        data_vector = self.model.get_column_data("Y1")
        self.assertEqual(len(data_vector), 1)
        self.assertEqual(data_vector[0], 15.5)

    def test_summary_statistics_calculations(self):
        """Verify statistical metrics match pure theoretical metrics accurately."""
        self.model.set_value(row=0, column_name="Y2", value=10.0)
        self.model.set_value(row=1, column_name="Y2", value=20.0)
        self.model.set_value(row=2, column_name="Y2", value=30.0)
        
        stats = self.model.get_summary_statistics("Y2")
        
        self.assertEqual(stats["count"], 3)
        self.assertAlmostEqual(stats["mean"], 20.0, places=4)
        self.assertAlmostEqual(stats["std"], 10.0, places=4)

    def test_malicious_type_rejection(self):
        """Ensure input validation safely drops text syntax attempts to prevent state corruption."""
        self.model.set_value(row=0, column_name="X", value="__import__('os').system('clear')")
        
        data_vector = self.model.get_column_data("X")
        self.assertEqual(data_vector.size, 0)

    def test_curve_fitting_precision(self):
        """Generate perfect synthetic Hill equations data and check if optimization resolves variables."""
        # Define known target properties
        true_bottom = 5.0
        true_top = 105.0
        true_log_ec50 = 2.5
        
        # Generate 10 predictable points along a log scale
        x_points = np.linspace(0.0, 5.0, 10)
        y_points = dose_response_model(x_points, true_bottom, true_top, true_log_ec50)
        
        # Run calculation through engine
        result = CurveFittingEngine.fit_dose_response(x_points, y_points)
        
        # Assertions
        self.assertTrue(result["success"], f"Curve fitting failed with error: {result.get('error')}")
        self.assertAlmostEqual(result["params"]["bottom"], true_bottom, places=3)
        self.assertAlmostEqual(result["params"]["top"], true_top, places=3)
        self.assertAlmostEqual(result["params"]["log_ec50"], true_log_ec50, places=3)

	#pass sample data matrices into our new t-test calculator and verify its accuracy.
class TestStatisticalTTestEngine(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        import sys
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.quit()
    def test_unpaired_t_test_student_precision(self):
        """Pass two distinct mock arrays and verify independent Student t-test metrics match exact expectations."""
        # Treatment Groups
        control_group = np.array([12.1, 11.8, 12.5, 13.0, 11.6])
        treated_group = np.array([14.5, 15.1, 13.8, 14.2, 14.9])
        
        result = TTestEngine.calculate_unpaired_t_test(control_group, treated_group, equal_var=True)
        
        # Verify execution completed successfully without math faults
        self.assertTrue(result["success"])
        self.assertAlmostEqual(result["results"]["mean_difference"], -2.3, places=4)
        # Ensure our generated p-value is significant (p < 0.01)
        self.assertLess(result["results"]["p_value"], 0.01)

    def test_insufficient_sample_size_handling(self):
        """Verify the test fails gracefully if groups contain fewer than two values."""
        broken_group = np.array([10.5])
        empty_group = np.array([])
        
        result = TTestEngine.calculate_unpaired_t_test(broken_group, empty_group)
        self.assertFalse(result["success"])
        self.assertIn("at least 2 observations", result["error"])

class TestScientificFileHandler(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        import sys
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.quit()

    def setUp(self):
        self.test_output_path = "tests/temp_test_matrix.csv"
        self.model = ScientificTableModel(table_type="XY")

    def tearDown(self):
        # Securely erase the temporary file if it was generated during evaluation
        if os.path.exists(self.test_output_path):
            os.remove(self.test_output_path)

    def test_file_export_and_import_loop(self):
        """Build a matrix, write it locally to a CSV, and verify integrity upon reload."""
        # 1. Populate the table model with control values
        self.model.set_value(row=0, column_name="X", value=1.0)
        self.model.set_value(row=0, column_name="Y1", value=100.5)
        self.model.set_value(row=1, column_name="X", value=2.0)
        self.model.set_value(row=1, column_name="Y1", value=200.7)

        # 2. Export matrix through our handler module
        export_status = ScientificFileHandler.export_to_csv(self.model, self.test_output_path)
        self.assertTrue(export_status)
        self.assertTrue(os.path.exists(self.test_output_path))

        # 3. Reload CSV back into an isolated engine module
        loaded_model = ScientificFileHandler.import_from_csv(self.test_output_path, table_type="XY")
        
        # 4. Check parameter equivalence validation checks
        loaded_x_data = loaded_model.get_column_data("X")
        loaded_y1_data = loaded_model.get_column_data("Y1")

        self.assertEqual(len(loaded_x_data), 2)
        self.assertAlmostEqual(loaded_y1_data[0], 100.5, places=2)
        self.assertAlmostEqual(loaded_y1_data[1], 200.7, places=2)


class TestPrismArchiveParser(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        import sys
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.quit()
    """
    Isolated exception-path evaluation suite for PrismParser.

    Every test builds a minimal .prism archive (a ZIP renamed with the .prism
    extension) using only Python's built-in zipfile and json libraries, writes
    it to a NamedTemporaryFile, runs a targeted parse attempt, and asserts the
    expected graceful behaviour.

    Teardown contract:
        All temporary .prism files created via _register_temp() are
        unconditionally deleted in tearDown(), regardless of test outcome.
        No leftover artefacts are ever written to the permanent test directory.
    """

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def setUp(self):
        """Initialises the temporary file registry before each test."""
        self._temp_registry: list = []

    def tearDown(self):
        """Deletes every registered temporary file after each test."""
        for path in self._temp_registry:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass  # Best-effort cleanup — never mask a test failure
        self._temp_registry.clear()

    # ------------------------------------------------------------------
    # Internal Helper
    # ------------------------------------------------------------------

    def _build_prism_file(self, zip_populator) -> str:
        """
        Creates a named temporary .prism file, delegates its ZIP content
        population to the caller-supplied callable, registers the path for
        teardown, and returns the absolute filesystem path.

        Args:
            zip_populator: Callable(zipfile.ZipFile) that writes members into
                           the open archive before it is closed and flushed.

        Returns:
            Absolute path string of the written .prism file.
        """
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zip_populator(zf)

        tmp = tempfile.NamedTemporaryFile(suffix=".prism", delete=False)
        tmp.write(buf.getvalue())
        tmp.flush()
        tmp.close()

        self._temp_registry.append(tmp.name)
        return tmp.name

    # ------------------------------------------------------------------
    # Test Cases
    # ------------------------------------------------------------------

    def test_empty_archive_raises_prism_parse_error_not_key_error(self):
        """
        An archive that is a structurally valid ZIP but contains no files at
        all (no document.json, no data/ tree) must surface a PrismParseError
        — NOT a raw KeyError or any other unhandled exception from inside
        ZipFile.read() or dict lookups within the parser.
        """
        path = self._build_prism_file(lambda zf: None)  # Populate nothing

        with self.assertRaises(PrismParseError) as context:
            PrismParser.parse(path)

        # Confirm the error message points to the missing manifest entry
        self.assertIn("document.json", str(context.exception))

    def test_archive_with_manifest_but_no_data_directory_returns_empty_list(self):
        """
        An archive containing a well-formed document.json that declares no
        sheets or tables, and that omits the data/ subdirectory entirely,
        must return an empty list rather than raising any exception.

        This validates graceful handling of the missing data/sheets/ and
        data/tables/ sub-directory structure without an unhandled FileNotFoundError,
        KeyError, or StopIteration leaking from the internal discovery loops.
        """
        manifest = {
            "title":   "Empty Manifest Test",
            "version": "10.0",
            "sheets":  [],
            "tables":  [],
        }

        def populate(zf: zipfile.ZipFile):
            zf.writestr("document.json", json.dumps(manifest))
            # Intentionally omit data/sheets/ and data/tables/ entirely

        path = self._build_prism_file(populate)

        result = PrismParser.parse(path)

        self.assertIsInstance(result, list,
            "Parser must return a list even when the data/ tree is absent.")
        self.assertEqual(len(result), 0,
            "Parser must return an empty list when no sheets are declared.")

    def test_archive_with_declared_sheets_but_missing_table_files_returns_empty_list(self):
        """
        An archive whose manifest declares sheet and table IDs, and whose
        data/sheets/ entries reference those IDs, but whose data/tables/
        directory is entirely absent must return an empty list.

        Verifies that the sheet→table linkage resolution loop skips broken
        references gracefully instead of raising a KeyError on dict lookup.
        """
        manifest = {
            "title":   "Broken Linkage Test",
            "version": "10.0",
            "sheets":  ["sheet_0"],
            "tables":  ["table_0"],
        }
        sheet_0 = {
            "id":           "sheet_0",
            "name":         "Ghost Sheet",
            "type":         "XY",
            "linked_table": "table_0",  # References a table that will not exist in the ZIP
        }

        def populate(zf: zipfile.ZipFile):
            zf.writestr("document.json",            json.dumps(manifest))
            zf.writestr("data/sheets/sheet_0.json", json.dumps(sheet_0))
            # Intentionally omit data/tables/ — the linked table_0 is absent

        path = self._build_prism_file(populate)

        result = PrismParser.parse(path)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0,
            "Sheets whose linked tables are missing must be silently skipped.")

    def test_corrupt_document_json_raises_prism_parse_error_not_json_decode_error(self):
        """
        An archive whose document.json contains syntactically invalid JSON
        must raise PrismParseError — NOT the raw json.JSONDecodeError that
        would propagate from json.loads() without the parser's error boundary.

        This ensures internal library exceptions are always translated into
        the public PrismParseError contract before surfacing to callers.
        """
        def populate(zf: zipfile.ZipFile):
            zf.writestr("document.json", "{ this is : NOT : valid JSON !!!}")

        path = self._build_prism_file(populate)

        with self.assertRaises(PrismParseError) as context:
            PrismParser.parse(path)

        # Verify the exception is not masking an unrelated internal crash
        self.assertNotIsInstance(context.exception.__cause__,
            KeyError,
            "PrismParseError must not wrap a raw KeyError from dict access.")

    def test_non_zip_bytes_raise_prism_parse_error_not_bad_zip_file(self):
        """
        A file with a .prism extension whose byte content is not a ZIP archive
        (e.g. a plain text or binary blob) must raise PrismParseError — NOT
        the raw zipfile.BadZipFile exception from the standard library.

        This validates the public exception boundary of the parser facade.
        """
        tmp = tempfile.NamedTemporaryFile(suffix=".prism", delete=False)
        tmp.write(b"This is plain text, not a ZIP archive.")
        tmp.flush()
        tmp.close()
        self._temp_registry.append(tmp.name)

        with self.assertRaises(PrismParseError):
            PrismParser.parse(tmp.name)

    def test_in_memory_zip_stream_matches_filesystem_parse_result(self):
        """
        Validates that a .prism archive built entirely in-memory via io.BytesIO
        and written to a NamedTemporaryFile produces identical ScientificTableModel
        output to what the data asserts.  Specifically checks that:
            - Exactly one model is returned.
            - The X column contains the expected numeric vector.
            - A JSON null cell in Y1 is dropped by get_column_data (NaN pruned).
        """
        manifest = {
            "title":   "In-Memory Stream Test",
            "version": "10.0",
            "sheets":  ["sheet_0"],
            "tables":  ["table_0"],
        }
        sheet_0 = {
            "id":           "sheet_0",
            "name":         "Stream Sheet",
            "type":         "XY",
            "linked_table": "table_0",
        }
        table_0 = {
            "id":      "table_0",
            "name":    "Stream Table",
            "columns": ["X", "Y1"],
            "rows": [
                [1.0, 10.0],
                [2.0, None],   # JSON null — must become NaN and be pruned
                [3.0, 30.0],
            ],
        }

        def populate(zf: zipfile.ZipFile):
            zf.writestr("document.json",            json.dumps(manifest))
            zf.writestr("data/sheets/sheet_0.json", json.dumps(sheet_0))
            zf.writestr("data/tables/table_0.json", json.dumps(table_0))

        path = self._build_prism_file(populate)

        models = PrismParser.parse(path)

        self.assertEqual(len(models), 1,
            "Expected exactly one ScientificTableModel from a single-sheet archive.")

        model = models[0]
        x_data  = list(model.get_column_data("X"))
        y1_data = list(model.get_column_data("Y1"))

        self.assertEqual(x_data, [1.0, 2.0, 3.0],
            f"X column vector mismatch: {x_data}")
        self.assertEqual(len(y1_data), 2,
            f"Y1 must have 2 values after NaN pruning (null row dropped), got: {y1_data}")
        self.assertAlmostEqual(y1_data[0], 10.0, places=5)
        self.assertAlmostEqual(y1_data[1], 30.0, places=5)

    def test_cross_platform_separators_and_nested_container_paths(self):
        """
        Validates that .prism archives containing Windows-style backslashes,
        leading dot paths (./), or nested container folders are parsed cleanly
        without triggering an Empty Archive warning or path-mismatch errors.
        """
        manifest = {
            "title": "Cross Platform Test",
            "version": "10.0",
            "sheets": ["sheet_0"],
            "tables": ["table_0"],
        }
        sheet_0 = {
            "id": "sheet_0",
            "name": "Cross Sheet",
            "type": "XY",
            "linked_table": "table_0",
        }
        table_0 = {
            "id": "table_0",
            "name": "Cross Table",
            "columns": ["X", "Y1"],
            "rows": [[5.0, 50.0], [6.0, 60.0]],
        }

        # Subtest A: Windows-style backslashes
        def populate_backslashes(zf: zipfile.ZipFile):
            zf.writestr("document.json", json.dumps(manifest))
            zf.writestr("data\\sheets\\sheet_0.json", json.dumps(sheet_0))
            zf.writestr("data\\tables\\table_0.json", json.dumps(table_0))

        path_bs = self._build_prism_file(populate_backslashes)
        models_bs = PrismParser.parse(path_bs)
        self.assertEqual(len(models_bs), 1)
        self.assertEqual(list(models_bs[0].get_column_data("X")), [5.0, 6.0])

        # Subtest B: Nested container directory (e.g. MyArchive/data/sheets/...)
        def populate_nested(zf: zipfile.ZipFile):
            zf.writestr("ContainerDir/document.json", json.dumps(manifest))
            zf.writestr("ContainerDir/data/sheets/sheet_0.json", json.dumps(sheet_0))
            zf.writestr("ContainerDir/data/tables/table_0.json", json.dumps(table_0))

        path_nested = self._build_prism_file(populate_nested)
        models_nested = PrismParser.parse(path_nested)
        self.assertEqual(len(models_nested), 1)
        self.assertEqual(list(models_nested[0].get_column_data("X")), [5.0, 6.0])

        # Subtest C: Leading dot paths (./data/sheets/...)
        def populate_dots(zf: zipfile.ZipFile):
            zf.writestr("./document.json", json.dumps(manifest))
            zf.writestr("./data/sheets/sheet_0.json", json.dumps(sheet_0))
            zf.writestr("./data/tables/table_0.json", json.dumps(table_0))

        path_dots = self._build_prism_file(populate_dots)
        models_dots = PrismParser.parse(path_dots)
        self.assertEqual(len(models_dots), 1)
        self.assertEqual(list(models_dots[0].get_column_data("X")), [5.0, 6.0])

    def test_native_prism_10_datasets_parsing(self):
        """
        Validates that native GraphPad Prism 10 files using the data/sets/ layout
        have their set ID strings and numeric float vectors mapped directly into
        ScientificTableModel columns without triggering Empty Archive warnings.
        """
        manifest = {
            "title": "Native Sets Manifest",
            "version": "10.0",
            "sets": ["set_101"]
        }
        set_payload = {
            "id": "set_101",
            "name": "Dose Response Curve Set",
            "type": "XY",
            "columns": ["X", "Y1", "Y2"],
            "rows": [
                [0.01, 15.2, 14.8],
                [0.1, 55.4, 54.9],
                [1.0, 98.1, 97.9]
            ]
        }

        def populate(zf: zipfile.ZipFile):
            zf.writestr("document.json", json.dumps(manifest))
            zf.writestr("data/sets/set_101.json", json.dumps(set_payload))

        path = self._build_prism_file(populate)
        models = PrismParser.parse(path)
        self.assertEqual(len(models), 1)
        m = models[0]
        self.assertEqual(m.sheet_name, "Dose Response Curve Set")
        self.assertEqual(list(m.get_column_data("X")), [0.01, 0.1, 1.0])
        self.assertEqual(list(m.get_column_data("Y1")), [15.2, 55.4, 98.1])

    def test_two_pass_multi_set_sheet_assembly(self):
        """
        Validates two-pass parsing architecture:
        1. Reads document.json for structural sheet definitions ('siDuox2', 'nM').
        2. Queries internal set links and re-assembles individual target set arrays
           under data/sets/ together into unified multi-column ScientificTableModel instances.
        3. Exposes clean human-readable sheet title strings for UI selector mapping.
        """
        manifest = {
            "title": "Two Pass Multi-Set Experiment",
            "version": "10.0",
            "sheets": [
                {"id": "s1", "name": "siDuox2", "type": "XY", "sets": ["set_a", "set_b"]},
                {"id": "s2", "name": "nM", "type": "XY", "sets": ["set_c"]}
            ]
        }
        set_a = {"id": "set_a", "name": "siDuox2 Rep 1", "x": [0.1, 1.0], "y1": [10.0, 100.0]}
        set_b = {"id": "set_b", "name": "siDuox2 Rep 2", "y2": [12.0, 105.0]}
        set_c = {"id": "set_c", "name": "nM Set", "x": [5.0, 10.0], "y1": [50.0, 80.0]}

        def populate(zf: zipfile.ZipFile):
            zf.writestr("document.json", json.dumps(manifest))
            zf.writestr("data/sets/set_a.json", json.dumps(set_a))
            zf.writestr("data/sets/set_b.json", json.dumps(set_b))
            zf.writestr("data/sets/set_c.json", json.dumps(set_c))

        path = self._build_prism_file(populate)
        models = PrismParser.parse(path)
        self.assertEqual(len(models), 2)
        m1, m2 = models[0], models[1]

        # Verify UI selector list mapping exposes only clean human-readable title strings
        self.assertEqual(m1.sheet_name, "siDuox2")
        self.assertEqual(m2.sheet_name, "nM")

        # Verify unified multi-column re-assembly (set_a and set_b combined into m1)
        self.assertEqual(list(m1.get_column_data("X")), [0.1, 1.0])
        self.assertEqual(list(m1.get_column_data("Y1")), [10.0, 100.0])
        self.assertEqual(list(m1.get_column_data("Y2")), [12.0, 105.0])

        # Verify m2
        self.assertEqual(list(m2.get_column_data("X")), [5.0, 10.0])
        self.assertEqual(list(m2.get_column_data("Y1")), [50.0, 80.0])

    def test_dict_sheets_document_json_parsing(self):
        """
        Validates parsing when document.json 'sheets' element is a dictionary
        mapping sheet_ids to sheet_meta objects (rather than a list).
        """
        manifest = {
            "title": "Dict Sheets Manifest Test",
            "version": "10.0",
            "sheets": {
                "sheet_101": {
                    "name": "siDuox2",
                    "type": "XY",
                    "sets": ["set_1"]
                },
                "sheet_102": {
                    "title": "nM Page View",
                    "type": "XY",
                    "sets": ["set_2"]
                }
            }
        }
        set_1 = {"id": "set_1", "name": "Set 1", "x": [1.0, 2.0], "y1": [10.0, 20.0]}
        set_2 = {"id": "set_2", "name": "Set 2", "x": [3.0, 4.0], "y1": [30.0, 40.0]}

        def populate(zf: zipfile.ZipFile):
            zf.writestr("document.json", json.dumps(manifest))
            zf.writestr("data/sets/set_1.json", json.dumps(set_1))
            zf.writestr("data/sets/set_2.json", json.dumps(set_2))

        path = self._build_prism_file(populate)
        models = PrismParser.parse(path)

        self.assertEqual(len(models), 2)
        self.assertEqual(models[0].sheet_name, "siDuox2")
        self.assertEqual(models[1].sheet_name, "nM Page View")
        self.assertEqual(list(models[0].get_column_data("X")), [1.0, 2.0])
        self.assertEqual(list(models[1].get_column_data("X")), [3.0, 4.0])

    def test_real_prism_10_file_parsing(self):
        """
        Validates end-to-end parsing of real native GraphPad Prism 10 .prism file
        (tests/test_files/SiK_qPCR_FOR_TESTING.prism), verifying that 11 data sheet models
        are returned with human-readable titles ('18s', 'Duox1', 'Duox2', etc.) and valid data.
        """
        test_file = os.path.join(os.path.dirname(__file__), "test_files", "SiK_qPCR_FOR_TESTING.prism")
        if not os.path.exists(test_file):
            self.skipTest(f"Test archive file not found at {test_file}")

        models = PrismParser.parse(test_file)
        self.assertEqual(len(models), 11)
        
        sheet_names = [m.sheet_name for m in models]
        self.assertIn("18s", sheet_names)
        self.assertIn("Duox1", sheet_names)
        self.assertIn("Duox2 fold siCtrl", sheet_names)
        
        # Verify first sheet ("18s") data vectors
        m_18s = next(m for m in models if m.sheet_name == "18s")
        self.assertEqual(list(m_18s.get_column_data("X")), [0.0, 10.0, 30.0, 60.0])


if __name__ == '__main__':
    unittest.main()

```

## File Path: tests/test_security.py
```python
import unittest
import os
import sys

# Append the project root to ensure imports resolve smoothly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from secure_guard import scan_file

class TestSecurityGuard(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.quit()

    def setUp(self):
        self.test_bad_file = "tests/temp_malicious_mock.py"
        self.test_good_file = "tests/temp_safe_mock.py"

    def tearDown(self):
        # Clean up temporary test files if they exist
        for filepath in [self.test_bad_file, self.test_good_file]:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_catches_sudo_injection(self):
        """Ensure the guard catches forbidden execution keywords like sudo."""
        with open(self.test_bad_file, "w") as f:
            f.write("import os\nos.system('sudo rm -rf /')")
        
        # scan_file should return False (failed audit)
        self.assertFalse(scan_file(self.test_bad_file))

    def test_approves_safe_code(self):
        """Ensure legitimate mathematical/scientific Python code passes without issues."""
        safe_code = """
import numpy as np
def calculate_mean(data):
    return np.mean(data)
"""
        with open(self.test_good_file, "w") as f:
            f.write(safe_code)
            
        # scan_file should return True (passed audit)
        self.assertTrue(scan_file(self.test_good_file))

if __name__ == '__main__':
    unittest.main()

```

## File Path: tests/test_advanced_stats.py
```python
"""
Unit test suite verifying Two-Way ANOVA and Kaplan-Meier Survival Analysis engines.
Licensed under GPLv3.
"""

import sys
import os
import unittest
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import QApplication

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.analysis.anova_two_way import TwoWayAnovaEngine
from src.analysis.survival_engine import KaplanMeierEngine
from src.analysis.report_generator import ScientificReportGenerator
from src.data_engine.table_model import ScientificTableModel


class TestTwoWayAnovaEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = QApplication.instance()
        if app is None:
            cls.app = QApplication(sys.argv + ["-platform", "offscreen"])
        else:
            cls.app = app

    @classmethod
    def tearDownClass(cls):
        app = QApplication.instance()
        if app:
            app.quit()

    def test_two_way_anova_precision(self):
        """Verifies Two-Way ANOVA sum of squares, degrees of freedom, and F-statistics."""
        df = pd.DataFrame({
            "Genotype": ["WT", "WT", "WT", "WT", "KO", "KO", "KO", "KO"],
            "Treatment": ["Vehicle", "Vehicle", "Drug", "Drug", "Vehicle", "Vehicle", "Drug", "Drug"],
            "Expression": [10.0, 10.4, 15.0, 15.6, 12.0, 12.6, 25.0, 25.6]
        })

        res = TwoWayAnovaEngine.calculate_two_way_anova(
            df=df,
            factor_a_col="Genotype",
            factor_b_col="Treatment",
            value_col="Expression"
        )

        self.assertTrue(res["success"], f"Two-Way ANOVA failed: {res.get('error')}")
        results = res["results"]

        # Check Degrees of Freedom
        self.assertEqual(results["factor_a"]["df"], 1)
        self.assertEqual(results["factor_b"]["df"], 1)
        self.assertEqual(results["interaction"]["df"], 1)
        self.assertEqual(results["residual"]["df"], 4)

        # Check p-values are significant
        self.assertLess(results["factor_a"]["p_value"], 0.01)
        self.assertLess(results["factor_b"]["p_value"], 0.001)
        self.assertLess(results["interaction"]["p_value"], 0.01)

    def test_empty_dataframe_handling(self):
        """Verifies graceful handling of empty or invalid DataFrame inputs."""
        res_empty = TwoWayAnovaEngine.calculate_two_way_anova(pd.DataFrame(), "A", "B", "Y")
        self.assertFalse(res_empty["success"])
        self.assertIn("empty", res_empty["error"])


class TestKaplanMeierEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = QApplication.instance()
        if app is None:
            cls.app = QApplication(sys.argv + ["-platform", "offscreen"])
        else:
            cls.app = app

    @classmethod
    def tearDownClass(cls):
        app = QApplication.instance()
        if app:
            app.quit()

    def test_kaplan_meier_survival_probabilities(self):
        """Verifies Kaplan-Meier product-limit survival probabilities and Greenwood standard errors."""
        times = [1.0, 2.0, 3.0, 4.0, 5.0]
        events = [1, 1, 0, 1, 1]  # Event at 1, 2, 4, 5; censored at 3

        res = KaplanMeierEngine.calculate_kaplan_meier(times, events)
        self.assertTrue(res["success"], f"Kaplan-Meier failed: {res.get('error')}")

        summary = res["summary"]
        self.assertEqual(summary["n_total"], 5)
        self.assertEqual(summary["total_events"], 4)
        self.assertEqual(summary["total_censored"], 1)

        rows = res["results"]["survival_table"]
        self.assertEqual(len(rows), 5)

        # Time 1: 1 event out of 5 at risk -> S(1) = 4/5 = 0.8
        self.assertAlmostEqual(rows[0]["survival_probability"], 0.8, places=4)
        self.assertEqual(rows[0]["at_risk"], 5)

        # Time 2: 1 event out of 4 at risk -> S(2) = 0.8 * (3/4) = 0.6
        self.assertAlmostEqual(rows[1]["survival_probability"], 0.6, places=4)
        self.assertEqual(rows[1]["at_risk"], 4)

        # Time 3: 1 censored out of 3 at risk -> S(3) = 0.6
        self.assertAlmostEqual(rows[2]["survival_probability"], 0.6, places=4)
        self.assertEqual(rows[2]["at_risk"], 3)

        # Verify Greenwood standard error is non-zero
        self.assertGreater(rows[1]["std_error"], 0.0)

    def test_insufficient_survival_data(self):
        """Verifies handling of empty input vectors."""
        res = KaplanMeierEngine.calculate_kaplan_meier([], [])
        self.assertFalse(res["success"])


class TestAdvancedReportGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = QApplication.instance()
        if app is None:
            cls.app = QApplication(sys.argv + ["-platform", "offscreen"])
        else:
            cls.app = app

    @classmethod
    def tearDownClass(cls):
        app = QApplication.instance()
        if app:
            app.quit()

    def test_report_includes_advanced_analyses(self):
        """Verifies master ledger HTML includes Two-Way ANOVA and Kaplan-Meier tables when relevant."""
        model = ScientificTableModel(table_type="XY", sheet_name="Survival Study")
        df = pd.DataFrame({
            "Time": [1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0],
            "Event": [1, 1, 0, 0, 1, 1, 0, 0],
            "Score": [10.0, 10.5, 15.0, 15.5, 12.0, 12.5, 25.0, 25.5]
        })
        model._data_frame = df

        html = ScientificReportGenerator.generate_master_report(model)
        self.assertIn("Survival Study", html)
        self.assertIn("Descriptive Statistics", html)
        self.assertIn("Kaplan-Meier Survival Analysis", html)
        self.assertIn("Two-Way Analysis of Variance", html)


from src.ui.mediator import WorkspaceMediator
from src.ui.table_view import ScientificTableWidget
from src.ui.plot_canvas import ScientificPlotCanvas
from PyQt6.QtWidgets import QStackedWidget, QTextBrowser


class TestMediatorAdvancedStats(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = QApplication.instance()
        if app is None:
            cls.app = QApplication(sys.argv + ["-platform", "offscreen"])
        else:
            cls.app = app

    @classmethod
    def tearDownClass(cls):
        app = QApplication.instance()
        if app:
            app.quit()

    def test_mediator_two_way_anova_execution(self):
        """Verifies mediator executes Two-Way ANOVA and updates results browser."""
        model = ScientificTableModel(table_type="Grouped", sheet_name="ANOVA Test")
        df = pd.DataFrame({
            "Genotype": ["WT", "WT", "WT", "WT", "KO", "KO", "KO", "KO"],
            "Treatment": ["Vehicle", "Vehicle", "Drug", "Drug", "Vehicle", "Vehicle", "Drug", "Drug"],
            "Expression": [10.0, 10.4, 15.0, 15.6, 12.0, 12.6, 25.0, 25.6]
        })
        model._data_frame = df

        table = ScientificTableWidget(model)
        canvas = ScientificPlotCanvas()
        stack = QStackedWidget()
        browser = QTextBrowser()
        stack.addWidget(table)
        stack.addWidget(browser)

        mediator = WorkspaceMediator(
            model=model, table=table, canvas=canvas, center_stack=stack, results_browser=browser
        )

        mediator.execute_two_way_anova(parent_window=None)
        self.assertEqual(stack.currentIndex(), 1)
        self.assertIn("Two-Way Analysis of Variance", browser.toHtml())

    def test_mediator_kaplan_meier_execution(self):
        """Verifies mediator executes Kaplan-Meier survival analysis and updates results browser."""
        model = ScientificTableModel(table_type="XY", sheet_name="Survival Test")
        df = pd.DataFrame({
            "Time": [1.0, 2.0, 3.0, 4.0, 5.0],
            "Event": [1, 1, 0, 1, 1]
        })
        model._data_frame = df

        table = ScientificTableWidget(model)
        canvas = ScientificPlotCanvas()
        stack = QStackedWidget()
        browser = QTextBrowser()
        stack.addWidget(table)
        stack.addWidget(browser)

        mediator = WorkspaceMediator(
            model=model, table=table, canvas=canvas, center_stack=stack, results_browser=browser
        )

        mediator.execute_kaplan_meier_survival(parent_window=None)
        self.assertEqual(stack.currentIndex(), 1)
        self.assertIn("Kaplan-Meier Survival Analysis", browser.toHtml())

    def test_plot_canvas_pdf_export(self):
        """Verifies _export_as_pdf executes cleanly without clipToView or rendering exceptions."""
        import tempfile
        canvas = ScientificPlotCanvas()
        canvas.refresh_plot([1.0, 2.0, 3.0], {"Y1": [0.5, 1.5, 2.5]})
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            canvas._export_as_pdf(tmp_path)
            self.assertTrue(os.path.exists(tmp_path))
            self.assertGreater(os.path.getsize(tmp_path), 0)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()

```

