import copy
import json
import math
import os
import re
import time
import bs4 as bs
import dash_bootstrap_components as dbc
import pandas as pd

from typing import Any, Dict, List, Optional, Tuple

from arango import ArangoClient
from dash import Input, Output, State, ctx, dash_table, html, no_update
from dash.exceptions import PreventUpdate
from dash_extensions.enrich import DashProxy, MultiplexerTransform
from dotenv import load_dotenv

#from cyto_config import (cyto_layout,cyto_style,cyto_stylesheet,default_inline)

from cyto_config_modern import (
    cyto_layout,
    cyto_style,
    cyto_stylesheet,
    default_inline
)

#from movies_arango_layout import movies_layout
from movies_arango_layout_modern import movies_layout

load_dotenv("./setup/arango.env")

# ---------- Initial Text / Defaults ----------
num_items_array=[0,1,2,3]

person1Name = "Kevin Bacon"
person1nconst = "nm4025714"

person2Name = "Sissy Spacek"
person2nconst = "nm0000651"

maxnodespergraph = 4
initial_clusters_on_page = 2
initial_page_number = 1

all_layout_types = ["random", "grid", "circle", "concentric", "breadthfirst", "cose"]
initial_layout_type = "breadthfirst"
all_node_shapes = [
    "barrel", "bottom-round-rectangle",  "bottomroundrectangle",
    "concave-hexagon", "concavehexagon", "cut-rectangle", "cutrectangle",
    "diamond",  "ellipse", "heptagon", "hexagon",
    "octagon", "pentagon", "polygon", 
    "rectangle", "rhomboid", "right-rhomboid", "round-diamond", "round-heptagon", "round-hexagon", "round-octagon", "round-pentagon", "round-rectangle", "round-tag",  "round-triangle",
    "square", "star", "tag", "triangle", "vee"
]

initial_title_node_shape = "ellipse"
initial_name_node_shape = "square"


# ---------- General Utility Functions ----------

def return_document_as_list(text: Any) -> html.Ul:
    if not isinstance(text, str):
        text = str(text)

    lines = [line.strip() for line in text.split("<br>") if line.strip()]
    output = []

    for line in lines:
        parts = []
        pos = 0

        for match in re.finditer(r"<i>(.*?)</i>", line):
            start, end = match.span()
            italic_text = match.group(1)

            if start > pos:
                parts.append(html.Span(line[pos:start]))

            parts.append(html.I(italic_text))
            pos = end

        if pos < len(line):
            parts.append(html.Span(line[pos:]))

        output.append(html.Li(parts, style={"marginBottom": "6px"}))

    return html.Ol(output, style={"paddingLeft": "20px"})

def convert_html_to_dash(el: Any, style: Optional[Dict[str, str]] = None):
    tags_permitted = {
        "div", "span", "a", "hr", "br", "p", "b", "i", "u", "s", "h1", "h2", "h3",
        "h4", "h5", "h6", "ol", "ul", "li", "em", "strong", "cite", "tt", "pre", "small",
        "big", "center", "blockquote", "address", "font", "img", "table", "tr", "td",
        "caption", "th", "textarea", "option"
    }

    def _extract_style(tag):
        if not tag.attrs.get("style"):
            return None
        style_dict = {}
        for item in tag.attrs["style"].split(";"):
            if ":" in item:
                key, value = item.split(":", 1)
                style_dict[key.strip()] = value.strip()
        return style_dict or None

    if isinstance(el, str):
        return convert_html_to_dash(bs.BeautifulSoup(el, "html.parser"))

    if isinstance(el, bs.element.NavigableString):
        return str(el)

    name = el.name
    style = _extract_style(el) if style is None else style
    contents = [convert_html_to_dash(x) for x in el.contents]

    if name.lower() not in tags_permitted:
        return contents[0] if len(contents) == 1 else html.Div(contents)

    return getattr(html, name.title())(contents, style=style)

