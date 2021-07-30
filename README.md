# 3D House Project
## Project Access
The project can be found in my [portfolio](https://3d.olivier.dotreppe.be/start)

## Tech used
- Python, Rasterio, Pandas, Plotly.
- Coded in a Class and as a Python Package
- Showcased in a Flask powered website:
  - Coded in HTML/CSS, with Bootstrap. The login function has now been deactivated.
  - an AJAX script allows to select and display information about the buildings
  - Initially a CI/CD was configured to check and pushing to Heroku.  The checks included Flake8 as a linter, and some unittest.
  - Now the docker image runs on a Debian powered VPS running Nginx.
- a quick and dirty cache system is in place as 
- Contained in a Docker Image

## The Data: DSM and DTMs to get CHM's!
The ressources have been found on the Geoportal of the public service of Wallonia's (SPW) website.
You can download them here: 
 - [Digital Terrain Model (DTM)](http://geoportail.wallonie.be/catalogue/7d23d8ab-962a-493f-8771-2054e06ad36f.html)
 - [Digital Surface Model (DSM)](http://geoportail.wallonie.be/catalogue/6029e738-f828-438b-b10a-85e67f77af92.html)
 - [Bâtiments 3D 2013-2014](https://geoportail.wallonie.be/catalogue/4de94d5d-9036-4953-beca-3ff76e4b1ec8.html)\

DSM, DTM and Canopy height model (CHM) are three important terms in this project!:
<img align="center" src="https://i.stack.imgur.com/1l3EA.png" />

## How does it works?
- it all starts with an address that we want to work from, let's take my school's address!
"1 Rue de Crehen Hannut" and the area we want to plot around (let's take boundary=200m!)
- search_address_mapbox(): will call mapbox's API to return the coordinates of the adress: (X, Y). it will add the boundary around that point to obtain a bounding box that we will plot (xMin, xMax, yMin, yMax)
- find_files(): it will loop through each MNS/MNT file to check if the bounding box fits within.
- create_chm(): it will first crop the MNS and MNT Tiff files to the correct size, and create the CHM by substracting them.
- create_plotly_map(): will create the map based on the CHM and save it to HTML

## ToDo?
- Improve the speed!
- I'm not happy either on how the cache is managed.
