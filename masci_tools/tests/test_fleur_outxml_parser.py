# -*- coding: utf-8 -*-
"""
Tests of the out.xml parser for Fleur
"""
import pytest
from masci_tools.io.parsers.fleur import outxml_parser
import os
import math
from pprint import pprint

# Collect the input files
file_path = 'files/fleur/Max-R5'

outxmlfilefolder = os.path.dirname(os.path.abspath(__file__))
outxmlfilefolder_valid = [os.path.abspath(os.path.join(outxmlfilefolder, file_path))]

outxmlfilelist = []
for folder in outxmlfilefolder_valid:
    for subdir, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.xml') and 'out' in file:
                outxmlfilelist.append(os.path.join(subdir, file))


@pytest.mark.parametrize('outxmlfilepath', outxmlfilelist)
def test_outxml_valid_outxml(outxmlfilepath):
    """
    test if valid inp.xml files are recognized by the inpxml_parser
    """
    from lxml import etree

    #Pass outxmlfile
    out_dict = outxml_parser(outxmlfilepath)

    assert out_dict is not None
    assert isinstance(out_dict, dict)
    assert out_dict != {}

    #Parse before
    parser = etree.XMLParser(attribute_defaults=True, encoding='utf-8')
    xmltree = etree.parse(outxmlfilepath, parser)
    out_dict = outxml_parser(xmltree, strict=True)

    assert out_dict is not None
    assert isinstance(out_dict, dict)
    assert out_dict != {}

    #call with contextmanager
    with open(outxmlfilepath, 'r') as outfile:
        out_dict = outxml_parser(outfile, strict=True)

    assert out_dict is not None
    assert isinstance(out_dict, dict)
    assert out_dict != {}


def test_outxml_validation_errors(data_regression):
    """
    Test the output parser against files for detecting validation
    """

    OUTXML_FILEPATH1 = os.path.join(outxmlfilefolder, 'files/fleur/broken_out_xml/simple_validation_error.xml')

    with pytest.raises(ValueError, match='Output file does not validate against the schema:'):
        out_dict = outxml_parser(OUTXML_FILEPATH1, strict=True)

    result_warnings = {'parser_warnings': []}
    out_dict = outxml_parser(OUTXML_FILEPATH1, strict=True, ignore_validation=True, parser_info_out=result_warnings)

    data_regression.check({'output_dict': out_dict, 'warnings': result_warnings})


def test_outxml_empty_out(data_regression):
    """
    Test the output parser against empty file
    """

    OUTXML_FILEPATH = os.path.join(outxmlfilefolder, 'files/fleur/broken_out_xml/empty_out.xml')

    result_warnings = {'parser_warnings': []}
    out_dict = outxml_parser(OUTXML_FILEPATH, strict=True, parser_info_out=result_warnings)

    data_regression.check({'output_dict': out_dict, 'warnings': result_warnings})


def test_outxml_broken(data_regression):
    """
    Test the output parser against a file which terminates after some iterations
    """

    OUTXML_FILEPATH = os.path.join(outxmlfilefolder, 'files/fleur/broken_out_xml/terminated.xml')

    result_warnings = {'parser_warnings': []}
    out_dict = outxml_parser(OUTXML_FILEPATH, strict=True, parser_info_out=result_warnings)

    data_regression.check({
        'output_dict': out_dict,
        'warnings': result_warnings,
    })


def test_outxml_broken_firstiter(data_regression):
    """
    Test the output parser against a file which terminates in the first iteration
    """
    OUTXML_FILEPATH = os.path.join(outxmlfilefolder, 'files/fleur/broken_out_xml/terminated_firstit.xml')
    result_warnings = {'parser_warnings': []}
    out_dict = outxml_parser(OUTXML_FILEPATH, strict=True, parser_info_out=result_warnings)

    data_regression.check({
        'output_dict': out_dict,
        'warnings': result_warnings,
    })


def test_outxml_garbage_values(data_regression):
    """
    Test the behaviour of the ouput parser when encountering NaN, Inf or fortran formatting errors ****
    """
    OUTXML_FILEPATH = os.path.join(outxmlfilefolder, 'files/fleur/broken_out_xml/garbage_values.xml')

    def isNaN(num):
        return math.isnan(num)  #num != num

    result_warnings = {'parser_warnings': []}
    out_dict = outxml_parser(OUTXML_FILEPATH, strict=True, ignore_validation=True, parser_info_out=result_warnings)

    assert isNaN(out_dict['fermi_energy'])
    assert out_dict['magnetic_moments'] == '********'
    assert out_dict['total_charge'] == float('Inf')

    data_regression.check({'warnings': result_warnings})


