# in this script we have the functions that will estimate the number of
#residents per household in the case we have the number of residents and households
#in the building

#in this script we will also have the functions that will determine the
#number of residents, households and number os residents per household in the
#case we don't have the input from the xml file

import pandas as pd
import get_neighborhood
import redistribute_case_diff_smaller_1
from volume import volume_building_2
import functions_case2 as fc2

def estimate_number_of_residents_per_household( file_path, building):
    #read csv file containing the percentage of each household size in each neighboorhood in munich
    #this file needs to be given by the main script
    #in the case of using another city, the file needs to be adapted
    df = pd.read_csv(file_path)

    #defines if building will go through the general method or the method for complete data buildings
    #In the case of complete data buildings the code calculates the number of households with certain sizes based on the already given
    #number of residents and households
    if building.complete == True:

        # Get the city block of the building
        city_block = get_neighborhood.get_suburb(building)

        # get the values of the dataframe, der richtige Verhältnis von Einwohner pro Wohneinheit bezüglich der Bezirk
        # Strip any leading or trailing whitespace characters from 'Bezirk' column
        df['Bezirk'] = df['Bezirk'].str.strip()

        # Find the row where 'Bezirk' matches the city_block
        row = df[df['Bezirk'] == city_block]

        if row.empty:
            print(f"City block '{city_block}' not found in the DataFrame.")
            #sucess = False
            temp = []
            case = 0
            return case,  temp, 0, 0

        # Extract values from columns '1 Person' to '5 Personen' for the identified row
        prozent_householdsize_cityblock = row.iloc[0][1:].tolist()

        household_sizes = [1, 2, 3, 4, 5]

        number_of_residents_in_building = int(building.num_of_inhabitants)
        number_of_households_in_building = int(building.number_of_building_units)

        #estimate number of households from each size based on average data
        number_of_households_per_size_av = [percent * number_of_households_in_building for percent in prozent_householdsize_cityblock]

        # Calculate the sum before rounding
        initial_sum = sum(number_of_households_per_size_av)

        # Round the estimated number of households per size
        rounded_number_of_households_per_size_av = [round(num) for num in number_of_households_per_size_av]

        # Calculate the difference
        rounded_sum = sum(rounded_number_of_households_per_size_av)
        difference = initial_sum - rounded_sum

        # Adjust the largest element to compensate for the difference
        if difference != 0:
            idx = number_of_households_per_size_av.index(max(number_of_households_per_size_av))
            rounded_number_of_households_per_size_av[idx] += int(difference)

        # Final rounded values
        number_of_households_per_size_av = rounded_number_of_households_per_size_av

        #number of residents based on the average data
        number_of_residents_in_building_av = sum(
            size * households for size, households in zip(household_sizes, number_of_households_per_size_av)
        )

        #diference between the number of residents providede by the gml file and the number calculated from the average data
        diff_number_of_residents = number_of_residents_in_building - number_of_residents_in_building_av

        #if the difference is larger than 8, the Table in the Robert Kaden Methode is not defined for this situation
        #therefore use the case 2 for buildings with incomplete data
        if diff_number_of_residents > 8:
            case, number_of_households_per_size_final, A_h_per_household, volume = estimate_number_of_residents_case_incomplete(building)

            #return case, number_of_households_per_size_final, A_h_per_household, volume

        #if the difference is smaller than 0, the code will redistribute the residents in the households so the number of residents is the same as the gml file
        #here there is a bug with the return of the function redistribute_case_diff_smaller_1.redistribute_households
        elif diff_number_of_residents < 0:
            number_of_households_per_size_final = redistribute_case_diff_smaller_1.redistribute_households(diff_number_of_residents, number_of_households_per_size_av, household_sizes)
            number_of_households_per_size_final = [int(i) for i in number_of_households_per_size_av]

            case = 1


        else:
            final_diff_number_of_residents, values_list = check_and_give_back_values("Schema Personen Differenz.csv", diff_number_of_residents)
            #final number of households with the specific number of residents
            number_of_households_per_size_final = []

            for i in range (4):
                number_of_households_per_size_final.append(number_of_households_per_size_av[i] + values_list[i])
            number_of_households_per_size_final.append(number_of_households_per_size_av[4])

            #check if there is a negative element in the list
            for i in number_of_households_per_size_final:
                if i < 0:
                    case, number_of_households_per_size_final, A_h_per_household , volume= estimate_number_of_residents_case_incomplete(
                        building)


                else:
                    continue



        #check if the number of residents is the same as the citygml file after the whole process
        check = [num * size for num, size in zip(number_of_households_per_size_final, household_sizes)]
        check = sum(check)


        if check == number_of_residents_in_building:
            #sucess = True
            case = 1
            #print(number_of_households_per_size_final)
            #return case,  number_of_households_per_size_final, A_h_per_household

        # even for buildings in case 1, it is needed to calculate the volume of the building and the heated area per household
        # with functions that come from the case 2 for lather steps(Kundenwert calculation)
        measured_height = float(building.measured_height)
        volume = volume_building_2(building.building_id)

        if volume == 0:
            print("Volume Calculations failed")
            number_of_households_per_size_final = [0, 0, 0, 0, 0]
            return 0, number_of_households_per_size_final, 0, 0

        # calculate the average storey height and the buildings heates area
        h_g, A_h = fc2.av_storey_h_and_h_area_building(building, volume)

        if h_g == 0 or h_g == None or A_h == 0 or A_h == None:
            return 0, [0, 0, 0, 0, 0], 0, 0

        #calculate the heated area per household
        A_h_per_household = fc2.heated_area_per_household(A_h, sum(number_of_households_per_size_final))
        if A_h_per_household == 0:
            case = 0
        return case, number_of_households_per_size_final, A_h_per_household, volume

    #in the case of buildings with incomplete data the code will calculate the number of households with certain sizes based on the volume of the building
    elif building.complete == False:

        case, number_of_households_per_size_final, A_h_per_household, volume = estimate_number_of_residents_case_incomplete(building)
        return case, number_of_households_per_size_final, A_h_per_household, volume



