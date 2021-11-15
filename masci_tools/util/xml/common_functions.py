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
Common functions for parsing input/output files or XMLschemas from FLEUR
"""
from typing import TYPE_CHECKING, Dict, Iterable, Optional, Tuple, TypeVar, Union, List, Set, cast
from masci_tools.util.typing import XPathLike
from lxml import etree
import warnings
import os
import copy
from logging import Logger
if TYPE_CHECKING:
    from masci_tools.io.parsers import fleur_schema

from .xpathbuilder import XPathBuilder


def clear_xml(tree: etree._ElementTree) -> Tuple[etree._ElementTree, Set[str]]:
    """
    Removes comments and executes xinclude tags of an
    xml tree.

    :param tree: an xml-tree which will be processed

    :returns: cleared_tree, an xmltree without comments and with replaced xinclude tags
    """
    import copy

    cleared_tree = copy.deepcopy(tree)

    #Remove comments outside the root element (Since they have no parents this would lead to a crash)
    root = cleared_tree.getroot()
    prev_sibling = root.getprevious()
    while prev_sibling is not None:
        if prev_sibling.tag is etree.Comment:
            root.append(prev_sibling)
            root.remove(prev_sibling)
        prev_sibling = prev_sibling.getprevious()

    next_sibling = root.getnext()
    while next_sibling is not None:
        if next_sibling.tag is etree.Comment:
            root.append(next_sibling)
            root.remove(next_sibling)
        next_sibling = next_sibling.getnext()

    #find any include tags
    include_tags: List[etree._Element] = eval_xpath(cleared_tree,
                                                    '//xi:include',
                                                    namespaces={'xi': 'http://www.w3.org/2001/XInclude'},
                                                    list_return=True)  #type:ignore

    parents = []
    known_tags = []
    for tag in include_tags:
        parent = tag.getparent()
        if parent is None:
            raise ValueError('Could not find parent of included tag')
        parents.append(parent)
        known_tags.append({elem.tag for elem in parent if isinstance(elem.tag, str)})

    # replace XInclude parts to validate against schema
    if len(include_tags) != 0:
        cleared_tree.xinclude()  #type:ignore

    all_included_tags: Set[str] = set()
    # get rid of xml:base attribute in the included parts
    for parent, old_tags in zip(parents, known_tags):
        new_tags = {elem.tag for elem in parent if isinstance(elem.tag, str)}

        #determine the elements not in old_tags, which are in tags
        #so what should have been included
        included_tag_names = new_tags.difference(old_tags)

        #Check for emtpy set (relax.xml include may not insert something)
        if not included_tag_names:
            continue

        all_included_tags = all_included_tags.union(included_tag_names)
        for tag_name in included_tag_names:
            for elem in parent.iterchildren(tag=tag_name):
                for attribute in elem.attrib.keys():
                    if 'base' in attribute:
                        elem.attrib.pop(attribute, None)  #type:ignore

    # remove comments from inp.xml
    comments: List[etree._Element] = cleared_tree.xpath('//comment()')  #type:ignore
    for comment in comments:
        com_parent = comment.getparent()
        if com_parent is None:
            raise ValueError('Could not find parent of comment tag')
        com_parent.remove(comment)

    etree.indent(cleared_tree)

    return cleared_tree, all_included_tags


def reverse_xinclude(
        xmltree: etree._ElementTree, schema_dict: 'fleur_schema.SchemaDict', included_tags: Iterable[str],
        **kwargs: os.PathLike) -> Tuple[etree._ElementTree, Dict[Union[os.PathLike, str], etree._ElementTree]]:
    """
    Split the xmltree back up according to the given included tags.
    The original xmltree will be returned with the corresponding xinclude tags
    and the included trees are returned in a dict mapping the inserted filename
    to the extracted tree

    Tags for which no known filename is known are returned under unknown-1.xml, ...
    The following tags have known filenames:

        - `relaxation`: ``relax.xml``
        - `kPointLists`: ``kpts.xml``
        - `symmetryOperations`: ``sym.xml``
        - `atomSpecies`: ``species.xml``
        - `atomGroups`: ``atoms.xml``

    Additional mappings can be given in the keyword arguments

    :param xmltree: an xml-tree which will be processed
    :param schema_dict: Schema dictionary containing all the necessary information
    :param included_tags: Iterable of str, containing the names of the tags to be excluded

    :returns: xmltree with the inseerted xinclude tags and a dict mapping the filenames
              to the excluded trees

    :raises ValueError: if the tag can not be found in teh given xmltree
    """
    import copy

    INCLUDE_NSMAP = {'xi': 'http://www.w3.org/2001/XInclude'}
    INCLUDE_TAG = etree.QName(INCLUDE_NSMAP['xi'], 'include')
    FALLBACK_TAG = etree.QName(INCLUDE_NSMAP['xi'], 'fallback')

    excluded_tree = copy.deepcopy(xmltree)

    include_file_names: Dict[str, Union[os.PathLike, str]] = {
        'relaxation': 'relax.xml',
        'kPointLists': 'kpts.xml',
        'symmetryOperations': 'sym.xml',
        'atomSpecies': 'species.xml',
        'atomGroups': 'atoms.xml'
    }

    include_file_names = {**include_file_names, **kwargs}

    unknown_file_names = 0
    included_trees = {}
    root = excluded_tree.getroot()

    if not all(isinstance(tag, str) for tag in included_tags):
        raise ValueError(f'included_tags is not made up of strings: {included_tags}')

    for tag in included_tags:
        if tag in include_file_names:
            file_name = include_file_names[tag]
        else:
            warnings.warn(f'No filename known for tag {tag}')
            unknown_file_names += 1
            file_name = f'unknown-{unknown_file_names}.xml'

        try:
            tag_xpath = schema_dict.tag_xpath(tag)
        except Exception as err:
            raise ValueError(f'Cannot determine place of included tag {tag}') from err
        included_tag_res: List[etree._Element] = eval_xpath(root, tag_xpath, list_return=True)  #type:ignore

        if len(included_tag_res) != 1:
            raise ValueError(f'Cannot determine place of included tag {tag}')
        included_tag = included_tag_res[0]

        included_trees[file_name] = etree.ElementTree(included_tag)

        parent = included_tag.getparent()
        if parent is None:
            raise ValueError('Could not find parent of included tag')

        xinclude_elem = etree.Element(INCLUDE_TAG, href=os.fspath(file_name), nsmap=INCLUDE_NSMAP)  #type:ignore
        xinclude_elem.append(etree.Element(FALLBACK_TAG))  #type:ignore

        parent.replace(included_tag, xinclude_elem)

    if 'relax.xml' not in included_trees:
        #The relax.xml include should always be there
        xinclude_elem = etree.Element(INCLUDE_TAG, href='relax.xml', nsmap=INCLUDE_NSMAP)  #type:ignore
        xinclude_elem.append(etree.Element(FALLBACK_TAG))  #type:ignore
        root.append(xinclude_elem)

    etree.indent(excluded_tree)
    for tree in included_trees.values():
        etree.indent(tree)

    return excluded_tree, included_trees


def validate_xml(xmltree: etree._ElementTree,
                 schema: etree.XMLSchema,
                 error_header: str = 'File does not validate') -> None:
    """
    Checks a given xmltree against a schema and produces a nice error message
    with all the validation errors collected

    :param xmltree: xmltree of the file to validate
    :param schema: etree.XMLSchema to validate against
    :param error_header: str to lead a evtl error message with

    :raises: etree.DocumentInvalid if the schema does not validate
    """
    from itertools import groupby

    try:
        cleared_tree, _ = clear_xml(xmltree)
        schema.assertValid(cleared_tree)
    except etree.DocumentInvalid as exc:
        error_log = sorted(schema.error_log, key=lambda x: x.message)  #type:ignore
        error_output = []
        first_occurence = []
        for message, group in groupby(error_log, key=lambda x: x.message):
            err_occurences = list(group)
            error_message = f'Line {err_occurences[0].line}: {message}'
            error_lines = ''
            if len(err_occurences) > 1:
                error_lines = f"; This error also occured on the lines {', '.join([str(x.line) for x in err_occurences[1:]])}"
            error_output.append(f'{error_message}{error_lines} \n')
            first_occurence.append(err_occurences[0].line)

        error_output = [line for _, line in sorted(zip(first_occurence, error_output))]
        errmsg = f"{error_header}: \n{''.join(error_output)}"
        raise etree.DocumentInvalid(errmsg) from exc


def eval_xpath(node: Union[etree._Element, etree._ElementTree, 'etree._XPathEvaluatorBase'],
               xpath: XPathLike,
               logger: Logger = None,
               list_return: bool = False,
               namespaces: 'etree._DictAnyStr' = None,
               **variables: 'etree._XPathObject') -> 'etree._XPathObject':
    """
    Tries to evaluate an xpath expression. If it fails it logs it.
    If a absolute path is given (starting with '/') and the tag of the node
    does not match the root.
    It will try to find the tag in the path and convert it into a relative path

    :param node: root node of an etree
    :param xpath: xpath expression (relative, or absolute)
    :param logger: logger object for logging warnings, errors, if not provided all errors will be raised
    :param list_return: if True, the returned quantity is always a list even if only one element is in it
    :param namespaces: dict, passed to namespaces argument in xpath call

    :returns: text, attribute or a node list
    """
    if isinstance(xpath, XPathBuilder):
        xpath_str = xpath.path
        variables = {**variables, **xpath.path_variables}
        xpath = xpath_str

    if not isinstance(node, (etree._Element, etree._ElementTree, etree._XPathEvaluatorBase)):  #pylint: disable=protected-access
        if logger is not None:
            logger.error('Wrong Type for xpath eval; Got: %s', type(node))
        raise TypeError(f'Wrong Type for xpath eval; Got: {type(node)}')

    if isinstance(xpath, etree.XPath) and isinstance(node, etree._XPathEvaluatorBase):  #pylint: disable=protected-access
        if logger is not None:
            logger.error('Got an XPath object and an XPathEvaluator in eval_xpath')
        raise TypeError('Got an XPath object and an XPathEvaluator in eval_xpath')

    if namespaces is not None and (isinstance(xpath, etree.XPath) or isinstance(node, etree._XPathEvaluatorBase)):  #pylint: disable=protected-access
        if logger is not None:
            logger.exception(
                'Passing namespaces is only supported for string xpaths and nodes. for etree.XPath or XPathEvaluatore use namespaces in the init function'
            )
        raise ValueError(
            'Passing namespaces is only supported for string xpaths and nodes. for etree.XPath or XPathEvaluatore use namespaces in the init function'
        )

    try:
        if isinstance(xpath, etree.XPath):
            return_value = xpath(node, **variables)
        elif isinstance(node, etree._XPathEvaluatorBase):  #pylint: disable=protected-access
            return_value = node(xpath, **variables)
        else:
            return_value = node.xpath(xpath, namespaces=namespaces, **variables)  #type:ignore
    except etree.XPathEvalError as err:
        if logger is not None:
            logger.exception(
                'There was a XpathEvalError on the xpath: %s \n'
                'Either it does not exist, or something is wrong with the expression.', xpath)
        raise ValueError(f'There was a XpathEvalError on the xpath: {str(xpath)} \n'
                         'Either it does not exist, or something is wrong with the expression.') from err
    if isinstance(return_value, list):
        if len(return_value) == 1 and not list_return:
            return return_value[0]  #type:ignore
    return return_value


def get_xml_attribute(node: etree._Element, attributename: str, logger: Logger = None) -> Optional[str]:
    """
    Get an attribute value from a node.

    :param node: a node from etree
    :param attributename: a string with the attribute name.
    :param logger: logger object for logging warnings, errors, if not provided all errors will be raised
    :returns: either attributevalue, or None
    """

    if etree.iselement(node):
        attrib_value = node.get(attributename)
        if attrib_value:
            return attrib_value
        if logger is None:
            raise ValueError(f'Tried to get attribute: "{attributename}" from element {node.tag}.\n '
                             f'I received "{attrib_value}", maybe the attribute does not exist')
        logger.warning(
            'Tried to get attribute: "%s" from element %s.\n '
            'I received "%s", maybe the attribute does not exist', attributename, node.tag, attrib_value)

    else:  # something doesn't work here, some nodes get through here
        if logger is None:
            raise TypeError(f'Can not get attributename: "{attributename}" from node of type {type(node)}, '
                            f'because node is not an element of etree.')
        logger.error(
            'Can not get attributename: "%s" from node of type %s, '
            'because node is not an element of etree.', attributename, type(node))

    return None


TXPathLike = TypeVar('TXPathLike', bound=XPathLike)


def split_off_tag(xpath: TXPathLike) -> Tuple[TXPathLike, str]:
    """
    Splits off the last part of the given xpath

    .. note::
        etree.XPath objects could lose context in here, i.e.
        non-default options passed at init

    :param xpath:  xpath to split up
    """
    if isinstance(xpath, XPathBuilder):
        xpath = cast(TXPathLike, copy.deepcopy(xpath))
        tag = xpath.strip_off_tag()
        return xpath, tag

    if isinstance(xpath, etree.XPath):
        xpath_str = xpath.path  #type:ignore
    else:
        xpath_str = xpath

    split_xpath = xpath_str.split('/')
    if split_xpath[-1] == '':
        xpath_str, tag = '/'.join(split_xpath[:-2]), split_xpath[-2]
    else:
        xpath_str, tag = '/'.join(split_xpath[:-1]), split_xpath[-1]

    if isinstance(xpath, etree.XPath):
        xpath = cast(TXPathLike, etree.XPath(xpath_str))
    else:
        xpath = xpath_str

    return xpath, tag


def add_tag(xpath: TXPathLike, tag: str) -> TXPathLike:
    """
    Add tag to xpath

    .. note::
        etree.XPath objects could lose context in here, i.e.
        non-default options passed at init

    :param xpath: xpath to change
    :param tag: str of the tag to add

    :returns: xpath with the form {old_xpath}/tag
    """
    if isinstance(xpath, XPathBuilder):
        xpath = cast(TXPathLike, copy.deepcopy(xpath))
        xpath.append_tag(tag)
    elif isinstance(xpath, etree.XPath):
        xpath = cast(TXPathLike, etree.XPath(f'{str(xpath.path)}/{tag}'))  #type:ignore [attr-defined]
    else:
        xpath = cast(TXPathLike, f'{str(xpath)}/{tag}')
    return xpath


def split_off_attrib(xpath: TXPathLike) -> Tuple[TXPathLike, str]:
    """
    Splits off attribute of the given xpath (part after @)

    .. note::
        etree.XPath objects could lose context in here, i.e.
        non-default options passed at init

    :param xpath: xpath to split up
    """
    if isinstance(xpath, XPathBuilder):
        xpath = cast(TXPathLike, copy.deepcopy(xpath))
        attrib = xpath.strip_off_tag()
        if '@' not in attrib:
            raise ValueError('Path does not end with an attribute')
        return xpath, attrib.lstrip('@')

    if isinstance(xpath, etree.XPath):
        xpath_str = xpath.path  #type: ignore
    else:
        xpath_str = xpath

    split_xpath = xpath_str.split('/@')
    if len(split_xpath) != 2:
        raise ValueError(f"Splitting off attribute failed for: '{split_xpath}'")
    xpath_str, attrib = tuple(split_xpath)

    if isinstance(xpath, etree.XPath):
        xpath = cast(TXPathLike, etree.XPath(xpath_str))
    else:
        xpath = cast(TXPathLike, xpath_str)

    return xpath, attrib


def check_complex_xpath(node: Union[etree._Element, etree._ElementTree], base_xpath: XPathLike,
                        complex_xpath: XPathLike) -> None:
    """
    Check that the given complex xpath produces a subset of the results
    for the simple xpath

    :param node: root node of an etree or an etree
    :param base_xpath: str of the xpath without complex syntax
    :param complex_xpath: str of the xpath to check

    :raises ValueError: If the complex_xpath does not produce a subset of the results
                        of the base_xpath
    """

    results_base = set(eval_xpath(node, base_xpath, list_return=True))  #type:ignore
    results_complex = set(eval_xpath(node, complex_xpath, list_return=True))  #type:ignore

    if not results_base.issuperset(results_complex):
        raise ValueError(
            f"Complex xpath '{str(complex_xpath)}' is not compatible with the base_xpath '{str(base_xpath)}'")


def abs_to_rel_xpath(xpath: str, new_root: str) -> str:
    """
    Convert a given xpath to be relative from a tag appearing in the
    original xpath.

    :param xpath: str of the xpath to convert
    :param new_root: str of the tag from which the new xpath should be relative

    :returns: str of the relative xpath
    """
    if new_root in xpath:
        xpath = xpath + '/'
        xpath_to_root = '/'.join(xpath.split(new_root + '/')[:-1]) + new_root
        xpath = xpath.replace(xpath_to_root, '.')
        xpath = xpath.rstrip('/')
    else:
        raise ValueError(f'New root element {new_root} does not appear in xpath {xpath}')

    return xpath
