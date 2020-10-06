import streamlit as st
from core import *

st.header('Upward Algorithm Tester')
'''
This dashboard generates explores the Upward Placement Algorithm by generating
a random set of analysts and teams and showing where the algorithm places them.

Currently, it only simulates inter-rotational placement. A future version will
simulate full-time placement and multi-tiered placement as well.
'''
st.sidebar.subheader('Random Data Parameters')
n_analysts = st.sidebar.slider('Number of Analysts', 1, 40)
n_teams = st.sidebar.slider('Number of Teams', 1, 15)
extra_spots = st.sidebar.slider('Extra Headcount', 0, 20)

rand_schema = random_schema(n_analysts, n_teams, extra_spots)

st.subheader('Schema')
st.json(rand_schema.json())

st.subheader('Algorithm Results')
results = rand_schema.set_placements(noisy=False)
for team in results.keys():
    analysts = results[team]
    analysts = [analyst.name for analyst in analysts]
    results[team] = analysts

st.json(results)

st.subheader('Algorithm Log')
log = rand_schema.log
for iteration in log.keys():
    if 'Unassigned Analysts' in log[iteration].keys():
        analysts = log[iteration]['Unassigned Analysts']
        analysts = [analyst.name for analyst in analysts]
        log[iteration]['Unassigned Analysts'] = analysts
st.json(log)
#st.write(rand_schema.log_txt)
