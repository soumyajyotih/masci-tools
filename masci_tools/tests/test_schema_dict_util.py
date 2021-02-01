# -*- coding: utf-8 -*-
"""
Test of the utility functions for the schema dictionaries
both path finding and easy information extraction
"""
import pytest
import os
import copy
import numpy as np
from masci_tools.io.parsers.fleur.fleur_schema import load_inpschema, load_outschema
from masci_tools.util.constants import FLEUR_DEFINED_CONSTANTS
from pprint import pprint

#Load different schema versions (for now only input schemas)
schema_dict_34 = load_inpschema('0.34')
schema_dict_27 = load_inpschema('0.27')
schema_dict_31 = load_inpschema('0.31')
outschema_dict_34 = load_outschema('0.34')
outschema_dict_31 = load_outschema('0.31')

INPUT_TAG_34 = outschema_dict_34['tag_paths'][outschema_dict_34['input_tag']]

FILE_PATH = os.path.dirname(os.path.abspath(__file__))
TEST_INPXML_PATH = os.path.join(FILE_PATH, 'files/fleur/Max-R5/FePt_film_SSFT_LO/files/inp2.xml')
TEST_OUTXML_PATH = os.path.join(FILE_PATH, 'files/fleur/Max-R5/GaAsMultiUForceXML/files/out.xml')
TEST_OUTXML_PATH2 = os.path.join(FILE_PATH, 'files/fleur/Max-R5/FePt_film_SSFT_LO/files/out.xml')


def test_get_tag_xpath_input():
    """
    Test the path finding for tags for the input schema without additional options
    And verify with different version of the schema
    """
    from masci_tools.util.schema_dict_util import get_tag_xpath

    #First example easy (magnetism tag is unique and should not differ between the versions)
    assert get_tag_xpath(schema_dict_27, 'magnetism') == '/fleurInput/calculationSetup/magnetism'
    assert get_tag_xpath(schema_dict_34, 'magnetism') == '/fleurInput/calculationSetup/magnetism'

    #Differing paths between the version
    assert get_tag_xpath(schema_dict_27, 'bzIntegration') == '/fleurInput/calculationSetup/bzIntegration'
    assert get_tag_xpath(schema_dict_34, 'bzIntegration') == '/fleurInput/cell/bzIntegration'

    #Non existent tag in old version
    assert get_tag_xpath(schema_dict_34, 'DMI') == '/fleurInput/forceTheorem/DMI'
    with pytest.raises(ValueError, match='The tag DMI has no possible paths with the current specification.'):
        get_tag_xpath(schema_dict_27, 'DMI')

    #Multiple possible paths
    with pytest.raises(ValueError, match='The tag ldaU has multiple possible paths with the current specification.'):
        get_tag_xpath(schema_dict_27, 'ldaU')
    with pytest.raises(ValueError, match='The tag ldaU has multiple possible paths with the current specification.'):
        get_tag_xpath(schema_dict_34, 'ldaU')


def test_get_tag_xpath_output():
    """
    Test the path finding for tags for the output schema without additional options
    And verify with different version of the schema
    """
    from masci_tools.util.schema_dict_util import get_tag_xpath

    #absolute
    assert get_tag_xpath(outschema_dict_34, 'iteration') == '/fleurOutput/scfLoop/iteration'
    assert get_tag_xpath(outschema_dict_31, 'iteration') == '/fleurOutput/scfLoop/iteration'

    #relative paths
    assert get_tag_xpath(outschema_dict_34, 'totalEnergy') == './totalEnergy'
    assert get_tag_xpath(outschema_dict_31, 'totalEnergy') == './totalEnergy'

    #Non existent tag
    assert get_tag_xpath(outschema_dict_34, 'fleurInput') == '/fleurOutput/fleurInput'
    with pytest.raises(ValueError, match='The tag fleurInput has no possible paths with the current specification.'):
        get_tag_xpath(outschema_dict_31, 'fleurInput')

    assert get_tag_xpath(outschema_dict_31, 'inputData') == '/fleurOutput/inputData'
    with pytest.raises(ValueError, match='The tag inputData has no possible paths with the current specification.'):
        get_tag_xpath(outschema_dict_34, 'inputData')

    #Multiple possible paths
    with pytest.raises(ValueError,
                       match='The tag spinDependentCharge has multiple possible paths with the current specification.'):
        get_tag_xpath(outschema_dict_31, 'spinDependentCharge')
    with pytest.raises(ValueError,
                       match='The tag spinDependentCharge has multiple possible paths with the current specification.'):
        get_tag_xpath(outschema_dict_34, 'spinDependentCharge')


