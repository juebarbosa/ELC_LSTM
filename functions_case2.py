import random
import time

def av_storey_h_and_h_area_building(building, Volume):
    # Average storey height calculation with CityGML Infos
    #check if building has attributes
    if building.measured_height == '' or building.storeys_above_ground == '':
        print("The building does not have a measured height or storeys above ground")
        return 0,0
    elif hasattr(building, 'measured_height') and hasattr(building, 'storeys_above_ground'):
        measured_height = float(building.measured_height)
        storeys_above_ground = float(building.storeys_above_ground)

        if measured_height > 0 and measured_height is not None and storeys_above_ground > 0 and storeys_above_ground is not None:
            h_g = measured_height / storeys_above_ground
    else:
        print("The building does not have a measured height or storeys above ground")
        return 0,0


    #calculate the buildgins heated area
    if h_g >= 2.5 and h_g <= 3.0:
        A_h = 0.32 * Volume
    else:
        A_h = ((1 / h_g) - 0.04) * Volume

    return h_g, A_h

def isValid(area, remaining_area, remaining_households):
    if area is not None:
        if 40 <= (remaining_area - area) / remaining_households <= 160:
            return True
        else:
            return False



def getNewHouseholdSize():

    # distribution of the heated area to the households
    FDD = [50, 175, 235, 173, 124, 107, 61, 29, 18, 28]
    # generate random integer that can be between 0 and 999 but not 1000
    n = random.randint(0, 999)
    tempSum = 0

    for i in range(0, 9):
        tempSum += FDD[i]

        if n < tempSum:
            area = 20 + i * 20 + random.randint(0, 19)
            return area



def heated_area_per_household(A_h, number_of_households):
    #for some buildings the distributionof the heated area takes too long due to the randomness of this funcitons
    #define a time limit for calculating the heated area per household, otherwise return 0
    start_time = time.time()

    A_h_per_household = []

    remaining_area = A_h
    remaining_households = number_of_households


    for household in range(number_of_households):

        while True:
            if time.time() - start_time > 500:
                print("time limit exceeded for the heated area per household calcualtion")
                return 0

            if remaining_households==1:
                area = remaining_area
                A_h_per_household.append(area)
                return sorted(A_h_per_household)

            # Loop until a valid area is found
            area = getNewHouseholdSize()
            valid= isValid(area, remaining_area, remaining_households - 1)

            if valid:
                A_h_per_household.append(area)
                remaining_area -= area
                remaining_households -= 1
                break  # Exit the while loop and continue to the next household
            else:
                # Restart the loop for the same household by skipping to the beginning of the while loop
                continue



def number_occupants_per_household(area):

    # the statistical data is derived from Destatis 2014
    FDD_occupants = [
        [894, 91, 15, 0, 0, 0],
        [699, 241, 45, 15, 0, 0],
        [421, 383, 126, 55, 15, 0],
        [284, 391, 172, 106, 32, 15],
        [204, 389, 200, 147, 41, 19],
        [153, 357, 218, 193, 56, 23],
        [129, 332, 218, 219, 71, 30],
        [117, 305, 216, 237, 86, 39],
        [112, 293, 212, 239, 97, 47],
        [111, 272, 199, 234, 112, 72]
    ]

    index = int((area - 20) / 20)
    if index > 9:
        index = int(9)

    n = random.randint(0, 999)
    tempSum = 0

    for i in range(0, 5):
        tempSum += FDD_occupants[index][i]
        if n < tempSum:
            number_of_occupants = i + 1
            if number_of_occupants == 6:
                number_of_occupants = 6 + random.randint(0, 2)
            return number_of_occupants


#heated_area_per_household(100, 2)

#print('number of residents for the household with 78m2 in sample 1 and 2: ',number_occupants_per_household(78))
#print('number of residents for the household with 98m2 in sample 3, 4 and 5:',number_occupants_per_household(98))
