import dash
from dash import dcc, html, callback_context, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import base64
import io

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Manual Integrator", style={'textAlign': 'center'}),
    dcc.Upload(
        id='upload-data',
        children=html.Button('Open New CSV-File'),
        multiple=False
    ),
    html.Div(id='file-info', style={'margin': '10px'}),
    dcc.Graph(id='graph', config={'modeBarButtonsToAdd': ['drawline']}),
    html.Button('Export Boundaries', id='export-btn'),
    dcc.Download(id='download'),
    html.Button('Import Boundaries', id='import-btn'),
    dcc.Upload(id='upload-markers', children=html.Div(['Drag and Drop or ', html.A('Select a File')]), multiple=False),
    dash_table.DataTable(
        id='markers-table',
        columns=[{"name": i, "id": i} for i in ['Marker Position']],
        data=[],
        style_table={'margin': '20px'}
    )
])

def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    return decoded

@app.callback(
    Output('file-info', 'children'),
    Output('graph', 'figure'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_graph(contents, file_name):
    if contents is None:
        return "No file uploaded", go.Figure()

    decoded_content = parse_contents(contents)
    try:
        df = pd.read_csv(io.StringIO(decoded_content.decode("utf-8")))
    except Exception as e:
        return f"Error loading file: {str(e)}", go.Figure()

    x_data = df[df.columns[0]]
    y_data = df[df.columns[1]]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_data, y=y_data, mode='lines', name='Signal'))
    fig.update_layout(title=file_name, xaxis={'title': df.columns[0]}, yaxis={'title': df.columns[1]})
    return f"Current file: {file_name}", fig

@app.callback(
    Output('markers-table', 'data'),
    Input('graph', 'relayoutData'),
    State('markers-table', 'data')
)
def manage_markers(relayoutData, existing_data):
    ctx = callback_context
    if not ctx.triggered:
        return existing_data

    # Check if a line has been drawn
    if 'shapes' in relayoutData:
        line = relayoutData['shapes'][-1]  # The last shape drawn
        if line['type'] == 'line':
            x0 = line['x0']
            existing_data.append({'Marker Position': x0})
            return existing_data

    return existing_data

@app.callback(
    Output('download', 'data'),
    Input('export-btn', 'n_clicks'),
    State('markers-table', 'data'),
    prevent_initial_call=True
)
def export_markers(n_clicks, data):
    if not data:
        return None

    df_export = pd.DataFrame(data)
    return dcc.send_data_frame(df_export.to_csv, "markers.csv", index=False)

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
        lines = decoded_content.decode("utf-8").strip().split('\n')
        data = [{'Marker Position': float(line.split(',')[0])} for line in lines]
    except Exception as e:
        return []

    return data

if __name__ == '__main__':
    app.run_server(debug=True)

