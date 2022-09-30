#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 16:05:03 2022

This script gets the InSAR data into season/year combos.

@author: mlees
"""

import matplotlib.pyplot as plt
import sys
sys.path.append('/home/mlees/InSAR_processing/postprocessing_scripts/')
sys.path.append('/Users/mlees/Documents/RESEARCH/InSAR_processing/postprocessing_scripts/')
from InSAR_postSBAS import *
import glob
from matplotlib.dates import date2num
from datetime import datetime as dt
import numpy as np

# Import Tule/Kaweah subbasins InSAR.
InSAR_data_kaweahtule =import_InSAR_csv('../Data_RAW/InSAR/DWR_InSAR_TuleKaweahsubbasinsONLY.csv')

#%% Now convert the data into Spring/Fall for each year.
columns_tmp = ['Longitude','Latitude','2015 Spring','2015 Fall','2016 Spring','2016 Fall','2017 Spring','2017 Fall','2018 Spring','2018 Fall','2019 Spring','2019 Fall','2020 Spring','2020 Fall','2021 Spring','2021 Fall'] # These are the output columns you desire
InSAR_data_all_timecompressed = pd.DataFrame(columns =columns_tmp)

headers_InSAR_byyearseason = {}

for year in np.array([2015,2016,2017,2018,2019,2020,2021]).astype(str):
    headers_InSAR_byyearseason['Spring %s' % year] = [col for col in InSAR_data_kaweahtule.columns if (col[:6]==year+'01') or (col[:6]==year+'02') or (col[:6]==year+'03') or (col[:6]==year+'04') or (col[:6]==year+'05')] # This defines Spring as Jan-May inclusive 
    headers_InSAR_byyearseason['Fall %s' % year] = [col for col in InSAR_data_kaweahtule.columns if (col[:6]==year+'09') or (col[:6]==year+'10') or (col[:6]==year+'11')] # This defines Fall as Sep-Nov inclusive

idx_to_remove = np.all([~np.isnan(InSAR_data_kaweahtule['20190919']),np.isnan(InSAR_data_kaweahtule['20190925']), ~np.isnan(InSAR_data_kaweahtule['20201007'])],axis=0) # 
print('\tRemoving %i entries out of %i because they seem to reset to zero in 2020.' % (np.sum(idx_to_remove),len(InSAR_data_kaweahtule)))
InSAR_data_kaweahtule = InSAR_data_kaweahtule[~idx_to_remove]

# For each year, take the mean of the deformation across Spring and Fall and assign that to the new dataframe.
for year in [2015,2016,2017,2018,2019,2020,2021]:
    InSAR_data_all_timecompressed['%s Spring' % year] =  InSAR_data_kaweahtule.loc[np.ones(len(InSAR_data_kaweahtule),dtype=bool),headers_InSAR_byyearseason['Spring %s' % year]].mean(axis=1,skipna=True)
    InSAR_data_all_timecompressed.loc[np.sum(~np.isnan(InSAR_data_kaweahtule[headers_InSAR_byyearseason['Spring %s' % year]].values),axis=1) <=5,'%s Spring' % year] = np.nan # Set to nan those pixels where Spring has a mean of fewer than 5 measurements 
    InSAR_data_all_timecompressed['%s Fall' % year] =  InSAR_data_kaweahtule.loc[np.ones(len(InSAR_data_kaweahtule),dtype=bool),headers_InSAR_byyearseason['Fall %s' % year]].mean(axis=1,skipna=True)
    InSAR_data_all_timecompressed.loc[np.sum(~np.isnan(InSAR_data_kaweahtule[headers_InSAR_byyearseason['Fall %s' % year]].values),axis=1) <=5,'%s Fall' % year] = np.nan # 
 # Set to nan those pixels where Fall has a mean of fewer than 5 measurements 

InSAR_data_all_timecompressed.loc[:,['Longitude','Latitude']] = InSAR_data_kaweahtule.loc[:,['Longitude','Latitude']]


InSAR_data_all_timecompressed.to_csv('InSAR_Data_TuleKaweah_timecompressed_nojumps.csv',index=False)
