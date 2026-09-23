"""
VibePad Schism Sidebar Navigation Tree Component.
Licensed under GPLv3.
"""

from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QAction
from src.data_engine.table_model import ScientificTableModel


class ScientificNavigationTree(QTreeWidget):
    """
    Categorized navigation sidebar tree for switching workspace data sheets,
    info pages, results, and graph views.

    Tree layout (Prism 10 style):
        📊  Data Tables
            └── 📄  [Sheet Name]
        ℹ️  Info
        📈  Results                       ← top-level category
            └── 📄  [Data Set Name]       ← per-dataset parent (node_type="results")
                └──   [Analysis Name]     ← specific test node  (node_type="test_node")
        📉  Graphs                        ← top-level category
            └── 📊  XY Plot ([Sheet])     ← flat graph entry    (node_type="graph")
            └── 📊  Grouped Bar Chart ... ← flat graph entry    (node_type="graph")

    Context menu (right-click):
        ➕ Add New Data Table
        🗑️ Delete Selected Item
    """
    sheet_selected = pyqtSignal(object)  # Emits target ScientificTableModel instance (backwards compatible)
    navigation_selected = pyqtSignal(object, str, str)  # Emits (model, node_type, sub_type)
    add_table_requested = pyqtSignal()   # Emits when user picks "Add New Data Table"
    delete_item_requested = pyqtSignal(object)  # Emits target model for deletion

    MODEL_ROLE = Qt.ItemDataRole.UserRole + 1
    NODE_TYPE_ROLE = Qt.ItemDataRole.UserRole + 2
    SUB_TYPE_ROLE = Qt.ItemDataRole.UserRole + 3
    ANCHOR_ROLE = Qt.ItemDataRole.UserRole + 4  # Stores anchor_id for test nodes

    SHAPE_EMOJIS = ["🟥", "🟧", "🟨", "🟩", "🟦", "🟪", "🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🔲", "🔳"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setAnimated(True)
        self.setIconSize(QSize(16, 16))
        self.setIndentation(18)
        self.init_categories()
        self.apply_stylesheet()
        self.currentItemChanged.connect(self._on_item_changed)
        self.itemChanged.connect(self.handle_item_renamed)

        # Enable right-click context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

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
                height: 30px;
                border-radius: 4px;
                padding: 4px 8px;
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

        Visual hierarchy & emojis:
          Data Tables Sub-nodes:    {model.icon_emoji}  {model.name}
          Results Sub-nodes (Parent): 🔬  {model.name}
          Results Leaf-nodes (Analyses): {shape_emoji}  {analysis_name}
          Graphs Sub-nodes (Parent):  {model.icon_emoji}  {model.name}
        """
        self.blockSignals(True)
        self.root_tables.takeChildren()
        self.root_info.takeChildren()
        self.root_results.takeChildren()
        self.root_graphs.takeChildren()

        if not models:
            self.blockSignals(False)
            return

        first_sheet_item = None
        for i, model in enumerate(models):
            name = getattr(model, "name", getattr(model, "sheet_name", f"Sheet {i+1}"))
            emoji = getattr(model, "icon_emoji", "📄")

            # ── Data Tables ──────────────────────────────────────────────────
            item_t = QTreeWidgetItem(self.root_tables, [f"{emoji}  {name}"])
            item_t.setData(0, self.MODEL_ROLE, model)
            item_t.setData(0, self.NODE_TYPE_ROLE, "table")
            item_t.setData(0, self.SUB_TYPE_ROLE, "xy")
            item_t.setFlags(item_t.flags() | Qt.ItemFlag.ItemIsEditable)
            if first_sheet_item is None:
                first_sheet_item = item_t

            # ── Results: top-level → per-dataset parent → analyses ───────────
            results_parent = QTreeWidgetItem(self.root_results, [f"🔬  {name}"])
            results_parent.setData(0, self.MODEL_ROLE, model)
            results_parent.setData(0, self.NODE_TYPE_ROLE, "results")
            results_parent.setData(0, self.SUB_TYPE_ROLE, "ledger")
            results_parent.setFlags(results_parent.flags() & ~Qt.ItemFlag.ItemIsEditable)
            results_parent.setExpanded(True)

            # Populate existing analyses as child test nodes under the dataset parent
            for j, entry in enumerate(getattr(model, "analysis_history", [])):
                if not isinstance(entry, dict):
                    continue
                analysis_name = entry.get("analysis_name") or entry.get("name", "Analysis")
                anchor_id = entry.get("anchor_id", "")
                shape_emoji = self.SHAPE_EMOJIS[j % len(self.SHAPE_EMOJIS)]
                child = QTreeWidgetItem(results_parent, [f"{shape_emoji}  {analysis_name}"])
                child.setData(0, self.MODEL_ROLE, model)
                child.setData(0, self.NODE_TYPE_ROLE, "test_node")
                child.setData(0, self.SUB_TYPE_ROLE, "ledger")
                child.setData(0, self.ANCHOR_ROLE, anchor_id)
                child.setFlags(child.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # ── Graphs: parent per dataset ───────────────────────────────────
            graphs_parent = QTreeWidgetItem(self.root_graphs, [f"{emoji}  {name}"])
            graphs_parent.setData(0, self.MODEL_ROLE, model)
            graphs_parent.setData(0, self.NODE_TYPE_ROLE, "graph")
            graphs_parent.setData(0, self.SUB_TYPE_ROLE, "xy")
            graphs_parent.setFlags(graphs_parent.flags() & ~Qt.ItemFlag.ItemIsEditable)
            graphs_parent.setExpanded(True)

            item_g_xy = QTreeWidgetItem(graphs_parent, [f"📊  XY Plot ({name})"])
            item_g_xy.setData(0, self.MODEL_ROLE, model)
            item_g_xy.setData(0, self.NODE_TYPE_ROLE, "graph")
            item_g_xy.setData(0, self.SUB_TYPE_ROLE, "xy")
            item_g_xy.setFlags(item_g_xy.flags() & ~Qt.ItemFlag.ItemIsEditable)

            item_g_bar = QTreeWidgetItem(graphs_parent, [f"📊  Grouped Bar Chart ({name})"])
            item_g_bar.setData(0, self.MODEL_ROLE, model)
            item_g_bar.setData(0, self.NODE_TYPE_ROLE, "graph")
            item_g_bar.setData(0, self.SUB_TYPE_ROLE, "bar_chart")
            item_g_bar.setFlags(item_g_bar.flags() & ~Qt.ItemFlag.ItemIsEditable)

        self.root_tables.setExpanded(True)
        self.root_results.setExpanded(True)
        self.root_graphs.setExpanded(True)

        self.blockSignals(False)

        if first_sheet_item:
            self.setCurrentItem(first_sheet_item)

    def add_analysis_node(self, model: ScientificTableModel, entry: dict) -> None:
        """
        Dynamically adds a single analysis result leaf node under the matching
        Results > [Data Set Name] parent node. Called after a new analysis runs.
        """
        analysis_name = entry.get("analysis_name") or entry.get("name", "Analysis")
        anchor_id = entry.get("anchor_id", "")

        for i in range(self.root_results.childCount()):
            parent = self.root_results.child(i)
            p_model = parent.data(0, self.MODEL_ROLE)
            if p_model is model or p_model == model:
                self.blockSignals(True)
                idx = parent.childCount()
                shape_emoji = self.SHAPE_EMOJIS[idx % len(self.SHAPE_EMOJIS)]
                child = QTreeWidgetItem(parent, [f"{shape_emoji}  {analysis_name}"])
                child.setData(0, self.MODEL_ROLE, model)
                child.setData(0, self.NODE_TYPE_ROLE, "test_node")
                child.setData(0, self.SUB_TYPE_ROLE, "ledger")
                child.setData(0, self.ANCHOR_ROLE, anchor_id)
                child.setFlags(child.flags() & ~Qt.ItemFlag.ItemIsEditable)
                parent.setExpanded(True)
                self.blockSignals(False)
                return

    def handle_item_renamed(self, item: QTreeWidgetItem, column: int):
        """
        Handles inline editing of Data Table nodes and propagates name changes
        to corresponding parent nodes in Results and Graphs sections.
        """
        if not item or item.parent() != self.root_tables or item.data(0, self.NODE_TYPE_ROLE) != "table":
            return
        model = item.data(0, self.MODEL_ROLE)
        if not model:
            return

        raw_text = item.text(0)
        emoji = getattr(model, "icon_emoji", "📄")
        new_name = raw_text.strip()
        if emoji and new_name.startswith(emoji):
            new_name = new_name[len(emoji):].strip()
        if not new_name:
            new_name = getattr(model, "name", "Sheet")

        model.name = new_name
        model.sheet_name = new_name

        self.blockSignals(True)
        item.setText(0, f"{emoji}  {new_name}")

        # Update Results parent node text
        for i in range(self.root_results.childCount()):
            r_child = self.root_results.child(i)
            r_model = r_child.data(0, self.MODEL_ROLE)
            if r_model is model or r_model == model:
                r_child.setText(0, f"🔬  {new_name}")
                break

        # Update Graphs parent node text and child sub-graph labels
        for i in range(self.root_graphs.childCount()):
            g_child = self.root_graphs.child(i)
            g_model = g_child.data(0, self.MODEL_ROLE)
            if g_model is model or g_model == model:
                g_child.setText(0, f"{emoji}  {new_name}")
                for j in range(g_child.childCount()):
                    sub_item = g_child.child(j)
                    sub_type = sub_item.data(0, self.SUB_TYPE_ROLE)
                    if sub_type == "xy":
                        sub_item.setText(0, f"📊  XY Plot ({new_name})")
                    elif sub_type == "bar_chart":
                        sub_item.setText(0, f"📊  Grouped Bar Chart ({new_name})")
                break

        self.blockSignals(False)

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

    def select_results_node(self, model: ScientificTableModel) -> None:
        """Synchronizes navigation tree selection to the Results parent node for target model."""
        if not model or not self.root_results:
            return
        for i in range(self.root_results.childCount()):
            child = self.root_results.child(i)
            item_model = child.data(0, self.MODEL_ROLE)
            if item_model is model or item_model == model:
                self.blockSignals(True)
                self.setCurrentItem(child)
                self.blockSignals(False)
                break

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

    def create_context_menu(self, item: QTreeWidgetItem) -> QMenu:
        """Constructs right-click context menu according to selected item hierarchy."""
        if not item:
            return None

        menu = QMenu(self)

        is_tables_root = (item is self.root_tables)
        is_tables_child = (item.parent() is self.root_tables)
        is_in_tables = is_tables_root or is_tables_child

        if is_in_tables:
            add_action = QAction("➕ Add New Data Table", self)
            add_action.triggered.connect(self.add_table_requested.emit)
            menu.addAction(add_action)

            if is_tables_child:
                model = item.data(0, self.MODEL_ROLE)
                delete_action = QAction("🗑️ Delete Data Table", self)
                delete_action.triggered.connect(lambda _, m=model: self.delete_item_requested.emit(m))
                menu.addAction(delete_action)
        else:
            model = item.data(0, self.MODEL_ROLE)
            delete_action = QAction("🗑️ Delete Item", self)
            delete_action.triggered.connect(lambda _, m=model: self.delete_item_requested.emit(m))
            menu.addAction(delete_action)

        return menu

    def _show_context_menu(self, position: QPoint):
        """Shows right-click context menu according to selected item hierarchy."""
        item = self.itemAt(position)
        if not item:
            item = self.currentItem()
        if not item:
            return

        menu = self.create_context_menu(item)
        if menu:
            menu.exec(self.viewport().mapToGlobal(position))
