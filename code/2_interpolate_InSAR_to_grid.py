#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 17:11:55 2022

This script interpolates the InSAR, with the same search radius used for the head data, and saves the resulting surface.

@author: mlees
"""

# Import modules and data
import pygmt
import pandas as pd
import sys
sys.path.append('/home/mlees/InSAR_processing/postprocessing_scripts/')
sys.path.append('/Users/mlees/Documents/RESEARCH/InSAR_processing/postprocessing_scripts/')
#import seaborn as sns
from InSAR_postSBAS import *
import numpy as np

def gmtgrdmath(arg_str):
    '''Matt's bodge wrapper since pygmt haven't made one yet.'''
    from pygmt.clib import Session
    with Session() as lib:
        lib.call_module("grdmath", arg_str)

# MANUALLY ENTER THE SEARCH RADIUS TO USE FOR EACH YEAR/SEASON. Get this from "coverage_summary_newshallowdataset"
searchradius_dict = {'Fall 2015':7.50 ,'Spring 2015':7.0, 'Fall 2016':9.5, 'Spring 2016':5.50, 'Fall 2017':5.50, 'Spring 2017':13.00, 'Fall 2018':6.5 ,'Spring 2018':6.00, 'Fall 2019':6.50, 'Spring 2019':5.5 ,'Fall 2020':8.00 ,'Spring 2020':9.00,'Fall 2021':8.00 ,'Spring 2021':11.50 }

InSAR_data_ToInterpolate = pd.read_csv('InSAR_Data_TuleKaweah_timecompressed_nojumps.csv')

tulekaweahoutline = import_kml_polygon('../Geospatial_data/KaweahTuleSubbasins_Merged.kml')

plotting_region = '%.2f/%.2f/%.2f/%.2f' % (np.min(tulekaweahoutline[0])-0.02,np.max(tulekaweahoutline[0])+0.02,np.min(tulekaweahoutline[1])-0.02,np.max(tulekaweahoutline[1])+0.08)

gridding_region = '%.2f/%.2f/%.2f/%.2f' % (np.min(tulekaweahoutline[0])-0.01,np.max(tulekaweahoutline[0]),np.min(tulekaweahoutline[1])-0.01,np.max(tulekaweahoutline[1]))


#%% Now grid the total difference between year,season and Spr 2015

spacing=1 # This is the grid spacing, in km. In the paper I set this to 1km.
make_map = True


for year in [2015,2016,2017,2018,2019,2020,2021]:
    for season in ["Spring","Fall"]:
        print('Doing', year,season,'.')
        points_tmp = np.array([InSAR_data_ToInterpolate['Longitude'].values,InSAR_data_ToInterpolate['Latitude'].values,1e-3 * (InSAR_data_ToInterpolate['%s %s' % (year,season)].values - InSAR_data_ToInterpolate['2015 Spring'].values)]).T # The 1e-3 in this part converts from mm to m
        pygmt.binstats(points_tmp,region=gridding_region,spacing='%ik+e' % spacing,statistic='a',search_radius='%.2fk' % searchradius_dict['%s %s' % (season, year)],registration='p',outgrid='tempout.nc')
        gmtgrdmath('tempout.nc ../Geospatial_data/GridMasks/DummyGridMask_TuleKaweah_spacing%.2f.nc MUL = Interpolated_Grids/%s%s.nc' % (spacing,season,year)) # Clip the result to the study area and save the resulting interpolated grid.
        if make_map:
            fig = pygmt.Figure()
            fig.basemap(region=plotting_region, projection="M10i", frame='p1')
               
            pygmt.makecpt(cmap="vik", series=np.array([-1.5, 0.2,0.1]),reverse=True)
            fig.grdimage(grid='Interpolated_Grids/%s%s.nc' % (season,year),nan_transparent=True,cmap=True)
            
            with pygmt.config(FONT_LABEL="19p",FONT_ANNOT_PRIMARY="16p"): # font sizes for colorbar
                fig.colorbar(frame='+l"Surface deformation (m)"',box='l+gwhite@20') # make the colorbar
             
            fig.text(position='TC',text='Spring 2015 to %s %s' % (season,year),font='36p,Helvetica-Bold,black',fill='white@30',pen='thickest,black',offset='1.5/-1.2')
            
            fig.plot(data='../Geospatial_data/KaweahTuleSubbasins_Merged.txt',pen='thickest,black')
            
            with pygmt.config(FONT_LABEL='22p',FONT_ANNOT_PRIMARY='22p',MAP_SCALE_HEIGHT=1.2):
                fig.basemap(map_scale='jTL+c38+w25k+u+ab+f+o1.5/3.2',box='l+gwhite@30')
        
            print('\tsaving...')
            fig.savefig('Interpolated_Grids/Maps/%s%s.png' % (season,year))