def test_get_tag_xpath_contains():
    """
    Test the selection of paths based on a contained keyword
    """
    from masci_tools.util.schema_dict_util import get_tag_xpath

    schema_dict = copy.deepcopy(schema_dict_34)

    with pytest.raises(ValueError, match='The tag ldaU has multiple possible paths with the current specification.'):
        get_tag_xpath(schema_dict, 'ldaU')
    with pytest.raises(ValueError, match='The tag ldaU has multiple possible paths with the current specification.'):
        get_tag_xpath(schema_dict, 'ldaU', contains='atom')

    assert get_tag_xpath(schema_dict, 'ldaU', contains='calculationSetup') == '/fleurInput/calculationSetup/ldaU'
    assert get_tag_xpath(schema_dict, 'ldaU', contains='species') == '/fleurInput/atomSpecies/species/ldaU'
    assert get_tag_xpath(schema_dict, 'ldaU', contains='Group') == '/fleurInput/atomGroups/atomGroup/ldaU'

    with pytest.raises(ValueError, match='The tag ldaU has no possible paths with the current specification.'):
        get_tag_xpath(schema_dict, 'ldaU', contains='group')

    #Make sure that this did not modify the schema dict
    assert schema_dict == schema_dict_34


def test_get_tag_xpath_notcontains():
    """
    Test the selection of paths based on a not contained keyword
    """
    from masci_tools.util.schema_dict_util import get_tag_xpath

    schema_dict = copy.deepcopy(schema_dict_34)

    with pytest.raises(ValueError, match='The tag ldaU has multiple possible paths with the current specification.'):
        get_tag_xpath(schema_dict, 'ldaU')
    with pytest.raises(ValueError, match='The tag ldaU has multiple possible paths with the current specification.'):
        path = get_tag_xpath(schema_dict, 'ldaU', not_contains='calculationSetup')

    assert get_tag_xpath(schema_dict, 'ldaU', not_contains='atom') == '/fleurInput/calculationSetup/ldaU'
    with pytest.raises(ValueError, match='The tag ldaU has multiple possible paths with the current specification.'):
        assert get_tag_xpath(schema_dict, 'ldaU', not_contains='Group') == '/fleurInput/atomSpecies/species/ldaU'

    assert get_tag_xpath(schema_dict, 'ldaU', contains='atom',
                         not_contains='species') == '/fleurInput/atomGroups/atomGroup/ldaU'

    #Make sure that this did not modify the schema dict
    assert schema_dict == schema_dict_34


def test_get_attrib_xpath_input():
    """
    Test the path finding for tags for the input schema without additional options
    And verify with different version of the schema
    """
    from masci_tools.util.schema_dict_util import get_attrib_xpath

    #First example easy (magnetism tag is unique and should not differ between the versions)
    assert get_attrib_xpath(schema_dict_27, 'jspins') == '/fleurInput/calculationSetup/magnetism/@jspins'
    assert get_attrib_xpath(schema_dict_34, 'jspins') == '/fleurInput/calculationSetup/magnetism/@jspins'

    #Differing paths between the version
    assert get_attrib_xpath(schema_dict_27, 'mode') == '/fleurInput/calculationSetup/bzIntegration/@mode'
    assert get_attrib_xpath(schema_dict_34, 'mode') == '/fleurInput/cell/bzIntegration/@mode'

    #Non existent tag in old version
    assert get_attrib_xpath(schema_dict_34,
                            'l_mtNocoPot') == '/fleurInput/calculationSetup/magnetism/mtNocoParams/@l_mtNocoPot'
    with pytest.raises(ValueError,
                       match='The attrib l_mtNocoPot has no possible paths with the current specification.'):
        get_attrib_xpath(schema_dict_27, 'l_mtNocoPot')

    #Multiple possible paths
    with pytest.raises(ValueError,
                       match='The attrib l_amf has multiple possible paths with the current specification.'):
        get_attrib_xpath(schema_dict_27, 'l_amf')
    with pytest.raises(ValueError,
                       match='The attrib l_amf has multiple possible paths with the current specification.'):
        get_attrib_xpath(schema_dict_34, 'l_amf')


