"""Original 24x24 glyphs drawn on a white-on-colour tile, AWS-icon style.

Every glyph is our own drawing on a 24-unit grid -- simple geometry only, no
tracing of anyone's icon set. `tile()` renders a rounded square in the service
category colour with the glyph knocked out in white, which is the visual
convention an AWS architecture diagram reader already knows.
"""
from .palette import CAT

W = "#ffffff"

# name -> (category, svg body drawn on a 0..24 grid, white on colour)
GLYPHS = {
 # --- compute -----------------------------------------------------------
 "lambda":   ("compute",   '<path d="M4.5 20.5 11.4 3.5h3.4L21.5 20.5h-3.6L13 7.9l-4.9 12.6Z" fill="#fff"/><path d="m10.2 12.8 3.1 7.7H9.7L8.1 16Z" fill="#fff" opacity=".78"/>'),
 "compute":  ("compute",   '<rect x="6" y="6" width="12" height="12" rx="2" fill="#fff"/><path d="M9 3v3M12 3v3M15 3v3M9 18v3M12 18v3M15 18v3M3 9h3M3 12h3M3 15h3M18 9h3M18 12h3M18 15h3" stroke="#fff" stroke-width="1.7" stroke-linecap="round"/>'),
 "container":("containers",'<path d="M3 11h4v6H3zM8 11h4v6H8zM13 11h4v6h-4zM8 5h4v5H8z" fill="#fff"/><path d="M18 12c2 0 3 .8 3 2.5S19.5 19 17 19" stroke="#fff" stroke-width="1.7" fill="none" stroke-linecap="round"/>'),
 # --- storage -----------------------------------------------------------
 "bucket":   ("storage",   '<path d="M4 6h16l-1.8 13.2a1.6 1.6 0 0 1-1.6 1.4H7.4a1.6 1.6 0 0 1-1.6-1.4Z" fill="#fff"/><ellipse cx="12" cy="6" rx="8" ry="2.6" fill="#fff"/>'),
 "archive":  ("storage",   '<rect x="3" y="4" width="18" height="5" rx="1" fill="#fff"/><path d="M5 10h14v9a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 5 19Z" fill="#fff" opacity=".9"/><path d="M10 14h4" stroke="'+CAT["storage"]+'" stroke-width="2" stroke-linecap="round"/>'),
 # --- database ----------------------------------------------------------
 "database": ("database",  '<ellipse cx="12" cy="6" rx="8" ry="3" fill="#fff"/><path d="M4 6v5c0 1.7 3.6 3 8 3s8-1.3 8-3V6" fill="#fff" opacity=".92"/><path d="M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6" fill="#fff" opacity=".8"/>'),
 # --- machine learning --------------------------------------------------
 "model":    ("ml",        '<path d="M12 3a5 5 0 0 1 4.6 3A4.4 4.4 0 0 1 18 14.6V16a4 4 0 0 1-6 3.5A4 4 0 0 1 6 16v-1.4A4.4 4.4 0 0 1 7.4 6 5 5 0 0 1 12 3Z" fill="#fff"/><path d="M12 7v10M9.5 10.5h5M9.5 14h5" stroke="'+CAT["ml"]+'" stroke-width="1.5" stroke-linecap="round"/>'),
 "ocr":      ("ml",        '<rect x="4" y="3" width="16" height="18" rx="2" fill="#fff"/><path d="M7.5 8h9M7.5 11.5h9M7.5 15h5.5" stroke="'+CAT["ml"]+'" stroke-width="1.7" stroke-linecap="round"/>'),
 "vision":   ("ml",        '<path d="M2 12s3.8-6 10-6 10 6 10 6-3.8 6-10 6S2 12 2 12Z" fill="#fff"/><circle cx="12" cy="12" r="3" fill="'+CAT["ml"]+'"/>'),
 "voice":    ("ml",        '<rect x="9" y="2.5" width="6" height="11" rx="3" fill="#fff"/><path d="M5.5 11.5a6.5 6.5 0 0 0 13 0M12 18v3.5M8.5 21.5h7" stroke="#fff" stroke-width="1.9" fill="none" stroke-linecap="round"/>'),
 # --- app integration ---------------------------------------------------
 "email":    ("integration",'<rect x="2.5" y="5" width="19" height="14" rx="2" fill="#fff"/><path d="m4 7.5 8 5.5 8-5.5" stroke="'+CAT["integration"]+'" stroke-width="1.9" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'),
 "queue":    ("integration",'<rect x="3" y="4" width="18" height="4.2" rx="1.4" fill="#fff"/><rect x="3" y="9.9" width="18" height="4.2" rx="1.4" fill="#fff" opacity=".85"/><rect x="3" y="15.8" width="18" height="4.2" rx="1.4" fill="#fff" opacity=".7"/>'),
 "event":    ("integration",'<path d="M13.5 2 5 13.4h5.2L9.5 22 19 10.2h-5.4Z" fill="#fff"/>'),
 "topic":    ("integration",'<circle cx="12" cy="12" r="3" fill="#fff"/><path d="M6.6 6.6a7.6 7.6 0 0 0 0 10.8M17.4 17.4a7.6 7.6 0 0 0 0-10.8M3.6 3.6a11.8 11.8 0 0 0 0 16.8M20.4 20.4a11.8 11.8 0 0 0 0-16.8" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/>'),
 "flow":     ("integration",'<rect x="2.5" y="8.5" width="7" height="7" rx="1.6" fill="#fff"/><rect x="14.5" y="2.5" width="7" height="7" rx="1.6" fill="#fff"/><rect x="14.5" y="14.5" width="7" height="7" rx="1.6" fill="#fff"/><path d="M9.5 12h2.5V6h2.5M9.5 12h2.5v6h2.5" stroke="#fff" stroke-width="1.7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'),
 "webhook":  ("integration",'<circle cx="6" cy="17.6" r="3.4" fill="#fff"/><circle cx="18" cy="17.6" r="3.4" fill="#fff"/><circle cx="12" cy="5.6" r="3.4" fill="#fff"/><path d="M9.9 8.3 7.3 14.3M14.1 8.3l2.6 6M9.4 17.6h5.2" stroke="#fff" stroke-width="1.9" stroke-linecap="round"/>'),
 # --- networking --------------------------------------------------------
 "gateway":  ("network",   '<path d="M12 2 3 6v6.4c0 5 3.8 8.6 9 9.6 5.2-1 9-4.6 9-9.6V6Z" fill="#fff"/><path d="M8 12h8M12.6 8.6 16 12l-3.4 3.4" stroke="'+CAT["network"]+'" stroke-width="1.9" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'),
 "cdn":      ("network",   '<circle cx="12" cy="12" r="9.2" fill="#fff"/><path d="M12 2.8c2.6 2.4 4 5.6 4 9.2s-1.4 6.8-4 9.2c-2.6-2.4-4-5.6-4-9.2s1.4-6.8 4-9.2ZM3.2 12h17.6" stroke="'+CAT["network"]+'" stroke-width="1.6" fill="none"/>'),
 "dns":      ("network",   '<circle cx="12" cy="12" r="9.2" fill="#fff"/><path d="M12 6.5v11M7 9.5h10M7 14.5h10" stroke="'+CAT["network"]+'" stroke-width="1.7" stroke-linecap="round"/>'),
 # --- security ----------------------------------------------------------
 "shield":   ("security",  '<path d="M12 2.2 4 5.6v6.2c0 4.9 3.3 8.6 8 10 4.7-1.4 8-5.1 8-10V5.6Z" fill="#fff"/><path d="m8.4 12 2.6 2.6 4.6-5" stroke="'+CAT["security"]+'" stroke-width="2.1" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'),
 "key":      ("security",  '<circle cx="8" cy="8" r="5" fill="#fff"/><circle cx="8" cy="8" r="1.8" fill="'+CAT["security"]+'"/><path d="m11.6 11.6 8 8M17 16l2.4-2.4M14.4 13.4 16.8 11" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>'),
 "lock":     ("security",  '<rect x="4.5" y="10" width="15" height="11" rx="2" fill="#fff"/><path d="M8 10V7.5a4 4 0 0 1 8 0V10" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round"/><circle cx="12" cy="15.5" r="1.7" fill="'+CAT["security"]+'"/>'),
 # --- management --------------------------------------------------------
 "monitor":  ("management",'<circle cx="12" cy="12" r="9.2" fill="#fff"/><path d="M12 6.5v5.5l3.6 2.4" stroke="'+CAT["management"]+'" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'),
 "clock":    ("management",'<circle cx="12" cy="12" r="9.2" fill="#fff"/><path d="M12 6.5V12l4 2.2" stroke="'+CAT["management"]+'" stroke-width="2" fill="none" stroke-linecap="round"/>'),
 "alarm":    ("management",'<path d="M12 3.2 22 20.2H2Z" fill="#fff"/><path d="M12 9.4v4.6" stroke="'+CAT["management"]+'" stroke-width="2.2" stroke-linecap="round"/><circle cx="12" cy="17.1" r="1.35" fill="'+CAT["management"]+'"/>'),
 "log":      ("management",'<rect x="4" y="3" width="16" height="18" rx="2" fill="#fff"/><path d="M7.5 8h9M7.5 12h9M7.5 16h6" stroke="'+CAT["management"]+'" stroke-width="1.7" stroke-linecap="round"/>'),
 # --- analytics ---------------------------------------------------------
 "chart":    ("analytics", '<rect x="3" y="3" width="18" height="18" rx="2.4" fill="#fff"/><path d="M7.5 16v-4M12 16V8m4.5 8v-6" stroke="'+CAT["analytics"]+'" stroke-width="2.2" stroke-linecap="round"/>'),
 "report":   ("analytics", '<path d="M5 2.5h9L19.5 8v13.5H5Z" fill="#fff"/><path d="M8.5 17v-3.5M12 17v-6m3.5 6v-2.5" stroke="'+CAT["analytics"]+'" stroke-width="2" stroke-linecap="round"/>'),
 "search":   ("analytics", '<circle cx="10.5" cy="10.5" r="6.4" fill="#fff"/><circle cx="10.5" cy="10.5" r="3.2" fill="'+CAT["analytics"]+'"/><path d="m15.4 15.4 5 5" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>'),
 # --- front-end / channels ---------------------------------------------
 "browser":  ("frontend",  '<rect x="2.5" y="4" width="19" height="16" rx="2" fill="#fff"/><path d="M2.5 8.5h19" stroke="'+CAT["frontend"]+'" stroke-width="1.7"/><circle cx="5.8" cy="6.3" r="1" fill="'+CAT["frontend"]+'"/><circle cx="8.8" cy="6.3" r="1" fill="'+CAT["frontend"]+'"/>'),
 "phone":    ("frontend",  '<rect x="6" y="2" width="12" height="20" rx="2.6" fill="#fff"/><path d="M10.4 5.2h3.2" stroke="'+CAT["frontend"]+'" stroke-width="1.6" stroke-linecap="round"/><circle cx="12" cy="18.6" r="1.2" fill="'+CAT["frontend"]+'"/>'),
 "chat":     ("frontend",  '<path d="M3 5.5A2.5 2.5 0 0 1 5.5 3h13A2.5 2.5 0 0 1 21 5.5v8a2.5 2.5 0 0 1-2.5 2.5H9l-6 5Z" fill="#fff"/><path d="M7.5 7.5h9M7.5 11.5h6" stroke="'+CAT["frontend"]+'" stroke-width="1.8" stroke-linecap="round"/>'),
 "form":     ("frontend",  '<rect x="3.5" y="2.5" width="17" height="19" rx="2" fill="#fff"/><path d="M7.5 7.5h9M7.5 11.5h9M7.5 15.5h5" stroke="'+CAT["frontend"]+'" stroke-width="1.8" stroke-linecap="round"/>'),
 # --- documents & money -------------------------------------------------
 "doc":      ("business",  '<path d="M5 2.5h9L19.5 8v13.5H5Z" fill="#fff"/><path d="M13.6 2.8V8.2h5.2" stroke="'+CAT["business"]+'" stroke-width="1.5" fill="none"/><path d="M8.5 12.5h7M8.5 16h4.5" stroke="'+CAT["business"]+'" stroke-width="1.7" stroke-linecap="round"/>'),
 "money":    ("business",  '<rect x="2.5" y="5" width="19" height="14" rx="2.2" fill="#fff"/><circle cx="12" cy="12" r="3.4" fill="'+CAT["business"]+'"/><path d="M5.6 8.4h1.4M17 15.6h1.4" stroke="'+CAT["business"]+'" stroke-width="1.7" stroke-linecap="round"/>'),
 "calendar": ("business",  '<rect x="3" y="4.5" width="18" height="16.5" rx="2" fill="#fff"/><path d="M3 9.5h18" stroke="'+CAT["business"]+'" stroke-width="1.7"/><path d="M8 2.5v4M16 2.5v4" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/><rect x="7" y="12.5" width="3.4" height="3.2" rx=".7" fill="'+CAT["business"]+'"/>'),
 "cart":     ("business",  '<path d="M2.5 3.5h3L8 15.5h10" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M6.6 6.5h15L19.4 13H8Z" fill="#fff"/><circle cx="9.5" cy="19.5" r="1.8" fill="#fff"/><circle cx="17.5" cy="19.5" r="1.8" fill="#fff"/>'),
 "tag":      ("business",  '<path d="M11.6 2.5H21v9.4l-9.6 9.6L2 12.1Z" fill="#fff"/><circle cx="17" cy="7" r="1.9" fill="'+CAT["business"]+'"/>'),
 "box":      ("business",  '<path d="M12 2.5 21 7v10l-9 4.5L3 17V7Z" fill="#fff"/><path d="M3 7l9 4.5L21 7M12 11.5V21" stroke="'+CAT["business"]+'" stroke-width="1.6" fill="none"/>'),
 "truck":    ("business",  '<rect x="1.8" y="6" width="12" height="10" rx="1.4" fill="#fff"/><path d="M13.8 9.2h4l3.4 3.6V16h-7.4Z" fill="#fff"/><circle cx="7" cy="18.4" r="2.2" fill="#fff"/><circle cx="17.4" cy="18.4" r="2.2" fill="#fff"/>'),
 # --- people & outside --------------------------------------------------
 "person":   ("human",     '<circle cx="12" cy="7.6" r="4.3" fill="#fff"/><path d="M3.6 21.2a8.4 8.4 0 0 1 16.8 0Z" fill="#fff"/>'),
 "team":     ("human",     '<circle cx="8.6" cy="8" r="3.6" fill="#fff"/><circle cx="17" cy="9.4" r="2.8" fill="#fff" opacity=".85"/><path d="M1.8 20.4a6.8 6.8 0 0 1 13.6 0Z" fill="#fff"/><path d="M16 14.4a5.6 5.6 0 0 1 6.2 6h-4.4Z" fill="#fff" opacity=".85"/>'),
 "external": ("external",  '<rect x="3" y="3" width="18" height="18" rx="3" fill="#fff"/><path d="M9.6 14.4 15.4 8.6M10.4 8.6h5v5" stroke="'+CAT["external"]+'" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'),
 "plug":     ("external",  '<path d="M8.4 2.5v5.2M15.6 2.5v5.2" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/><path d="M5.6 7.7h12.8v3.6a6.4 6.4 0 0 1-12.8 0Z" fill="#fff"/><path d="M12 17.7v3.8" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>'),
 "cloud":    ("external",  '<path d="M7.4 19.5a5 5 0 0 1-.6-9.96A6.3 6.3 0 0 1 18.6 11a4.3 4.3 0 0 1-.6 8.5Z" fill="#fff"/>'),
 # --- generic roles -----------------------------------------------------
 "inbox":    ("integration",'<path d="M3 13.5 5.6 4.2h12.8L21 13.5V19a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 19Z" fill="#fff"/><path d="M3 13.5h5a4 4 0 0 0 8 0h5" stroke="'+CAT["integration"]+'" stroke-width="1.8" fill="none" stroke-linejoin="round"/>'),
 "filter":   ("analytics", '<path d="M2.6 4h18.8l-7.3 8.6v7.2l-4.2 2.2v-9.4Z" fill="#fff"/>'),
 "check":    ("ml",        '<circle cx="12" cy="12" r="9.4" fill="#fff"/><path d="m7.8 12.2 3 3 5.4-6" stroke="'+CAT["ml"]+'" stroke-width="2.3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'),
 "bell":     ("integration",'<path d="M12 2.6a6.4 6.4 0 0 1 6.4 6.4c0 4.3 1.5 5.9 2.1 6.5H3.5c.6-.6 2.1-2.2 2.1-6.5A6.4 6.4 0 0 1 12 2.6Z" fill="#fff"/><path d="M9.7 18.6a2.5 2.5 0 0 0 4.6 0" stroke="#fff" stroke-width="1.9" fill="none" stroke-linecap="round"/>'),
 "image":    ("frontend",  '<rect x="2.6" y="4.4" width="18.8" height="15.2" rx="2.2" fill="#fff"/><circle cx="8.4" cy="9.6" r="1.9" fill="'+CAT["frontend"]+'"/><path d="m4 17.4 5-5 4.4 4.4 3-2.8 4.6 4.4Z" fill="'+CAT["frontend"]+'"/>'),
 "link":     ("network",   '<path d="M9.6 14.4 14.4 9.6" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/><path d="M13 6.4 15 4.4a4.4 4.4 0 0 1 6.2 6.2l-2 2M11 17.6l-2 2a4.4 4.4 0 0 1-6.2-6.2l2-2" stroke="#fff" stroke-width="2.2" fill="none" stroke-linecap="round"/>'),
 "code":     ("devtools",  '<rect x="2.6" y="3.6" width="18.8" height="16.8" rx="2.4" fill="#fff"/><path d="m9 9.4-2.6 2.6L9 14.6M15 9.4l2.6 2.6L15 14.6" stroke="'+CAT["devtools"]+'" stroke-width="1.9" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'),
 "stop":     ("security",  '<circle cx="12" cy="12" r="9.4" fill="#fff"/><path d="M8.4 8.4l7.2 7.2M15.6 8.4l-7.2 7.2" stroke="'+CAT["security"]+'" stroke-width="2.4" stroke-linecap="round"/>'),
 "branch":   ("integration",'<path d="M12 2.2 21.8 12 12 21.8 2.2 12Z" fill="#fff"/><path d="M12 7.6v5.2" stroke="'+CAT["integration"]+'" stroke-width="2.3" stroke-linecap="round"/><circle cx="12" cy="16.4" r="1.4" fill="'+CAT["integration"]+'"/>'),
 "counter":  ("analytics", '<rect x="3" y="3" width="18" height="18" rx="3.4" fill="#fff"/><path d="M7.6 15.8V8.6M12 15.8v-4.4M16.4 15.8V6.4" stroke="'+CAT["analytics"]+'" stroke-width="2.6" stroke-linecap="round"/>'),
 "retry":    ("management",'<path d="M20 12a8 8 0 1 1-2.6-5.9" stroke="#fff" stroke-width="2.3" fill="none" stroke-linecap="round"/><path d="M20.6 3.4v5h-5" stroke="#fff" stroke-width="2.3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'),
 "map":      ("business",  '<path d="M2.6 5.8 8.6 3.2v15l-6 2.6Zm6-2.6 6.8 2.6v15l-6.8-2.6Zm6.8 2.6 6-2.6v15l-6 2.6Z" fill="#fff"/><path d="M8.6 3.2v15M15.4 5.8v15" stroke="'+CAT["business"]+'" stroke-width="1.4"/>'),
}


def tile(name, x, y, size=26, rx=5):
    """A colour tile with the glyph knocked out, placed at (x, y)."""
    cat, body = GLYPHS[name]
    s = size / 24.0
    return (
        f'<g transform="translate({x:.1f},{y:.1f})" aria-hidden="true">'
        f'<rect width="{size:.1f}" height="{size:.1f}" rx="{rx}" fill="{CAT[cat]}"/>'
        f'<g transform="scale({s:.4f})">{body}</g>'
        f'</g>'
    )


def category_of(name):
    return GLYPHS[name][0]
