"""
Tests of the Greensfunction module
"""
from masci_tools.tools.greensfunction import GreensFunction, GreensfElement
import numpy as np


def test_greensfunction_sphavg(test_file):
    """
    Basic test of greensfunction
    """

    gf = GreensFunction.fromFile(test_file('fleur/greensf/greensf_sphavg.hdf'), index=1)

    elem = gf.element._replace(atomDiff=gf.element.atomDiff.tolist())
    assert elem == GreensfElement(l=2,
                                  lp=2,
                                  atomType=1,
                                  atomTypep=1,
                                  sphavg=True,
                                  onsite=True,
                                  kresolved=False,
                                  contour=1,
                                  nLO=0,
                                  atomDiff=[0., 0., 0.])

    assert not gf.mperp
    assert gf.sphavg
    
    assert isinstance(gf.energy_dependence(spin=1), np.ndarray)
    assert gf.energy_dependence(spin=1).shape == (128, 5, 5)  #(nz,2*l+1,2*l+1)
    assert gf.energy_dependence(spin=1).dtype == float

    assert gf.energy_dependence(m=0,mp=0,spin=1).shape == (128, )  #(nz,2*l+1,2*l+1)
    assert gf.energy_dependence(m=0,mp=0,spin=1).dtype == float
    
    assert gf.energy_dependence(spin=1,both_contours=True).shape == (128, 5, 5, 2)  #(nz,2*l+1,2*l+1,2)
    assert gf.energy_dependence(spin=1,both_contours=True).dtype == complex
    
    assert isinstance(gf.trace_energy_dependence(spin=1), np.ndarray)
    assert gf.trace_energy_dependence(spin=1).shape == (128,)
    assert gf.trace_energy_dependence(spin=1).dtype == float


def test_greensfunction_radial(test_file):
    """
    Basic test of greensfunction
    """

    gf = GreensFunction.fromFile(test_file('fleur/greensf/greensf_radial.hdf'), l=2)

    elem = gf.element._replace(atomDiff=gf.element.atomDiff.tolist())
    assert elem == GreensfElement(l=2,
                                  lp=2,
                                  atomType=1,
                                  atomTypep=1,
                                  sphavg=False,
                                  onsite=True,
                                  kresolved=False,
                                  contour=1,
                                  nLO=1,
                                  atomDiff=[0., 0., 0.])

    assert not gf.mperp
    assert not gf.sphavg
    
    assert isinstance(gf.energy_dependence(spin=1), np.ndarray)
    assert gf.energy_dependence(spin=1).shape == (128, 5, 5)  #(nz,2*l+1,2*l+1)
    assert gf.energy_dependence(spin=1).dtype == float

    assert gf.energy_dependence(m=0,mp=0,spin=1).shape == (128, )  #(nz,2*l+1,2*l+1)
    assert gf.energy_dependence(m=0,mp=0,spin=1).dtype == float
    
    assert gf.energy_dependence(spin=1,both_contours=True).shape == (128, 5, 5, 2)  #(nz,2*l+1,2*l+1,2)
    assert gf.energy_dependence(spin=1,both_contours=True).dtype == complex
    
    assert isinstance(gf.trace_energy_dependence(spin=1), np.ndarray)
    assert gf.trace_energy_dependence(spin=1).shape == (128,)
    assert gf.trace_energy_dependence(spin=1).dtype == float