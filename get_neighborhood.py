import requests
from geopy.geocoders import Nominatim
from pyproj import CRS, Transformer
import time

def get_suburb(building):
    # Construct the URL for the Nominatim API
    url = 'https://nominatim.openstreetmap.org/search'


    '''Needs to adapt this in the case of other cities'''
    if building.locality == 'München':
        city = 'Munich'

    elif building.locality == None or building.locality == '' or building.Street == None or building.Street == '':
        city, suburb = get_city_suburb_from_coordinates(building.X, building.Y)
        return suburb


    # Define the parameters for the search
    params = {
        'street': building.Street,
        'city': city,
        'format': 'json',
        'addressdetails': 1,
        'limit': 1
    }

    # Define the headers
    headers = {
        'User-Agent': 'Your REason Here (your.email@domain.com)'
    }

    # Send the request to the API
    response = requests.get(url, params=params, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()

        # Check if any results were returned
        if data:
            # Extract the address details
            address = data[0].get('address', {})

            # Get the suburb
            suburb = address.get('suburb', 'Suburb not found')

            return suburb
        else:
            return 'Address not found'
    else:
        return f'Error fetching data from the API: {response.status_code}'



def get_city_suburb_from_coordinates(x, y):
    x = float(x)
    y = float(y)

    # Use a descriptive user_agent string that includes contact info
    geolocator = Nominatim(user_agent="bachelor_thesis (ju.ebarbosa@gmail.com)")

    # Likely UTM zones to test (adjust based on region of interest)
    likely_zones = range(28, 39)

    for utm_zone in likely_zones:
        try:
            # Define UTM CRS for Northern Hemisphere
            utm_crs_north = CRS.from_string(f"+proj=utm +zone={utm_zone} +datum=WGS84 +units=m +no_defs +north")
            transformer_north = Transformer.from_crs(utm_crs_north, CRS.from_epsg(4326), always_xy=True)
            lon, lat = transformer_north.transform(x, y)

            # Make sure to slow down the requests to avoid rate limits
            time.sleep(1)  # Ensure 1 request per second

            # Perform reverse geocoding
            location = geolocator.reverse((lat, lon), exactly_one=True, timeout=10)
            if location:
                address = location.raw['address']
                if 'suburb' in address:
                    suburb = address['suburb']
                    city = address.get('city', address.get('town', 'Unknown'))
                    return city, suburb
                elif 'city_district' in address:
                    suburb = address['city_district']
                    city = address.get('city', address.get('town', 'Unknown'))
                    return city, suburb

            # Define UTM CRS for Southern Hemisphere
            utm_crs_south = CRS.from_string(f"+proj=utm +zone={utm_zone} +datum=WGS84 +units=m +no_defs +south")
            transformer_south = Transformer.from_crs(utm_crs_south, CRS.from_epsg(4326), always_xy=True)
            lon, lat = transformer_south.transform(x, y)

            # Make sure to slow down the requests to avoid rate limits
            time.sleep(1)  # Ensure 1 request per second

            # Perform reverse geocoding again for southern hemisphere
            location = geolocator.reverse((lat, lon), exactly_one=True, timeout=10)
            if location:
                address = location.raw['address']
                if 'suburb' in address:
                    suburb = address['suburb']
                    city = address.get('city', address.get('town', 'Unknown'))
                    return city, suburb
                elif 'city_district' in address:
                    suburb = address['city_district']
                    city = address.get('city', address.get('town', 'Unknown'))
                    return city, suburb

        except Exception as e:
            # Add specific handling for insufficient privileges
            if "GeocoderInsufficientPrivileges" in str(e):
                print("GeocoderInsufficientPrivileges error encountered.")
            print(f"Error in UTM zone {utm_zone}: {e}")
            continue

    return "Unknown", "Unknown"


def get_X_Y_from_posList(building):
    import xml.etree.ElementTree as ET


    # Define namespaces
    namespaces = {
        'gml': 'http://www.opengis.net/gml',
        'xAL': 'urn:oasis:names:tc:ciq:xsdschema:xAL:2.0',
        'bldg': 'http://www.opengis.net/citygml/building/1.0',
        'gen': 'http://www.opengis.net/citygml/generics/1.0',
    }

    # Parse the CityGML file
    tree = ET.parse("./input/Isarvorstadt.gml")  # Replace with your file
    root = tree.getroot()

    # Construct the expected GroundSurface ID pattern
    ground_surface_id_prefix = f"{building.building_id}_"

    # Find the GroundSurface element with a matching ID
    for ground_surface in root.findall(".//bldg:GroundSurface", namespaces):
        if ground_surface.get("{http://www.opengis.net/gml}id", "").startswith(ground_surface_id_prefix):
            pos_list_element = ground_surface.find(".//gml:posList", namespaces)
            if pos_list_element is not None:
                pos_list = pos_list_element.text.strip().split()  # Split coordinates into a list
                x, y = float(pos_list[0]), float(pos_list[1])  # Extract first X, Y
                return x, y
            else:
                print("No posList element found in GroundSurface")
                return None, None


#Example
#x_coord = '690672.52'
#y_coord = '5341936.573'

#city, suburb = get_city_suburb_from_coordinates(x_coord, y_coord)
#print(f"The coordinates are located in the city: {city}, suburb: {suburb}")