def test_get_attrib_xpath_output():
    """
    Test the path finding for tags for the input schema without additional options
    And verify with different version of the schema
    """
    from masci_tools.util.schema_dict_util import get_attrib_xpath

    #absolute
    assert get_attrib_xpath(outschema_dict_31, 'nat') == '/fleurOutput/numericalParameters/atomsInCell/@nat'
    assert get_attrib_xpath(outschema_dict_34, 'nat') == '/fleurOutput/numericalParameters/atomsInCell/@nat'

    #relative
    assert get_attrib_xpath(outschema_dict_31, 'qvectors') == './Forcetheorem_SSDISP/@qvectors'
    assert get_attrib_xpath(outschema_dict_34, 'qvectors') == './Forcetheorem_SSDISP/@qvectors'


def test_get_attrib_xpath_contains():
    """
    Test the selection of paths based on a contained keyword
    """
    from masci_tools.util.schema_dict_util import get_attrib_xpath

    schema_dict = copy.deepcopy(schema_dict_34)

    with pytest.raises(ValueError,
                       match='The attrib l_mperp has multiple possible paths with the current specification.'):
        get_attrib_xpath(schema_dict, 'l_mperp')

    assert get_attrib_xpath(schema_dict, 'l_mperp',
                            contains='magnetism') == '/fleurInput/calculationSetup/magnetism/mtNocoParams/@l_mperp'
    assert get_attrib_xpath(schema_dict, 'l_mperp',
                            contains='greensFunction') == '/fleurInput/calculationSetup/greensFunction/@l_mperp'

    with pytest.raises(ValueError, match='The attrib l_mperp has no possible paths with the current specification.'):
        get_attrib_xpath(schema_dict, 'l_mperp', contains='atom')

    #Make sure that this did not modify the schema dict
    assert schema_dict == schema_dict_34


def test_get_attrib_xpath_notcontains():
    """
    Test the selection of paths based on a contained keyword
    """
    from masci_tools.util.schema_dict_util import get_attrib_xpath

    schema_dict = copy.deepcopy(schema_dict_34)

    with pytest.raises(ValueError,
                       match='The attrib l_mperp has multiple possible paths with the current specification.'):
        get_attrib_xpath(schema_dict, 'l_mperp')

    assert get_attrib_xpath(
        schema_dict, 'l_mperp',
        not_contains='greensFunction') == '/fleurInput/calculationSetup/magnetism/mtNocoParams/@l_mperp'
    assert get_attrib_xpath(schema_dict, 'l_mperp',
                            not_contains='magnetism') == '/fleurInput/calculationSetup/greensFunction/@l_mperp'

    assert get_attrib_xpath(schema_dict, 'l_mperp', contains='greensFunction',
                            not_contains='magnetism') == '/fleurInput/calculationSetup/greensFunction/@l_mperp'

    with pytest.raises(ValueError, match='The attrib l_mperp has no possible paths with the current specification.'):
        get_attrib_xpath(schema_dict, 'l_mperp', not_contains='calculationSetup')

    #Make sure that this did not modify the schema dict
    assert schema_dict == schema_dict_34


def test_get_attrib_xpath_exclude():
    """
    Test the selection of paths based on a contained keyword
    """
    from masci_tools.util.schema_dict_util import get_attrib_xpath

    schema_dict = copy.deepcopy(schema_dict_34)

    assert get_attrib_xpath(schema_dict, 'alpha') == '/fleurInput/calculationSetup/scfLoop/@alpha'
    assert get_attrib_xpath(schema_dict, 'alpha', exclude=['unique_path',
                                                           'other']) == '/fleurInput/calculationSetup/scfLoop/@alpha'
    with pytest.raises(ValueError,
                       match='The attrib alpha has multiple possible paths with the current specification.'):
        get_attrib_xpath(schema_dict, 'alpha', exclude=['unique'])

    assert get_attrib_xpath(schema_dict, 'alpha', not_contains='atom',
                            exclude=['unique'
                                     ]) == '/fleurInput/calculationSetup/greensFunction/contourSemicircle/@alpha'

    #Make sure that this did not modify the schema dict
    assert schema_dict == schema_dict_34


