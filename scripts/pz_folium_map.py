# -*- coding: utf-8 -*-
"""
Created on Fri Jan 29 19:41:15 2021

@author: manlaya
"""
import os
from datetime import datetime

# set wd for running script
path = os.path.dirname(__file__)
os.chdir(path)

#!pip install folium
import pandas as pd
import json
import folium

from folium import plugins

from classes.class_ftp_synthesis import ftp_synthesis as ftp_synth
from classes.class_pz_map import pz_map

path_data = r'../data/'
path_OUT = r'../manlaya.github.io/'

update = datetime.now().strftime('%d-%m-%Y')

# =============================================================================
# Read Data
# =============================================================================
pz = pd.read_excel(path_data+'rsx_pz_hdf_wgs84.xlsx') #,  encoding = 'utf-8')
df_ftp = pd.read_excel('../suivi_ftp.xlsx', index_col='indice')

#'----- Cleaning before join
# typage....
# EDIT no need if col is index
# pz['indice'] = [str(x) for x in pz['indice']]
# df_ftp['indice'] = [str(x) for x in df_ftp['indice']]

df_ftp = df_ftp.drop('nom', axis = 1)
# join
pz = pz.join(df_ftp, on='indice')

# dealing with NA
pz = pz.fillna(9999)


# =============================================================================
# #'------ creating map ----
# =============================================================================

print("-"*50,'\n',"-"*13, "Creating map synthesis", "-"*13, '\n',"-"*50)

#pz.X_L93 = pz.X_L93.astype(float)
#x_l93 = pz['long'].tolist()

# View creation, based on mean coordonnates
# Other tiles:
# OpenStreetMap, Stamen Terrain, Stamen Toner, Mapbox Bright, and Mapbox Control Room

dmap = folium.Map(location=[pz['lat'].mean(), pz['long'].mean()], zoom_start=8,
                  tiles = "OpenStreetMap")

# add different background layers
# folium.TileLayer('stamentoner').add_to(dmap)

folium.TileLayer(tiles = 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
                 attr = 'Kartendaten : © OpenStreetMap-Mitwirkende, SRTM | Kartendarstellung : © OpenTopoMap (CC-BY-SA)', name = 'Opentopomap',
                 Overlay = False, control=True).add_to(dmap)
#url = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}'

folium.TileLayer(tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                 attr = 'Esri', name = 'Esri World',
                 Overlay = False, control=True).add_to(dmap)

# add geojson with data table for search plugin
# my_style_fun = lambda x:{"fillColor": "#000000",
#                          "color": "#000000",
#                          #"weight": 0,
#                          "fillOpacity": 0
#                          }

#overlay= False #tooltip  Display a text when hovering over the object

# rsx = r'../SIG/data/rsx_pz_hdf_wgs84.geojson'
# geojson_obj = folium.GeoJson(rsx, name = 'Rsx Pz', 
#                               control = False, marker = folium.Circle() ,
#                               overlay= False, show = False, # show only if overlay
#                               style_function = my_style_fun).add_to(dmap)

# bug = style and show not working when .add_to(dmap)
# ok when dmap.add_child...

geojson_obj = folium.GeoJson(data=json.load(open(path_data+'rsx_pz_hdf_wgs84.geojson', 
                                                 encoding= 'utf-8')), 
                             name="Search layer",
                             # control = False, #conflit avec show --> force l'affichage
                             show = False)#.add_to(dmap)

dmap = dmap.add_child(geojson_obj)
   
pz['delay_push'] = ftp_synth.calc_delay(pz)

pz['color_push'] = [pz_map.legend_col(x) for x in pz['delay_push']]
#pz['color_info'] = [info_col(x,y) for x,y in [pz['bsh'], pz['sech']]]


# add features
#fg = folium.FeatureGroup(name="Réseau piézométrique HdF")

# TODO ugly, simplify
# EDIT : done !
# add by group : LIL, REI, ROU
# can now display pz from each zones individually
# https://python-visualization.github.io/folium/modules.html
# need plugin #

