import numpy as np

from pykml import parser
from pykml.factory import KML_ElementMaker as KML
from os import path
from zipfile import ZipFile
from lxml import etree

RED = 'ff0000ff'
GREEN = 'ff00ff00'
BLUE = 'ffff0000'


def unzip_kmz(kml_file):
    kmz = ZipFile(kml_file)
    kml = kmz.open('doc.kml', 'r').read()
    return kml


def get_node(node_name, child_name, root):
    opengis = '{http://www.opengis.net/kml/2.2}'
    for child in root.iter():
        if child.tag == ''.join([opengis, node_name]):
            if child.name == child_name:
                return child


def get_coordinate(folder_name, placemark_name, root):
    """
        folder_name = access to folder.name in root
        placemark_name = interested placemark in root
        root = kml document start at root node
    """
    folder = get_node('Folder', folder_name, root)
    
    placemark = get_node('Placemark', placemark_name, folder)
    raw_coor = placemark.MultiGeometry.LineString.coordinates.text
    coor_placemark = raw_coor.split(' ')

    print('Current Folder:', folder.name)
    print('Current Placemark:', placemark.name)

    return coor_placemark, raw_coor


def to_ROW_string(coordinates):
    ROW = ''
    for p in coordinates:
        ROW = ROW + ','.join([str(x) for x in p]) + ' '
    return ROW


def get_ROW_offset(coordinates, offset):
    """
        offset, 0.00005 = 5m
    """
    ROW_L, ROW_R = [], []
    for coor in coordinates:
        coor_lla = coor.split(',')
        if not coor_lla:
            continue
        try:
            coor_lla = np.array(coor_lla).astype(np.float64)
            temp_l = coor_lla[0] + offset
            temp_r = coor_lla[0] - offset
            ROW_L.append([temp_l, coor_lla[1], 0])
            ROW_R.append([temp_r, coor_lla[1], 0])
        except ValueError:
            continue 

    ROW_L = np.array(ROW_L).astype(np.str)
    ROW_R = np.array(ROW_R).astype(np.str)

    return to_ROW_string(ROW_L), to_ROW_string(ROW_R)


def placemark_generator(placemark_id, placemark_name, line_color, line_width, coordinates):
    """
        All parameter should be a string, except coordinates is a list of strings
    """
    if placemark_name == 'main':
        multi_geometry = KML.MultiGeometry(KML.LineString(KML.coordinates(coordinates)))
    else:
        multi_geometry = KML.MultiGeometry(
            KML.LineString(KML.coordinates(coordinates[0])),
            KML.LineString(KML.coordinates(coordinates[1]))
        )

    placemark = KML.Placemark(
        KML.name(placemark_name),
        KML.Style(
            KML.LineStyle(
                KML.color(line_color),
                KML.width(line_width)
            )
        ),
        KML.extrude(0),
        multi_geometry,
        id=placemark_id
    )

    return placemark



def route_folder_generator(root, placemark_name, ROW_offset, buffer_offset):
    route, raw_route = get_coordinate('MainPipeline', placemark_name, root)
    ROW_L, ROW_R = get_ROW_offset(route, ROW_offset)
    buffer_L, buffer_R = get_ROW_offset(route, buffer_offset)
    pm_main = placemark_generator('000', 'main', GREEN, 4, raw_route)
    pm_ROW = placemark_generator('001', 'ROW', BLUE, 4, [ROW_L, ROW_R])
    pm_buffer = placemark_generator('002', 'buffer', RED, 4, [buffer_L, buffer_R])
    folder_kml = KML.Folder(
        KML.name(placemark_name),
        pm_main,
        pm_ROW,
        pm_buffer 
    )

    return folder_kml


        



if __name__ == '__main__':
    with open('./data/sample.kml') as kml:
        root = parser.parse(kml).getroot()

    with open('./processed_data/route_ICS.kml', 'w') as f:
        doc = KML.kml(
            KML.Document(
                KML.name('ICS Modified'),
                route_folder_generator(root, 'RC6700', 0.000025, 0.00005),
                route_folder_generator(root, 'RC6800', 0.000025, 0.00005),
                route_folder_generator(root, 'RC0690', 0.00004, 0.00005),
                route_folder_generator(root, 'RC0660', 0.00004, 0.00005),
                route_folder_generator(root, 'RC063601', 0.00002, 0.00005),
                route_folder_generator(root, 'RC0664', 0.00004, 0.00005),
                route_folder_generator(root, 'RC0400', 0.00010, 0.00005),
                route_folder_generator(root, 'RC0460', 0.00011, 0.00005),
                route_folder_generator(root, 'RC5600', 0.00010, 0.00005),
                route_folder_generator(root, 'RC0430', 0.000025, 0.00005),
                route_folder_generator(root, 'RC4900', 0.00010, 0.00005),
                route_folder_generator(root, 'RC5610', 0.000025, 0.00005),
            )
        )
        f.write(etree.tostring(doc, pretty_print=True))
    f.close()


   
    