def get_query(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file:
        return file.read()

def safe_max_pages(total_nodes: int, nodes_per_page: int) -> int:
    if nodes_per_page <= 0:
        return 1
    return max(1, math.ceil(total_nodes / nodes_per_page))

def dedupe_elements(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    unique_elements = []

    for element in elements:
        data = element.get("data", {})
        if "id" in data:
            key = ("node", data["id"])
        else:
            key = (
                "edge",
                data.get("source"),
                data.get("target"),
                data.get("label", ""),
            )

        if key not in seen:
            seen.add(key)
            unique_elements.append(element)

    return unique_elements

def normalize_color_value(value: Optional[Dict[str, str]], fallback: str = "#119DFF") -> str:
    if isinstance(value, dict) and value.get("hex"):
        return value["hex"]
    return fallback

def normalize_shape_value(value: Optional[str], fallback: str) -> str:
    return value if value else fallback

def parse_clicked_node_from_table_json(value: Optional[str]) -> Tuple[str, str]:
    if not value:
        return person1nconst, person1Name

    payload = json.loads(value)
    raw_id = payload["id"]
    label = payload.get("label", "")

    if "/" in raw_id:
        node_id = raw_id.split("/", 1)[1]
    else:
        node_id = raw_id

    return node_id, label

def extract_edge_ids(edge):
    """
    Extracts the tconst and nconst from a JSON edge object.
    Example:
      source: "title_basics/tt6293610" → tconst = "tt6293610"
      target: "name_basics/nm0491697"  → nconst = "nm0491697"
    """
    source_val = edge.get("source", "")
    target_val = edge.get("target", "")

    tconst = source_val.split("/")[-1] if source_val else None
    primaryTitle = edge.get("primaryTitle", "")
    nconst = target_val.split("/")[-1] if target_val else None
    primaryName = edge.get("primaryName", "")

    return tconst, primaryTitle, nconst, primaryName

def principals_to_table(records):
    """
    Convert a list of title_principals records into a table containing
    Category, Job, Characters.
    """
    table = []

    for rec in records:
        table.append({
            "Category": rec.get("category", ""),
            "Job": rec.get("job", ""),
            "Characters": rec.get("characters", "")
        })

    return table



#Helper Function for Node Creation
def compute_center_graph_output(
    selected_node,
    layout_type,
    title_color,
    name_color,
    edge_color,
    title_shape,
    name_shape,
    nodes_on_page,
    clusters_on_page,
    page_number,
):
    raw_id = selected_node.get("id", "")
    label = selected_node.get("label", "Unknown")

    center_id = raw_id.split("/", 1)[1] if "/" in raw_id else raw_id

    requested_page = max(1, int(page_number or 1))
    nodes_on_page = max(1, int(nodes_on_page or maxnodespergraph))
    clusters_on_page = max(1, int(clusters_on_page or 1))

    elements, total_nodes, max_pages, final_page = build_graph_for_center(
        center_id=center_id,
        center_label=label,
        page_number=requested_page,
        nodes_per_page=nodes_on_page,
        cluster_depth=clusters_on_page,
    )

    return (
        elements,
        get_cytoscape_layout(layout_type or initial_layout_type),
        get_cytoscape_stylesheet(title_color, name_color, edge_color, title_shape, name_shape),
        total_nodes,
        max_pages,
        final_page,
    )



# ---------- Database Connection ----------

FullHost = "http://" + os.getenv("ARANGO_SERVER") + ":8529"

client = ArangoClient(hosts=FullHost, request_timeout=100)
db = client.db(
    os.getenv("MOVIES_DATABASE_NAME"),
    username=os.getenv("MOVIES_DATABASE_USERNAME"),
    password=os.getenv("MOVIES_PASSWORD"),
)

MoviesPersonsQuery = get_query("./MoviesPersonsQuery_lev.aql")
JobsForEdgeClick = get_query("./jobs_for_edge_click.aql")
PersonRelationshipQuery = get_query("./PersonRelationshipQuery_Direct.aql")
PersonRelationshipQuery_As_Nodes = get_query("./PersonRelationshipQuery_As_Nodes.aql")
NodesForPersonAtCenterForCyto = get_query("./NodesForPersonAtCenterForCyto_Direct.aql")
EdgesForPersonAtCenterForCyto = get_query("./EdgesForPersonAtCenterForCyto_Direct.aql")
TotalNodesForPersonAtCenterForCyto = get_query("./TotalNodesForPersonAtCenterForCyto_Direct.aql")
CheckIfNodeIsEpisode = get_query("./CheckIfNodeIsEpisode.aql")
GetEpisodeParent = get_query("./GetEpisodeParent.aql")


def run_query(query_text: str, bind_vars: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    bind_vars = bind_vars or {}
    cursor = db.aql.execute(query_text, bind_vars=bind_vars, batch_size=1)
    return [doc for doc in cursor]

def get_text_results_for_name(movie_person_name: Optional[str]) -> List[Dict[str, Any]]:
    if movie_person_name is None:
        movie_person_name = person1Name
    return run_query(MoviesPersonsQuery, {"myname": movie_person_name})

def get_related_episodes(tconst: str) -> List[Dict[str, Any]]:
    return run_query(CheckIfNodeIsEpisode, {"tconst": tconst})

def get_episode_parent(tconst: str) -> List[Dict[str, Any]]:
    return run_query(GetEpisodeParent, {"tconst": tconst})

def get_relationships(nconst1: str, nconst2: str) -> List[Dict[str, Any]]:
    return run_query(PersonRelationshipQuery, {"nconst1": nconst1, "nconst2": nconst2})

def get_relationships_nodes(nconst1: str, nconst2: str) -> List[Dict[str, Any]]:
    return run_query(PersonRelationshipQuery_As_Nodes, {"nconst1": nconst1, "nconst2": nconst2})

def get_edge_jobs(nconst: str, tconst: str) -> List[Dict[str, Any]]:

    return run_query(JobsForEdgeClick, {"nconst": nconst, "tconst": tconst})    


#Process Returned Data 

def get_node_collection_prefix(node_id: str) -> str:
    return "name_basics" if node_id.startswith("nm") else "title_basics"

def build_center_node(node_id: str, label: str) -> Dict[str, Dict[str, str]]:
    return {"data": {"id": f"{get_node_collection_prefix(node_id)}/{node_id}", "label": label}}

def convert_kpaths_to_elements(paths):
    nodes = {}
    edges = []

    for path in paths:
        for v in path.get("vertices", []):
            vid = v["_id"]
            label = v.get("primaryName") or v.get("primaryTitle") or vid
            nodes[vid] = {"data": {"id": vid, "label": label}}

        for e in path.get("edges", []):
            edges.append({
                "data": {
                    "source": e["_from"],
                    "target": e["_to"],
                    "label": e.get("label", ""),
                    "primaryName": e.get("primaryName", ""),
                    "primaryTitle": e.get("primaryTitle", "")
                }
            })

    return list(nodes.values()) + edges


def build_graph_for_center(
    center_id: str,
    center_label: str,
    page_number: int,
    nodes_per_page: int,
    cluster_depth: int,
    ) -> Tuple[List[Dict[str, Any]], int, int, int]:
        nodes_per_page = max(1, int(nodes_per_page or 1))
        requested_page = max(1, int(page_number or 1))
        cluster_depth = max(1, int(cluster_depth or 1))

        total_node_query_bind_vars = {"nconst": center_id}
        total_return_nodes_json = run_query(TotalNodesForPersonAtCenterForCyto, total_node_query_bind_vars)
        total_return_nodes = total_return_nodes_json[0]["nodecount"] if total_return_nodes_json else 0

        max_pages = safe_max_pages(total_return_nodes, nodes_per_page)
        final_page = min(requested_page, max_pages)
        offset = (final_page - 1) * nodes_per_page

        all_nodes: List[Dict[str, Any]] = [build_center_node(center_id, center_label)]
        all_edges: List[Dict[str, Any]] = []
        frontier_ids = [center_id]

        for _depth in range(cluster_depth):
            frontier_csv = ",".join(frontier_ids)
            if not frontier_csv:
                break

            node_query_bind_vars = {
                "nconst": frontier_csv,
                "myoffset": offset,
                "mycount": nodes_per_page,
            }
            edge_query_bind_vars = {
                "nconst": frontier_csv,
                "myoffset": offset,
                "mycount": nodes_per_page,
            }

            level_nodes = run_query(NodesForPersonAtCenterForCyto, node_query_bind_vars)
            level_edges = run_query(EdgesForPersonAtCenterForCyto, edge_query_bind_vars)

            all_nodes.extend(level_nodes)
            all_edges.extend(level_edges)

            next_frontier = []
            for node in level_nodes:
                raw_id = node.get("data", {}).get("id", "")
                if "/" in raw_id:
                    next_frontier.append(raw_id.split("/", 1)[1])

            frontier_ids = next_frontier
            if not frontier_ids:
                break




        elements = dedupe_elements(all_edges + all_nodes)
        return elements, total_return_nodes, max_pages, final_page

def build_graph_for_six_degrees(
    center_id: str,
    center_label: str,
    page_number: int,
    nodes_per_page: int,
    cluster_depth: int,
    n1: str,
    n2: str
):

    # Run the 6-degree K_PATHS query
    paths = run_query(
        PersonRelationshipQuery_As_Nodes,
        {"nconst1": n1, "nconst2": n2},
    )

    elements = convert_kpaths_to_elements(paths)

    # For six-degrees, just return the full graph
    total_nodes = len(elements)
    max_pages = 1
    final_page = 1

    #Clean Up Duplicate Elements
    elements = dedupe_elements(elements)


    #Check if Node Is Episode
    for elem in elements:
        data = elem.get("data", {})

        # Only process title nodes
        node_id = data.get("id")
        if node_id and node_id.startswith("title_basics/"):

            tconst = node_id.split("/")[-1]

            # myepisodes is a list of dicts
            myepisodes = get_related_episodes(tconst)


            if myepisodes:   # same as len(myepisodes) != 0
                episode_info = myepisodes[0]
                parentTconst = episode_info["parentTconst"]

                myParentShow = get_episode_parent(tconst)
                parent_info = myParentShow[0]
                parentPrimaryTitle = parent_info["primaryTitle"]

                
                # -----------------------------
                # 1. Modify existing node label
                # -----------------------------
                old_label = data.get("label", "")
                data["label"] = f"{old_label} (EPISODE)"

                # -----------------------------
                # 2. Add NEW parent node
                # -----------------------------
                parent_node = {
                    "data": {
                        "id": f"title_basics/{parentTconst}",
                        "label": parentPrimaryTitle   # Parent Show Title
                    }
                }
                elements.append(parent_node)

                # -----------------------------
                # 3. Add NEW edge to parent
                # -----------------------------
                parent_edge = {
                    "data": {
                        "source": f"title_basics/{tconst}",
                        "target": f"title_basics/{parentTconst}",
                        "label": "SERIES"
                    }
                }
                elements.append(parent_edge)



    return elements, total_nodes, max_pages, final_page



def get_selected_label_from_options(value: str, options: List[Dict[str, Any]]) -> str:
    for element in options or []:
        if element.get("value") == value:
            return element.get("label", value)
    return value

def get_cytoscape_layout(layout_name: str) -> Dict[str, Any]:
    layout = copy.deepcopy(cyto_layout)
    layout["name"] = layout_name
    return layout

def get_cytoscape_stylesheet(
    title_color: Optional[Dict[str, str]],
    name_color: Optional[Dict[str, str]],
    edge_color: Optional[Dict[str, str]],
    title_shape: Optional[str],
    name_shape: Optional[str],
) -> List[Dict[str, Any]]:
    stylesheet = copy.deepcopy(cyto_stylesheet)

    stylesheet[2]["style"]["background-color"] = normalize_color_value(title_color)
    stylesheet[2]["style"]["shape"] = normalize_shape_value(title_shape, initial_title_node_shape)

    stylesheet[3]["style"]["background-color"] = normalize_color_value(name_color)
    stylesheet[3]["style"]["shape"] = normalize_shape_value(name_shape, initial_name_node_shape)

    stylesheet[1]["style"]["line-color"] = normalize_color_value(edge_color)

    return stylesheet

# ---------- Initial Graph / Data ----------

baseresults = get_text_results_for_name(person1Name)
dropdownelements = [
    {"label": f"{doc['primaryName']}-{doc['nconst']}", "value": doc["nconst"]}
    for doc in baseresults
]
initial_dropdownelement = dropdownelements[0]["value"] if dropdownelements else None

initial_graph_elements, initial_total_nodes, initial_max_pages, initial_final_page = build_graph_for_center(
    center_id=person1nconst,
    center_label=person1Name,
    page_number=initial_page_number,
    nodes_per_page=maxnodespergraph,
    cluster_depth=initial_clusters_on_page,
)

initial_df = pd.DataFrame(baseresults)
myinitialtable = dash_table.DataTable(
    initial_df.to_dict("records"),
    [{"name": i, "id": i} for i in initial_df.columns],
) if not initial_df.empty else dash_table.DataTable([], [])

# ---------- App / Layout ----------

app = DashProxy(transforms=[MultiplexerTransform()], external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = movies_layout(
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
    get_cytoscape_stylesheet
)

# ---------- Callbacks ----------

# Callback for Name Search Query Type
@app.callback(
    Output("querydescription", "children"),
    Input("namesearchquerytype", "value"),
)
def update_output_querytype(value: str):
    global MoviesPersonsQuery

    if value == "levenshtein":
        MoviesPersonsQuery = get_query("./MoviesPersonsQuery_lev.aql")
        return "Levenshtein Queries are quicker but sometimes will not bring back all the desired results"

    MoviesPersonsQuery = get_query("./MoviesPersonsQuery_like.aql")
    return "The like Query will add % to each side of your text for short strings this could take a long time"

# Callback for Name Search
@app.callback(
    Output("name_search_dashtable", "children"),
    Output("person-dropdown-1", "options"),
    Output("person-dropdown-1", "value"),
    Input("Find-Person", "n_clicks"),
    State("persontofind", "value"),
)
def update_output_find_person(n_clicks: int, value: Optional[str]):
    person1_results = get_text_results_for_name(value)

    if len(person1_results) == 0:
        first_return = f'There were no results for "{value}" and the button has been clicked {n_clicks} times'
        return first_return, myinitialtable, dropdownelements, initial_dropdownelement

    first_return = f'The input value was "{value}" and the button has been clicked {n_clicks} times'
    df = pd.DataFrame(person1_results)
    my_dash_table = dash_table.DataTable(
        df.to_dict("records"),
        [{"name": i, "id": i} for i in df.columns],
    )
    new_dropdown = [
        {"label": f"{doc['primaryName']}-{doc['nconst']}", "value": doc["nconst"]}
        for doc in person1_results
    ]
    new_first_element = new_dropdown[0]["value"]

    return my_dash_table, new_dropdown, new_first_element

#Callback for Selecting Exact Person Node from Drop-Down
@app.callback(
    Output("selected-node-store", "data"),
    Output("container-add-person", "children"),
    Output("page-number", "value"),
    Output("current-node-1", "children"),
    Input("person-dropdown-1", "value"),
    State("person-dropdown-1", "options"),
    prevent_initial_call=True,
)
def select_dropdown_node(value: Optional[str], options: List[Dict[str, Any]]):
    if not value:
        raise PreventUpdate

    label = get_selected_label_from_options(value, options)
    selected = {"id": f"name_basics/{value}", "label": label}
    return selected, json.dumps(selected), 1, json.dumps(selected)

# Select Start and End Nodes and Deal with Drop Down
@app.callback(
    Output("person1nconst", "children"),
    Output("person1name", "children"),
    Output("person2nconst", "children"),
    Output("person2name", "children"),
    Input("submit-person1", "n_clicks"),
    Input("submit-person2", "n_clicks"),
    State("container-add-person", "children")
)
def update_output_add_person(_n_clicks1: int, _n_clicks2: int, value: Optional[str]):
    clicked_node_nconst, clicked_node_name = parse_clicked_node_from_table_json(value)
  
    if ctx.triggered_id == "submit-person1":
        return clicked_node_nconst, clicked_node_name, no_update, no_update

    if ctx.triggered_id == "submit-person2":
        return no_update, no_update, clicked_node_nconst, clicked_node_name

    raise PreventUpdate


#Show Relationship between 2 nodes
@app.callback(
    Output("person-relationship-text", "children"),
    Output("relationship_dashtable", "children"),
#    Output("relationship_selector", "options"),
#    Output("relationship_selector", "value"),
    Output("six-degrees-array", "data"),
    Input("show-relationship", "n_clicks"),
    State("person1nconst", "children"),
    State("person2nconst", "children")
)
def update_output_relationship(n_clicks: int, value1: str, value2: str):
    relationship_results = get_relationships(value1, value2)

    # Convert results to text
    relationship_results_text = ""
    for doc in relationship_results:
        relationship_results_text += repr(doc)

    for char in "[],'":
        relationship_results_text = relationship_results_text.replace(char, "")

    # Number of rows returned
    num_items = len(relationship_results)

    # Build dropdown options
    num_items_array = [{"label": str(i), "value": i} for i in range(1, num_items + 1)]

    #Build Array of Nodes and Edges to store in Array
    #current_six_degrees_array = [1,2,3]
    current_six_degrees_array = get_relationships_nodes(value1, value2)

    return (
        f"The button has been clicked {n_clicks} times. And the Relationship between {value1} and {value2} is: ",
        return_document_as_list(relationship_results_text),
 #       num_items_array,   # dropdown options
 #       1 if num_items > 0 else None,  # default selected value
        current_six_degrees_array
    )

#The Cytoscape chart itself.  Updates to the Six-Degrees Relationship Table
@app.callback(
    Output("cytoscape1", "elements"),
    Output("cytoscape1", "layout"),
    Output("cytoscape1", "stylesheet"),
    Output("total-return-nodes", "children"),
    Output("page-number", "max"),
    Output("page-number", "value", allow_duplicate=True),
    Input("update-graph-to-table", "n_clicks"),
    Input("six-degrees-array", "data"),
    State("selected-node-store", "data"),
    State("layout_type", "value"),
    State("title-node-color-picker", "value"),
    State("name-node-color-picker", "value"),
    State("edge-color-picker", "value"),
    State("title_node_shape", "value"),
    State("name_node_shape", "value"),
    State("nodes-on-page", "value"),
    State("clusters-on-page", "value"),
    State("page-number", "value"),
    State("person1nconst", "children"),
    State("person2nconst", "children"),
    prevent_initial_call=True,
)
def update_graph_six_degrees(
    n_clicks: int,
    my_relationships: Optional[str],
    selected_node: Optional[Dict[str, Any]],
    layout_type: str,
    title_color: Optional[Dict[str, str]],
    name_color: Optional[Dict[str, str]],
    edge_color: Optional[Dict[str, str]],
    title_shape: Optional[str],
    name_shape: Optional[str],
    nodes_on_page: Optional[int],
    clusters_on_page: Optional[int],
    page_number: Optional[int],
    p1nconst: Optional[str],
    p2nconst: Optional[str]
    ):

        if not n_clicks or not selected_node:
            raise PreventUpdate

        raw_id = selected_node.get("id", "")
        label = selected_node.get("label", "Unknown")

        if "/" in raw_id:
            center_id = raw_id.split("/", 1)[1]
        else:
            center_id = raw_id

        requested_page = max(1, int(page_number or 1))
        nodes_on_page = max(1, int(nodes_on_page or maxnodespergraph))
        clusters_on_page = max(1, int(clusters_on_page or 1))
        
  
        elements, total_nodes, max_pages, final_page = build_graph_for_six_degrees(
            center_id=center_id,
            center_label=label,
            page_number=requested_page,
            nodes_per_page=nodes_on_page,
            cluster_depth=clusters_on_page,
            n1=p1nconst,
            n2=p2nconst,
        )

        return (
            elements,
            get_cytoscape_layout(layout_type or initial_layout_type),
            get_cytoscape_stylesheet(title_color, name_color, edge_color, title_shape, name_shape),
            total_nodes,
            max_pages,
            final_page,
        )

#The Cytoscape chart itself.  Executes on Update Graph to specific Node
@app.callback(
    Output("cytoscape1", "elements"),
    Output("cytoscape1", "layout"),
    Output("cytoscape1", "stylesheet"),
    Output("total-return-nodes", "children"),
    Output("page-number", "max"),
    Output("page-number", "value", allow_duplicate=True),
    Input("update-graph-to-node", "n_clicks"),
    State("selected-node-store", "data"),
    State("layout_type", "value"),
    State("title-node-color-picker", "value"),
    State("name-node-color-picker", "value"),
    State("edge-color-picker", "value"),
    State("title_node_shape", "value"),
    State("name_node_shape", "value"),
    State("nodes-on-page", "value"),
    State("clusters-on-page", "value"),
    State("page-number", "value"),
    prevent_initial_call=True,
)
def update_graph_center_node(
    n_clicks,
    selected_node,
    layout_type,
    title_color,
    name_color,
    edge_color,
    title_shape,
    name_shape,
    nodes_on_page,
    clusters_on_page,
    page_number,
):
    if not n_clicks or not selected_node:
        raise PreventUpdate

    return compute_center_graph_output(
        selected_node,
        layout_type,
        title_color,
        name_color,
        edge_color,
        title_shape,
        name_shape,
        nodes_on_page,
        clusters_on_page,
        page_number,
    )


#CLicking Edge
@app.callback(
    Output("jobs-modal", "is_open"),
    Output("jobs-modal-header", "children"),
    Output("modal-jobs-body-total", "children"),
    Input("cytoscape1", "tapEdgeData"),
    Input("jobsclose", "n_clicks"),
    State("jobs-modal", "is_open"),
)
def job_info(tap_edge_data, n_close, is_open):

    trigger = ctx.triggered_id

    # Close button clicked → close modal
    if trigger == "jobsclose":
        return False, no_update, no_update

    # Edge clicked → open modal + update body
    if trigger == "cytoscape1" and tap_edge_data:
        #Send edge nconst and tconst to Query to get Job Roles
        edge_tconst,edge_primaryTitle,edge_nconst,edge_primaryName=extract_edge_ids(tap_edge_data)
        #alljobs=get_edge_jobs("nm0491697","tt6293610")
        alljobs=get_edge_jobs(edge_nconst,edge_tconst)
        edge_table = principals_to_table(alljobs)
        header = html.Pre("Jobs / Roles for "+edge_primaryName+" in " +edge_primaryTitle, style={"whiteSpace": "pre-wrap"})

        body = dash_table.DataTable(
            data=edge_table,
            columns=[{"name": c, "id": c} for c in ["Category", "Job", "Characters"]],
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "4px"},
            style_header={"fontWeight": "bold"},
        )

        return True,header,body

    # No change
    return is_open, no_update, no_update

#Special Call back for holding down Alt-Key to bring up Modal Info Dialog
@app.callback(
    Output("alt-modal", "is_open"),
    Output("alt-modal-body-imdb", "href"),
    Output("alt-modal-body-wiki", "href"),
    Output("alt-modal-header", "children"),
    Output("alt-click-store", "data"),

    # NEW: graph update outputs
    Output("cytoscape1", "elements"),
    Output("cytoscape1", "layout"),
    Output("cytoscape1", "stylesheet"),
    Output("total-return-nodes", "children"),
    Output("page-number", "max"),
    Output("page-number", "value", allow_duplicate=True),

    Input("cytoscape1", "tapNodeData"),
    Input("altclose", "n_clicks"),

    # NEW: graph update states
    State("alt-click-store", "data"),
    State("layout_type", "value"),
    State("title-node-color-picker", "value"),
    State("name-node-color-picker", "value"),
    State("edge-color-picker", "value"),
    State("title_node_shape", "value"),
    State("name_node_shape", "value"),
    State("nodes-on-page", "value"),
    State("clusters-on-page", "value"),
    State("page-number", "value"),

    prevent_initial_call=True
)
def toggle_modal(
    tap_node_data,
     _close_button,
    alt_click_state,
    layout_type,
    title_color,
    name_color,
    edge_color,
    title_shape,
    name_shape,
    nodes_on_page,
    clusters_on_page,
    page_number,
):

    # Close modal
    if ctx.triggered_id == "altclose":
        return (
            False, "", "", "", {"armed": False, "ts": 0},
            no_update, no_update, no_update, no_update, no_update, no_update
        )

    if not tap_node_data:
        raise PreventUpdate

    armed = bool((alt_click_state or {}).get("armed"))
    ts = int((alt_click_state or {}).get("ts", 0))
    now_ms = int(time.time() * 1000)

    # ---------- NORMAL CLICK (no alt key) ----------
    if not armed or (now_ms - ts) >= 1200:
        graph_outputs = compute_center_graph_output(
            tap_node_data,
            layout_type,
            title_color,
            name_color,
            edge_color,
            title_shape,
            name_shape,
            nodes_on_page,
            clusters_on_page,
            page_number,
        )

        return (
            False, "", "", "", {"armed": False, "ts": 0},
            *graph_outputs
        )

    # ---------- ALT CLICK (open modal) ----------
    label = tap_node_data.get("label", "Unknown")
    raw_id = tap_node_data.get("id", "")
    node_id = raw_id.split("/", 1)[1] if "/" in raw_id else raw_id

    imdb_page = (
        f"https://www.imdb.com/title/{node_id}"
        if node_id.startswith("tt")
        else f"https://www.imdb.com/name/{node_id}"
    )
    wiki_page = f"https://en.wikipedia.org/w/index.php?search={label.replace(' ', '_')}"

    return (
        True,
        imdb_page,
        wiki_page,
        f"{label}-{node_id}",
        {"armed": False, "ts": 0},
        no_update, no_update, no_update, no_update, no_update, no_update
    )


if __name__ == "__main__":
    app.run(host=os.getenv("LOCALHOST"), port=os.getenv("LOCALPORT"), debug=True)