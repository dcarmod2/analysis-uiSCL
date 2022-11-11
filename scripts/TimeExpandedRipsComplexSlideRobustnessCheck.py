#!/usr/bin/env python
# coding: utf-8

# ### This file produces the time expanded rips complexes for the tranist or car networks
# - it is currently set up to do the computation for the car network
# - the last cell computes cohomology of the car network, this cell should not be run when looking at transit


from ripser import ripser
from persim import plot_diagrams,bottleneck
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
import seaborn as sns
import networkx as nx
import matplotlib.pyplot as plt
import itertools
import gudhi as gd
import sympy
from tqdm.notebook import tqdm,trange
import pickle
import os
import gc
import subprocess
from natsort import natsorted
from scipy.sparse import coo_matrix

### Make time expanded distance matrix

def make_coo_matrix_nodelay(origins,point_origins,dfs,timeRange=15,maxTime=60,savefile=None):
    
    num_layers = len(dfs)
    num_origins = len(origins)
    # We construct a sparse num_origins * num_origins * num_layers
    # matrix which will contain the distances to form
    # a Rips complex. Non-existent entries in sparse
    # matrices are interpreted as infinity by ripser.
    
    # First we need to add the distances which correspond to waiting at a stop 
    
    data = [timeRange*j  for i in origins
                 for k in range(0,num_layers+maxTime//timeRange)
                   for j in range(1,maxTime//timeRange  - (k-num_layers))
                   ]
    
    rows = [i + num_origins*k  for i in origins
                 for k in range(0,num_layers+maxTime//timeRange)
                   for _ in range(1,maxTime//timeRange  - (k-num_layers))
                   ]
    
    cols = [i + num_origins*j + k*num_origins for i in origins
                       for k in range(0,num_layers+maxTime//timeRange)
                        for j in range(1,maxTime//timeRange  - (k-num_layers))]
    
    
    
    matrix_size = (maxTime//timeRange + num_layers) * num_origins
    
    print("Forming {} by {} sparse distance matrix".format(matrix_size,matrix_size))
    for layer_ind,df in enumerate(dfs):
        # dfs are ordered by start time
        
        # figure out connections to each layer by 
        # making a connection from layer i to layer
        # i + ceil(travel_time/timeRange)
        for j,origin in tqdm(enumerate(origins)):
            origin_loc = num_origins * layer_ind + j
            dist_dict = {}
            seen = set([j])
            
            for cutoff in range(timeRange,maxTime+1,timeRange):
                geom = df.loc[(j,cutoff),'geometry']
                in_pts = [i for i,ori in enumerate(point_origins) if ori.within(geom)]
                for pt in in_pts:
                    if pt not in seen:
                        dist_dict[pt] = cutoff
                        seen.add(pt)
            
            inds_data = [(int(num_origins*(np.ceil(val/timeRange) + k) + num_origins * layer_ind + key), val + k*timeRange) for key,val in dist_dict.items()
                        for k in range(0,int(np.ceil(maxTime/timeRange) - np.ceil(val/timeRange)) + num_layers - layer_ind)]
            data += [x[1] for x in inds_data]
            cols += [x[0] for x in inds_data]
            rows += [origin_loc for _ in inds_data]
        
     
    out_mat = coo_matrix((data,(rows,cols)),shape=(matrix_size,matrix_size))
    symmetrized = out_mat + out_mat.transpose()
    if savefile:
        with open(savefile,'w+') as f:
            for i,dat in enumerate(data):
                f.write("{} {} {}".format(rows[i],cols[i],dat))
                if i < len(data)-1:
                    f.write("\n")
    return out_mat


# #### For each subregion in stockholm, use isochrone data to make a sparse distance matrix representing travel times in the transit or car network. 
# - depending on whether is looking at transit or car, lines should be commented/uncommented and directory names changed accordingly

# for file in natsorted([x for x in os.listdir('RobustIsochrones') if not x.startswith('.DS')]):


slide_num = 38
file = f"stock_nowater_pairs_400_{slide_num}-25200-32400.json"
trans_gdfs = [gpd.read_file("RobustIsochrones/" + file)]
origins = sorted(set(trans_gdfs[0].loc[:,'origin']))

trans_dfs = [trans_gdfs[0].set_index(['origin','cutoff']) for _ in range(20)]
#car_dfs = [x.set_index(['origin','cutoff']) for x in car_gdfs]
#bike_dfs = [x.set_index(['origin','cutoff']) for x in bike_gdfs]
for df in tqdm(trans_dfs):
    df['geometry'] = df['geometry'].simplify(tolerance=0.005)

point_origins = [shapely.geometry.Point(x,y) for x,y in trans_gdfs[0][trans_gdfs[0]['cutoff'] == 60].loc[:,['fromLon','fromLat']].values]
sparse_nodelay = make_coo_matrix_nodelay(origins,point_origins,trans_dfs,5,60,f"sparsemat_slide_hole_trans_{slide_num}.txt")
print(len(origins))

gc.collect()
