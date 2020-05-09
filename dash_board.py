import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

from data_loader import postprocess_data

# Start styles #####################################################################
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
colors = {
    'background': '#ffffff',
    'text': '#4f5250'
}
####################################################################################

kelly_colors, document_projections, it, iw, flat_data, document_topics, topics_vis = postprocess_data()

# Controll elements
topic_selector = dcc.Dropdown(
    id='topic_selector',
    options=[{'label': f'Topic {x}', 'value': x} for x in set(it)],
    value=[x for x in set(it)],
    multi=True
)

projection_selector1 = dcc.Dropdown(
    id='projection_selector1',
    options=[{'label': f'Topic {x}', 'value': x} for x in set(it)],
    value=0,
    multi=False,
    clearable=False
)

projection_selector2 = dcc.Dropdown(
    id='projection_selector2',
    options=[{'label': f'Topic {x}', 'value': x} for x in set(it)],
    value=1,
    multi=False,
    clearable=False
)

selector_div = html.Div(
    children=[html.Label(["Topic 1 Projection Axis x", projection_selector1]),
              html.Label(["Topic 2 Projection Axis y", projection_selector2])],
    style={
        "width": "100%",
    }
)


# End Control elements


### Define callbacks to bind elements to controller ###################################################

@app.callback(
    dash.dependencies.Output('topic_projection', 'figure'),
    [dash.dependencies.Input('projection_selector1', 'value'),
     dash.dependencies.Input('projection_selector2', 'value')])
def produce_scatter_projection(axis1, axis2):
    f = {
        'data': [
            {
                'x': document_projections.iloc[:, axis1].values,
                'y': document_projections.iloc[:, axis2].values,
                'text': [f'Document ID : {x}' for x in document_topics.index.values],
                'mode': 'markers',
                'marker': {'size': 5}
            }
        ],
        'layout': {
            'clickmode': 'event+select',
            'closest': "closest",
            "height": "750",
            "width@": "100%",
            'title': f"Projection on topics {1}, {2}",
        }
    }
    return f


@app.callback(
    dash.dependencies.Output('topic_model-graph', 'figure'),
    [dash.dependencies.Input('topic_selector', 'value')])
def update_topics(value):
    fl = flat_data.copy().iloc[flat_data.index.get_level_values("TopicID").isin(value), :]
    iw_ = fl.index.get_level_values("TopicID")
    it_ = fl.index.get_level_values("Word").values.tolist()

    return {
        'data': [go.Bar(x=fl["weight"].values.tolist(),
                        y=[f"{it_[i]} : {iw_[i]}" for i in range(len(iw_))],
                        marker_color=["rgb" + str(kelly_colors[x]) for ix, x in enumerate(iw_)],
                        hovertext=[f"Topic Id {x}" for x in it_],
                        orientation='h')],
        'layout': {
            'title': 'Topic Distribution Visualisation',
            "height": str((max(len(value * 5) * 25, 600))),
            "width@": "100%"
        }}


# Write Documents
@app.callback(
    dash.dependencies.Output('document_contents', 'children'),
    [dash.dependencies.Input('topic_projection', 'clickData')])
def display_click_data(clickData):
    print(clickData)
    if clickData is None:
        return "Please select a point first"
    _document_db_id = clickData["points"][0]["text"][len("Document ID : "):]
    _document_db_id = int(_document_db_id)
    # Get Document and the topics
    # Topics distr
    _pd_index = clickData["points"][0]["pointIndex"]
    _dt_pd_distr = document_topics.iloc[_pd_index, :].values
    _dt_pd_distr = [[f"Topic {ix} : Weight {x} ", html.Br()] for ix, x in enumerate(_dt_pd_distr)]

    _dt_pd_distr = [y for x in _dt_pd_distr for y in x]
    return [html.Div(_dt_pd_distr), html.Br(), html.Br(), html.Br(), html.H3("The full document content"),
            html.Span(_document_db_id)]


#### End of Callbacks ###############################################################################

# barchart
All_topics = dcc.Graph(
    id='topic_model-graph',
)

# Scatterplot
document_projection_plot = dcc.Graph(
    id='topic_projection',
)


def update_point(trace, points, selector):
    print("test")


title_bar = html.Div(
    children=[html.H1(children='LDA Topic Models by TK', style={
        'textAlign': 'center',
        'color': "white",
        'width': "100%",
        'font-weight': 'bolder'
    })
              ],
    style={
        "width": "100%",
        "backgroundColor": "#2ba287",
        "height": "130px",
        "padding-top": "30px"
    }
)

left_div = html.Div(
    children=[
        html.H4(children="Topics Selection:",
                style={"textAlign": "left", 'color': colors['text'], "font-weight": "bold"}),
        topic_selector,
        All_topics],
    className='col s12 m6',
    style={"width": "49%", "float": "left", "overflow": "auto", "border": "1px dotted green"}
)

right_div_plot = html.Div(
    id="right_div_1_plot",
    children=[document_projection_plot])
right_div_print = html.Div(
    id="right_div_1_print",
    children=[html.H3("Document topics:"), html.Div(id="document_contents", children="Please select Document First")])

right_div = html.Div(
    id="right_div_1",
    children=[html.H4(children="Documents Projection:",
                      style={"textAlign": "left", 'color': colors['text'],
                             "font-weight": "bold"}),
              selector_div,
              right_div_plot,
              right_div_print]
    ,
    className='col s12 m6',
    style={"width": "49%", "float": "right", "border": "1px green dotted"}
)

app.layout = html.Div(children=[
    title_bar,

    html.Div(children='''
        Visualisation of LDA results.
    '''),

    # Start the left right mode
    html.Div(className='row',
             style={"width": "100%", 'display': 'inline-block',
                    "margin": "auto", "overflow": "auto",
                    "backgroundColor": colors["background"], "padding": "0"},
             children=[left_div, right_div]),
    html.Div(className='row',
             style={"width": "100%", 'display': 'inline-block',
                    "margin": "auto", "overflow": "auto",
                    "backgroundColor": colors["background"], "padding": "0"},
             children=["Bugabuga"])
],
    style={'backgroundColor': colors['background'], "height": "800px"}
)

if __name__ == '__main__':
    app.run_server(debug=True)
