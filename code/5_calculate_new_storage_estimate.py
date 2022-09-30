#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  1 09:32:20 2022

This script calculates and saves:
    1) the new storage estimate due to changes in saturation (with new head dataset))
    2) the new storage estimate due to changes in porosity
    3) the total new storage estimate


@author: mlees
"""

# Import modules, define functions, import miscellaneous data files, define plotting and gridding regions.
import sys
sys.path.append('/home/mlees/InSAR_processing/postprocessing_scripts/')
sys.path.append('/Users/mlees/Documents/RESEARCH/InSAR_processing/postprocessing_scripts/')
from InSAR_postSBAS import *
import pygmt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime as dt

save=True

tulekaweahoutline = import_kml_polygon('../Geospatial_data/KaweahTuleSubbasins_Merged.kml')

specific_yield=9 # in percent, taken from Williamson and others 1989

plotting_region = '%.2f/%.2f/%.2f/%.2f' % (np.min(tulekaweahoutline[0])-0.02,np.max(tulekaweahoutline[0])+0.02,np.min(tulekaweahoutline[1])-0.02,np.max(tulekaweahoutline[1])+0.08)
gridding_region = '%.2f/%.2f/%.2f/%.2f' % (np.min(tulekaweahoutline[0])-0.01,np.max(tulekaweahoutline[0]),np.min(tulekaweahoutline[1])-0.01,np.max(tulekaweahoutline[1]))


#%% Calculate the estimate due to changes in saturation
print()

# First, get V0 (which is my zero value, in Spr 2015)
print('Calculating V0 for drainage of pores.')
#V0_pores = pygmt.grdvolume('../HeadInterpolation/Interpolated_Head_NewShallowDataset/Spring2015.nc',output_type='numpy',unit='k',Z='%.7f' % (1e-3 * 0.01*specific_yield),f='g')[0][2] # Calc the total volume in km3
V0_pores = pygmt.grdvolume('../HeadInterpolation/Interpolated_Head_NewShallowDataset/Spring2015_NEWINTERP.nc',output_type='numpy',unit='k',Z='%.7f' % (1e-3 * 0.01*specific_yield),f='g')[0][2] # Calc the total volume in km3

print('\tDone. V0 = %.2f km3.' % V0_pores)

# Now, form the V timeseries for the BrewsterPlus.
print('Calculating V timeseries...')
V_sat_timeseries_TMPDICT={}
for year in [2015,2016,2017,2018,2019,2020,2021]: # First set zero time
    for season in ["Spring","Fall"]:
#        V_tmp = pygmt.grdvolume('../HeadInterpolation/Interpolated_Head_NewShallowDataset/%s%s.nc' % (season,year),output_type='numpy',unit='k',Z='%.7f' % (1e-3 * 0.01*specific_yield),f='g')[0][2] # calc total volume in km3
        V_tmp = pygmt.grdvolume('../HeadInterpolation/Interpolated_Head_NewShallowDataset/%s%s_NEWINTERP.nc' % (season,year),output_type='numpy',unit='k',Z='%.7f' % (1e-3 * 0.01*specific_yield),f='g')[0][2] # calc total volume in km3

        V_sat_timeseries_TMPDICT['%s %s' % (season,year)] = V_tmp - V0_pores # Add it to the timeseries by differencing from V0
        print('\t%s %s V = %.2f km3.' % (season,year,V_sat_timeseries_TMPDICT['%s %s' % (season,year)]))
 
V_sat_timeseries = pd.Series(V_sat_timeseries_TMPDICT,name='V (km3)')
    
#%% Calculate the estimate due to changes in porosity
print('Calculating V for porosity changes.')

InSAR_timeseries_TMPDICT={}

columns=['Spring 2015-Fall 2015','Spring 2015-Spring 2016','Spring 2015-Fall 2016','Spring 2015-Spring 2017','Spring 2015-Fall 2017','Spring 2015-Spring 2018','Spring 2015-Fall 2018','Spring 2015-Spring 2019','Spring 2015-Fall 2019','Spring 2015-Spring 2020','Spring 2015-Fall 2020','Spring 2015-Spring 2021','Spring 2015-Fall 2021']

# Set up the dataframe
for year in [2015,2016,2017,2018,2019,2020,2021]:
    for season in ['Spring','Fall']:
        dVtmp1 = 1e-9* pygmt.grdvolume('../InSAR_analysis/Interpolated_Grids/%s%s.nc' % (season, year),output_type='numpy',unit='e',f='g')[0][2] # volume change in km3        
        InSAR_timeseries_TMPDICT['%s %s' % (season,year)] = dVtmp1
        print('\t%s %s V is %.2f km3.' % (season,year, dVtmp1))

    
V_por_timeseries = pd.Series(InSAR_timeseries_TMPDICT,name='V (km3)')

#%% Sum the two to get the total storage estimate, and save the whole lot

Storage_Series_Out = pd.DataFrame({'Saturation Storage (km3)':V_sat_timeseries,'Porosity Storage (km3)':V_por_timeseries})
Storage_Series_Out['Total Storage (km3)'] = Storage_Series_Out['Saturation Storage (km3)'] + Storage_Series_Out['Porosity Storage (km3)']
if save:
#    Storage_Series_Out.to_csv('NewStorageEstimates.csv',index=False)

    Storage_Series_Out.to_csv('NewStorageEstimates_NEWINTERP.csv',index=False)

def import_kml_polygon(filename):
    '''import a single .kml polygon created in Google Earth. Should work in simple cases.......'''
    
    kml_file = filename # Name of the kml file
    
    # Load the file as a string, skipping the first line because for some reason fastkml cannot deal with that...
    with open(kml_file, 'rt', encoding="utf-8") as myfile:
        doc=myfile.readlines()[1:]
        myfile.close()
    doc = ''.join(doc) # gets it as a string
    
    # Using the very opaque fastkml module to parse out the features. I wonder if the length of features is 2 if it's a 2-segment line..?
    k = kml.KML()
    k.from_string(doc)
    features = list(k.features())
    
    # Extract the first feature and a LineString object corresponding to it!
    f1 = list(features[0].features())
    t = f1[0].geometry
    A = np.array(t.exterior.coords)
    Polylon = A[:,0]
    Polylat = A[:,1]
    
    return Polylon, Polylat
