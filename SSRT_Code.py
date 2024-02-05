#  Importing the libraries

import pandas as pd
import os
from tkinter import Tcl
from dotenv import load_dotenv

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#  Defining the files and the path of the data
load_dotenv()
path = os.getenv("INPUT_PATH")
os.chdir(path)
folder = os.listdir(path)
folder = Tcl().call('lsort', '-dict', folder)  # Code used to correctly sort the files by number

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#  Here we create a dictionary of the data with the id numbers of the participants and the dataframes we will work on:
#  Labels:
# id: identification number of the participants
# df: dataframes with the data of the participants
# race_model: list with the values of the mean response time of go trials minus the mean response time of unsuccesful
#   stop trials
# p_respondsignal: list with the values of the p(respond|signal) => Subject probability of responding on a stop trial.
# ssrt_mm: list with the values of SSRTT calculated using the Mean Method
# p_adj: list with the values of the adjusted p(respond|signal) to compensate for go omissions
#   (used to calculate SSRTT with IM)
# ssrt_im: list with the values of SSRTT calculated using the Integration Method (with replacement of go omissions)
# p_gomission: participants probability of not responding on a go trial (go omission)
# p_choicerrors: participants probability of responding incorrectly on a go trial (choice error)
# meanRTgo: list with the values of the mean response time on go trials of the participants
# meanSSD: list with the values of the mean stop signal delay
# meanRTunsuccessfulNoGo: list with the values of the mean response time on unsuccesful stop trials

data = {
    'id': [],
    'df': [],
    'race_model': [],
    'p_respondsignal': [],
    'p_adj': [],
    'p_gomission': [],
    'p_choicerrors': [],
    'n_respondsignal': [],
    'n_gomission': [],
    'n_choicerrors': [],
    'meanRTgo': [],
    'meanRTunsuccessfulNoGo': [],
    'meanSSD': [],
    'ssrt_mm': [],
    'ssrt_im': [],
    'ssrt_im_adj': []
}

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

""" Loading and preparing the data for the analysis """

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# Code to read all the files, clean the data and store them as dataframes
for file in folder:
    if file.endswith('.csv'):
        data['id'].append(int(file.split('-')[0]))
        df_csv = pd.read_csv(file, header=0, skiprows=[i for i in range(1, 25)],
                             usecols=['correct_response', 'response', 'correct_kb_response', 'response_time',
                                      'stop_after'], dtype={'correct_kb_response': int})
        data['df'].append(df_csv)
    elif file.endswith('.xlsx'):
        data['id'].append(int(file.split('-')[0]))
        df_excel = pd.read_excel(file, header=0, skiprows=[i for i in range(1, 25)],
                                 usecols=['correct_response', 'response', 'correct_kb_response', 'response_time',
                                          'stop_after'], dtype={'correct_kb_response': int})
        data['df'].append(df_excel)

#  Code to replace the wrong values in the 'correct_kb_response' column by comparing the 'response' and 'correct_response' values.
for df in data['df']:
    i = 0
    while i < len(df):
        if df.iloc[i, 1] == df.iloc[i, 2]:
            df.iloc[i, 0] = 1
        elif df.iloc[i, 1] != df.iloc[i, 2]:
            df.iloc[i, 0] = 0
        i += 1

#  Code to add a column called block that is equal to the column 'correct_response' but replaces the values as follows:
#  {'right': 'Go', 'left': 'Go', 'None': 'NoGo'}
block_value = {'right': 'Go', 'left': 'Go', 'None': 'NoGo'}
for df in data['df']:
    df['block'] = df['correct_response'].replace(block_value)

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# Function to call the information in the dictionary by calling the id of the participants
def data_df(data, id):
    df = data['df'][data['id'].index(id)]
    return df

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

""" Statistical Analysis of the data """

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# Code to check if the assumption of the race model is violated:
# SSRT should not be estimated if meanRT(NoGo-0) is numerically longer than meanRT(Go)
for df in data['df']:
    df_g = df.groupby(['block']).get_group(('Go'))
    df_g = df_g[df_g['response'].str.contains('None') == False]
    v_mg = df_g['response_time'].mean()
    try:
        df_n0 = df.groupby(['block', 'correct_kb_response']).get_group(('NoGo', 0))
        v_n0 = df_n0['response_time'].mean()
        data['race_model'].append(v_mg - v_n0)
    except:
        data['race_model'].append(v_mg)


# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# Code to calculate the probability of go omissions (p_gomission)
for df in data['df']:
    try:
        df_gnone = df.groupby(['block', 'response']).get_group(('Go', 'None'))
        v_gnone = df_gnone['response'].count()
        data['n_gomission'].append(v_gnone)
        data['p_gomission'].append(v_gnone / 150)
    except:
        data['n_gomission'].append(0)
        data['p_gomission'].append(0)


# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# Code to calculate the probability of choice errors on go trials
for df in data['df']:
    try:
        df_g0 = df.groupby(['block', 'correct_kb_response']).get_group(('Go', 0))
        df_gnone = df.groupby(['block', 'response']).get_group(('Go', 'None'))
    except:
        try:
            df_g0 = df.groupby(['block', 'correct_kb_response']).get_group(('Go', 0))
        except:
            data['n_choicerrors'].append(0)
            data['p_choicerrors'].append(0)
        else:
            v_g0 = df_g0['correct_kb_response'].count()
            data['n_choicerrors'].append(v_g0)
            data['p_choicerrors'].append(v_g0 / 150)
    else:
        v_g0 = df_g0['correct_kb_response'].count()
        v_gnone = df_gnone['response'].count()
        data['n_choicerrors'].append(v_g0 - v_gnone)
        data['p_choicerrors'].append((v_g0 / 150) - (v_gnone / 150))

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# Code to calculate the mean RT on all go Trials
for df in data['df']:
    df_g = df.groupby(['block']).get_group('Go')
    df_g = df_g[df_g['response'].str.contains('None') == False]
    v_mg = df_g['response_time'].mean()
    data['meanRTgo'].append(v_mg)

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# Code to calculate the average Stop-Signal delay (SSD)
for df in data['df']:
    mSSD = df['stop_after'].mean()
    data['meanSSD'].append(mSSD)

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# Code to calculate the mean RT of go responses on unsuccessful stop trials
for df in data['df']:
    try:
        df_n0 = df.groupby(['block', 'correct_kb_response']).get_group(('NoGo', 0))
        v_mn0 = df_n0['response_time'].mean()
        data['meanRTunsuccessfulNoGo'].append(v_mn0)
    except:
        data['meanRTunsuccessfulNoGo'].append(0)

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# Code to create a p(respond|signal) to NoGo trials:
# p(respond|signal) = probability of responding on a stop trial (NoGo)
for df in data['df']:
    df_n1 = df.groupby(['block', 'correct_kb_response']).get_group(('NoGo', 1))  # p(NoGo(0)) = 1 - (NoGo(1))
    v_sn1 = df_n1['correct_kb_response'].sum()
    data['n_respondsignal'].append(50 - v_sn1)
    p = 1 - (v_sn1 / 50)
    data['p_respondsignal'].append(p)

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# Estimates SSRT using Mean Method:
for df in data['df']:
    df_g = df.groupby(['block']).get_group(('Go'))
    v_mg = df_g['response_time'].mean()
    v_ssd = df['stop_after'].mean()
    data['ssrt_mm'].append(v_mg - v_ssd)

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# Estimates SSRT using Integration Method with replacement of go omissions
# Finds the nth RT using p(respond|Signal) and calculate SSRTT using Integration Method
for df in data['df']:
    df_g = df.groupby(['block']).get_group('Go').copy()
    df_g_subset = df_g[df_g['response'].str.contains('None') == False]
    maxRT = df_g_subset['response_time'].max()
    df_g.loc[df_g.response_time > 1990, 'response_time'] = maxRT
    df_n1 = df.groupby(['block', 'correct_kb_response']).get_group(('NoGo', 1))
    v_sn1 = df_n1['correct_kb_response'].sum()
    p = 1 - (v_sn1 / 50)
    nth = round(p * 150)
    df_go_sorted = df.groupby(['block']).get_group('Go').sort_values(by=['response_time'])
    nthRT = df_go_sorted['response_time'].iloc[nth - 1]
    meanSSD = df['stop_after'].mean()
    data['ssrt_im'].append(nthRT - meanSSD)

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# Code to estimate the SSRT using the Integration Method with p_adjusted values:
# In order to calculate the SSRT, be mindful of the number of trials of your experiment (both Go and Stop trials). Here
# we are utilizing 200 total trials, 150 Go trials and 50 stop trials.
for df in data['df']:
    try:
        df_gnone = df.groupby(['block', 'response']).get_group(('Go', 'None'))
        v_gnone_count = df_gnone['response'].count()
        df_n1 = df.groupby(['block', 'correct_kb_response']).get_group(('NoGo', 1))
        v_sn1 = df_n1['correct_kb_response'].sum()
        p_adj = 1 - ((v_sn1 / 50 - (v_gnone_count / 150)) / (1 - (v_gnone_count / 150)))
        data['p_adj'].append(p_adj)
        nth = round(p_adj * 150)
        df_go_sorted = df.groupby(['block']).get_group('Go').sort_values(by=['response_time'])
        nthRT = df_go_sorted['response_time'].iloc[nth - 1]
        meanSSD = df['stop_after'].mean()
        data['ssrt_im_adj'].append(nthRT - meanSSD)
    except:
        df_n1 = df.groupby(['block', 'correct_kb_response']).get_group(('NoGo', 1))  # NoGo(1) = 1 - NoGo(0)
        v_sn1 = df_n1['correct_kb_response'].sum()
        p_adj = 1 - (v_sn1 / 50)
        data['p_adj'].append(p_adj)
        nth = round(p_adj * 150)
        df_go_sorted = df.groupby(['block']).get_group('Go').sort_values(by=['response_time'])
        nthRT = df_go_sorted['response_time'].iloc[nth - 1]
        meanSSD = df['stop_after'].mean()
        data['ssrt_im_adj'].append(nthRT - meanSSD)

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#  Code to present the data:
data_f = {key: val for key, val in data.items() if key != 'df'}
tab_data = pd.DataFrame(data_f)

# Defining the path and name of the Excel file that will be saved from the dataframe
path_to_save = os.getenv("OUTPUT_PATH")
tab_data.to_excel(path_to_save, index=False)
print(tab_data)

# END OF CODE
# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////