# -*- coding: utf-8 -*-
"""
Created on Wed Aug 10 14:42:45 2016

@author: Stuart
"""

import Tkinter as tk
import ttk

from tk_simple_dialog import Dialog

from ..visualisation.generic import generic_histogram, hour_of_day_histogam

from ..visualisation.power_curve import PowerCurvePlotter

from ..visualisation.turbulence import TurbulenceByDirection
from ..visualisation.turbulence import TurbulenceBySpeed
from ..visualisation.turbulence import TurbulenceByShear

from ..visualisation.shear import ShearByDirection
from ..visualisation.shear import ShearBySpeed

from ..visualisation.power_coefficient import PowerCoefficientBySpeed

from ..core.status import Status

class VisualisationDialogFactory:

    def __init__(self, analysis):
        self.analysis = analysis

    def new_visualisaton(self, visualisation):

        if visualisation == "Power Curve":
        
            plotter = PowerCurvePlotter(self.analysis)

            plotter.plot(self.analysis.baseline.wind_speed_column,
                            self.analysis.actualPower,
                            self.analysis.allMeasuredPowerCurve,
                            specified_title = 'Warranted',
                            mean_title = 'Measured Mean',
                            gridLines = True)

        elif visualisation == "Turbulence by Direction":

            if not self.analysis.hasDirection:
                Status.add("Cannot plot turbulence by direction: analysis does not have direction defined", red=True)
                return

            plotter = TurbulenceByDirection(self.analysis)
            plotter.plot()

        elif visualisation == "Turbulence by Speed":

            plotter = TurbulenceBySpeed(self.analysis)
            plotter.plot()

        elif visualisation == "Turbulence by Shear":

            if not self.analysis.hasShear:
                Status.add("Cannot plot turbulence by shear: analysis does not have shear", red=True)
                return

            plotter = TurbulenceByShear(self.analysis)
            plotter.plot()

        elif visualisation == "Shear by Direction":

            if not self.analysis.hasShear:
                Status.add("Cannot plot shear by direction: analysis does not have shear", red=True)
                return

            if not self.analysis.hasDirection:
                Status.add("Cannot plot turbulence by direction: analysis does not have direction defined", red=True)
                return

            plotter = ShearByDirection(self.analysis)
            plotter.plot()

        elif visualisation == "Shear by Speed":

            if not self.analysis.hasShear:
                Status.add("Cannot plot shear by speed: analysis does not have shear", red=True)
                return

            plotter = ShearBySpeed(self.analysis)
            plotter.plot()

        elif visualisation == "Power Coefficient by Speed":

            plotter = PowerCoefficientBySpeed(self.analysis)
            plotter.plot()

        elif visualisation == "TI Corrected Power Curve":

            if not self.analysis.turbRenormActive:
                Status.add("TI correction is not active; cannot plot TI corrected power curve.")
                return
            elif not self.analysis.hasTurbulence:
                Status.add("TI is not defined; cannot plot TI corrected power curve.")
                return
            plotter = PowerCurvePlotter(analysis=self.analysis)
            plotter.plot(self.analysis.baseline.wind_speed_column,
                         self.analysis.measuredTurbulencePower,
                         self.analysis.allMeasuredTurbCorrectedPowerCurve,
                         specified_title='Warranted',
                         mean_title='Measured Mean (TI Corrected)',
                         gridLines=True)

        elif visualisation == 'Wind Speed Histogram':
            generic_histogram(self.analysis.dataFrame, self.analysis.baseline.wind_speed_column, unit='m/s')

        elif visualisation == 'TI Histogram':
            if not self.analysis.hasTurbulence:
                Status.add("TI not defined. Cannot plot TI histogram.")
                return
            generic_histogram(self.analysis.dataFrame, self.analysis.hubTurbulence)

        elif visualisation == 'Shear Histogram':
            if not self.analysis.hasShear:
                Status.add("Shear not defined. Cannot plot shear exponent histogram.")
                return
            generic_histogram(self.analysis.dataFrame, self.analysis.shearExponent)

        elif visualisation == 'Density Histogram':
            if not self.analysis.hasDensity:
                Status.add("Density not defined. Cannot plot shear exponent histogram.")
                return
            generic_histogram(self.analysis.dataFrame, self.analysis.hubDensity, unit=r'$kg/m^{3}$')

        elif visualisation == 'Wind Direction Histogram':
            if not self.analysis.hasDirection:
                Status.add("Wind Direction not defined. Cannot plot wind direction histogram.")
                return
            generic_histogram(self.analysis.dataFrame, self.analysis.windDirection, unit='deg')

        elif visualisation == 'Hour of Day Histogram':
            hour_of_day_histogam(self.analysis.dataFrame)

        else:
            raise Exception("Unknown visualation: {0}".format(visualisation))
