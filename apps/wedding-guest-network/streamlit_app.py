"""
Wedding Guest Network Visualizer
PyVis force graph: Groom/Bride → Social Group hubs → Guests.
Built by OpenClaw 🦞
"""
# v5.2.0 — rigid drag, collapse/expand hubs, popup next to node, edit via location.href

import json
import math
import pathlib
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pyvis.network import Network

st.set_page_config(page_title="Wedding Guest Network", page_icon="💒", layout="wide")

# =============================================================================
# GUEST DATA
# =============================================================================

_GUESTS_FILE = pathlib.Path(__file__).parent / "guests.json"

with open(_GUESTS_FILE, "r", encoding="utf-8") as _f:
    GUEST_INITIAL = json.load(_f)

# Normalize: migrate old "group" (string) → "groups" (list) if needed
for _g in GUEST_INITIAL:
    if "groups" not in _g:
        _g["groups"] = [_g.pop("group")] if "group" in _g else []

# =============================================================================
# COLOR SCHEME
# =============================================================================

# Each group gets a distinct, vivid color — no more blue monoculture
GROUP_HUB_COLORS = {
    "Family":                  "#1565C0",  # deep blue
    "Basic School":            "#2E7D32",  # forest green
    "Secondary School":        "#00838F",  # dark teal
    "University":              "#283593",  # indigo
    "Reboleira Parish":        "#E65100",  # deep orange
    "Erasmus Milan":           "#B71C1C",  # dark red
    "Erasmus Netherlands":     "#F57F17",  # amber
    "Work (Planos Ótimos)":    "#4A148C",  # deep purple
    "Work (Sonant)":           "#1B5E20",  # dark green
    "Special (Reciprocity)":   "#827717",  # olive
    "Friends":                 "#AD1457",  # deep pink
    "Work":                    "#BF360C",  # burnt orange
    "Common Friends":          "#6A1B9A",  # violet
}

# Guest circles: lighter tint of their group's hub color
def _lighter(hex_color: str, factor: float = 0.45) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "#{:02x}{:02x}{:02x}".format(
        int(r + (255 - r) * factor),
        int(g + (255 - g) * factor),
        int(b + (255 - b) * factor),
    )

GROUP_GUEST_COLORS = {k: _lighter(v) for k, v in GROUP_HUB_COLORS.items()}

# Border color and shape tell you which side a group belongs to
SIDE_BORDER = {"Rafael": "#90CAF9", "Catarina": "#F48FB1", "Common": "#CE93D8"}
SIDE_SHAPE  = {"Rafael": "square", "Catarina": "diamond", "Common": "hexagon"}

PRIORITY_SIZE = {"High": 28, "Medium": 18, "Low": 11}

ALL_GROUPS = sorted([
    "Family", "Basic School", "Secondary School", "University",
    "Reboleira Parish", "Erasmus Milan", "Erasmus Netherlands",
    "Work (Planos Ótimos)", "Work (Sonant)", "Special (Reciprocity)",
    "Friends", "Common Friends", "Work", "Other",
])

# =============================================================================
# SESSION STATE
# =============================================================================

if "guests" not in st.session_state:
    st.session_state.guests = GUEST_INITIAL

# =============================================================================
# SIDEBAR — edit mode when ?edit=<name> in URL, otherwise normal management
# =============================================================================

edit_name = st.query_params.get("edit", "")

