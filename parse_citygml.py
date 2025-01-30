from pathlib import Path
from lxml import etree
import xml.etree.ElementTree as ET
from Building import CityBuilding
from collections import defaultdict


ID_TAG = '{http://www.opengis.net/gml}id'

#this function will return all the buildings as an instance from the class building in python
def parse_citygml_into_instance(citygml_filename):
    # Parse the XML file
    tree = ET.parse(str(citygml_filename))
    root = tree.getroot()

    # Define the namespace mappings
    namespaces = {
        'core': 'http://www.opengis.net/citygml/2.0',
        'bldg': 'http://www.opengis.net/citygml/building/2.0',
        'gen': 'http://www.opengis.net/citygml/generics/2.0',
        'gml': 'http://www.opengis.net/gml',
        'xAL': 'urn:oasis:names:tc:ciq:xsdschema:xAL:2.0'
    }

    # Create a list to hold all buildings
    buildings = []

    # Iterate over each building and extract data
    for building_elem in root.findall('core:cityObjectMember/bldg:Building', namespaces):
        building_data = {}

        # Extract attributes
        building_data['building_id'] = building_elem.attrib.get('{http://www.opengis.net/gml}id', '')
        building_data['creation_date'] = building_elem.findtext('core:creationDate', '', namespaces)

        external_ref = building_elem.find('core:externalReference/core:informationSystem', namespaces)
        building_data['information_system'] = external_ref.text if external_ref is not None else ''

        external_name = building_elem.find('core:externalReference/core:externalObject/core:name', namespaces)
        building_data['external_name'] = external_name.text if external_name is not None else ''

        # Initialize a defaultdict to store generic attributes
        generic_attributes = defaultdict(lambda: '')

        # Iterate over the specified attributes and extract their values
        for attribute_name in [
            'building_groupe_ID', 'construction_type', 'building_year_of_construction', 'building_gross_floor_area',
            'ownership_type', 'owners', 'Munich_BuildingID', 'house_number', 'building_usage', 'usable_and_living_area',
            'usable_area', 'Street', 'refurbishment_state', 'refurbishment_type', 'number_of_floors_total',
            'building_type', 'num_of_inhabitants', 'number_of_building_units', 'X', 'Y', 'Kategorie', 'ENEV',
            'Photovolta', 'Fernwärme', 'GMLID'
        ]:
            # Check each attribute in all possible types (string, int, double)
            for attr_type in ['stringAttribute', 'intAttribute', 'doubleAttribute']:
                attribute_element = building_elem.find(
                    f'gen:{attr_type}[@name="{attribute_name}"]/gen:value', namespaces)
                if attribute_element is not None:
                    generic_attributes[attribute_name] = attribute_element.text
                    break  # Found the attribute, no need to check further types

        # Add all generic attributes to building_data
        building_data.update(generic_attributes)

        building_data['year_of_construction'] = building_elem.findtext('bldg:yearOfConstruction', '', namespaces)
        building_data['roof_type'] = building_elem.findtext('bldg:roofType', '', namespaces)
        building_data['measured_height'] = building_elem.findtext('bldg:measuredHeight', '', namespaces)
        building_data['storeys_above_ground'] = building_elem.findtext('bldg:storeysAboveGround', '', namespaces)

        # Extract address details
        address = building_elem.find('bldg:address/core:Address/core:xalAddress/xAL:AddressDetails/xAL:Country', namespaces)
        if address is not None:
            country = address.find('xAL:CountryName', namespaces)
            locality = address.find('xAL:Locality/xAL:LocalityName', namespaces)
            thoroughfare = address.find('xAL:Locality/xAL:Thoroughfare/xAL:ThoroughfareName', namespaces)

            building_data['country'] = country.text if country is not None else ''
            building_data['locality'] = locality.text if locality is not None else ''
            building_data['thoroughfare'] = thoroughfare.text if thoroughfare is not None else ''
        else:
            building_data['country'] = ''
            building_data['locality'] = ''
            building_data['thoroughfare'] = ''

        # Create a Building instance
        building_instance = CityBuilding(**building_data)

        # Add the building instance to the list
        buildings.append(building_instance)

    # Print the buildings to verify
    for b in buildings:
        print(b)
        print("\n")  # Adding empty line for better readability

    return buildings





