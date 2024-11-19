"""
- from google
    - https://cloud.google.com/storage/docs/public-datasets/landsat
- GeoTIFFS
- historical only (2013 - 2021)
- Level 1
"""


"""
The images are organized in the Worldwide Reference System (WRS-2) grid, which is a global grid dividing the world into 251 orbital paths and 248 rows. Different Landsat satellites have used sensors with slightly different characteristics, so Cloud Storage organizes the data by sensor in the following effective directory structure:

/SENSOR_ID/01/PATH/ROW/SCENE_ID/

The components of this path are:

    SENSOR_ID: An identifier for the particular satellite and camera sensor.
    01: An indicator that the data is part of Landsat Collection 1.
    PATH: The WRS path number.
    ROW: The WRS row number.
    SCENE_ID: The unique scene ID.

As an example, one Landsat 8 scene over California can be found here:

gs://gcp-public-data-landsat/LC08/01/044/034/LC08_L1GT_044034_20130330_20170310_01_T2/

To help locate data of interest, an index CSV file of the Landsat data is available. This CSV file lists basic properties of the available images, including their acquisition dates and their spatial extent as minimum and maximum latitudes and longitudes. The file is found in the Landsat Cloud Storage bucket:

gs://gcp-public-data-landsat/index.csv.gz


"""