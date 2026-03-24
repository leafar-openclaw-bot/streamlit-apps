"""
Wedding Guest Network Visualizer
Interactive social graph of wedding guests clustered by relationship groups.
Built by OpenClaw 🦞
"""
# v2.0.0 — Refactor: JSON data, group hub topology, drift fix, spread initial positions

import json
import math
import re
import streamlit as st
import pandas as pd
from pyvis.network import Network
from pathlib import Path

st.set_page_config(
    page_title="Wedding Guest Network",
    page_icon="💒",
    layout="wide",
)

# =============================================================================
# CONSTANTS
# =============================================================================

GUESTS_FILE = Path(__file__).parent / "guests.json"

COLOR_SCHEME = {
    "Rafael": {
        "Family": "#1E88E5",
        "Basic School": "#42A5F5",
        "Secondary School": "#2196F3",
        "University": "#1976D2",
        "Reboleira Parish": "#64B5F6",
        "Erasmus Milan": "#0D47A1",
        "Erasmus Netherlands": "#1565C0",
        "Work (Planos Ótimos)": "#90CAF9",
        "Work (Sonant)": "#BBDEFB",
        "Special (Reciprocity)": "#3F51B5",
    },
    "Catarina": {
        "Family": "#E91E63",
        "Friends": "#F48FB1",
        "University": "#D81B60",
        "Work": "#F8BBD9",
    },
    "Common": {
        "Common Friends": "#9C27B0",
    },
}

PRIORITY_SHAPE = {"High": "star", "Medium": "dot", "Low": "dot"}
PRIORITY_SIZE = {"High": 30, "Medium": 20, "Low": 12}

# =============================================================================
# SESSION STATE
# =============================================================================

if "guests" not in st.session_state:
    with open(GUESTS_FILE, "r", encoding="utf-8") as f:
        st.session_state.guests = json.load(f)

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.title("💒 Guest Management")

    st.subheader("➕ Add New Guest")
    with st.form("add_guest_form", clear_on_submit=True):
        new_name = st.text_input("Name", placeholder="Full name")
        new_side = st.selectbox("Side", ["Rafael", "Catarina", "Common"])
        new_group = st.selectbox(
            "Group",
            [
                "Family", "Basic School", "Secondary School",
                "University", "Reboleira Parish",
                "Erasmus Milan", "Erasmus Netherlands",
                "Work (Planos Ótimos)", "Work (Sonant)",
                "Friends", "Common Friends",
                "Special (Reciprocity)", "Other",
            ],
        )
        new_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        new_notes = st.text_input("Notes (plus-ones, etc.)", placeholder="Optional notes")

        if st.form_submit_button("Add Guest") and new_name:
            st.session_state.guests.append({
                "name": new_name, "side": new_side, "group": new_group,
                "priority": new_priority, "notes": new_notes,
            })
            st.success(f"✅ Added {new_name}")

    st.divider()

    st.subheader("🔍 Filters")
    filter_side = st.multiselect(
        "Filter by Side", ["Rafael", "Catarina", "Common"],
        default=["Rafael", "Catarina", "Common"],
    )
    filter_priority = st.multiselect(
        "Filter by Priority", ["High", "Medium", "Low"],
        default=["High", "Medium", "Low"],
    )
    all_groups = list(dict.fromkeys(g["group"] for g in st.session_state.guests))
    filter_group = st.multiselect("Filter by Group", all_groups, default=all_groups)

    st.subheader("⚙️ Graph Physics")
    physics_enabled = st.checkbox("Enable Physics (draggable)", value=True)
    if physics_enabled:
        spring_length = st.slider("Spring Length", 50, 300, 120)
        spring_strength = st.slider("Spring Strength", 0.001, 0.1, 0.02)
    else:
        spring_length = 120
        spring_strength = 0.02

    st.divider()

    st.subheader("📊 Statistics")
    st.metric("Total Guests", len(st.session_state.guests))
    st.metric("High Priority", sum(1 for g in st.session_state.guests if g["priority"] == "High"))

# =============================================================================
# MAIN CONTENT
# =============================================================================

