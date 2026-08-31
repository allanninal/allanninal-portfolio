"""Shared AWS-dark palette + service icon library for /build.

The /build diagrams were authored monochrome (white boxes, #111 strokes and
text, #555 sub-labels). Everything here maps that vocabulary onto the AWS
console dark theme and adds the colourful service icons.
"""

# --- surfaces -------------------------------------------------------------
DG_BG      = "#16212f"   # plate behind the diagram
BOX_FILL   = "#20303f"   # component box
BOX_FILL_2 = "#233346"   # external / off-AWS box
STROKE     = "#3f5169"   # box outline
LINE       = "#6b8199"   # connector
TEXT       = "#e6edf5"   # title text
SUB        = "#9fb0c4"   # sub-label
FAINT      = "#8d99a8"   # container labels, notes
ACCENT     = "#ff9900"   # AWS orange

# --- AWS icon-set category colours (2023 set) -----------------------------
CAT = {
    "analytics":   "#8C4FFF",
    "integration": "#E7157B",
    "compute":     "#ED7100",
    "containers":  "#ED7100",
    "database":    "#C925D1",
    "devtools":    "#C925D1",
    "frontend":    "#DD344C",
    "iot":         "#7AA116",
    "ml":          "#01A88D",
    "management":  "#E7157B",
    "migration":   "#01A88D",
    "network":     "#8C4FFF",
    "security":    "#DD344C",
    "storage":     "#7AA116",
    "business":    "#DD344C",
    "human":       "#4A90D9",   # people / outside-the-cloud actors
    "external":    "#7D8CA3",   # third-party systems
}

CAT_LABEL = {
    "compute":     "Compute",
    "storage":     "Storage",
    "database":    "Database",
    "integration": "App integration",
    "ml":          "Machine learning",
    "network":     "Networking",
    "security":    "Security & identity",
    "management":  "Management",
    "analytics":   "Analytics",
    "frontend":    "Front-end & mobile",
    "human":       "People",
    "external":    "Outside AWS",
}
