import csv
import dataclasses
import io
import logging
from functools import lru_cache
from typing import Any, List, Optional

import pandas as pd

from csdmpy.constants import Constants, AgeBracket, PlacementType, PlacementCategory
from csdmpy.data.ssda903 import SSDA903TableType
from csdmpy.datastore import DataFile, DataStore, TableType

log = logging.getLogger(__name__)


class DemandModellingDataContainer:
    """
    A container for demand modelling data. Indexes data by year and table type. Provides methods for
    merging data to create a single, consistent dataset.
    """

    def __init__(self, datastore: DataStore):
        self.__datastore = datastore

        self.__file_info = []
        for file_info in datastore.files:
            if not file_info.metadata.table:
                table_type = self._detect_table_type(file_info)
                metadata = dataclasses.replace(file_info.metadata, table=table_type)
                file_info = dataclasses.replace(file_info, metadata=metadata)

            # We only care about Header and Episodes
            if file_info.metadata.table in [
                SSDA903TableType.HEADER,
                SSDA903TableType.EPISODES,
            ]:
                self.__file_info.append(file_info)

    def __read_first_line(self, file_info: DataFile) -> List[Any]:
        """
        Reads the first line of a file and returns the values as a list.
        This only currently works for CSV files.
        """
        with self.__datastore.open(file_info) as f:
            reader = csv.reader(io.TextIOWrapper(f))
            return next(reader)

    def _detect_table_type(self, file_info: DataFile) -> Optional[TableType]:
        """
        Detect the table type of a file by reading the first line of the file and looking for a
        known table type.

        :param file_info: The file to detect the table type for
        :return: The table type or None if not found.
        """
        first_row = set(self.__read_first_line(file_info))
        if len(first_row) == 0:
            return None

        for table_type in SSDA903TableType:
            table_class = table_type.value
            fields = table_class.fields
            if len(set(fields) - first_row) == 0:
                return table_type

        return None

    @property
    def first_year(self):
        return min([info.metadata.year for info in self.__file_info])

    @property
    def last_year(self):
        return max([info.metadata.year for info in self.__file_info])

    def get_table(self, year: int, table_type: TableType) -> pd.DataFrame:
        """
        Gets a table for a given year and table type.

        :param year: The year to get the table for
        :param table_type: The table type to get
        :return: A pandas DataFrame containing the table data
        """
        for info in self.__file_info:
            metadata = info.metadata
            if metadata.year == year and metadata.table == table_type:
                return self.__datastore.to_dataframe(info)

        raise ValueError(
            f"Could not find table for year {year} and table type {table_type}"
        )

    def get_combined_year(self, year: int) -> pd.DataFrame:
        """
        Returns the combined view for the year consisting of Episodes and Headers

        :param year: The year to get the combined view for
        :return: A pandas DataFrame containing the combined view
        """

        header = self.get_table(year, SSDA903TableType.HEADER)
        episodes = self.get_table(year, SSDA903TableType.EPISODES)

        # TODO: This should be done when the table is first read
        header["DOB"] = pd.to_datetime(header["DOB"], format="%d/%m/%Y")
        episodes["DECOM"] = pd.to_datetime(episodes["DECOM"], format="%d/%m/%Y")
        episodes["DEC"] = pd.to_datetime(episodes["DEC"], format="%d/%m/%Y")

        merged = header.merge(
            episodes, how="inner", on="CHILD", suffixes=("_header", "_episodes")
        )

        return merged

    def get_combined_data(self, combined: pd.DataFrame = None) -> pd.DataFrame:
        """
        Returns the combined view for all years consisting of Episodes and Headers. Runs some sanity checks
        as

        :param combined: A pandas DataFrame containing the combined view - if not provided, it will simply concatenate
                         the values for all years in this container
        :return: A pandas DataFrame containing the combined view
        """
        if not combined:
            combined = pd.concat(
                [
                    self.get_combined_year(year)
                    for year in range(self.first_year, self.last_year + 1)
                ]
            )
        else:
            combined = combined.copy()

        # Just do some basic data validation checks
        assert not combined["CHILD"].isna().any()
        assert not combined["DECOM"].isna().any()

        # Then clean up the episodes
        # We first sort by child, decom and dec, and make sure NAs are first (for dropping duplicates)
        combined.sort_values(
            ["CHILD", "DECOM", "DEC"], inplace=True, na_position="first"
        )

        # If a child has two episodes starting on the same day (usually if NA in one year and then done in next)
        # keep the latest non-NA finish date
        combined.drop_duplicates(["CHILD", "DECOM"], keep="last", inplace=True)
        log.debug(
            "%s records remaining after removing episodes that start on the same date.",
            combined.shape,
        )

        # If a child has two episodes with the same end date, keep the longer one.
        # This also works for open episodes - if there are two open, keep the larger one.
        combined.drop_duplicates(["CHILD", "DEC"], keep="first", inplace=True)
        log.debug(
            "%s records remaining after removing episodes that end on the same date.",
            combined.shape,
        )

        # If a child has overlapping episodes, shorten the earlier one
        decom_next = combined.groupby("CHILD")["DECOM"].shift(-1)
        change_ix = combined["DEC"].isna() | combined["DEC"].gt(decom_next)
        combined.loc[change_ix, "DEC"] = decom_next[change_ix]

        return combined

    def get_enriched_view(self, combined: pd.DataFrame = None) -> pd.DataFrame:
        """
        Adds several additional columns to the combined view to support the model calculations.

        * age - the age of the child at the start of the episode
        * age_end - the age of the child at the end of the episode

        """

        if not combined:
            combined = self.get_combined_data()
        else:
            combined = combined.copy()

        combined = self._add_ages(combined)
        combined = self._add_age_bins(combined)
        combined = self._add_related_placement_type(combined, 1, "PLACE_AFTER")
        combined = self._add_related_placement_type(combined, -1, "PLACE_BEFORE")
        combined = self._add_placement_categories(combined)
        return combined

    @staticmethod
    def _add_ages(combined: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates the age of the child at the start and end of the episode and adds them as columns

        WARNING: This method modifies the dataframe in place.
        """

        combined["age"] = (combined["DECOM"] - combined["DOB"]).dt.days / Constants.YEAR_IN_DAYS
        combined["end_age"] = (combined["DEC"] - combined["DOB"]).dt.days / Constants.YEAR_IN_DAYS
        return combined

    @staticmethod
    def _add_age_bins(combined: pd.DataFrame) -> pd.DataFrame:
        """
        Adds age bins for the child at the start and end of the episode and adds them as columns

        WARNING: This method modifies the dataframe in place.
        """
        combined['age_bin'] = combined['age'].apply(AgeBracket.bracket_for)
        combined['end_age_bin'] = combined['end_age'].apply(AgeBracket.bracket_for)
        return combined

    @staticmethod
    def _add_related_placement_type(combined: pd.DataFrame, offset: int, new_column_name: str) -> pd.DataFrame:
        """
        Adds the related placement type, usually 1 for after, or -1 for preceeding.

        WARNING: This method modifies the dataframe in place.
        """
        combined.sort_values(['CHILD', 'DECOM', 'DEC'], inplace=True, na_position='first')
        offset_mask = (combined['CHILD'] == combined['CHILD'].shift(-offset)) & (combined['DEC'] != combined['DECOM'].shift(-offset))
        combined.loc[offset_mask, new_column_name] = Constants.NOT_IN_CARE
        combined[new_column_name] = combined.groupby('CHILD')['PLACE'].shift(1).fillna(Constants.NOT_IN_CARE)
        return combined

    @staticmethod
    def _add_placement_categories(combined: pd.DataFrame) -> pd.DataFrame:
        """
        Adds placement category for

        WARNING: This method modifies the dataframe in place.
        """
        combined['placement_type'] = combined['PLACE'].apply(PlacementType.category_by_type)
        combined['placement_type_before'] = combined['PLACE_BEFORE'].apply(PlacementType.category_by_type)
        combined['placement_type_after'] = combined['PLACE_AFTER'].apply(PlacementType.category_by_type)
        return combined
