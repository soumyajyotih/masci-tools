# -*- coding: utf-8 -*-
"""Common base classes and methods for all plotting classes. Actual plotting classes are
divided into inheriting submodules, one per plotting tool (matplotlib, and so on).
"""
from abc import ABC, abstractmethod
from collections import namedtuple
from enum import Enum
import logging

from studenproject18ws.hdf.output_types import *
from studenproject18ws.dos.reader import get_dos_num_groups_characters

##########################################################################
#####################Section 1: Abstract Plot base classes ###############
#####################for different applications ##########################
##########################################################################


class PlotDataType(Enum):
    Bands = 1
    DOS_CSV = 2
    DOS_HDF = 3

class AbstractPlot(ABC):
    """
    Base class for all Plot classes.
    """

    def __init__(self, data: Data):
        """
        :param data:

        Attributes
        ----------
            icdv    interactive control display values (namedtuple)

        """
        if not hasattr(self, 'types'):
            self.types = set()
        self.data = data
        self.icdv = None

    @abstractmethod
    def get_data_ylim(self):
        """
        Useful for getting info on the maximum ylim before plotting, e.g. to set ylim to a GUI control.
        :return:
        """
        pass

    def get_alphas_colors_for_spin_overlay(self, spins, plotDataTypes = []):
        alphas = {0: 1, 1: 1} if (len(spins) == 1) else {0: 0.7, 1: 0.4}
        if any(typ in self.types for typ in plotDataTypes):
            # DOS: only two lines. loooks odd if spin1 DOS is half-transparent
            alphas = {0: 1, 1: 1}
        colors = {0: 'blue', 1: 'red'}
        return (alphas, colors)

class AbstractBandPlot(AbstractPlot):
    def __init__(self, data: DataBands):
        AbstractPlot.__init__(self, data)
        self.types.update([PlotDataType.Bands])

        self.icdv = BandDataDisplayValues(self)

class AbstractDOSPlot(AbstractPlot):
    def __init__(self, data: Data, filepaths_dos: list):
        AbstractPlot.__init__(self, data)
        self.filepaths_dos = filepaths_dos
        if filepaths_dos:
            self.types.update([PlotDataType.DOS_CSV])
        else:
            self.types.update([PlotDataType.DOS_HDF])

        self.icdv = DOSDataDisplayValues(self)

class AbstractBandDOSPlot(AbstractBandPlot, AbstractDOSPlot):
    def __init__(self, data: DataBands, filepaths_dos: list):
        AbstractBandPlot.__init__(self, data)
        AbstractDOSPlot.__init__(self, data, filepaths_dos)

        self.icdv = BandDOSDataDisplayValues(self)


##########################################################################
#####################Section 2: abstract base classes ####################
#####################that define values for interactive###################
#####################controls for plots###################################
##########################################################################


class InteractiveControlDisplayValues(ABC):
    def __init__(self, plotter: AbstractPlot):
        pass

    @abstractmethod
    def convert_selections(self):
        pass


class DOSDataDisplayValues(InteractiveControlDisplayValues):
    def __init__(self, plotter: AbstractDOSPlot):
        InteractiveControlDisplayValues.__init__(self, plotter)

        if (not hasattr(self, 'groups') and (not hasattr(self, 'characters'))):
            self.characters = ['s', 'p', 'd', 'f']
            self.groups = None
            if (PlotDataType.Bands in plotter.types
                    or PlotDataType.DOS_HDF in plotter.types):
                self.groups = plotter.data.atoms_group_keys
            elif (PlotDataType.DOS_CSV in plotter.types):
                (num_groups, num_chars) = get_dos_num_groups_characters(plotter.filepaths_dos[0])
                if (num_groups, num_chars) == (None, None):
                    logging.warn(f"Could not discern num_atom_groups, num_characters "
                                 f"from DOS CSV file {plotter.filepaths_dos[0]}.")
                self.characters = self.characters[:num_chars]
                self.groups = dict.fromkeys(range(1, num_groups + 1)).keys()

    def convert_selections(self, characters=[], groups=[]):
        # convert arguments to the expected format for code 181124
        groups_conved = [el - 1 for el in groups] if groups else []
        characters_conved = [self.characters.index(el) for el in characters] if characters else []

        # convert arguments to the expected format for code 181212
        mask_characters = [el in characters for el in self.characters] if characters else []
        mask_groups = [el in [el for el in groups] for el in self.groups] if groups else []

        return (mask_characters, mask_groups)


class BandDataDisplayValues(InteractiveControlDisplayValues):
    """
    Definitions for user-based data selection controls for interactive band plotting interfaces.
    """

    def __init__(self, plotter: AbstractBandPlot):
        """
        :param plotter: e.g. BandPlot or DOSPlot
        """
        InteractiveControlDisplayValues.__init__(self, plotter)

        if not hasattr(self, 'characters'):
            self.characters = ['s', 'p', 'd', 'f']
        if not hasattr(self, 'groups'):
            self.groups = plotter.data.atoms_group_keys

        SliderSelection = namedtuple('SliderSelection', ['label', 'min', 'max', 'step', 'initial'])
        if not hasattr(self, 'bands'):
            bands = [band for band in range(plotter.data.eigenvalues.shape[2])]
            self.bands = bands
            self.bands_slider = SliderSelection(label="Bands",
                                         min=bands[0]+1,
                                         max=bands[-1]+1,
                                         step=1,
                                         initial=[bands[0]+1, bands[-1]+1])

        if not hasattr(self, 'spins'):
                self.spins = [spin for spin in range(plotter.data.num_spin)]
        if not hasattr(self, 'ylim'):
            ylim = plotter.get_data_ylim()
            self.ylim = SliderSelection(label="y range",
                                        min=ylim[0],
                                        max=ylim[1],
                                        step=(ylim[1] - ylim[0]) / 100,
                                        initial=ylim)
        if not hasattr(self, 'exponent'):
            self.exponent = SliderSelection("Unfolding", 0.0, 4.0, 0.01, 1.0)
        if not hasattr(self, 'marker_size'):
            self.marker_size = SliderSelection("Marker Size", 0.0, 10.0, 0.01, 1.0)

    def convert_selections(self, bands=[], characters=[], groups=[]):
        # convert arguments to the expected format for code 181124
        bands_conved = range(bands[0] - 1, bands[1]) if bands else []
        groups_conved = [el - 1 for el in groups] if groups else []
        characters_conved = [self.characters.index(el) for el in characters] if characters else []

        # convert arguments to the expected format for code 181212
        mask_characters = [el in characters for el in self.characters] if characters else []
        mask_bands = [el in bands_conved for el in self.bands] if bands else []
        mask_groups = [el in [el for el in groups] for el in self.groups] if groups else []

        return (mask_bands, mask_characters, mask_groups)


class BandDOSDataDisplayValues(BandDataDisplayValues, DOSDataDisplayValues):
    """
    Notes
    ----
    Since inherits first from BandData the DOSData, will use inherited
    methods from BandData first if present in both. Example: will use conver_selections()
    of BandDataDisplayValues.
    """

    def __init__(self, plotter: AbstractBandDOSPlot):
        DOSDataDisplayValues.__init__(self, plotter)
        BandDataDisplayValues.__init__(self, plotter)