with st.sidebar:
    st.title("💒 Guest Management")

    if edit_name:
        real = next((g for g in st.session_state.guests if g["name"] == edit_name), None)
        if real:
            st.subheader("✏️ Edit Guest")
            st.markdown(f"**{real['name']}**")
            with st.form("edit_form"):
                ep = st.selectbox("Priority", ["High", "Medium", "Low"],
                                  index=["High", "Medium", "Low"].index(real["priority"]))
                eg = st.multiselect("Groups", ALL_GROUPS, default=real["groups"])
                es = st.selectbox("Side", ["Rafael", "Catarina", "Common"],
                                  index=["Rafael", "Catarina", "Common"].index(real["side"]))
                en = st.text_input("Notes", value=real.get("notes", ""))
                c1, c2 = st.columns(2)
                if c1.form_submit_button("💾 Save"):
                    real["priority"] = ep
                    real["groups"] = eg
                    real["side"] = es
                    real["notes"] = en
                    st.query_params.clear()
                    st.rerun()
                if c2.form_submit_button("🗑️ Delete"):
                    st.session_state.guests = [
                        g for g in st.session_state.guests if g["name"] != real["name"]
                    ]
                    st.query_params.clear()
                    st.rerun()
        else:
            st.warning(f"Guest '{edit_name}' not found.")
        if st.button("← Cancel"):
            st.query_params.clear()
            st.rerun()

    else:
        with st.form("add_guest_form", clear_on_submit=True):
            st.subheader("Add New Guest")
            new_name     = st.text_input("Name", placeholder="Full name")
            new_side     = st.selectbox("Side", ["Rafael", "Catarina", "Common"])
            new_groups   = st.multiselect("Groups", ALL_GROUPS, default=["Family"])
            new_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            new_notes    = st.text_input("Notes", placeholder="Optional notes")
            if st.form_submit_button("Add Guest") and new_name:
                names = [g["name"] for g in st.session_state.guests]
                if new_name in names:
                    st.error(f"Already exists: {new_name}")
                else:
                    st.session_state.guests.append({
                        "name": new_name, "side": new_side, "groups": new_groups,
                        "priority": new_priority, "notes": new_notes,
                    })
                    st.success(f"Added {new_name}")

        st.divider()
        st.subheader("Filters")
        filter_side     = st.multiselect("Side", ["Rafael", "Catarina", "Common"],
                                          default=["Rafael", "Catarina", "Common"])
        filter_priority = st.multiselect("Priority", ["High", "Medium", "Low"],
                                          default=["High", "Medium", "Low"])
        filter_group    = st.multiselect("Group", ALL_GROUPS, default=ALL_GROUPS)

        st.divider()
        st.subheader("Statistics")
        gs = st.session_state.guests
        st.metric("Total", len(gs))
        st.metric("High Priority", sum(1 for g in gs if g["priority"] == "High"))
        c1, c2 = st.columns(2)
        c1.metric("Rafael",   sum(1 for g in gs if g["side"] == "Rafael"))
        c2.metric("Catarina", sum(1 for g in gs if g["side"] == "Catarina"))
        st.metric("Common",   sum(1 for g in gs if g["side"] == "Common"))

# =============================================================================
# MAIN
# =============================================================================

if not edit_name:
    filtered = [
        g for g in st.session_state.guests
        if g["side"] in filter_side
        and g["priority"] in filter_priority
        and any(grp in filter_group for grp in g["groups"])
    ]
else:
    filtered = list(st.session_state.guests)

st.title("💒 Wedding Guest Network")
st.caption(
    "⬜ Square = Rafael's groups  ·  ◇ Diamond = Catarina's groups  ·  ⬡ Hexagon = Common  ·  "
    "⭕ Large circle = Rafael / Catarina  ·  ● Small circles = guests (size = priority)  ·  "
    "Click a guest to view & edit"
)
st.caption(f"Showing {len(filtered)} of {len(st.session_state.guests)} guests")

# =============================================================================
# BUILD PYVIS NETWORK
# =============================================================================

