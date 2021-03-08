# -*- coding: utf-8 -*-
"""
Created on Fri Jan 29 19:41:15 2021

@author: manlaya
"""

import os

# set wd for running script
path = os.path.dirname(__file__)
os.chdir(path)

import ftplib
import pandas as pd

#if subfolder then subfold_name.script_name"
from classes.class_ftp_synthesis import ftp_synthesis as ftp_synth

path_data = r'../data/'
path_OUT = r'../'

#------- set ftp connection
con_infos = open(r'../.con_ftp.txt').readlines()
host = str(con_infos[2]).strip()
user = str(con_infos[4]).strip()
password = str(con_infos[6]).strip()


ftp = ftplib.FTP(host,user,password) # on se connecte
ftp.encoding = "utf-8"
# print the welcome message
print(ftp.getwelcome())

# ---------- last ok ---------------------
# ./HARMONISES

print("-"*50,'\n',"-"*16, "Collecting files", "-"*16, '\n',"-"*50)

df_harmonises = ftp_synth.list_files(ftp, dir_name = 'HARMONISES', format_date="%Y%m%d%H%M%S")
df_ott = ftp_synth.list_files(ftp, dir_name = 'OTT', format_date="%Y%m%d%H%M%S")
df_seba  = ftp_synth.list_files(ftp, dir_name = 'SEBA', format_date="%Y%m%d_%H%M%S")

df_ok = df_harmonises.append(df_ott)

print('DFs created (Harmon, SEBA, OTT)')

# ---------- last pb ---------------------
# './SEBA' ; name begin with '.' or size = 0

#ftp.cwd('SEBA')

# for file_name in ftp.nlst():
# we don't get files beginning with '.'. Why ??
# same with dir()

print("-"*50,'\n',"-"*15, "Checkin for errors", "-"*15, '\n',"-"*50)

df_errors = ftp_synth.check_errors(ftp, 'SEBA')

print('Errors checked, merging dataframes...')

# disconnect ftp
ftp.quit()

del ftp, host, password, user

print('Closing ftp connection...')

#-------------- Make unique df for map and export -----------
# join dfs
df_ftp = df_ok.merge(df_errors, on='indice', how='left')
# group by max(date)
df_ftp = df_ftp.groupby(['indice']).max()

#pz = pd.read_csv(r'../SIG/rsx_pz_hdf.csv',  sep = ';', encoding = 'ANSI')
pz = pd.read_excel(path_data+'rsx_pz_hdf_wgs84.xlsx') #,  encoding = 'utf-8')

# clean before join
# typage....
pz['indice'] = [str(x) for x in pz['indice']]
#df_ftp['indice'] = [str(x) for x in df_ftp['indice']] # indice is index here
# join
pz = pz.join(df_ftp, on='indice')

df_export = pz[['indice', 'nom', 'size', 'file', 'last_push', 'last_error']]

# sort by date
df_export = df_export.sort_values(by = ['last_push','last_error'], ascending=True)

# Exports : csv and xlsx (for teams)
#df_ftp.to_csv(r'./suivi_ftp.csv', sep=';')
df_export.to_excel(path_OUT+'suivi_ftp.xlsx', sheet_name='ftp_synthese', index = False)

print('Exporting done !')
# cleaning
del df_errors, df_harmonises, df_ok, df_ott, df_seba, df_ftp

# copy file
# from shutil import copyfile
# src = path_OUT+'suivi_ftp.xlsx'
# dst = '../../suivi_ftp.xlsx'
# copyfile(src, dst)
