#This script provides two functions
#one to calculate the volume and the other to calculate the heated area per household

#import connect_to_database
import psycopg2
import numpy as np
import re
import time
import xml.etree.ElementTree as ET



def volume_building(measured_height):

    try:
        connect = connect_to_database.connect_to_database()
        cursor = connect.cursor()

        # Query to fetch the lod2_solid_id and calculate the volume
        volume_query = """
                SELECT sg.id, CG_Volume(CG_MakeSolid(sg.solid_geometry)) AS volume
                FROM citydb.building b
                JOIN citydb.surface_geometry sg
                ON b.lod2_solid_id = sg.root_id
                WHERE b.measured_height = %s AND sg.is_solid = 1;
                """
        cursor.execute(volume_query, (measured_height,))
        result = cursor.fetchone()

    except psycopg2.Error as e:
        print("Error in the CG_Volume Calculation: ", e)
        return 0

    if result:
        geometry_id, volume = result
        print(f"Geometry ID: {geometry_id}, Building Height {measured_height}m, Volume: {volume} m³")

    else:
        print("no valid geometry found for this measured_height: ", measured_height)
        return 0


    # Close the connection
    cursor.close()
    connect.close()

    return volume


#alternative function to calcualte the volume
#  in this case, the geometry is imported from the database and then the volume is calculated in python
# i checked the results of this in comparison to the CG_Volume function and the values are the same

#function for parsing the text that the database query returns
def parse_polyhedral_surface(measured_height):
    """
    read the polyhedralsurface text that is the result of a query in citydb
    returns a list of polygons with theirs points and its xyz coordinates
    """
    #connect to database
    connect = connect_to_database.connect_to_database()
    cursor = connect.cursor()

    # Query to fetch the lod2_solid_id and calculate the volume
    polyhedralsurface_query = """
                    SELECT ST_AsTExt(sg.solid_geometry) AS geometry
                    FROM citydb.building b
                    JOIN citydb.surface_geometry sg
                    ON  b.lod2_solid_id = sg.root_id
                    WHERE sg.is_solid = 1 and b.measured_height= %s;
                    """
    cursor.execute(polyhedralsurface_query, (measured_height,))
    polyhedralsurface_text = cursor.fetchone()
    # Close the connection
    cursor.close()
    connect.close()


    # Extract all sets of coordinates for each polygon
    polygons_texts = re.findall(r'\(\(([^()]+)\)\)', str(polyhedralsurface_text[0]))
    polygons = []

    #loop to get the coordinates of each point for each polygons
    for polygon in polygons_texts:
        # Split each polygon into individual vertex coordinates
        vertices = polygon.split(',')
        face = []

        for vertex in vertices:
            # Split each vertex into x, y, z and convert to float
            x, y, z = map(float, vertex.split())
            face.append((x, y, z))

        polygons.append(face)

    return polygons


def parse_citygml_exterior(file_path, building_id):
    # Parse the CityGML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Define the namespaces
    namespaces = {
        'gml': 'http://www.opengis.net/gml',
        'bldg': 'http://www.opengis.net/citygml/building/2.0',
    }

    polygons = []

    # Find the building with the specific ID
    building = root.find(f".//bldg:Building[@gml:id='{building_id}']", namespaces)
    if building is None:
        namespaces = {
            'gml': 'http://www.opengis.net/gml',
            'xAL': 'urn:oasis:names:tc:ciq:xsdschema:xAL:2.0',
            'bldg': 'http://www.opengis.net/citygml/building/1.0',
            'gen': 'http://www.opengis.net/citygml/generics/1.0',
        }

        # Find the building with the specific ID
        building = root.find(f".//bldg:Building[@gml:id='{building_id}']", namespaces)


        if building is None:
            print(f"No building found with ID: {building_id}")
            return polygons  # Return an empty list if the building is not found

    # Iterate over WallSurface, GroundSurface, and RoofSurface for the specific building
    for surface_type in ['WallSurface', 'GroundSurface', 'RoofSurface']:
        surfaces = building.findall(f".//bldg:{surface_type}", namespaces)
        for surface in surfaces:
            # Find all LinearRing elements within this surface
            for linear_ring in surface.findall(".//gml:LinearRing", namespaces):
                pos_list_element = linear_ring.find("gml:posList", namespaces)
                if pos_list_element is not None:
                    # Extract the 3D coordinates
                    pos_list = pos_list_element.text.strip().split()
                    coordinates = [
                        (float(pos_list[i]), float(pos_list[i + 1]), float(pos_list[i + 2]))
                        for i in range(0, len(pos_list), 3)
                    ]
                    polygons.append(coordinates)

    return polygons
def volume_building_2(building_id):
    start_time = time.time()
    file_path = "./input/Isarvorstadt.gml"
    #polygons = parse_polyhedral_surface(measured_height)
    polygons = parse_citygml_exterior(file_path,building_id)


    volume = 0.0
    origin = np.array([0.0, 0.0, 0.0])

    for polygon in polygons:
        for i in range(1, len(polygon) - 1):
            if time.time()- start_time > 60:
                print('Time limit exceeded')
                return 0
            # Get three vertices forming a triangle on the face
            v0, v1, v2 = np.array(polygon[0]), np.array(polygon[i]), np.array(polygon[i + 1])

            # Compute the volume of the tetrahedron formed by origin, v0, v1, v2
            tetrahedron_volume = np.dot(np.cross(v1 - v0, v2 - v0), v0) / 6.0
            volume += tetrahedron_volume

    volume = round(abs(volume), 2)

    print('BUIlding with id', building_id, 'has a volume of', (volume))
    return volume



# Calculate volume
#volume_building_2("DEBY_LOD2_4913214")
#volume_building_2("DEBY_LOD2_52671398")


#script
#DEBY_LOD2_4913214
#volume = volume_building(4.4401)
#print(volume_building(12.321))
#Geometry ID: 1386950, root_id = 1857857, Building Height 12.321m, Volume: 2903.265968747979 m³




#DEBY_LOD2_52671398
#root_id = 1845143
#id no pgadmin = 1374360
#measured_heught = 14.701
#volume = 15786,62
