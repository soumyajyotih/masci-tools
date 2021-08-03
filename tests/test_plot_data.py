# -*- coding: utf-8 -*-
"""
Tests of the `masci_tools.vis.data` module
"""
import pytest
from itertools import product
import numpy as np
import pandas as pd

USE_CDS = True
try:
    from bokeh.models import ColumnDataSource
except ImportError:
    USE_CDS = False


def test_normalize_list_or_array():
    """
    Test of the normalize_list_or_array function
    """
    from masci_tools.vis.data import normalize_list_or_array

    #Single array
    x = np.linspace(-1, 1, 10)
    data = normalize_list_or_array(x, 'x', {})
    assert data == {'x': x}

    y = [np.linspace(-5, 1, 10), [1, 2, 3, 5]]
    data = normalize_list_or_array(y, 'y', data)
    assert data == [{'x_0': x, 'y_0': y[0]}, {'x_1': x, 'y_1': y[1]}]

    z = 5
    data = normalize_list_or_array(z, 'z', data)
    assert data == [{'x_0': x, 'y_0': y[0], 'z_0': z}, {'x_1': x, 'y_1': y[1], 'z_1': 5}]

    color = ['red', 'blue']
    data = normalize_list_or_array(color, 'color', data)
    assert data == [{
        'x_0': x,
        'y_0': y[0],
        'z_0': z,
        'color_0': 'red'
    }, {
        'x_1': x,
        'y_1': y[1],
        'z_1': z,
        'color_1': 'blue'
    }]

    color2 = [pd.Series([1, 2, 3]), pd.Series([4, 5, 6])]
    data = normalize_list_or_array(color2, 'color', data)
    assert data == [{
        'x_0': x,
        'y_0': y[0],
        'z_0': z,
        'color_0': color2[0]
    }, {
        'x_1': x,
        'y_1': y[1],
        'z_1': z,
        'color_1': color2[1]
    }]

    too_long_data = [np.linspace(0, 1, 2), np.linspace(3, 4, 5), np.linspace(6, 7, 8)]
    with pytest.raises(ValueError):
        data = normalize_list_or_array(too_long_data, 'dont_enter_this', data)


def test_normalize_list_or_array_flatten_np():
    """
    Test of the normalize_list_or_array function with flatten_np=True
    """
    from masci_tools.vis.data import normalize_list_or_array

    x = np.linspace(-1, 1, 10)
    y = np.linspace(-1, 1, 10)
    xv, yv = np.meshgrid(x, y)

    data = normalize_list_or_array(xv, 'x', {}, flatten_np=True)
    data = normalize_list_or_array(yv, 'y', data, flatten_np=True)

    assert data['x'].shape == (100,)
    assert data['y'].shape == (100,)


def test_normalize_list_or_array_forbid_split_up():
    """
    Test of the normalize_list_or_array function with forbid_split_up=True
    """
    from masci_tools.vis.data import normalize_list_or_array

    x = np.linspace(-1, 1, 10)
    data = normalize_list_or_array(x, 'x', {}, forbid_split_up=True)
    assert data == {'x': x}

    y = [np.linspace(-5, 1, 10), [1, 2, 3, 5]]
    data = normalize_list_or_array(y, 'y', data, forbid_split_up=True)
    assert data == {'x': x, 'y': y}


ENTRIES = [{
    'x': 'x',
    'y': 'y'
}, {
    'x_values': 'test',
    'y': ['y1', 'y2', 'y3']
}, {
    'color': ['test', 'x'],
    'type': ['y1', 'y2']
}]

COLUMNS = [[{
    'x': 'x',
    'y': 'y'
}], [{
    'x_values': 'test',
    'y': 'y1'
}, {
    'x_values': 'test',
    'y': 'y2'
}, {
    'x_values': 'test',
    'y': 'y3'
}], [{
    'color': 'test',
    'type': 'y1'
}, {
    'color': 'x',
    'type': 'y2'
}]]

x_data = np.linspace(-10, 10, 101)

dict_data = {
    'x': x_data,
    'test': x_data * 4,
    'y': x_data**2,
    'y1': 5 * x_data - 10,
    'y2': np.cos(x_data),
    'y3': np.exp(x_data)
}

#yapf: disable
dict_data_multiple = [[{
                          'x': dict_data['x'],
                          'y': dict_data['y']
                      }],
                      [{
                          'test': dict_data['test'],
                          'y1': dict_data['y1']
                      }, {
                          'test': dict_data['test'],
                          'y2': dict_data['y2']
                      }, {
                          'test': dict_data['test'],
                          'y3': dict_data['y3']
                      }],
                      [{
                          'test': dict_data['test'],
                          'y1': dict_data['y1']
                      }, {
                          'x': dict_data['x'],
                          'y2': dict_data['y2']
                      }]]
#yapf: enable


SINGLE_SOURCES = [dict_data, pd.DataFrame(data=dict_data)]

if USE_CDS:
    SINGLE_SOURCES.append(ColumnDataSource(dict_data))

MULTIPLE_SOURCES = dict_data_multiple.copy()

for row in dict_data_multiple:
    MULTIPLE_SOURCES.append([pd.DataFrame(data=data) for data in row])

if USE_CDS:
    for row in dict_data_multiple:
        MULTIPLE_SOURCES.append([ColumnDataSource(data) for data in row])


