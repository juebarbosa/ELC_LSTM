import parse_citygml
from pathlib import Path
import estimate_number_of_residents_per_household
from bdew import get_load_profile_df
import matplotlib.pyplot as plt
import create_building_part
import os
from lxml import etree
import pandas as pd
import Building
from pyproj import CRS, Transformer
from LSTM_munich_FINAL import predict_energy_consumption as predict_energy_consumption
from LSTM_munich_FINAL import prepare_features as prepare_features
from tensorflow.keras.models import load_model
import get_neighborhood

#first define all the correct input, output and data paths
#path to 3dwebclient folder tables_data_households
output_dir_tables_web_map_client = r'C:\Users\jueba\3dcitydb-web-map-1.9.0\3dwebclient\tables_data_households'

#get the citygml file from the folder 'input'
folder_path = Path('./input')

citygml_file = 'Isarvorstadt.gml'
file_path = folder_path / citygml_file

# Check if the file exists
if file_path.exists():
    # Read the file content
    with open(file_path, 'r') as file:
        content = file.read()



#now this function will transform each building into a class instance in python, with their characteristics.
#In the variable citygml_buildings we have all buildings as python instances form the class CityBuilding

citygml_buildings = parse_citygml.parse_citygml_into_instance_2(file_path)
print('\n\n')

# Initialize lists to store the number of households per size for all buildings
number_of_households_per_size_final_for_all_buildings = []

# Initialize counters for missing attributes
missing_building_usage = 0
missing_locality = 0
missing_street = 0
missing_number_of_building_units = 0
missing_num_of_inhabitants = 0

#List of residential buildings
wohnen_buildings = []

# Filtered list of valid buildings
filtered_buildings = []

# Iterate through each building
for building in citygml_buildings:
    # Check if building_usage exists and is "Wohnen"
    #if not hasattr(building, 'building_usage'):
    #    missing_building_usage += 1
    if hasattr(building,'building_usage') and building.building_usage == "Wohnen":
        wohnen_buildings.append(building)

        # Check if locality exists
        if not hasattr(building, 'locality') or building.locality is None:
            missing_locality += 1

        # Check if street exists
        if not hasattr(building, 'Street') or building.Street is None:
            missing_street += 1

        # Check if number_of_building_units exists
        if not hasattr(building, 'number_of_building_units') or building.number_of_building_units is None:
            missing_number_of_building_units += 1

        # Check if num_of_inhabitants exists
        if not hasattr(building, 'num_of_inhabitants') or building.num_of_inhabitants is None:
            missing_num_of_inhabitants += 1

    elif hasattr(building, 'function') and building.function == '31001_1000':
        wohnen_buildings.append(building)

        # Check if locality exists
        if not hasattr(building, 'locality') or building.locality is None:
            missing_locality += 1

        # Check if street exists
        if not hasattr(building, 'Street') or building.Street is None:
            missing_street += 1

        # Check if number_of_building_units exists
        if not hasattr(building, 'number_of_building_units') or building.number_of_building_units is None:
            missing_number_of_building_units += 1

        # Check if num_of_inhabitants exists
        if not hasattr(building, 'num_of_inhabitants') or building.num_of_inhabitants is None:
            missing_num_of_inhabitants += 1




#add to the buildings that meet the first three conditions the instance complete equal False or True
    #if hasattr(building, 'building_usage') and building.building_usage == "Wohnen":
for building in wohnen_buildings:
    if (not hasattr(building, 'number_of_building_units') or building.number_of_building_units is None or
            not hasattr(building, 'num_of_inhabitants') or building.num_of_inhabitants is None):
        setattr(building, 'complete', False)
    else:
        setattr(building, 'complete', True)

    filtered_buildings.append(building)

# Print the results
print(f"Total buildings: {len(citygml_buildings)}")
print(f"Buildings with 'building_usage'='Wohnen' or 'building_function' = 31001_1000: {len(wohnen_buildings)}")
print(f"Buildings missing 'locality': {missing_locality}")
print(f"Buildings missing 'Street': {missing_street}")
print(f"Buildings missing 'number_of_building_units': {missing_number_of_building_units}")
print(f"Buildings missing 'num_of_inhabitants': {missing_num_of_inhabitants}")


number_of_sucesses = 0
number_of_fails = 0
case_0 = 0
case_1 = 0
case_2 = 0
new_buildings_list = []
temptemp = 0
j = 0

