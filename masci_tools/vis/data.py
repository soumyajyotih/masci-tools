# -*- coding: utf-8 -*-
###############################################################################
# Copyright (c), Forschungszentrum Jülich GmbH, IAS-1/PGI-1, Germany.         #
#                All rights reserved.                                         #
# This file is part of the Masci-tools package.                               #
# (Material science tools)                                                    #
#                                                                             #
# The code is hosted on GitHub at https://github.com/judftteam/masci-tools.   #
# For further information on the license, see the LICENSE.txt file.           #
# For further information please visit http://judft.de/.                      #
#                                                                             #
###############################################################################
"""
This module contains classes and functions to make plotting functions
more flexible with respect to the used data. This way plotting functions
can both allow the flexible usage of lists, arrays directly or dataframes
together with the keys that should be used
"""
from collections import namedtuple
import numpy as np
import pandas as pd
import copy
from bokeh.models import ColumnDataSource


class PlotData:
    """Class for iterating over the data in a dict or dataframe with
      automatic filling in of single defined keys to get a list of
      keys to extract.

      The iteration allows for implicit definition of data for multiple
      plot sets, without excessive copying of the given data

      Usage Example

      .. code-block:: python

         from masci_tools.vis.data import PlotData
         import numpy as np

         #Let's say we have one energy grid and a couple of functions
         #defined on this energy grid.
         #We collect these in a dict

         x = np.linspace(-10,10,100)
         data = {'x': x, 'y1': np.sin(x), 'y2':np.cos(x), 'y3', x**2}

         p = PlotData(data, x='x', y=['y1', 'y2', 'y3'])

         #If we now iterate over this object it will result in the data
         #for y being returned together with the x data (The same would work the other way around)
         for entry in p:
            print(entry.x) #'x' entry
            print(entry.y) #'y1' then 'y2' and finally 'y3'

         #Additionally data for z, color and size can be defined


      :param data: object or list of objects which can be bracket indexed with the given keys
                   e.g. dicts, pandas dataframes, ...
      :param mask: optional list or Tuple of bool, of the same length as the specified data
                   When iterating over it only the objects with the mask set to True are returned
      :same_length: bool if True and any sources are dicts it will be checked for same dimensions
                    in (ALL) entries (not only for keys plotted against each other)
      :strict_data_keys: bool if True no new data keys are allowed to be entered via :py:meth:`copy_data()`


      Kwargs are used to specify the columns in a namedtuple
      If a list is given for any of the keys the data will be expanded to a list of
      namedtuple with the same length

    """

    #These we know to be safely working as the data argument
    #In principle this could be extended to any Mapping
    ALLOWED_DATA_HOLDERS = (dict, pd.DataFrame, ColumnDataSource)

    def __init__(self, data, mask=None, use_column_source=False, same_length=False, strict_data_keys=False, **kwargs):

        self.data = data
        self.strict_data_keys = strict_data_keys

        if isinstance(self.data, list):
            assert isinstance(self.data[0], self.ALLOWED_DATA_HOLDERS), f'Wrong type for data argument: Got {self.data}'
            dict_data = isinstance(self.data[0], dict)
        else:
            assert isinstance(self.data, self.ALLOWED_DATA_HOLDERS), f'Wrong type for data argument: Got {self.data}'
            dict_data = isinstance(self.data, dict)

        if same_length and dict_data:
            if isinstance(self.data, list):
                for index, entry in enumerate(self.data):
                    if isinstance(entry, dict):
                        self.data[index] = _normalize_dict_entries(entry)
            else:
                self.data = _normalize_dict_entries(self.data)

        if dict_data and use_column_source:
            if isinstance(self.data, list):
                for index, entry in enumerate(self.data):
                    self.data[index] = ColumnDataSource(entry)
            else:
                self.data = ColumnDataSource(self.data)

        self._column_spec = namedtuple('Columns', list(kwargs.keys()))

        if any(isinstance(val, list) for val in kwargs.values()):
            num_sets = max(len(val) for val in kwargs.values() if isinstance(val, list))

            if isinstance(self.data, list):
                if len(self.data) != num_sets:
                    raise ValueError('Mismatch in lengths between data and indices')

            column_args = {}
            for key, val in kwargs.items():
                if isinstance(val, list):
                    if len(val) != num_sets:
                        raise ValueError(f'Mismatch of dimensions: {val} num_sets: {num_sets}')
                    column_args[key] = val
                else:
                    column_args[key] = [val] * num_sets

            self.columns = [
                self._column_spec(**{key: value[index]
                                     for key, value in column_args.items()})
                for index in range(num_sets)
            ]
        else:
            if isinstance(self.data, list):
                num_sets = len(self.data)
            else:
                num_sets = 1
            self.columns = [self._column_spec(**kwargs)] * num_sets

        if mask is None:
            mask = [True] * num_sets
        if not isinstance(mask, (list, tuple)) or len(mask) != num_sets:
            raise ValueError(f'Wrong Value for mask: {mask}')
        self.mask = mask

    def _add_data_key(self, new_data_key):
        """
        Add a new column of data keys initialized with Nones

        :param new_data_key: string of the new data key to add
        """

        if self.strict_data_keys:
            raise ValueError('No new data keys allowed after initialization')

        self._column_spec = namedtuple('Columns', self._column_spec._fields + (new_data_key,))

        #Rebuild the columns list
        for indx, column in enumerate(self.columns):
            self.columns[indx] = self._column_spec(**{**column._asdict(), **{new_data_key: None}})

    @property
    def masked_columns(self):
        """
        Return the columns that are not disabled by the mask argument
        """
        return [col for col, msk in zip(self.columns, self.mask) if msk]

    def __iter__(self):
        """
        Iterate over PlotData. Returns the values for the data
        """
        return PlotDataIterator(self, mode='values')

    def keys(self, first=False):
        """
        Iterate over PlotData keys. Returns the keys for the corresponding sources

        :param first: bool, if True only the first entry is returned
        """
        if first:
            return next(PlotDataIterator(self, mode='keys'))
        else:
            return PlotDataIterator(self, mode='keys')

    def values(self, first=False):
        """
        Iterate over PlotData values. Returns the values for the data

        :param first: bool, if True only the first entry is returned
        """
        if first:
            return next(PlotDataIterator(self, mode='values'))
        else:
            return PlotDataIterator(self, mode='values')

    def items(self, first=False):
        """
        Iterate over PlotData items. Returns the key and corresponding source for the data

        :param first: bool, if True only the first entry is returned
        """
        if first:
            return next(PlotDataIterator(self, mode='items'))
        else:
            return PlotDataIterator(self, mode='items')

    def get_keys(self, data_key):
        """
        Get the keys for a given data column for all entries

        :param data_key: name of the data key to return the keys

        :returns: list of keys, corresponding to the entries for the
                  given data in the sources
        """
        if data_key not in self._column_spec._fields:
            raise ValueError(f'Field {data_key} does not exist')

        keys = []
        for entry in self.keys():
            keys.append(entry._asdict()[data_key])

        return keys

    def get_values(self, data_key):
        """
        Get the values for a given data column for all entries

        :param data_key: name of the data key to return the values

        :returns: list of values, corresponding to the entries for the
                  given data in the sources
        """
        if data_key not in self._column_spec._fields:
            raise ValueError(f'Field {data_key} does not exist')

        values = []
        for entry in self.values():
            values.append(entry._asdict()[data_key])

        return values

    def min(self, data_key, separate=False, mask=None):
        """
        Get the minimum value for a given data column for all entries

        :param data_key: name of the data key to determine the minimum
        :param separate: bool if True the minimum will be determined and returned
                         for all entries separately
        :param mask: optional mask to select specifc rows from the data entries

        :returns: minimum value for all entries either combined or as a list
        """
        if data_key not in self._column_spec._fields:
            raise ValueError(f'Field {data_key} does not exist')

        if mask is not None:
            if len(mask) == len(self):
                mask_gen = (mask_indx for mask_indx in mask)
            else:
                mask_gen = (mask for i in self)
        else:
            mask_gen = (None for i in self)

        min_val = []
        for (entry, source), mask_entry in zip(self.items(), mask_gen):

            key = entry._asdict()[data_key]

            if mask_entry is None:
                data = source[key]
            else:
                data = source[key][mask_entry]

            if isinstance(source[key], (np.ndarray, pd.Series)):
                min_val.append(data.min())
            else:
                min_val.append(min(data))

        if separate:
            return min_val
        else:
            return min(min_val)

    def max(self, data_key, separate=False, mask=None):
        """
        Get the maximum value for a given data column for all entries

        :param data_key: name of the data key to determine the maximum
        :param separate: bool if True the maximum will be determined and returned
                         for all entries separately
        :param mask: optional mask to select specifc rows from the data entries

        :returns: maximum value for all entries either combined or as a list
        """
        if data_key not in self._column_spec._fields:
            raise ValueError(f'Field {data_key} does not exist')

        if mask is not None:
            if len(mask) == len(self):
                mask_gen = (mask_indx for mask_indx in mask)
            else:
                mask_gen = (mask for i in range(len(self)))
        else:
            mask_gen = (None for i in range(len(self)))

        max_val = []
        for (entry, source), mask_entry in zip(self.items(), mask_gen):

            key = entry._asdict()[data_key]

            if mask_entry is None:
                data = source[key]
            else:
                data = source[key][mask_entry]

            if isinstance(source[key], (np.ndarray, pd.Series)):
                max_val.append(data.max())
            else:
                max_val.append(max(data))

        if separate:
            return max_val
        else:
            return max(max_val)

    def apply(self, data_key, lambda_func):
        """
        Apply a function to a given data column for all entries

        .. warning::
            This operation is done in-place. Meaning if there are multiple
            data entries pointing to the same data set and only one should be
            modified by this method, the data needs to be copied beforehand
            using :py:meth:`copy_data()`

        :param data_key: name of the data key to apply the function
        :param lambda_func: function to apply to the data
        """
        if data_key not in self._column_spec._fields:
            raise ValueError(f'Field {data_key} does not exist')

        for indx, (entry, source) in enumerate(self.items()):

            key = entry._asdict()[data_key]

            if isinstance(source[key], pd.Series):
                if isinstance(source, pd.DataFrame):
                    dataframe_func = lambda x, k=key: lambda_func(x) if x.name == k else x
                    new_source = source.apply(dataframe_func)
                    if isinstance(self.data, list):
                        self.data[indx] = new_source
                    else:
                        self.data = new_source
                else:
                    source[key] = source[key].apply(lambda_func)
            elif isinstance(source[key], np.ndarray):
                source[key] = lambda_func(source[key])
            else:
                source[key] = [lambda_func(value) for value in source[key]]

    def get_function_result(self, data_key, func, list_return=False, **kwargs):
        """
        Apply a function to a given data column for all entries and return the results

        :param data_key: name of the data key to apply the function to
        :param func: function to apply to the data to get the results
                     if func is a string then it will be used to get the attribute
                     with the corresponding name from the source and call it
        """
        if data_key not in self._column_spec._fields:
            raise ValueError(f'Field {data_key} does not exist')

        result = []
        for indx, (entry, source) in enumerate(self.items()):

            key = entry._asdict()[data_key]
            if isinstance(func, str):
                result.append(getattr(source[key], func)(**kwargs))
            else:
                result.append(func(source[key], **kwargs))

        if len(result) == 1 and not list_return:
            return result[0]
        else:
            return result

    def sort_data(self, by_data_keys, **kwargs):
        """
        Sort the data by the given data_key(s)

        .. note::
            This function will convert the data arguments to ``pd.Dataframe``
            objects

        .. note::
            If there are multiple plot sets and only one data source. This function
            will expand the data to be one data source sorted according to the data_keys
            for each plot

        :param by_data_keys: str or list of str of the data_keys to sort by

        Kwargs are passed on to ``pd.Dataframe.sort_values()``
        """

        if not isinstance(by_data_keys, list):
            by_data_keys = [by_data_keys]

        for data_key in by_data_keys:
            if data_key not in self._column_spec._fields:
                raise ValueError(f'Field {data_key} does not exist')

        #For sorting data we always go to a pandas DataFrame for simplicity

        expand_data = not isinstance(self.data, list) and len(self) > 1

        if expand_data:
            data = []

        for indx, (entry, source) in enumerate(self.items()):

            if not isinstance(source, pd.DataFrame):
                source = pd.DataFrame(data=source)

            sort_keys = [entry._asdict()[data_key] for data_key in by_data_keys]
            sorted_source = source.sort_values(sort_keys, **kwargs)

            if expand_data:
                data.append(sorted_source)
            else:
                if isinstance(self.data, list):
                    self.data[indx] = sorted_source
                else:
                    self.data = sorted_source

        if expand_data:
            self.data = data

    def group_data(self, by, **kwargs):
        """
        Group the data by the given data_key(s) or other arguments for groupby

        .. note::
            This function will convert the data arguments to ``pd.Dataframe``
            objects

        :param by: str or list of str of the data_keys to sort by or other valid
                   arguments for by in ``pd.Dataframe.groupby()``

        Kwargs are passed on to ``pd.Dataframe.groupby()``
        """

        by_data_keys = None
        if isinstance(by, (list, str)):
            by_data_keys = by
            if not isinstance(by_data_keys, list):
                by_data_keys = [by_data_keys]

            for data_key in by_data_keys:
                if data_key not in self._column_spec._fields:
                    raise ValueError(f'Field {data_key} does not exist')

        #For grouping data we always go to a pandas Dataframe
        columns = []
        sources = []
        masks = []

        for indx, ((entry, source), mask) in enumerate(zip(self.items(), self.mask)):

            if not isinstance(source, pd.DataFrame):
                source = pd.DataFrame(data=source)

            if by_data_keys is not None:
                group_keys = [entry._asdict()[data_key] for data_key in by_data_keys]
                gb = source.groupby(group_keys, **kwargs)
            else:
                gb = source.groupby(by, **kwargs)

            columns.extend([entry] * len(gb))
            sources.extend([gb.get_group(x) for x in gb.groups])
            masks.extend([mask] * len(gb))

        self.columns = columns
        self.data = sources
        self.mask = masks

    def shift_data(self, data_key, shifts, shifted_data_key=None, separate_data=True, negative=False):
        """
        Apply shifts to a given data column for all entries

        :param data_key: name of the data key to shift
        :param shifts: float or array of floats with the shifts to apply
        :param shifted_data_key: optional string, if given the data will be copied
                                 to this data key
        :param separate_data: bool, if True and shifted_data_key is not given the data
                              will be copied to itself (This separates the data for all columns)
        :param negative: bool if True the shifts are applied with a minus sign
        """
        if data_key not in self._column_spec._fields:
            raise ValueError(f'Field {data_key} does not exist')

        if shifted_data_key is not None:
            self.copy_data(data_key, shifted_data_key)
            data_key = shifted_data_key
        elif separate_data:
            self.copy_data(data_key, data_key, force=True)

        if isinstance(shifts, (np.ndarray, list, pd.Series)):
            if len(shifts) != len(self):
                raise ValueError(f"Wrong number of shifts: Expected '{len(self)}' got '{len(shifts)}'")
        else:
            shifts = [shifts] * len(self)

        for (entry, source), shift in zip(self.items(), shifts):

            key = entry._asdict()[data_key]
            if isinstance(source[key], (ColumnDataSource, pd.Series, np.ndarray)):
                if negative:
                    source[key] -= shift
                else:
                    source[key] += shift
            else:
                if negative:
                    source[key] = [value - shift for value in source[key]]
                else:
                    source[key] = [value + shift for value in source[key]]

    def copy_data(self, data_key_from, data_key_to, prefix=None, rename_original=False, force=False):
        """
        Copy the data for a given data key to another one

        :param data_key_from: data key to copy from
        :param data_key_to: data key to copy to
        :param prefix: optional prefix to use for the renamed data entries. Can be used
                       to avoid name clashes. If not given the data keys are used
        :param rename_original: optional bool (default False). If True the original entries are renamed
                                instead of the ones under ``data_key_to``
        """
        if data_key_from not in self._column_spec._fields:
            raise ValueError(f'Field {data_key_from} does not exist')

        if data_key_to not in self._column_spec._fields:
            if self.strict_data_keys:
                raise ValueError(f'Field {data_key_to} does not exist')

            self._add_data_key(data_key_to)

        for indx, (entry, source) in enumerate(self.items()):

            key = entry._asdict()[data_key_from]
            if rename_original:
                new_key = f'{prefix}_{indx}' if prefix is not None else f'{data_key_from}_{indx}'
                self.columns[indx] = entry._replace(**{data_key_from: new_key, data_key_to: key})
            else:
                new_key = f'{prefix}_{indx}' if prefix is not None else f'{data_key_to}_{indx}'
                self.columns[indx] = entry._replace(**{data_key_to: new_key})

            if new_key in source and not force:
                raise ValueError(f'Key {new_key} already exists')

            if isinstance(source, pd.DataFrame):
                new_column = pd.Series(data=source[key], name=new_key, copy=True)
                new_source = pd.concat([source, new_column], axis=1)
                if isinstance(self.data, list):
                    self.data[indx] = new_source
                else:
                    self.data = new_source
            elif isinstance(source, ColumnDataSource):
                source.add(copy.copy(source[key]), name=new_key)
            else:
                source[new_key] = copy.copy(source[key])

    def distinct_datasets(self, data_key):
        """
        Return how many different data sets are present for the given
        data key

        :param      data_key:  The data key to analyse

        :returns: int of the number of different datasets
        """
        if data_key not in self._column_spec._fields:
            raise ValueError(f'Field {data_key} does not exist')

        data_sets = []
        for entry, source in self.items():
            key = entry._asdict()[data_key]

            normed_set = source[key]
            if isinstance(source[key], pd.Series):
                normed_set = source[key].to_numpy()

            if all(not np.array_equal(normed_set, prev) for prev in data_sets):
                data_sets.append(normed_set)

        return len(data_sets)

    def __len__(self):
        return len(self.masked_columns)

    def __getitem__(self, key):
        if isinstance(self.data, list):
            if isinstance(key, tuple):
                return self.data[key[0]][key[1:]]
            else:
                raise KeyError("No index given but data is a list. Provide key as '(index,key)'")
        else:
            return self.data[key]

    def export(self, **kwargs):
        raise NotImplementedError