def test_get_attrib_xpath_exclude_output():
    """
    Test the selection of paths based on a contained keyword
    """
    from masci_tools.util.schema_dict_util import get_attrib_xpath

    schema_dict = copy.deepcopy(outschema_dict_34)

    with pytest.raises(ValueError,
                       match='The attrib units has multiple possible paths with the current specification.'):
        get_attrib_xpath(schema_dict, 'units')

    assert get_attrib_xpath(schema_dict, 'units', contains='DMI') == './Forcetheorem_DMI/@units'
    assert get_attrib_xpath(schema_dict, 'units', exclude=['other'], contains='DMI') == './Forcetheorem_DMI/@units'

    with pytest.raises(ValueError, match='The attrib units has no possible paths with the current specification.'):
        get_attrib_xpath(schema_dict, 'units', exclude=['unique_path'], contains='DMI')

    #Make sure that this did not modify the schema dict
    assert schema_dict == outschema_dict_34


def test_read_contants():
    """
    Test of the read_constants function
    """
    from lxml import etree
    from masci_tools.util.schema_dict_util import read_constants

    schema_dict = copy.deepcopy(schema_dict_34)

    VALID_INP_CONSTANTS_PATH = os.path.join(FILE_PATH, 'files/fleur/inp_with_constants.xml')
    INVALID_INP_CONSTANTS_PATH = os.path.join(FILE_PATH, 'files/fleur/inp_invalid_constants.xml')
    VALID_OUT_CONSTANTS_PATH = os.path.join(FILE_PATH, 'files/fleur/out_with_constants.xml')

    parser = etree.XMLParser(attribute_defaults=True, recover=False, encoding='utf-8')
    xmltree = etree.parse(VALID_INP_CONSTANTS_PATH, parser)
    outxmltree = etree.parse(VALID_OUT_CONSTANTS_PATH, parser)
    invalidxmltree = etree.parse(INVALID_INP_CONSTANTS_PATH, parser)

    root1 = xmltree.getroot()
    root2 = outxmltree.getroot()
    root3 = invalidxmltree.getroot()

    expected_constants = {
        'A': -3.14,
        'Ang': 1.889726124772898,
        'Bohr': 1.0,
        'Deg': 0.017453292519943295,
        'Pi': 3.141592653589793,
        'nm': 18.89726124772898,
        'notPi': 3.0,
        'pm': 0.01889726124772898
    }
    result = read_constants(root1, schema_dict)
    assert result == expected_constants

    result = read_constants(root2, schema_dict, replace_root=INPUT_TAG_34)
    assert result == expected_constants

    with pytest.raises(KeyError, match='Ambiguous definition of key Pi'):
        result = read_constants(root3, schema_dict)

    assert schema_dict == schema_dict_34


