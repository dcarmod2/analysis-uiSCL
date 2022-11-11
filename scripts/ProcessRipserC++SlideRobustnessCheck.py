#!/usr/bin/env python
# coding: utf-8

# ### Given sparse matrices representing the time-expanded rips complexes for both car and public transit travel, this file finds candidate regions in a city where new transit hubs should be introduced.


import re
import numpy as np
import matplotlib.pyplot as plt
from persim import plot_diagrams,bottleneck
import datetime
import os
import geopandas as gpd
import pandas as pd
import shapely
import json
import networkx as nx
import random
import requests
import polyline
import pickle
from tqdm.notebook import tqdm,trange
import gc
import itertools
import subprocess

from shapely.geometry import MultiPoint, Point, Polygon


start = datetime.datetime(2020,2,14,6,5)
window = datetime.timedelta(minutes=5)

six_am = 1581656400000


def graph_to_geojson(G,origins,comp_colors=None):
    geoJ = {'type':'FeatureCollection'}
    features = []
    heightScale = 500
    if not comp_colors:
        clr_choices = [str(i) for i in range(0,10)] + ['A','B','C','D','E','F']
        comp_colors = [(comp,'#'+''.join([random.choice(clr_choices) for _ in range(0,6)])) for comp in nx.connected_components(G)]
    
    
    for node in G.nodes:
        feat = {'type':'Feature','properties':{}}
        
        for comp,clr in comp_colors:
            if node in comp:
                feat['properties']['color'] = clr
                break
                
        node = int(node)
        layer = node//len(origins)
        loc = node % len(origins)
        latlon = origins[loc]
        height = layer * heightScale
        lon,lat = latlon
        lon,lat = float(lon),float(lat)
        feat['properties']['lat'] = lat
        feat['properties']['lon'] = lon
        feat['properties']['height'] = height
        
                
        feat['geometry'] = {'type':'Point','coordinates':[lon,lat]}
        features.append(feat)
        
    for edge in G.edges:
        feat = {'type':'Feature','properties':{}}
        ori,dest = edge
        feat['properties']['weight'] = G.edges[edge]['weight']
        
        for comp,clr in comp_colors:
            if ori in comp:
                feat['properties']['color'] = clr
                break
                
        ori = int(ori)
        dest = int(dest)
        layerori = ori//len(origins)
        layerdest = dest//len(origins)
        locori = ori % len(origins)
        locdest = dest % len(origins)
        oriheight = layerori*heightScale
        destheight = layerdest*heightScale
        
        latlonori = origins[locori]
        orilon,orilat = latlonori
        orilon,orilat = float(orilon),float(orilat)
        feat['properties']['orilat'] = orilat
        feat['properties']['orilon'] = orilon
        feat['properties']['oriheight'] = oriheight
        
        latlondest = origins[locdest]
        destlon,destlat = latlondest
        destlon,destlat = float(destlon),float(destlat)
        feat['properties']['destlat'] = destlat
        feat['properties']['destlon'] = destlon
        feat['properties']['destheight'] = destheight
        
        feat['geometry'] = {'type':'LineString','coordinates':[[orilon,orilat,oriheight],[destlon,destlat,destheight]]}
        features.append(feat)
    geoJ['features'] = features
    return json.dumps(geoJ)



def inter_within(inter1,inter2):
    return inter2[0] <= inter1[0] <= inter2[1]

clist = ['#1f77b4',
'#ff7f0e',
'#2ca02c',
'#d62728',
'#9467bd',
'#8c564b',
'#e377c2',
'#7f7f7f',
'#bcbd22',
'#17becf'
]

def get_loc_and_time(ind,start_time,window,origins,point_origins):
    layer = ind//len(origins)
    loc = ind % len(origins)
    
    t = start_time + window*layer
    locs = [x for x in point_origins[loc].coords][0]
    return locs,t.strftime("%H:%M")
        
    
def get_loc_and_time_ints(ind,start_time,window,origins,point_origins):
    layer = ind//len(origins)
    loc = ind % len(origins)
    height_scale = 10
    t = start_time + window*layer
    locs = [x for x in point_origins[loc].coords][0]
    return locs,(t.minute + 60* t.hour)*height_scale


