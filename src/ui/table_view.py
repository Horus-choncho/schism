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
