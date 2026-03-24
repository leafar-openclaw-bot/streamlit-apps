"""
Wedding Guest Network Visualizer
PyVis force graph: Groom/Bride → Social Group hubs → Guests.
Built by OpenClaw 🦞
"""
# v5.0.0 — repulsion solver (centralGravity=0) for hub-clustering; click-to-edit popup

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

# Hub (group node) colors — vivid/saturated
GROUP_HUB_COLORS = {
    "Family":                  "#0D47A1",
    "Basic School":            "#1565C0",
    "Secondary School":        "#1976D2",
    "University":              "#1E88E5",
    "Reboleira Parish":        "#2196F3",
    "Erasmus Milan":           "#039BE5",
    "Erasmus Netherlands":     "#0288D1",
    "Work (Planos Ótimos)":    "#0277BD",
    "Work (Sonant)":           "#01579B",
    "Special (Reciprocity)":   "#4527A0",
    "Friends":                 "#AD1457",
    "Work":                    "#C2185B",
    "Common Friends":          "#6A1B9A",
}

# Guest node colors — lighter tint of the same hue
def _lighter(hex_color: str, factor: float = 0.45) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "#{:02x}{:02x}{:02x}".format(
        int(r + (255 - r) * factor),
        int(g + (255 - g) * factor),
        int(b + (255 - b) * factor),
    )

GROUP_GUEST_COLORS = {k: _lighter(v) for k, v in GROUP_HUB_COLORS.items()}

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
        # ---- EDIT MODE ----
        real = next((g for g in st.session_state.guests if g["name"] == edit_name), None)
        if real:
            st.subheader(f"✏️ Edit Guest")
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
        # ---- NORMAL MODE ----
        with st.form("add_guest_form", clear_on_submit=True):
            st.subheader("Add New Guest")
            new_name = st.text_input("Name", placeholder="Full name")
            new_side = st.selectbox("Side", ["Rafael", "Catarina", "Common"])
            new_groups = st.multiselect("Groups", ALL_GROUPS, default=["Family"])
            new_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            new_notes = st.text_input("Notes", placeholder="Optional notes")
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
        filter_side = st.multiselect("Side", ["Rafael", "Catarina", "Common"],
                                      default=["Rafael", "Catarina", "Common"])
        filter_priority = st.multiselect("Priority", ["High", "Medium", "Low"],
                                         default=["High", "Medium", "Low"])
        filter_group = st.multiselect("Group", ALL_GROUPS, default=ALL_GROUPS)

        st.divider()

        st.subheader("Statistics")
        gs = st.session_state.guests
        st.metric("Total", len(gs))
        st.metric("High Priority", sum(1 for g in gs if g["priority"] == "High"))
        c1, c2 = st.columns(2)
        c1.metric("Rafael", sum(1 for g in gs if g["side"] == "Rafael"))
        c2.metric("Catarina", sum(1 for g in gs if g["side"] == "Catarina"))
        st.metric("Common", sum(1 for g in gs if g["side"] == "Common"))

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
    # During edit mode keep last filter (use all)
    filtered = list(st.session_state.guests)

