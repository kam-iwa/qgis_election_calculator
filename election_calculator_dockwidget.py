# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ElectionCalculatorDockWidget
                                 A QGIS plugin
 Election calculator plugin with different electoral systems
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2025-02-11
        git sha              : $Format:%H$
        copyright            : (C) 2025 by Kamil Iwaniuk
        email                : iwaniukkamil@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
from enum import Enum

from qgis.core import (Qgis, QgsMapLayer, QgsMapLayerProxyModel, QgsFieldProxyModel, QgsAggregateCalculator, QgsVectorLayer,
                       QgsProject, QgsFeature, QgsField)
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtWidgets import QTableWidgetItem
from qgis.PyQt.QtCore import pyqtSignal, Qt, QVariant
from qgis.utils import iface

from .election_calculator_methods import ElectionCalculatorSeatsDistributor

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'election_calculator_dockwidget_base.ui'))


class ElectionCalculatorMethod(Enum):
    DHONDT = 0
    SAINTE_LAGUE = 1
    SAINTE_LAGUE_SCANDINAVIAN = 2
    HARE_NIEMEYER = 3


class ElectionCalculatorDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(ElectionCalculatorDockWidget, self).__init__(parent)
        self.setupUi(self)
        self._init_ui()
        self._init_signals()

    def signal_on_dataLayerComboBox_layer_changed(self, layer):
        if layer is not None:
            field_names = [f.name() for f in layer.fields() if f.typeName() in ["Integer", "Integer64"]]

            self.voteCountComboBox.clear()
            self.voteCountComboBox.addItems(field_names)
            self.constituencyVoteCountComboBox.setLayer(layer)

        else:
            self.voteCountComboBox.clear()
            self.constituencyVoteCountComboBox.setLayer(None)

    def signal_on_voteCountComboBox_fields_changed(self, fields):
        self.multiThresholdTableWidget.clear()
        self.multiThresholdTableWidget.setRowCount(len(fields))
        for idx, field in enumerate(fields):
            self.multiThresholdTableWidget.setItem(idx, 0, QTableWidgetItem(field))
            self.multiThresholdTableWidget.item(idx, 0).setFlags(Qt.NoItemFlags)
            self.multiThresholdTableWidget.setItem(idx, 1, QTableWidgetItem('0'))

    def signal_on_thresholdCheckBox_check_state_changed(self, checked):
        if checked:
            self.oneThresholdWidget.setEnabled(True)
            self.oneThresholdWidget.setVisible(True)

            self.multiThresholdWidget.setEnabled(True)
            self.multiThresholdWidget.setVisible(True)
        else:
            self.oneThresholdWidget.setEnabled(False)
            self.oneThresholdWidget.setVisible(False)

            self.multiThresholdWidget.setEnabled(False)
            self.multiThresholdWidget.setVisible(False)

    def signal_on_radioButton_change_clicked(self, id: int):
        if id == 0:
            self.oneThresholdSpinBox.setEnabled(True)
            self.multiThresholdTableWidget.setEnabled(False)
        else:
            self.oneThresholdSpinBox.setEnabled(False)
            self.multiThresholdTableWidget.setEnabled(True)

    def signal_on_executeButton_run(self):
        input_layer = self.dataLayerComboBox.currentLayer()
        seats_count_field = self.constituencyVoteCountComboBox.currentField()

        parties_fields = self.voteCountComboBox.checkedItems()
        parties_fields_count = len(parties_fields)
        if parties_fields_count == 0:
            iface.messageBar().pushMessage("Warning", "Too few selected columns with number of votes", level=Qgis.Warning)
            return

        votes_total_by_party = {party_field: 0 for party_field in parties_fields}
        votes_total = 0

        for party_field in parties_fields:
            votes_party = input_layer.aggregate(QgsAggregateCalculator.Sum, party_field)[0]
            votes_total_by_party[party_field] = votes_party
            votes_total += (votes_party if votes_party is not None else 0)

        threshold = self._execute_calculate_threshold(parties_fields_count)
        if not threshold:
            iface.messageBar().pushMessage("Warning", "The value of the election threshold must be a integer", level=Qgis.Warning)
            return

        parties_above_threshold = self._execute_get_parties_above_threshold(threshold, votes_total, votes_total_by_party, parties_fields)
        if len(parties_above_threshold) == 0:
            iface.messageBar().pushMessage("Warning", "No party exceeds the stated electoral threshold. Set a different electoral threshold", level=Qgis.Warning)
            return

        method = self.methodComboBox.currentIndex()
        seats_distributor = ElectionCalculatorSeatsDistributor(input_layer, parties_above_threshold, seats_count_field)

        if method == ElectionCalculatorMethod.DHONDT.value:
            calculation_result = seats_distributor.calculate(seats_distributor.dhondt2)
        elif method == ElectionCalculatorMethod.SAINTE_LAGUE.value:
            calculation_result = seats_distributor.calculate(seats_distributor.sainte_lague)
        elif method == ElectionCalculatorMethod.SAINTE_LAGUE_SCANDINAVIAN.value:
            calculation_result = seats_distributor.calculate(seats_distributor.sainte_lague_scandinavian)
        elif method == ElectionCalculatorMethod.HARE_NIEMEYER.value:
            calculation_result = seats_distributor.calculate(seats_distributor.hare_niemeyer)
        else:
            iface.messageBar().pushMessage("Warning", "Incorrect method of counting seats", level=Qgis.Warning)
            return

        if calculation_result is None:
            iface.messageBar().pushMessage("Warning", "The number of seats to be distributed in each constituence must be at least 1", level=Qgis.Warning)
            return

        self._execute_create_output_layer(input_layer, parties_above_threshold, calculation_result)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def _init_ui(self):
        self.dataLayerComboBox.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.constituencyVoteCountComboBox.setFilters(QgsFieldProxyModel.Numeric)

        self.groupRadioButtons = QtWidgets.QButtonGroup()
        self.groupRadioButtons.addButton(self.oneThresholdRadioButton, 0)
        self.groupRadioButtons.addButton(self.multiThresholdRadioButton, 1)

        self.oneThresholdWidget.setEnabled(False)
        self.oneThresholdWidget.setVisible(False)
        self.oneThresholdRadioButton.setChecked(True)
        self.oneThresholdSpinBox.setEnabled(True)

        self.multiThresholdTableWidget.clear()
        self.multiThresholdTableWidget.setHorizontalHeaderLabels(["Field", "Threshold values"])
        self.multiThresholdWidget.setEnabled(False)
        self.multiThresholdWidget.setVisible(False)
        self.multiThresholdTableWidget.setEnabled(False)

    def _init_signals(self):
        self.dataLayerComboBox.layerChanged.connect(self.signal_on_dataLayerComboBox_layer_changed)
        self.voteCountComboBox.checkedItemsChanged.connect(self.signal_on_voteCountComboBox_fields_changed)
        self.thresholdCheckBox.stateChanged.connect(self.signal_on_thresholdCheckBox_check_state_changed)
        self.groupRadioButtons.idClicked.connect(self.signal_on_radioButton_change_clicked)

        self.executeButton.pressed.connect(self.signal_on_executeButton_run)

        self.signal_on_dataLayerComboBox_layer_changed(self.dataLayerComboBox.currentLayer())

    def _execute_calculate_threshold(self, parties_count: int):
        if self.thresholdCheckBox.isChecked():
            threshold_type = self.groupRadioButtons.checkedId()
            if threshold_type == 0:
                threshold = ('single', self.oneThresholdSpinBox.value())
            else:
                thresholds_values = []

                for idx in range(0, parties_count):
                    try:
                        value = int(self.multiThresholdTableWidget.item(idx, 1).text())
                    except ValueError:
                        return None

                    thresholds_values.append(value)

                threshold = ('multi', thresholds_values)
        else:
            threshold = ('single', 0)

        return threshold

    def _execute_get_parties_above_threshold(self, threshold, votes_total, votes_total_by_party, parties_fields):
        parties_above_threshold = []
        if threshold[0] == 'single':
            for current_party, current_votes in votes_total_by_party.items():

                if ((current_votes / votes_total) * 100) >= threshold[1]:
                    parties_above_threshold.append(current_party)
        else:
            for current_party, current_votes in votes_total_by_party.items():
                current_threshold_id = parties_fields.index(current_party)
                current_threshold = threshold[1][current_threshold_id]

                if ((current_votes / votes_total) * 100)  >= current_threshold:
                    parties_above_threshold.append(current_party)

        return parties_above_threshold

    def _execute_create_output_layer(self, input_layer: QgsMapLayer, parties_above_threshold: list, calculation_result: dict):
        output_layer = QgsVectorLayer(input_layer.geometryType().name, "results_" + input_layer.name(), "memory")
        output_layer.setCrs(input_layer.crs())
        output_provider = output_layer.dataProvider()

        new_fields = []
        for party_column in parties_above_threshold:
            new_fields.append(
                QgsField(f"RESULTS_{party_column}", QVariant.Int)
            )

        output_provider.addAttributes(list(input_layer.fields()) + new_fields)
        output_layer.updateFields()

        output_features = []
        for feature in input_layer.getFeatures():
            output_feature = QgsFeature()
            output_feature.setFields(output_layer.fields())
            output_feature.setGeometry(feature.geometry())

            attributes = []
            for attr in feature.attributes():
                attributes.append(attr)

            output_results = calculation_result[feature.id()]
            for i in range(0, len(parties_above_threshold)):
                try:
                    attributes.append(output_results[i])
                except KeyError:
                    attributes.append(0)

            output_feature.setAttributes(attributes)
            output_features.append(output_feature)

        output_layer.dataProvider().addFeatures(output_features)

        QgsProject.instance().addMapLayer(output_layer)
