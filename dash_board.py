import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px

from sklearn.decomposition import PCA
from data_loader import preprocess_data
import plotly.graph_objs as go

# Styles
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
colors = {
    'background': '#ffffff',
    'text': '#4f5250'
}

# End styles #####################################################################
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


def prep_data_viz():
    all_topics, document_topics = preprocess_data(db=False)
    document_topics = pd.DataFrame(document_topics).transpose()
    all_topics = pd.DataFrame.from_dict(all_topics)
    n_topics = len(all_topics.columns)
    topics_flat = get_flat_topic_df(all_topics, n_topics)
    return topics_flat, document_topics


def convertTupleStr(tup):
    return '<br>'.join(map(str, tup))


print(convertTupleStr((1, 2, 3, 4)))


def get_flat_topic_df(all_topics, n_topics):
    """
    Get df with Multiindex to plot easier
    :param all_topics: the IDs of the topics as list
    :param n_topics: the number of topics in the model
    :return: df with index [TopicID, Word] and weight
    """
    init_topic = all_topics.columns[0]
    # TODO refator due duplication.
    topics_flat = all_topics[[init_topic]].copy().dropna(axis=0)
    topics_flat.index.rename("Word", inplace=True)
    topics_flat.columns = ["weight"]
    topics_flat["TopicID"] = init_topic
    topics_flat.set_index("TopicID", inplace=True, append=True)  # ADD the index
    topics_flat = topics_flat.reorder_levels(["TopicID", "Word"])
    for init_topic in all_topics.columns[1:]:
        tf = all_topics[[init_topic]].copy().dropna(axis=0)
        tf.index.rename("Word", inplace=True)
        tf.columns = ["weight"]
        tf["TopicID"] = init_topic
        tf.set_index("TopicID", inplace=True, append=True)  # ADD the index
        tf = tf.reorder_levels(["TopicID", "Word"])
        topics_flat = pd.concat([topics_flat, tf], axis=0)
    topics_flat = pd.concat(
        [topics_flat.
             iloc[topics_flat.index.get_level_values("TopicID") == x, :]
             .copy().sort_values(by="weight", ascending=False) for x in range(n_topics)],
        axis=0)

    return topics_flat


flat_data, document_topics = prep_data_viz()
iw = flat_data.index.get_level_values("Word").values.tolist()
it = flat_data.index.get_level_values("TopicID").values.tolist()
pca_ = PCA(n_components=len(set(it)))
document_projections = pd.DataFrame(pca_.fit_transform(document_topics), index=document_topics.index.copy())

kelly_colors = [(255, 179, 0),
                (128, 62, 117),
                (255, 104, 0),
                (166, 189, 215),
                (193, 0, 32),
                (206, 162, 98),
                (129, 112, 102),
                (0, 125, 52),
                (246, 118, 142),
                (0, 83, 138),
                (255, 122, 92),
                (83, 55, 122),
                (255, 142, 0),
                (179, 40, 81),
                (244, 200, 0),
                (127, 24, 13),
                (147, 170, 0),
                (89, 51, 21),
                (241, 58, 19),
                (35, 44, 22)
                ]

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


@app.callback(
    dash.dependencies.Output('right_div_1', 'children'),
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
            'closest' : "closest",
            "height": "750",
            "width@": "100%",
            'title': f"Projection on topics {1}, {2}",
        }
    }
    f = go.FigureWidget(px.scatter_3d(document_projections, x = 1, y = 2, z = 3, hover_name = 'company_nm'))

    f.layout.clickmode = 'event+select'
    f.data[0].on_click(update_point) # if click, then update point/df.
    return  f


#

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

right_div = html.Div(
    id="right_div_1",
    children=[html.H4(children="Documents Projection:",
                      style={"textAlign": "left", 'color': colors['text'],
                             "font-weight": "bold"}), selector_div, document_projection_plot
              ],
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
             children=[left_div, right_div])
],
    style={'backgroundColor': colors['background'], "height": "800px"}
)

if __name__ == '__main__':
    app.run_server(debug=True)
