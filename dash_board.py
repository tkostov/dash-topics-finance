import bs4 as bs
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go

from data_loader import postprocess_data, get_document_text


# Def parser
def convert_html_to_dash(el, style=None):
    CST_PERMITIDOS = {'div', 'span', 'a', 'hr', 'br', 'p', 'b', 'i', 'u', 's', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ol',
                      'ul', 'li',
                      'em', 'strong', 'cite', 'tt', 'pre', 'small', 'big', 'center', 'blockquote', 'address', 'font',
                      'img',
                      'table', 'tr', 'td', 'caption', 'th', 'textarea', 'option'}

    def __extract_style(el):
        if not el.attrs.get("style"):
            return None
        return {k.strip(): v.strip() for k, v in [x.split(": ") for x in el.attrs["style"].split(";")]}

    if type(el) is str:
        return convert_html_to_dash(bs.BeautifulSoup(el, 'html.parser'))
    if type(el) == bs.element.NavigableString:
        return str(el)
    else:
        name = el.name
        style = __extract_style(el) if style is None else style
        contents = [convert_html_to_dash(x) for x in el.contents]
        if name.title().lower() not in CST_PERMITIDOS:
            return contents[0] if len(contents) == 1 else html.Div(contents)
        return getattr(html, name.title())(contents, style=style)


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
            'title': f"Projection on PCs {axis1}, {axis2}",
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
                        hovertext=[f"Topic Id {iw_[i]} | {it_[i]}" for i in range(len(iw_))],
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
    _dt_pd_distr = [[f"Topic {ix}", x] for ix, x in enumerate(_dt_pd_distr)]
    _dt_pd_distr = pd.DataFrame(_dt_pd_distr, columns=["TID", "Weight"])

    important_topics = _dt_pd_distr.sort_values(by="Weight", axis=0, ascending=False).head(2).TID.apply(
        lambda x: int(x[len("Topic "):])).values
    important_topics_weights = _dt_pd_distr.Weight.values[important_topics] / _dt_pd_distr.Weight.values[
        important_topics].sum()

    distr_chart = dcc.Graph(id='PerDocDistrChart',
                            figure={'data': [
                                {'x': _dt_pd_distr["TID"].values,
                                 'y': _dt_pd_distr.Weight.values,
                                 'type': 'bar', 'name': 'Topic Distribution'}],
                                'layout': {
                                    'title': 'Topic Distribution for document {}'.format(str(_document_db_id))
                                }
                            }
                            )
    fl = flat_data.copy().iloc[flat_data.index.get_level_values("TopicID").isin(important_topics), :]
    fl.iloc[fl.index.get_level_values("TopicID") == important_topics[0], :] *= important_topics_weights[0]
    fl.iloc[fl.index.get_level_values("TopicID") == important_topics[1], :] *= important_topics_weights[1]
    iw_ = fl.index.get_level_values("TopicID")
    it_ = fl.index.get_level_values("Word").values.tolist()

    f = {
        'data': [go.Bar(y=fl["weight"].values.tolist(),
                        x=[f"{it_[i]} : {iw_[i]}" for i in range(len(iw_))],
                        marker_color=["rgb" + str(kelly_colors[x]) for ix, x in enumerate(iw_)],
                        hovertext=[f"Topic Id {iw_[i]} | {it_[i]}" for i in range(len(iw_))],
                        orientation='v')],
        'layout': {
            'title': f'Word Distribution document {_document_db_id} | Top 2 topics scaled by topic weight',
            "width@": "100%"
        }}
    word_distr_chart = dcc.Graph(id='PerDocDistrChart',
                                 figure=f)
    doc_text = get_document_text(_document_db_id).replace("\n", "<br>")
    print(important_topics)
    return [html.Div(children=[distr_chart]), word_distr_chart, html.Br(), html.Br(), html.Br(),
            html.H3("The full document content"),
            # TODO here
            html.Span(convert_html_to_dash(doc_text))]


#### End of Callbacks ###############################################################################

# barchart
All_topics = dcc.Graph(
    id='topic_model-graph',
)

# Scatterplot
document_projection_plot = dcc.Graph(
    id='topic_projection',
)

topic_viz_plot = dcc.Graph(id="TopicSizeRel", figure={
    'data': [
        {
            'x': topics_vis["pc1"].values,
            'y': topics_vis["pc2"].values,
            "text": [
                f"{topics_vis['Salient Word'].values[ix][0]}"
                for ix in range(len(topics_vis["Salient Word"].values))],
            'mode': 'markers+text',
            'size': topics_vis["overall weight"].values,
            'marker': {'size': topics_vis["overall weight"].values * 1,
                       'sizemode': 'area',
                       'sizeref': 2. * max(topics_vis["overall weight"].values) / (40. ** 2),
                       'sizemin': 4
                       },
            "textposition": "bottom center"
        }
    ],
    'layout': {
        'clickmode': 'event+select',
        'closest': "closest",
        "height": "750",
        "width@": "100%",
        'title': f"Projection on PCs",
    }
}
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
             children=[topic_viz_plot])
],
    style={'backgroundColor': colors['background'], "height": "800px"}
)

if __name__ == '__main__':
    app.run_server(debug=False, host="0.0.0.0", port="8050")
