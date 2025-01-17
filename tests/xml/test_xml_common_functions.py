"""
Test of the functions in masci_tools.util.xml.common_functions
"""
import pytest
import logging
from lxml import etree
from masci_tools.util.xml.xpathbuilder import XPathBuilder

LOGGER = logging.getLogger(__name__)


def test_eval_xpath(caplog, load_inpxml):
    """
    Test of the eval_xpath function
    """
    from masci_tools.util.xml.common_functions import eval_xpath

    xmltree, _ = load_inpxml('fleur/test_clear.xml', absolute=False)
    root = xmltree.getroot()

    scfLoop = eval_xpath(root, '//scfLoop')
    assert isinstance(scfLoop, etree._Element)

    scfLoop = eval_xpath(root, '//scfLoop', list_return=True)
    assert len(scfLoop) == 1
    assert isinstance(scfLoop[0], etree._Element)

    include_tags = eval_xpath(root,
                              '//xi:include',
                              namespaces={'xi': 'http://www.w3.org/2001/XInclude'},
                              list_return=True)
    assert len(include_tags) == 2
    assert isinstance(include_tags[0], etree._Element)

    species_z = eval_xpath(root, "//species[@name='Cu-1']/@atomicNumber")
    assert species_z == '29'

    ldau_tags = eval_xpath(root, "//species[@name='Cu-1']/ldaU")
    assert ldau_tags == []

    with pytest.raises(ValueError, match='There was a XpathEvalError on the xpath:'):
        ldau_tags = eval_xpath(root, "//species/[@name='Cu-1']/ldaU")

    with caplog.at_level(logging.WARNING):
        with pytest.raises(ValueError, match='There was a XpathEvalError on the xpath:'):
            ldau_tags = eval_xpath(root, "//species/[@name='Cu-1']/ldaU", logger=LOGGER)

    assert 'There was a XpathEvalError on the xpath:' in caplog.text


def test_eval_xpath_all(load_inpxml):
    """
    Test of the eval_xpath function
    """
    from masci_tools.util.xml.common_functions import eval_xpath_all

    xmltree, _ = load_inpxml('fleur/test_clear.xml', absolute=False)
    root = xmltree.getroot()

    scfLoop = eval_xpath_all(root, '//scfLoop', etree._Element)
    assert isinstance(scfLoop, list)
    assert all(isinstance(n, etree._Element) for n in scfLoop)

    include_tags = eval_xpath_all(root,
                                  '//xi:include',
                                  etree._Element,
                                  namespaces={'xi': 'http://www.w3.org/2001/XInclude'})
    assert len(include_tags) == 2
    assert isinstance(include_tags[0], etree._Element)

    with pytest.raises(TypeError):
        eval_xpath_all(root, '//scfLoop', str)

    species_z = eval_xpath_all(root, "//species[@name='Cu-1']/@atomicNumber", str)
    assert species_z == ['29']

    ldau_tags = eval_xpath_all(root, "//species[@name='Cu-1']/ldaU")
    assert ldau_tags == []


def test_eval_xpath_one(load_inpxml):
    """
    Test of the eval_xpath function
    """
    from masci_tools.util.xml.common_functions import eval_xpath_one

    xmltree, _ = load_inpxml('fleur/test_clear.xml', absolute=False)
    root = xmltree.getroot()

    scfLoop = eval_xpath_one(root, '//scfLoop', etree._Element)
    assert isinstance(scfLoop, etree._Element)

    with pytest.raises(ValueError):
        eval_xpath_one(root, '//xi:include', etree._Element, namespaces={'xi': 'http://www.w3.org/2001/XInclude'})

    with pytest.raises(TypeError):
        eval_xpath_one(root, '//scfLoop', str)

    species_z = eval_xpath_one(root, "//species[@name='Cu-1']/@atomicNumber", str)
    assert species_z == '29'

    with pytest.raises(ValueError):
        eval_xpath_one(root, "//species[@name='Cu-1']/ldaU")