# upload the model andget the scalers
directory_path = './open_smart_meter_data/hourly_munich'
X, y, scaler_area, scaler_lat, scaler_lon, scaler_y, scaler_day, scaler_hour, scaler_day_week, scaler_month, scaler_year = prepare_features(directory_path)
model = load_model('./energy_consumption_final_model.keras')
# Loop through each building that has all required attributes
for building in filtered_buildings:
    j +=1

    #estimate the number of households and their sizes per number of residents
    case, temp, A_h_per_household, volume = estimate_number_of_residents_per_household.estimate_number_of_residents_per_household("./Anteile_der_Privathaushalte_in Prozent_nach_Stadtbezirken_2020_komma.csv", building)

    if case == 0:
        case_0 += 1
        continue

    if case == 1:
        case_1 += 1

    if case == 2:
        case_2 += 1

    # total number of households in the dataset
    temptemp += sum(temp)

    # change the information about building units and residents in the CityBuilding instance
    building.number_of_building_units = sum(temp)

    #actualize the number of inhabitants in the building
    building.num_of_inhabitants = sum([temp[i] * (i + 1) for i in range(len(temp))])

    #create a volume attribute for the building instace
    building.volume = volume

    # create a list with the required building details and the new temp data

    building_info = [ building.building_id if hasattr(building, 'building_id') else 0,
        building.building_usage if hasattr(building, 'building_usage') else 0,
        building.num_of_inhabitants if getattr(building, 'num_of_inhabitants', None) is not None else 0,
        building.number_of_building_units if getattr(building, 'number_of_building_units', None) is not None else 0
        ] + temp

    number_of_households_per_size_final_for_all_buildings.append(building_info)

    # make list of instances of households
    households = []
    #for now all kw eauql to zero
    KW = 0

    #Define the Kundenwerts for each household and then save them as a building attribute
    #for KW_LSTM we call the function predict_energy_consumption
    #for KW_stats we define fixed values
    KW_stats_list = [1900, 2890, 3720, 4085, 5430]

    #calculate the latitude and longitude of the building
    transformer = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True)

    #check if building has X and Y attributes
    if not hasattr(building, 'X') or not hasattr(building, 'Y'):
        X,Y = get_neighborhood.get_X_Y_from_posList(building)
        print(f"Building {building.building_id} got X and Y coordinates from the ground surface")
        building.X = X
        building.Y = Y

    lon, lat = transformer.transform(building.X, building.Y)

    if sum(temp) == len(A_h_per_household):
        for i in range(temp[0]):
            residents = 1
            KW_Stats = KW_stats_list[0]
            index = i
            h_area = int(A_h_per_household[index])
            yearly_dataframe, KW_LSTM = predict_energy_consumption(model, h_area, lat, lon, scaler_area, scaler_lat, scaler_lon, scaler_y, scaler_day, scaler_hour, scaler_day_week, scaler_month, scaler_year)

            yearly_dataframe.to_csv(
                os.path.join(output_dir_tables_web_map_client, f'{building.building_id}_W{index}_LSTM.csv'),index = False)

            KW_LSTM = int(KW_LSTM)

            #create instances of the class household
            h = Building.household(residents, h_area, KW_LSTM, KW_Stats)

            # add to the building the instance household as a new attribute
            setattr(building, f'household_{i}', h)

        for i in range(temp[1]):
            residents = 2
            index = index+1
            KW_Stats = KW_stats_list[1]
            h_area = int(A_h_per_household[index])
            yearly_dataframe, KW_LSTM = predict_energy_consumption(model, h_area, lat, lon, scaler_area, scaler_lat, scaler_lon, scaler_y, scaler_day, scaler_hour, scaler_day_week, scaler_month, scaler_year)

            yearly_dataframe.to_csv(
                os.path.join(output_dir_tables_web_map_client, f'{building.building_id}_W{index}_LSTM.csv'),index = False)

            KW_LSTM = int(KW_LSTM)

            # create instances of the class household
            h = Building.household(residents, h_area, KW_LSTM, KW_Stats)

            # add to the building the instance household as a new attribute
            setattr(building, f'household_{index}', h)




        for i in range(temp[2]):
            residents = 3
            index = index+1
            KW_Stats = KW_stats_list[2]
            h_area = int(A_h_per_household[index])
            yearly_dataframe, KW_LSTM = predict_energy_consumption(model, h_area, lat, lon, scaler_area, scaler_lat, scaler_lon, scaler_y, scaler_day, scaler_hour, scaler_day_week, scaler_month, scaler_year)

            yearly_dataframe.to_csv(
                os.path.join(output_dir_tables_web_map_client, f'{building.building_id}_W{index}_LSTM.csv'),index = False)

            KW_LSTM = int(KW_LSTM)

            # create instances of the class household
            h = Building.household(residents, h_area, KW_LSTM, KW_Stats)

            # add to the building the instance household as a new attribute
            setattr(building, f'household_{index}', h)

        for i in range(temp[3]):
            residents = 4
            index = index+1
            KW_Stats = KW_stats_list[3]
            h_area = int(A_h_per_household[index])
            yearly_dataframe, KW_LSTM = predict_energy_consumption(model, h_area, lat, lon, scaler_area, scaler_lat, scaler_lon, scaler_y, scaler_day, scaler_hour, scaler_day_week, scaler_month, scaler_year)

            yearly_dataframe.to_csv(
                os.path.join(output_dir_tables_web_map_client, f'{building.building_id}_W{index}_LSTM.csv'),index = False)

            KW_LSTM = int(KW_LSTM)

            # create instances of the class household
            h = Building.household(residents, h_area, KW_LSTM, KW_Stats)

            # add to the building the instance household as a new attribute
            setattr(building, f'household_{index}', h)

        for i in range(temp[4]):
            residents = 5
            index = index+1
            KW_Stats = KW_stats_list[4]
            h_area = int(A_h_per_household[index])
            yearly_dataframe, KW_LSTM = predict_energy_consumption(model, h_area, lat, lon, scaler_area, scaler_lat, scaler_lon, scaler_y, scaler_day, scaler_hour, scaler_day_week, scaler_month, scaler_year)

            yearly_dataframe.to_csv(
                os.path.join(output_dir_tables_web_map_client, f'{building.building_id}_W{index}_LSTM.csv'),index = False)

            KW_LSTM = int(KW_LSTM)

            # create instances of the class household
            h = Building.household(residents, h_area, KW_LSTM, KW_Stats)

            # add to the building the instance household as a new attribute
            setattr(building, f'household_{index}', h)
    else:
        continue


    if case == 1 or case == 2:
        # creating new list of instances of buildings to keep calculating
        new_buildings_list.append(building)
    else:
        pass

    #loop for stopping the run only after some buildings to help with debugging
    if j>1:
        break


