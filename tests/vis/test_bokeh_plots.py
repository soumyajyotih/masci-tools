"""
Tests of the bokeh visualization. Since the concrete visualization is difficult
to test we check the content of the underlying json for correctness
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def test_bokeh_methods_imports():
    """
    Test that all expected functions are still there
    """
    from masci_tools.vis.bokeh_plots import set_bokeh_plot_defaults
    from masci_tools.vis.bokeh_plots import reset_bokeh_plot_defaults
    from masci_tools.vis.bokeh_plots import show_bokeh_plot_defaults
    from masci_tools.vis.bokeh_plots import save_bokeh_defaults
    from masci_tools.vis.bokeh_plots import load_bokeh_defaults
    from masci_tools.vis.bokeh_plots import bokeh_scatter
    from masci_tools.vis.bokeh_plots import bokeh_multi_scatter
    from masci_tools.vis.bokeh_plots import bokeh_line
    from masci_tools.vis.bokeh_plots import bokeh_dos
    from masci_tools.vis.bokeh_plots import bokeh_spinpol_dos
    from masci_tools.vis.bokeh_plots import bokeh_bands
    from masci_tools.vis.bokeh_plots import bokeh_spinpol_bands
    from masci_tools.vis.bokeh_plots import periodic_table_plot
    from masci_tools.vis.bokeh_plots import plot_convergence_results
    from masci_tools.vis.bokeh_plots import plot_convergence_results_m


TEST_CHANGES = [{'marker_size': 50}, {'show': False}, {'straight_line_options': {'line_color': 'red'}}]

EXPECTED_RESULT = [{
    'marker_size': 50
}, {
    'show': False
}, {
    'straight_line_options': {
        'line_color': 'red',
        'line_width': 1.0,
        'line_dash': 'dashed'
    },
}]


@pytest.mark.parametrize('change_dict, result', zip(TEST_CHANGES, EXPECTED_RESULT))
def test_set_defaults(change_dict, result):
    """
    Test the setting of default values
    """
    from masci_tools.vis.bokeh_plots import plot_params
    from masci_tools.vis.bokeh_plots import set_bokeh_plot_defaults
    from masci_tools.vis.bokeh_plots import reset_bokeh_plot_defaults

    value_before = {}
    for key in change_dict:
        value_before[key] = plot_params[key]

    set_bokeh_plot_defaults(**change_dict)

    for key, val in result.items():
        assert plot_params[key] == val

    reset_bokeh_plot_defaults()

    for key, val in value_before.items():
        assert plot_params[key] == val


def test_bokeh_save_defaults(file_regression):
    """
    Test adding of custom parameters
    """
    import tempfile
    from masci_tools.vis.bokeh_plots import set_bokeh_plot_defaults
    from masci_tools.vis.bokeh_plots import reset_bokeh_plot_defaults
    from masci_tools.vis.bokeh_plots import save_bokeh_defaults

    set_bokeh_plot_defaults(marker_size=50,
                            line_alpha=0.5,
                            figure_kwargs={
                                'x_axis_type': 'log',
                                'active_inspect': 'hover'
                            })

    with tempfile.TemporaryDirectory() as td:
        save_bokeh_defaults(Path(td) / 'defaults')

        with open(Path(td) / 'defaults', encoding='utf-8') as file:
            txt = file.read().strip()

    file_regression.check(txt)
    reset_bokeh_plot_defaults()


def test_bokeh_load_defaults(file_regression):
    """
    Test adding of custom parameters
    """
    import tempfile
    from masci_tools.vis.bokeh_plots import set_bokeh_plot_defaults
    from masci_tools.vis.bokeh_plots import reset_bokeh_plot_defaults
    from masci_tools.vis.bokeh_plots import save_bokeh_defaults
    from masci_tools.vis.bokeh_plots import load_bokeh_defaults

    set_bokeh_plot_defaults(marker_size=50,
                            line_alpha=0.5,
                            figure_kwargs={
                                'x_axis_type': 'log',
                                'active_inspect': 'hover'
                            })

    with tempfile.TemporaryDirectory() as td:
        save_bokeh_defaults(Path(td) / 'defaults')

        reset_bokeh_plot_defaults()

        load_bokeh_defaults(Path(td) / 'defaults')

    with tempfile.TemporaryDirectory() as td:
        save_bokeh_defaults(Path(td) / 'defaults')

        with open(Path(td) / 'defaults', encoding='utf-8') as file:
            txt = file.read().strip()

    file_regression.check(txt)
    reset_bokeh_plot_defaults()


def test_scatter_default(check_bokeh_plot):
    """
    Test with default values
    """
    from masci_tools.vis.bokeh_plots import bokeh_scatter
    x = np.linspace(-10, 10, 100)
    y = x**2

    source = pd.DataFrame(data={'x': x, 'y': y})

    p = bokeh_scatter('x', 'y', data=source, show=False)

    check_bokeh_plot(p)


def test_scatter_deprecated_signature(check_bokeh_plot):
    """
    Test with default values and old signature
    """
    from masci_tools.vis.bokeh_plots import bokeh_scatter
    x = np.linspace(-10, 10, 100)
    y = x**2

    source = pd.DataFrame(data={'x': x, 'y': y})

    with pytest.deprecated_call():
        p = bokeh_scatter(source, show=False)

    check_bokeh_plot(p)


def test_scatter_param_change(check_bokeh_plot):
    """
    Test with parameters changed
    """
    from masci_tools.vis.bokeh_plots import bokeh_scatter
    x = np.linspace(-10, 10, 100)
    y = x**2

    source = pd.DataFrame(data={'x': x, 'y': y})

    p = bokeh_scatter('x',
                      'y',
                      data=source,
                      show=False,
                      color='darkred',
                      label_fontsize='24pt',
                      marker='square',
                      marker_size=12,
                      alpha=0.8)

    check_bokeh_plot(p)


def test_scatter_limits(check_bokeh_plot):
    """
    Test with setting limits
    """
    from masci_tools.vis.bokeh_plots import bokeh_scatter
    x = np.linspace(-10, 10, 100)
    y = x**2

    source = pd.DataFrame(data={'x': x, 'y': y})

    p = bokeh_scatter('x', 'y', data=source, show=False, limits={'x': (0, 10), 'y': (-50, 50)})

    check_bokeh_plot(p)


def test_scatter_straight_lines(check_bokeh_plot):
    """
    Test with straight lines
    """
    from masci_tools.vis.bokeh_plots import bokeh_scatter
    x = np.linspace(-10, 10, 100)
    y = x**2

    source = pd.DataFrame(data={'x': x, 'y': y})

    p = bokeh_scatter('x', 'y', data=source, show=False, straight_lines={'vertical': 0, 'horizontal': [10, 20, 30]})

    check_bokeh_plot(p)


def test_scatter_legend(check_bokeh_plot):
    """
    Test with straight lines
    """
    from masci_tools.vis.bokeh_plots import bokeh_scatter
    x = np.linspace(-10, 10, 100)
    y = x**2

    source = pd.DataFrame(data={'x': x, 'y': y})

    p = bokeh_scatter('x', 'y', data=source, show=False, legend_label='Test Data')

    check_bokeh_plot(p)


def test_multi_scatter_default_no_data(check_bokeh_plot):
    """
    Test with default values
    """
    from masci_tools.vis.bokeh_plots import bokeh_multi_scatter

    x = [np.linspace(-10, 10, 100)] * 4 + [np.linspace(-10, 20, 100)]
    y = [x[0]**2, x[1] * 5 + 30, 50 * np.sin(x[2]), 50 * np.cos(x[3]), -5 * x[4] + 30]

    p = bokeh_multi_scatter(x, y, show=False)

    check_bokeh_plot(p)


def test_multi_scatter_deprecated_signature(check_bokeh_plot):
    """
    Test with default values and old signature
    """
    from masci_tools.vis.bokeh_plots import bokeh_multi_scatter
    x = np.linspace(-10, 10, 100)
    y = x**2

    source = pd.DataFrame(data={'x': x, 'y': y})

    with pytest.deprecated_call():
        p = bokeh_multi_scatter(source, show=False)

    check_bokeh_plot(p)


def test_line_default_no_data_line(check_bokeh_plot):
    """
    Test with default values
    """
    from masci_tools.vis.bokeh_plots import bokeh_line

    x = [np.linspace(-10, 10, 100)] * 4 + [np.linspace(-10, 20, 100)]
    y = [x[0]**2, x[1] * 5 + 30, 50 * np.sin(x[2]), 50 * np.cos(x[3]), -5 * x[4] + 30]

    p = bokeh_line(x, y, show=False)

    check_bokeh_plot(p)


def test_line_multi_deprecated_signature_line(check_bokeh_plot):
    """
    Test with default values and old signature
    """
    from masci_tools.vis.bokeh_plots import bokeh_line
    x = np.linspace(-10, 10, 100)
    y = x**2

    source = pd.DataFrame(data={'x': x, 'y': y})

    with pytest.deprecated_call():
        p = bokeh_line(source, show=False)

    check_bokeh_plot(p)


def test_convergence_defaults(check_bokeh_plot, convergence_plot_data):
    """
    Test of convergence plot with default values
    """
    from masci_tools.vis.bokeh_plots import plot_convergence_results

    iteration, distance, energy = convergence_plot_data(1)
    with pytest.deprecated_call():
        p = plot_convergence_results(iteration, distance, energy, show=False)

    check_bokeh_plot(p)


def test_convergence_param_change(check_bokeh_plot, convergence_plot_data):
    """
    Test of convergence plot with changed parameters
    """
    from masci_tools.vis.bokeh_plots import plot_convergence_results

    iteration, distance, energy = convergence_plot_data(1)

    with pytest.deprecated_call():
        p = plot_convergence_results(iteration,
                                     distance,
                                     energy,
                                     show=False,
                                     color='darkred',
                                     label_fontsize='24pt',
                                     marker='square',
                                     marker_size=12,
                                     alpha=0.8)

    check_bokeh_plot(p)


def test_convergence_multi_defaults(check_bokeh_plot, convergence_plot_data):
    """
    Test of multiple convergence plot with default values
    """
    from masci_tools.vis.bokeh_plots import plot_convergence_results_m

    iteration, distance, energy = convergence_plot_data(15)

    with pytest.deprecated_call():
        p = plot_convergence_results_m(iteration, distance, energy, show=False)

    # need to return the figure in order for mpl checks to work
    check_bokeh_plot(p)


def test_lattice_constant_defaults_single(check_bokeh_plot, lattice_constant_data):
    """
    Test with default parameters
    """
    from masci_tools.vis.bokeh_plots import plot_lattice_constant

    scaling, _, energy = lattice_constant_data(1)

    p = plot_lattice_constant(scaling, energy, show=False)

    check_bokeh_plot(p)


def test_lattice_constant_defaults_single_fit(check_bokeh_plot, lattice_constant_data):
    """
    Test with default parameters
    """
    from masci_tools.vis.bokeh_plots import plot_lattice_constant

    scaling, energy_data, fit = lattice_constant_data(1)

    p = plot_lattice_constant(scaling, energy_data, fit_data=fit, show=False)

    check_bokeh_plot(p)


def test_lattice_constant_defaults_multi(check_bokeh_plot, lattice_constant_data):
    """
    Test with default parameters
    """
    from masci_tools.vis.bokeh_plots import plot_lattice_constant

    scaling, _, energy = lattice_constant_data(5)

    p = plot_lattice_constant(scaling, energy, show=False)

    check_bokeh_plot(p)


def test_lattice_constant_defaults_multi_fit(check_bokeh_plot, lattice_constant_data):
    """
    Test with default parameters
    """
    from masci_tools.vis.bokeh_plots import plot_lattice_constant

    scaling, energy_data, fit = lattice_constant_data(5)

    p = plot_lattice_constant(scaling, energy_data, fit_data=fit, show=False)

    check_bokeh_plot(p)


def test_periodic_table_plot_defaults(check_bokeh_plot):
    """
    Test with default parameters
    """
    from masci_tools.vis.bokeh_plots import periodic_table_plot

    p = periodic_table_plot(['atomic radius', 'year discovered'],
                            positions=[0.1, -0.05],
                            show=False,
                            color_data='atomic radius',
                            include_legend=True)

    check_bokeh_plot(p)


def test_matrix_plot_defaults(check_bokeh_plot):
    """
    Test with default parameters
    """
    from masci_tools.vis.bokeh_plots import matrix_plot

    x = np.linspace(-1, 1, 11)
    y = np.linspace(-1, 1, 11)

    xv, yv = np.meshgrid(x, y)
    z = 10 * np.exp(-xv**2 - yv**2)
    xv, yv, z = xv.flatten(), yv.flatten(), z.flatten()

    p = matrix_plot([f'{x:.1f}' for x in z],
                    xv,
                    yv,
                    positions=[0.0],
                    x_offset=-0.06,
                    color_data=z,
                    show=False,
                    block_size=0.18)

    check_bokeh_plot(p)


def test_matrix_plot_categorical_axis(check_bokeh_plot):
    """
    Test with categorical axis
    """
    pytest.importorskip('bokeh', minversion='2.0.0')
    from masci_tools.vis.bokeh_plots import matrix_plot

    x_names = ['Apple', 'Orange', 'Banana', 'Pear', 'Cherry']
    y_names = ['New York', 'Chicago', 'Boston', 'Los Angeles', 'Washington D.C.', 'Houston', 'Philadelphia']

    x = np.linspace(-1, 1, 5)
    y = np.linspace(-1, 1, 7)

    xv, yv = np.meshgrid(x, y)
    z = 10 * np.exp(-xv**2 - yv**2)
    z = z.flatten()
    xv, yv = np.meshgrid(x_names, y_names)
    xv, yv = xv.flatten(), yv.flatten()

    #Dont be confused that the output does not habe the same
    #shape as e^(-r^2). The categories are ordered in the function
    p = matrix_plot([f'{x:.1f}' for x in z],
                    xv,
                    yv,
                    positions=[0.0],
                    x_offset=0.0,
                    color_data=z,
                    show=False,
                    categorical_axis=True,
                    block_size_pixel=150,
                    text_font_size='14pt',
                    text_font_style='bold')

    check_bokeh_plot(p)


def test_matrix_plot_categorical_axis_secondary_color(check_bokeh_plot):
    """
    Test with categorical axis
    """
    pytest.importorskip('bokeh', minversion='2.0.0')
    from masci_tools.vis.bokeh_plots import matrix_plot

    x_names = ['Apple', 'Orange', 'Banana', 'Pear', 'Cherry']
    y_names = ['New York', 'Chicago', 'Boston', 'Los Angeles', 'Washington D.C.', 'Houston', 'Philadelphia']

    x = np.linspace(-1, 1, 5)
    y = np.linspace(-1, 1, 7)

    xv, yv = np.meshgrid(x, y)
    z = 10 * np.exp(-xv**2 - yv**2)
    z = z.flatten()
    z2 = 10 * xv
    z2 = z2.flatten()
    xv, yv = np.meshgrid(x_names, y_names)
    xv, yv = xv.flatten(), yv.flatten()

    #Dont be confused that the output does not habe the same
    #shape as e^(-r^2). The categories are ordered in the function
    p = matrix_plot([f'{x:.1f}' for x in z],
                    xv,
                    yv,
                    positions=[0.0],
                    x_offset=0.0,
                    color_data=z,
                    secondary_color_data=z2,
                    show=False,
                    categorical_axis=True,
                    block_size_pixel=150,
                    text_font_size='14pt',
                    text_font_style='bold')

    check_bokeh_plot(p)
