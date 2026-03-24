"""
Wedding Guest Network Visualizer
Interactive social graph of wedding guests clustered by relationship groups.
Built by OpenClaw 🦞
"""
# v1.0.0 — Initial release

import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
from datetime import datetime
import io

st.set_page_config(
    page_title="Wedding Guest Network",
    page_icon="💒",
    layout="wide",
)

# =============================================================================
# GUEST DATA (initialized from GUEST_LIST.md)
# =============================================================================

def get_initial_guests():
    """Initial guest data from GUEST_LIST.md"""
    guests = [
        # Rafael's Family
        {"name": "José (Rafa's Dad)", "side": "Rafael", "group": "Family", "priority": "High", "notes": "Father"},
        {"name": "Ana Maria (Rafa's Mom)", "side": "Rafael", "group": "Family", "priority": "High", "notes": "Mother"},
        {"name": "João Francisco", "side": "Rafael", "group": "Family", "priority": "High", "notes": "Brother"},
        {"name": "Ana Cristima", "side": "Rafael", "group": "Family", "priority": "High", "notes": "Sister"},
        {"name": "Tiago Paula", "side": "Rafael", "group": "Family", "priority": "High", "notes": "Brother-in-law (expected spouse of Ana Cristima)"},
        {"name": "Tia Luz", "side": "Rafael", "group": "Family", "priority": "Medium", "notes": ""},
        {"name": "Joao Pedro", "side": "Rafael", "group": "Family", "priority": "Medium", "notes": "Cousin"},
        {"name": "Madalena", "side": "Rafael", "group": "Family", "priority": "Medium", "notes": "Cousin"},
        {"name": "Tio Luis", "side": "Rafael", "group": "Family", "priority": "Medium", "notes": ""},
        {"name": "Teresa", "side": "Rafael", "group": "Family", "priority": "Medium", "notes": ""},
        {"name": "Deicy", "side": "Rafael", "group": "Family", "priority": "Low", "notes": "Cousin"},
        
        # Rafael's Friends - Basic School
        {"name": "Jeenal", "side": "Rafael", "group": "Basic School", "priority": "Medium", "notes": ""},
        {"name": "João Carlos", "side": "Rafael", "group": "Basic School", "priority": "Medium", "notes": ""},
        {"name": "Bruno", "side": "Rafael", "group": "Basic School", "priority": "High", "notes": "+ Tânia (plus-one)"},
        {"name": "Tânia", "side": "Rafael", "group": "Basic School", "priority": "Medium", "notes": "Plus-one of Bruno"},
        {"name": "Sofia Cotrim", "side": "Rafael", "group": "Basic School", "priority": "Medium", "notes": ""},
        {"name": "Tiago Luzio", "side": "Rafael", "group": "Basic School", "priority": "Medium", "notes": ""},
        
        # Rafael's Friends - Secondary School
        {"name": "André Miranda", "side": "Rafael", "group": "Secondary School", "priority": "High", "notes": ""},
        
        # Rafael's Friends - University
        {"name": "Manuel Madeira", "side": "Rafael", "group": "University", "priority": "High", "notes": ""},
        {"name": "Tiago Rodrigues", "side": "Rafael", "group": "University", "priority": "High", "notes": "Also common friend"},
        {"name": "Salomé", "side": "Rafael", "group": "University", "priority": "High", "notes": "+ boyfriend (Carlota's boyfriend)"},
        {"name": "Carlota Santos", "side": "Rafael", "group": "University", "priority": "High", "notes": "+ boyfriend"},
        {"name": "Margarida Pinho", "side": "Rafael", "group": "University", "priority": "Medium", "notes": ""},
        {"name": "Margarida Lopes", "side": "Rafael", "group": "University", "priority": "Medium", "notes": ""},
        {"name": "Maria Folque", "side": "Rafael", "group": "University", "priority": "High", "notes": ""},
        
        # Rafael's Friends - Reboleira/Parish
        {"name": "Inês Viegas", "side": "Rafael", "group": "Reboleira Parish", "priority": "Medium", "notes": ""},
        {"name": "Sara Miranda", "side": "Rafael", "group": "Reboleira Parish", "priority": "Medium", "notes": "+ boyfriend"},
        {"name": "Beatriz Quaresma", "side": "Rafael", "group": "Reboleira Parish", "priority": "Medium", "notes": ""},
        {"name": "João Roberto", "side": "Rafael", "group": "Reboleira Parish", "priority": "Low", "notes": ""},
        
        # Erasmus Milan
        {"name": "David Vambrout", "side": "Rafael", "group": "Erasmus Milan", "priority": "High", "notes": "Erasmus in Milan, Italy"},
        {"name": "Ann-Kathrin", "side": "Rafael", "group": "Erasmus Milan", "priority": "Medium", "notes": "Erasmus in Milan, Italy"},
        {"name": "Eva", "side": "Rafael", "group": "Erasmus Milan", "priority": "Medium", "notes": "Erasmus in Milan, Italy"},
        
        # Erasmus Netherlands
        {"name": "Hilde", "side": "Rafael", "group": "Erasmus Netherlands", "priority": "Medium", "notes": "Erasmus in Netherlands"},
        {"name": "Maud", "side": "Rafael", "group": "Erasmus Netherlands", "priority": "Medium", "notes": "Erasmus in Netherlands"},
        {"name": "Staan", "side": "Rafael", "group": "Erasmus Netherlands", "priority": "Medium", "notes": "Erasmus in Netherlands"},
        {"name": "Julie Wallet", "side": "Rafael", "group": "Erasmus Netherlands", "priority": "High", "notes": "Erasmus in Netherlands, + Ettiene Wallet, + 2 children"},
        {"name": "Ettiene Wallet", "side": "Rafael", "group": "Erasmus Netherlands", "priority": "High", "notes": "Erasmus in Netherlands, + Julie Wallet, + 2 children"},
        {"name": "Vinish Yogesh", "side": "Rafael", "group": "Erasmus Netherlands", "priority": "Medium", "notes": "Erasmus in Netherlands, + wife"},
        
        # Work - Planos Ótimos
        {"name": "Rafael Andrade", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Medium", "notes": ""},
        {"name": "Nuno Afonso", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Medium", "notes": ""},
        {"name": "Susana Balhico", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Low", "notes": ""},
        {"name": "Raquel Ganilho", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Low", "notes": ""},
        {"name": "Mariana Ganilho", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Medium", "notes": "+ Duarte Calado"},
        {"name": "Duarte Calado", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Medium", "notes": "+ Mariana Ganilho"},
        {"name": "Isabel Gala", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Low", "notes": ""},
        {"name": "José Mesquita Guimarães", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Low", "notes": ""},
        {"name": "Rafael Mesquita Guimarães", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Low", "notes": ""},
        {"name": "Maria Mesquita Guimarães", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Low", "notes": ""},
        {"name": "Beatriz Barros", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Low", "notes": ""},
        {"name": "Mariana Camarneiro", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Low", "notes": ""},
        {"name": "Sofia Camarneiro", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Low", "notes": ""},
        {"name": "Bernardo Neuville", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Low", "notes": ""},
        {"name": "Jaona Silvano", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Low", "notes": ""},
        {"name": "Leonor Freitas do Amaral", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Low", "notes": ""},
        {"name": "Luis Tovar", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Low", "notes": ""},
        {"name": "Miguel Sousa", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Low", "notes": ""},
        {"name": "Miriam Sculco", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Low", "notes": ""},
        {"name": "Maria Ana Pacheco", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Low", "notes": ""},
        
        # Work - Sonant
        {"name": "Zé Pedro Cruz Fernandes", "side": "Rafael", "group": "Work (Sonant)", "priority": "Medium", "notes": ""},
        {"name": "Pedro Correia", "side": "Rafael", "group": "Work (Sonant)", "priority": "Medium", "notes": ""},
        {"name": "Pedro Henriques", "side": "Rafael", "group": "Work (Sonant)", "priority": "Medium", "notes": ""},
        {"name": "Juliana Vareda", "side": "Rafael", "group": "Work (Sonant)", "priority": "Low", "notes": ""},
        {"name": "Gonçalo Canhoto", "side": "Rafael", "group": "Work (Sonant)", "priority": "Low", "notes": ""},
        {"name": "Leandro Duarte", "side": "Rafael", "group": "Work (Sonant)", "priority": "Low", "notes": "Uncertain attendance"},
        
        # Common Friends
        {"name": "Tiago Rodrigues", "side": "Common", "group": "Common Friends", "priority": "High", "notes": "Rafael & Catarina's friend"},
        {"name": "Graça Rodrigues", "side": "Common", "group": "Common Friends", "priority": "High", "notes": "Rafael & Catarina's friend"},
        
        # Special / Reciprocity
        {"name": "Irmãs Condesso", "side": "Rafael", "group": "Special (Reciprocity)", "priority": "Low", "notes": "Past wedding invite"},
        {"name": "João Araújo", "side": "Rafael", "group": "Special (Reciprocity)", "priority": "Low", "notes": "Past wedding invite, + wife"},
        {"name": "Guilherme", "side": "Rafael", "group": "Special (Reciprocity)", "priority": "Low", "notes": "Past wedding invite, + Madalena"},
        {"name": "Madalena", "side": "Rafael", "group": "Special (Reciprocity)", "priority": "Low", "notes": "Past wedding invite, + Guilherme"},
        
        # Catarina's Family (placeholder - to be filled)
        {"name": "Catarina's Parents", "side": "Catarina", "group": "Family", "priority": "High", "notes": "To be specified"},
        {"name": "Catarina's Siblings", "side": "Catarina", "group": "Family", "priority": "High", "notes": "To be specified"},
        
        # Catarina's Friends (placeholder - to be filled)
        {"name": "Catarina's Friend 1", "side": "Catarina", "group": "Friends", "priority": "Medium", "notes": "To be specified"},
        {"name": "Catarina's Friend 2", "side": "Catarina", "group": "Friends", "priority": "Medium", "notes": "To be specified"},
        {"name": "Catarina's University Friends", "side": "Catarina", "group": "University", "priority": "Medium", "notes": "To be specified"},
        {"name": "Catarina's Work Friends", "side": "Catarina", "group": "Work", "priority": "Low", "notes": "To be specified"},
    ]
    return guests

# =============================================================================
# COLOR SCHEME
# =============================================================================

COLOR_SCHEME = {
    "Rafael": {
        "Family": "#1E88E5",          # Blue
        "Basic School": "#42A5F5",    # Light blue
        "Secondary School": "#2196F3", # Blue
        "University": "#1976D2",      # Dark blue
        "Reboleira Parish": "#64B5F6", # Light blue
        "Erasmus Milan": "#0D47A1",   # Dark blue
        "Erasmus Netherlands": "#1565C0", # Dark blue
        "Work (Planos Ótimos)": "#90CAF9", # Very light blue
        "Work (Sonant)": "#BBDEFB",   # Pale blue
        "Special (Reciprocity)": "#3F51B5", # Indigo
    },
    "Catarina": {
        "Family": "#E91E63",          # Pink
        "Friends": "#F48FB1",         # Light pink
        "University": "#D81B60",      # Dark pink
        "Work": "#F8BBD9",            # Pale pink
    },
    "Common": {
        "Common Friends": "#9C27B0",  # Purple
    }
}

# Node shape by priority
PRIORITY_SHAPE = {
    "High": "star",
    "Medium": "dot",
    "Low": "dot"
}

PRIORITY_SIZE = {
    "High": 40,
    "Medium": 25,
    "Low": 15
}

# =============================================================================
# SESSION STATE
# =============================================================================

if "guests" not in st.session_state:
    st.session_state.guests = get_initial_guests()

# =============================================================================
# SIDEBAR: ADD GUEST FORM & FILTERS
# =============================================================================

with st.sidebar:
    st.title("💒 Guest Management")
    
    # Add New Guest Form
    st.subheader("➕ Add New Guest")
    with st.form("add_guest_form", clear_on_submit=True):
        new_name = st.text_input("Name", placeholder="Full name")
        new_side = st.selectbox("Side", ["Rafael", "Catarina", "Common"])
        new_group = st.selectbox(
            "Group",
            [
                "Family",
                "Basic School",
                "Secondary School", 
                "University",
                "Reboleira Parish",
                "Erasmus Milan",
                "Erasmus Netherlands",
                "Work (Planos Ótimos)",
                "Work (Sonant)",
                "Friends",
                "Common Friends",
                "Special (Reciprocity)",
                "Other"
            ]
        )
        new_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        new_notes = st.text_input("Notes (plus-ones, etc.)", placeholder="Optional notes")
        
        submitted = st.form_submit_button("Add Guest")
        if submitted and new_name:
            st.session_state.guests.append({
                "name": new_name,
                "side": new_side,
                "group": new_group,
                "priority": new_priority,
                "notes": new_notes
            })
            st.success(f"✅ Added {new_name}")
    
    st.divider()
    
    # Filters
    st.subheader("🔍 Filters")
    
    filter_side = st.multiselect(
        "Filter by Side",
        ["Rafael", "Catarina", "Common"],
        default=["Rafael", "Catarina", "Common"]
    )
    
    filter_priority = st.multiselect(
        "Filter by Priority",
        ["High", "Medium", "Low"],
        default=["High", "Medium", "Low"]
    )
    
    filter_group = st.multiselect(
        "Filter by Group",
        list(set(g["group"] for g in st.session_state.guests)),
        default=list(set(g["group"] for g in st.session_state.guests))
    )
    
    # Physics controls
    st.subheader("⚙️ Graph Physics")
    physics_enabled = st.checkbox("Enable Physics (draggable)", value=True)
    if physics_enabled:
        spring_length = st.slider("Spring Length", 50, 300, 150)
        spring_strength = st.slider("Spring Strength", 0.001, 0.1, 0.01)
    else:
        spring_length = 150
        spring_strength = 0.01
    
    st.divider()
    
    # Stats
    st.subheader("📊 Statistics")
    total_guests = len(st.session_state.guests)
    high_priority = len([g for g in st.session_state.guests if g["priority"] == "High"])
    st.metric("Total Guests", total_guests)
    st.metric("High Priority", high_priority)

# =============================================================================
# MAIN CONTENT
# =============================================================================

st.title("💒 Wedding Guest Network")
st.markdown("*Interactive social graph for visualizing and organizing wedding guests*")

# Filter guests
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

def build_network(guests, spring_length=150, spring_strength=0.01, physics=True):
    """Build PyVis network from guest data"""
    
    net = Network(
        height="700px",
        width="100%",
        bgcolor="#1e1e1e",
        font_color="white",
        directed=False,
        notebook=False,
        select_menu=True,
        filter_menu=True,
    )
    
    # Physics settings
    if physics:
        net.set_options(f"""
        {{
            "nodes": {{
                "borderWidth": 2,
                "borderWidthSelected": 4,
                "font": {{"size": 14, "face": "arial"}}
            }},
            "edges": {{
                "color": {{"inherit": true}},
                "smooth": {{"type": "continuous"}}
            }},
            "physics": {{
                "enabled": true,
                "forceAtlas2Based": {{
                    "gravitationalConstant": -50,
                    "centralGravity": 0.01,
                    "springLength": {spring_length},
                    "springConstant": {spring_strength},
                    "damping": 0.4
                }},
                "minVelocity": 0.75,
                "solver": "forceAtlas2Based"
            }}
        }}
        """)
    else:
        net.set_options(f"""
        {{
            "nodes": {{
                "borderWidth": 2,
                "borderWidthSelected": 4,
                "font": {{"size": 14, "face": "arial"}}
            }},
            "edges": {{
                "color": {{"inherit": true}},
                "smooth": {{"type": "continuous"}}
            }},
            "physics": {{
                "enabled": false
            }}
        }}
        """)
    
    # Add Rafael hub (center-left)
    net.add_node("Rafael", label="Rafael\n(Groom)", 
                 color="#0D47A1", size=60, shape="star", 
                 title="Rafael - Groom", group="Rafael")
    
    # Add Catarina hub (center-right)
    net.add_node("Catarina", label="Catarina\n(Bride)", 
                 color="#AD1457", size=60, shape="star", 
                 title="Catarina - Bride", group="Catarina")
    
    # Group guests by cluster
    groups = {}
    for guest in guests:
        group = guest["group"]
        if group not in groups:
            groups[group] = []
        groups[group].append(guest)
    
    # Position clusters around the two centers
    rafael_groups = ["Family", "Basic School", "Secondary School", "University", 
                     "Reboleira Parish", "Erasmus Milan", "Erasmus Netherlands",
                     "Work (Planos Ótimos)", "Work (Sonant)", "Special (Reciprocity)"]
    catarina_groups = ["Friends", "Work"]
    
    # Add guest nodes
    for guest in guests:
        side = guest["side"]
        group = guest["group"]
        priority = guest["priority"]
        
        # Get color based on side and group
        if side == "Common":
            color = COLOR_SCHEME["Common"].get(group, "#9C27B0")
        elif side == "Rafael":
            color = COLOR_SCHEME["Rafael"].get(group, "#2196F3")
        elif side == "Catarina":
            color = COLOR_SCHEME["Catarina"].get(group, "#E91E63")
        else:
            color = "#757575"
        
        # Build tooltip
        tooltip = f"""
        <b>{guest['name']}</b><br>
        Side: {guest['side']}<br>
        Group: {guest['group']}<br>
        Priority: {guest['priority']}<br>
        Notes: {guest['notes'] if guest['notes'] else 'None'}
        """
        
        net.add_node(
            guest["name"],
            label=guest["name"],
            color=color,
            size=PRIORITY_SIZE.get(priority, 20),
            shape=PRIORITY_SHAPE.get(priority, "dot"),
            title=tooltip,
            group=side
        )
        
        # Connect to Rafael or Catarina or both (Common)
        if side == "Rafael":
            net.add_edge(guest["name"], "Rafael", color="#1E88E5", width=1)
        elif side == "Catarina":
            net.add_edge(guest["name"], "Catarina", color="#E91E63", width=1)
        elif side == "Common":
            # Connect to both with purple edges
            net.add_edge(guest["name"], "Rafael", color="#9C27B0", width=2)
            net.add_edge(guest["name"], "Catarina", color="#9C27B0", width=2)
    
    return net

# Build and display network
if filtered_guests:
    net = build_network(filtered_guests, spring_length, spring_strength, physics_enabled)
    
    # Generate HTML - embed vis.js CDN for better compatibility
    html = net.generate_html(notebook=False, open=False)
    
    # Inject vis.js CDN for Streamlit Cloud compatibility
    if "cdnjs" in html or "unpkg" in html or "jsdelivr" in html:
        # Replace any existing CDN links with a reliable one
        html = html.replace(
            'src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"',
            'src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis-network.min.js"'
        )
    
    # Display in Streamlit using st.html (available in Streamlit 1.27+)
    st.html(html)
else:
    st.warning("No guests match the current filters. Try adjusting your filters.")

# =============================================================================
# GUEST TABLE
# =============================================================================

st.divider()
st.subheader("📋 Guest List")

# Create DataFrame for display
df = pd.DataFrame(filtered_guests)
if not df.empty:
    # Sort by side, then priority, then group
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    df["priority_num"] = df["priority"].map(priority_order)
    df = df.sort_values(["side", "priority_num", "group", "name"])
    df = df.drop("priority_num", axis=1)
    
    # Color function for side column
    def color_side(val):
        if val == "Rafael":
            return "background-color: #bbdefb; color: #0d47a1"
        elif val == "Catarina":
            return "background-color: #f8bbd9; color: #ad1457"
        else:
            return "background-color: #e1bee7; color: #7b1fa2"
    
    def color_priority(val):
        if val == "High":
            return "background-color: #c8e6c9; color: #2e7d32"
        elif val == "Medium":
            return "background-color: #fff9c4; color: #f57f17"
        else:
            return "background-color: #ffcdd2; color: #c62828"
    
    # Build styled dataframe (using .map instead of deprecated .applymap)
    styled_df = df.style.map(color_side, subset=["side"]).map(color_priority, subset=["priority"])
    
    # Display styled dataframe
    st.dataframe(styled_df, hide_index=True)
else:
    st.info("No guests to display")

# =============================================================================
# FOOTER
# =============================================================================

st.divider()
st.caption("""
Built by OpenClaw 🦞 | Wedding Guest Network Visualizer  
💒 Rafael & Catarina - Getting Married!
""")