st.title("💒 Wedding Guest Network")
st.markdown("*Interactive social graph for visualizing and organizing wedding guests*")

filtered_guests = [
    g for g in st.session_state.guests
    if g["side"] in filter_side
    and g["priority"] in filter_priority
    and g["group"] in filter_group
]

st.caption(f"Showing {len(filtered_guests)} of {len(st.session_state.guests)} guests")

# =============================================================================
# BUILD NETWORK GRAPH
# =============================================================================

def _group_color(side: str, group: str) -> str:
    return COLOR_SCHEME.get(side, {}).get(group, "#757575")


def build_network(guests, spring_length=120, spring_strength=0.02, physics=True):
    """Build PyVis network: Rafael/Catarina → group hubs → guests."""

    net = Network(
        height="700px", width="100%",
        bgcolor="#1e1e1e", font_color="white",
        directed=False, notebook=False,
        select_menu=True, filter_menu=True,
    )

    physics_options = f"""
    {{
        "nodes": {{
            "borderWidth": 2,
            "borderWidthSelected": 4,
            "font": {{"size": 13, "face": "arial"}}
        }},
        "edges": {{
            "color": {{"inherit": true}},
            "smooth": {{"type": "continuous"}}
        }},
        "physics": {{
            "enabled": {"true" if physics else "false"},
            "forceAtlas2Based": {{
                "gravitationalConstant": -100,
                "centralGravity": 0.05,
                "springLength": {spring_length},
                "springConstant": {spring_strength},
                "damping": 0.4
            }},
            "minVelocity": 0.75,
            "solver": "forceAtlas2Based"
        }}
    }}
    """
    net.set_options(physics_options)

    # --- Groom & bride (fixed anchors) ---
    net.add_node(
        "Rafael", label="Rafael\n(Groom)",
        color="#0D47A1", size=60, shape="star",
        title="Rafael - Groom", group="Rafael",
        x=-400, y=0, fixed=False,
    )
    net.add_node(
        "Catarina", label="Catarina\n(Bride)",
        color="#AD1457", size=60, shape="star",
        title="Catarina - Bride", group="Catarina",
        x=400, y=0, fixed=False,
    )

    # --- Determine which groups appear per side ---
    # Build mapping: group → set of sides present in filtered guests
    group_sides: dict[str, set] = {}
    for g in guests:
        group_sides.setdefault(g["group"], set()).add(g["side"])

    # For each unique group, determine its "anchor side(s)" for positioning:
    #   Rafael-only → orbit around Rafael (left half)
    #   Catarina-only → orbit around Catarina (right half)
    #   Common or mixed → orbit between them (top/bottom)
    rafael_groups = sorted(
        grp for grp, sides in group_sides.items()
        if sides == {"Rafael"}
    )
    catarina_groups = sorted(
        grp for grp, sides in group_sides.items()
        if sides == {"Catarina"}
    )
    common_groups = sorted(
        grp for grp, sides in group_sides.items()
        if "Common" in sides or len(sides) > 1
    )

    def place_group_nodes(group_list, cx, cy, radius, arc_start, arc_end):
        """Add group hub nodes spread uniformly on an arc around (cx, cy)."""
        n = len(group_list)
        for i, grp in enumerate(group_list):
            angle = arc_start + (arc_end - arc_start) * (i / max(n - 1, 1))
            gx = cx + radius * math.cos(angle)
            gy = cy + radius * math.sin(angle)

            # Pick a representative color from the group's guests
            rep_guest = next((g for g in guests if g["group"] == grp), None)
            if rep_guest:
                color = _group_color(rep_guest["side"], grp)
            else:
                color = "#757575"

            net.add_node(
                f"__group__{grp}",
                label=grp,
                color=color,
                size=35,
                shape="diamond",
                title=f"Group: {grp}",
                group=grp,
                x=int(gx), y=int(gy),
            )

    # Rafael's groups: left semicircle (π/2 to 3π/2, i.e. pointing left)
    place_group_nodes(rafael_groups, cx=-400, cy=0, radius=300,
                      arc_start=math.pi * 0.25, arc_end=math.pi * 1.75)

    # Catarina's groups: right semicircle
    place_group_nodes(catarina_groups, cx=400, cy=0, radius=300,
                      arc_start=-math.pi * 0.75, arc_end=math.pi * 0.75)

    # Common groups: between the two, spread vertically
    place_group_nodes(common_groups, cx=0, cy=0, radius=250,
                      arc_start=-math.pi * 0.4, arc_end=math.pi * 0.4)

    # --- Edges: groom/bride → group hubs ---
    added_group_edges: set = set()

    def ensure_group_edge(side, grp):
        key = (side, grp)
        if key not in added_group_edges:
            if side == "Rafael":
                net.add_edge("Rafael", f"__group__{grp}", color="#1E88E5", width=2)
            elif side == "Catarina":
                net.add_edge("Catarina", f"__group__{grp}", color="#E91E63", width=2)
            added_group_edges.add(key)

    for g in guests:
        grp = g["group"]
        if g["side"] == "Common":
            ensure_group_edge("Rafael", grp)
            ensure_group_edge("Catarina", grp)
        else:
            ensure_group_edge(g["side"], grp)

    # --- Guest nodes & edges to their group hub ---
    for guest in guests:
        side = guest["side"]
        grp = guest["group"]
        priority = guest["priority"]

        if side == "Common":
            color = COLOR_SCHEME["Common"].get(grp, "#9C27B0")
        elif side == "Rafael":
            color = COLOR_SCHEME["Rafael"].get(grp, "#2196F3")
        elif side == "Catarina":
            color = COLOR_SCHEME["Catarina"].get(grp, "#E91E63")
        else:
            color = "#757575"

        tooltip = (
            f"<b>{guest['name']}</b><br>"
            f"Side: {side}<br>"
            f"Group: {grp}<br>"
            f"Priority: {priority}<br>"
            f"Notes: {guest['notes'] or 'None'}"
        )

        net.add_node(
            guest["name"],
            label=guest["name"],
            color=color,
            size=PRIORITY_SIZE.get(priority, 20),
            shape=PRIORITY_SHAPE.get(priority, "dot"),
            title=tooltip,
            group=side,
        )

        edge_color = "#9C27B0" if side == "Common" else color
        net.add_edge(f"__group__{grp}", guest["name"], color=edge_color, width=1)

    return net


