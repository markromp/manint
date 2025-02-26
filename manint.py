import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import base64
import io

app = dash.Dash(__name__)

# Initial app layout with placeholders
app.layout = html.Div([
    html.H3("Group stage - Intercompany Collaboration", style={'text-align': 'center'}),
    dcc.Upload(
        id='upload-data',
        children=html.Button('Open New CSV-File'),
        multiple=False
    ),
    html.Div(id='file-label', style={'margin-top': '10px'}),
    dcc.Graph(id='main-graph'),
    html.Button('Export Boundaries', id='export-button', n_clicks=0),
    dcc.Download(id='download-boundaries'),
    html.Div(id='boundary-message', style={'color': 'red'}),
    dash_table.DataTable(
        id='markers-list',
        columns=[{"name": "Markers", "id": "marker"}],
        style_table={'overflowX': 'scroll'},
        style_cell={'textAlign': 'left'},
        data=[]
    )
])

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            return pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        else:
            return None
    except Exception as e:
        print(e)
        return None

# Callback to handle file uploads and update graph
@app.callback(
    [Output('file-label', 'children'),
     Output('main-graph', 'figure')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_graph(contents, filename):
    if contents is None:
        return "No file selected", go.Figure()

    df = parse_contents(contents, filename)
    if df is None or len(df.columns) < 2:
        return f"Failed to load {filename}", go.Figure()

    x_data = df[df.columns[0]]
    y_data = df[df.columns[1]]
    
    # Plot the data
    figure = go.Figure(data=go.Scatter(x=x_data, y=y_data, mode='lines', name='Signal'))
    figure.update_layout(title=f"File: {filename}", xaxis_title='X', yaxis_title='Y')
    return f"Current file: {filename}", figure

# Manage markers using clickData and manage export functionality
@app.callback(
    Output('markers-list', 'data'),
    Output('boundary-message', 'children'),
    Input('main-graph', 'clickData'),
    State('markers-list', 'data')
)
def manage_markers(clickData, existing_data):
    if clickData:
        marker_x = clickData['points'][0]['x']
        marker_y = clickData['points'][0]['y']
        
        # Simple logic to check if a similar marker already exists
        if any(d['marker'] == (marker_x, marker_y) for d in existing_data):
            return existing_data, "Marker already exists"
        
        existing_data.append({'marker': (marker_x, marker_y)})
        return existing_data, ""
    return existing_data, ""

# Export markers
@app.callback(
    Output('download-boundaries', 'data'),
    Input('export-button', 'n_clicks'),
    State('markers-list', 'data'),
    prevent_initial_call=True
)
def export_markers(n_clicks, rows):
    if n_clicks > 0 and rows:
        df = pd.DataFrame(rows)
        return dcc.send_data_frame(df.to_csv, 'markers.csv', index=False)
    return None

if __name__ == '__main__':
    app.run_server(debug=True)
