"""
Tests of the xml_getters
"""
import pytest
import os
from pathlib import Path

file_path2 = '../files/fleur/Max-R5'

inpxmlfilefolder = os.path.dirname(os.path.abspath(__file__))

inpxmlfilefolder_valid = [
    #    os.path.abspath(os.path.join(inpxmlfilefolder, file_path1)),
    os.path.abspath(os.path.join(inpxmlfilefolder, file_path2))
]

broken_inputs = [
    'CoHybridPBE0',
    'CoUnfold',
    'gw1Interface',
    'GaAsWannSOC',
    'TiO2eelsXML',
    'gw2Interface',
    'Fe_film_SS_conv',
    'SiHybrid8kpt_nosym',
    'SiHybrid8kpt_sym',
    'SiHybridGammaNoInv',
    'Fe_bulk_SS_conv',
    'Fe_film_SSFT',
    os.fspath(Path('Max-R5') / 'NiO_ldauXML'),
    os.fspath(Path('Max-R5') / 'Bi2Te3XML'),
]

TEST_FILM_INPXML_PATH = 'fleur/Max-R5/FePt_film_SSFT_LO/files/inp2.xml'
TEST_BULK_INPXML_PATH = 'fleur/Max-R5/SiLOXML/files/inp.xml'
TEST_SINGLE_KPOINT_PATH = 'fleur/Max-R5/SmAtomjDOS/files/inp.xml'
TEST_MULTIPLE_KPOINT_SETS_PATH = 'fleur/test_multiple_ksets.xml'
TEST_MAX4_INPXML_PATH = 'fleur/aiida_fleur/inpxml/FePt/inp.xml'
TEST_RELAX_INPXML_PATH = 'fleur/Max-R5/GaAsMultiUForceXML/files/inp-3.xml'
TEST_RELAX_OUTXML_PATH = 'fleur/Max-R5/GaAsMultiUForceXML/files/out.xml'
TEST_RELAX_RELAXXML_PATH = 'fleur/Max-R5/GaAsMultiUForceXML/files/relax.xml'
TEST_NO_SYMMETRY_PATH = 'fleur/aiida_fleur/inpxml/Fe_fccXML/files/inp.xml'
TEST_WITH_RELAX_INPXML_PATH = 'fleur/Max-R5/H2ORelaxBFGS/files/inp.xml'
TEST_NON_STANDARD_KIND_INPXML_PATH = 'fleur/Max-R5/CrystalFieldOutput/files/inp.xml'
TEST_KPT_MESH_SPECIFICATION_INPXML_PATH = 'fleur/Max-R5/Gd_Hubbard1/files/inp.xml'

inpxmlfilelist = []
inpxmlfilelist_content = []
for folder in inpxmlfilefolder_valid:
    for subdir, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.xml') and 'inp' in file:
                non_valid = False
                for broken in broken_inputs:
                    if broken in subdir:
                        non_valid = True
                if not non_valid:
                    inpxmlfilelist.append(os.path.join(subdir, file))


@pytest.mark.parametrize('inpxmlfilepath', inpxmlfilelist)
def test_get_cell(load_inpxml, inpxmlfilepath):
    """
    Test that get_cell works for all input files
    """
    from masci_tools.util.xml.xml_getters import get_cell
    import numpy as np

    xmltree, schema_dict = load_inpxml(inpxmlfilepath)

    cell, pbc = get_cell(xmltree, schema_dict)

    assert isinstance(cell, np.ndarray)
    assert cell.shape == (3, 3)
    assert isinstance(pbc, tuple)
    assert len(pbc) == 3


@pytest.mark.parametrize('inpxmlfilepath', inpxmlfilelist)
def test_get_symmetry_information(load_inpxml, inpxmlfilepath):
    """
    Test that get_cell works for all input files
    """
    from masci_tools.util.xml.xml_getters import get_symmetry_information
    import numpy as np

    xmltree, schema_dict = load_inpxml(inpxmlfilepath)

    rotations, shifts = get_symmetry_information(xmltree, schema_dict)

    assert all(isinstance(rot, np.ndarray) for rot in rotations)
    assert all(isinstance(shift, np.ndarray) for shift in shifts)
    assert all(rot.shape == (3, 3) for rot in rotations)
    assert all(shift.shape == (3,) for shift in shifts)


