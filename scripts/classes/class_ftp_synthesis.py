# -*- coding: utf-8 -*-
"""
Created on Fri Jan 29 19:41:15 2021

@author: manlaya
"""
import ftplib
import pandas as pd
import re #regex
from datetime import datetime

class ftp_synthesis:
    def __init__(self, host, user, password):
        ftp = ftplib.FTP(host,user,password) # on se connecte
        ftp.encoding = "utf-8"
        # print the welcome message
        print(ftp.getwelcome())
        
    # https://www.thepythoncode.com/article/list-files-and-directories-in-ftp-server-in-python
    # some utility functions that we gonna need
    def get_size_format(n, suffix="B"):
        # converts bytes to scaled format (e.g KB, MB, etc.)
        for unit in ["", "K", "M", "G", "T", "P"]:
            if n < 1024:
                return f"{n:.2f}{unit}{suffix}"
            n /= 1024
    
    def get_datetime_format(date_time):
        # convert to datetime object
        date_time = datetime.strptime(date_time, "%Y%m%d%H%M%S")
        # convert to human readable date time string
        return date_time.strftime("%Y/%m/%d %H:%M:%S")
    
    def list_files(ftp, dir_name, format_date):
        # change ftp wd
        #wdir = ftp.pwd()
        #print(wdir)
        ftp.cwd(dir_name)
        #ftp.pwd()
        
        # listing
        files=[]
        ftp.dir(files.append) # get files listing
        #print(files)
        
        df = pd.DataFrame(files)
        df.columns = ['varii']
        
        n=1
        df=df.drop(df.tail(n).index[0],axis=0)
        
        df = df.varii.replace('-rwx------    1 2001       piezogroup', '', regex=True)
        df = pd.DataFrame({'info':[str.strip(i) for i in df]})
        df = pd.DataFrame(df['info'].str.split().tolist(), columns=['size', 'day','day_num', 'hour', 'file'])
        
        size = df['size'].tolist()
        size = [int(i) for i in size]
        size = [ftp_synthesis.get_size_format(i) for i in size]
        df['size'] = size
        
        df['indice']= df['file'].str.slice(0, 10)
        df['last_push'] = df['file'].str.slice(11, -4)
        df['last_push'] = pd.to_datetime(df['last_push'], format=format_date)
        
        df = df.drop(['day','day_num','hour'], 1) # 0 line, 1 col
        
        #dict = {'indice': indice, 'last_push': date, 'size': size, 'file_name': file_n}
        #df1 = pd.DataFrame(dict)
    
        #back to the root folder
        ftp.cwd('../')
        return df
    
    def check_errors(ftp, path):
        ftp.cwd(path)
        names = []
        #mlsd ok...
        # List ALL files in path
        for file_data in ftp.mlsd():
            # extract returning data
            file_name, meta = file_data
            #print(file_name)
            names.append(file_name)    
        # Looking for points at the beginning of files name    
        regexp = '^\.'
        errors = []
        #seba_ok = []
        # check for matching errors
        for i in names:
        # root and previous folder ('.', '..') not needed... filter on element length 
            if len(i)>2:
                match = re.match(regexp, i)
                #print(match)
                if match is not None:
                    #print(match)
                    errors.append(i)
                    #errors.append(match[1])
                #else:
                #    seba_ok.append(i)
        #error = [names[i] for i in names if len(i)>2 & re.match(regexp, i) is not None]
        
        # Transform into df to join
        indice = [x[1:11] for x in errors]
        date_m = [x[12:-4] for x in errors]
        date_m = [datetime.strptime(i, "%Y%m%d_%H%M%S") for i in date_m]
        
        d = {'indice' : indice, 'last_error':date_m}
        df_error = pd.DataFrame(d)
        
        # back to root folder
        ftp.cwd('../')
        
        return df_error

    # time since last push calculation
    def calc_delay(df):
        delay_push = []
        for i in range(0,len(df)):
            #si télétransmis df.iloc[i]['nom_col'] ou [i,14]
            if df.iloc[i]['teletrans'] ==1:
                #si une date
                if df.iloc[i]['last_push'] != 9999:
                    delay = datetime.now() - df.iloc[i]['last_push']
                    delay = round(float(delay.total_seconds()/(60*60*24)),2)
                    delay_push.append(delay)
                else:
                    # si pas de date mais télétransmis on met une valeure arbitraire
                    delay_push.append(float(99.0))
            elif df.iloc[i]['suivi_actif']==1:
                # sinon on code la valeur nulle
                # 9999 si suivi mais pas télétransmis
                delay_push.append(float(9999.0))
            else:
                # - 9999 si actuellement pas suivi
                delay_push.append(float(-9999.0))
            
        return delay_push

if __name__=='__main__':
    ftp_synthesis()