feature_group = folium.FeatureGroup('Réseau piézométrique HdF')
dmap.add_child(feature_group)

for grp_name, df_grp in pz.groupby('zone'):
    
    sub_group = plugins.FeatureGroupSubGroup(feature_group, grp_name)
    #name_fg = "Réseau piézométrique HdF - "+ grp_name
    #sub_group = folium.FeatureGroup(name_fg)
    
    for row in df_grp.itertuples():
        # df_grp.iloc[row]['last_error']
        #if  row.last_error == 9999:
        #    row.last_error = 'None'
        
        html_infos = f'<b>Indice :</b> {row.indice} <br>\
                        <b>Nom :</b> {row.nom} <br>\
                        <br>\
                        <b>Zone :</b> {row.zone} <br>\
                        <b>BSH :</b> {row.bsh} <br>\
                        <b>Sech :</b> {row.sech} <br>\
                        <br>\
                        <b>Time since last push :</b> {row.delay_push} (days)<br>\
                        <b>Last push ok :</b> {row.last_push}<br>\
                        <b>Last error :</b> <i>{row.last_error}</i> <br>\
                        <a href=" {row.lien_ades} "target="_blank"> Lien ADES'
        
        #iframe = folium.IFrame(html_infos)
        
        # iframe rather than html directly in folium marker popup arg allow to modify size
        # edit non need of iframe...
        my_popup = folium.Popup(html_infos,
                      min_width=50,
                      max_width=200)
        
        # custom icon
        # icons = plugins.BeautifyIcon(icon='info-sign',
        #                               text_color = info_col(row.bsh,row.sech),
        #                               background_color = row.color_push)
        
        sub_group.add_child(folium.Marker(location=[row.lat, row.long],
                                              popup= my_popup,
                                              #icon = icons))
                                                icon=folium.Icon(color=row.color_push,
                                                                icon="info-sign",
                                                                icon_color=pz_map.info_col(row.bsh,row.sech))))
    dmap = dmap.add_child(sub_group)   
    #feature_group.add_to(dmap)

del row, grp_name, df_grp

##################################" OLD #######################################"
##add features
# feature_group = folium.FeatureGroup(name="Réseau piézométrique HdF")

# for long,lat, indice, name, delay_push, link, bsh, sech, zone, push, error \
# in zip(pz['long'],pz['lat'],pz['indice'],pz['nom'], pz['delay_push'],
#         pz['lien_ades'], pz['bsh'], pz['sech'], pz['zone'], pz['last_push'], pz['last_error']):
    
#     delay_push = round(delay_push, 2)
#     if error == 9999:
#         error = 'None'
#     feature_group.add_child(folium.Marker(location=[lat,long],
#     #pop up can be written with f-strings and html !
#                                 popup=(folium.Popup(f'<b>Indice :</b> {indice} <br>{name} <br> \
#                                                     <b>Zone :</b> {zone} <br>\
#                                                     <b>BSH :</b> {bsh} \
#                                                     <br><b> Sech :</b> {sech} <br>\
#                                                     <b>Time since last push :</b> {delay_push} (days)<br>\
#                                                     <b>Last push ok :</b> {push}<br>\
#                                                     <b>Last error :</b> <i>{error}</i> <br>\
#                                                     <a href=" {link} "target="_blank"> Lien ADES')),
#                                 icon=folium.Icon(color=legend_col(delay_push),icon="info-sign", icon_color=info_col(bsh,sech))))

# dmap = dmap.add_child(feature_group)

###############################################################################

#dmap = dmap.add_child(fg)

# add contour zone
# add json files
# option 1 : load geojson_file before passing folium.GeoJson
dmap = dmap.add_child(folium.GeoJson(data=json.load(open(path_data+'bassin_ap.geojson', encoding= 'utf-8')),
                                     show=False, name="Bassin AP"))
