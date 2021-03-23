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
Plotting routines for fleur density of states with and without hdf
"""
import warnings
import io


def fleur_plot_dos(dosfile, dosfile_dn=None, hdf_group='Local', spinpol=True, bokeh_plot=False, **kwargs):
    """
    Plot the density of states either from a `banddos.hdf` or text output
    """
    from masci_tools.io.parsers.hdf5 import HDF5Reader
    from masci_tools.io.parsers.hdf5.recipes import dos_recipe_format
    from masci_tools.vis.plot_methods import plot_dos, plot_spinpol_dos
    from masci_tools.vis.bokeh_plots import bokeh_dos, bokeh_spinpol_dos
    import pandas as pd

    if isinstance(dosfile, io.IOBase):
        filename = dosfile._file.name
    else:
        filename = dosfile

    if filename.endswith('.hdf'):
        if dosfile_dn is not None:
            warnings.warn('path_to_dosfile_dn is ignored for hdf files')

        dos_recipe = dos_recipe_format(hdf_group)

        with HDF5Reader(dosfile) as h5reader:
            dosdata, attrs = h5reader.read(recipe=dos_recipe)
        dosdata = pd.DataFrame(data=dosdata)

        spinpol = attrs['spins'] == 2 and spinpol
        legend_labels, keys = generate_dos_labels(dosdata, attrs, spinpol)

    else:
        #TODO: txt input
        raise NotImplementedError

    if bokeh_plot:
        if spinpol:
            fig = bokeh_spinpol_dos(dosdata, ynames=keys, legend_label=legend_labels, **kwargs)
        else:
            fig = bokeh_dos(dosdata, ynames=keys, legend_label=legend_labels, **kwargs)
    else:
        if spinpol:
            dosdata_up = [dosdata[key].to_numpy() for key in keys if '_up' in key]
            dosdata_dn = [dosdata[key].to_numpy() for key in keys if '_down' in key]
            fig = plot_spinpol_dos(dosdata_up, dosdata_dn, dosdata['energy_grid'], plot_label=legend_labels, **kwargs)
        else:
            dosdata_up = [dosdata[key].to_numpy() for key in keys if '_up' in key]
            fig = plot_dos(dosdata_up, dosdata['energy_grid'], plot_label=legend_labels, **kwargs)

    return fig


def dos_order(key):

    if key == 'energy_grid':
        return (-1,)

    if '_up' in key:
        key = key.split('_up')[0]
        spin = 0
    else:
        key = key.split('_down')[0]
        spin = 1

    general = ('Total', 'INT', 'Sym')
    orbital_order = ('', 's', 'p', 'd', 'f')

    if key in general:
        return (spin, general.index(key))
    elif ':' in key:
        before, after = key.split(':')

        tail = after.lstrip('0123456789')
        atom_type = int(after[:-len(tail)]) if len(tail) > 0 else int(after[0])

        if tail in orbital_order:
            return (spin, len(general) + atom_type, orbital_order.index(tail))
        else:
            return (spin, len(general) + atom_type, orbital_order)

    return None


def generate_dos_labels(dosdata, attributes, spinpol):

    labels = []
    plot_order = []

    atom_elements = list(attributes['atoms_elements'])

    for key in sorted(dosdata.keys(), key=dos_order):
        if key == 'energy_grid':
            continue

        plot_order.append(key)
        if 'INT' in key:
            key = 'Interstitial'
            if spinpol:
                key = 'Interstitial up/down'
            labels.append(key)
        elif ':' in key:  #Atom specific DOS

            before, after = key.split(':')

            tail = after.lstrip('0123456789')
            atom_type = int(after[:-len(tail)])

            atom_label = attributes['atoms_elements'][atom_type - 1]

            if atom_elements.count(atom_label) != 1:
                atom_occ = atom_elements[:atom_type].count(atom_label)

                atom_label = f'{atom_label}-{atom_occ}'

            if '_up' in tail:
                tail = tail.split('_up')[0]
                if spinpol:
                    tail = f'{tail} up/down'
            else:
                tail = tail.split('_down')[0]
                if spinpol:
                    tail = f'{tail} up/down'

            labels.append(f'{atom_label} {tail}')

        else:
            if '_up' in key:
                key = key.split('_up')[0]
                if spinpol:
                    key = f'{key} up/down'
            elif '_down' in key:
                key = key.split('_down')[0]
                if spinpol:
                    key = f'{key} up/down'
            labels.append(key)

    return labels, plot_order


def select_from_Local(dos_data_up, dos_data_dn, natoms, interstitial, atoms, l_resolved):

    keys_to_plot = {'Total'}

    if interstitial:
        keys_to_plot.add('INT')

    if atoms == 'all':
        atoms = range(1, natoms + 1)
    elif atoms is not None:
        if not isinstance(atoms, list):
            atoms = [atoms]

    if atoms is not None:
        keys_to_plot.update(f'MT:{atom}' for atom in atoms)

    if l_resolved == 'all':
        l_resolved = range(1, natoms + 1)
    elif l_resolved is not None:
        if not isinstance(l_resolved, list):
            l_resolved = [l_resolved]

    if l_resolved is not None:
        keys_to_plot.update(f'MT:{atom}{orbital}' for atom in l_resolved for orbital in 'spdf')

    keys_to_plot = sorted(keys_to_plot)
    dos_data_up = [dos_data_up[key] for key in keys_to_plot]
    if dos_data_dn is not None:
        dos_data_dn = [dos_data_dn[key] for key in keys_to_plot]

    return dos_data_up, dos_data_dn, keys_to_plot