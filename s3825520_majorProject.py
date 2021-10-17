
########## Forest Plantation Suitability ##########

### Project Setup ###

# project data filepath is defined
filepath = "C:/Users/Dell/Desktop/testing/sample_data/"

# Modify the forest Year according to the data file
StartYear = "forest_2010.tif"   # e.g forest_2015.tif, forest_2020.tif etc.
EndYear = "forest_2017.tif"     # e.g forest_2015.tif, forest_2020.tif etc.
forest_pixel = "(A == 8)" # e.g forest pixel value = 8, 9 etc..

# Vector layer names are setup
districtFilename = "district.shp"
roadFileName = "road.shp"
settlementFileName = "settlement.shp"
rfppfFileName = "rfppf.shp" # reserved and protected public forest boundary

# add vector layers to QGIS
districtLayer = iface.addVectorLayer(filepath + districtFilename, districtFilename[:-4],"ogr")
roadLayer = iface.addVectorLayer(filepath + roadFileName, roadFileName[:-4],"ogr")
settlementLayer = iface.addVectorLayer(filepath + settlementFileName, settlementFileName[:-4],"ogr")
rfppflayer = iface.addVectorLayer(filepath + rfppfFileName, rfppfFileName[:-4],"ogr")


# create new folder to store standardised rasters
standardized_output = filepath + "standardized_output/" 
if not os.path.exists(standardized_output):
    os.makedirs(standardized_output)

# create new folder for intermediate output
intermediate = filepath + "intermediate/" 
if not os.path.exists(intermediate):
    os.makedirs(intermediate)

# create new folder for landcover output
landcover_filepath = filepath + "landcover/"
# load landcover maps
# create new folder for output
landcover_clipped = landcover_filepath + "clipped/" 
if not os.path.exists(landcover_clipped):
    os.makedirs(landcover_clipped)

# create new folder for Suitability output 
Suitability_output = filepath + "Suitability_output/" 
if not os.path.exists(Suitability_output):
    os.makedirs(Suitability_output)

    
#################### Deforestation ####################

##### clip all landcover by district and extract forest area only #####  
for file in os.listdir(landcover_filepath):
    #only do this stuff for the tif
    if file.endswith(".tif"):
        outputFileName = file[:-4] + '_clipped' + file[-4:]
        
        # clip the landcover
        clip_parameters = {"INPUT":(landcover_filepath + file),"MASK":districtLayer,"OUTPUT":(landcover_clipped + outputFileName)}
        processing.run("gdal:cliprasterbymasklayer",clip_parameters)   
        
        # take the clipped landcover
        landcover = QgsRasterLayer(landcover_clipped + outputFileName)
#               
        # extract forest area
        forestFileName = "forest_" + file[4:8] + file[-4:]
        extract_forest = forest_pixel
        parameters = {"INPUT_A":landcover,"BAND_A":1,"FORMULA":extract_forest,"OUTPUT":(landcover_clipped + forestFileName)}
        processing.run('gdal:rastercalculator', parameters)


##### calculate deforestation area #####
forest_StartLayer = QgsRasterLayer(landcover_clipped + StartYear) # load forest cover startYear
forest_EndLayer = QgsRasterLayer(landcover_clipped + EndYear) # load forest cover endYear
 
deforestation = "((A * 10) + B)"  # change pixel calculation
parameters = {"INPUT_A":forest_StartLayer,"BAND_A":1,"INPUT_B":forest_EndLayer,"BAND_B":1,"FORMULA":deforestation,"OUTPUT":(intermediate + "deforestation.tif")}
processing.run('gdal:rastercalculator', parameters)

# extract deforestation layer
deforestation = QgsRasterLayer(intermediate + "deforestation.tif")
parameters = {"INPUT_A":deforestation,"BAND_A":1,"FORMULA":"(A == 10)","OUTPUT":(standardized_output + "deforestation.tif")}
processing.run('gdal:rastercalculator', parameters)


#################### Location Index ####################   

##### create distance rasters for settlement and road #####

### first convert settlement and road vectors to rasters

## settlement raster
rasterize_settlement_parameters = {"INPUT":settlementLayer,"FIELD":"id","UNITS":1,"WIDTH":30,"HEIGHT":30,"EXTENT":settlementLayer,"NODATA":0.0,"OUTPUT":(intermediate + "settlement.tif")}
processing.run("gdal:rasterize",rasterize_settlement_parameters)