@pytest.mark.parametrize('inpxmlfilepath', inpxmlfilelist)
def test_get_structuredata(load_inpxml, inpxmlfilepath):
    """
    Test that get_cell works for all input files
    """
    from masci_tools.util.xml.xml_getters import get_structuredata
    from masci_tools.util.schema_dict_util import evaluate_attribute
    from masci_tools.io.common_functions import AtomSiteProperties
    import numpy as np

    xmltree, schema_dict = load_inpxml(inpxmlfilepath)

    #Detect the input files which should raise a UserWarning for adjusting the species names
    species_names = evaluate_attribute(xmltree, schema_dict, 'name', contains='species')
    if any('(' in name for name in species_names):
        with pytest.warns(UserWarning):
            atoms, cell, pbc = get_structuredata(xmltree, schema_dict)
    else:
        atoms, cell, pbc = get_structuredata(xmltree, schema_dict)

    assert isinstance(atoms, list)
    assert len(atoms) != 0
    assert all(isinstance(atom, AtomSiteProperties) for atom in atoms)
    assert isinstance(cell, np.ndarray)
    assert cell.shape == (3, 3)
    assert isinstance(pbc, tuple)
    assert len(pbc) == 3


@pytest.mark.parametrize('inpxmlfilepath', inpxmlfilelist)
def test_get_parameterdata(load_inpxml, inpxmlfilepath):
    """
    Test that get_cell works for all input files
    """
    from masci_tools.util.xml.xml_getters import get_parameterdata

    xmltree, schema_dict = load_inpxml(inpxmlfilepath)

    para = get_parameterdata(xmltree, schema_dict)

    assert isinstance(para, dict)
    assert len(para) != 0


@pytest.mark.parametrize('inpxmlfilepath', inpxmlfilelist)
def test_get_fleur_modes(load_inpxml, inpxmlfilepath):
    """
    Test that get_cell works for all input files
    """
    from masci_tools.util.xml.xml_getters import get_fleur_modes

    xmltree, schema_dict = load_inpxml(inpxmlfilepath)

    modes = get_fleur_modes(xmltree, schema_dict)

    assert isinstance(modes, dict)
    assert len(modes) != 0


@pytest.mark.parametrize('inpxmlfilepath', inpxmlfilelist)
def test_get_kpointsdata(load_inpxml, inpxmlfilepath):
    """
    Test that get_cell works for all input files
    """
    from masci_tools.util.xml.xml_getters import get_kpointsdata
    import numpy as np

    xmltree, schema_dict = load_inpxml(inpxmlfilepath)

    kpoints, weights, cell, pbc = get_kpointsdata(xmltree, schema_dict)

    assert kpoints is not None
    assert weights is not None
    assert isinstance(cell, np.ndarray)
    assert cell.shape == (3, 3)
    assert isinstance(pbc, tuple)
    assert len(pbc) == 3


@pytest.mark.parametrize('inpxmlfilepath', inpxmlfilelist)
def test_get_nkpts(load_inpxml, inpxmlfilepath):
    """
    Test that get_nkpts works for all input files
    """
    from masci_tools.util.xml.xml_getters import get_nkpts

    xmltree, schema_dict = load_inpxml(inpxmlfilepath)

    nkpts = get_nkpts(xmltree, schema_dict)

    assert isinstance(nkpts, int)
    assert nkpts != 0


@pytest.mark.parametrize('inpxmlfilepath', inpxmlfilelist)
def test_get_special_kpoints(load_inpxml, inpxmlfilepath):
    """
    Test that get_special_kpoints works for all input files
    """
    from masci_tools.util.xml.xml_getters import get_special_kpoints

    xmltree, schema_dict = load_inpxml(inpxmlfilepath)

    special_points = get_special_kpoints(xmltree, schema_dict)

    assert special_points is not None