def test_eval_xpath_first(load_inpxml):
    """
    Test of the eval_xpath function
    """
    from masci_tools.util.xml.common_functions import eval_xpath_first

    xmltree, _ = load_inpxml('fleur/test_clear.xml', absolute=False)
    root = xmltree.getroot()

    scfLoop = eval_xpath_first(root, '//scfLoop', etree._Element)
    assert isinstance(scfLoop, etree._Element)

    include_tag = eval_xpath_first(root,
                                   '//xi:include',
                                   etree._Element,
                                   namespaces={'xi': 'http://www.w3.org/2001/XInclude'})

    assert isinstance(include_tag, etree._Element)
    assert include_tag.attrib['href'] == 'test_include.xml'

    with pytest.raises(TypeError):
        eval_xpath_first(root, '//scfLoop', str)

    species_z = eval_xpath_first(root, "//species[@name='Cu-1']/@atomicNumber", str)
    assert species_z == '29'

    with pytest.raises(ValueError):
        eval_xpath_first(root, "//species[@name='Cu-1']/ldaU")


def test_clear_xml(load_inpxml):
    """
    Test of the clear_xml function
    """
    from masci_tools.util.xml.common_functions import eval_xpath, clear_xml

    xmltree, _ = load_inpxml('fleur/test_clear.xml', absolute=False)
    root = xmltree.getroot()

    #Check that the file contains comments and includes
    comments = eval_xpath(root, '//comment()', list_return=True)
    assert len(comments) == 3

    include_tags = eval_xpath(root,
                              '//xi:include',
                              namespaces={'xi': 'http://www.w3.org/2001/XInclude'},
                              list_return=True)
    assert len(include_tags) == 2

    symmetry_tags = eval_xpath(root, '//symOp', list_return=True)
    assert len(symmetry_tags) == 0

    cleared_tree, all_include_tags = clear_xml(xmltree)
    cleared_root = cleared_tree.getroot()
    old_root = xmltree.getroot()

    assert all_include_tags == {'symmetryOperations'}
    #Make sure that the original tree was not modified
    comments = eval_xpath(old_root, '//comment()', list_return=True)
    assert len(comments) == 3

    #Check that the cleared tree is correct
    comments = eval_xpath(cleared_root, '//comment()', list_return=True)
    assert len(comments) == 0

    include_tags = eval_xpath(cleared_root,
                              '//xi:include',
                              namespaces={'xi': 'http://www.w3.org/2001/XInclude'},
                              list_return=True)
    assert len(include_tags) == 0

    symmetry_tags = eval_xpath(cleared_root, '//symOp', list_return=True)
    assert len(symmetry_tags) == 16


def test_clear_xml_multiple_comments_outside_root(load_inpxml):
    """
    Test of the clear_xml function
    """
    from masci_tools.util.xml.common_functions import eval_xpath, clear_xml

    xmltree, _ = load_inpxml('fleur/test_clear_multiple_comments.xml', absolute=False)
    root = xmltree.getroot()

    assert root.getprevious() is not None
    assert root.getnext() is not None

    cleared_tree, _ = clear_xml(xmltree)
    cleared_root = cleared_tree.getroot()

    assert cleared_root.getprevious() is None
    assert cleared_root.getnext() is None