def _get_plot_data_test_arguments(*args, only_single=False):
    """
    Returns a list for parametrizing plot_data tests, which will be parametrized
    for single sources and list sources of all types

    all given arguments should be defined once for all rows in ``ENTRIES`` and will be zipped
    together with the sources
    """
    repeats = 2
    if USE_CDS:
        repeats = 3

    res = list(product(zip(ENTRIES, *args), SINGLE_SOURCES))
    if not only_single:
        res += list(zip(zip(ENTRIES * repeats, *tuple(arg * repeats for arg in args)), MULTIPLE_SOURCES))

    return res


@pytest.mark.parametrize('inputs, data', _get_plot_data_test_arguments(COLUMNS))
def test_plot_data(inputs, data):
    """
    Basic test of PlotData
    """
    from masci_tools.vis.data import PlotData

    entries, expected_columns = inputs

    p = PlotData(data, **entries, use_column_source=True)

    assert len(p) == len(expected_columns)
    assert len(list(p.keys())) == len(expected_columns)
    assert len(list(p.values())) == len(expected_columns)
    assert len(list(p.items())) == len(expected_columns)

    for entry, col in zip(p.keys(), expected_columns):
        assert entry._fields == tuple(entries.keys())
        assert entry._asdict() == col

    for indx, (entry, col) in enumerate(zip(p.values(), expected_columns)):
        assert entry._fields == tuple(entries.keys())
        if isinstance(data, list):
            assert entry._asdict() == {
                key: data[indx][val] if getattr(data[indx], 'data', None) is None else data[indx].data[val]
                for key, val in col.items()
            }
        else:
            assert entry._asdict() == {
                key: data[val] if getattr(data, 'data', None) is None else data.data[val] for key, val in col.items()
            }

    for indx, ((entry, source), col) in enumerate(zip(p.items(), expected_columns)):
        assert entry._fields == tuple(entries.keys())
        assert entry._asdict() == col
        if isinstance(data, pd.DataFrame):
            assert source.equals(data)
        elif isinstance(data, list):
            if isinstance(data[indx], pd.DataFrame):
                assert source.equals(data[indx])
            else:
                assert source == data[indx]
        else:
            assert source == data

    entry = p.keys(first=True)
    assert entry._fields == tuple(entries.keys())
    assert entry._asdict() == expected_columns[0]

    entry = p.values(first=True)
    assert entry._fields == tuple(entries.keys())
    if isinstance(data, list):
        assert entry._asdict() == {
            key: data[0][val] if getattr(data[0], 'data', None) is None else data[0].data[val]
            for key, val in expected_columns[0].items()
        }
    else:
        assert entry._asdict() == {
            key: data[val] if getattr(data, 'data', None) is None else data.data[val]
            for key, val in expected_columns[0].items()
        }

    entry, source = p.items(first=True)
    assert entry._fields == tuple(entries.keys())
    assert entry._asdict() == expected_columns[0]
    if isinstance(data, pd.DataFrame):
        assert source.equals(data)
    elif isinstance(data, list):
        if isinstance(data[0], pd.DataFrame):
            assert source.equals(data[0])
        else:
            assert source == data[0]
    else:
        assert source == data


EXPECTED_MIN = [{
    'x': [-10.0],
    'y': [0.0]
}, {
    'x_values': [-40.0, -40.0, -40.0],
    'y': [-60.0, -0.9996930, 4.53999e-05]
}, {
    'color': [-40.0, -10.0],
    'type': [-60.0, -0.9996930]
}]


@pytest.mark.parametrize('inputs, data', _get_plot_data_test_arguments(EXPECTED_MIN))
def test_plot_data_min(inputs, data):
    """
    Test of PlotData min function
    """
    from masci_tools.vis.data import PlotData

    entries, expected_min = inputs

    p = PlotData(data, **entries, use_column_source=True)

    for key, expected in expected_min.items():

        assert p.min(key) == pytest.approx(min(expected))


@pytest.mark.parametrize('inputs, data', _get_plot_data_test_arguments(EXPECTED_MIN))
def test_plot_data_min_separate(inputs, data):
    """
    Test of PlotData min function
    """
    from masci_tools.vis.data import PlotData

    entries, expected_min = inputs

    p = PlotData(data, **entries, use_column_source=True)

    for key, expected in expected_min.items():

        assert p.min(key, separate=True) == pytest.approx(expected)


@pytest.mark.parametrize('data_args', _get_plot_data_test_arguments(only_single=True))
def test_plot_data_min_mask(data_args):
    """
    Test of PlotData min function
    """
    from masci_tools.vis.data import PlotData

    _, data = data_args

    entries = ENTRIES[0]
    p = PlotData(data, **entries, use_column_source=True)
    assert p.min('x', mask=x_data > 5) == pytest.approx(5.2)

    entries = ENTRIES[1]
    p = PlotData(data, **entries, use_column_source=True)
    assert p.min('y', mask=[x_data > 5, x_data < 5, x_data >= 9],
                 separate=True) == pytest.approx([16.0, -0.9996930, 8103.0839275])


def test_plot_data_max():
    pass


def test_plot_data_apply():
    pass


def test_plot_data_copy_data():
    pass


def test_process_data_arguments():
    pass


def test_process_data_arguments_data_given():
    pass


def test_process_data_arguments_single_plot():
    pass
