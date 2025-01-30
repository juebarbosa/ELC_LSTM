
def redistribute_households(diff_number_of_residents, number_of_households_per_size_av, household_sizes):
    if diff_number_of_residents < 1:
        abs_diff = abs(diff_number_of_residents)

        # Find the largest household size index
        for i in reversed(range(len(number_of_households_per_size_av))):
            if number_of_households_per_size_av[i] >=  1:
                largest_household_index = i
                break

        number_people_in_largest_households = number_of_households_per_size_av[largest_household_index] * household_sizes[largest_household_index]

        if abs_diff <= number_people_in_largest_households:
            new_number_people_in_largest_households = number_people_in_largest_households - abs_diff

            #check if new number still fits as a household from size largest_household_index
            if (new_number_people_in_largest_households % household_sizes[largest_household_index]) == 0:
                number_of_households_per_size_av[largest_household_index] = new_number_people_in_largest_households / household_sizes[largest_household_index]

            else:
                #divide the new number of people in the largest household by the household size and get the rest of the division
                rest = new_number_people_in_largest_households % household_sizes[largest_household_index]
                #redistribute the rest to the corresponding household size
                for j in household_sizes:
                    if rest == j:
                        number_of_households_per_size_av[j] += 1
                        break
            #make every element of the list a integer

            return number_of_households_per_size_av


        else:
            temp = -(abs_diff - number_people_in_largest_households)
            number_of_households_per_size_av[largest_household_index] = 0
            number_of_households_per_size_av = redistribute_households(temp, number_of_households_per_size_av, household_sizes)