def test_get_xml_attribute(load_inpxml, caplog):
    """
    Test of the clear_xml function
    """
    from masci_tools.util.xml.common_functions import get_xml_attribute, eval_xpath
    xmltree, _ = load_inpxml('fleur/test_clear.xml', absolute=False)
    root = xmltree.getroot()

    scfLoop = eval_xpath(root, '//scfLoop')
    assert get_xml_attribute(scfLoop, 'alpha') == '.05000000'
    assert get_xml_attribute(scfLoop, 'itmax') == '1'
    assert get_xml_attribute(scfLoop, 'maxIterBroyd') == '99'

    with pytest.raises(ValueError, match='Tried to get attribute: "TEST" from element scfLoop.'):
        get_xml_attribute(scfLoop, 'TEST')

    with caplog.at_level(logging.WARNING):
        assert get_xml_attribute(scfLoop, 'TEST', logger=LOGGER) is None
    assert 'Tried to get attribute: "TEST" from element scfLoop.' in caplog.text

    with pytest.raises(TypeError,
                       match='Can not get attributename: "TEST" from node of type <class \'lxml.etree._ElementTree\'>'):
        get_xml_attribute(xmltree, 'TEST')

    with caplog.at_level(logging.WARNING):
        assert get_xml_attribute(xmltree, 'TEST', logger=LOGGER) is None
    assert 'Can not get attributename: "TEST" from node of type <class \'lxml.etree._ElementTree\'>' in caplog.text


def test_split_off_tag():
    """
    Test of the split_off_tag function
    """
    from masci_tools.util.xml.common_functions import split_off_tag

    assert split_off_tag('/fleurInput/calculationSetup/cutoffs') == ('/fleurInput/calculationSetup', 'cutoffs')
    assert split_off_tag('/fleurInput/calculationSetup/cutoffs/') == ('/fleurInput/calculationSetup', 'cutoffs')
    assert split_off_tag('./calculationSetup/cutoffs') == ('./calculationSetup', 'cutoffs')

    path, tag = split_off_tag(XPathBuilder('/fleurInput/calculationSetup/cutoffs'))
    assert str(path) == '/fleurInput/calculationSetup'
    assert tag == 'cutoffs'

    path, tag = split_off_tag(etree.XPath('/fleurInput/calculationSetup/cutoffs'))
    assert str(path) == '/fleurInput/calculationSetup'
    assert tag == 'cutoffs'


def test_add_tag():
    """
    Test of the add_tag function
    """
    from masci_tools.util.xml.common_functions import add_tag

    assert add_tag('/fleurInput/calculationSetup', 'cutoffs') == '/fleurInput/calculationSetup/cutoffs'
    assert add_tag('/fleurInput/calculationSetup/', 'cutoffs') == '/fleurInput/calculationSetup/cutoffs'
    assert add_tag('./calculationSetup', 'cutoffs') == './calculationSetup/cutoffs'

    path = add_tag(XPathBuilder('/fleurInput/calculationSetup/'), 'cutoffs')
    assert str(path) == '/fleurInput/calculationSetup/cutoffs'

    path = add_tag(etree.XPath('/fleurInput/calculationSetup'), 'cutoffs')
    assert str(path) == '/fleurInput/calculationSetup/cutoffs'


def test_split_off_attrib():
    """
    Test of the split_off_tag function
    """
    from masci_tools.util.xml.common_functions import split_off_attrib

    assert split_off_attrib('/fleurInput/calculationSetup/cutoffs/@Kmax') == ('/fleurInput/calculationSetup/cutoffs',
                                                                              'Kmax')
    path, attrib = split_off_attrib(XPathBuilder('/fleurInput/calculationSetup/cutoffs/@Kmax'))

    assert str(path) == '/fleurInput/calculationSetup/cutoffs'
    assert attrib == 'Kmax'

    path, attrib = split_off_attrib(etree.XPath('/fleurInput/calculationSetup/cutoffs/@Kmax'))

    assert str(path) == '/fleurInput/calculationSetup/cutoffs'
    assert attrib == 'Kmax'

    with pytest.raises(ValueError):
        split_off_attrib('/fleurInput/calculationSetup/cutoffs')
    with pytest.raises(ValueError):
        split_off_attrib(XPathBuilder('/fleurInput/calculationSetup/cutoffs'))
    with pytest.raises(ValueError):
        split_off_attrib("/fleurInput/atomSpecies/species[@name='TEST']")
    assert split_off_attrib('./calculationSetup/cutoffs/@Kmax') == ('./calculationSetup/cutoffs', 'Kmax')


