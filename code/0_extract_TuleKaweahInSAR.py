#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 15:08:51 2022

This short, one-off script extracts the study area InSAR pixels.

@author: mlees
"""

# First, get the dataset down to a Season/Year value for each pixel.

import pandas as pd
import sys
sys.path.append('/home/mlees/InSAR_processing/postprocessing_scripts/')
sys.path.append('/Users/mlees/Documents/RESEARCH/InSAR_processing/postprocessing_scripts/')
#import seaborn as sns
from InSAR_postSBAS import *
import glob
save=False

#bigdata_location='/Users/mlees/Documents/RESEARCH/bigdata'
bigdata_location='/home/mlees/bigdata'

insarfiles_location = '/home/mlees/bigdata/InSAR/Processed_datasets/TRE_Altamira_Vertical_Feb2022update'

InSAR_files_todo = glob.glob('%s/DWR_CALIFORNIA_OCT2021_VERT_*.csv' % insarfiles_location)
InSAR_files_todo = [file for file in InSAR_files_todo if 'GMT' in file]
InSAR_files_todo = [file for file in InSAR_files_todo if 'SNIPPET' not in file]

deformation_data_tmp_dummy  = import_InSAR_csv('%s/DWR_CALIFORNIA_OCT2021_VERT_01_SNIPPET.csv_GMT.csv' % insarfiles_location)

tulekaweahoutline = import_kml_polygon('../../Geospatial_data/KaweahTuleSubbasins_Merged.kml')

#%% Now clip to KaweahTule and export

deformation_out = InSAR_data_all_timecompressed = pd.DataFrame(columns =deformation_data_tmp_dummy.columns)

for file in InSAR_files_todo:
    print('Doing %s' % file)
    deformation_data_tmp = import_InSAR_csv(file)
    deformation_data_tmp = extract_from_polygon(tulekaweahoutline[0],tulekaweahoutline[1],deformation_data_tmp) # Just get study area pixels
    deformation_out = pd.concat([deformation_out,deformation_data_tmp],ignore_index=True)

deformation_out.to_csv('DWR_InSAR_TuleKaweahsubbasinsONLY.csv',index=False)