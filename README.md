# ELC_LSTM
Modeling Residential Energy Load Profiles with Semantic 3DCity Models and Machine Learning

For running the main.py please follow the instructions:
- download 3D web map client (documentation: https://3dcitydb-docs.readthedocs.io/en/latest/webmap/)
  - create an folder named "tables_data_households" inside the folder 3Dwebclient
  - the documentation explains how to export your CityGML file as Collada file so the visualisation is possible
 
- indtall in your envionroment the following python modules: pathlib, matplotlib, lxml, pandas, requests, geopy, pyproj, numpy, demandlib, keras, tensorflow, scikit-learn

- in the main.py:
  - in line 18 write your own path to the folder 3dwebclient/tables_data_households
  - in line 23 write the name of your own CityGML input file
  - the file Anteile_der_Privathaushalte_in Prozent_nach_Stadtbezirken_2020_komma.csv used in line 140 refers to the statistical data of the city of Munich. This needs to be extended for working with other cities
  - in line 37 the function to parse your CItyGML file may be another one; inspect the functions in the file parse_citygml.py to see which function fits; if any of these functions fits please write an issue
 
- the file create_building_part.py is for CityGML version2.0, it would need editing for cases when working with other versions
- in the file functions_case2.py the function heated_area_per_household may take too long for buildings with households with similar sizes due to the randomness
- in the file get_neighborhood.py needs to adapted for cases when working with other cities than Munich
- in the file get_neighborhood.py write in line 62 your own user_agent
- in the file volume.py edit on line 153 the file path to your own cityGMl input file

    