def estimate_number_of_residents_case_incomplete(building):

    #Volume calculation with SQL query 3DCityDB and SG_Volume
    measured_height = float(building.measured_height)
    V= volume_building_2(building.building_id)

    if V == 0:
        print("Volume Calculations failed")
        number_of_households_per_size_final = [0, 0, 0, 0, 0]
        return 0, number_of_households_per_size_final, 0, 0

    #calculate the average storey height and the buildings heates area
    h_g, A_h = fc2.av_storey_h_and_h_area_building(building, V)

    if h_g == 0 or h_g == None or  A_h == 0 or A_h == None:
        return 0, [0, 0, 0, 0, 0], 0, 0

    # now we calculate the number of households per building

    # define type of building
    if A_h > 130.8 :
        building_type = "MFH"
    elif A_h <= 130.8:
        building_type = "SFH"
    ''''couldnt find the the conditions for Apartment Blocks and High rise buildings'''

    # calculate number of households
    if building_type == "MFH":
        number_of_households = round(A_h / 80.2)
        # reduction of the total heated area by 41% accounting for the buildings service areas
        # circulation areas and structural areas
        A_h = A_h* 0.59
    elif building_type == "AB":
        number_of_households = round(A_h / 62.4)
        A_h = A_h * 0.59
    elif building_type == "HRB":
        number_of_households = round(A_h / 54.3)
        A_h = A_h * 0.59
    elif building_type == "SFH":
        number_of_households = 1


    # distribution of household areas to the number of existing households based on Table 1 FDD for household areas
    # a pseudo random number is used to recreate the same distribution of households

    A_h_per_household = fc2.heated_area_per_household(A_h, number_of_households)
    if A_h_per_household == 0:
        return 0,0,0,0

    # estimate the number of occupants per household
    # this is based on the same greedy approach and assesses the number of occupants per
    # household based on an FDD
    # the statistical data is derived from Destatis 2014

    number_of_households_per_size_final =[0, 0, 0, 0, 0, 0]

    for household in range(len(A_h_per_household)):
        number_of_occupants = fc2.number_occupants_per_household(A_h_per_household[household])


        # build the list that will return the number of households with certain sizes
        if number_of_occupants == 1:
            number_of_households_per_size_final[0] += 1
        elif number_of_occupants == 2:
            number_of_households_per_size_final[1] += 1
        elif number_of_occupants == 3:
            number_of_households_per_size_final[2] += 1
        elif number_of_occupants == 4:
            number_of_households_per_size_final[3] += 1
        elif number_of_occupants == 5:
            number_of_households_per_size_final[4] += 1
        elif number_of_occupants == 6:
            number_of_households_per_size_final[4] += 1
        elif number_of_occupants == 7:
            number_of_households_per_size_final[4] += 1
        elif number_of_occupants == 8:
            number_of_households_per_size_final[4] += 1

    return 2, number_of_households_per_size_final, A_h_per_household, V



def check_and_give_back_values(csv_filename, diff_number_of_residents):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_filename)

    # Extract the first column (assuming it contains the values to check)
    values = df.iloc[:, 0]

    # Initialize the result list
    result_list = []

    # Check if the value is exactly in the first column
    if diff_number_of_residents in values.values:
        row = df[values == diff_number_of_residents]
        result_list = row.iloc[0, 1:5].tolist()
        return diff_number_of_residents, result_list

    elif diff_number_of_residents == 0:
        result_list = [0,0,0,0]
        return diff_number_of_residents, result_list
