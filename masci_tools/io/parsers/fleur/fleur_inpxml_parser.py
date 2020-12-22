# -*- coding: utf-8 -*-
###############################################################################
# Copyright (c), Forschungszentrum Jülich GmbH, IAS-1/PGI-1, Germany.         #
#                All rights reserved.                                         #
# This file is part of the Masci-tools package.                               #
# (Material science tools)                                                    #
#                                                                             #
# The code is hosted on GitHub at https://github.com/judftteam/masci-tools    #
# For further information on the license, see the LICENSE.txt file            #
# For further information please visit http://www.flapw.de or                 #
#                                                                             #
###############################################################################
"""
This module contains functions to load an fleur inp.xml file, parse it with a schema
and convert its content to a dict
"""
from lxml import etree
from pprint import pprint
from masci_tools.io.parsers.fleur.fleur_schema import load_inpschema
from masci_tools.util.xml.common_xml_util import clear_xml, convert_xml_attribute, convert_xml_text
from masci_tools.util.schema_dict_util import read_constants


def inpxml_parser(inpxmlfile, version=None, parser_info_out=None):
    """
    Parses the given inp.xml file to a python dictionary utilizing the schema
    defined by the version number to validate and corretly convert to the dictionary

    :param inpxmlfile: either path to the inp.xml file or a xml etree to be parsed
    :param version: version string to enforce that a given schema is used
    :param parser_info_out: dict, with warnings, info, errors, ...

    :return: python dictionary with the parsed inp.xml
    """

    if parser_info_out is None:
        parser_info_out = {'parser_warnings': []}

    parser_version = '0.1.0'
    parser_info_out['parser_info'] = f'Masci-Tools Fleur inp.xml Parser v{parser_version}'

    if isinstance(inpxmlfile, str):
        parser = etree.XMLParser(attribute_defaults=True, encoding='utf-8')
        try:
            xmltree = etree.parse(inpxmlfile, parser)
        except etree.XMLSyntaxError as msg:
            raise ValueError(f'Failed to parse input file: {msg}') from msg
    else:
        xmltree = inpxmlfile

    if version is None:
        try:
            root = xmltree.getroot()
            version = root.attrib['fleurInputVersion']
        except KeyError as exc:
            raise ValueError('Failed to extract inputVersion') from exc

    parser_info_out['fleur_inp_version'] = version
    schema_dict, xmlschema = load_inpschema(version, schema_return=True)

    xmltree = clear_xml(xmltree)
    root = xmltree.getroot()

    constants = read_constants(xmltree, schema_dict)

    if not xmlschema.validate(xmltree):
        # get more information on what does not validate
        parser_on_fly = etree.XMLParser(attribute_defaults=True, schema=xmlschema, encoding='utf-8')
        inpxmlfile = etree.tostring(xmltree)
        message = ''
        try:
            tree_x = etree.fromstring(inpxmlfile, parser_on_fly)
        except etree.XMLSyntaxError as msg:
            message = msg
            raise ValueError(f'Input file does not validate against the schema: {message}') from msg
        raise ValueError('Input file does not validate against the schema: Reason is unknown')

    else:
        inp_dict = inpxml_todict(root, schema_dict, constants, parser_info_out=parser_info_out)

    return inp_dict