def test_evaluate_attribute():
    """
    Test of the evaluate_attribute function
    """
    from lxml import etree
    from masci_tools.util.schema_dict_util import evaluate_attribute

    schema_dict = copy.deepcopy(schema_dict_34)

    parser = etree.XMLParser(attribute_defaults=True, recover=False, encoding='utf-8')
    xmltree = etree.parse(TEST_INPXML_PATH, parser)
    outxmltree = etree.parse(TEST_OUTXML_PATH2, parser)

    outroot = outxmltree.getroot()
    root = xmltree.getroot()

    assert evaluate_attribute(root, schema_dict, 'jspins', FLEUR_DEFINED_CONSTANTS) == 2
    assert evaluate_attribute(root, schema_dict, 'l_noco', FLEUR_DEFINED_CONSTANTS)
    assert evaluate_attribute(root, schema_dict, 'mode', FLEUR_DEFINED_CONSTANTS) == 'hist'
    assert pytest.approx(evaluate_attribute(root, schema_dict, 'radius', FLEUR_DEFINED_CONSTANTS,
                                            contains='species')) == [2.2, 2.2]

    with pytest.raises(ValueError, match='The attrib beta has multiple possible paths with the current specification.'):
        evaluate_attribute(root, schema_dict, 'beta', FLEUR_DEFINED_CONSTANTS, exclude=['unique'])

    assert pytest.approx(
        evaluate_attribute(root,
                           schema_dict,
                           'beta',
                           FLEUR_DEFINED_CONSTANTS,
                           exclude=['unique'],
                           contains='nocoParams',
                           not_contains='species')) == [np.pi / 2.0, np.pi / 2.0]

    assert pytest.approx(
        evaluate_attribute(root,
                           schema_dict,
                           'beta',
                           FLEUR_DEFINED_CONSTANTS,
                           tag_name='nocoParams',
                           not_contains='species')) == [np.pi / 2.0, np.pi / 2.0]

    with pytest.raises(ValueError, match='No attribute TEST found at tag nocoParams'):
        evaluate_attribute(
            root,
            schema_dict,
            'TEST',
            FLEUR_DEFINED_CONSTANTS,
            tag_name='nocoParams',
            not_contains='species',
        )

    assert pytest.approx(
        evaluate_attribute(outroot,
                           schema_dict,
                           'beta',
                           FLEUR_DEFINED_CONSTANTS,
                           exclude=['unique'],
                           contains='nocoParams',
                           not_contains='species',
                           replace_root=INPUT_TAG_34)) == [np.pi / 2.0, np.pi / 2.0]

    iteration = outroot.xpath('//iteration')[0]

    assert evaluate_attribute(iteration,
                              outschema_dict_34,
                              'units',
                              FLEUR_DEFINED_CONSTANTS,
                              tag_name='Forcetheorem_SSDISP') == 'Htr'

    with pytest.raises(ValueError, match='No attribute TEST found at tag Forcetheorem_SSDISP'):
        evaluate_attribute(iteration,
                           outschema_dict_34,
                           'TEST',
                           FLEUR_DEFINED_CONSTANTS,
                           tag_name='Forcetheorem_SSDISP')

    with pytest.raises(ValueError,
                       match='The attrib spinf has multiple possible paths with the current specification.'):
        evaluate_attribute(root, schema_dict, 'spinf', FLEUR_DEFINED_CONSTANTS)

    expected_info = {'parser_warnings': ['No values found for attribute radius']}

    parser_info_out = {'parser_warnings': []}
    assert evaluate_attribute(
        root, schema_dict, 'radius', FLEUR_DEFINED_CONSTANTS, not_contains='species',
        parser_info_out=parser_info_out) is None
    assert parser_info_out == expected_info
    assert schema_dict == schema_dict_34


def test_evaluate_text():
    """
    Test of the evaluate_text function
    """
    from lxml import etree
    from masci_tools.util.schema_dict_util import evaluate_text

    schema_dict = copy.deepcopy(schema_dict_34)

    parser = etree.XMLParser(attribute_defaults=True, recover=False, encoding='utf-8')
    xmltree = etree.parse(TEST_INPXML_PATH, parser)
    outxmltree = etree.parse(TEST_OUTXML_PATH2, parser)

    outroot = outxmltree.getroot()
    root = xmltree.getroot()

    assert pytest.approx(evaluate_text(root, schema_dict, 'qss', FLEUR_DEFINED_CONSTANTS)) == [0.0, 0.0, 0.0]
    kpoints = evaluate_text(root, schema_dict, 'kPoint', FLEUR_DEFINED_CONSTANTS)
    expected = [[-0.25, 0.25, 0.0], [0.25, 0.25, 0.0]]
    for val, result in zip(kpoints, expected):
        assert pytest.approx(val) == result

    positions = evaluate_text(root, schema_dict, 'filmPos', FLEUR_DEFINED_CONSTANTS)
    positions_out = evaluate_text(outroot, schema_dict, 'filmPos', FLEUR_DEFINED_CONSTANTS, replace_root=INPUT_TAG_34)

    expected = [[0.0, 0.0, -0.9964250044], [0.5, 0.5, 0.9964250044]]
    for val, result in zip(positions, expected):
        assert pytest.approx(val) == result
    for val, result in zip(positions_out, expected):
        assert pytest.approx(val) == result

    with pytest.raises(ValueError, match='The tag row-1 has multiple possible paths with the current specification.'):
        evaluate_text(root, schema_dict, 'row-1', FLEUR_DEFINED_CONSTANTS)
    #Test the correct passing of contains parameters

    sym_row1 = evaluate_text(root, schema_dict, 'row-1', FLEUR_DEFINED_CONSTANTS, contains='symOp')
    expected = [[1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]]
    for val, result in zip(sym_row1, expected):
        assert pytest.approx(val) == result
    assert pytest.approx(
        evaluate_text(root,
                      schema_dict,
                      'row-1',
                      FLEUR_DEFINED_CONSTANTS,
                      not_contains='symOp',
                      contains='filmLattice/bravaisMatrix')) == [5.3011797029, 0.0, 0.0]

    with pytest.raises(ValueError, match='The tag TEST has no possible paths with the current specification.'):
        evaluate_text(root, schema_dict, 'TEST', FLEUR_DEFINED_CONSTANTS)

    expected_info = {'parser_warnings': ['No text found for tag magnetism']}
    parser_info_out = {'parser_warnings': []}
    assert evaluate_text(root, schema_dict, 'magnetism', FLEUR_DEFINED_CONSTANTS,
                         parser_info_out=parser_info_out) is None

    assert schema_dict == schema_dict_34


