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
    folder = get_node('Folder', folder_name, root)
    print(folder.name)
    
    placemark = get_node('Placemark', placemark_name, folder)
    raw_coor = placemark.MultiGeometry.LineString.coordinates.text
    coor_placemark = raw_coor.split(' ')
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
        



if __name__ == '__main__':
    with open('./data/sample.kml') as kml:
        root = parser.parse(kml).getroot()

    RC6700, raw_RC6700 = get_coordinate('MainPipeline', 'RC6700', root)
    ROW_L, ROW_R = get_ROW_offset(RC6700, 0.000025)
    buffer_L, buffer_R = get_ROW_offset(RC6700, 0.00005)


    pm_main = KML.Placemark(
        KML.name('main'),
        KML.Style(
            KML.LineStyle(
                KML.color(GREEN),
                KML.width('4')
            )
        ),
        KML.extrude(0),
        KML.MultiGeometry(
            KML.LineString(
                KML.coordinates(raw_RC6700)
            )
        ),
        id='000'
    )

    pm_ROW = KML.Placemark(
        KML.name('ROW'),
        KML.Style(
            KML.LineStyle(
                KML.color(BLUE),
                KML.width('4')
            )
        ),
        KML.extrude(0),
        KML.MultiGeometry(
            KML.LineString(
                KML.coordinates(ROW_R)
            ),
            KML.LineString(
                KML.coordinates(ROW_L)
            )
        ),
        id='001'
    )


    pm_buffer = KML.Placemark(
        KML.name('Buffer'),
        KML.Style(
            KML.LineStyle(
                KML.color(RED),
                KML.width('4')
            )
        ),
        KML.extrude(0),
        KML.MultiGeometry(
            KML.LineString(
                KML.coordinates(buffer_R)
            ),
            KML.LineString(
                KML.coordinates(buffer_L)
            )
        ),
        id='002'
    )

    with open('./processed_data/RC6700_ICS.kml', 'w') as f:
        doc = KML.kml(
            KML.Document(
                KML.name('ICS Modified'),
                KML.Folder(
                    KML.name('RC6700'),
                    pm_main,
                    pm_ROW,
                    pm_buffer
                )
            )
        )
        f.write(etree.tostring(doc, pretty_print=True))
    f.close()


   
    