dmap = dmap.add_child(folium.GeoJson(data=json.load(open(path_data+'bassin_sn.geojson', encoding= 'utf-8')),
                                     show=False, name="Bassin SN"))

# option 2 : just pass filename
dmap = dmap.add_child(folium.GeoJson(data=path_data+'zones_rsx_pz_hdf_wgs84_cut.geojson',
                                     show=False, name="Zone de gestion - HdF"))
                                     #style_function=lambda x: {'Color':'green' if x['zone']== 'LIL' else 'orange' if x['zone'] == 'REI' else 'red'}))

#upload file
#file = open('map.html')
#ftp.storbinary('map.html', file)

# empty legend for text box
html_title = f'<center>Suivi FTP <br>Réseau piézométrique BRGM<br>Hauts-de-France<br>\
               <br>Update : {update}'

dmap = pz_map.add_categorical_legend(dmap, html_title ,colors='',labels='')
# true legend
dmap = pz_map.add_categorical_legend(dmap, 'Time since last push (days)',
                             colors = ['#0bb3f7','#39bb1c', '#fae5d3 ','#f59a2d','#eb2612','#000000', '#afafaf'],
                           labels = ['<1j', '1-3j', '3-5j', '5-10j', '>10j', 'Non télétransmis', 'Non équipé'])
dmap = pz_map.add_categorical_legend(dmap, 'Informations (i)',
                             colors = ['#9c5c00','#1056eb' ,'#7010eb', '#ffffff'],
                           labels = ['Sech', 'BSH', 'Sech+BSH', 'Standard'])

# add title

#loc = 'Suivi FTP - Réseau piézométrique BRGM Hauts-de-France'
#title_html = '''
#             <h1 align="center" style="font-size:16px"><b>{}</b></h1>
 #            '''.format(loc) 
#dmap.get_root().html.add_child(folium.Element(title_html))

#dmap.add_child(folium.Element(title_html))

# --------------------------------------- bonus ------------------------------------- 
# Add the geological map of France
folium.WmsTileLayer('http://geoservices.brgm.fr/geologie', 
                    'GEOLOGIE', attr = 'BRGM', name = 'Géologie - BRGM', overlay= False, show = False).add_to(dmap)
# re bonus : ign maps
folium.WmsTileLayer('http://mapsref.brgm.fr/wxs/refcom-brgm/refign',
                    'FONDS_SCAN', attr = 'IGN', name = 'Scans - IGN', overlay= False, show = False).add_to(dmap)

# custom with plugins
# https://notebook.community/python-visualization/folium/examples/Plugins
plugins.LocateControl().add_to(dmap)
# search in layers
# https://python-visualization.github.io/folium/plugins.html
search = plugins.Search(layer = geojson_obj,
                        search_label  = 'indice',
                        geom_type='Point',
                        placeholder='Search for BSS',
                        #show=False,
                        collapsed=False, search_zoom = 12).add_to(dmap)

# add layers control
dmap = dmap.add_child(folium.LayerControl()) #collapsed=False for always on display

# add measure tool
# source plugin git : https://github.com/python-visualization/folium/blob/master/examples/plugin-MeasureControl.ipynb

dmap.add_child(plugins.MeasureControl()) # collapsed=False

minimap = plugins.MiniMap()
dmap.add_child(minimap)

# search with openstreetmap nomatim service
plugins.Geocoder(collapsed = True,
                 position  = 'topright',
                 # ,
                 add_marker= False).add_to(dmap)

#fmtr = "function(num) {return L.Util.formatNum(num, 3) + ' º ';};"
plugins.MousePosition(position='bottomright', separator=' | ', prefix="Mouse:").add_to(dmap)#, lat_formatter=fmtr, lng_formatter=fmtr)

print('map done ! ')

#-----------------------------------------------------------------------------------

# export
dmap.save(path_OUT+'map.html')

# The end !
print("-"*50,'\n',"-"*18, "Job finished !", "-"*18, '\n',"-"*50)
