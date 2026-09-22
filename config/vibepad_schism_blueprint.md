# VibePad Schism — Project Context Manifesto & Architectural Blueprint

This document serves as a comprehensive technical blueprint and architectural specification for **VibePad Schism** (OpenPrism-Qt). It is designed to instantly brief any developer or AI reasoning model on the project layout, system contracts, file structures, and active APIs.

---

## 1. Core Project Specifications

### 1.1 Overview & Domain
**VibePad Schism** is an open-source, desktop scientific data analysis, curve fitting, statistical hypothesis testing, and publication-ready vector graphing application built on top of **PyQt6**, **PyQtGraph**, **Pandas**, **SciPy**, and **Statsmodels**.

### 1.2 License Compliance
- **License**: GNU General Public License v3 (GPLv3).
- All source files contain mandatory GPLv3 headers certifying compliance and copyleft distribution terms.

### 1.3 Three-Pane Splitter Architecture
The user interface shell (`src/main.py`) utilizes nested `QSplitter` layout containers to provide a responsive, three-pane workspace:
- **Left Pane (`ScientificNavigationTree`)**: `QTreeWidget` sidebar organizing workspace data into hierarchical nodes:
  - 📊 Data Tables (Multi-sheet data models)
  - ℹ️ Info (Metadata sheets)
  - 📄 Results (HTML master results ledgers)
  - 📈 Graphs (XY line plots, Grouped bar charts)
- **Center Pane (`QStackedWidget`)**:
  - **Index 0 (`ScientificTableWidget`)**: Spreadsheet data grid with custom headers, cell editing, and column rename signals.
  - **Index 1 (`QTextBrowser`)**: Scientific Results Ledger Sheet displaying styled HTML reports of descriptive stats, curve fits, t-tests, ANOVAs, and survival analyses.
- **Right Pane (`ScientificPlotCanvas`)**: `pyqtgraph.GraphicsLayoutWidget` container rendering interactive scatter plots, fitted curves, error bars, custom text annotations, legends, and export capabilities.

### 1.4 Native File Format (`.schism`)
- **Format Structure**: Compressed `.zip` archive containing:
  - `manifest.json`: Metadata, sheet ordering, active tab, canvas style mappings (`color`, `symbol`, `line_style`, `line_width`, `symbol_size`).
  - `sheet_0.csv`, `sheet_1.csv`, ...: Raw numerical matrix data per sheet.
- **Quick Save Shortcut Macro**: `Ctrl+S` (`QKeySequence.StandardKey.Save`) triggers silent save directly to `current_filepath` without confirmation dialogs.
- **Recent Files Vector**: Persistent history file at `~/.config/vibepad_schism/recent_files.txt` caching the last 5 opened file paths.

### 1.5 Security Posture & Execution Policy
- **Policy**: Non-privileged local terminal user-space execution policy (`No-Sudo-Strict-Local`).
- **Automated Security Guard (`tests/test_security.py`)**: Scans codebase and test fixtures to ensure zero banned privilege-escalation commands (e.g., `sudo`).

---

## 2. Directory Layout & Module Maps