def test_evaluate_tag():
    """
    Test of the evaluate_tag function
    """
    from lxml import etree
    from masci_tools.util.schema_dict_util import evaluate_tag

    schema_dict = copy.deepcopy(schema_dict_34)

    parser = etree.XMLParser(attribute_defaults=True, recover=False, encoding='utf-8')
    xmltree = etree.parse(TEST_INPXML_PATH, parser)
    outxmltree = etree.parse(TEST_OUTXML_PATH2, parser)

    outroot = outxmltree.getroot()
    root = xmltree.getroot()

    expected = {
        'itmax': 1,
        'maxIterBroyd': 99,
        'imix': 'Anderson',
        'alpha': 0.05,
        'precondParam': 0.0,
        'spinf': 2.0,
        'minDistance': 1e-05,
        'maxTimeToStartIter': None
    }
    scfloop = evaluate_tag(root, schema_dict, 'scfLoop', FLEUR_DEFINED_CONSTANTS)
    assert scfloop == expected

    with pytest.raises(ValueError, match='The tag TEST has no possible paths with the current specification.'):
        evaluate_tag(root, schema_dict, 'TEST', FLEUR_DEFINED_CONSTANTS)
    with pytest.raises(ValueError,
                       match='The tag mtSphere has multiple possible paths with the current specification.'):
        evaluate_tag(root, schema_dict, 'mtSphere', FLEUR_DEFINED_CONSTANTS)

    expected_info = {
        'parser_warnings': [
            'Failed to evaluate attributes from tag qss: '
            'No attributes to parse either the tag does not '
            'exist or it has no attributes'
        ]
    }
    parser_info_out = {'parser_warnings': []}
    assert evaluate_tag(root, schema_dict, 'qss', FLEUR_DEFINED_CONSTANTS, parser_info_out=parser_info_out) == {}
    assert parser_info_out == expected_info

    expected = {'radius': [2.2, 2.2], 'gridPoints': [787, 787], 'logIncrement': [0.016, 0.017]}
    mtRadii = evaluate_tag(root, schema_dict, 'mtSphere', FLEUR_DEFINED_CONSTANTS, contains='species')
    assert mtRadii == expected

    mtRadii = evaluate_tag(outroot,
                           schema_dict,
                           'mtSphere',
                           FLEUR_DEFINED_CONSTANTS,
                           contains='species',
                           replace_root=INPUT_TAG_34)
    assert mtRadii == expected

    expected = {
        'l_constrained': None,
        'l_mtNocoPot': None,
        'l_relaxSQA': None,
        'l_magn': None,
        'M': None,
        'alpha': [0.0, 0.0],
        'beta': [1.570796326, 1.570796326],
        'b_cons_x': None,
        'b_cons_y': None
    }
    nocoParams = evaluate_tag(root, schema_dict, 'nocoParams', FLEUR_DEFINED_CONSTANTS, contains='atomGroup')
    assert nocoParams == expected

    expected = {
        'alpha': [0.0, 0.0],
        'beta': [1.570796326, 1.570796326],
    }
    nocoParams = evaluate_tag(root,
                              schema_dict,
                              'nocoParams',
                              FLEUR_DEFINED_CONSTANTS,
                              contains='atomGroup',
                              only_required=True)
    assert nocoParams == expected

    expected = {
        'beta': [1.570796326, 1.570796326],
    }
    nocoParams = evaluate_tag(root,
                              schema_dict,
                              'nocoParams',
                              FLEUR_DEFINED_CONSTANTS,
                              contains='atomGroup',
                              only_required=True,
                              ignore=['alpha'])
    assert nocoParams == expected

    assert schema_dict == schema_dict_34