def build_network(guests: list) -> Network:
    net = Network(
        height="720px", width="100%",
        bgcolor="#1e1e1e", font_color="white",
        directed=False, notebook=False,
        cdn_resources="in_line",
    )

    # repulsion solver, centralGravity=0: guests only feel spring pull toward
    # their fixed group hub — no drift toward canvas center.
    net.set_options(json.dumps({
        "nodes": {
            "borderWidth": 2,
            "font": {"size": 12, "face": "arial", "color": "white"},
        },
        "edges": {
            "smooth": {"type": "continuous"},
            "color": {"inherit": "from"},
        },
        "physics": {
            "enabled": True,
            "solver": "repulsion",
            "repulsion": {
                "centralGravity": 0,
                "springLength": 70,
                "springConstant": 0.5,
                "nodeDistance": 160,
                "damping": 0.5,
            },
            "stabilization": {"iterations": 400, "updateInterval": 25},
        },
        "interaction": {
            "hover": False,          # disable built-in hover tooltip
            "tooltipDelay": 99999,   # effectively disable vis.js tooltips
        },
    }))

    # ---- Groom & Bride — fixed large circles ----
    for node_id, label, bg, border, x in [
        ("__Rafael__",   "Rafael\n(Groom)",  "#0D47A1", "#90CAF9", -440),
        ("__Catarina__", "Catarina\n(Bride)", "#AD1457", "#F48FB1",  440),
    ]:
        net.add_node(node_id, label=label,
                     color={"background": bg, "border": border,
                            "highlight": {"background": bg, "border": "#ffffff"}},
                     size=52, shape="dot",
                     font={"size": 14, "bold": True, "color": "white"},
                     title="",          # no vis.js tooltip
                     x=x, y=0, physics=False)

    # ---- Classify groups by side ----
    all_grps = sorted(set(grp for g in guests for grp in g["groups"]))
    catarina_grps = [g for g in all_grps if g in ("Friends", "Work")]
    common_grps   = [g for g in all_grps if "Common" in g]
    rafael_grps   = [g for g in all_grps if g not in catarina_grps and g not in common_grps]

    def grp_side(grp):
        if grp in catarina_grps: return "Catarina"
        if grp in common_grps:   return "Common"
        return "Rafael"

    def add_group_arc(group_list, cx, cy, radius, arc_start, arc_end):
        n = len(group_list)
        for i, grp in enumerate(group_list):
            angle = (arc_start + arc_end) / 2 if n == 1 else \
                    arc_start + (arc_end - arc_start) * i / (n - 1)
            gx = int(cx + radius * math.cos(angle))
            gy = int(cy + radius * math.sin(angle))
            side   = grp_side(grp)
            bg     = GROUP_HUB_COLORS.get(grp, "#607D8B")
            border = SIDE_BORDER[side]
            shape  = SIDE_SHAPE[side]
            net.add_node(
                f"__group__{grp}", label=grp,
                color={"background": bg, "border": border,
                       "highlight": {"background": bg, "border": "#ffffff"}},
                size=26, shape=shape,
                font={"size": 11, "color": "white"},
                title="",            # no vis.js tooltip
                x=gx, y=gy, physics=False,
            )

    add_group_arc(rafael_grps,   -440,  0, 300, math.pi * 0.28, math.pi * 1.72)
    add_group_arc(catarina_grps,  440,  0, 300, math.pi * -0.72, math.pi * 0.72)
    add_group_arc(common_grps,      0, -220, 130, math.pi * -0.4, math.pi * 0.4)

    # ---- Edges: anchor → group hubs ----
    added_hub_edges = set()
    for g in guests:
        for grp in g["groups"]:
            gid = f"__group__{grp}"
            if g["side"] in ("Rafael", "Common") and ("R", grp) not in added_hub_edges:
                net.add_edge("__Rafael__", gid, color="#42A5F5", width=2)
                added_hub_edges.add(("R", grp))
            if g["side"] in ("Catarina", "Common") and ("C", grp) not in added_hub_edges:
                net.add_edge("__Catarina__", gid, color="#F48FB1", width=2)
                added_hub_edges.add(("C", grp))

    # ---- Guest nodes + edges to group hubs ----
    for g in guests:
        primary    = g["groups"][0] if g["groups"] else "Family"
        node_color = GROUP_GUEST_COLORS.get(primary, "#90A4AE")
        hub_color  = GROUP_HUB_COLORS.get(primary, "#607D8B")
        net.add_node(
            g["name"], label=g["name"],
            color={"background": node_color, "border": hub_color,
                   "highlight": {"background": hub_color, "border": "#ffffff"}},
            size=PRIORITY_SIZE.get(g["priority"], 14),
            shape="dot",
            font={"size": 11, "color": "white"},
            title="",   # tooltip handled by our popup, not vis.js
        )
        for grp in g["groups"]:
            net.add_edge(f"__group__{grp}", g["name"],
                         color={"color": node_color, "opacity": 0.6}, width=1)

    return net