st.title("💒 Wedding Guest Network")
st.caption(
    "🔵 Circles = guests (colored by group, size = priority)  ·  "
    "⬛ Squares = social groups (fixed anchors)  ·  "
    "⭕ Large circles = Rafael & Catarina  ·  "
    "Click a person to view & edit"
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

    # Physics: repulsion solver with centralGravity=0 so guests only respond
    # to spring forces from their connected group hub (which is fixed).
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
                "centralGravity": 0,      # no center pull — nodes cluster around hub
                "springLength": 70,       # rest length of edge springs
                "springConstant": 0.5,    # stiffness — higher = tighter cluster
                "nodeDistance": 160,      # repulsion range between unconnected nodes
                "damping": 0.5,
            },
            "stabilization": {"iterations": 400, "updateInterval": 25},
        },
        "interaction": {"hover": True, "tooltipDelay": 100},
    }))

    # ---- Groom & Bride — fixed large circles ----
    net.add_node("__Rafael__", label="Rafael\n(Groom)",
                 color={"background": "#0D47A1", "border": "#42A5F5",
                        "highlight": {"background": "#1565C0", "border": "#90CAF9"}},
                 size=52, shape="dot",
                 font={"size": 14, "bold": True},
                 title="<b>Rafael</b> — Groom",
                 x=-420, y=0, physics=False)
    net.add_node("__Catarina__", label="Catarina\n(Bride)",
                 color={"background": "#AD1457", "border": "#F48FB1",
                        "highlight": {"background": "#C2185B", "border": "#F48FB1"}},
                 size=52, shape="dot",
                 font={"size": 14, "bold": True},
                 title="<b>Catarina</b> — Bride",
                 x=420, y=0, physics=False)

    # ---- Group hub nodes — squares, fixed on arcs around their anchor ----
    all_grps = sorted(set(grp for g in guests for grp in g["groups"]))
    catarina_grps = [g for g in all_grps if g in ("Friends", "Work")]
    common_grps   = [g for g in all_grps if "Common" in g]
    rafael_grps   = [g for g in all_grps if g not in catarina_grps and g not in common_grps]

    def add_group_arc(group_list, cx, cy, radius, arc_start, arc_end):
        n = len(group_list)
        for i, grp in enumerate(group_list):
            angle = (arc_start + arc_end) / 2 if n == 1 else \
                    arc_start + (arc_end - arc_start) * i / (n - 1)
            gx = int(cx + radius * math.cos(angle))
            gy = int(cy + radius * math.sin(angle))
            hub_color = GROUP_HUB_COLORS.get(grp, "#607D8B")
            net.add_node(
                f"__group__{grp}", label=grp,
                color={"background": hub_color, "border": "#ffffff",
                       "highlight": {"background": hub_color, "border": "#ffffff"}},
                size=26, shape="square",
                font={"size": 11, "color": "white"},
                title=f"<b>Group:</b> {grp}",
                x=gx, y=gy, physics=False,
            )

    add_group_arc(rafael_grps,   -420,  0, 290, math.pi * 0.30, math.pi * 1.70)
    add_group_arc(catarina_grps,  420,  0, 290, math.pi * -0.70, math.pi * 0.70)
    add_group_arc(common_grps,      0, -210, 130, math.pi * -0.40, math.pi * 0.40)

    # ---- Edges: groom/bride → group hubs ----
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

    # ---- Guest nodes + edges to their group hubs ----
    for g in guests:
        primary = g["groups"][0] if g["groups"] else "Family"
        node_color = GROUP_GUEST_COLORS.get(primary, "#90A4AE")
        hub_color  = GROUP_HUB_COLORS.get(primary, "#607D8B")
        tooltip = (
            f"<b>{g['name']}</b><br>"
            f"Side: {g['side']}<br>"
            f"Groups: {', '.join(g['groups'])}<br>"
            f"Priority: {g['priority']}"
            + (f"<br><i>{g['notes']}</i>" if g.get("notes") else "")
        )
        net.add_node(
            g["name"], label=g["name"],
            color={"background": node_color, "border": hub_color,
                   "highlight": {"background": hub_color, "border": "#ffffff"}},
            size=PRIORITY_SIZE.get(g["priority"], 14),
            shape="dot",
            font={"size": 11, "color": "white"},
            title=tooltip,
        )
        for grp in g["groups"]:
            net.add_edge(f"__group__{grp}", g["name"],
                         color={"color": node_color, "opacity": 0.6}, width=1)

    return net


