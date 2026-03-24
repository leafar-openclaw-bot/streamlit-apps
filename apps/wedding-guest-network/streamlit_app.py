"""
Wedding Guest Network Visualizer
PyVis force graph: Groom/Bride → Social Group hubs → Guests.
Built by OpenClaw 🦞
"""
# v4.0.0 — Back to PyVis + st.html (reliable on Streamlit Cloud); group-hub topology

import json
import math
import pathlib
import re
import streamlit as st
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

GROUP_COLORS = {
    "Family": "#1565C0",
    "Basic School": "#1E88E5",
    "Secondary School": "#2196F3",
    "University": "#1976D2",
    "Reboleira Parish": "#42A5F5",
    "Erasmus Milan": "#0D47A1",
    "Erasmus Netherlands": "#1565C0",
    "Work (Planos Ótimos)": "#64B5F6",
    "Work (Sonant)": "#90CAF9",
    "Special (Reciprocity)": "#3F51B5",
    "Friends": "#E91E63",
    "Work": "#F48FB1",
    "Common Friends": "#7B1FA2",
}

PRIORITY_SIZE = {"High": 30, "Medium": 20, "Low": 12}

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

if "selected_guest" not in st.session_state:
    st.session_state.selected_guest = None

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.title("💒 Guest Management")

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

    # Edit selected guest
    selected = st.session_state.selected_guest
    if selected:
        real = next((g for g in st.session_state.guests if g["name"] == selected["name"]), None)
        if real:
            st.subheader(f"Edit: {real['name']}")
            with st.form("edit_form"):
                ep = st.selectbox("Priority", ["High", "Medium", "Low"],
                                  index=["High", "Medium", "Low"].index(real["priority"]))
                eg = st.multiselect("Groups", ALL_GROUPS, default=real["groups"])
                en = st.text_input("Notes", value=real["notes"])
                c1, c2 = st.columns(2)
                if c1.form_submit_button("Save"):
                    real["priority"] = ep
                    real["groups"] = eg
                    real["notes"] = en
                    st.session_state.selected_guest = None
                    st.rerun()
                if c2.form_submit_button("Delete"):
                    st.session_state.guests = [g for g in st.session_state.guests if g["name"] != real["name"]]
                    st.session_state.selected_guest = None
                    st.rerun()
        if st.button("Clear selection"):
            st.session_state.selected_guest = None
            st.rerun()
    else:
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

st.title("💒 Wedding Guest Network")
st.caption("Squares = social groups (fixed) · Circles = guests (physics) · Click sidebar to edit")

filtered = [
    g for g in st.session_state.guests
    if g["side"] in filter_side
    and g["priority"] in filter_priority
    and any(grp in filter_group for grp in g["groups"])
]
st.caption(f"Showing {len(filtered)} of {len(st.session_state.guests)} guests")

# =============================================================================
# BUILD PYVIS NETWORK
# =============================================================================

def build_network(guests, physics=True, spring_length=120, spring_strength=0.02):
    net = Network(
        height="700px", width="100%",
        bgcolor="#1e1e1e", font_color="white",
        directed=False, notebook=False,
    )

    net.set_options(json.dumps({
        "nodes": {"borderWidth": 2, "font": {"size": 11, "face": "arial"}},
        "edges": {"smooth": {"type": "continuous"}, "color": {"inherit": True}},
        "physics": {
            "enabled": physics,
            "forceAtlas2Based": {
                "gravitationalConstant": -100,
                "centralGravity": 0.05,
                "springLength": spring_length,
                "springConstant": spring_strength,
                "damping": 0.4,
            },
            "minVelocity": 0.75,
            "solver": "forceAtlas2Based",
        },
    }))

    # Groom and bride — fixed anchors
    net.add_node("__Rafael__", label="Rafael\n(Groom)",
                 color="#0D47A1", size=55, shape="star",
                 title="Rafael - Groom", x=-400, y=0, physics=False)
    net.add_node("__Catarina__", label="Catarina\n(Bride)",
                 color="#AD1457", size=55, shape="star",
                 title="Catarina - Bride", x=400, y=0, physics=False)

    # Partition groups by side
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
            net.add_node(
                f"__group__{grp}", label=grp,
                color=GROUP_COLORS.get(grp, "#757575"),
                size=28, shape="square",
                title=f"Group: {grp}",
                x=gx, y=gy, physics=False,
            )

    add_group_arc(rafael_grps,   -400,  0, 280, math.pi * 0.30, math.pi * 1.70)
    add_group_arc(catarina_grps,  400,  0, 280, math.pi * -0.70, math.pi * 0.70)
    add_group_arc(common_grps,      0, -200, 120, math.pi * -0.40, math.pi * 0.40)

    # Edges: groom/bride → group hubs
    added = set()
    for g in guests:
        for grp in g["groups"]:
            gid = f"__group__{grp}"
            if g["side"] in ("Rafael", "Common") and ("R", grp) not in added:
                net.add_edge("__Rafael__", gid, color="#1E88E5", width=2)
                added.add(("R", grp))
            if g["side"] in ("Catarina", "Common") and ("C", grp) not in added:
                net.add_edge("__Catarina__", gid, color="#E91E63", width=2)
                added.add(("C", grp))

    # Guest nodes + edges to their group hubs
    for g in guests:
        primary = g["groups"][0] if g["groups"] else "Family"
        color = GROUP_COLORS.get(primary, "#757575")
        tooltip = (f"<b>{g['name']}</b><br>Side: {g['side']}<br>"
                   f"Groups: {', '.join(g['groups'])}<br>Priority: {g['priority']}"
                   + (f"<br>{g['notes']}" if g["notes"] else ""))
        net.add_node(
            g["name"], label=g["name"],
            color=color,
            size=PRIORITY_SIZE.get(g["priority"], 15),
            shape="dot", title=tooltip,
        )
        for grp in g["groups"]:
            net.add_edge(f"__group__{grp}", g["name"], color=color, width=1)

    return net


if filtered:
    net = build_network(filtered,
                        physics=True,
                        spring_length=120,
                        spring_strength=0.02)
    html = net.generate_html()
    # Ensure a working vis-network CDN
    html = re.sub(
        r'src="https?://[^"]*vis-network[^"]*"',
        'src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis-network.min.js"',
        html,
    )
    st.html(html)
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
     "Priority": g["priority"], "Notes": g["notes"]}
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
st.caption("Built by OpenClaw 🦞 | Rafael & Catarina | v4.0.0")
