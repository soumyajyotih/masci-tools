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
This module contains the dictionary with all defined tasks for the outxml_parser.
The entries in the ``TASK_DEFINITION`` dict specify how to parse specific attributes tags.

This needs to be maintained if the specifications do not work for a new schema version
because of changed attribute names for example.

Each entry in the ``TASK_DEFINITION`` dict can contain a series of keys, which by default
correspond to the keys in the output dictionary

The following keys are expected in each entry:
    :param parse_type: str, defines which methods to use when extracting the information
    :param subdict: str, if present the parsed values are put into this key in the output dictionary
    :param overwrite_last: bool, if True no list is inserted and each entry overwrites the last

If `parse_type` is not equal to ``xmlGetter`` the following key is required:
    :param path_spec: dict with all the arguments that should be passed to tag_xpath
                      or attrib_xpath to get the correct path
    :param kwargs: additional arguments to pass to the parsing function

In the case of ``xmlGetter`` the following keys are allowed:
    :param name: name of the function in `masci_tools.util.xml.xml_getters` (required)
    :param result_names: list of str defining the keys under which to enter the outputs of the function

For the allAttribs parse_type there are more keys that can appear:
    :param base_value: str, optional. If given the attribute
                       with this name will be inserted into the key from the task_definition
                       all other keys are formatted as {task_key}_{attribute_name}
    :param overwrite: list of str, these attributes will not create a list and overwrite any value
                      that might be there
    :param flat: bool, if False the dict parsed from the tag is inserted as a dict into the correspondin key
                       if True the values will be extracted and put into the output dictionary with the
                       format {task_key}_{attribute_name}

Each task entry can have additional keys to specify, when to perform the task.
These are denoted with underscores in their names and are all optional:

    :param _general: bool, default False. If True the parsing is not performed for each iteration on the
                     iteration node but beforehand and on the root node
    :param _modes: list of tuples, sets conditions for the keys in fleur_modes to perform the task
                   .e.g. [('jspins', 2), ('soc', True)] means only perform this task for a magnetic soc calculation
    :param _minimal: bool, default False, denotes task to perform when minimal_mode=True is passed to the parser
    :param _special: bool, default False, If true these tasks are not added by default and need to be added manually
    :param _conversions: list of str, gives the names of functions in fleur_outxml_conversions to perform after parsing


The following keys are special at the moment:
    - ``fleur_modes`` specifies how to identify the type of the calculation (e.g. SOC, magnetic, lda+u)
      this is used to determine, whether additional things should be parsed

Following is the current specification of tasks

.. literalinclude:: ../../../../masci_tools/io/parsers/fleur/default_parse_tasks.py
   :language: python
   :lines: 70-
   :linenos:

"""
from masci_tools.util.parse_utils import Conversion

__working_out_versions__ = {'0.34', '0.35', '0.36', '0.37'}
__base_version__ = '0.34'

TASKS_DEFINITION = {
    #--------Definitions for general info from outfile (start, endtime, number_iterations)--------
    'general_out_info': {
        '_general': True,
        '_minimal': True,
        '_conversions': [Conversion(name='calculate_walltime')],
        'creator_name': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'version',
                'not_contains': 'git'
            }
        },
        'creator_target_architecture': {
            'parse_type': 'text',
            'path_spec': {
                'name': 'targetComputerArchitectures'
            }
        },
        'output_file_version': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'fleurOutputVersion'
            }
        },
        'number_of_iterations': {
            'parse_type': 'numberNodes',
            'path_spec': {
                'name': 'iteration'
            }
        },
        'number_of_atoms': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'nat'
            }
        },
        'number_of_atom_types': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'ntype'
            }
        },
        'number_of_kpoints': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'count',
                'contains': 'numericalParameters'
            }
        },
        'start_date': {
            'parse_type': 'allAttribs',
            'path_spec': {
                'name': 'startDateAndTime'
            },
            'flat': False,
            'kwargs': {
                'ignore': ['zone'],
            }
        },
        'end_date': {
            'parse_type': 'allAttribs',
            'path_spec': {
                'name': 'endDateAndTime'
            },
            'flat': False,
            'kwargs': {
                'ignore': ['zone'],
            }
        }
    },
    #--------Defintions for general info from input section of outfile (kmax, symmetries, ..)--------
    'general_inp_info': {
        '_general': True,
        '_minimal': True,
        'title': {
            'parse_type': 'text',
            'path_spec': {
                'name': 'comment'
            }
        },
        'kmax': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'Kmax'
            }
        },
        'gmax': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'Gmax'
            }
        },
        'number_of_spin_components': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'jspins'
            }
        },
        'number_of_symmetries': {
            'parse_type': 'numberNodes',
            'path_spec': {
                'name': 'symOp'
            }
        },
        'number_of_species': {
            'parse_type': 'numberNodes',
            'path_spec': {
                'name': 'species'
            }
        },
        'film': {
            'parse_type': 'exists',
            'path_spec': {
                'name': 'filmPos'
            }
        },
    },
    #--------Defintions for lda+u info from input section (species, ldau tags)--------
    'ldau_info': {
        '_general': True,
        '_modes': [('ldau', True)],
        '_conversions': [Conversion(name='convert_ldau_definitions')],
        'parsed_ldau': {
            'parse_type': 'allAttribs',
            'path_spec': {
                'name': 'ldaU',
                'contains': 'species'
            },
            'subdict': 'ldau_info',
            'flat': False,
            'kwargs': {
                'only_required': True
            }
        },
        'ldau_species': {
            'parse_type': 'parentAttribs',
            'path_spec': {
                'name': 'ldaU',
                'contains': 'species'
            },
            'subdict': 'ldau_info',
            'flat': False,
            'kwargs': {
                'only_required': True
            }
        }
    },
    'ldahia_info': {
        '_general': True,
        '_modes': [('ldahia', True)],
        '_conversions': [Conversion(name='convert_ldahia_definitions')],
        'parsed_ldahia': {
            'parse_type': 'allAttribs',
            'path_spec': {
                'name': 'ldaHIA',
                'contains': 'species'
            },
            'subdict': 'ldahia_info',
            'flat': False,
        },
        'ldahia_species': {
            'parse_type': 'parentAttribs',
            'path_spec': {
                'name': 'ldaHIA',
                'contains': 'species'
            },
            'subdict': 'ldahia_info',
            'flat': False,
            'kwargs': {
                'only_required': True
            }
        }
    },
    #--------Defintions for relaxation info from input section (bravais matrix, atompos)
    #--------for Bulk and film
    'relax_info': {
        '_general': True,
        '_modes': [
            ('relax', True),
        ],
        '_conversions': [Conversion(name='convert_relax_info')],
        'parsed_relax_info': {
            'parse_type': 'xmlGetter',
            'name': 'get_structuredata',
            'kwargs': {
                'convert_to_angstroem': False,
                'include_relaxations': False
            }
        }
    },
    'hubbard1_distances': {
        '_general': True,  #General because not every iteration contains a hubbard1 iteration
        '_minimum_version': '0.35',
        '_minimal': True,
        '_modes': [('ldahia', True)],
        'occupation_distance': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'occupationDistance'
            },
            'kwargs': {
                'iteration_path': True,
                'list_return': True
            },
            'subdict': 'ldahia_info',
        },
        'element_distance': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'elementDistance'
            },
            'kwargs': {
                'iteration_path': True,
                'list_return': True
            },
            'subdict': 'ldahia_info',
        }
    },
    #----General iteration tasks
    # iteration number
    # total energy (only total or also contributions, also lda+u correction)
    # distances (nonmagnetic and magnetic, lda+u density matrix)
    # charges (total, interstitial, mt sphere)
    # fermi energy and bandgap
    # magnetic moments
    # orbital magnetic moments
    # forces
    'iteration_number': {
        '_minimal': True,
        'number_of_iterations_total': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'overallNumber'
            },
            'overwrite_last': True,
        }
    },
    'total_energy': {
        '_minimal':
        True,
        '_conversions': [
            Conversion(name='convert_htr_to_ev', kwargs={
                'name': 'energy_hartree',
                'converted_name': 'energy',
            }),
            Conversion(name='convert_htr_to_ev',
                       kwargs={
                           'name': 'ts_energy_hartree',
                           'converted_name': 'ts_energy',
                           'pop': True
                       })
        ],
        'energy_hartree': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'value',
                'tag_name': 'freeEnergy'
            }
        },
        'energy_hartree_units': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'units',
                'tag_name': 'totalEnergy'
            },
            'overwrite_last': True,
        },
        'ts_energy_hartree': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'value',
                'tag_name': 'tkbtimesentropy'
            }
        }
    },
    'distances': {
        '_minimal': True,
        'density_convergence': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'distance',
                'tag_name': 'chargeDensity'
            }
        },
        'density_convergence_units': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'units',
                'tag_name': 'densityConvergence',
            },
            'overwrite_last': True,
        }
    },
    'magnetic_distances': {
        '_minimal': True,
        '_modes': [('jspin', 2)],
        'overall_density_convergence': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'distance',
                'tag_name': 'overallChargeDensity'
            }
        },
        'spin_density_convergence': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'distance',
                'tag_name': 'spinDensity'
            }
        }
    },
    'total_energy_contributions': {
        'sum_of_eigenvalues': {
            'parse_type': 'singleValue',
            'path_spec': {
                'name': 'sumOfEigenvalues'
            },
            'kwargs': {
                'only_required': True
            }
        },
        'energy_core_electrons': {
            'parse_type': 'singleValue',
            'path_spec': {
                'name': 'coreElectrons',
                'contains': 'sumOfEigenvalues'
            },
            'kwargs': {
                'only_required': True
            }
        },
        'energy_valence_electrons': {
            'parse_type': 'singleValue',
            'path_spec': {
                'name': 'valenceElectrons'
            },
            'kwargs': {
                'only_required': True
            }
        },
        'charge_den_xc_den_integral': {
            'parse_type': 'singleValue',
            'path_spec': {
                'name': 'chargeDenXCDenIntegral'
            },
            'kwargs': {
                'only_required': True
            }
        },
    },
    'ldau_energy_correction': {
        '_modes': [('ldau', True)],
        'ldau_energy_correction': {
            'parse_type': 'singleValue',
            'path_spec': {
                'name': 'dftUCorrection'
            },
            'subdict': 'ldau_info',
            'kwargs': {
                'only_required': True
            }
        },
    },
    'nmmp_distances': {
        '_minimal': True,
        '_modes': [('ldau', True)],
        'density_matrix_distance': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'distance',
                'contains': 'ldaUDensityMatrixConvergence'
            },
            'subdict': 'ldau_info'
        },
    },
    'fermi_energy': {
        'fermi_energy': {
            'parse_type': 'singleValue',
            'path_spec': {
                'name': 'FermiEnergy'
            },
        }
    },
    'bandgap': {
        '_modes': [('bz_integration', 'hist')],
        'bandgap': {
            'parse_type': 'singleValue',
            'path_spec': {
                'name': 'bandgap'
            },
        }
    },
    'magnetic_moments': {
        '_modes': [('jspin', 2)],
        'magnetic_moments': {
            'parse_type': 'allAttribs',
            'path_spec': {
                'name': 'magneticMoment'
            },
            'base_value': 'moment',
            'kwargs': {
                'ignore': ['atomType'],
            }
        }
    },
    'orbital_magnetic_moments': {
        '_modes': [('jspin', 2), ('soc', True)],
        'orbital_magnetic_moments': {
            'parse_type': 'allAttribs',
            'path_spec': {
                'name': 'orbMagMoment'
            },
            'base_value': 'moment',
            'kwargs': {
                'ignore': ['atomType'],
            }
        }
    },
    'global_magnetic_moments': {
        '_minimum_version': '0.35',
        '_modes': [('noco', True)],
        'magnetic_vec_moments': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'vec',
                'contains': 'magnetic',
                'tag_name': 'globalMagMoment'
            }
        }
    },
    'magnetic_moment': {
        '_minimum_version': '0.36',
        '_modes': [('jspin', 2), ('noco', False)],
        'magnetic_vec_moments': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'vec',
                'contains': 'magneticMomentsIn',
                'not_contains': 'local'
            }
        }
    },
    'forces': {
        '_minimal': True,
        '_modes': [('relax', True)],
        '_conversions': [Conversion(name='convert_forces')],
        'force_units': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'units',
                'tag_name': 'totalForcesOnRepresentativeAtoms'
            },
            'overwrite_last': True
        },
        'parsed_forces': {
            'parse_type': 'allAttribs',
            'path_spec': {
                'name': 'forceTotal'
            },
            'flat': False,
            'kwargs': {
                'only_required': True
            }
        }
    },
    'charges': {
        '_conversions': [Conversion(name='calculate_total_magnetic_moment')],
        'spin_dependent_charge': {
            'parse_type': 'allAttribs',
            'path_spec': {
                'name': 'spinDependentCharge',
                'contains': 'allElectronCharges',
                'not_contains': 'fixed'
            },
            'kwargs': {
                'only_required': True
            }
        },
        'total_charge': {
            'parse_type': 'singleValue',
            'path_spec': {
                'name': 'totalCharge',
                'contains': 'allElectronCharges',
                'not_contains': 'fixed'
            },
            'kwargs': {
                'only_required': True
            }
        }
    },
    #-------Tasks for forcetheorem Calculations
    # DMI, JIJ, MAE, SSDISP
    'forcetheorem_dmi': {
        '_special': True,
        'dmi_force': {
            'parse_type': 'allAttribs',
            'path_spec': {
                'name': 'Entry',
                'contains': 'DMI'
            }
        },
        'dmi_force_so': {
            'parse_type': 'allAttribs',
            'path_spec': {
                'name': 'allAtoms',
                'contains': 'DMI'
            }
        },
        'dmi_force_qs': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'qpoints',
                'contains': 'Forcetheorem_DMI'
            }
        },
        'dmi_force_angles': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'Angles',
                'contains': 'Forcetheorem_DMI'
            }
        },
        'dmi_force_units': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'units',
                'contains': 'Forcetheorem_DMI'
            }
        }
    },
    'forcetheorem_ssdisp': {
        '_special': True,
        'spst_force': {
            'parse_type': 'allAttribs',
            'path_spec': {
                'name': 'Entry',
                'contains': 'SSDISP'
            }
        },
        'spst_force_qs': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'qvectors',
                'contains': 'Forcetheorem_SSDISP'
            }
        },
        'spst_force_units': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'units',
                'contains': 'Forcetheorem_SSDISP'
            }
        }
    },
    'forcetheorem_mae': {
        '_special': True,
        'mae_force': {
            'parse_type': 'allAttribs',
            'path_spec': {
                'name': 'Angle',
                'contains': 'MAE'
            }
        },
        'mae_force_units': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'units',
                'contains': 'Forcetheorem_MAE'
            }
        }
    },
    'forcetheorem_jij': {
        '_special': True,
        'jij_force': {
            'parse_type': 'allAttribs',
            'path_spec': {
                'name': 'Config',
                'contains': 'JIJ'
            }
        },
        'jij_force_units': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'units',
                'contains': 'Forcetheorem_JIJ'
            }
        }
    },
    'torques': {
        '_minimum_version': '0.35',  #Typo torgue/torque before
        '_optional': True,
        'torque_x': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'sigma_x',
                'contains': 'noncollinearTorque'
            }
        },
        'torque_y': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'sigma_y',
                'contains': 'noncollinearTorque'
            }
        }
    },
    'noco_angles': {
        '_general': True,
        '_optional': True,
        'noco_alpha': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'alpha',
                'tag_name': 'nocoParams',
                'contains': 'Group'
            }
        },
        'noco_beta': {
            'parse_type': 'attrib',
            'path_spec': {
                'name': 'beta',
                'tag_name': 'nocoParams',
                'contains': 'Group'
            }
        }
    },
    'corelevels': {
        '_optional': True,
        'corestates': {
            'parse_type': 'allAttribs',
            'path_spec': {
                'name': 'coreStates'
            },
            'kwargs': {
                'subtags': True,
            },
            'flat': False
        }
    }
}