def inject_popup(html: str, guests: list) -> str:
    """Inject popup + rigid-drag + collapse/expand logic into the PyVis HTML."""
    guests_map  = {g["name"]: g for g in guests}
    guests_json = json.dumps(guests_map, ensure_ascii=False)

    code = f"""
<style>
#gn-popup {{
    display: none;
    position: fixed;
    background: #242424;
    border: 1px solid #555;
    border-radius: 10px;
    padding: 18px 20px 16px;
    color: #eee;
    font-family: Arial, sans-serif;
    font-size: 13px;
    width: 280px;
    z-index: 9999;
    box-shadow: 0 8px 32px rgba(0,0,0,0.7);
    pointer-events: auto;
}}
#gn-popup h3 {{
    margin: 0 0 12px; font-size: 16px; color: #fff;
    padding-right: 20px; line-height: 1.3;
}}
.gn-field  {{ display:flex; gap:8px; align-items:baseline; margin:5px 0; }}
.gn-lbl    {{ color:#888; font-size:11px; text-transform:uppercase;
              letter-spacing:.5px; min-width:54px; flex-shrink:0; }}
.gn-val    {{ color:#eee; }}
.gn-High   {{ color:#81c784; font-weight:bold; }}
.gn-Medium {{ color:#fff176; font-weight:bold; }}
.gn-Low    {{ color:#ef9a9a; font-weight:bold; }}
.gn-Rafael   {{ color:#90caf9; }}
.gn-Catarina {{ color:#f48fb1; }}
.gn-Common   {{ color:#ce93d8; }}
.gn-notes  {{ font-style:italic; color:#bbb; }}
.gn-btn-row {{ display:flex; gap:8px; margin-top:14px; }}
.gn-btn    {{ flex:1; padding:8px; border:none; border-radius:6px;
              cursor:pointer; font-size:12px; font-weight:bold; }}
.gn-edit   {{ background:#1565C0; color:#fff; }}
.gn-edit:hover  {{ background:#1976D2; }}
.gn-close  {{ background:#333; color:#aaa; }}
.gn-close:hover {{ background:#444; }}
#gn-x {{
    position:absolute; top:11px; right:14px;
    cursor:pointer; color:#666; font-size:20px;
    line-height:1; user-select:none;
}}
#gn-x:hover {{ color:#aaa; }}
</style>

<div id="gn-popup">
  <span id="gn-x" onclick="gnClose()">&#215;</span>
  <h3 id="gn-name"></h3>
  <div class="gn-field">
    <span class="gn-lbl">Side</span>
    <span class="gn-val" id="gn-side"></span>
  </div>
  <div class="gn-field">
    <span class="gn-lbl">Groups</span>
    <span class="gn-val" id="gn-groups"></span>
  </div>
  <div class="gn-field">
    <span class="gn-lbl">Priority</span>
    <span class="gn-val" id="gn-priority"></span>
  </div>
  <div class="gn-field" id="gn-notes-row" style="display:none">
    <span class="gn-lbl">Notes</span>
    <span class="gn-val gn-notes" id="gn-notes"></span>
  </div>
  <div class="gn-btn-row">
    <button class="gn-btn gn-edit"  onclick="gnEdit()">&#9998;&nbsp;Edit</button>
    <button class="gn-btn gn-close" onclick="gnClose()">Close</button>
  </div>
</div>

<script>
// ─── Guest data ────────────────────────────────────────────────────────────
var _GN = {guests_json};

// ─── Popup ─────────────────────────────────────────────────────────────────
var _gnSel = null;
var _gnOutside = null;

function gnClose() {{
    document.getElementById("gn-popup").style.display = "none";
    _gnSel = null;
    if (_gnOutside) {{
        document.removeEventListener("mousedown", _gnOutside);
        _gnOutside = null;
    }}
    if (typeof network !== "undefined") network.unselectAll();
}}

function gnEdit() {{
    if (!_gnSel) return;
    // Navigate parent to ?edit=<name> — triggers Streamlit rerun with edit form
    window.parent.location.href = "?edit=" + encodeURIComponent(_gnSel);
}}

function gnPosition(sx, sy) {{
    var popup = document.getElementById("gn-popup");
    var pw = 296, ph = popup.offsetHeight || 220;
    var vw = window.innerWidth, vh = window.innerHeight;
    var left = sx + 16;
    if (left + pw > vw - 8) left = sx - pw - 16;
    left = Math.max(8, left);
    var top = sy - Math.round(ph / 2);
    top = Math.max(8, Math.min(top, vh - ph - 8));
    popup.style.left = left + "px";
    popup.style.top  = top  + "px";
}}

function gnShow(id, sx, sy) {{
    var g = _GN[id];
    if (!g) return;
    _gnSel = id;
    document.getElementById("gn-name").textContent = g.name;
    var sEl = document.getElementById("gn-side");
    sEl.textContent = g.side; sEl.className = "gn-val gn-" + g.side;
    document.getElementById("gn-groups").textContent = (g.groups || []).join(", ");
    var pEl = document.getElementById("gn-priority");
    pEl.textContent = g.priority; pEl.className = "gn-val gn-" + g.priority;
    var nRow = document.getElementById("gn-notes-row");
    if (g.notes) {{
        document.getElementById("gn-notes").textContent = g.notes;
        nRow.style.display = "flex";
    }} else {{
        nRow.style.display = "none";
    }}
    var popup = document.getElementById("gn-popup");
    popup.style.display = "block";
    gnPosition(sx, sy);
    // Close on click outside (delayed to skip the current mousedown)
    if (_gnOutside) document.removeEventListener("mousedown", _gnOutside);
    setTimeout(function() {{
        _gnOutside = function(e) {{
            if (!popup.contains(e.target)) gnClose();
        }};
        document.addEventListener("mousedown", _gnOutside);
    }}, 100);
}}

// ─── Rigid dragging ────────────────────────────────────────────────────────
var _dId = null, _dGroupIds = [], _dStart = {{}}, _dPhysics = [];

function _collectGuests(hubId, ids, pos) {{
    network.getConnectedNodes(hubId).forEach(function(gId) {{
        if (!gId.startsWith("__") && ids.indexOf(gId) < 0) {{
            var nd = nodes.get(gId);
            if (nd && !nd.hidden) {{ ids.push(gId); _dStart[gId] = pos[gId]; }}
        }}
    }});
}}

network.on("dragStart", function(p) {{
    if (!p.nodes.length) return;
    _dId = p.nodes[0]; _dGroupIds = []; _dStart = {{}}; _dPhysics = [];
    var pos = network.getPositions();
    _dStart[_dId] = pos[_dId];

    if (_dId === "__Rafael__" || _dId === "__Catarina__") {{
        network.getConnectedNodes(_dId).forEach(function(hubId) {{
            if (!hubId.startsWith("__group__")) return;
            if (_dGroupIds.indexOf(hubId) < 0) {{ _dGroupIds.push(hubId); _dStart[hubId] = pos[hubId]; }}
            _collectGuests(hubId, _dGroupIds, pos);
        }});
    }} else if (_dId.startsWith("__group__")) {{
        _collectGuests(_dId, _dGroupIds, pos);
    }}

    // Freeze physics on visible guests so physics engine doesn't fight the drag
    _dPhysics = _dGroupIds.filter(function(id) {{ return !id.startsWith("__"); }});
    if (_dPhysics.length) nodes.update(_dPhysics.map(function(id) {{ return {{id:id, physics:false}}; }}));
}});

network.on("drag", function(p) {{
    if (!p.nodes.length || !_dGroupIds.length) return;
    var cur = network.getPositions([_dId])[_dId];
    var dx = cur.x - _dStart[_dId].x, dy = cur.y - _dStart[_dId].y;
    nodes.update(_dGroupIds.map(function(id) {{
        return {{ id:id, x: _dStart[id].x + dx, y: _dStart[id].y + dy }};
    }}));
}});

network.on("dragEnd", function() {{
    if (_dPhysics.length) nodes.update(_dPhysics.map(function(id) {{ return {{id:id, physics:true}}; }}));
    _dId = null; _dGroupIds = []; _dStart = {{}}; _dPhysics = [];
}});

// ─── Double-click group hub: collapse / expand ──────────────────────────────
var _collapsed = {{}};   // groupId → true/false
var _collData   = {{}};   // groupId → {{ nodeIds, edgeIds, baseLabel }}

network.on("doubleClick", function(p) {{
    gnClose();
    if (!p.nodes.length) return;
    var id = p.nodes[0];
    if (!id.startsWith("__group__")) return;

    var nd        = nodes.get(id);
    var baseLabel = nd ? nd.label.replace(/\\n\\(\\d+\\)$/, "") : id.replace("__group__","");

    if (_collapsed[id]) {{
        // ── EXPAND ──
        var info = _collData[id] || {{ nodeIds:[], edgeIds:[] }};
        nodes.update(info.nodeIds.map(function(n) {{ return {{id:n, hidden:false}}; }}));
        edges.update(info.edgeIds.map(function(e) {{ return {{id:e, hidden:false}}; }}));
        nodes.update({{ id:id, label:baseLabel }});
        _collapsed[id] = false;
        delete _collData[id];
    }} else {{
        // ── COLLAPSE ──
        var guestIds = network.getConnectedNodes(id).filter(function(g) {{ return !g.startsWith("__"); }});
        var edgeIds  = [];
        guestIds.forEach(function(gId) {{
            network.getConnectedEdges(gId).forEach(function(eId) {{
                if (edgeIds.indexOf(eId) < 0) edgeIds.push(eId);
            }});
        }});
        _collData[id]   = {{ nodeIds:guestIds, edgeIds:edgeIds }};
        _collapsed[id]  = true;
        nodes.update(guestIds.map(function(n) {{ return {{id:n, hidden:true}}; }}));
        edges.update(edgeIds.map(function(e) {{ return {{id:e, hidden:true}}; }}));
        nodes.update({{ id:id, label: baseLabel + "\\n(" + guestIds.length + ")" }});
    }}
}});

// ─── Select node → show popup ──────────────────────────────────────────────
network.on("selectNode", function(p) {{
    if (!p.nodes.length) return;
    var id = p.nodes[0];
    if (id.startsWith("__")) {{ gnClose(); return; }}
    var nodePos = network.getPositions([id])[id];
    var dom     = network.canvasToDOM(nodePos);
    var rect    = document.getElementById("mynetwork").getBoundingClientRect();
    gnShow(id, rect.left + dom.x, rect.top + dom.y);
}});
</script>
"""
    return html.replace("</body>", code + "\n</body>")