#print('number of succeeded estimations:',number_of_sucesses)
#print('number of fails:', number_of_fails)
print('number os cases 0:', case_0)
print('number os cases 1:', case_1)
print('number of cases 2:', case_2)

#print len of filtered buildings
print('number of filtered buildings:', len(filtered_buildings))
print('number of calculated buildings:', len(new_buildings_list))

print('\n')
print(*number_of_households_per_size_final_for_all_buildings, sep="\n")
print('total number of households in the dataset=',temptemp)


#Update CityGMl file with the new information on the household level about number of residents, KWs, and areas

# Load the same GML file as the beginning of the code
tree = etree.parse(file_path)
root = tree.getroot()

# Define the namespace mappings
namespaces = {
    'core': 'http://www.opengis.net/citygml/2.0',
    'bldg': 'http://www.opengis.net/citygml/building/2.0',
    'gen': 'http://www.opengis.net/citygml/generics/2.0',
    'gml': 'http://www.opengis.net/gml',
    'xAL': 'urn:oasis:names:tc:ciq:xsdschema:xAL:2.0'
}

for building in new_buildings_list:

    #extract the building_id to finde the corresponding building in the GML file
    building_id = building.building_id

    #finde the corresponding building in the gml file
    building_element = root.find(f".//{{http://www.opengis.net/citygml/building/2.0}}Building[@gml:id='{building_id}']", namespaces)
    if building_element is None:
        # Define the namespace  for file Isarvorstadt
        namespaces = {
            'gml': 'http://www.opengis.net/gml',
            'xAL': 'urn:oasis:names:tc:ciq:xsdschema:xAL:2.0',
            'bldg': 'http://www.opengis.net/citygml/building/1.0',
            'gen': 'http://www.opengis.net/citygml/generics/1.0',
        }
        building_element = root.find(f".//{{http://www.opengis.net/citygml/building/1.0}}Building[@gml:id='{building_id}']", namespaces)

    if building_element is not None:
        integer_number_of_building_units = int(building.number_of_building_units)
        # loop over the households in the building object
        for i in range(1, integer_number_of_building_units + 1):
            #make the household atributtes callable
            household_attr = f'household_{i}'

            # Use getattr to dynamically access the household attribute
            household_instance = getattr(building, household_attr, None)

            # Check if the household_instance exists to avoid errors
            if household_instance:
                household_size = household_instance.residents
                household_kw_lstm = round(household_instance.KW_LSTM,2)
                household_kw_stats = household_instance.KW_Stats
                household_area = household_instance.h_area

            # create a BuildingPart in citygml for each household
            building_part = create_building_part.create_building_part(household_size, household_kw_lstm, household_kw_stats, household_area, i, namespaces)

            # append the building_part to the building_element
            building_element.append(building_part)



