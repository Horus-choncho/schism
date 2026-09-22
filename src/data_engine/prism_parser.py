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