# =============================================================================
# RENDER NETWORK
# =============================================================================

if filtered:
    net  = build_network(filtered)
    html = net.generate_html()
    html = inject_popup(html, filtered)
    components.html(html, height=760, scrolling=False)
else:
    st.warning("No guests match the current filters.")

# =============================================================================
# GUEST TABLE
# =============================================================================

st.divider()
st.subheader("Guest List")

df_rows = [
    {"Name": g["name"], "Side": g["side"],
     "Groups": ", ".join(g["groups"]),
     "Priority": g["priority"], "Notes": g.get("notes", "")}
    for g in filtered
]

if df_rows:
    df    = pd.DataFrame(df_rows)
    p_ord = {"High": 0, "Medium": 1, "Low": 2}
    df["_p"] = df["Priority"].map(p_ord)
    df = df.sort_values(["Side", "_p", "Groups", "Name"]).drop("_p", axis=1)

    def color_side(v):
        if v == "Rafael":   return "background-color:#bbdefb;color:#0d47a1"
        if v == "Catarina": return "background-color:#f8bbd9;color:#ad1457"
        return "background-color:#e1bee7;color:#7b1fa2"

    def color_priority(v):
        if v == "High":   return "background-color:#c8e6c9;color:#2e7d32"
        if v == "Medium": return "background-color:#fff9c4;color:#f57f17"
        return "background-color:#ffcdd2;color:#c62828"

    st.dataframe(
        df.style.map(color_side, subset=["Side"]).map(color_priority, subset=["Priority"]),
        hide_index=True,
    )
else:
    st.info("No guests to display.")

st.divider()
st.caption("Built by OpenClaw 🦞 | Rafael & Catarina | v5.1.0")
