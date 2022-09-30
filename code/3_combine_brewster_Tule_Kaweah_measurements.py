#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 11:16:01 2022

This script pulls together Brewster, KaweahExtra and TuleExtra to create a single new head dataset.

@author: mlees
"""
# Imports
import sys
sys.path.append('/home/mlees/InSAR_processing/postprocessing_scripts/')
sys.path.append('/Users/mlees/Documents/RESEARCH/InSAR_processing/postprocessing_scripts/')
from InSAR_postSBAS import *
import numpy as np

save=True

brewster_fileloc='../Data_RAW/Head/shallow_groundwater_points_BREWSTER_2022version.csv'

print('Importing Seasonal Well data from: "%s".' % brewster_fileloc)
print('\tFilesize found to be %s.' % file_size(brewster_fileloc))
#data = pd.read_csv(fileloc,parse_dates=[28])
seasonalwelldata_statewide = pd.read_csv(brewster_fileloc)
seasonalwelldata_statewide.rename(columns={'X':'Longitude', 'Y':'Latitude'},inplace=True)

print('Total number of Well Entries statewide = %i' % len(seasonalwelldata_statewide))
print('Clipping to study area...')
tulekaweahoutline = import_kml_polygon('../Geospatial_data/KaweahTuleSubbasins_Merged.kml')

seasonalwelldata_TuleKaweah = extract_from_polygon(tulekaweahoutline[0],tulekaweahoutline[1],seasonalwelldata_statewide)
seasonalwelldata_TuleKaweah = seasonalwelldata_TuleKaweah.drop_duplicates(subset=["SITE_CODE",'WSE','MSMT_YEAR','MSMT_SEASON'],inplace=False)
seasonalwelldata_TuleKaweah.astype({'WELL_NAME': 'str'})
seasonalwelldata_TuleKaweah['WELL_NAME'].fillna("",inplace=True)


extradata_Tule = pd.read_csv('ExtraDataTule_ManualEdits.csv')
extradata_Tule.replace(to_replace='BrewsterDup',value=np.nan,inplace=True) # Remove the brewster duplicates

extradata_Kaweah = pd.read_csv('ExtraDataKaweah_combined_ManualEditsPlusFourKaweahExtra.csv')
extradata_Kaweah = extradata_Kaweah[extradata_Kaweah['BrewsterDup?']==False]
extradata_Kaweah['SOURCE']='ExtraDataKaweah'
#%% Reformat the extradata_Tule to be similar to the seasonalwelldata

dict_tmp ={}
i_tmp=0
for gsawellname in extradata_Tule['Well Name (standard form)'].values:
    for year in [2015,2016,2017,2018,2019,2020,2021]:
        for season in ['Fall','Spring']:
            if ~np.isnan(float(extradata_Tule.loc[extradata_Tule['Well Name (standard form)']==gsawellname,'%s %s' % (season,year)].values[0])):
                A_tmp = extradata_Tule[extradata_Tule['Well Name (standard form)']==gsawellname]
                dict_tmp[i_tmp]={'WELL_NAME':gsawellname,'Latitude':A_tmp['Lat'],'Longitude':A_tmp['Lon'],'MSMT_YEAR':year,'MSMT_SEASON':season,'WSE':float(extradata_Tule.loc[extradata_Tule['Well Name (standard form)']==gsawellname,'%s %s' % (season,year)].values[0]),'SOURCE':'ExtraDataTule'}
                i_tmp+=1
extradata_Tule_reformatted = pd.concat({k: pd.DataFrame(v) for k, v in dict_tmp.items()}, axis=0) # Lol no idea how this line works but it does!!
extradata_Tule_reformatted = extradata_Tule_reformatted[~np.isnan(extradata_Tule_reformatted['Latitude'])]


#%% Combine all the data into a Brewster+ dataframe
extradata_Kaweah_formerger = extradata_Kaweah.rename(columns={'Site Code':'WELL_NAME', 'Lat':'Latitude','Lon':'Longitude',"WSE (ft)":"WSE"},inplace=False)
Brewsterplusdataframe =  pd.concat([seasonalwelldata_TuleKaweah,extradata_Kaweah_formerger,extradata_Tule_reformatted],axis=0,ignore_index=True)
Brewsterplusdataframe.loc[Brewsterplusdataframe['WELL_NAME']=='','WELL_NAME'] = Brewsterplusdataframe.loc[Brewsterplusdataframe['WELL_NAME']=='']['SWN']


#%% Save it

if save:
    Brewsterplusdataframe.to_csv('NewShallowHeadMeasurementsDataset.csv',index=False)
