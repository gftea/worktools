"""
The script extract cells and routes data from TMA raw script and 
generate Campaign xml file which can be imported to TMA E500.
When importing the generated file from TMA, please uncheck all options.

ekaiqch 2016-08-02
"""

from xml.etree import ElementTree as ET
from xml.etree.ElementTree import ElementTree
from argparse import ArgumentParser
import re
import os, sys



if sys.version_info[0:3] < (3,4,3):
    exit("Python version should be >= 3.4.3")


class RootElem(object):
    root_template = '''\
<?xml version="1.0" encoding="utf-16"?>
<!-- TMA LOADSYS Campaign Version 0 -->
<Campaign xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <CampaignFormatVersion>1</CampaignFormatVersion>
    <IsUnFrozen>true</IsUnFrozen>
    <CampaignName>MyCampaign</CampaignName>
    <RouteSetAndENBConfig>
        <ConfigName>Stability</ConfigName>
        <eNodeBs>
        </eNodeBs>
        <RouteSet>
        </RouteSet>
    </RouteSetAndENBConfig>  
</Campaign>
'''
    def __init__(self, name):
        self.__elem = ET.fromstring(RootElem.root_template)
        # below is workaround for namespace handling
        self.__elem.set('xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")
        self.__elem.set('xmlns:xsd', "http://www.w3.org/2001/XMLSchema")
        self.__elem.find('./CampaignName').text = name
        
    def addEnb(self, enb):
        self.__elem.find(".//eNodeBs").append(enb.getElem())
    
    def addRoute(self, route):
        self.__elem.find(".//RouteSet").append(route.getElem())
    
    def getElem(self):
        return self.__elem


class EnbElem(object):
    enbconfig_template = '''\
<eNBConfig>
    <eNodeBName>eNB_1</eNodeBName>
    <Center>
        <X>0</X>
        <Y>0</Y>
    </Center>
    <Cells>
    </Cells>
</eNBConfig>
'''
    def __init__(self, enb_id, x, y):
        self.__elem = ET.fromstring(EnbElem.enbconfig_template)
        self.__elem.find("./eNodeBName").text = "eNB_" + str(enb_id) 
        self.__elem.find(".//X").text = x
        self.__elem.find(".//Y").text = y

    def addCell(self, cell):
        self.__elem.find(".//Cells").append(cell.getElem())

    def getElem(self):
        return self.__elem
        
class CellElem(object):
    cell_template = '''\
<Transmitter>
    <Radius>200</Radius>
    <StartAngle>0</StartAngle>
    <EndAngle>120</EndAngle>
    <CellId>0</CellId>
</Transmitter>
'''
    def __init__(self, cid, radius, start, end):
        self.__elem = ET.fromstring(CellElem.cell_template)
        self.__elem.find(".//CellId").text = cid
        self.__elem.find(".//Radius").text = radius
        self.__elem.find(".//StartAngle").text = start
        self.__elem.find(".//EndAngle").text = end

    def getElem(self):
        return self.__elem

class RouteElem(object):
    route_template = '''\
<Route>
    <Name>r1</Name>
    <Waypoints>
    </Waypoints>
    <WaypointGraphicValue>RedPin</WaypointGraphicValue>
</Route>
'''
    def __init__(self, route_id, graph='RedPin'):
        self.__elem = ET.fromstring(RouteElem.route_template)
        self.__elem.find(".//Name").text = 'r' + str(route_id)
        self.__elem.find(".//WaypointGraphicValue").text = graph

    def addWaypoint(self, wp):
        self.__elem.find("./Waypoints").append(wp.getElem())

    def getElem(self):
        return self.__elem
        
class WayPointElem(object):
    waypoint_template = '''\
<WayPoint>
    <X>110</X>
    <Y>55</Y>
</WayPoint>
'''
    def __init__(self, x, y):
        self.__elem = ET.fromstring(WayPointElem.waypoint_template)
        self.__elem.find("./X").text = x
        self.__elem.find("./Y").text = y

    def getElem(self):
        return self.__elem


def main():
    arg_parser = ArgumentParser()
    arg_parser.add_argument('raw_script_file')
    args = arg_parser.parse_args()


    re_mtsconfigenb = re.compile(r"^FORW MTE MTSCONFIGENB\s+(\d+)\s*\{\s*(.+)\s*\}$", re.I)
    re_enb = re.compile(r"(\d+)\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s*\{(.+?)\s*\}\s*")
    re_cell = re.compile(r"(\d+)\s+\d+\s+(\d+)\s*\[\s*(\d+)\s+(\d+)\s+.+?\]")

    re_mstconfigpath = re.compile(r"^FORW MTE MTSCONFIGPATH\s+(\d+)\s+(\d+)\s*\{\s*(.+)\s*\}$", re.I)
    re_waypoint = re.compile("(-?\d+)\s+(-?\d+)")

    f_rootname = os.path.splitext(os.path.basename(args.raw_script_file))[0]
    root_elem = RootElem(f_rootname) 
    wp_set = set() # for excluding duplicated path

    with open(args.raw_script_file) as f:
        for line in f.readlines():
            # remove comment string
            (mts_cmd, sep, c) = line.partition(r"#") 
            mts_cmd = mts_cmd.strip()

            m_cmd = re_mtsconfigenb.fullmatch(mts_cmd)
            if m_cmd :
                enbs = m_cmd.group(2)
                for m_enb in re_enb.finditer(enbs):
                    enb_elem = EnbElem(m_enb.group(1), m_enb.group(2), m_enb.group(3))
                    cells = m_enb.group(5)
                    for m_cell in re_cell.finditer(cells):
                        cell_elem = CellElem(*m_cell.groups())
                        enb_elem.addCell(cell_elem)
                    root_elem.addEnb(enb_elem)

            m_cmd = re_mstconfigpath.fullmatch(mts_cmd)
            if m_cmd and m_cmd.group(3) not in wp_set:
                route_elem = RouteElem(m_cmd.group(1))
                waypoints = m_cmd.group(3)
                wp_set.add(waypoints)
                for m_wp in re_waypoint.finditer(waypoints):
                    wp = WayPointElem(*m_wp.groups())
                    route_elem.addWaypoint(wp)
                root_elem.addRoute(route_elem)

    outfile_name = f_rootname + '.xml'


    if os.path.exists(outfile_name):
        os.remove(outfile_name)
    tree = ElementTree(root_elem.getElem())

    xmltext = ET.tostring(root_elem.getElem(), encoding='unicode')
    xmltext = '\n'.join(RootElem.root_template.splitlines()[0:2] + [xmltext])
    with open(outfile_name, 'w') as f:
        f.write(xmltext)


if __name__ == '__main__':
    main()
