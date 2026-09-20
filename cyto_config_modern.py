# Layout helpers
default_inline = {
    "display": "block",
    "padding": "0",
}

default_inline_dropdown_old = {
    "display": "inline-block",
    "padding-left": "10px",
    "width": "150px",
}

# Cytoscape layout + style
cyto_layout = {"name": "circle"}

cyto_style = {
    "width": "100%",
    "height": "640px",
}

cyto_stylesheet = [
    {
        "selector": "node",
        "style": {
            "background-color": "#14B8A6",
            "border-color": "#0F766E",
            "border-width": 2,
            "color": "#111827",
            "font-size": "12px",
            "font-weight": "700",
            "label": "data(label)",
            "text-background-color": "#FFFFFF",
            "text-background-opacity": 0.82,
            "text-background-padding": "3px",
            "text-border-opacity": 0,
            "text-halign": "center",
            "text-valign": "center",
        },
    },
    {
        "selector": "edge",
        "style": {
            "curve-style": "bezier",
            "label": "data(job)",
            "line-color": "#F97316",
            "target-arrow-color": "#F97316",
            "target-arrow-shape": "triangle",
            "width": 2,
            "font-size": "10px",
            "color": "#374151",
            "text-background-color": "#FFFFFF",
            "text-background-opacity": 0.78,
            "text-background-padding": "2px",
        },
    },
    {
        "selector": '[id *= "tt"]',
        "style": {
            "shape": "round-rectangle",
            "background-color": "#2563EB",
            "border-color": "#1D4ED8",
            "color": "#0F172A",
        },
    },
    {
        "selector": '[id *= "nm"]',
        "style": {
            "shape": "ellipse",
            "background-color": "#14B8A6",
            "border-color": "#0F766E",
        },
    },
    {
        "selector": ":selected",
        "style": {
            "background-color": "#F97316",
            "border-color": "#EA580C",
            "line-color": "#F97316",
            "target-arrow-color": "#F97316",
        },
    },
]