def test_outxml_incompatible_versions():
    """
    Test the output parser against files with broken/wrong or unsupported version strings
    """

    #output version does not exist (InputSchema is loaded first so this is the raised error)
    OUTXML_FILEPATH1 = os.path.join(outxmlfilefolder, 'files/fleur/broken_out_xml/non_existing_version.xml')
    with pytest.raises(FileNotFoundError, match='No FleurInputSchema.xsd found'):
        out_dict = outxml_parser(OUTXML_FILEPATH1, strict=True)

    #version string 0.27 and programVersion='fleur 27' not supported
    OUTXML_FILEPATH1 = os.path.join(outxmlfilefolder, 'files/fleur/broken_out_xml/non_supported_version.xml')
    with pytest.raises(ValueError, match='Versions before fleur MaX4.0 are not supported'):
        out_dict = outxml_parser(OUTXML_FILEPATH1, strict=True)


def test_outxml_additional_tasks_simple(data_regression):
    """
    Test the definition of additional tasks (resding an attribute)
    """
    OUTXML_FILEPATH = os.path.join(outxmlfilefolder_valid[0], 'SiLOXML/files/out.xml')

    TEST_TASK_ITERATION = {
        'core_states': {
            'core_eig_val_sum': {
                'parse_type': 'attrib',
                'path_spec': {
                    'name': 'eigValSum'
                }
            }
        }
    }

    out_dict = outxml_parser(OUTXML_FILEPATH, additional_tasks=TEST_TASK_ITERATION)

    data_regression.check({
        'output_dict': out_dict,
    })

    TEST_TASK_ITERATION_INVALID = {
        'core_states': {
            'core_eig_val_sum': {
                'parse_type': 'attrib',
                'path_spec': {
                    'name': 'eigValSum'
                },
                'ignore': ['eigValSum']
            }
        }
    }
    with pytest.raises(ValueError, match="Got extra Keys: {'ignore'}"):
        out_dict = outxml_parser(OUTXML_FILEPATH, additional_tasks=TEST_TASK_ITERATION_INVALID)


def test_outxml_additional_tasks_allattribs(data_regression):
    """
    Test the definition of additional tasks (reading an all attributes of a tag)
    """
    OUTXML_FILEPATH = os.path.join(outxmlfilefolder_valid[0], 'SiLOXML/files/out.xml')

    TEST_TASK_ITERATION_ALLATTRIBS = {
        'core_states': {
            'core_info': {
                'parse_type': 'allAttribs',
                'path_spec': {
                    'name': 'coreStates'
                },
                'subdict': 'core_info'
            }
        }
    }
    out_dict = outxml_parser(OUTXML_FILEPATH, additional_tasks=TEST_TASK_ITERATION_ALLATTRIBS)
    data_regression.check({
        'output_dict': out_dict,
    })

    TEST_TASK_ITERATION_ALLATTRIBS_INVALID = {
        'core_states': {
            'core_info': {
                'parse_type': 'allAttribs',
                'path_spec': {
                    'name': 'coreStates'
                },
                'overwrite_last': True
            }
        }
    }
    with pytest.raises(ValueError, match="Got extra Keys: {'overwrite_last'}"):
        out_dict = outxml_parser(OUTXML_FILEPATH, additional_tasks=TEST_TASK_ITERATION_ALLATTRIBS_INVALID)


def test_outxml_add_tasks_overwrite(data_regression):
    """
    Test the overwriting of tasks
    """

    OUTXML_FILEPATH = os.path.join(outxmlfilefolder_valid[0], 'SiLOXML/files/out.xml')

    REPLACE_BANDGAP = {
        'bandgap': {
            'bandgap': {
                'parse_type': 'singleValue',
                'path_spec': {
                    'name': 'freeEnergy'
                },
                'only_required': True
            }
        }
    }

    with pytest.raises(ValueError, match="Task 'bandgap' is already defined."):
        out_dict = outxml_parser(OUTXML_FILEPATH, additional_tasks=REPLACE_BANDGAP)

    out_dict = outxml_parser(OUTXML_FILEPATH, additional_tasks=REPLACE_BANDGAP, overwrite=True)
    data_regression.check({
        'output_dict': out_dict,
    })


def test_outxml_add_tasks_append(data_regression):
    """
    Test the append option for defining additional tasks
    """

    OUTXML_FILEPATH = os.path.join(outxmlfilefolder_valid[0], 'SiLOXML/files/out.xml')

    #Move the number_of_atom_types from general_out_info to general_inp_info
    #and write the comment from the inp.xml into it
    #This tests both the correct insertin in general_inp_info and that inner keys can be
    #overwritten in general_out_info

    REPLACE_DICT = {
        'general_out_info': {
            'number_of_atom_types': {}
        },
        'general_inp_info': {
            'number_of_atom_types': {
                'parse_type': 'text',
                'path_spec': {
                    'name': 'comment'
                }
            }
        }
    }

    with pytest.raises(ValueError, match="Task 'general_out_info' is already defined."):
        out_dict = outxml_parser(OUTXML_FILEPATH, additional_tasks=REPLACE_DICT)

    out_dict = outxml_parser(OUTXML_FILEPATH, additional_tasks=REPLACE_DICT, append=True)
    data_regression.check({
        'output_dict': out_dict,
    })