# settlement distance
settlementLayer = QgsRasterLayer(intermediate + "settlement.tif")
settlement_distance_parameters = {"INPUT":settlementLayer,"BAND":1,"UNITS":0,"NODATA":0.0,"OUTPUT":(filepath + "settlement_distance.tif")}
processing.run("gdal:proximity",settlement_distance_parameters)

settlement_distance_FileName = "settlement_distance.tif"  # add layer to Qgis
settlementLayer = iface.addRasterLayer(filepath + settlement_distance_FileName, settlement_distance_FileName[:-4],"gdal")

## road raster

rasterize_road_parameters = {"INPUT":roadLayer,"FIELD":"id","UNITS":1,"WIDTH":30,"HEIGHT":30,"EXTENT":roadLayer,"NODATA":0.0,"OUTPUT":(intermediate + "road.tif")}
processing.run("gdal:rasterize",rasterize_road_parameters)

# road distance
roadLayer = QgsRasterLayer(intermediate + "road.tif")
road_distance_parameters = {"INPUT":roadLayer,"BAND":1,"UNITS":0,"NODATA":0.0,"OUTPUT":(filepath + "road_distance.tif")}
processing.run("gdal:proximity",road_distance_parameters)

road_distance_FileName = "road_distance.tif" # add layer to Qgis
roadLayer = iface.addRasterLayer(filepath + road_distance_FileName, road_distance_FileName[:-4],"gdal")

# calculate slope
dem_raster_FileName = "DEM.tif" # add DEM 
demLayer = iface.addRasterLayer(filepath + dem_raster_FileName, dem_raster_FileName[:-4],"gdal")

slope_parameters = {"INPUT":demLayer,"BAND":1,"OUTPUT":(filepath + "slope.tif")}  # slope calculation parameters
processing.run("gdal:slope",slope_parameters)

slope_raster_FileName = "slope.tif"
slopeLayer = iface.addRasterLayer(filepath + slope_raster_FileName, slope_raster_FileName[:-4],"gdal")

# create new folder to store clip rasters (DEM,slope, road, settlement)
clipped_output = filepath + "clipped/" 
if not os.path.exists(clipped_output):
    os.makedirs(clipped_output)
    
# clip all rasters by district
suffix = "_clip"
for file in os.listdir(filepath):
    #only do this stuff for the tif
    if file.endswith(".tif"):
        outputFileName = file[:-4] + suffix + file[-4:]
        clip_parameters = {"INPUT":(filepath + file),"MASK":districtLayer,"OUTPUT":(clipped_output + outputFileName)}
        processing.run("gdal:cliprasterbymasklayer",clip_parameters)
        
   
### standarised all rasters (dem, slope, settlement,road)
for file in os.listdir(clipped_output):
    if file.endswith('.tif'):
        # import raster
        filelayer = iface.addRasterLayer((clipped_output + file), file[:-4],"gdal")
        
        # get statistics of the raster
        stats = filelayer.dataProvider().bandStatistics(1, QgsRasterBandStats.All)
        min = stats.minimumValue
        max = stats.maximumValue
        max_min= max-min
        outputFileName = file[:-4] + '_standardized' + file[-4:]
        
        # calculate the standardization of the raster
        formula = "(A-{0})/{1}".format(min,max_min)
        parameters = {"INPUT_A":filelayer,"BAND_A":1,"FORMULA":formula,"OUTPUT":(standardized_output + outputFileName)}
        processing.run('gdal:rastercalculator', parameters)
        
    

#################### Suitabilitiy calculation (weighted sum calculation) ####################

### Load standardized files
deforestationlayer = QgsRasterLayer(standardized_output + "deforestation.tif")
slopelayer = QgsRasterLayer(standardized_output + "slope_clip_standardized.tif")
roadlayer = QgsRasterLayer(standardized_output + "road_distance_clip_standardized.tif")
settlementlayer = QgsRasterLayer(standardized_output + "settlement_distance_clip_standardized.tif")
demlayer = QgsRasterLayer(standardized_output + "DEM_clip_standardized.tif")


### Prepare for Raster calculation
output = Suitability_output + "SuitableArea.tif"

entries = []

# deforestation
deforestation = QgsRasterCalculatorEntry()
deforestation.ref = 'deforestation@1'
deforestation.raster = deforestationlayer
deforestation.bandNumber = 1
entries.append(deforestation)


# slope
slope = QgsRasterCalculatorEntry()
slope.ref = 'slope@1'
slope.raster = slopelayer
slope.bandNumber = 1
entries.append(slope)

# road
road = QgsRasterCalculatorEntry()
road.ref = 'road@1'
road.raster = roadlayer
road.bandNumber = 1
entries.append(road)

