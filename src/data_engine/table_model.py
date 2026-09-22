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