# Define the output directory path for the CityGML updated file and for the tables
# containing the semantic information that will be shown in the 3dwebclient
output_dir = './output'
#output_dir_tables_web_map_client = r'C:\Users\jueba\3dcitydb-web-map-1.9.0\3dwebclient\tables_data_households'

# Define the output file path
output_file_path = os.path.join(output_dir, 'Isarvorstadt_processed.gml')

# Save the modified GML file to the specified path
etree.indent(root)
root_tree = etree.ElementTree(root)
root_tree.write(output_file_path, pretty_print=True, xml_declaration=True, encoding='UTF-8')
print(f"File saved successfully to: {output_file_path}")



#export csv file to upload in google spreadsheets and later use in the 3d web map client for visualisation
#for each building in new_buildings_list there should be a line with multiple columns
#the columns should be : id, measured_height, num_of_inhabitants, num_of_building_units, storeys_above_ground, bbuilding_usage, building_function, adress
web_client_data = (pd.DataFrame(columns=['id', 'measured_height', 'num_of_inhabitants', 'num_of_building_parts', 'storeys_above_ground', 'building_usage', 'building_function', 'address']))

for building in new_buildings_list:

    #check is building_usage exists
    if not hasattr(building, 'building_usage'):
        building_data = {
            'id': building.building_id,
            'measured_height': building.measured_height,
            'num_of_inhabitants': building.num_of_inhabitants,
            'num_of_building_parts': building.number_of_building_units,
            'storeys_above_ground': building.storeys_above_ground,
            'building_function': building.function
        }
    else:
        building_data = {
            'id': building.building_id,
            'measured_height': building.measured_height,
            'num_of_inhabitants': building.num_of_inhabitants,
            'num_of_building_parts': building.number_of_building_units,
            'storeys_above_ground': building.storeys_above_ground,
            'building_usage': building.building_usage,
            'address': building.Street
        }

    # Append the dictionary as a new row in the DataFrame
    web_client_data = pd.concat([web_client_data, pd.DataFrame([building_data])], ignore_index=True)

    #also make for every building a table with the data of all the households
    household_data = pd.DataFrame(columns=['id','residents', 'area', 'ELC_LSTM', 'ELC_Stats'])
    for i in range(int(building.number_of_building_units)):
        household = getattr(building, f'household_{i}')
        household_data = pd.concat([household_data, pd.DataFrame([{'id': i, 'residents': household.residents, 'area': household.h_area, 'ELC_LSTM': household.KW_LSTM, 'ELC_Stats': household.KW_Stats}])], ignore_index=True)
        #calculate the BDEW load profile for each KW_lstm value and then save as a csv file
        verlauf_df = get_load_profile_df.get_load_profile_df(2024, int(household.KW_LSTM))
        print('this is the total sum from bdwe before resampling to hourly',(verlauf_df['h0_dyn'].sum),'and this the household KW LSTM', household.KW_LSTM)
        #to plot in the web map client we need to resample the data to daily
        verlauf_df = verlauf_df.resample('H').sum()
        print('this is the total sum from bdew after resampling',(verlauf_df['h0_dyn'].sum),'and this the household KW LSTM', household.KW_LSTM)
        #save in 3dwebclient for visualisation
        verlauf_df.to_csv(os.path.join(output_dir_tables_web_map_client, f'{building.building_id}_W{i}_H0SLP_LSTM.csv'))

        # calculate the BDEW load profile for each KW_stats value and then save as a csv file
        verlauf_df = get_load_profile_df.get_load_profile_df(2024, int(household.KW_Stats))
        print('this is the total sum from bdwe before resampling to hourly', (verlauf_df['h0_dyn'].sum),
              'and this the household KW LSTM', household.KW_Stats)
        # to plot in the web map client we need to resample the data to daily
        verlauf_df = verlauf_df.resample('H').sum()
        print('this is the total sum from bdew after resampling', (verlauf_df['h0_dyn'].sum),
              'and this the household KW LSTM', household.KW_Stats)
        # save in 3dwebclient for visualisation
        verlauf_df.to_csv(os.path.join(output_dir_tables_web_map_client, f'{building.building_id}_W{i}_H0SLP_Stats.csv'))

    household_data.to_csv(os.path.join(output_dir_tables_web_map_client, f'{building.building_id}.csv'))

#save as csv
web_client_data.to_csv(os.path.join(output_dir, 'web_client_data_isarvorstadt.csv'))