def test_single_value_tag():
    """
    Test of the evaluate_single_value_tag function
    """
    from lxml import etree
    from masci_tools.util.schema_dict_util import evaluate_single_value_tag, get_tag_xpath
    from masci_tools.util.xml.common_xml_util import eval_xpath

    schema_dict = copy.deepcopy(outschema_dict_34)

    parser = etree.XMLParser(attribute_defaults=True, recover=False, encoding='utf-8')
    xmltree = etree.parse(TEST_OUTXML_PATH, parser)
    root = xmltree.getroot()

    iteration_xpath = get_tag_xpath(schema_dict, 'iteration')
    iteration = eval_xpath(root, iteration_xpath, list_return=True)[0]

    expected = {'comment': None, 'units': 'Htr', 'value': -4204.714048254}
    totalEnergy = evaluate_single_value_tag(iteration, schema_dict, 'totalEnergy', FLEUR_DEFINED_CONSTANTS)
    assert totalEnergy == expected

    expected = {'value': -4204.714048254}
    totalEnergy = evaluate_single_value_tag(iteration,
                                            schema_dict,
                                            'totalEnergy',
                                            FLEUR_DEFINED_CONSTANTS,
                                            only_required=True)
    assert totalEnergy == expected

    with pytest.raises(ValueError, match='The tag total_energy has no possible paths with the current specification.'):
        evaluate_single_value_tag(root, schema_dict, 'total_energy', FLEUR_DEFINED_CONSTANTS)
    with pytest.raises(ValueError,
                       match='The tag totalCharge has multiple possible paths with the current specification.'):
        evaluate_single_value_tag(root, schema_dict, 'totalCharge', FLEUR_DEFINED_CONSTANTS)

    expected = {'units': None, 'value': 63.9999999893}
    totalCharge = evaluate_single_value_tag(iteration,
                                            schema_dict,
                                            'totalCharge',
                                            FLEUR_DEFINED_CONSTANTS,
                                            contains='allElectronCharges',
                                            not_contains='fixed')
    assert totalCharge == expected

    expected = {'value': 63.9999999893}
    totalCharge = evaluate_single_value_tag(iteration,
                                            schema_dict,
                                            'totalCharge',
                                            FLEUR_DEFINED_CONSTANTS,
                                            contains='allElectronCharges',
                                            not_contains='fixed',
                                            ignore=['units'])
    assert totalCharge == expected

    assert schema_dict == outschema_dict_34


