from lxml import etree


# Helper function to create a BuildingPart with household size and KW attributes
def create_building_part(household_size, household_kw_lstm, household_kw_stats, household_area, household_number, namespaces):
    ns_gen = namespaces['gen']  # Generic attributes namespace
    ns_bldg = namespaces['bldg']  # Building namespace

    # Create the consistsOfBuildingPart element
    consists_of_building_part = etree.Element(f"{{{ns_bldg}}}consistsOfBuildingPart")
    # Create the BuildingPart element
    building_part = etree.Element("{http://www.opengis.net/citygml/building/2.0}BuildingPart")

    # Add the Household attribute
    household_attribute = etree.Element(f"{{{ns_gen}}}stringAttribute", name="Household")
    household_value = etree.SubElement(household_attribute, f"{{{ns_gen}}}value")
    household_value.text = str(household_number)
    building_part.append(household_attribute)

    # Add the size attribute
    size_attribute = etree.Element(f"{{{ns_gen}}}stringAttribute", name="number_of_residents")
    size_value = etree.SubElement(size_attribute, f"{{{ns_gen}}}value")
    size_value.text = str(household_size)
    building_part.append(size_attribute)

    # Add the area attribute
    size_attribute = etree.Element(f"{{{ns_gen}}}stringAttribute", name="area")
    size_value = etree.SubElement(size_attribute, f"{{{ns_gen}}}value")
    size_value.text = str(household_area)
    building_part.append(size_attribute)

    # Add the Kundenwert LSTM (KW) attribute
    kw_lstm_attribute = etree.Element(f"{{{ns_gen}}}stringAttribute", name="ELC_LSTM")
    kw_lstm_value = etree.SubElement(kw_lstm_attribute, f"{{{ns_gen}}}value")
    kw_lstm_value.text = str(household_kw_lstm)
    building_part.append(kw_lstm_attribute)

    # Add the Kundenwert Stats (KW) attribute
    kw_stats_attribute = etree.Element(f"{{{ns_gen}}}stringAttribute", name="ELC_Stats")
    kw_stats_value = etree.SubElement(kw_stats_attribute, f"{{{ns_gen}}}value")
    kw_stats_value.text = str(household_kw_stats)
    building_part.append(kw_stats_attribute)

    # Append the BuildingPart to consistsOfBuildingPart
    consists_of_building_part.append(building_part)

    return consists_of_building_part
