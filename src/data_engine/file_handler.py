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
                        "csv_filename": csv_filename,
                        "analysis_history": getattr(model, "analysis_history", []),
                        "icon_emoji": getattr(model, "icon_emoji", None)
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
                    icon_emoji = sheet.get("icon_emoji")

                    model = ScientificTableModel(table_type=table_type, sheet_name=sheet_name, icon_emoji=icon_emoji)
                    model.analysis_history = sheet.get("analysis_history", [])
                    if csv_filename in zf.namelist():
                        csv_content = zf.read(csv_filename).decode("utf-8")
                        df = pd.read_csv(io.StringIO(csv_content), keep_default_na=True)
                        model._data_frame = df
                    models.append(model)

            ScientificFileHandler.add_recent_file(filepath)
            return models
        except Exception:
            return []