def get_hull(gen,origins,point_origins):
    
    edges = [[x%len(origins),y%len(origins)] for x,y in gen if x%len(origins) != y%len(origins)]
    map_dicts = {}
    #print(edges)
    for edge in edges:
        src,tar = edge
        try:
            map_dicts[src] += [src,tar]
        except KeyError:
            map_dicts[src] = [src,tar]
        try:
            map_dicts[tar] += [src,tar]
        except KeyError:
            map_dicts[tar] = [src,tar]
    #print(map_dicts)
    
    cur_node = edges[0][0]
    points = [cur_node]
    while len(map_dicts) > 0:
        next_nodes = map_dicts.pop(cur_node)
        valid = [x for x in next_nodes if x != cur_node and x not in points]
        
        if not valid:
            break
        next_node = valid[0]
        points.append(next_node)
        cur_node = next_node
        
    #print(points)
    return Polygon([point_origins[pt] for pt in points] + [point_origins[points[0]]])

def cycle_to_geojson(info_list):
    to_ret = {'type': 'FeatureCollection', 'features':[]}
    for start,end in info_list:
        (startx,starty),starth = start
        (endx,endy),endh = end
        coords = [[startx,starty,starth],[endx,endy,endh]]
        feat = {'type':'Feature','properties': {'startLon': startx,
                                               'startLat': starty,
                                               'startHeight': starth,
                                               'endLon': endx,
                                               'endLat': endy,
                                               'endHeight': endh,
                                               
                                               'persistence': 0 },
               'geometry': {'type': 'LineString',
                           'coordinates': coords}}
        to_ret['features'].append(feat)
    
    return to_ret


def get_transit_plan(data):
    date='2020-02-14'
    fromPlace,fromTime,toPlace,toTime = data
    r = requests.get('http://localhost:8080/otp/routers/default/plan',params={'fromPlace':fromPlace,
                                                                          'toPlace':toPlace,
                                                                         'date':date,
                                                                         'time':fromTime,
                                                                           'mode':'WALK,TRANSIT' })
    
    js_resp = r.json()
    fastest_trip = min([(itin['endTime'],itin) 
                        for itin in js_resp['plan']['itineraries']],key = lambda x:x[0])
    
    return fastest_trip[1]

def get_transit_plan_car(data):
    date='2020-02-14'
    fromPlace,fromTime,toPlace,toTime = data
    r = requests.get('http://localhost:8080/otp/routers/default/plan',params={'fromPlace':fromPlace,
                                                                          'toPlace':toPlace,
                                                                         'date':date,
                                                                         'time':fromTime,
                                                                              'maxPreTransitTime':3000,
                                                                             'mode':'WALK,CAR'})
    
    js_resp = r.json()
    
    fastest_trip = min([(itin['endTime'],itin) 
                        for itin in js_resp['plan']['itineraries']],key = lambda x:x[0])
    
    return fastest_trip[1]

def get_transit_plan_bike(data):
    date='2020-02-14'
    fromPlace,fromTime,toPlace,toTime = data
    r = requests.get('http://localhost:8080/otp/routers/default/plan',params={'fromPlace':fromPlace,
                                                                          'toPlace':toPlace,
                                                                         'date':date,
                                                                         'time':fromTime,
                                                                             'mode':'WALK,BICYCLE'})
    
    js_resp = r.json()
    fastest_trip = min([(itin['endTime'],itin) 
                        for itin in js_resp['plan']['itineraries']],key = lambda x:x[0])
    
    return fastest_trip[1]

def legs_to_geojson(pathFeats):
    allFeats = []
    for pathFeat in pathFeats:
        features = []
        for leg in pathFeat['legs']:
            feat = {}
            feat['type'] = 'Feature'
            feat['properties']={key:val for key,val in leg.items()}
            feat['properties']['globalStartTime'] = pathFeat['startTime']
            feat['properties']['globalArrivalTime'] = pathFeat['endTime']
            feat['geometry'] = {'type':'LineString', 
                                'coordinates':[[x[1],x[0]] for x in polyline.decode(leg['legGeometry']['points'])]}
            features.append(feat)

        collected = {"type":"FeatureCollection","features":features}
        allFeats.append(collected)
    return json.dumps(allFeats)

