import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from gsheetsdb import connect

from bokeh.plotting import figure



# Create a connection object.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
    ],
)
conn = connect(credentials=credentials)

# Perform SQL query on the Google Sheet.
# Uses st.cache to only rerun when the query changes or after 10 min.
@st.cache(ttl=600)
def run_query(query):
    rows = conn.execute(query, headers=1)
    rows = rows.fetchall()
    return rows

sheet_url = st.secrets["private_gsheets_url"]
rows = run_query(f'SELECT * FROM "{sheet_url}"')

@st.cache()
def get_data():
    # TODO: must be a better way to get rows into dataframe.. see google docs
    df = pd.DataFrame({
        'date': [row.Date for row in rows],
        'distance': [row.Distance for row in rows],
        'speed': [row.Speed for row in rows],
        'avg_hr': [row.Avg_HR for row in rows]
    })
    df['duration (hr)'] = df['distance'] / df['speed']
    df.sort_values(by='date', inplace=True)
    return df

df = get_data()
st.write("# Marathon Training")
st.write("2022 Portland Marathon Training runs")


p = figure(x_axis_type="datetime", title="Running Distances", plot_height=350, plot_width=800)
p.background_fill_color = "#97ead2"
p.xgrid.grid_line_color=None
p.ygrid.grid_line_alpha=0.5
p.xaxis.axis_label = 'Time'
p.yaxis.axis_label = 'Value'

p.line(df['date'], df['distance'], width=3, color="#FEA572")
p.circle(df['date'], df['distance'], size=8, color="#FE640B")

st.bokeh_chart(p)


st.dataframe(df)