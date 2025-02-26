import dash
from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import io
import base64

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Manual Integrator", style={'textAlign': 'center'}),
    dcc.Upload(
        id='upload-data',
        children=html.Button('Open New CSV-File'),
        style={'display': 'block', 'margin': '10px auto'}
    ),
    html.Div(id='file-label', style={'textAlign': 'center'}),
    dcc.Graph(id='graph', config={'modeBarButtonsToAdd': ['drawline']}),
    html.Div([
        html.Button('Export Boundaries', id='export-button', n_clicks=0),
        dcc.Download(id='download-markers')
    ], style={'textAlign': 'center', 'margin': '10px'}),
    dcc.Upload(
        id='upload-markers',
        children=html.Div(['Drag and Drop or ', html.A('Select a File for Import Boundaries')]),
        style={
            'width': '100%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
        }
    ),
    dash_table.DataTable(
        id='markers-table',
        columns=[{"name": "Marker Position", "id": "position"}],
        data=[],
        style_table={'margin': 'auto', 'width': '50%'}
    )
])

def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    return decoded

@app.callback(
    [Output('file-label', 'children'),
     Output('graph', 'figure')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_graph(contents, filename):
    if contents is None:
        return "No file selected", go.Figure()

    decoded_content = parse_contents(contents)
    try:
        df = pd.read_csv(io.StringIO(decoded_content.decode('utf-8')))
    except Exception as e:
        return f"Error loading file: {str(e)}", go.Figure()

    if df.shape[1] < 2:
        return "CSV does not have at least two columns.", go.Figure()

    x_data = df[df.columns[0]]
    y_data = df[df.columns[1]]

    fig = go.Figure(data=go.Scatter(x=x_data, y=y_data, mode='lines', name='Signal'))
    fig.update_layout(title=filename, xaxis_title=df.columns[0], yaxis_title=df.columns[1])

    return f"Current file: {filename}", fig

@app.callback(
    Output('markers-table', 'data'),
    Input('graph', 'relayoutData'),
    State('markers-table', 'data')
)
def manage_markers(relayoutData, existing_data):
    ctx = callback_context
    if not ctx.triggered or 'shapes' not in relayoutData:
        return existing_data

    new_data = []
    shapes = relayoutData['shapes']
    for shape in shapes:
        if shape['type'] == 'line' and shape['x0'] == shape['x1']:
            pos = shape['x0']
            new_data.append({'position': pos})
            
    # Append new markers only if they are unique
    updated_positions = set([item['position'] for item in existing_data])
    for item in new_data:
        if item['position'] not in updated_positions:
            existing_data.append(item)

    return existing_data

@app.callback(
    Output('download-markers', 'data'),
    Input('export-button', 'n_clicks'),
    State('markers-table', 'data'),
    prevent_initial_call=True
)
def export_markers(n_clicks, marker_data):
    if not marker_data:
        return None

    df = pd.DataFrame(marker_data)
    return dcc.send_data_frame(df.to_csv, "markers.csv", index=False)

@app.callback(
    Output('markers-table', 'data'),
    Input('upload-markers', 'contents'),
    prevent_initial_call=True
)
def import_markers(contents):
    if contents is None:
        return []

    decoded_content = parse_contents(contents)
    try:
        df = pd.read_csv(io.StringIO(decoded_content.decode('utf-8')))
        return [{'position': row[0]} for row in df.itertuples(index=False)]
    except Exception as e:
        print(str(e))
        return []

if __name__ == '__main__':
    app.run_server(debug=True)