def inpxml_todict(parent, schema_dict, constants, omitted_tags=False, base_xpath=None, parser_info_out=None):
    """
    Recursive operation which transforms an xml etree to
    python nested dictionaries and lists.
    Decision to add a list is if the tag name is in the given list tag_several

    :param parent: some xmltree, or xml element
    :param schema_dict: structure/layout of the xml file in python dictionary
    :param constants: dict with all the defined constants
    :param omitted_tags: switch. If True only a list of the contained tags is returned
                         Used to omitt useless tags like e.g ['atomSpecies']['species'][3]
                         becomes ['atomSpecies'][3]
    :param base_xpath: str, keeps track of the place in the inp.xml currently being processed
    :param parser_info_out: dict, with warnings, info, errors, ...

    :return: a python dictionary
    """

    if parser_info_out is None:
        parser_info_out = {'parser_warnings': []}

    #Check if this is the first call to this routine
    if base_xpath is None:
        base_xpath = f'/{parent.tag}'

    return_dict = {}
    if list(parent.items()):
        return_dict = dict(list(parent.items()))
        # Now we have to convert lazy fortan style into pretty things for the Database
        for key in return_dict:
            if key in schema_dict['attrib_types']:
                conversion_warnings = []
                return_dict[key], suc = convert_xml_attribute(return_dict[key],
                                                              schema_dict['attrib_types'][key],
                                                              constants,
                                                              conversion_warnings=conversion_warnings)
                if not suc:
                    parser_info_out['parser_warnings'].append(
                        f"Failed to convert attribute '{key}': "
                        'Below are the warnings raised from convert_xml_attribute')
                    for warning in conversion_warnings:
                        parser_info_out['parser_warnings'].append(warning)

    if parent.text:
        # has text, but we don't want all the '\n' s and empty stings in the database
        if parent.text.strip() != '':  # might not be the best solutions
            if parent.tag not in schema_dict['simple_elements']:
                raise ValueError(
                    f'Something is wrong in the schema_dict: {parent.tag} is not in simple_elements, but it has text')
            conversion_warnings = []
            converted_text, suc = convert_xml_text(parent.text,
                                                   schema_dict['simple_elements'][parent.tag],
                                                   constants,
                                                   conversion_warnings=conversion_warnings)
            if not suc:
                parser_info_out['parser_warnings'].append(f"Failed to convert text of '{parent.tag}': "
                                                          'Below are the warnings raised from convert_xml_text')
                for warning in conversion_warnings:
                    parser_info_out['parser_warnings'].append(warning)

            if not return_dict:
                return_dict = converted_text
            else:
                return_dict['text_value'] = converted_text
                if 'label' in return_dict:
                    return_dict['text_label'] = return_dict['label']
                    return_dict.pop('label')

    if base_xpath in schema_dict['tag_info']:
        tag_info = schema_dict['tag_info'][base_xpath]
    else:
        tag_info = {'several': []}

    for element in parent:

        new_base_xpath = f'{base_xpath}/{element.tag}'
        omitt_contained_tags = element.tag in schema_dict['omitt_contained_tags']
        new_return_dict = inpxml_todict(element,
                                        schema_dict,
                                        constants,
                                        base_xpath=new_base_xpath,
                                        omitted_tags=omitt_contained_tags,
                                        parser_info_out=parser_info_out)

        if element.tag in tag_info['several']:
            # make a list, otherwise the tag will be overwritten in the dict
            if element.tag not in return_dict:  # is this the first occurence?
                if omitted_tags:
                    if len(return_dict) == 0:
                        return_dict = []
                else:
                    return_dict[element.tag] = []
            if omitted_tags:
                return_dict.append(new_return_dict)
            elif 'text_value' in new_return_dict:
                for key, value in new_return_dict.items():
                    if key == 'text_value':
                        return_dict[element.tag].append(value)
                    elif key == 'text_label':
                        if 'labels' not in return_dict:
                            return_dict['labels'] = {}
                        return_dict['labels'][value] = new_return_dict['text_value']
                    else:
                        if key not in return_dict:
                            return_dict[key] = []
                        elif not isinstance(return_dict[key], list):  #Key seems to be defined already
                            raise ValueError(f'{key} cannot be extracted to the next level')
                        return_dict[key].append(value)
                for key in new_return_dict.keys():
                    if key in ['text_value', 'text_label']:
                        continue
                    if len(return_dict[key]) != len(return_dict[element.tag]):
                        raise ValueError(
                            f'Extracted optional argument {key} at the moment only label is supported correctly')
            else:
                return_dict[element.tag].append(new_return_dict)
        else:
            return_dict[element.tag] = new_return_dict

    return return_dict