```
prism-alt/
├── config/
│   └── vibepad_schism_blueprint.md    # [THIS FILE] Full technical manifesto & API blueprint
├── src/
│   ├── __init__.py
│   ├── main.py                        # Application entry point & VibePadSchismMainWindow shell
│   ├── analysis/                      # Statistical calculation & report generation engines
│   │   ├── __init__.py
│   │   ├── anova_engine.py            # One-Way ANOVA & Tukey HSD post-hoc testing
│   │   ├── anova_two_way.py           # Two-Way ANOVA (Factor A x Factor B x Interaction)
│   │   ├── curve_fitting.py           # 4PL Dose-Response nonlinear regression
│   │   ├── descriptive.py             # Column descriptive statistics (Mean, SD, SEM, Median)
│   │   ├── report_generator.py        # Master HTML scientific ledger generator
│   │   ├── survival_engine.py         # Kaplan-Meier non-parametric survival analysis
│   │   └── t_test.py                  # Independent two-sample t-test
│   ├── data_engine/                   # Core data models & file I/O handlers
│   │   ├── __init__.py
│   │   ├── file_handler.py            # CSV & .schism ZIP archive packaging / recent files
│   │   ├── prism_parser.py            # GraphPad .prism XML/ZIP archive importer
│   │   └── table_model.py             # ScientificTableModel (Pandas-backed spreadsheet)
│   └── ui/                            # PyQt6 user interface components
│       ├── __init__.py
│       ├── analyze_dialog.py          # GraphPad-style Analyze Data Hub dialog
│       ├── logo.png                   # Application window icon asset
│       ├── mediator.py                # WorkspaceMediator central event router
│       ├── navigation_tree.py         # ScientificNavigationTree sidebar navigation widget
│       ├── plot_canvas.py             # ScientificPlotCanvas (PyQtGraph canvas & PDF exporter)
│       └── table_view.py              # ScientificTableWidget spreadsheet grid widget
└── tests/                             # Automated unit test suite
    ├── __init__.py
    ├── test_advanced_stats.py         # Tests for Two-Way ANOVA, Kaplan-Meier, PDF export, Mediator
    ├── test_axis_ticks_reset.py       # Tests for axis tick mark formatting & resets
    ├── test_header_controls_filtering.py # Tests for column header renaming & data filtering
    ├── test_math_engine.py            # Tests for table model, curve fitting, t-test
    ├── test_results_and_barchart.py   # Tests for results browser HTML & bar chart rendering
    ├── test_schism_archive.py         # Integration tests for .schism ZIP archive export/import
    ├── test_security.py               # Security compliance scanner guard
    ├── test_statistics_suite.py       # Tests for One-Way ANOVA & descriptive stats
    └── test_theme_ui.py               # Tests for UI stylesheets & theme styling
```

---

## 3. Active Code APIs & Technical Interfaces

### 3.1 Data Model: `ScientificTableModel` (`src/data_engine/table_model.py`)
- `__init__(table_type: str = "XY", sheet_name: str = "Data1")`: Initializes table with default columns (`X, Y1, Y2, Y3` for XY; `A, B, C` for Grouped).
- `set_value(row: int, column_name: str, value: float) -> None`: Sets cell value at row and column name, growing DataFrame rows if necessary.
- `get_column_data(column_name: str) -> np.ndarray`: Returns numeric float numpy array for specified column with `NaN` values removed.
- `get_summary_statistics(column_name: str) -> dict`: Computes mean, std, sem, median, min, max, count for column.
- `rename_column(old_name: str, new_name: str) -> bool`: Renames column header while preserving data.
- `to_dict() -> dict`: Serializes table state into structured dictionary format.
- `from_dict(data: dict) -> ScientificTableModel`: Static factory instantiating model from serialized dictionary.

### 3.2 Disk Persistence: `ScientificFileHandler` (`src/data_engine/file_handler.py`)
- `export_to_csv(model: ScientificTableModel, filepath: str) -> bool`: Exports active table model to CSV file.
- `import_from_csv(filepath: str, table_type: str = "XY") -> ScientificTableModel`: Imports CSV file into table model.
- `export_to_schism(models: list[ScientificTableModel], filepath: str, style_map: dict = None) -> bool`: Packages multi-sheet models and canvas style maps into `.schism` ZIP archive.
- `import_from_schism(filepath: str) -> tuple[list[ScientificTableModel], dict]`: Unpacks `.schism` archive returning table models and style mapping dict.
- `get_recent_files() -> list[str]`: Reads cached recent file paths from `~/.config/vibepad_schism/recent_files.txt`.
- `add_recent_file(filepath: str) -> None`: Appends file path to recent files list (max 5 entries).

### 3.3 Nonlinear Regression: `CurveFittingEngine` (`src/analysis/curve_fitting.py`)
- `dose_response_model(x: np.ndarray, bottom: float, top: float, log_ec50: float, hillslope: float = 1.0) -> np.ndarray`: Evaluates 4PL sigmoid equation with exponent clipping (`np.clip(log_ec50 - x, -20, 20)`) preventing floating-point overflow.
- `fit_dose_response(x_data: np.ndarray, y_data: np.ndarray) -> dict`: Fits 4PL curve using `scipy.optimize.curve_fit` with initial guesses and bounds (`bottom`, `top`, `log_ec50`). Returns `r_squared`, `popt`, `pcov`, `bottom`, `top`, `ec50`, `log_ec50`.