class PlotDataIterator:
    """
    Class containing the iteration behaviour over the
    :py:class:`PlotData` class. Can be used in three modes:

      - `keys`: Returns the keys to be entered in the corresponding data sources for each entry
      - `values`: Returns the data for each entry
      - `items`: Returns the keys and the data sources in a tuple

    The keys and values are always returned in a ``namedtuple`` with fields corresponding
    to the set data keys
    """

    def __init__(self, plot_data, mode='values'):
        self._plot_data = plot_data
        self._column_iter = iter(col for col, msk in zip(self._plot_data.columns, self._plot_data.mask) if msk)

        self._data_indx = 0
        self._iter_mode = mode

    def __iter__(self):
        return self

    def __next__(self):
        columns = next(self._column_iter)
        if self._iter_mode == 'keys':
            return columns
        elif self._iter_mode == 'values':
            if isinstance(self._plot_data.data, list):
                plot_data = {
                    key: self._plot_data.data[self._data_indx][val] if val is not None else None
                    for key, val in columns._asdict().items()
                }
                self._data_indx += 1
            else:
                plot_data = {
                    key: self._plot_data.data[val] if val is not None else None
                    for key, val in columns._asdict().items()
                }
            return self._plot_data._column_spec(**plot_data)
        elif self._iter_mode == 'items':
            if isinstance(self._plot_data.data, list):
                data_source = self._plot_data.data[self._data_indx]
                self._data_indx += 1
            else:
                data_source = self._plot_data.data
            return columns, data_source
        raise StopIteration


