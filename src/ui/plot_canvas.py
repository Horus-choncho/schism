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

        self.delete_btn = QPushButton("🗑️  Delete Annotation")
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
        self.toolbar.setMinimumHeight(36)
        self.toolbar.setContentsMargins(4, 2, 4, 2)

        # Add Text Annotation Action
        add_text_action = QAction("➕  Add Text (T)", self)
        add_text_action.setToolTip("Add draggable text annotation to graph canvas")
        add_text_action.triggered.connect(self.add_text_annotation)
        self.toolbar.addAction(add_text_action)

        self.toolbar.addSeparator()

        # Export Plot Action
        export_action = QAction("📤  Export Plot...", self)
        export_action.setToolTip("Save plot as PNG image or PDF document")
        export_action.triggered.connect(self.export_plot)
        self.toolbar.addAction(export_action)

        layout.addWidget(self.toolbar)

        # --- Secondary Plot Configuration Control Toolbar ---
        self.controls_toolbar = QToolBar("Plot Configuration", self)
        self.controls_toolbar.setMinimumHeight(38)
        self.controls_toolbar.setContentsMargins(4, 2, 4, 2)
        self.controls_toolbar.setStyleSheet("background-color: #252525; border-bottom: 1px solid #3d3d3d;")

        type_label = QLabel(" 📈  Plot Type: ", self)
        type_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        self.controls_toolbar.addWidget(type_label)

        self.plot_type_combo = QComboBox(self)
        self.plot_type_combo.addItems(["XY Line Scatter", "Bar Chart", "Box Plot"])
        self.plot_type_combo.setMinimumWidth(140)
        self.plot_type_combo.setMinimumHeight(26)
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
        self.sd_multiplier_spin.setMinimumHeight(26)
        self.controls_toolbar.addWidget(self.sd_multiplier_spin)

        self.plot_type_combo.currentTextChanged.connect(self._on_plot_controls_changed)
        self.show_error_bars_cb.toggled.connect(self._on_plot_controls_changed)
        self.sd_multiplier_spin.valueChanged.connect(self._on_plot_controls_changed)

        layout.addWidget(self.controls_toolbar)

        # Create pyqtgraph PlotWidget element with high-contrast white background
        self.plot_widget = pg.PlotWidget(title="🔬  Experimental Analysis Workspace")
        self.plot_widget.setBackground('w')  # High-contrast white canvas background

        # Enable ViewBox clipping to lock plot curves, bars, and error whiskers within axis boundaries
        self.plot_widget.plotItem.setClipToView(True)
        view_box = self.plot_widget.plotItem.getViewBox()
        view_box.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape, True)
        view_box.setDefaultPadding(0.05)

        # Initialize high-contrast scientific legend on self.plot_widget.plotItem
        self.legend = self.plot_widget.addLegend(
            offset=(10, 10),
            labelTextColor='k',
            brush=pg.mkBrush(255, 255, 255, 220),
            pen=pg.mkPen('#3d3d3d', width=1)
        )

        # Configure crisp scientific axis labels and grid styling
        self.plot_widget.setLabel('bottom', 'Independent Variable (X-Axis)', colors='k')
        self.plot_widget.setLabel('left', 'Dependent Variable (Y-Axis)', colors='k')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.15)

        layout.addWidget(self.plot_widget)

    def reset_axis_ticks(self) -> None:
        """Clears custom category string tick mappings from axes, resetting to pure continuous linear scale."""
        self.plot_widget.getAxis('bottom').setTicks(None)
        self.plot_widget.getAxis('left').setTicks(None)

    def set_axis_titles(self, x_title: str = None, y_title: str = None) -> None:
        """Dynamically updates the bottom (X) and left (Y) axis title labels.

        Args:
            x_title (str, optional): Label string for the X-axis (bottom).
            y_title (str, optional): Label string for the Y-axis (left).
        """
        if x_title is not None:
            self.plot_widget.setLabel('bottom', str(x_title), colors='k')
        if y_title is not None:
            self.plot_widget.setLabel('left', str(y_title), colors='k')

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
        x_data = np.asarray(x_data, dtype=float) if x_data is not None else np.array([], dtype=float)
        if fit_curve_y is not None:
            fit_curve_y = np.asarray(fit_curve_y, dtype=float)

        self._last_x_data = x_data
        self._last_fit_curve_y = fit_curve_y

        # Reset bottom axis ticks to continuous linear numeric scale
        self.reset_axis_ticks()

        # Clear active legend entries
        if hasattr(self, "legend") and self.legend is not None:
            self.legend.clear()

        # Handle 1D array fallback
        if isinstance(y_datasets_dict, np.ndarray):
            y_datasets_dict = {"Y1": y_datasets_dict}
        elif isinstance(y_datasets_dict, list):
            y_datasets_dict = {"Y1": np.asarray(y_datasets_dict, dtype=float)}
        elif not isinstance(y_datasets_dict, dict):
            y_datasets_dict = {}

        # Ensure all dataset vectors in dictionary are numpy float arrays
        clean_y_datasets = {}
        for k, v in y_datasets_dict.items():
            clean_y_datasets[k] = np.asarray(v, dtype=float)
        y_datasets_dict = clean_y_datasets

        self._last_y_datasets_dict = y_datasets_dict

        # Clear obsolete plot items while explicitly preserving SchismTextItem / TextItem / LegendItem annotations
        for item in list(self.plot_widget.items()):
            if not isinstance(item, (pg.TextItem, SchismTextItem, pg.AxisItem, pg.ViewBox, pg.LegendItem)):
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
                clickable=True,
                name=str(col_name)
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

        # Clear active legend entries
        if hasattr(self, "legend") and self.legend is not None:
            self.legend.clear()

        # Clear existing plot graphics items (retaining text annotations and legend)
        for item in list(self.plot_widget.items()):
            if not isinstance(item, (pg.TextItem, SchismTextItem, pg.AxisItem, pg.ViewBox, pg.LegendItem)):
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

        default_colors = ["#0284c7", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6"]

        if x_col:
            categories = model.get_column_data(x_col)
            y_cols = [c for c in cols if c != x_col]
            if not y_cols:
                return

            num_categories = len(categories)
            num_series = len(y_cols)
            if num_categories == 0 or num_series == 0:
                return

            group_width = 0.8
            bar_width = group_width / max(1, num_series)
            category_positions = np.arange(num_categories, dtype=float) * 1.5

            ticks = [(category_positions[cat_idx], str(cat_val)) for cat_idx, cat_val in enumerate(categories)]
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

                offset = - (group_width / 2.0) + (series_idx + 0.5) * bar_width
                x_pos = category_positions + offset

                color = default_colors[series_idx % len(default_colors)]
                brush = pg.mkBrush(color)
                pen = pg.mkPen('#000000', width=1.5)

                bg = pg.BarGraphItem(
                    x=x_pos,
                    height=means,
                    width=bar_width * 0.9,
                    brush=brush,
                    pen=pen
                )
                self.plot_widget.addItem(bg)
                if hasattr(self, "legend") and self.legend is not None:
                    self.legend.addItem(bg, str(col_name))

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

            self.set_axis_titles(x_title=str(x_col), y_title=f'Result (Mean ± {sd_mult}x SD)')
        else:
            y_cols = cols
            num_series = len(y_cols)
            if num_series == 0:
                return

            category_positions = np.arange(num_series, dtype=float) * 1.5
            ticks = [(category_positions[idx], str(col_name)) for idx, col_name in enumerate(y_cols)]
            ax = self.plot_widget.getAxis('bottom')
            ax.setTicks([ticks])

            sd_mult = self.sd_multiplier_spin.value()
            show_err = self.show_error_bars_cb.isChecked()
            bar_width = 0.6

            for idx, col_name in enumerate(y_cols):
                data_vec = model.get_column_data(col_name)
                if data_vec.size == 0:
                    continue

                mean_val = float(np.mean(data_vec))
                std_val = float(np.std(data_vec, ddof=1)) if data_vec.size > 1 else 0.0
                err_val = float(std_val * sd_mult)

                x_pos = np.array([category_positions[idx]])
                color = default_colors[idx % len(default_colors)]
                brush = pg.mkBrush(color)
                pen = pg.mkPen('#000000', width=1.5)

                bg = pg.BarGraphItem(
                    x=x_pos,
                    height=np.array([mean_val]),
                    width=bar_width,
                    brush=brush,
                    pen=pen
                )
                self.plot_widget.addItem(bg)
                if hasattr(self, "legend") and self.legend is not None:
                    self.legend.addItem(bg, str(col_name))

                if show_err and err_val > 0:
                    err = pg.ErrorBarItem(
                        x=x_pos,
                        y=np.array([mean_val]),
                        top=np.array([err_val]),
                        bottom=np.array([err_val]),
                        beam=bar_width * 0.3,
                        pen=pg.mkPen('#000000', width=1.5)
                    )
                    self.plot_widget.addItem(err)

            self.set_axis_titles(x_title='Column / Factor Names', y_title=f'Result (Mean ± {sd_mult}x SD)')

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

        # Clear active legend entries
        if hasattr(self, "legend") and self.legend is not None:
            self.legend.clear()

        for item in list(self.plot_widget.items()):
            if not isinstance(item, (pg.TextItem, SchismTextItem, pg.AxisItem, pg.ViewBox, pg.LegendItem)):
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
            if hasattr(self, "legend") and self.legend is not None:
                self.legend.addItem(bg, str(col_name))

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

        x_title_str = str(x_col) if 'x_col' in locals() and x_col else 'Column / Factor Names'
        self.set_axis_titles(x_title=x_title_str, y_title=f'Distribution (Median / IQR ± {sd_mult}x SD)')

    def render_kaplan_meier_survival(self, km_results: dict) -> None:
        """Renders a dedicated step-function survival curve plotting Survival Probability S(t) (0.0 to 1.0) over Time.

        Args:
            km_results (dict): Output payload from KaplanMeierEngine containing 'survival_table'.
        """
        self.reset_axis_ticks()

        # Clear active legend entries
        if hasattr(self, "legend") and self.legend is not None:
            self.legend.clear()

        for item in list(self.plot_widget.items()):
            if not isinstance(item, (pg.TextItem, SchismTextItem, pg.AxisItem, pg.ViewBox, pg.LegendItem)):
                try:
                    self.plot_widget.removeItem(item)
                except Exception:
                    pass

        if not km_results or "survival_table" not in km_results:
            return

        table_rows = km_results["survival_table"]
        if not table_rows:
            return

        step_x = [0.0]
        step_y = [1.0]

        censored_x = []
        censored_y = []

        curr_prob = 1.0
        for row in table_rows:
            t = float(row["time"])
            prob = float(row["survival_probability"])
            events = int(row["events"])
            censored = int(row["censored"])

            step_x.append(t)
            step_y.append(curr_prob)

            step_x.append(t)
            step_y.append(prob)
            curr_prob = prob

            if censored > 0:
                for _ in range(censored):
                    censored_x.append(t)
                    censored_y.append(prob)

        curve_item = pg.PlotDataItem(
            x=np.array(step_x),
            y=np.array(step_y),
            pen=pg.mkPen('#0284c7', width=2.5)
        )
        self.plot_widget.addItem(curve_item)
        if hasattr(self, "legend") and self.legend is not None:
            self.legend.addItem(curve_item, "Survival S(t)")

        if censored_x:
            censored_item = pg.PlotDataItem(
                x=np.array(censored_x),
                y=np.array(censored_y),
                pen=None,
                symbol='+',
                symbolSize=10,
                symbolPen=pg.mkPen('#ef4444', width=2),
                symbolBrush=pg.mkBrush('#ef4444')
            )
            self.plot_widget.addItem(censored_item)

        self.set_axis_titles(x_title='Time', y_title='Survival Probability S(t)')
        self.plot_widget.setYRange(0.0, 1.05, padding=0)

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
        """Renders the active plot view into a vector-graphics A4 PDF document preserving aspect ratio."""
        writer = QPdfWriter(filepath)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setResolution(300)

        painter = QPainter(writer)

        page_w = float(writer.width())
        page_h = float(writer.height())
        margin = 150.0  # 300 DPI margin (~0.5 inch / 12.7 mm)

        avail_w = max(1.0, page_w - (2.0 * margin))
        avail_h = max(1.0, page_h - (2.0 * margin))

        widget_w = float(max(1, self.plot_widget.width()))
        widget_h = float(max(1, self.plot_widget.height()))
        aspect = widget_w / widget_h

        # Uniform aspect ratio fitting
        if (avail_w / avail_h) > aspect:
            target_h = avail_h
            target_w = target_h * aspect
        else:
            target_w = avail_w
            target_h = target_w / max(0.001, aspect)

        offset_x = margin + (avail_w - target_w) / 2.0
        offset_y = margin + (avail_h - target_h) / 2.0

        target_rect = QRectF(offset_x, offset_y, target_w, target_h)
        source_rect = QRect(0, 0, int(widget_w), int(widget_h))

        plot_item = self.plot_widget.getPlotItem()
        view_box = self.plot_widget.getViewBox()
        orig_range = view_box.viewRange() if hasattr(view_box, "viewRange") else None

        plot_item.setClipToView(True)

        try:
            self.plot_widget.render(painter, target_rect, source_rect)
        finally:
            plot_item.setClipToView(False)
            if orig_range and hasattr(view_box, "setRange"):
                view_box.setRange(xRange=orig_range[0], yRange=orig_range[1], padding=0)
            painter.end()