# settlement
settlement = QgsRasterCalculatorEntry()
settlement.ref = 'settlement@1'
settlement.raster = settlementlayer
settlement.bandNumber = 1
entries.append(settlement)

# DEM
dem = QgsRasterCalculatorEntry()
dem.ref = 'dem@1'
dem.raster = demlayer
dem.bandNumber = 1
entries.append(dem)


##### raster calculator setup for weighted sum #####
calc = QgsRasterCalculator('(deforestation@1 * ((0.4*slope@1)+(0.3*road@1) + (0.2*settlement@1)+(0.1*dem@1)))', output,'GTiff',\
demlayer.extent(),demlayer.width(),demlayer.height(),entries)
calc.processCalculation()

outputfile = "SuitableArea.tif"
outputfile = iface.addRasterLayer(Suitability_output + outputfile, outputfile[:-4],"gdal")


##### reclassify the resulting suitable area #####

stats = outputfile.dataProvider().bandStatistics(1, QgsRasterBandStats.All) # get the raster statistics

class_break = (stats.maximumValue)/3   # three categories are used for reclassification

### define classification break
class_1 = 0.0000000001
class_2 = class_break
class_3 = class_break * 2
class_max = stats.maximumValue

table = [class_1,class_2,1,class_2,class_3,2, class_3,class_max,3] # classification breaks are prepared in a list

parameters = {'INPUT_RASTER':outputfile,'RASTER_BAND':1,
            'TABLE':table,'NO_DATA':-9999,'RANGE_BOUNDARIES':2,'DATA_TYPE':0,
            'OUTPUT':(Suitability_output + 'Suitablility_class.tif')}

processing.run('qgis:reclassifybytable',parameters)

suitable_class = "Suitablility_class.tif"
suitable_class = iface.addRasterLayer(Suitability_output + suitable_class, suitable_class[:-4],"gdal")



# calculate Suitability_class for each reserved forest (rfppf)

zonal_parameters = {"INPUT_RASTER":suitable_class,"RASTER_BAND":1,"INPUT_VECTOR":rfppflayer,
                "COLUMN_PREFIX":"class_","OUTPUT":(Suitability_output + "Suitability_level.shp")}
processing.run("native:zonalhistogram",zonal_parameters)

suitable_level = "Suitability_level.shp"
suitable_level = iface.addVectorLayer(Suitability_output + suitable_level, suitable_level[:-4],"ogr")


##### calculate area in hectares for suitability level #####

### add Area fields

suitable_level.startEditing()
addFields = suitable_level.dataProvider().addAttributes([QgsField('level_1', QVariant.Double),QgsField('level_2', QVariant.String),QgsField('level_3', QVariant.Double)])
suitable_level.updateFields()
suitable_level.commitChanges()


### calculate area
# Area calculation expression

# level_1 area in ha
level_1_expression = QgsExpression('(class_1 * 30 * 30)/10000')
context = QgsExpressionContext()
context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(suitable_level))

# level_2 area in ha
level_2_expression = QgsExpression('(class_2 * 30 * 30)/10000')
context = QgsExpressionContext()
context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(suitable_level))

# level_3 area in ha
level_3_expression = QgsExpression('(class_3 * 30 * 30)/10000')
context = QgsExpressionContext()
context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(suitable_level))

# areas for each level are calculated for each feature within a "for" loop
with edit(suitable_level):
    for feature in suitable_level.getFeatures():
        context.setFeature(feature)
        
        #calculate level_1 area in ha
        feature["level_1"] = level_1_expression.evaluate(context)
        
        #calculate level_2 area in ha
        feature["level_2"] = level_2_expression.evaluate(context)
        
        #calculate level_3 area in ha
        feature["level_3"] = level_3_expression.evaluate(context)
        
        suitable_level.updateFeature(feature)
        

# delete unnecessary columns
delete_fields = ['class_0','class_1','class_2','class_3','class_241'] # list the unnecessary fields

# loop all fields and find the target fields to delete
for field in delete_fields:
    # get the index of the field
    field_index = suitable_level.fields().indexFromName(field)
    
    # delete the field using the its index
    layer_provider=suitable_level.dataProvider()
    layer_provider.deleteAttributes([field_index])
    suitable_level.updateFields()
    

# The final output file is "Suitability_level.shp" which have three columns for each level. Area is in hecture.
    # Level_1 for high suitability
    # Level_2 for medium suitability
    # Level_3 for low suitability

# RF_NAME field holds the reserved forests in the district.



