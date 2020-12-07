import streamlit as st
import numpy as np
import pandas as pd
import base64
from core import *

'''
# Upward Sorting Hat
'''

def read_file(file):
    try:
        df = pd.read_csv(file)
    except ValueError:
        df = pd.read_excel(file)
    return df


def map_perf(perf_string):
    perf_map = {
        'Low': 1,
        'Meets': 2,
        'Strong': 3,
        'Top': 4
    }
    return perf_map[perf_string]


def get_table_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a download="robot_results.csv" href="data:file/csv;base64,{b64}">Download as a CSV.</a>'
    return href

def generate_schema(analyst_df, team_df, rotation_type):
    analyst_data = analyst_df.to_dict(orient='rows')
    team_data = team_df.to_dict(orient='row')
    if rotation_type == 'Rotation':
        analysts = []
        for row in analyst_data:
            new_analyst = Analyst(name=row['Analyst Name'],
                                  clas=int(row['Analyst Class'][-1]),
                                  perf=map_perf(row['Analyst Performance']),
                                  prefs={
                                      row['First Choice']: 0,
                                      row['Second Choice']: 1,
                                      row['Third Choice']: 2
                                  }
                                  )
            analysts.append(new_analyst)
        teams = []
        for row in team_data:
            new_team = Team(name=row['Department Name'],
                            headcount=row['Department Headcount'])
            teams.append(new_team)
        schema = Schema(analysts, teams)
        return schema
    if rotation_type == 'Final':
        analysts = []
        for row in analyst_data:
            new_analyst = Analyst(name=row['Analyst Name'],
                                  clas=0,
                                  perf=map_perf(row['Analyst Performance']),
                                  prefs={
                                      row['First Choice']: 0,
                                      row['Second Choice']: 1,
                                      row['Third Choice']: 2
                                  }
                                  )
            analysts.append(new_analyst)
        teams = []
        for row in team_data:
            df_cols = list(team_df.columns)
            rating_cols = df_cols[2:]
            ratings = {}
            for col in rating_cols:
                if isinstance(row[col], str):
                    ratings[row[col]] = int(col)
            new_team = Team(name=row['Department Name'],
                            headcount=row['Department Headcount'],
                            ratings=ratings)
            teams.append(new_team)
            schema = Schema(analysts, teams)
        return schema

rotation_type = st.selectbox('Choose Placement Type', ['Rotation', 'Final'])
analyst_file = st.file_uploader('Upload Analyst Data', ['csv'])
if analyst_file:
    analyst_df = read_file(analyst_file)
    st.write('### Analyst Data')
    st.write(analyst_df)

team_file = st.file_uploader('Upload Team Data', ['csv'])
if team_file:
    team_df = read_file(team_file)
    st.write('### Team Data')
    st.write(team_df)

if team_file and analyst_file:
    # '''
    # If the data looks good, press the button below.
    # '''
    # run_algorithm = st.button('Run Algorithm')
    # if run_algorithm:
    schema = generate_schema(analyst_df, team_df, rotation_type)
    ranktype = 'fulltime' if rotation_type == 'Final' else 'rotation'
    '''
    ## Placements
    Given the data you input, here's where the analysts all end up.
    '''
    ## For dev
    results = schema.set_placements(ranktype=ranktype)
    results_df = []
    for team in results.keys():
        analysts = results[team]
        analysts = [analyst.name for analyst in analysts]
        results[team] = analysts
        for analyst in analysts:
            row = {'Team': team, 'Analyst': analyst}
            results_df.append(row)
    results_df = pd.DataFrame(results_df)
    download_link = get_table_download_link(results_df)
    st.write(results)
    st.write(download_link, unsafe_allow_html=True)
    '''
    ## Algorithm Log
    The log shows how the algorithm behaved, and where it placed analysts in
    each iteration, until it finally converged.
    '''

    log = schema.log
    for iteration in log.keys():
        if 'Unassigned Analysts' in log[iteration].keys():
            analysts = log[iteration]['Unassigned Analysts']
            analysts = [analyst.name for analyst in analysts]
            log[iteration]['Unassigned Analysts'] = analysts
    st.json(log)
    '## Schema'
    'The "schema" displays how the program interpreted the data.'
    st.write(schema.json())
