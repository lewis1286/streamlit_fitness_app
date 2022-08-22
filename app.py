from bokeh.plotting import figure
from google.oauth2 import service_account
from gsheetsdb import connect
import pandas as pd
import streamlit as st


# COLORS:  #003f5c, #58508d, #bc5090, #ff6361 and #ffa600
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
        'date': [row.Date for row in rows if row.Activity == 'Run'],
        'distance': [row.Distance for row in rows if row.Activity == 'Run'],
        'speed': [row.Speed for row in rows if row.Activity == 'Run'],
        'avg_hr': [row.Avg_HR for row in rows if row.Activity == 'Run']
    })
    df['duration (hr)'] = df['distance'] / df['speed']
    df.sort_values(by='date', inplace=True)
    df['hr_smooth'] = df['avg_hr'].rolling(6, win_type='cosine').mean()

    return df

df = get_data()
st.markdown("# Marathon Training Runs")

st.vega_lite_chart(df, {
    'title': {
        'text': 'Running Distances Over Time',
        "color": "#2ecc71",
        "fontSize": 24
    },
    'layer': [
        {
            'mark': {'type': 'line'},
            'encoding': {
                'x': {
                    'field': 'date',
                    'type': 'temporal',
                    "title": {
                        "text": "Run Date",
                        "color": "#ffa600"
                    }
                },
                'y': {
                    'field': 'distance',
                    'type': 'quantitative',
                    "title": "Distance (mi)"
                },
                "color": {"value": "#db646f"}
            }
        },
        {
            'mark': {'type': 'circle', 'size': '90', 'tooltip': True},
            'encoding': {
                'x': {'field': 'date', 'type': 'temporal'},
                'y': {'field': 'distance', 'type': 'quantitative'},
                "color": {"value": "#db646f"}
            }
        },
    ]
}, use_container_width=True)



st.write("---")
st.markdown("## Heart Rate")
st.write("""
    Hopefully one would see a descending average heart rate on each run over time.  
    This is ignoring the fact that higher speeds and distances yield higher heartrates, as well as hills, 
    temperature.. but over a long enough time-scale, ideally these will average out.
""")

st.vega_lite_chart(df,
    {
        'title': {
            'text': 'Average HR',
            "color": "#2ecc71",
            "fontSize": 24
        },
        "layer": [
            {
                "mark": {"type": "line", "tooltip": False},
                "encoding": {
                    "x": {
                        'field': 'date',
                        'type': 'temporal',
                        "title": "Run Date"
                    },
                    "y": {
                        "field": "avg_hr",
                        "type": "quantitative",
                        "title": "Average Heart Rate (bpm)",
                        "scale": {"domain": [120, 170]}
                    },
                    "color": {"value": "#db646f"}
                }
            },
            {
                "mark": {"type": "circle", "size": 90, "tooltip": True},
                "encoding": {
                    "x": {
                        "field": "date",
                        "type": "temporal",
                    },
                    "y": {
                        "field": "avg_hr",
                        "type": "quantitative"
                    },
                    "color": {"value": "#db646f"}
                }

            },
            {
                "mark": {"type": "line", "tooltip": False},
                "encoding": {
                    "x": {
                        "field": "date",
                        "type": "temporal",
                    },
                    "y": {
                        "field": "hr_smooth",
                        "type": "quantitative"
                    }
                }
            }
        ]
    }, use_container_width=True
)

st.write("---")
st.markdown("## How it works")
st.image("assets/overview.png", caption="data flow")
LINK_COLOR="#94D2BD"

st.markdown(f"""
My runs are recorded on a garmin Fenix 5x wristwatch (GPS, heartrate).  The Garmin app has an API to automatically push 
activities to Strava, that can be accessed through their UI.  The Strava activities are pushed to a Google sheet using Zapier.
It would be nice if Garmin exposed an API to Zapier, but not yet and not sure if it's on their roadmap.  This streamlit app reads straight
from google sheets.  See <a href="https://docs.streamlit.io/knowledge-base/tutorials/databases/public-gsheet"> here </a> for a walkthrough 
on how it works and <a href="https://github.com/lewis1286/streamlit_fitness_app"> here </a> for the code
""", unsafe_allow_html=True)

# FOOTER
# thanks https://discuss.streamlit.io/t/streamlit-footer/12181
footer="""
    <style>
        a:link , a:visited{
            color: blue;
            background-color: transparent;
            text-decoration: underline;
        }

        a:hover,  a:active {
            color: red;
            background-color: transparent;
            text-decoration: underline;
        }

        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: white;
            color: black;
            text-align: center;
        }
    </style>
    <div class="footer">
    <p>Developed with ❤ by <a style='display: block; text-align: center;' href="https://www.diffusecreation.com" target="_blank">Lewis Guignard</a></p>
    </div>
"""
# takes up too much real estate on mobile
# st.markdown(footer, unsafe_allow_html=True)


st.markdown("""
    ---
    <div>
        <p style='display: block; text-align: right;'>
            Developed with ❤ by <a  href="https://www.diffusecreation.com" target="_blank">Lewis Guignard</a> 
        </p>
    </div>
""", unsafe_allow_html=True)