def test_get_cell_film(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_cell
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml(TEST_FILM_INPXML_PATH, absolute=False)

    cell, pbc = get_cell(xmltree, schema_dict)

    data_regression.check({'cell': convert_to_pystd(cell), 'pbc': pbc})


def test_get_cell_film_max6(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_cell
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml('fleur/Max-R6/inp_film.xml', absolute=False)

    cell, pbc = get_cell(xmltree, schema_dict)

    data_regression.check({'cell': convert_to_pystd(cell), 'pbc': pbc})


def test_get_cell_bulk(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_cell
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml(TEST_BULK_INPXML_PATH, absolute=False)

    cell, pbc = get_cell(xmltree, schema_dict)

    data_regression.check({'cell': convert_to_pystd(cell), 'pbc': pbc})


def test_get_cell_output(load_outxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_cell
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_outxml('fleur/Max-R5/SiLOXML/files/out.xml', absolute=False)

    cell, pbc = get_cell(xmltree, schema_dict)

    data_regression.check({'cell': convert_to_pystd(cell), 'pbc': pbc})


def test_get_symmetry_information_existing(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_symmetry_information
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml(TEST_BULK_INPXML_PATH, absolute=False)

    rotations, shifts = get_symmetry_information(xmltree, schema_dict)

    data_regression.check({'rotations': convert_to_pystd(rotations), 'shifts': convert_to_pystd(shifts)})


def test_get_symmetry_output(load_outxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_symmetry_information
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_outxml('fleur/Max-R5/SiLOXML/files/out.xml', absolute=False)

    rotations, shifts = get_symmetry_information(xmltree, schema_dict)

    data_regression.check({'rotations': convert_to_pystd(rotations), 'shifts': convert_to_pystd(shifts)})


def test_get_symmetry_information_nonexisting(load_inpxml):

    from masci_tools.util.xml.xml_getters import get_symmetry_information

    xmltree, schema_dict = load_inpxml(TEST_NO_SYMMETRY_PATH, absolute=False)

    with pytest.raises(ValueError, match='No explicit symmetry information included'):
        rotations, shifts = get_symmetry_information(xmltree, schema_dict)


def test_get_structuredata_film(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_structuredata
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml(TEST_FILM_INPXML_PATH, absolute=False)

    atoms, cell, pbc = get_structuredata(xmltree, schema_dict)

    data_regression.check({
        'atoms': convert_to_pystd([dict(atom._asdict()) for atom in atoms]),
        'cell': convert_to_pystd(cell),
        'pbc': pbc
    })


def test_get_structuredata_bulk(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_structuredata
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml(TEST_BULK_INPXML_PATH, absolute=False)

    atoms, cell, pbc = get_structuredata(xmltree, schema_dict)

    data_regression.check({
        'atoms': convert_to_pystd([dict(atom._asdict()) for atom in atoms]),
        'cell': convert_to_pystd(cell),
        'pbc': pbc
    })


def test_get_structuredata_no_relaxed(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_structuredata
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml(TEST_WITH_RELAX_INPXML_PATH, absolute=False)

    atoms, cell, pbc = get_structuredata(xmltree, schema_dict, include_relaxations=False)

    data_regression.check({
        'atoms': convert_to_pystd([dict(atom._asdict()) for atom in atoms]),
        'cell': convert_to_pystd(cell),
        'pbc': pbc
    })


def test_get_structuredata_relaxed(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_structuredata
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml(TEST_WITH_RELAX_INPXML_PATH, absolute=False)

    atoms, cell, pbc = get_structuredata(xmltree, schema_dict)

    data_regression.check({
        'atoms': convert_to_pystd([dict(atom._asdict()) for atom in atoms]),
        'cell': convert_to_pystd(cell),
        'pbc': pbc
    })


def test_get_structuredata_output(load_outxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_structuredata
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_outxml('fleur/Max-R5/SiLOXML/files/out.xml', absolute=False)

    atoms, cell, pbc = get_structuredata(xmltree, schema_dict)

    data_regression.check({
        'atoms': convert_to_pystd([dict(atom._asdict()) for atom in atoms]),
        'cell': convert_to_pystd(cell),
        'pbc': pbc
    })


def test_get_structuredata_norm_kinds(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_structuredata
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml(TEST_NON_STANDARD_KIND_INPXML_PATH, absolute=False)

    with pytest.warns(UserWarning):
        atoms, cell, pbc = get_structuredata(xmltree, schema_dict)

    data_regression.check({
        'atoms': convert_to_pystd([dict(atom._asdict()) for atom in atoms]),
        'cell': convert_to_pystd(cell),
        'pbc': pbc
    })


def test_fleur_modes_film(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_fleur_modes

    xmltree, schema_dict = load_inpxml(TEST_FILM_INPXML_PATH, absolute=False)

    modes = get_fleur_modes(xmltree, schema_dict)

    data_regression.check(modes)


def test_fleur_modes_bulk(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_fleur_modes

    xmltree, schema_dict = load_inpxml(TEST_BULK_INPXML_PATH, absolute=False)

    modes = get_fleur_modes(xmltree, schema_dict)

    data_regression.check(modes)


def test_fleur_modes_output(load_outxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_fleur_modes

    xmltree, schema_dict = load_outxml('fleur/Max-R5/SiLOXML/files/out.xml', absolute=False)

    modes = get_fleur_modes(xmltree, schema_dict)

    data_regression.check(modes)


def test_get_parameterdata_film(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_parameterdata

    xmltree, schema_dict = load_inpxml(TEST_FILM_INPXML_PATH, absolute=False)

    para = get_parameterdata(xmltree, schema_dict)

    data_regression.check(para)


def test_get_parameterdata_bulk(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_parameterdata

    xmltree, schema_dict = load_inpxml(TEST_BULK_INPXML_PATH, absolute=False)

    para = get_parameterdata(xmltree, schema_dict)

    data_regression.check(para)


def test_get_parameterdata_econfig_extraction(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_parameterdata

    xmltree, schema_dict = load_inpxml(TEST_FILM_INPXML_PATH, absolute=False)

    para = get_parameterdata(xmltree, schema_dict, extract_econfig=True)

    data_regression.check(para)


def test_get_parameterdata_econfig_extraction_not_inpgen_ready(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_parameterdata

    xmltree, schema_dict = load_inpxml(TEST_FILM_INPXML_PATH, absolute=False)

    para = get_parameterdata(xmltree, schema_dict, extract_econfig=True, inpgen_ready=False)

    data_regression.check(para)


def test_get_parameterdata_norm_kinds(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_parameterdata

    xmltree, schema_dict = load_inpxml(TEST_NON_STANDARD_KIND_INPXML_PATH, absolute=False)

    para = get_parameterdata(xmltree, schema_dict)

    data_regression.check(para)


def test_get_parameterdata_mesh_specification(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_parameterdata

    xmltree, schema_dict = load_inpxml(TEST_KPT_MESH_SPECIFICATION_INPXML_PATH, absolute=False)

    para = get_parameterdata(xmltree, schema_dict)

    data_regression.check(para)


def test_get_parameterdata_special_los(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_parameterdata

    xmltree, schema_dict = load_inpxml('fleur/inp_special_los.xml', absolute=False)

    para = get_parameterdata(xmltree, schema_dict)

    data_regression.check(para)


def test_get_parameterdata_special_los_not_allowed(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_parameterdata

    xmltree, schema_dict = load_inpxml('fleur/inp_special_los.xml', absolute=False)

    para = get_parameterdata(xmltree, schema_dict, allow_special_los=False)

    data_regression.check(para)


def test_get_parameterdata_kpoint_with_gamma(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_parameterdata

    xmltree, schema_dict = load_inpxml(TEST_MULTIPLE_KPOINT_SETS_PATH, absolute=False)
    node = xmltree.xpath('//kPointListSelection')[0]
    node.set('listName', 'third-set')

    para = get_parameterdata(xmltree, schema_dict)

    data_regression.check(para)


def test_get_parameterdata_output(load_outxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_parameterdata

    xmltree, schema_dict = load_outxml('fleur/Max-R5/SiLOXML/files/out.xml', absolute=False)

    para = get_parameterdata(xmltree, schema_dict)

    data_regression.check(para)


def test_get_kpointsdata_film(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_kpointsdata
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml(TEST_FILM_INPXML_PATH, absolute=False)

    kpoints, weights, cell, pbc = get_kpointsdata(xmltree, schema_dict)

    data_regression.check({'kpoints': kpoints, 'weights': weights, 'cell': convert_to_pystd(cell), 'pbc': pbc})


def test_get_kpointsdata_bulk(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_kpointsdata
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml(TEST_BULK_INPXML_PATH, absolute=False)

    kpoints, weights, cell, pbc = get_kpointsdata(xmltree, schema_dict)

    data_regression.check({'kpoints': kpoints, 'weights': weights, 'cell': convert_to_pystd(cell), 'pbc': pbc})


def test_get_kpointsdata_single_kpoint(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_kpointsdata
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml(TEST_SINGLE_KPOINT_PATH, absolute=False)

    kpoints, weights, cell, pbc = get_kpointsdata(xmltree, schema_dict)

    data_regression.check({'kpoints': kpoints, 'weights': weights, 'cell': convert_to_pystd(cell), 'pbc': pbc})


def test_get_kpointsdata_multiple_sets(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_kpointsdata
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml(TEST_MULTIPLE_KPOINT_SETS_PATH, absolute=False)

    kpoints, weights, cell, pbc = get_kpointsdata(xmltree, schema_dict)

    data_regression.check({'kpoints': kpoints, 'weights': weights, 'cell': convert_to_pystd(cell), 'pbc': pbc})


def test_get_kpointsdata_multiple_sets_selection(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_kpointsdata
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml(TEST_MULTIPLE_KPOINT_SETS_PATH, absolute=False)

    kpoints, weights, cell, pbc = get_kpointsdata(xmltree, schema_dict, name='default')

    data_regression.check({'kpoints': kpoints, 'weights': weights, 'cell': convert_to_pystd(cell), 'pbc': pbc})


def test_get_kpointsdata_multiple_sets_selection_index(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_kpointsdata
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml(TEST_MULTIPLE_KPOINT_SETS_PATH, absolute=False)

    kpoints, weights, cell, pbc = get_kpointsdata(xmltree, schema_dict, index=0)

    data_regression.check({'kpoints': kpoints, 'weights': weights, 'cell': convert_to_pystd(cell), 'pbc': pbc})


def test_get_kpointsdata_multiple_sets_selection_used(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_kpointsdata
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml(TEST_MULTIPLE_KPOINT_SETS_PATH, absolute=False)

    #Conflicting arguments
    with pytest.raises(ValueError):
        kpoints, weights, cell, pbc = get_kpointsdata(xmltree, schema_dict, index=0, only_used=True)
    with pytest.raises(ValueError):
        kpoints, weights, cell, pbc = get_kpointsdata(xmltree, schema_dict, name='default', only_used=True)

    kpoints, weights, cell, pbc = get_kpointsdata(xmltree, schema_dict, only_used=True)

    data_regression.check({'kpoints': kpoints, 'weights': weights, 'cell': convert_to_pystd(cell), 'pbc': pbc})


def test_get_kpointsdata_output(load_outxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_kpointsdata
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_outxml('fleur/Max-R5/SiLOXML/files/out.xml', absolute=False)

    kpoints, weights, cell, pbc = get_kpointsdata(xmltree, schema_dict)

    data_regression.check({'kpoints': kpoints, 'weights': weights, 'cell': convert_to_pystd(cell), 'pbc': pbc})


def test_get_kpointsdata_output_max4(load_outxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_kpointsdata
    from masci_tools.io.common_functions import convert_to_pystd

    with pytest.warns(UserWarning):
        xmltree, schema_dict = load_outxml('fleur/old_versions/Max4_test_out.xml', absolute=False)

    kpoints, weights, cell, pbc = get_kpointsdata(xmltree, schema_dict)

    data_regression.check({'kpoints': kpoints, 'weights': weights, 'cell': convert_to_pystd(cell), 'pbc': pbc})


def test_get_kpointsdata_max4(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_kpointsdata
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml(TEST_MAX4_INPXML_PATH, absolute=False)

    kpoints, weights, cell, pbc = get_kpointsdata(xmltree, schema_dict)

    data_regression.check({'kpoints': kpoints, 'weights': weights, 'cell': convert_to_pystd(cell), 'pbc': pbc})


def test_get_parameterdata_max4(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_parameterdata

    xmltree, schema_dict = load_inpxml(TEST_MAX4_INPXML_PATH, absolute=False)

    para = get_parameterdata(xmltree, schema_dict)

    data_regression.check(para)


def test_fleur_modes_max4(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_fleur_modes

    xmltree, schema_dict = load_inpxml(TEST_MAX4_INPXML_PATH, absolute=False)

    modes = get_fleur_modes(xmltree, schema_dict)

    data_regression.check(modes)


def test_get_structuredata_max4(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_structuredata
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml(TEST_MAX4_INPXML_PATH, absolute=False)

    atoms, cell, pbc = get_structuredata(xmltree, schema_dict)

    data_regression.check({
        'atoms': convert_to_pystd([dict(atom._asdict()) for atom in atoms]),
        'cell': convert_to_pystd(cell),
        'pbc': pbc
    })


def test_get_cell_max4(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_cell
    from masci_tools.io.common_functions import convert_to_pystd

    xmltree, schema_dict = load_inpxml(TEST_MAX4_INPXML_PATH, absolute=False)

    cell, pbc = get_cell(xmltree, schema_dict)

    data_regression.check({'cell': convert_to_pystd(cell), 'pbc': pbc})


def test_get_nkpts_single(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_nkpts

    xmltree, schema_dict = load_inpxml(TEST_SINGLE_KPOINT_PATH, absolute=False)

    nkpts = get_nkpts(xmltree, schema_dict)

    assert isinstance(nkpts, int)
    assert nkpts == 1


def test_get_nkpts_multiple(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_nkpts

    xmltree, schema_dict = load_inpxml(TEST_MULTIPLE_KPOINT_SETS_PATH, absolute=False)

    nkpts = get_nkpts(xmltree, schema_dict)

    assert isinstance(nkpts, int)
    assert nkpts == 20


def test_nkpts_output(load_outxml):

    from masci_tools.util.xml.xml_getters import get_nkpts

    xmltree, schema_dict = load_outxml('fleur/Max-R5/SiLOXML/files/out.xml', absolute=False)

    nkpts = get_nkpts(xmltree, schema_dict)

    assert isinstance(nkpts, int)
    assert nkpts == 2


def test_get_nkpts_max4(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_nkpts

    xmltree, schema_dict = load_inpxml(TEST_MAX4_INPXML_PATH, absolute=False)

    nkpts = get_nkpts(xmltree, schema_dict)

    assert isinstance(nkpts, int)
    assert nkpts == 1


def test_get_nkpts_max4_altkpoint(load_inpxml):

    from masci_tools.util.xml.xml_getters import get_nkpts
    from masci_tools.util.xml.xml_setters_names import set_inpchanges

    xmltree, schema_dict = load_inpxml(TEST_MAX4_INPXML_PATH, absolute=False)

    #Activate band calculations
    xmltree = set_inpchanges(xmltree, schema_dict, {'band': True})

    with pytest.warns(UserWarning):
        nkpts = get_nkpts(xmltree, schema_dict)

    assert isinstance(nkpts, int)
    assert nkpts == 240


def test_get_relaxation_information_inpxml(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_relaxation_information

    xmltree, schema_dict = load_inpxml(TEST_RELAX_INPXML_PATH, absolute=False)

    relax_dict = get_relaxation_information(xmltree, schema_dict)

    data_regression.check(relax_dict)


def test_get_relaxation_information_outxml(load_outxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_relaxation_information

    xmltree, schema_dict = load_outxml(TEST_RELAX_OUTXML_PATH, absolute=False)

    relax_dict = get_relaxation_information(xmltree, schema_dict)

    data_regression.check(relax_dict)


def test_get_relaxation_information_relaxxml(load_inpxml, data_regression, test_file):

    from masci_tools.util.xml.xml_getters import get_relaxation_information
    from lxml import etree

    xmltree, schema_dict = load_inpxml(TEST_RELAX_INPXML_PATH, absolute=False)  #schema_dict has to come from somewhere
    xmltree = etree.parse(test_file(TEST_RELAX_RELAXXML_PATH))

    with pytest.warns(UserWarning, match='Cannot extract custom constants'):
        relax_dict = get_relaxation_information(xmltree, schema_dict)

    data_regression.check(relax_dict)


def test_get_special_kpoints_single(load_inpxml):

    from masci_tools.util.xml.xml_getters import get_special_kpoints
    xmltree, schema_dict = load_inpxml('fleur/Max-R5/CuBandXML/files/inp.xml', absolute=False)
    special_points = get_special_kpoints(xmltree, schema_dict)

    assert special_points == [(0, 'great'), (19, 'path')]


def test_get_special_kpoints_multiple(load_inpxml):

    from masci_tools.util.xml.xml_getters import get_special_kpoints
    xmltree, schema_dict = load_inpxml(TEST_MULTIPLE_KPOINT_SETS_PATH, absolute=False)
    special_points = get_special_kpoints(xmltree, schema_dict)

    assert special_points == {
        'default': [(1, 'these'), (6, 'are'), (11, 'very'), (15, 'special')],
        'second-set': [(0, 'test')],
        'third-set': []
    }


def test_get_special_kpoints_multiple_selection(load_inpxml):

    from masci_tools.util.xml.xml_getters import get_special_kpoints
    xmltree, schema_dict = load_inpxml(TEST_MULTIPLE_KPOINT_SETS_PATH, absolute=False)
    special_points = get_special_kpoints(xmltree, schema_dict, name='default')

    assert special_points == [(1, 'these'), (6, 'are'), (11, 'very'), (15, 'special')]


def test_get_special_kpoints_multiple_selection_index(load_inpxml):

    from masci_tools.util.xml.xml_getters import get_special_kpoints
    xmltree, schema_dict = load_inpxml(TEST_MULTIPLE_KPOINT_SETS_PATH, absolute=False)
    special_points = get_special_kpoints(xmltree, schema_dict, index=0)

    assert special_points == [(1, 'these'), (6, 'are'), (11, 'very'), (15, 'special')]


def test_get_special_kpoints_multiple_selection_used(load_inpxml):

    from masci_tools.util.xml.xml_getters import get_special_kpoints
    xmltree, schema_dict = load_inpxml(TEST_MULTIPLE_KPOINT_SETS_PATH, absolute=False)
    #Conflicting arguments
    with pytest.raises(ValueError):
        special_points = get_special_kpoints(xmltree, schema_dict, name='default', only_used=True)
    with pytest.raises(ValueError):
        special_points = get_special_kpoints(xmltree, schema_dict, index=0, only_used=True)

    special_points = get_special_kpoints(xmltree, schema_dict, only_used=True)

    assert special_points == [(1, 'these'), (6, 'are'), (11, 'very'), (15, 'special')]


def test_get_special_kpoints_output(load_outxml):

    from masci_tools.util.xml.xml_getters import get_special_kpoints
    xmltree, schema_dict = load_outxml('fleur/Max-R5/CuBandXML/files/out.xml', absolute=False)
    special_points = get_special_kpoints(xmltree, schema_dict)

    assert special_points == [(0, 'great'), (19, 'path')]


def test_get_parameterdata_kpt_no_mesh_attributes(load_inpxml, data_regression):

    from masci_tools.util.xml.xml_getters import get_parameterdata

    xmltree, schema_dict = load_inpxml('fleur/inp_kmesh_no_mesh_attrs.xml', absolute=False)

    para = get_parameterdata(xmltree, schema_dict)

    data_regression.check(para)