def parse_citygml_into_instance_2(citygml_filename):
    # Parse the XML file
    tree = ET.parse(str(citygml_filename))
    root = tree.getroot()

    # Define the namespace mappings
    namespaces = {
        'gml': 'http://www.opengis.net/gml',
        'xAL': 'urn:oasis:names:tc:ciq:xsdschema:xAL:2.0',
        'bldg': 'http://www.opengis.net/citygml/building/1.0',
        'gen': 'http://www.opengis.net/citygml/generics/1.0',
    }

    # Create a list to hold all buildings
    buildings = []

    # Iterate over each building and extract data
    for building_elem in root.findall('.//bldg:Building', namespaces):
        building_data = {}

        # Extract attributes
        building_data['building_id'] = building_elem.attrib.get('{http://www.opengis.net/gml}id', '')
        building_data['creation_date'] = building_elem.findtext('.//creationDate', '', namespaces)

        external_ref = building_elem.find('.//externalReference/informationSystem', namespaces)
        building_data['information_system'] = external_ref.text if external_ref is not None else ''

        external_name = building_elem.find('.//externalReference/externalObject/name', namespaces)
        building_data['external_name'] = external_name.text if external_name is not None else ''

        # Initialize a defaultdict to store generic attributes
        generic_attributes = defaultdict(lambda: '')

        # Iterate over the specified attributes and extract their values
        for attribute_name in [
            'building_groupe_ID', 'construction_type', 'building_year_of_construction', 'building_gross_floor_area',
            'ownership_type', 'owners', 'Munich_BuildingID', 'house_number', 'building_usage', 'usable_and_living_area',
            'usable_area', 'Street', 'refurbishment_state', 'refurbishment_type', 'number_of_floors_total',
            'building_type', 'num_of_inhabitants', 'number_of_building_units', 'X', 'Y', 'Kategorie', 'ENEV',
            'Photovolta', 'Fernwärme', 'GMLID'
        ]:
            # Check each attribute in all possible types (string, int, double)
            for attr_type in ['stringAttribute', 'intAttribute', 'doubleAttribute']:
                attribute_element = building_elem.find(
                    f'gen:{attr_type}[@name="{attribute_name}"]/gen:value', namespaces)
                if attribute_element is not None:
                    generic_attributes[attribute_name] = attribute_element.text
                    break  # Found the attribute, no need to check further types

        # Add all generic attributes to building_data
        building_data.update(generic_attributes)

        building_data['year_of_construction'] = building_elem.findtext('bldg:yearOfConstruction', '', namespaces)
        building_data['roof_type'] = building_elem.findtext('bldg:roofType', '', namespaces)
        building_data['measured_height'] = building_elem.findtext('bldg:measuredHeight', '', namespaces)
        building_data['storeys_above_ground'] = building_elem.findtext('bldg:storeysAboveGround', '', namespaces)
        building_data['function'] = building_elem.findtext('bldg:function', '', namespaces)

        # Extract address details
        address = building_elem.find('bldg:address/Address/xalAddress/xAL:AddressDetails/xAL:Country', namespaces)
        if address is not None:
            country = address.find('xAL:CountryName', namespaces)
            locality = address.find('xAL:LocalityName', namespaces)
            thoroughfare = address.find('xAL:Locality/xAL:Thoroughfare/xAL:ThoroughfareName', namespaces)

            building_data['country'] = country.text if country is not None else ''
            building_data['locality'] = locality.text if locality is not None else ''
            building_data['thoroughfare'] = thoroughfare.text if thoroughfare is not None else ''
        else:
            building_data['country'] = ''
            building_data['locality'] = ''
            building_data['thoroughfare'] = ''

        # Create a Building instance
        building_instance = CityBuilding(**building_data)

        # Add the building instance to the list
        buildings.append(building_instance)

    # Print the buildings to verify
    for b in buildings:
        print(b)
        print("\n")  # Adding empty line for better readability

    return buildings



def get_building_by_id(buildings, building_id):
    for building in buildings:
        if building.building_id == building_id:
            print(repr(building))
            return building
    return None


