import numpy as np
from os.path import dirname, join
import pandas as pd

from analysis import Analysis
from ..core.status import Status
from ..reporting.plots import MatplotlibPlotter


class SensitivityAnalysis(Analysis):

    def __init__(self, analysis_config):

        Analysis.__init__(self, analysis_config)

        self.powerCurveSensitivityResults = {}
        self.powerCurveSensitivityVariationMetrics = pd.DataFrame(columns=['Power Curve Variation Metric'])

        self.calculate_sensitivity_analysis()
        self.calculate_scatter_metric()

        Status.add("Complete.")

    def export_sensitivity_plots(self, path):

        if not self.hasActualPower:
            return

        plotter = MatplotlibPlotter(path, self)

        if len(self.powerCurveSensitivityResults.keys()) > 0:
            for sensCol in self.powerCurveSensitivityResults.keys():
                plotter.plotPowerCurveSensitivity(sensCol)

            plotter.plotPowerCurveSensitivityVariationMetrics()

    def report(self, path):

        Analysis.report(self, path)
        self.export_sensitivity_plots(join(dirname(path), 'Sensitivity Analysis Plots'))

    def export_time_series(self, path, **kwargs):

        Analysis.export_time_series(self, path, **kwargs)
        self.export_sensitivity_plots(join(dirname(path), 'Sensitivity Analysis Plots'))

    def calculate_sensitivity_analysis(self):

        sens_pow_curve = self.allMeasuredTurbCorrectedPowerCurve if self.turbRenormActive else self.allMeasuredPowerCurve
        sens_pow_column = self.measuredTurbulencePower if self.turbRenormActive else self.actualPower
        sens_pow_interp_column = self.measuredTurbPowerCurveInterp if self.turbRenormActive else self.measuredPowerCurveInterp
        self.interpolatePowerCurve(sens_pow_curve, self.baseline_wind_speed, sens_pow_interp_column)
        Status.add("Attempting power curve sensitivty analysis for %s power curve..." % sens_pow_curve.name)
        self.perform_sensitivity_analysis(sens_pow_curve, sens_pow_column, sens_pow_interp_column)

    def calculate_scatter_metric(self):

        if self.hasActualPower:
            self.powerCurveScatterMetric = self.calculatePowerCurveScatterMetric(self.allMeasuredPowerCurve,
                                                                                 self.actualPower, self.dataFrame.index)
            self.dayTimePowerCurveScatterMetric = self.calculatePowerCurveScatterMetric(self.dayTimePowerCurve,
                                                                                        self.actualPower,
                                                                                        self.dataFrame.index[
                                                                                            self.get_day_filter()])
            self.nightTimePowerCurveScatterMetric = self.calculatePowerCurveScatterMetric(self.nightTimePowerCurve,
                                                                                          self.actualPower,
                                                                                          self.dataFrame.index[
                                                                                              self.get_night_filter()])
            if self.turbRenormActive:
                self.powerCurveScatterMetricAfterTiRenorm = self.calculatePowerCurveScatterMetric(
                    self.allMeasuredTurbCorrectedPowerCurve, self.measuredTurbulencePower, self.dataFrame.index)
            self.powerCurveScatterMetricByWindSpeed = self.calculateScatterMetricByWindSpeed(self.allMeasuredPowerCurve,
                                                                                             self.actualPower)
            if self.turbRenormActive:
                self.powerCurveScatterMetricByWindSpeedAfterTiRenorm = self.calculateScatterMetricByWindSpeed(
                    self.allMeasuredTurbCorrectedPowerCurve, self.measuredTurbulencePower)
            self.iec_2005_cat_A_power_curve_uncertainty()

    def perform_sensitivity_analysis(self, power_curve, power_column, interp_pow_column, n_random_tests=20):

        mask = self.get_base_filter()
        filteredDataFrame = self.dataFrame[mask]

        # calculate significance threshold based on generated random variable
        rand_columns, rand_sensitivity_results = [], []

        for i in range(n_random_tests):
            rand_columns.append('Random ' + str(i + 1))

        filteredDataFrame = filteredDataFrame.join(
            pd.DataFrame(np.random.rand(len(filteredDataFrame), n_random_tests), columns=rand_columns,
                         index=filteredDataFrame.index), how='inner')

        for col in rand_columns:
            variation_metric = self.calculatePowerCurveSensitivity(filteredDataFrame, power_curve, col, power_column,
                                                                   interp_pow_column)[1]
            rand_sensitivity_results.append(variation_metric)

        self.sensitivityAnalysisThreshold = np.mean(rand_sensitivity_results)

        message = "\nSignificance threshold for power curve variation metric is %.2f%%."
        Status.add(message % (self.sensitivityAnalysisThreshold * 100.), verbosity=2)
        filteredDataFrame.drop(rand_columns, axis=1, inplace=True)

        # sensitivity to time of day, time of year, time elapsed in test
        filteredDataFrame.loc[:, 'Days Elapsed In Test'] = (filteredDataFrame[self.timeStamp] -
                                                            filteredDataFrame[self.timeStamp].min()).dt.days
        filteredDataFrame.loc[:, 'Hours From Noon'] = np.abs(filteredDataFrame[self.timeStamp].dt.hour - 12)
        filteredDataFrame.loc[:, 'Hours From Midnight'] = np.minimum(filteredDataFrame[self.timeStamp].dt.hour,
                                                                     np.abs(24 -
                                                                            filteredDataFrame[self.timeStamp].dt.hour))
        filteredDataFrame.loc[:, 'Days From 182nd Day Of Year'] = np.abs(filteredDataFrame[self.timeStamp].dt.dayofyear
                                                                         - 182)
        filteredDataFrame.loc[:, 'Days From December Solstice'] = filteredDataFrame[self.timeStamp].apply(
            lambda x: x.replace(day=22, month=12)) - filteredDataFrame[self.timeStamp]
        filteredDataFrame.loc[:, 'Days From December Solstice'] = np.minimum(
            np.abs(filteredDataFrame['Days From December Solstice'].dt.days),
            365 - np.abs(filteredDataFrame['Days From December Solstice'].dt.days))

        for col in self._get_sensitivity_analysis_columns():
            Status.add("\nAttempting to compute sensitivity of power curve to %s..." % col, verbosity=2)
            try:
                results_df, variation_metric = self.calculatePowerCurveSensitivity(filteredDataFrame, power_curve, col,
                                                                                   power_column, interp_pow_column)
                if (not np.isnan(variation_metric)) and (variation_metric != 0):
                    self.powerCurveSensitivityResults[col] = results_df
                    self.powerCurveSensitivityVariationMetrics.loc[col, 'Power Curve Variation Metric'] = variation_metric
                message = "Variation of power curve with respect to %s is %.2f%%."
                Status.add(message % (col,variation_metric * 100.), verbosity=2)
            except Exception as e:
                Status.add("Could not run sensitivity analysis for %s." % col, verbosity=2)
                Status.add("Exception: {0}".format(e), verbosity=3)

        self.powerCurveSensitivityVariationMetrics.loc['Significance Threshold', 'Power Curve Variation Metric'] = \
            self.sensitivityAnalysisThreshold
        self.powerCurveSensitivityVariationMetrics.sort('Power Curve Variation Metric', ascending=False, inplace=True)

    def calculatePowerCurveSensitivity(self, dataFrame, power_curve, dataColumn, power_column, interp_pow_column):

        dataFrame.loc[:, 'Energy MWh'] = (dataFrame[power_column] * (float(self.timeStepInSeconds) / 3600.)).astype(
            'float')

        from collections import OrderedDict
        self.sensitivityLabels = OrderedDict(
            [("V Low", "#0000ff"), ("Low", "#4400bb"), ("Medium", "#880088"), ("High", "#bb0044"),
             ("V High", "#ff0000")])  # categories to split data into using data_column and colour to plot
        cutOffForCategories = list(np.arange(0., 1., 1. / len(self.sensitivityLabels.keys()))) + [1.]

        minCount = len(
            self.sensitivityLabels.keys()) * 4  # at least 4 data points for each category for a ws bin to be valid

        wsBinnedCount = dataFrame[['Wind Speed Bin', dataColumn]].groupby('Wind Speed Bin').count()
        validWsBins = wsBinnedCount.index[
            wsBinnedCount[dataColumn] > minCount]  # ws bins that have enough data for the sensitivity analysis

        dataFrame.loc[:, 'Bin'] = np.nan  # pre-allocating
        dataFrame.loc[:, 'Power Delta kW'] = dataFrame[power_column] - dataFrame[interp_pow_column]
        dataFrame.loc[:, 'Energy Delta MWh'] = dataFrame['Power Delta kW'] * (float(self.timeStepInSeconds) / 3600.)

        for wsBin in dataFrame[
            'Wind Speed Bin'].unique():  # within each wind speed bin, bin again by the categorising by sensCol
            if wsBin in validWsBins:
                try:
                    filt = dataFrame['Wind Speed Bin'] == wsBin
                    dataFrame.loc[filt, 'Bin'] = pd.qcut(dataFrame[dataColumn][filt], cutOffForCategories,
                                                         labels=self.sensitivityLabels.keys())
                except:
                    Status.add("\tCould not categorise data by %s for WS bin %s." % (dataColumn, wsBin), verbosity=3)

        sensitivityResults = dataFrame[
            [power_column, 'Energy MWh', 'Wind Speed Bin', 'Bin', 'Power Delta kW', 'Energy Delta MWh']].groupby(
            ['Wind Speed Bin', 'Bin']).agg(
            {power_column: np.mean, 'Energy MWh': np.sum, 'Wind Speed Bin': len, 'Power Delta kW': np.mean,
             'Energy Delta MWh': np.sum})

        return sensitivityResults.rename(columns={'Wind Speed Bin': 'Data Count'}), np.abs(
            sensitivityResults['Energy Delta MWh']).sum() / (
               power_curve.data_frame[power_column] * power_curve.data_frame['Data Count'] * (
               float(self.timeStepInSeconds) / 3600.)).sum()

    def calculateScatterMetricByWindSpeed(self, measuredPowerCurve, powerColumn):
        index = self.dataFrame[self.windSpeedBin].unique()
        index.sort()
        df = pd.DataFrame(index=index, columns=['Scatter Metric'])
        for ws in df.index:
            if ws >= measuredPowerCurve.cutInWindSpeed:
                rows = self.dataFrame[self.baseline_wind_speed] == ws
                df.loc[ws, 'Scatter Metric'] = self.calculatePowerCurveScatterMetric(measuredPowerCurve, powerColumn,
                                                                                     rows)
        return df.dropna()

    def _get_sensitivity_analysis_columns(self):
        cols = ['Days From December Solstice', 'Hours From Noon', 'Days Elapsed In Test']
        if self.hasDensity:
            cols.append(self.hubDensity)
        if self.hasShear:
            cols.append(self.shearExponent)
        if self.hasDirection:
            cols.append(self.windDirection)
        if self.hasTurbulence:
            cols.append(self.hubTurbulence)
        if self.inflowAngle in self.dataFrame.columns:
            cols.append(self.inflowAngle)
        for dataset_config in self.datasetConfigs:
            cols += dataset_config.additional_sensitivity_analysis_cols
        return cols
