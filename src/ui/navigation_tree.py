"""
VibePad Schism Sidebar Navigation Tree Component.
Licensed under GPLv3.
"""

from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from src.data_engine.table_model import ScientificTableModel


class ScientificNavigationTree(QTreeWidget):
    """
    Categorized navigation sidebar tree for switching workspace data sheets,
    info pages, results, and graph views.
    """
    sheet_selected = pyqtSignal(object)  # Emits target ScientificTableModel instance (backwards compatible)
    navigation_selected = pyqtSignal(object, str, str)  # Emits (model, node_type, sub_type)

    MODEL_ROLE = Qt.ItemDataRole.UserRole + 1
    NODE_TYPE_ROLE = Qt.ItemDataRole.UserRole + 2
    SUB_TYPE_ROLE = Qt.ItemDataRole.UserRole + 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setAnimated(True)
        self.setIconSize(QSize(16, 16))
        self.setIndentation(18)
        self.init_categories()
        self.apply_stylesheet()
        self.currentItemChanged.connect(self._on_item_changed)

    def init_categories(self):
        """Initializes the standard scientific workspace categories."""
        self.clear()
        self.root_tables = QTreeWidgetItem(self, ["📊  Data Tables"])
        self.root_info = QTreeWidgetItem(self, ["ℹ️  Info"])
        self.root_results = QTreeWidgetItem(self, ["📈  Results"])
        self.root_graphs = QTreeWidgetItem(self, ["📉  Graphs"])

        for root in [self.root_tables, self.root_info, self.root_results, self.root_graphs]:
            font = root.font(0)
            font.setBold(True)
            root.setFont(0, font)
            root.setExpanded(True)

    def apply_stylesheet(self):
        """Applies a clean charcoal dark mode theme to the tree widget."""
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #252525;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                font-size: 13px;
                color: #ffffff;
                padding: 4px;
                outline: 0;
            }
            QTreeWidget::item {
                height: 28px;
                border-radius: 4px;
                padding-left: 8px;
                padding-right: 8px;
                margin-top: 1px;
                margin-bottom: 1px;
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
            QTreeWidget::branch {
                background: transparent;
            }
        """)

    def populate_models(self, models: list):
        """
        Populates Data Tables, Results, and Graphs categories matching Prism 10 layout.
        Auto-selects the first sheet item.
        """
        self.root_tables.takeChildren()
        self.root_info.takeChildren()
        self.root_results.takeChildren()
        self.root_graphs.takeChildren()

        if not models:
            return

        first_sheet_item = None
        for i, model in enumerate(models):
            sheet_name = getattr(model, "sheet_name", getattr(model, "name", f"Sheet {i+1}"))
            
            # Data Tables
            item_t = QTreeWidgetItem(self.root_tables, [f"📄  {sheet_name}"])
            item_t.setData(0, self.MODEL_ROLE, model)
            item_t.setData(0, self.NODE_TYPE_ROLE, "table")
            item_t.setData(0, self.SUB_TYPE_ROLE, "xy")
            if first_sheet_item is None:
                first_sheet_item = item_t

            # Results
            item_r = QTreeWidgetItem(self.root_results, [f"📄  Results Ledger ({sheet_name})"])
            item_r.setData(0, self.MODEL_ROLE, model)
            item_r.setData(0, self.NODE_TYPE_ROLE, "results")
            item_r.setData(0, self.SUB_TYPE_ROLE, "ledger")

            # Graphs
            item_g_xy = QTreeWidgetItem(self.root_graphs, [f"📊  XY Plot ({sheet_name})"])
            item_g_xy.setData(0, self.MODEL_ROLE, model)
            item_g_xy.setData(0, self.NODE_TYPE_ROLE, "graph")
            item_g_xy.setData(0, self.SUB_TYPE_ROLE, "xy")

            item_g_bar = QTreeWidgetItem(self.root_graphs, [f"📊  Grouped Bar Chart ({sheet_name})"])
            item_g_bar.setData(0, self.MODEL_ROLE, model)
            item_g_bar.setData(0, self.NODE_TYPE_ROLE, "graph")
            item_g_bar.setData(0, self.SUB_TYPE_ROLE, "bar_chart")

        self.root_tables.setExpanded(True)
        self.root_results.setExpanded(True)
        self.root_graphs.setExpanded(True)

        if first_sheet_item:
            self.setCurrentItem(first_sheet_item)

    def filter_sub_nodes_for_model(self, active_model: ScientificTableModel):
        """
        Dynamically filters Results and Graphs sub-nodes to display ONLY entries
        calculated from the currently active model/table.
        """
        if not active_model:
            return

        for category_root in [self.root_results, self.root_graphs]:
            for i in range(category_root.childCount()):
                child = category_root.child(i)
                item_model = child.data(0, self.MODEL_ROLE)
                if item_model is active_model or item_model == active_model:
                    child.setHidden(False)
                else:
                    child.setHidden(True)

    def _on_item_changed(self, current: QTreeWidgetItem, previous: QTreeWidgetItem):
        """Handles selection signal and emits target model and navigation payloads."""
        if not current:
            return
        model = current.data(0, self.MODEL_ROLE)
        node_type = current.data(0, self.NODE_TYPE_ROLE) or "table"
        sub_type = current.data(0, self.SUB_TYPE_ROLE) or "xy"

        if model and isinstance(model, ScientificTableModel):
            self.filter_sub_nodes_for_model(model)
            self.navigation_selected.emit(model, str(node_type), str(sub_type))
            self.sheet_selected.emit(model)