def inject_popup(html: str, guests: list) -> str:
    """Inject a click-to-view/edit popup into the PyVis HTML."""
    guests_map = {g["name"]: g for g in guests}
    guests_json = json.dumps(guests_map, ensure_ascii=False)

    popup_code = f"""
<style>
#gn-overlay {{
    display:none; position:fixed; inset:0;
    background:rgba(0,0,0,0.35); z-index:9998;
}}
#gn-popup {{
    display:none; position:fixed;
    top:50%; left:50%; transform:translate(-50%,-50%);
    background:#242424; border:1px solid #555; border-radius:10px;
    padding:22px 24px; color:#eee; font-family:Arial,sans-serif;
    font-size:13px; width:310px; z-index:9999;
    box-shadow:0 10px 40px rgba(0,0,0,0.7);
}}
#gn-popup h3 {{ margin:0 0 14px; font-size:17px; color:#fff; padding-right:20px; }}
.gn-field {{ margin:6px 0; display:flex; gap:8px; align-items:baseline; }}
.gn-lbl {{ color:#888; font-size:11px; text-transform:uppercase;
           letter-spacing:.5px; min-width:56px; flex-shrink:0; }}
.gn-val {{ color:#eee; }}
.gn-High   {{ color:#81c784; font-weight:bold; }}
.gn-Medium {{ color:#fff176; font-weight:bold; }}
.gn-Low    {{ color:#ef9a9a; font-weight:bold; }}
.gn-Rafael   {{ color:#90caf9; }}
.gn-Catarina {{ color:#f48fb1; }}
.gn-Common   {{ color:#ce93d8; }}
.gn-btn-row {{ display:flex; gap:8px; margin-top:16px; }}
.gn-btn {{ flex:1; padding:8px; border:none; border-radius:6px;
           cursor:pointer; font-size:13px; font-weight:bold; }}
.gn-edit  {{ background:#1565C0; color:#fff; }}
.gn-edit:hover  {{ background:#1976D2; }}
.gn-close {{ background:#333; color:#aaa; }}
.gn-close:hover {{ background:#444; }}
#gn-x {{ position:absolute; top:12px; right:16px; cursor:pointer;
         color:#666; font-size:20px; line-height:1; user-select:none; }}
#gn-x:hover {{ color:#aaa; }}
</style>

<div id="gn-overlay" onclick="gnClose()"></div>
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
    <span class="gn-val" id="gn-notes" style="font-style:italic;color:#bbb"></span>
  </div>
  <div class="gn-btn-row">
    <button class="gn-btn gn-edit" onclick="gnEdit()">&#9998;&nbsp;Edit</button>
    <button class="gn-btn gn-close" onclick="gnClose()">Close</button>
  </div>
</div>

<script>
var _GN = {guests_json};
var _gnSel = null;

function gnClose() {{
  document.getElementById("gn-popup").style.display   = "none";
  document.getElementById("gn-overlay").style.display = "none";
  _gnSel = null;
  if (typeof network !== "undefined") network.unselectAll();
}}

function gnEdit() {{
  if (!_gnSel) return;
  var url = window.parent.location.pathname + "?edit=" + encodeURIComponent(_gnSel);
  window.parent.history.pushState({{}}, "", url);
  window.parent.dispatchEvent(new PopStateEvent("popstate"));
}}

function gnShow(id) {{
  var g = _GN[id];
  if (!g) return;
  _gnSel = id;
  document.getElementById("gn-name").textContent = g.name;
  var sEl = document.getElementById("gn-side");
  sEl.textContent = g.side;
  sEl.className = "gn-val gn-" + g.side;
  document.getElementById("gn-groups").textContent = g.groups.join(", ");
  var pEl = document.getElementById("gn-priority");
  pEl.textContent = g.priority;
  pEl.className = "gn-val gn-" + g.priority;
  var notesRow = document.getElementById("gn-notes-row");
  if (g.notes) {{
    document.getElementById("gn-notes").textContent = g.notes;
    notesRow.style.display = "flex";
  }} else {{
    notesRow.style.display = "none";
  }}
  document.getElementById("gn-popup").style.display   = "block";
  document.getElementById("gn-overlay").style.display = "block";
}}

(function waitForNetwork() {{
  if (typeof network !== "undefined") {{
    network.on("selectNode", function(p) {{
      if (!p.nodes.length) return;
      var id = p.nodes[0];
      if (id.startsWith("__")) {{ gnClose(); return; }}
      gnShow(id);
    }});
  }} else {{
    setTimeout(waitForNetwork, 80);
  }}
}})();
</script>
"""
    return html.replace("</body>", popup_code + "\n</body>")


# =============================================================================
# RENDER NETWORK
# =============================================================================

if filtered:
    net = build_network(filtered)
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
    df = pd.DataFrame(df_rows)
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
st.caption("Built by OpenClaw 🦞 | Rafael & Catarina | v5.0.0")
