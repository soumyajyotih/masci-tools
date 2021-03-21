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
This module defines commonly used recipes for the :py:class:`~masci_tools.io.parsers.hdf5.reader.HDF5Reader`

Available are:
    - Recipe for bandstructure calculations with Fleur
    - Recipes for almost all DOS calculation modes of Fleur

A Recipe is a python dictionary in a specific format.

A Template Example:

.. code-block:: python

    from masci_tools.io.parser.hdf5.readers import Transformation, AttribTransformation

    RecipeExample = {
        'datasets': {
            'example_dataset': {
                'h5path': '/path/in/hdf/file',
                'transforms': [Transformation(name='get_first_element')]
            },
            'example_attrib_transform': {
                'h5path': '/other/path/in/hdf/file',
                'transforms': [AttribTransformation(name='multiply_by_attribute', attrib_name='example_attribute')]
            }
        },
        'attributes': {
            'example_attribute': {
                'h5path':
                '/path/in/hdf/file',
                'transforms':
                [Transformation(name='get_attribute', args=('attribName',)),
                 Transformation(name='get_first_element')]
            }
        }
    }

The Recipe consists of two sections 'datasets' and 'attributes'. All data from these two sections will be returned
in separate python dictionaries by the :py:class:`~masci_tools.io.parsers.hdf5.reader.HDF5Reader` class

Each entry in those sections has to have a `h5path` entry, which will specify the dataset to initially
read from the hdf file. Then each entry can define a entry `transforms` with a list of the namedtuples
imported at the top of the code example. These correponds to function calls to functions in
:py:mod:`~masci_tools.io.parsers.hdf5.transforms` to transform the read in data

Entries in the `attributes` section are read and transformed first and can subsequently be used in transformations
for the `datasets`. These correpsond to the transforms created with the :py:class:`~masci_tools.io.parsers.hdf5.reader.AttribTransformation`
namedtuple instead of :py:class:`~masci_tools.io.parsers.hdf5.reader.Transformation`.
"""
from masci_tools.util.constants import HTR_TO_EV, BOHR_A
from masci_tools.io.parsers.hdf5.reader import Transformation, AttribTransformation


def dos_recipe_format(group):

    if group == 'Local':
        atom_prefix = 'MT'
    elif group == 'jDOS':
        atom_prefix = 'jDOS'
    elif group == 'Orbcomp':
        atom_prefix = 'ORBCOMP'
    elif group == 'mcd':
        atom_prefix = 'MCD'
    else:
        raise ValueError(f'Unknown group: {group}')

    return {
        'datasets': {
            'dos': {
                'h5path':
                f'/{group}/DOS',
                'transforms': [
                    Transformation(name='get_all_child_datasets', kwargs={'ignore': 'energyGrid'}),
                    AttribTransformation(name='add_partial_sums',
                                         attrib_name='atom_groups',
                                         args=('{atom_prefix}:{{}}'.format(atom_prefix=atom_prefix).format,)),
                    Transformation(name='multiply_scalar', args=(1.0 / HTR_TO_EV,)),
                    Transformation(name='split_array', kwargs={'suffixes': ['up', 'down']})
                ],
                'unpack_dict':
                True,
            },
            'energy_grid': {
                'h5path': f'/{group}/DOS/energyGrid',
                'transforms': [Transformation(name='multiply_scalar', args=(HTR_TO_EV,))]
            }
        },
        'attributes': {
            'atoms_elements': {
                'h5path': '/atoms/atomicNumbers',
                'description': 'Atomic numbers',
                'transforms': [Transformation(name='periodic_elements')]
            },
            'atom_groups': {
                'h5path': '/atoms/equivAtomsGroup'
            },
            'fermi_energy': {
                'h5path':
                '/general',
                'description':
                'fermi_energy of the system',
                'transforms': [
                    Transformation(name='get_attribute', args=('lastFermiEnergy',)),
                    Transformation(name='get_first_element')
                ]
            },
            'spins': {
                'h5path':
                '/general',
                'description':
                'number of distinct spin directions in the system',
                'transforms':
                [Transformation(name='get_attribute', args=('spins',)),
                 Transformation(name='get_first_element')]
            }
        }
    }


#DOS Recipes
FleurDOS = dos_recipe_format('Local')
FleurJDOS = dos_recipe_format('jDOS')
FleurORBCOMP = dos_recipe_format('Orbcomp')
FleurMCD = dos_recipe_format('mcd')

#Recipe for bandstructures
FleurBands = {
    'datasets': {
        'weights': {
            'h5path':
            '/Local/BS',
            'transforms': [
                Transformation(name='get_all_child_datasets', kwargs={'ignore': ['eigenvalues', 'kpts']}),
                AttribTransformation(name='add_partial_sums', attrib_name='atom_groups', args=('MT:{}'.format,)),
                Transformation(name='split_array', kwargs={'suffixes': ['up', 'down']})
            ],
            'unpack_dict':
            True
        },
        'eigenvalues': {
            'h5path':
            '/Local/BS/eigenvalues',
            'transforms': [
                Transformation(name='multiply_scalar', args=(HTR_TO_EV,)),
                Transformation(name='split_array', kwargs={
                    'suffixes': ['up', 'down'],
                    'name': 'eigenvalues'
                })
            ],
            'unpack_dict':
            True
        },
        'kpath': {
            'h5path':
            '/Local/BS/kpts',
            'transforms': [
                AttribTransformation(name='multiply_by_attribute',
                                     attrib_name='reciprocal_cell',
                                     kwargs={
                                         'reverse_order': True,
                                         'by_element': True
                                     }),
                Transformation(name='calculate_norm', kwargs={'between_neighbours': True}),
                Transformation(name='cumulative_sum')
            ]
        },
        'kpoints': {
            'h5path': 'Local/BS/kpts',
        }
    },
    'attributes': {
        'atoms_elements': {
            'h5path': '/atoms/atomicNumbers',
            'description': 'Atomic numbers',
            'transforms': [Transformation(name='periodic_elements')]
        },
        'atoms_position': {
            'h5path': '/atoms/positions',
            'description': 'Atom coordinates per atom',
        },
        'atom_groups': {
            'h5path': '/atoms/equivAtomsGroup'
        },
        'bravais_matrix': {
            'h5path': '/cell/bravaisMatrix',
            'description': 'Coordinate transformation internal to physical for atoms',
            'transforms': [Transformation(name='multiply_scalar', args=(BOHR_A,))]
        },
        'reciprocal_cell': {
            'h5path': '/cell/reciprocalCell'
        },
        'special_kpoint_indices': {
            'h5path': '/kpts/specialPointIndices'
        },
        'special_kpoint_labels': {
            'h5path': '/kpts/specialPointLabels',
            'transforms': [Transformation(name='convert_to_str')]
        },
        'fermi_energy': {
            'h5path':
            '/general',
            'description':
            'fermi_energy of the system',
            'transforms':
            [Transformation(name='get_attribute', args=('lastFermiEnergy',)),
             Transformation(name='get_first_element')]
        },
        'spins': {
            'h5path': '/general',
            'description': 'number of distinct spin directions in the system',
            'transforms':
            [Transformation(name='get_attribute', args=('spins',)),
             Transformation(name='get_first_element')]
        }
    }
}