def test_outxml_max4compatibility(data_regression):
    """
    Test if Max4 output files are processed correctly
    """

    OUTXML_FILEPATH = os.path.abspath(os.path.join(outxmlfilefolder, 'files/fleur/Max-R4/Max4_test_out.xml'))

    warnings = {'parser_warnings': []}
    out_dict = outxml_parser(OUTXML_FILEPATH, parser_info_out=warnings, iteration_to_parse='all')
    data_regression.check({
        'output_dict': out_dict,
        'warnings': warnings,
    })


def test_outxml_max5_0_compatibility(data_regression):
    """
    Test if Max5.0 output files are processed correctly
    """

    OUTXML_FILEPATH = os.path.abspath(os.path.join(outxmlfilefolder, 'files/fleur/Max-R5/Max5_0_test_out.xml'))

    warnings = {'parser_warnings': []}
    out_dict = outxml_parser(OUTXML_FILEPATH, parser_info_out=warnings, iteration_to_parse='all')
    data_regression.check({
        'output_dict': out_dict,
        'warnings': warnings,
    })


def test_outxml_differing_versions(data_regression):
    """
    Test if files with different input/output versions are parsed correctly
    """
    OUTXML_FILEPATH = os.path.abspath(os.path.join(outxmlfilefolder, 'files/fleur/output_mixed_versions.xml'))

    warnings = {'parser_warnings': []}
    out_dict = outxml_parser(OUTXML_FILEPATH, parser_info_out=warnings)

    data_regression.check({
        'output_dict': out_dict,
        'warnings': warnings,
    })


def test_outxml_newer_version(data_regression):
    """
    Test if files with not yet existent versions are parsed correctly (fallback to last available)
    """
    OUTXML_FILEPATH = os.path.abspath(os.path.join(outxmlfilefolder, 'files/fleur/output_newer_version.xml'))

    warnings = {'parser_warnings': []}
    out_dict = outxml_parser(OUTXML_FILEPATH, parser_info_out=warnings)

    data_regression.check({
        'output_dict': out_dict,
        'warnings': warnings,
    })


def test_outxml_lastiter(data_regression):
    """
    Test the parsing of only the last iteration
    """

    OUTXML_FILEPATH = os.path.join(outxmlfilefolder_valid[0], 'SiLOXML/files/out.xml')

    out_dict = outxml_parser(OUTXML_FILEPATH, strict=True)
    data_regression.check({
        'output_dict': out_dict,
    })


def test_outxml_firstiter(data_regression):
    """
    Test the parsing of only the first iteration
    """

    OUTXML_FILEPATH = os.path.join(outxmlfilefolder_valid[0], 'SiLOXML/files/out.xml')

    out_dict = outxml_parser(OUTXML_FILEPATH, iteration_to_parse='first', strict=True)
    data_regression.check({
        'output_dict': out_dict,
    })


def test_outxml_alliter(data_regression):
    """
    Test the parsing of all available iterations
    """

    OUTXML_FILEPATH = os.path.join(outxmlfilefolder_valid[0], 'SiLOXML/files/out.xml')

    out_dict = outxml_parser(OUTXML_FILEPATH, iteration_to_parse='all', strict=True)
    data_regression.check({
        'output_dict': out_dict,
    })


def test_outxml_indexiter(data_regression):
    """
    Test the parsing of an iteration specified by index
    """

    OUTXML_FILEPATH = os.path.join(outxmlfilefolder_valid[0], 'SiLOXML/files/out.xml')

    out_dict = outxml_parser(OUTXML_FILEPATH, iteration_to_parse=3, strict=True)
    data_regression.check({
        'output_dict': out_dict,
    })


def test_outxml_minimal_mode(data_regression):
    """
    Test the minimal mode of the outxml_parser
    """

    OUTXML_FILEPATH = os.path.join(outxmlfilefolder_valid[0], 'SiLOXML/files/out.xml')

    out_dict = outxml_parser(OUTXML_FILEPATH, iteration_to_parse='all', minimal_mode=True, strict=True)
    data_regression.check({
        'output_dict': out_dict,
    })


def test_outxml_magnetic(data_regression):
    """
    Test the outxml_parser for magnetic calculations
    """

    OUTXML_FILEPATH = os.path.join(outxmlfilefolder_valid[0], 'Fe_bct_LOXML/files/out.xml')

    out_dict = outxml_parser(OUTXML_FILEPATH, iteration_to_parse='all', strict=True)
    data_regression.check({})


def test_outxml_ldaurelax(data_regression):
    """
    Test the outxml_parser for LDA+U and forces
    """

    OUTXML_FILEPATH = os.path.join(outxmlfilefolder_valid[0], 'GaAsMultiUForceXML/files/out.xml')

    out_dict = outxml_parser(OUTXML_FILEPATH, iteration_to_parse='all', strict=True)
    data_regression.check({
        'output_dict': out_dict,
    })


def test_outxml_force(data_regression):
    """
    Test the outxml_parser for a forcetheorem calculation
    """

    OUTXML_FILEPATH = os.path.join(outxmlfilefolder_valid[0], 'FePt_film_SSFT_LO/files/out.xml')

    out_dict = outxml_parser(OUTXML_FILEPATH, iteration_to_parse='all', strict=True)

    data_regression.check({
        'output_dict': out_dict,
    })