def legs_to_geojson_py(pathFeats):
    allFeats = []
    for pathFeat in pathFeats:
        features = []
        for leg in pathFeat['legs']:
            feat = {}
            feat['type'] = 'Feature'
            feat['properties']={key:val for key,val in leg.items()}
            feat['properties']['globalStartTime'] = pathFeat['startTime']
            feat['properties']['globalArrivalTime'] = pathFeat['endTime']
            feat['geometry'] = {'type':'LineString', 
                                'coordinates':[[x[1],x[0]] for x in polyline.decode(leg['legGeometry']['points'])]}
            features.append(feat)

        collected = {"type":"FeatureCollection","features":features}
        allFeats.append(collected)
    return allFeats

def legs_to_geojson_edges(pathFeats):
    features = []
    for pathFeat in pathFeats:
        
        for leg in pathFeat['legs']:
            feat = {}
            feat['type'] = 'Feature'
            feat['properties']={key:val for key,val in leg.items()}
            feat['properties']['globalStartTime'] = pathFeat['startTime']
            feat['properties']['globalArrivalTime'] = pathFeat['endTime']
            feat['geometry'] = {'type':'LineString', 
                                'coordinates':[[x[1],x[0]] for x in polyline.decode(leg['legGeometry']['points'])]}
            features.append(feat)

    collected = {"type":"FeatureCollection","features":features}
        
    return collected


def legs_to_geojson_with_startTime(pathFeats,startTimes):
    allFeats = []
    for pathFeat,startTime in zip(pathFeats,startTimes):
        features = []
        for leg in pathFeat['legs']:
            feat = {}
            feat['type'] = 'Feature'
            feat['properties']={key:val for key,val in leg.items()}
            feat['properties']['globalStartTime'] = startTime
            feat['properties']['globalArrivalTime'] = pathFeat['endTime']
            feat['geometry'] = {'type':'LineString', 
                                'coordinates':[[x[1],x[0]] for x in polyline.decode(leg['legGeometry']['points'])]}
            features.append(feat)

        collected = {"type":"FeatureCollection","features":features}
        allFeats.append(collected)
    return json.dumps(allFeats)