def normalize_list_or_array(data, key, out_data, flatten_np=False, forbid_split_up=False):
    """
    Split up a given list/numpy array or pd.Series to be used in the plotting methods

    :param data: The (array-like) data to be normalized
    :param key: key under which to enter the new data
    :param out_data: dict containining previously normalized data
    :param flatten_np: bool, if True multidimensional numpy arrays are flattened
    :param forbid_split_up: bool, if True multidimensional arrays are not split up

    The rules are the following:
        - if ``data`` is a multidimensional array (list of lists, etc.)
          and it is not forbidden by the given argument the first dimension
          of the array is iterated over and interpreted as separate entries
          (if the data was previously split up into multiple sets a length check is performed)
        - if ``data`` is a one-dimensional array and of a different length than the
          number of defined data sets it is added to all previously existing entries
        - if ``data`` is a one-dimensional array and of the same length as the
          number of defined data sets each entry is added to the corresponding data set

    :returns: list of dicts or dict containing the nomralized data
    """
    LIST_TYPES = (list, np.ndarray, pd.Series)

    if isinstance(data, np.ndarray) and flatten_np:
        data = data.flatten()

    if isinstance(data, LIST_TYPES):
        if isinstance(data[0], LIST_TYPES) and not forbid_split_up:
            #Split up
            if isinstance(out_data, list):
                if len(out_data) != len(data):
                    raise ValueError(
                        f"Mismatch of dimensions: Got two different dimensions 'key' {len(data)} 'previous' {len(out_data)}"
                    )
                for indx, (entry, new_data) in enumerate(zip(out_data, data)):
                    entry[f'{key}_{indx}'] = new_data
            else:
                new_list = []
                for indx, new_data in enumerate(data):
                    old_data = out_data.copy()
                    new_list.append({
                        (f'{key}_{indx}' if val is not None else key): val for key, val in old_data.items()
                    })
                    new_list[-1][f'{key}_{indx}'] = new_data
                out_data = new_list

            return out_data
        elif isinstance(out_data, list):
            if len(out_data) == len(data):
                for indx, (entry, new_data) in enumerate(zip(out_data, data)):
                    entry[f'{key}_{indx}'] = new_data
                return out_data

    if isinstance(out_data, list):
        for indx, entry in enumerate(out_data):
            entry[f'{key}_{indx}'] = data
    else:
        out_data[key] = data

    return out_data