def test_evaluate_parent_tag():
    """
    Test of the evaluate_parent_tag function
    """
    from lxml import etree
    from masci_tools.util.schema_dict_util import evaluate_parent_tag

    schema_dict = copy.deepcopy(schema_dict_34)

    parser = etree.XMLParser(attribute_defaults=True, recover=False, encoding='utf-8')
    xmltree = etree.parse(TEST_OUTXML_PATH, parser)
    root = xmltree.getroot()

    expected = {
        'atomicNumber': [31, 31, 33, 33],
        'element': ['Ga', 'Ga', 'As', 'As'],
        'name': ['Ga-1', 'Ga-1', 'As-2', 'As-2']
    }
    ldaU_species = evaluate_parent_tag(root,
                                       schema_dict,
                                       'ldaU',
                                       FLEUR_DEFINED_CONSTANTS,
                                       contains='species',
                                       replace_root=INPUT_TAG_34)
    pprint(ldaU_species)
    assert ldaU_species == expected

    expected = {'atomicNumber': [31, 31, 33, 33], 'name': ['Ga-1', 'Ga-1', 'As-2', 'As-2']}
    ldaU_species = evaluate_parent_tag(root,
                                       schema_dict,
                                       'ldaU',
                                       FLEUR_DEFINED_CONSTANTS,
                                       contains='species',
                                       only_required=True,
                                       replace_root=INPUT_TAG_34)
    pprint(ldaU_species)
    assert ldaU_species == expected

    expected = {'name': ['Ga-1', 'Ga-1', 'As-2', 'As-2']}
    ldaU_species = evaluate_parent_tag(root,
                                       schema_dict,
                                       'ldaU',
                                       FLEUR_DEFINED_CONSTANTS,
                                       contains='species',
                                       only_required=True,
                                       replace_root=INPUT_TAG_34,
                                       ignore=['atomicNumber'])
    pprint(ldaU_species)
    assert ldaU_species == expected

    assert schema_dict == schema_dict_34


def test_tag_exists():
    """
    Test of the tag_exists function
    """
    from lxml import etree
    from masci_tools.util.schema_dict_util import tag_exists

    schema_dict = copy.deepcopy(schema_dict_34)

    parser = etree.XMLParser(attribute_defaults=True, recover=False, encoding='utf-8')
    xmltree = etree.parse(TEST_INPXML_PATH, parser)
    outxmltree = etree.parse(TEST_OUTXML_PATH2, parser)

    outroot = outxmltree.getroot()
    root = xmltree.getroot()

    assert tag_exists(root, schema_dict, 'filmPos')
    assert tag_exists(root, schema_dict, 'calculationSetup')

    assert not tag_exists(root, schema_dict, 'ldaU', contains='species')
    assert tag_exists(root, schema_dict, 'ldaU', not_contains='atom')

    assert not tag_exists(outroot, schema_dict, 'ldaU', contains='species', replace_root=INPUT_TAG_34)
    assert tag_exists(outroot, schema_dict, 'ldaU', not_contains='atom', replace_root=INPUT_TAG_34)

    with pytest.raises(ValueError, match='The tag ldaU has multiple possible paths with the current specification.'):
        tag_exists(root, schema_dict, 'ldaU')
    with pytest.raises(ValueError, match='The tag ldaU has no possible paths with the current specification.'):
        tag_exists(root, schema_dict, 'ldaU', contains='group')

    assert schema_dict == schema_dict_34


def test_get_number_of_nodes():
    """
    Test of the get_number_of_nodes function
    """
    from lxml import etree
    from masci_tools.util.schema_dict_util import get_number_of_nodes

    schema_dict = copy.deepcopy(schema_dict_34)

    parser = etree.XMLParser(attribute_defaults=True, recover=False, encoding='utf-8')
    xmltree = etree.parse(TEST_INPXML_PATH, parser)
    outxmltree = etree.parse(TEST_OUTXML_PATH2, parser)

    outroot = outxmltree.getroot()
    root = xmltree.getroot()

    assert get_number_of_nodes(root, schema_dict, 'filmPos') == 2
    assert get_number_of_nodes(root, schema_dict, 'calculationSetup') == 1
    assert get_number_of_nodes(root, schema_dict, 'ldaU', contains='species') == 0
    assert get_number_of_nodes(root, schema_dict, 'ldaU', not_contains='atom') == 1

    assert get_number_of_nodes(outroot, schema_dict, 'filmPos', replace_root=INPUT_TAG_34) == 2
    assert get_number_of_nodes(outroot, schema_dict, 'calculationSetup', replace_root=INPUT_TAG_34) == 1

    with pytest.raises(ValueError, match='The tag ldaU has multiple possible paths with the current specification.'):
        get_number_of_nodes(root, schema_dict, 'ldaU')
    with pytest.raises(ValueError, match='The tag ldaU has no possible paths with the current specification.'):
        get_number_of_nodes(root, schema_dict, 'ldaU', contains='group')

    assert schema_dict == schema_dict_34