def test_check_complex_xpath(load_inpxml):
    """
    Test of the check_complex_xpath function
    """
    from masci_tools.util.xml.common_functions import check_complex_xpath

    xmltree, _ = load_inpxml('fleur/Max-R5/FePt_film_SSFT_LO/files/inp2.xml', absolute=False)

    check_complex_xpath(xmltree, '/fleurInput/atomSpecies/species', "/fleurInput/atomSpecies/species[@name='Fe-1']")

    with pytest.raises(ValueError):
        check_complex_xpath(xmltree, '/fleurInput/atomSpecies/species',
                            "/fleurInput/atomSpecies/species[@name='Fe-1']/lo")

    with pytest.raises(ValueError):
        check_complex_xpath(xmltree, '/fleurInput/atomSpecies/species',
                            "/fleurInput/atomSpecies/species[@name='Fe-1']/@name")

    check_complex_xpath(xmltree, '/fleurInput/atomSpecies/species', '/fleurInput/atomSpecies/species')
    check_complex_xpath(xmltree, '/fleurInput/atomSpecies/species',
                        "/fleurInput/atomSpecies/species[@name='does_not_exist']")
    check_complex_xpath(xmltree, '/fleurInput/atomSpecies/species/lo', "//species[@name='Pt-1']/lo")


def test_abs_to_rel_xpath():

    from masci_tools.util.xml.common_functions import abs_to_rel_xpath

    assert abs_to_rel_xpath('/test/new_root/relative/path', 'new_root') == './relative/path'
    assert abs_to_rel_xpath('/test/new_root/relative/path/@attrib', 'new_root') == './relative/path/@attrib'
    assert abs_to_rel_xpath('/test/new_root/relative/path', 'path') == '.'
    assert abs_to_rel_xpath('/test/new_root/relative/path/@attrib', 'path') == './@attrib'

    with pytest.raises(ValueError):
        abs_to_rel_xpath('/test/new_root/relative/path/@attrib', 'non_existent')

    assert abs_to_rel_xpath('/test/new_root/relativeExtra/path', 'relativeExtra') == './path'
    with pytest.raises(ValueError):
        abs_to_rel_xpath('/test/new_root/relativeExtra/path', 'relative')


@pytest.mark.parametrize('xpath,tag,result', [
    ('/test/tag/path', 'tag', True),
    ('/test/tags/path', 'tag', False),
    ('/test/tag/path', 'path', True),
    ('/test/tag/path', 'test', True),
    ('test/tag/path', 'tag', True),
    ('./test/tag/path', 'test', True),
    ('.', 'tag', False),
    ('/test/tag/path[asf]', 'tag', True),
    ('/test/tag[tests]/path[test]', 'tag', True),
    ('/test/tag[tests]/path[test]', 'tests', False),
    ('/test/tag[tests]/path[test]', 'test', True),
    (XPathBuilder('/test/tag/path'), 'test', True),
    (etree.XPath('/test/tag[tests]/path[test]'), 'test', True),
])
def test_contains_tag(xpath, tag, result):
    """
    Test of the contains tag function
    """
    from masci_tools.util.xml.common_functions import contains_tag

    assert contains_tag(xpath, tag) == result


def test_serialize_xml_objects():
    """
    Test of the serialize_xml_objects function
    """
    from masci_tools.util.xml.common_functions import serialize_xml_objects

    elem = etree.Element('test')
    elem_tree = etree.Element('test2').getroottree()

    res = serialize_xml_objects((elem_tree, 1, 'xer', elem), {
        'test': elem_tree,
        'another': 1,
        'string': 'xer',
        'here': elem
    })

    assert res == (('<test2/>\n', 1, 'xer', '<test/>\n'), {
        'test': '<test2/>\n',
        'another': 1,
        'string': 'xer',
        'here': '<test/>\n'
    })