def _normalize_dict_entries(dict_data):

    LIST_TYPES = (list, np.ndarray, pd.Series)

    length = max(len(data) for data in dict_data.values() if isinstance(data, LIST_TYPES))

    for key, val in dict_data.items():
        if not isinstance(val, LIST_TYPES):
            dict_data[key] = np.ones(length) * val
        elif len(val) != length:
            raise ValueError('Different lengths of data sets are not allowed for this plot'
                             f"Expected '{length}' got '{len(val)}'")

    return dict_data


def process_data_arguments(data=None,
                           single_plot=False,
                           mask=None,
                           use_column_source=False,
                           flatten_np=False,
                           forbid_split_up=None,
                           same_length=False,
                           **kwargs):
    """
    Initialize PlotData from np.arrays or lists of np.arrays or lists or a already given
    data argument, i.e. mapping

    :param data: either None or Mapping to be used as the data in the PlotData class
    :param single_plot: bool, if True only a single dataset is allowed
    :param mask: list of bools deactivating some data sets for plotting
    :param use_column_source: bool, if True all data arguments are converted to ColumnDataSource of bokeh
    :param flatten_np: bool, if True multidimensional numpy arrays are flattened (Only if data not given)
    :param forbid_split_up: set of keys for which not to split up multidimensional arrays
    :same_length: bool if True and any sources are dicts it will be checked for same dimensions
                  in (ALL) entries (not only for keys plotted against each other)

    Kwargs define which keys belong to which data entries if data is given or they contain
    the data to be normalized

    The following two example calls will both create a PlotData object with the same two
    plot data sets with the entries ``x`` and ``y``::

        import numpy as np

        x = np.linspace(-10,10,100)
        y1 = y**2
        y2 = np.sin(x)

        #Use a predefined data argument (a dict in this case) and the keys in the kwargs
        p = process_data_arguments({'x': x, 'y1': y1, 'y2': y2}, x='x', y=['y1','y2'])

        #Let the function normalize the given arrays
        p = process_data_arguments=(x=x,y=[y1, y2])

    :returns: A :py:class:`PlotData` object corresponding to the given data
    """

    if forbid_split_up is None:
        forbid_split_up = set()

    if data is None:
        data = {}
        keys = {}

        for key, val in kwargs.items():
            if val is None:
                continue
            data = normalize_list_or_array(val,
                                           key,
                                           data,
                                           flatten_np=flatten_np,
                                           forbid_split_up=key in forbid_split_up)
        for key, val in kwargs.items():
            if val is not None:
                if isinstance(data, list):
                    keys[key] = [f'{key}_{indx}' for indx in range(len(data))]
                else:
                    keys[key] = key
            else:
                keys[key] = None
    else:
        keys = kwargs

    p_data = PlotData(data, mask=mask, use_column_source=use_column_source, same_length=same_length, **keys)

    if len(p_data) != 1 and single_plot:
        raise ValueError(f'Got multiple data sets ({len(p_data)}) but expected 1')

    return p_data
