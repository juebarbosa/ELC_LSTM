
![visualisation1](https://github.com/user-attachments/assets/76be7847-fa90-402a-ba8d-8ceb90dd3ce7)
![visualisation4](https://github.com/user-attachments/assets/5e8614cc-0d46-466b-a6f9-69c23a645e18)

# ELC_LSTM
Modeling Residential Energy Load Profiles with Semantic 3DCity Models and Machine Learning

this work takes a CityGML file as input and calculates for the residential buildings:
- the number of households at the building level
- for each household:
  - their area
  - number of residents
  - 3 options for the annual electricity consumption (2024) and their plots

For obtaining the updated CityGML file, the tables for using in 3d webclient just run the main.py script. Follow the instructions to run the main script without problems:


- download 3D web map client (documentation: https://3dcitydb-docs.readthedocs.io/en/latest/webmap/)
  - create an folder named "tables_data_households" inside the folder 3Dwebclient
  - the documentation explains how to export your CityGML file as Collada file so the visualisation is possible
  - update the script.js file in the 3dwebclient folder with the script.js file that is in this repository
 
- indtall in your envionroment the following python modules: pathlib, matplotlib, lxml, pandas, requests, geopy, pyproj, numpy, demandlib, keras, tensorflow, scikit-learn

- in the main.py:
  - in line 18 write your own path to the folder 3dwebclient/tables_data_households
  - in line 23 write the name of your own CityGML input file
  - the file Anteile_der_Privathaushalte_in Prozent_nach_Stadtbezirken_2020_komma.csv used in line 140 refers to the statistical data of the city of Munich. This needs to be extended for working with other cities
  - in line 37 the function to parse your CItyGML file may be another one; inspect the functions in the file parse_citygml.py to see which function fits; if any of these functions fits please write an issue
  - in line 383 change the name of the updated output CityGML file
 
- the file create_building_part.py is for CityGML version2.0, it would need editing for cases when working with other versions
  
- in the file functions_case2.py the function heated_area_per_household may take too long for buildings with households with similar sizes due to the randomness
  
- in the file get_neighborhood.py:
  -  needs to adapted for cases when working with other cities than Munich
  -  write in line 62 your own user_agent
  - write in line 134 the path to your CityGML file
  
- in the file volume.py edit on line 153 the file path to your own cityGMl input file

    
NOTE:
this code was tested for a private file from the neighborhood Harthof in Munich and for a 2kmx2km tile downloaded for the neighborhood of Isarvorstadt from https://geodaten.bayern.de/opengeodata/OpenDataDetail.html?pn=lod2 
Slight changes in the CItyGML files can lead to reading errors in the files, for example different namespaces or building attributes. 
