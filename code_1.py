# Published dashboard URL: https://your-dashboard-link.com
# (If you have password-protected your site, include the password here, e.g., Password: mypassword)

import numpy as np
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import ssl

# Optional: Uncomment the next line if you continue to have SSL certificate issues.
# ssl._create_default_https_context = ssl._create_unverified_context

# -------------------------------------------------------------
# Step 1: Create the dataset for the dashboard.
# -------------------------------------------------------------
url = "https://en.wikipedia.org/wiki/List_of_FIFA_World_Cup_finals"

# Read all tables from the URL
tables = pd.read_html(url)

df = None
for table in tables:
    # Convert column names to strings and strip whitespace
    table.columns = table.columns.astype(str).str.strip()
    cols = table.columns.tolist()
    print("Found table columns:", cols)  # Debug: view columns
    if 'Year' in cols and ( 'Winner' in cols or 'Winners' in cols ) and \
       ( 'Runner-up' in cols or 'Runners-up' in cols or 'Runners‑up' in cols ):
        df = table.copy()
        break

if df is None:
    raise ValueError("No suitable table found on the Wikipedia page. Please check the page structure.")

# Determine correct column names for winners and runner-ups
if 'Winners' in df.columns:
    winner_col = 'Winners'
elif 'Winner' in df.columns:
    winner_col = 'Winner'
else:
    raise ValueError("No Winner column found.")

if 'Runners‑up' in df.columns:
    runner_col = 'Runners‑up'
elif 'Runners-up' in df.columns:
    runner_col = 'Runners-up'
elif 'Runner-up' in df.columns:
    runner_col = 'Runner-up'
else:
    raise ValueError("No Runner‑up column found.")

# Select only the necessary columns: Year, Winner, and Runner-up
df = df[['Year', winner_col, runner_col]].copy()

# Standardize country names: treat West Germany as Germany
df[winner_col] = df[winner_col].replace({'West Germany': 'Germany'})
df[runner_col] = df[runner_col].replace({'West Germany': 'Germany'})

# Create a dataset for the choropleth map: count wins per country
win_counts = df[winner_col].value_counts().reset_index()
win_counts.columns = ['Country', 'Wins']

# -------------------------------------------------------------
# Step 2: Build the interactive dashboard.
# -------------------------------------------------------------
# Create a Choropleth map using Plotly Express
fig = px.choropleth(
    win_counts,
    locations='Country',
    locationmode='country names',
    color='Wins',
    hover_name='Country',
    color_continuous_scale=px.colors.sequential.Plasma,
    title='FIFA World Cup Wins by Country'
)

# Update the figure background to #F9FEFF
fig.update_layout(
    paper_bgcolor='#F9FEFF',
    plot_bgcolor='#F9FEFF'
)
fig.update_geos(bgcolor='#F9FEFF')

# Initialize the Dash app
app = dash.Dash(__name__)
# Expose the underlying Flask server for deployment (e.g., on Render)
server = app.server

# Define the app layout with a light background color and your name below the title.
app.layout = html.Div([
    html.H3("Mikhail Karmali (201495920)"),
    html.H1("FIFA World Cup Winners Dashboard"),
    
    # Display the choropleth map
    dcc.Graph(id='choropleth-map', figure=fig),
    
    # List all countries that have won the World Cup
    html.Div([
        html.H2("Countries that have Secured a World Cup Title"),
        html.Ul([html.Li(country) for country in sorted(win_counts['Country'].unique())])
    ], style={'margin-top': '30px'}),
    
    # Dropdown for selecting a country to view stats
    html.Div([
        html.H2("Choose a Nation to Review Its World Cup Record"),
        dcc.Dropdown(
            id='country-dropdown',
            options=[{'label': country, 'value': country} for country in sorted(win_counts['Country'].unique())],
            placeholder="Select a Nation"
        ),
        html.Div(id='country-stats', style={'margin-top': '10px', 'font-weight': 'bold'})
    ], style={'margin-top': '30px'}),
    
    # Dropdown for selecting a year to view match details
    html.Div([
        html.H2("Select a Year to Uncover Final Match Outcomes"),
        dcc.Dropdown(
            id='year-dropdown',
            options=[{'label': str(year), 'value': year} for year in sorted(df['Year'].unique())],
            placeholder="Select a Year"
        ),
        html.Div(id='year-details', style={'margin-top': '10px', 'font-weight': 'bold'})
    ], style={'margin-top': '30px'})
],
style={
    'backgroundColor': '#F9FEFF',  # Light background for the entire dashboard
    'padding': '20px'
})

# -------------------------------------------------------------
# Step 3: Callbacks
# -------------------------------------------------------------
# Callback to update stats for a selected country
@app.callback(
    Output('country-stats', 'children'),
    [Input('country-dropdown', 'value')]
)
def update_country_stats(selected_country):
    if not selected_country:
        return "Please select a nation from the dropdown above."
    
    # Count championships and runner-up finishes
    championships = df[df[winner_col] == selected_country].shape[0]
    second_place = df[df[runner_col] == selected_country].shape[0]
    total_appearances = championships + second_place
    # Get years when the country won and was runner-up
    win_years = df.loc[df[winner_col] == selected_country, 'Year'].tolist()
    runner_years = df.loc[df[runner_col] == selected_country, 'Year'].tolist()
    
    return html.Div([
        html.H3(f"{selected_country} – World Cup Record"),
        html.P(f"Championship Titles: {championships}"),
        html.P(f"Second-Place Finishes: {second_place}"),
        html.P(f"Overall Finals Appearances: {total_appearances}"),
        html.P(
            "Championship Years: " + ", ".join(str(y) for y in win_years)
            if win_years else "Championship Years: None"
        ),
        html.P(
            "Runner-Up Years: " + ", ".join(str(y) for y in runner_years)
            if runner_years else "Runner-Up Years: None"
        )
    ])

# Callback to update match details for a selected year
@app.callback(
    Output('year-details', 'children'),
    [Input('year-dropdown', 'value')]
)
def update_year_details(selected_year):
    if not selected_year:
        return "Please select a year from the dropdown above."
    match = df[df['Year'] == selected_year]
    if match.empty:
        return "Data not available for the selected year."
    winner = match.iloc[0][winner_col]
    runner_up = match.iloc[0][runner_col]
    return f"In {selected_year}, the title was clinched by {winner}, with {runner_up} finishing as runner-up."

# -------------------------------------------------------------
# Step 4: Run the app locally.
# -------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
