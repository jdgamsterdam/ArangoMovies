from dash import html, dcc
import dash_daq as daq
import dash_cytoscape as cyto
import dash_bootstrap_components as dbc
import json


# This function must receive all dynamic values as parameters.
def movies_layout(
    app,
    person1nconst,
    person1Name,
    person2nconst,
    person2Name,
    myinitialtable,
    dropdownelements,
    initial_dropdownelement,
    initial_graph_elements,
    initial_layout_type,
    initial_title_node_shape,
    initial_name_node_shape,
    all_layout_types,
    all_node_shapes,
    initial_total_nodes,
    initial_clusters_on_page,
    maxnodespergraph,
    initial_final_page,
    initial_max_pages,
    default_inline,
    cyto_style,
    get_cytoscape_layout,
    get_cytoscape_stylesheet,
):
    return html.Div(
        className="app-shell",
        children=[
            dbc.Modal(
                id="jobs-modal",
                is_open=False,
                className="modal-lg modern-modal",
                children=[
                    dbc.ModalHeader(
                        id="jobs-modal-header",
                        className="modal-jobs-header",
                        children=[dbc.ModalTitle("Header")],
                    ),
                    dbc.ModalBody(
                        id="modal-jobs-body-total",
                        className="modal-jobs-body-total",
                        children=[html.Div("Where Table Goes")],
                    ),
                    dbc.ModalFooter(
                        dbc.Button("Close", id="jobsclose", className="ms-auto", n_clicks=0)
                    ),
                ],
            ),
            dbc.Modal(
                id="alt-modal",
                is_open=False,
                className="modal-sm modern-modal",
                children=[
                    dbc.ModalHeader(
                        id="alt-modal-header",
                        className="alt-modal-header",
                        children=[dbc.ModalTitle("Header")],
                    ),
                    dbc.ModalBody(
                        id="alt-modal-body-total",
                        className="alt-modal-body-total logo-link-stack",
                        children=[
                            html.A(
                                children=html.Img(
                                    src=app.get_asset_url("IMDB_Logo_2016.svg"),
                                    className="imdb-image-style",
                                ),
                                id="alt-modal-body-imdb",
                                href="https://imdb.com",
                                target="_blank",
                            ),
                            html.A(
                                children=html.Img(
                                    src=app.get_asset_url("Wikipedia_logo.svg"),
                                    className="wiki-image-style",
                                ),
                                id="alt-modal-body-wiki",
                                href="https://wikipedia.com",
                                target="_blank",
                            ),
                        ],
                    ),
                    dbc.ModalFooter(
                        dbc.Button("Close", id="altclose", className="ms-auto", n_clicks=0)
                    ),
                ],
            ),

            html.Div(id="alt-key-state", children="false", style={"display": "none"}),
            dcc.Store(id="edge-store", data={"id": "MyID", "label": "MyLabel"}),
            dcc.Store(
                id="selected-node-store",
                data={"id": f"name_basics/{person1nconst}", "label": person1Name},
            ),
            dcc.Store(id="alt-click-store", data={"armed": False, "ts": 0}),
            dcc.Store(
                id="six-degrees-array",
                data={"id": f"name_basics/{person1nconst}", "label": person1Name},
            ),

            html.Header(
                className="hero",
                children=[
                    html.Div(className="eyebrow", children="Movie network explorer"),
                    html.Div(className="my-title", children="Six Degrees of Kevin Bacon"),
                    html.P(
                        className="hero-copy",
                        children="Search people, choose start and end nodes, then explore how films and shows connect them.",
                    ),
                ],
            ),

            html.Main(
                className="dashboard-grid",
                children=[
                    html.Section(
                        className="card search-card",
                        children=[
                            html.Div(className="section-kicker", children="01 · Search"),
                            html.Div(className="field-name", children="Find a person by full or partial name"),
                            html.Div(
                                className="radio-with-description",
                                children=[
                                    dcc.RadioItems(
                                        [
                                            {"label": "Like Query", "value": "likequery"},
                                            {"label": "Levenshtein Distance", "value": "levenshtein"},
                                        ],
                                        "levenshtein",
                                        id="namesearchquerytype",
                                        inline=True,
                                    ),
                                    html.Span(
                                        className="description",
                                        children="Query Description",
                                        id="querydescription",
                                    ),
                                ],
                            ),
                            html.Div(
                                id="selection-table",
                                className="selection-table field-with-search-button",
                                children=[
                                    dcc.Input(
                                        id="persontofind",
                                        type="text",
                                        className="search-input",
                                        value=person1Name,
                                        placeholder="Type a name…",
                                    ),
                                    html.Button("Find Person", id="Find-Person", n_clicks=0, className="primary-button"),
                                    html.Div("Enter a value and press submit", className="helper-text"),
                                ],
                            ),
                            html.Div(
                                className="dropdown-with-description",
                                children=[
                                    dcc.Dropdown(
                                        id="person-dropdown-1",
                                        options=dropdownelements,
                                        value=initial_dropdownelement,
                                        className="wide-dropdown",
                                    ),
                                    html.Div(
                                        id="container-add-person",
                                        className="selected-json",
                                        children=json.dumps(
                                            {"id": f"name_basics/{person1nconst}", "label": person1Name}
                                        ),
                                    ),
                                ],
                            ),
                            html.Div(
                                id="cytorow_selection",
                                style={"width": "100%"},
                                className="add-nodes",
                                children=[
                                    html.P("Add selected person (From Table to the Right) as a graph node", className="helper-text"),
                                    html.Button("Set as Start Node", id="submit-person1", n_clicks=0, className="secondary-button"),
                                    html.Button("Set as End Node", id="submit-person2", n_clicks=0, className="secondary-button"),
                                ],
                            ),
                        ],
                    ),

                    html.Section(
                        className="card results-card",
                        children=[
                            html.Div(className="section-kicker", children="02 · Results"),
                            html.Div(
                                className="node-table",
                                id="name_search_dashtable",
                                children=[myinitialtable],
                            ),
                        ],
                    ),

                    html.Section(
                        className="card relationship-card",
                        children=[
                            html.Div(className="section-kicker", children="03 · Relationship"),
                            html.Div(
                                id="realtionship-table",
                                className="selected-node-table relationship-grid",
                                children=[
                                    html.Div(
                                        className="node-summary",
                                        children=[
                                            html.P("Start Node"),
                                            html.Div(person1Name, id="person1name", className="node-name"),
                                            html.Div(person1nconst, id="person1nconst", className="node-id"),
                                        ],
                                    ),
                                    html.Div(
                                        className="node-summary",
                                        children=[
                                            html.P("End Node"),
                                            html.Div(person2Name, id="person2name", className="node-name"),
                                            html.Div(person2nconst, id="person2nconst", className="node-id"),
                                        ],
                                    ),
                                    html.Div(
                                        className="relationship-result",
                                        children=[
                                            html.Div(
                                                "The relationship between these two people is:",
                                                id="person-relationship-text",
                                                className="relationship-label",
                                            ),
                                            html.Div(
                                                id="relationship_dashtable",
                                                className="table-as-numbered-list",
                                                children=[html.P("List as Table")],
                                            ),
                                            html.Button(
                                                "Show Relationship",
                                                id="show-relationship",
                                                n_clicks=0,
                                                className="primary-button",
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),

                    html.Section(
                        id="SelectLayoutColors",
                        className="card settings-card color-layout-settings",
                        children=[
                            html.Div(className="section-kicker", children="04 · Graph settings"),
                            html.Div(
                                className="picker-grid",
                                children=[
                                    daq.ColorPicker(
                                        id="title-node-color-picker",
                                        label="Title Node Color",
                                        value=dict(hex="#2563EB"),
                                        style=default_inline,
                                    ),
                                    daq.ColorPicker(
                                        id="name-node-color-picker",
                                        label="Name Node Color",
                                        value=dict(hex="#14B8A6"),
                                        style=default_inline,
                                    ),
                                    daq.ColorPicker(
                                        id="edge-color-picker",
                                        label="Edge Color",
                                        value=dict(hex="#F97316"),
                                        style=default_inline,
                                    ),
                                ],
                            ),
                            html.Div(
                                id="SelectLayoutTypes",
                                className="graphtype-layout-settings settings-panel",
                                children=[
                                    html.Div("Node and edge shapes", className="dropdown-title panel-title"),
                                    html.Div([
                                        html.Span("Graph display type", className="dropdown-title"),
                                        dcc.Dropdown(all_layout_types, initial_layout_type, id="layout_type"),
                                    ]),
                                    html.Div([
                                        html.Span("Title Node Shape", className="dropdown-title"),
                                        dcc.Dropdown(all_node_shapes, initial_title_node_shape, id="title_node_shape"),
                                    ]),
                                    html.Div([
                                        html.Span("Name Node Shape", className="dropdown-title"),
                                        dcc.Dropdown(all_node_shapes, initial_name_node_shape, id="name_node_shape"),
                                    ]),
                                ],
                            ),
                            html.Div(
                                id="cyto_cluster_settings",
                                className="cluster-settings settings-panel",
                                children=[
                                    html.Div([
                                        html.Span("Total Connected Nodes  (Note: Note Working at Present)", className="dropdown-title"),
                                        html.Div(id="total-return-nodes", children=initial_total_nodes, className="metric-value"),
                                    ]),
                                    html.Div([
                                        html.Span("Clusters", className="dropdown-title"),
                                        dcc.Input(
                                            className="cluster-input",
                                            id="clusters-on-page",
                                            type="number",
                                            value=initial_clusters_on_page,
                                            min=1,
                                            max=25,
                                            step=1,
                                        ),
                                    ]),
                                    html.Div([
                                        html.Span("Nodes on Page", className="dropdown-title"),
                                        dcc.Input(
                                            className="cluster-input",
                                            id="nodes-on-page",
                                            type="number",
                                            value=maxnodespergraph,
                                            min=1,
                                            max=25,
                                            step=1,
                                        ),
                                    ]),
                                    html.Div([
                                        html.Span("Current Page Number", className="dropdown-title"),
                                        dcc.Input(
                                            className="cluster-input",
                                            id="page-number",
                                            type="number",
                                            value=initial_final_page,
                                            min=1,
                                            max=initial_max_pages,
                                            step=1,
                                        ),
                                    ]),
                                ],
                            ),
                            html.Div(
                                id="update_graph_button",
                                className="update-button settings-panel",
                                children=[
                                    html.Div(
                                        className="button-row",
                                        children=[
                                            html.Button("Six Degrees Table", id="update-graph-to-table", n_clicks=0, className="secondary-button"),
                                            html.Button("Current Selection as Center Node", id="update-graph-to-node", n_clicks=0, className="secondary-button"),
                                        ],
                                    ),
                                    html.Div(id="current-node-1", children=person1nconst, className="node-id current-node-id"),
                                ],
                            ),
                        ],
                    ),

                    html.Section(
                        className="card instruction-card click-instruction",
                        children=[
                            html.Div(className="section-kicker", children="How to explore"),
                            html.Div("Pause Ad-Blocker to See Details Box"),
                            html.Div("Left-click a node to expand its connections"),
                            html.Div("Hold Alt and left-click a node for more details on a person or show. NOTE: This is a bit finicky so you my need to restart to get it to work."),
                            html.Div("Click an edge to see that person’s roles/jobs in the show or movie"),
                        ],
                    ),

                    html.Section(
                        id="cytorow",
                        className="graph-card card",
                        children=[
                            cyto.Cytoscape(
                                id="cytoscape1",
                                elements=initial_graph_elements,
                                layout=get_cytoscape_layout(initial_layout_type),
                                style=cyto_style,
                                stylesheet=get_cytoscape_stylesheet(
                                    {"hex": "#2563EB"},
                                    {"hex": "#14B8A6"},
                                    {"hex": "#F97316"},
                                    initial_title_node_shape,
                                    initial_name_node_shape,
                                ),
                            )
                        ],
                    ),
                ],
            ),
        ],
    )