def int_to_time(t):
    heightScale = 10
    time = t//heightScale
    dt = datetime.datetime(2020,2,14,time//60,time%60)
    
    return dt.strftime('%H:%M') 

def extract_pts(gens,ind,origins,point_origins):
    start_lat = point_origins[gens[ind][0][1][0]%len(origins)].y
    start_lon = point_origins[gens[ind][0][1][0]%len(origins)].x
    end_lat = point_origins[gens[ind][0][1][1]%len(origins)].y
    end_lon = point_origins[gens[ind][0][1][1]%len(origins)].x
    
    return f'{start_lat},{start_lon}',f'{end_lat},{end_lon}'



# #### The commented out code here computes homology generators using the representative-cycles branch of ripser (which needs to be installed from source after downloading from github here: https://github.com/Ripser/ripser/tree/representative-cycles 
# 
# #### Note that the first argument to subprocess.run should be the location of your built executable for ripser


# for i in range(17,18):
slide_num = 36
with open(f"output_slide_hole_{slide_num}.txt","w+") as f:
    p = subprocess.run(["../../ripser/ripser-representatives", "--format", "sparse" ,"--dim", "1", "--threshold", "100", f'sparsemat_slide_hole_trans_{slide_num}.txt'], stdout=f)
        


STOCKHOLM_PROJ='EPSG:5850'
UNPROJECT='EPSG:4326'


transit_isochrone_dir = 'RobustIsochrones/'
car_isochrone_dir = 'SlideIsochronesCar/'
subdir = f'Slide_{slide_num}/'
graph_file = f'sparsemat_slide_hole_trans_{slide_num}.txt'
sample_isochrone = gpd.read_file(transit_isochrone_dir + f'stock_nowater_pairs_400_{slide_num}-25200-32400.json')
origins = sample_isochrone[sample_isochrone['cutoff'] == 60].loc[:,['fromLon','fromLat']].values
point_origins = [shapely.geometry.Point(x,y) for x,y in sample_isochrone[sample_isochrone['cutoff'] == 60].loc[:,['fromLon','fromLat']].values]
transit_output_filename = f"output_slide_hole_{slide_num}.txt"
with open(transit_output_filename,'r') as f:
    lines = [line.strip().split(':') 
        for line in f.readlines()
            if line.startswith(' [')]
    
with open(transit_output_filename,'r') as f:
    lines_plus = [line.strip().split(':') 
                for line in f.readlines()
                if line.startswith('+')]
    
intervals0 = []
gens0 = []
intervals1 = []
gens1 = []
for linepair in tqdm(lines):
    bd, gen = linepair
    birth,death = re.findall(r'\[(\d+),(\d*)',bd)[0]
    try:
        birth,death = int(birth),int(death)
    except ValueError:
        # infinite death case
        birth = int(birth)
        death = np.inf

    gen_plus_birth = [x.strip('{} ').split(' ') for x in gen.split(', ')]
    if len(gen_plus_birth[0]) > 1:
        # dim 1
        fixed = [[int(y.strip('[]')) for y in x[0].split(',')] for x in gen_plus_birth]
        gens1.append(fixed)
        intervals1.append([birth,death])
    else:
        # dim 0
        fixed = [int(x[0][1:-1]) for x in gen_plus_birth]
        gens0.append(fixed)
        intervals0.append([birth,death])

    #print(gen_plus_birth)

with open(f'CarCohomology/car_coho_slide_{slide_num}.p','rb') as f:
    carRips = pickle.load(f)
    
coc_sets = [[set(x[:-1]) for x in y] for y in carRips['cocycles'][1]]

maximpact = np.percentile([np.log(intervals1[i][1] + 1)-np.log(intervals1[i][0] + 1) 
                            for i,_ in enumerate(intervals1) if intervals1[i][1] < 60],99.9)
maxpers = np.percentile([intervals1[i][1] - intervals1[i][0]  for i,_ in enumerate(intervals1) if intervals1[i][1] < 60],99.9)

allpers = [i for i,_ in enumerate(intervals1) if intervals1[i][1]  - intervals1[i][0] >= maxpers and intervals1[i][1] < 60]
allpers_with_pers = [(i,intervals1[i][1]  - intervals1[i][0]) for i,_ in enumerate(intervals1) if intervals1[i][1]  - intervals1[i][0] >= maxpers and intervals1[i][1] < 60]
allimpact_with_endp = [(i,np.log(intervals1[i][1]+1)  - np.log(intervals1[i][0]+1),intervals1[i][0],intervals1[i][1]) for i,_ in enumerate(intervals1) if np.log(intervals1[i][1]+1)  - np.log(intervals1[i][0]+1) >= maximpact and intervals1[i][1] < 60]

sorted_allpers_with_pers = sorted(allpers_with_pers,key=lambda x: x[1])
sorted_allimpact = sorted(allimpact_with_endp,key=lambda x:x[1])
mode_imb_allpers = []
modified_gens = []
"""for tmpind,(ind,pers) in enumerate(sorted_allpers_with_pers[-10:]):
    testgen = [set(x) for x in gens1[ind]]
    relevant_coc = [(coc,carRips['dgms'][1][i][1]) for i,coc in enumerate(coc_sets) if inter_within(intervals1[ind],
                                                                        carRips['dgms'][1][i]) ]
    is_zero = True
    cur_birth = intervals1[ind][0]
    print(f"Gen: {ind}, Starting birth: {cur_birth}")
    for check,death in relevant_coc:
        cursum = 0
        for edge in check:
            for gen_edge in testgen:
                if gen_edge.difference(edge):
                    cursum += 1
        if cursum % 2 != 0:
            if cur_birth < death:
                cur_birth = death
    print(f"Gen: {ind}, Ending birth: {cur_birth}")
    if cur_birth == intervals1[ind][0]:
        mode_imb_allpers.append((ind,death-cur_birth))
    else:
        modified_gens.append((ind,death-cur_birth))"""

mode_imb_allimpact = []
modified_gens_impact = []
for tmpind,(ind,imp,birth,orig_death) in enumerate(sorted_allimpact[-50:-30]):
    testgen = [set(x) for x in gens1[ind]]
    relevant_coc = [(coc,carRips['dgms'][1][i][1]) for i,coc in enumerate(coc_sets) if inter_within(intervals1[ind],
                                                                        carRips['dgms'][1][i]) ]
    is_zero = True
    cur_birth = birth
    print(f"Gen: {ind}, Starting birth: {cur_birth}")
    for check,death in relevant_coc:
        cursum = 0
        for edge in check:
            for gen_edge in testgen:
                if gen_edge.difference(edge):
                    cursum += 1
        if cursum % 2 != 0:
            if cur_birth < death:
                cur_birth = death
    print(f"Gen: {ind}, Ending birth: {cur_birth}")
    if cur_birth == intervals1[ind][0]:
        mode_imb_allimpact.append((ind,imp,birth,orig_death))
    else:
        modified_gens_impact.append((ind,np.log(death+1)-np.log(cur_birth+1),cur_birth,orig_death))
    
for j,gentup in enumerate(mode_imb_allpers):
    max_gen = gentup[0]
    max_feat_pers_int = sorted([[get_loc_and_time_ints(x,start,window,origins,point_origins),get_loc_and_time_ints(y,start,window,origins,point_origins)] for x,y in gens1[max_gen]],key=lambda x: x[0][1])
    with open(f"KeplerViz/CheckFeatSlide_{slide_num}_gen_{j}.json","w+") as f:
        f.write(json.dumps(cycle_to_geojson(max_feat_pers_int)))
        

#
        
for j,gentup in enumerate(mode_imb_allpers):
    max_gen = gentup[0]
    gen = gens1[max_gen]
    feat = shapely.geometry.mapping(get_hull(gen,origins,point_origins))
    geoj_dict = {'type':'FeatureCollection','features':[{'type':'Feature',
                                                            'geometry':feat}]}
                                    
    with open(f"KeplerViz/CheckPolySlide_{slide_num}_gen_{j}.json","w+") as f:
        f.write(json.dumps(geoj_dict))
                                    
for j,gentup in enumerate(modified_gens):
    max_gen = gentup[0]
    max_feat_pers_int = sorted([[get_loc_and_time_ints(x,start,window,origins,point_origins),get_loc_and_time_ints(y,start,window,origins,point_origins)] for x,y in gens1[max_gen]],key=lambda x: x[0][1])
    with open(f"KeplerViz/CheckModFeatSlide_{slide_num}_gen_{j}.json","w+") as f:
        f.write(json.dumps(cycle_to_geojson(max_feat_pers_int)))
        
for j,gentup in enumerate(modified_gens):
    max_gen = gentup[0]
    gen = gens1[max_gen]
    feat = shapely.geometry.mapping(get_hull(gen,origins,point_origins))
    geoj_dict = {'type':'FeatureCollection','features':[{'type':'Feature',
                                                            'geometry':feat}]}
                                    
    with open(f"KeplerViz/CheckModPolySlide_{slide_num}_gen_{j}.json","w+") as f:
        f.write(json.dumps(geoj_dict))
                                    
for j,gentup in enumerate(mode_imb_allimpact):
    max_gen = gentup[0]
    max_feat_pers_int = sorted([[get_loc_and_time_ints(x,start,window,origins,point_origins),get_loc_and_time_ints(y,start,window,origins,point_origins)] for x,y in gens1[max_gen]],key=lambda x: x[0][1])
    with open(f"KeplerViz/CheckImpactFeatSlide_{slide_num}_gen_{j}.json","w+") as f:
        f.write(json.dumps(cycle_to_geojson(max_feat_pers_int)))
                                    
    
        
for j,gentup in enumerate(mode_imb_allimpact):
    max_gen = gentup[0]
    gen = gens1[max_gen]
    feat = shapely.geometry.mapping(get_hull(gen,origins,point_origins))
    geoj_dict = {'type':'FeatureCollection','features':[{'type':'Feature',
                                                            'geometry':feat}]}
    with open(f"KeplerViz/CheckImpactPolySlide_{slide_num}_gen_{j}.json","w+") as f:
        f.write(json.dumps(geoj_dict))
                                    
for j,gentup in enumerate(modified_gens_impact):
    max_gen = gentup[0]
    max_feat_pers_int = sorted([[get_loc_and_time_ints(x,start,window,origins,point_origins),get_loc_and_time_ints(y,start,window,origins,point_origins)] for x,y in gens1[max_gen]],key=lambda x: x[0][1])
    with open(f"KeplerViz/CheckModImpactFeatSlide_{slide_num}_gen_{j}.json","w+") as f:
        f.write(json.dumps(cycle_to_geojson(max_feat_pers_int)))
        
for j,gentup in enumerate(modified_gens_impact):
    max_gen = gentup[0]
    gen = gens1[max_gen]
    feat = shapely.geometry.mapping(get_hull(gen,origins,point_origins))
    geoj_dict = {'type':'FeatureCollection','features':[{'type':'Feature',
                                                            'geometry':feat}]}
                                    
    with open(f"KeplerViz/CheckModImpactPolySlide_{slide_num}_gen_{j}.json","w+") as f:
        f.write(json.dumps(geoj_dict))
    
gc.collect()