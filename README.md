# Quantitative Risk Assessment (QRA) tool prototype

![alt text](https://raw.githubusercontent.com/undefiened/QRA_tool/main/banner.png "A banner showing a screenshot of the tool")

A web application for computing the number of people exposed to risk from drone operation as well as the air risk of an operation.

The tool original prototype was developed by [AEAR group](https://sites.google.com/view/aeargroup/home) from Linköping University together with LFV and is available at https://undefiened.github.io/uav_risk/.

This fork is available at https://tiagomig.github.io/QRA_tool/.

The population density data for Swedish maps is derived from the [Statistics Sweden](https://www.scb.se/)'s data provided via [Swedish University of Agricultural Sciences](http://www.slu.se/en/).

For the Canary islands, the population density map was converted from GeoTiff to GeoJSON from the file "GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R6_C17.tif".

The air traffic data is derived from the data obtained from [OpenSky Network](https://opensky-network.org/).

A Python script was added to extract live data around the map extent coordinates (duration and frequency configurables).

Please contact Leonid Sedov (leonid.sedov@liu.se) for all questions related to the original repository (https://github.com/undefiened/QRA_tool) or Tiago Grossinho (tiago [DOT] grossinho [AT] gmail [DOT] com) for all questions related to this fork.

# Compilation instructions

## Query traffic data
- If you have an Opensky licence to extract historical data:
  - Run python data_querying.py and edit the airport ICAO code and date/time information prior to running
- If not, you can use data_querying_live.py to extract live data over a certain time extent (in real time), and based on the xxx_extent.geojson file, to reduce the queries to Opensky

## Process GeoJSON
- Run data_processing.py and edit the input/output files inside
NOTE that the population property must be called "Totalt" in the input file

## Clean output GeoJSON
- Run data_cleaning.py and edit the input/output files inside
This may make the output file a bit smaller

## To compile bundle.js
- You need to download JNode (node + npm). Then execute:
  - SET PATH=%PATH%;<NPM_PATH>\node-v24.13.0-win-x64\
  - npm install
  - npx webpack --mode production (to compile into production)
  - npx webpack --mode development --devtool source-map --watch (to add debug information and compile in dev, ie recompile each time a file is modified)

## To deploy locally
- Run python -m http.server 8080 --bind 127.0.0.1