### 3.4 Hypothesis Testing: `TTestEngine` (`src/analysis/t_test.py`)
- `calculate_unpaired_t_test(group_a: np.ndarray, group_b: np.ndarray, equal_var: bool = True) -> dict`: Computes independent two-sample t-test using `scipy.stats.ttest_ind`. Returns `mean_difference`, `standard_error_difference`, `degrees_of_freedom`, `t_statistic`, `p_value`, `confidence_interval`.

### 3.5 One-Way ANOVA: `AnovaEngine` (`src/analysis/anova_engine.py`)
- `calculate_one_way_anova(groups: dict[str, np.ndarray]) -> dict`: Computes one-way ANOVA F-statistic and p-value across multiple group arrays, including Tukey HSD post-hoc pairwise comparisons.

### 3.6 Two-Way ANOVA: `TwoWayAnovaEngine` (`src/analysis/anova_two_way.py`)
- `calculate_two_way_anova(df: pd.DataFrame, factor_a_col: str, factor_b_col: str, value_col: str) -> dict`: Computes two-factor ANOVA for Factor A, Factor B, and Interaction ($A \times B$). Uses `statsmodels.api.stats.anova_lm` with fallback to direct SciPy sum-of-squares calculation.

### 3.7 Survival Analysis: `KaplanMeierEngine` (`src/analysis/survival_engine.py`)
- `calculate_kaplan_meier(time_data: list|np.ndarray, event_data: list|np.ndarray) -> dict`: Computes non-parametric step-function survival probabilities $S(t)$, Greenwood standard errors, 95% confidence intervals, cumulative hazard $H(t)$, and estimated median survival time.

### 3.8 Master Report Generator: `ScientificReportGenerator` (`src/analysis/report_generator.py`)
- `generate_master_report(model: ScientificTableModel) -> str`: Compiles comprehensive HTML ledger sheet containing descriptive stats, curve fitting results, t-tests, One-Way ANOVA, Two-Way ANOVA, and Kaplan-Meier tables.

### 3.9 Central Router: `WorkspaceMediator` (`src/ui/mediator.py`)
- `__init__(model, table, canvas, tree=None, center_stack=None, results_browser=None)`: Connects UI signals and views.
- `sync_data_to_visualization() -> None`: Extracts numerical matrix from table model and updates plot canvas graphics items in real time.
- `execute_workspace_t_test(parent_window) -> None`: Prompts or extracts Y1 vs Y2 vectors and runs unpaired t-test.
- `execute_two_way_anova(parent_window) -> None`: Validates 3+ columns, runs Two-Way ANOVA, shows summary dialog, updates results browser HTML, and switches center stack to index 1.
- `execute_kaplan_meier_survival(parent_window) -> None`: Resolves Time/Event columns, calculates Kaplan-Meier survival, shows summary dialog, updates results browser HTML, and switches center stack to index 1.
- `save_workspace_to_disk(parent_window, filepath=None, silent=False) -> None`: Exports workspace to CSV or `.schism` archive.
- `load_schism_workspace(parent_window) -> None`: Opens and unpacks `.schism` ZIP archive.

### 3.10 Visualization & Vector Export: `ScientificPlotCanvas` (`src/ui/plot_canvas.py`)
- `refresh_plot(x_data, y_datasets_dict, fit_curve_y=None) -> None`: Re-renders scatter points, error bars, connecting lines, and fitted curves on pyqtgraph viewport.
- `export_plot() -> None`: Spawns QFileDialog for PNG/PDF file export selection.
- `_export_as_png(filepath: str) -> None`: Uses `pyqtgraph.exporters.ImageExporter` to write 1920px PNG raster image.
- `_export_as_pdf(filepath: str) -> None`: Vector PDF exporter using `QPdfWriter(filepath)`:
  - Sets `self.plot_widget.getPlotItem().setClipToView(True)` to lock plotted lines inside grid bounds.
  - Defines `target_rect = QRectF(10, 10, writer.width() - 20, writer.height() - 20)` and `source_rect = QRect(0, 0, self.plot_widget.width(), self.plot_widget.height())`.
  - Calls `self.plot_widget.render(painter, target_rect, source_rect)` to achieve high-DPI font scaling and vector line precision.
  - Safely resets `setClipToView(False)` and ends painter in `finally` block.

---

## 4. Verification Protocols & Test Execution

To verify the entire VibePad Schism codebase and run automated test suites:

```bash
# 1. Execute full unit test suite (offscreen headless mode)
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests

# 2. Execute security compliance audit
python3 tests/test_security.py
```