# Build and display network
if filtered_guests:
    net = build_network(filtered_guests, spring_length, spring_strength, physics_enabled)
    html = net.generate_html()

    # Ensure a working vis-network CDN
    vis_cdn = "https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis-network.min.js"
    html = re.sub(
        r'src="https?://[^"]*vis-network[^"]*"',
        f'src="{vis_cdn}"',
        html,
    )

    st.components.v1.html(html, height=750, scrolling=True)
else:
    st.warning("No guests match the current filters. Try adjusting your filters.")

# =============================================================================
# GUEST TABLE
# =============================================================================

st.divider()
st.subheader("📋 Guest List")

df = pd.DataFrame(filtered_guests)
if not df.empty:
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    df["priority_num"] = df["priority"].map(priority_order)
    df = df.sort_values(["side", "priority_num", "group", "name"]).drop("priority_num", axis=1)

    def color_side(val):
        if val == "Rafael":
            return "background-color: #bbdefb; color: #0d47a1"
        elif val == "Catarina":
            return "background-color: #f8bbd9; color: #ad1457"
        return "background-color: #e1bee7; color: #7b1fa2"

    def color_priority(val):
        if val == "High":
            return "background-color: #c8e6c9; color: #2e7d32"
        elif val == "Medium":
            return "background-color: #fff9c4; color: #f57f17"
        return "background-color: #ffcdd2; color: #c62828"

    styled_df = df.style.map(color_side, subset=["side"]).map(color_priority, subset=["priority"])
    st.dataframe(styled_df, hide_index=True)
else:
    st.info("No guests to display")

# =============================================================================
# FOOTER
# =============================================================================

st.divider()
st.caption("Built by OpenClaw 🦞 | Wedding Guest Network Visualizer  \n💒 Rafael & Catarina - Getting Married!")
