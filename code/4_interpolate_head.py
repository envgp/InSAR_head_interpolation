#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 14:00:22 2022

This script will do two things:
    1) use the search radius to create the interpolated head surface for each year/season
    2) use the same approach to interpolate the Alam/Scanlon style head data. Use the same search radii.

@author: mlees
"""

# MANUALLY ENTER THE SEARCH RADIUS TO USE FOR EACH YEAR/SEASON. Get this from "coverage_summary_newshallowdataset"
searchradius_dict = {'Fall 2015':7.50 ,'Spring 2015':7.0, 'Fall 2016':9.5, 'Spring 2016':5.50, 'Fall 2017':5.50, 'Spring 2017':13.00, 'Fall 2018':6.5 ,'Spring 2018':6.00, 'Fall 2019':6.50, 'Spring 2019':5.5 ,'Fall 2020':8.00 ,'Spring 2020':9.00,'Fall 2021':8.00 ,'Spring 2021':11.50 }

# Import modeles and data
import sys
sys.path.append('/home/mlees/InSAR_processing/postprocessing_scripts/')
sys.path.append('/Users/mlees/Documents/RESEARCH/InSAR_processing/postprocessing_scripts/')
from InSAR_postSBAS import *
import pygmt
import numpy as np
from netCDF4 import Dataset
import os 
import csv

def gmtgrdmath(arg_str):
    '''Matt's bodge wrapper since pygmt haven't made one yet.'''
    from pygmt.clib import Session
    with Session() as lib:
        lib.call_module("grdmath", arg_str)

FEET_TO_M = 0.3048

new_shallow_dataset_fileloc='../CreatingNewHeadDataset/NewShallowHeadMeasurementsDataset.csv'

print('Importing New Shallow Head Measurements from: "%s".' % new_shallow_dataset_fileloc)
print('\tFilesize found to be %s.' % file_size(new_shallow_dataset_fileloc))
new_shallow_dataset = pd.read_csv(new_shallow_dataset_fileloc)

print('Total number of imported measurements = %i' % len(new_shallow_dataset))
print("Clipping to study area... this is a sanity check as there shouldn't be anything outside the study area")
tulekaweahoutline = import_kml_polygon('../Geospatial_data/KaweahTuleSubbasins_Merged.kml')
tulekaweahsatoutline = import_kml_polygon('../Geospatial_data/KaweahTuleSubbasins_SaturatedMerged.kml')

new_shallow_dataset_TuleKaweah = extract_from_polygon(tulekaweahsatoutline[0],tulekaweahsatoutline[1],new_shallow_dataset) # Check we only have Tule/Kaweah data - for new shallow msmts, only use the saturated bit.


# Import the periodic measurements head data, to be used for the Scanlon and Alam-style interpolation
print('Importing DWR periodic measurements...')
seasonalwelldata_PeriodicMeasurementsAll = pd.read_csv('../Data_RAW/Head/DWR_PeriodicGroundwaterLevels/PeriodicMeasurements_InSeasonalFormat.csv')
seasonalwelldata_PeriodicMeasurementsAll.dropna(subset=['WSE'],inplace=True) # Remove entries with a Nan measurement
seasonalwelldata_PeriodicMeasurements_TuleKaweah = extract_from_polygon(tulekaweahoutline[0],tulekaweahoutline[1],seasonalwelldata_PeriodicMeasurementsAll) # Check we only have Tule/Kaweah data - for periodic all don't only use the saturated bit.

plotting_region = '%.2f/%.2f/%.2f/%.2f' % (np.min(tulekaweahoutline[0])-0.02,np.max(tulekaweahoutline[0])+0.02,np.min(tulekaweahoutline[1])-0.02,np.max(tulekaweahoutline[1])+0.08)

gridding_region = '%.2f/%.2f/%.2f/%.2f' % (np.min(tulekaweahoutline[0])-0.01,np.max(tulekaweahoutline[0]),np.min(tulekaweahoutline[1])-0.01,np.max(tulekaweahoutline[1]))

#%% Make the interpolated surface for each season/year combo, NewShallowDataset

spacing=1 # This is the grid spacing, in km. In the paper I set this to 1km.
make_map = True

print('Making interpolated surface for new shallow head dataset.')
for year in [2015,2016,2017,2018,2019,2020,2021]: # First set zero time
    for season in ["Spring","Fall"]:
        print('Doing %s %s with search radius %.2f.' % (season, year,searchradius_dict['%s %s' % (season, year)]))
        logical_tmp = np.all([new_shallow_dataset_TuleKaweah['MSMT_YEAR']==year,new_shallow_dataset_TuleKaweah['MSMT_SEASON']==season],axis=0)

        points_tmp = np.array([new_shallow_dataset_TuleKaweah['Longitude'][logical_tmp],new_shallow_dataset_TuleKaweah['Latitude'][logical_tmp],FEET_TO_M * new_shallow_dataset_TuleKaweah['WSE'][logical_tmp]]).T # Find the head measurements to be used for the V0 calc

        head_tmp_emptyasnan = pygmt.binstats(points_tmp,region=gridding_region,spacing='%ik+e' % spacing,statistic='a',search_radius='%.2fk' % searchradius_dict['%s %s' % (season, year)],registration='p') # Do the spatial averaging once, filling any empty nodes with nan
        # pygmt.binstats(points_tmp,region=gridding_region,spacing='%ik+e' % spacing,statistic='a',search_radius='%.2fk' % searchradius_dict['%s %s' % (season, year)],registration='p',empty=np.nanmean(head_tmp_emptyasnan),outgrid='tempout.nc') # Now repeat the process, but this time fill empty nodes with the mean of the previous version and save to a file so I can use with gmtgrdmath.
        pygmt.binstats(points_tmp,region=gridding_region,spacing='%ik+e' % spacing,statistic='a',search_radius='%.2fk' % searchradius_dict['%s %s' % (season, year)],registration='p',empty=-9999,outgrid='tempout.nc') # Now repeat the process, but this time fill empty nodes with -9999 and save to a file so I can use with gmtgrdmath.
        #gmtgrdmath('tempout.nc ../Geospatial_data/GridMasks/DummyGridMask_TuleKaweahSaturated_spacing%.2f.nc MUL = Interpolated_Head_NewShallowDataset/%s%s.nc' % (spacing,season,year)) # Clip the result to the SATURATED study area and save the resulting interpolated grid.
        #gmtgrdmath('tempout.nc ../Geospatial_data/GridMasks/DummyGridMask_TuleKaweahSaturated_spacing%.2f.nc MUL = tmp_clipped.nc' % spacing) # Clip the result to the SATURATED study area and save the resulting interpolated grid.
        pygmt.grdfill('tempout.nc',outgrid='tmp_filled.nc',mode='n',N=-9999) # NEW SECTION: this takes the -9999 values and instead makes them the nearest non-Nan value...
        gmtgrdmath('tmp_filled.nc ../Geospatial_data/GridMasks/DummyGridMask_TuleKaweahSaturated_spacing%.2f.nc MUL = Interpolated_Head_NewShallowDataset/%s%s_NEWINTERP.nc' % (spacing,season,year)) # Clip the result to the SATURATED study area and save the resulting interpolated grid.
        
    
        if make_map: # Plot a map if desired
            Fig = pygmt.Figure()
            Fig.basemap(region=plotting_region,projection='M12c',frame=["a","+t%s %s" % (year,season)])
            pygmt.makecpt(series=[-55,180])
            Fig.grdimage('Interpolated_Head_NewShallowDataset/%s%s_NEWINTERP.nc' % (season,year),cmap=True,nan_transparent=True)
            #Fig.grdimage('final_clipped_tmp.nc',cmap=True,nan_transparent=True)
       
            Fig.plot(data='../Geospatial_data/KaweahTuleSubbasins_Merged.txt',pen='fat,black',label='Kaweah Tule subbasin outline')
            
            # Plot the well locations
            Fig.plot(x=points_tmp[:,0],y=points_tmp[:,1],style='E0/0.5k/0.5k',color='black',label='Wells')
            
            with pygmt.config(FONT_LABEL="19p",FONT_ANNOT_PRIMARY="16p"): # font sizes for colorbar
                Fig.colorbar(position='JBC',frame=['a50f25+l"Head (m above sea level)"'],box='l+gwhite@20') # make the colorbar
                
            with pygmt.config(FONT_LABEL='14p',FONT_ANNOT_PRIMARY='12p'):
                Fig.basemap(map_scale='jTL+c33.3+w%.2fk+u10+ab+o1/0.75' % searchradius_dict['%s %s' % (season, year)])
    
            Fig.savefig('Interpolated_Head_NewShallowDataset/Maps/%s%s_NEWINTERP.png' % (season,year),transparent=True)
    
#%% Make the interpolated surface for each season/year combo, AllPeriodicMeasurements

spacing=1 # This is the grid spacing, in km. In the paper I set this to 1km.
make_map = True

print('Making interpolated surface for DWR periodic measurements dataset.')
for year in [2015,2016,2017,2018,2019,2020,2021]: # First set zero time
    for season in ["Spring","Fall"]:
        print('Doing %s %s with search radius %.2f.' % (season, year,searchradius_dict['%s %s' % (season, year)]))
        logical_tmp = np.all([seasonalwelldata_PeriodicMeasurements_TuleKaweah['MSMT_YEAR']==year,seasonalwelldata_PeriodicMeasurements_TuleKaweah['MSMT_SEASON']==season],axis=0)

        points_tmp = np.array([seasonalwelldata_PeriodicMeasurements_TuleKaweah['Longitude'][logical_tmp],seasonalwelldata_PeriodicMeasurements_TuleKaweah['Latitude'][logical_tmp],FEET_TO_M * seasonalwelldata_PeriodicMeasurements_TuleKaweah['WSE'][logical_tmp]]).T # Find the head measurements to be used for the V0 calc


        head_tmp_emptyasnan = pygmt.binstats(points_tmp,region=gridding_region,spacing='%ik+e' % spacing,statistic='a',search_radius='%.2fk' % searchradius_dict['%s %s' % (season, year)],registration='p') # Do the spatial averaging once, filling any empty nodes with nan
        pygmt.binstats(points_tmp,region=gridding_region,spacing='%ik+e' % spacing,statistic='a',search_radius='%.2fk' % searchradius_dict['%s %s' % (season, year)],registration='p',empty=-9999,outgrid='tempout.nc') # Now repeat the process, but this time fill empty nodes with -9999 and save to a file so I can use with gmtgrdmath.
        pygmt.grdfill('tempout.nc',outgrid='tmp_filled.nc',mode='n',N=-9999) # NEW SECTION: this takes the -9999 values and instead makes them the nearest non-Nan value...

        gmtgrdmath('tmp_filled.nc ../Geospatial_data/GridMasks/DummyGridMask_TuleKaweah_spacing%.2f.nc MUL = Interpolated_Head_DWRPeriodicData/%s%s_NEWINTERP.nc' % (spacing,season,year)) # Clip the result to the SATURATED study area and save the resulting interpolated grid.
    
        if make_map: # Plot a map if desired
            Fig = pygmt.Figure()
            Fig.basemap(region=plotting_region,projection='M12c',frame=["a","+t%s %s" % (year,season)])
            pygmt.makecpt(series=[-55,180])
            Fig.grdimage('Interpolated_Head_DWRPeriodicData/%s%s_NEWINTERP.nc' % (season,year),cmap=True,nan_transparent=True)
                   
            Fig.plot(data='../Geospatial_data/KaweahTuleSubbasins_Merged.txt',pen='fat,black',label='Kaweah Tule subbasin outline')
            
            # Plot the well locations
            Fig.plot(x=points_tmp[:,0],y=points_tmp[:,1],style='E0/0.5k/0.5k',color='black',label='Wells')
            
            with pygmt.config(FONT_LABEL="19p",FONT_ANNOT_PRIMARY="16p"): # font sizes for colorbar
                Fig.colorbar(position='JBC',frame=['a50f25+l"Head (m above sea level)"'],box='l+gwhite@20') # make the colorbar
                
            with pygmt.config(FONT_LABEL='14p',FONT_ANNOT_PRIMARY='12p'):
                Fig.basemap(map_scale='jTL+c33.3+w%.2fk+u10+ab+o1/0.75' % searchradius_dict['%s %s' % (season, year)])
    
            Fig.savefig('Interpolated_Head_DWRPeriodicData/Maps/%s%s_NEWINTERP.png' % (season,year),transparent=True)