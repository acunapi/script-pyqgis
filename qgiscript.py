from qgis.core import (QgsProject, QgsVectorLayer, QgsFeature, QgsPointXY, QgsGeometry,
                       QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsLayout,
                       QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutItemPicture,
                       QgsLayoutExporter, QgsLayoutPoint, QgsLayoutSize)
from qgis.analysis import QgsGeometryAnalyzer
from PyQt5.QtWidgets import (QFileDialog, QApplication, QDialog, QGridLayout, QLabel,
                             QLineEdit, QPushButton)

def get_input_params():
    """Prompts the user to enter the input parameters for the affected area map."""
    app = QApplication([])
    dialog = QDialog()
    dialog.setWindowTitle("Affected Area Map")
    layout = QGridLayout(dialog)

    # Geopackage file path
    gpkg_label = QLabel("Geopackage file path:")
    layout.addWidget(gpkg_label, 0, 0)
    gpkg_line_edit = QLineEdit()
    layout.addWidget(gpkg_line_edit, 0, 1)
    gpkg_button = QPushButton("Browse")
    layout.addWidget(gpkg_button, 0, 2)

    # Incident location X coordinate
    incident_x_label = QLabel("Incident location X coordinate:")
    layout.addWidget(incident_x_label, 1, 0)
    incident_x_line_edit = QLineEdit()
    layout.addWidget(incident_x_line_edit, 1, 1)

    # Incident location Y coordinate
    incident_y_label = QLabel("Incident location Y coordinate:")
    layout.addWidget(incident_y_label, 2, 0)
    incident_y_line_edit = QLineEdit()
    layout.addWidget(incident_y_line_edit, 2, 1)

    # Buffer radius
    buffer_label = QLabel("Buffer radius (m):")
    layout.addWidget(buffer_label, 3, 0)
    buffer_line_edit = QLineEdit()
    layout.addWidget(buffer_line_edit, 3, 1)

    # OK and cancel buttons
    ok_button = QPushButton("OK")
    layout.addWidget(ok_button, 4, 1)
    cancel_button = QPushButton("Cancel")
    layout.addWidget(cancel_button, 4, 2)

    def browse_for_gpkg():
        """Opens a file dialog to browse for the geopackage file."""
        file_path, _ = QFileDialog.getOpenFileName(dialog, "Open Geopackage", "", "Geopackage files (*.gpkg)")
        if file_path:
            gpkg_line_edit.setText(file_path)

    def ok_clicked():
        """Closes the dialog and returns the input parameters."""
        gpkg_path = gpkg_line_edit.text()
        incident_x = float(incident_x_line_edit.text())
        incident_y = float(incident_y_line_edit.text())
        buffer_radius = float(buffer_line_edit.text())
        dialog.close()
        app.exit(0)
        return gpkg_path, incident_x, incident_y, buffer_radius

    gpkg_button.clicked.connect(browse_for_gpkg)
    ok_button.clicked.connect(ok_clicked)
    cancel_button.clicked.connect(dialog.reject)
    dialog.exec_()

def generate_affected_area_map():
    # Get the input parameters from the user
    gpkg_path, incident_x, incident_y, buffer_radius = get_input_params()

    # Load the municipalities layer
    municipalities_layer = QgsVectorLayer(gpkg_path + "|layername=datos_p5 - municipios", "municipalities", "ogr")
    QgsProject.instance().addMapLayer(municipalities_layer)

    # Create a point geometry for the incident location
    incident_point = QgsPointXY(incident_x, incident_y)
    incident_geometry = QgsGeometry.fromPointXY(incident_point)

        # Generate buffer around the incident location
    buffer = incident_geometry.buffer(buffer_radius, 5)
    buffer_layer = QgsVectorLayer("Polygon?crs=EPSG:25831", "affected_area", "memory")
    QgsProject.instance().addMapLayer(buffer_layer)

    # Add the buffer to the buffer layer
    buffer_layer.startEditing()
    buffer_feature = QgsFeature()
    buffer_feature.setGeometry(buffer)
    buffer_layer.addFeature(buffer_feature)
    buffer_layer.commitChanges()

    # Insert the buffer layer above the municipalities layer
    QgsProject.instance().layerTreeRoot().insertChildNode(2, QgsLayerTreeLayer(buffer_layer))

    # Clip the municipalities layer with the buffer
    clipped_layer = QgsVectorLayer("Polygon?crs=EPSG:25831", "clipped_municipalities", "memory")
    QgsGeometryAnalyzer().intersection(municipalities_layer, buffer_layer, clipped_layer)

    # Calculate the total affected population
    total_population = 0
    for feature in clipped_layer.getFeatures():
        total_population += feature["población"]

    # Set up the map composition
    layout = QgsLayout(QgsProject.instance())
    layout.initializeDefaults()

    # Add the map item
    map_item = QgsLayoutItemMap(layout)
    map_item.setExtent(buffer.boundingBox())
    map_item.attemptMove(QgsLayoutPoint(20, 20))
    map_item.attemptResize(QgsLayoutSize(180, 180))
    layout.addItem(map_item)

    # Add the title
    map_title = "Incident Affected Area"
    title_item = QgsLayoutItemLabel(layout)
    title_item.setText(map_title)
    title_item.adjustSizeToText()
    title_item.attemptMove(QgsLayoutPoint(20, 200))
    layout.addItem(title_item)

    # Add the orientation arrow
    arrow_item = QgsLayoutItemPicture(layout)
    arrow_item.setPicturePath("path/to/arrow_image.svg")
    arrow_item.attemptMove(QgsLayoutPoint(160, 200))
    arrow_item.attemptResize(QgsLayoutSize(20, 20))
    layout.addItem(arrow_item)

    # Add the affected population text
    population_item = QgsLayoutItemLabel(layout)
    population_item.setText(f"Affected population: {total_population}")
    population_item.adjustSizeToText()
    population_item.attemptMove(QgsLayoutPoint(20, 220))
    layout.addItem(population_item)

    # Export the layout to a PDF file
    output_file_path, _ = QFileDialog.getSaveFileName(None, "Save PDF", "", "PDF files (*.pdf)")
    if output_file_path:
        exporter = QgsLayoutExporter(layout)
        exporter.exportToPdf(output_file_path, QgsLayoutExporter.PdfExportSettings())

# Call the function to generate the affected area map
generate_affected_area_map()

