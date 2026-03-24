"""
Wedding Guest Network Visualizer
Interactive D3.js force-directed graph for wedding guest management.
Built by OpenClaw 🦞
"""
# v2.0.0 — D3.js visualization (PyVis removed)

import streamlit as st
import pandas as pd
import json

st.set_page_config(
    page_title="Wedding Guest Network",
    page_icon="💒",
    layout="wide",
)

# =============================================================================
# GUEST DATA
# =============================================================================

def get_initial_guests():
    guests = [
        # Rafael's Family
        {"name": "José (Rafa's Dad)", "side": "Rafael", "group": "Family", "priority": "High", "notes": "Father"},
        {"name": "Ana Maria (Rafa's Mom)", "side": "Rafael", "group": "Family", "priority": "High", "notes": "Mother"},
        {"name": "João Francisco", "side": "Rafael", "group": "Family", "priority": "High", "notes": "Brother"},
        {"name": "Ana Cristima", "side": "Rafael", "group": "Family", "priority": "High", "notes": "Sister"},
        {"name": "Tiago Paula", "side": "Rafael", "group": "Family", "priority": "High", "notes": "Brother-in-law"},
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
        {"name": "Salomé", "side": "Rafael", "group": "University", "priority": "High", "notes": ""},
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
        {"name": "David Vambrout", "side": "Rafael", "group": "Erasmus Milan", "priority": "High", "notes": "Milan, Italy"},
        {"name": "Ann-Kathrin", "side": "Rafael", "group": "Erasmus Milan", "priority": "Medium", "notes": "Milan, Italy"},
        {"name": "Eva", "side": "Rafael", "group": "Erasmus Milan", "priority": "Medium", "notes": "Milan, Italy"},
        # Erasmus Netherlands
        {"name": "Hilde", "side": "Rafael", "group": "Erasmus Netherlands", "priority": "Medium", "notes": "Netherlands"},
        {"name": "Maud", "side": "Rafael", "group": "Erasmus Netherlands", "priority": "Medium", "notes": "Netherlands"},
        {"name": "Staan", "side": "Rafael", "group": "Erasmus Netherlands", "priority": "Medium", "notes": "Netherlands"},
        {"name": "Julie Wallet", "side": "Rafael", "group": "Erasmus Netherlands", "priority": "High", "notes": "+ Ettiene + 2 children"},
        {"name": "Ettiene Wallet", "side": "Rafael", "group": "Erasmus Netherlands", "priority": "High", "notes": "+ Julie + 2 children"},
        {"name": "Vinish Yogesh", "side": "Rafael", "group": "Erasmus Netherlands", "priority": "Medium", "notes": "+ wife"},
        # Work - Planos Ótimos
        {"name": "Rafael Andrade", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Medium", "notes": ""},
        {"name": "Nuno Afonso", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Medium", "notes": ""},
        {"name": "Susana Balhico", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Low", "notes": ""},
        {"name": "Raquel Ganilho", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Low", "notes": ""},
        {"name": "Mariana Ganilho", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Medium", "notes": "+ Duarte Calado"},
        {"name": "Duarte Calado", "side": "Rafael", "group": "Work (Planos Ótimos)", "priority": "Medium", "notes": ""},
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
        {"name": "Leandro Duarte", "side": "Rafael", "group": "Work (Sonant)", "priority": "Low", "notes": ""},
        # Common Friends
        {"name": "Tiago Rodrigues", "side": "Common", "group": "Common Friends", "priority": "High", "notes": "Rafael & Catarina's friend"},
        {"name": "Graça Rodrigues", "side": "Common", "group": "Common Friends", "priority": "High", "notes": "Rafael & Catarina's friend"},
        # Special / Reciprocity
        {"name": "Irmãs Condesso", "side": "Rafael", "group": "Special (Reciprocity)", "priority": "Low", "notes": "Past wedding invite"},
        {"name": "João Araújo", "side": "Rafael", "group": "Special (Reciprocity)", "priority": "Low", "notes": "+ wife"},
        {"name": "Guilherme", "side": "Rafael", "group": "Special (Reciprocity)", "priority": "Low", "notes": "+ Madalena"},
        {"name": "Madalena", "side": "Rafael", "group": "Special (Reciprocity)", "priority": "Low", "notes": ""},
        # Catarina placeholder entries
        {"name": "Catarina's Parents", "side": "Catarina", "group": "Family", "priority": "High", "notes": "To be specified"},
        {"name": "Catarina's Siblings", "side": "Catarina", "group": "Family", "priority": "High", "notes": "To be specified"},
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

def get_color(side, group):
    if side == "Common":
        return COLOR_SCHEME["Common"].get(group, "#9C27B0")
    elif side == "Rafael":
        return COLOR_SCHEME["Rafael"].get(group, "#2196F3")
    elif side == "Catarina":
        return COLOR_SCHEME["Catarina"].get(group, "#E91E63")
    return "#757575"

PRIORITY_SIZE = {"High": 16, "Medium": 11, "Low": 7}

# =============================================================================
# SESSION STATE
# =============================================================================

if "guests" not in st.session_state:
    st.session_state.guests = get_initial_guests()

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.title("💒 Guest Management")

    with st.form("add_guest_form", clear_on_submit=True):
        st.subheader("➕ Add New Guest")
        new_name = st.text_input("Name", placeholder="Full name", label_visibility="collapsed")
        new_side = st.selectbox("Side", ["Rafael", "Catarina", "Common"])
        new_group = st.selectbox("Group", [
            "Family", "Basic School", "Secondary School", "University",
            "Reboleira Parish", "Erasmus Milan", "Erasmus Netherlands",
            "Work (Planos Ótimos)", "Work (Sonant)", "Friends",
            "Common Friends", "Special (Reciprocity)", "Other"
        ])
        new_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        new_notes = st.text_input("Notes", placeholder="Optional notes", label_visibility="collapsed")
        submitted = st.form_submit_button("Add Guest")
        if submitted and new_name:
            st.session_state.guests.append({
                "name": new_name, "side": new_side, "group": new_group,
                "priority": new_priority, "notes": new_notes
            })
            st.success(f"✅ Added {new_name}")

    st.divider()

    st.subheader("🔍 Filters")
    filter_side = st.multiselect("Side", ["Rafael", "Catarina", "Common"],
                                  default=["Rafael", "Catarina", "Common"])
    filter_priority = st.multiselect("Priority", ["High", "Medium", "Low"],
                                      default=["High", "Medium", "Low"])
    all_groups = sorted(set(g["group"] for g in st.session_state.guests))
    filter_group = st.multiselect("Group", all_groups, default=all_groups)

    st.divider()
    st.subheader("📊 Statistics")
    total = len(st.session_state.guests)
    high = len([g for g in st.session_state.guests if g["priority"] == "High"])
    rafael_n = len([g for g in st.session_state.guests if g["side"] == "Rafael"])
    Catarina_n = len([g for g in st.session_state.guests if g["side"] == "Catarina"])
    common_n = len([g for g in st.session_state.guests if g["side"] == "Common"])
    st.metric("Total Guests", total)
    st.metric("High Priority", high)
    col1, col2 = st.columns(2)
    with col1: st.metric("🔵 Rafael", rafael_n)
    with col2: st.metric("🩷 Catarina", Catarina_n)
    st.metric("🟣 Common", common_n)

# =============================================================================
# MAIN
# =============================================================================

st.title("💒 Wedding Guest Network")
st.caption("Interactive social graph — drag nodes to rearrange · hover for details")

filtered_guests = [
    g for g in st.session_state.guests
    if g["side"] in filter_side
    and g["priority"] in filter_priority
    and g["group"] in filter_group
]

st.caption(f"Showing {len(filtered_guests)} of {len(st.session_state.guests)} guests")

# =============================================================================
# D3.JS VISUALIZATION
# =============================================================================

def build_d3_html(guests):
    """Build a self-contained D3.js force-directed graph as an inline HTML string."""

    nodes = []
    links = []

    # Rafael center node
    nodes.append({
        "id": "Rafael", "name": "Rafael", "label": "Rafael",
        "side": "Rafael", "group": "Center", "priority": "High",
        "notes": "Groom", "is_center": True, "size": 26, "color": "#0D47A1"
    })

    # Catarina center node
    nodes.append({
        "id": "Catarina", "name": "Catarina", "label": "Catarina",
        "side": "Catarina", "group": "Center", "priority": "High",
        "notes": "Bride", "is_center": True, "size": 26, "color": "#AD1457"
    })

    # Add guest nodes and links
    for g in guests:
        side = g["side"]
        grp = g["group"]
        size = PRIORITY_SIZE.get(g["priority"], 10)
        color = get_color(side, grp)

        if side == "Common":
            links.append({"source": g["name"], "target": "Rafael", "color": "#9C27B0", "width": 1.5})
            links.append({"source": g["name"], "target": "Catarina", "color": "#9C27B0", "width": 1.5})
        elif side == "Rafael":
            links.append({"source": g["name"], "target": "Rafael", "color": "#1E88E5", "width": 1})
        elif side == "Catarina":
            links.append({"source": g["name"], "target": "Catarina", "color": "#E91E63", "width": 1})

        nodes.append({
            "id": g["name"], "name": g["name"], "label": g["name"],
            "side": side, "group": grp, "priority": g["priority"],
            "notes": g["notes"], "is_center": False, "size": size, "color": color
        })

    nodes_json = json.dumps(nodes)
    links_json = json.dumps(links)

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #0E1117; font-family: 'Segoe UI', Arial, sans-serif; overflow: hidden; }}
    svg {{ width: 100%; height: 100vh; display: block; }}
    .link {{ stroke-opacity: 0.55; fill: none; }}
    .node circle {{ stroke: rgba(255,255,255,0.25); stroke-width: 1.5px; cursor: grab; transition: stroke 0.2s; }}
    .node circle:hover {{ stroke: white; stroke-width: 2.5px; }}
    .node text {{ font-size: 9px; fill: #cccccc; pointer-events: none; text-anchor: middle; dominant-baseline: middle; font-weight: 500; text-shadow: 0 1px 4px rgba(0,0,0,0.9); }}
    .node.center circle {{ stroke: rgba(255,255,255,0.7); stroke-width: 3px; cursor: default; }}
    .node.center text {{ font-size: 12px; font-weight: 700; fill: white; }}
    #tooltip {{ position: fixed; background: rgba(14,14,24,0.97); border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; padding: 10px 14px; font-size: 12px; color: #e0e0e0; pointer-events: none; opacity: 0; transition: opacity 0.15s; z-index: 9999; max-width: 240px; box-shadow: 0 4px 24px rgba(0,0,0,0.6); line-height: 1.6; }}
    #tooltip b {{ color: white; font-size: 13px; }}
    .tip-side {{ display: block; margin-bottom: 3px; font-weight: 600; }}
    .tip-hi {{ color: #4CAF50; }} .tip-med {{ color: #FFC107; }} .tip-lo {{ color: #f44336; }}
    #legend {{ position: fixed; bottom: 14px; left: 14px; background: rgba(14,17,23,0.88); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 10px 14px; font-size: 11px; color: #b0b0b0; z-index: 999; }}
    .leg-title {{ font-weight: 700; color: white; margin-bottom: 6px; font-size: 12px; }}
    .leg-item {{ display: flex; align-items: center; gap: 6px; margin-bottom: 3px; }}
    .leg-dot {{ width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }}
    .leg-line {{ width: 18px; height: 2px; border-radius: 1px; flex-shrink: 0; }}
  </style>
</head>
<body>
  <svg id="graph"></svg>
  <div id="tooltip">
    <span class="tip-side" id="tt-side"></span>
    <b id="tt-name"></b><br>
    <span id="tt-group"></span><br>
    Priority: <span id="tt-priority"></span><br>
    <span id="tt-notes"></span>
  </div>
  <div id="legend">
    <div class="leg-title">Legend</div>
    <div class="leg-item"><div class="leg-dot" style="background:#0D47A1"></div> Rafael (Groom)</div>
    <div class="leg-item"><div class="leg-dot" style="background:#AD1457"></div> Catarina (Bride)</div>
    <div class="leg-item"><div class="leg-dot" style="background:#9C27B0"></div> Common Friends</div>
    <div class="leg-item"><div class="leg-line" style="background:#1E88E5"></div> Rafael's connection</div>
    <div class="leg-item"><div class="leg-line" style="background:#E91E63"></div> Catarina's connection</div>
    <div class="leg-item"><div class="leg-line" style="background:#9C27B0"></div> Common friend link</div>
  </div>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
  <script>
    const nodes = {nodes_json};
    const links = {links_json};

    const W = window.innerWidth;
    const H = window.innerHeight;

    // Fixed center positions for the couple
    const rafaelX = W * 0.3;
    const CatarinaX = W * 0.7;
    const centerY = H / 2;

    const allNodes = nodes.map(n => {{
      if (n.id === 'Rafael') {{ n.fx = rafaelX; n.fy = centerY; }}
      else if (n.id === 'Catarina') {{ n.fx = CatarinaX; n.fy = centerY; }}
      return n;
    }});

    const nodeMap = {{}};
    allNodes.forEach(n => nodeMap[n.id] = n);

    const svg = d3.select("#graph");

    const simulation = d3.forceSimulation(allNodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(d => d.source.id === 'Rafael' || d.source.id === 'Catarina' ? 140 : 65).strength(0.4))
      .force("charge", d3.forceManyBody().strength(d => d.is_center ? -900 : -100).distanceMax(350))
      .force("center", d3.forceCenter(W / 2, H / 2).strength(0.04))
      .force("collision", d3.forceCollide().radius(d => d.size + 10).strength(0.7))
      .force("x", d3.forceX(W / 2).strength(d => d.is_center ? 0.25 : 0.015))
      .force("y", d3.forceY(H / 2).strength(d => d.is_center ? 0.08 : 0.008))
      .alphaDecay(0.018)
      .velocityDecay(0.35);

    const link = svg.append("g").selectAll("line").data(links).join("line")
      .attr("class", "link")
      .attr("stroke", d => d.color || "#888")
      .attr("stroke-width", d => d.width || 1);

    const node = svg.append("g").selectAll("g").data(allNodes).join("g")
      .attr("class", d => "node" + (d.is_center ? " center" : ""))
      .call(d3.drag()
        .on("start", (e, d) => {{ if (!d.is_center) {{ if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }} }})
        .on("drag", (e, d) => {{ if (!d.is_center) {{ d.fx = e.x; d.fy = e.y; }} }})
        .on("end", (e, d) => {{ if (!d.is_center) {{ if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }} }})
      );

    node.append("circle")
      .attr("r", d => d.size || 6)
      .attr("fill", d => d.color || "#888")
      .style("filter", d => d.is_center ? "drop-shadow(0 0 8px rgba(255,255,255,0.35))" : "none");

    node.append("text")
      .attr("dy", d => (d.size || 6) + 11)
      .text(d => d.label.length > 18 ? d.label.substring(0, 16) + "…" : d.label);

    const tooltip = document.getElementById("tooltip");
    const ttSide = document.getElementById("tt-side");
    const ttName = document.getElementById("tt-name");
    const ttGroup = document.getElementById("tt-group");
    const ttPriority = document.getElementById("tt-priority");
    const ttNotes = document.getElementById("tt-notes");

    node.on("mouseover", function(event, d) {{
      tooltip.style.opacity = "1";
      const pClass = d.priority === 'High' ? 'tip-hi' : d.priority === 'Medium' ? 'tip-med' : 'tip-lo';
      const emoji = d.side === 'Rafael' ? '🔵' : d.side === 'Catarina' ? '🩷' : '🟣';
      const sideColor = d.side === 'Rafael' ? '#1E88E5' : d.side === 'Catarina' ? '#E91E63' : '#9C27B0';
      ttSide.textContent = emoji + " " + d.side;
      ttSide.style.color = sideColor;
      ttName.textContent = d.name;
      ttGroup.textContent = "Group: " + d.group;
      ttPriority.textContent = d.priority;
      ttPriority.className = pClass;
      ttNotes.textContent = d.notes ? "Notes: " + d.notes : "";
    }})
    .on("mousemove", function(event) {{
      tooltip.style.left = (event.pageX + 14) + "px";
      tooltip.style.top = (event.pageY - 10) + "px";
    }})
    .on("mouseout", function() {{ tooltip.style.opacity = "0"; }});

    simulation.on("tick", () => {{
      link
        .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
      node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
    }});

    window.addEventListener("resize", () => {{
      const w = window.innerWidth, h = window.innerHeight;
      simulation.force("center", d3.forceCenter(w / 2, h / 2).strength(0.04));
      allNodes.forEach(n => {{
        if (n.id === 'Rafael') {{ n.fx = w * 0.3; n.fy = h / 2; }}
        else if (n.id === 'Catarina') {{ n.fx = w * 0.7; n.fy = h / 2; }}
      }});
      simulation.alpha(0.25).restart();
    }});
  </script>
</body>
</html>"""
    return html

if filtered_guests:
    d3_html = build_d3_html(filtered_guests)
    st.components.v1.html(d3_html, height=700, scrolling=False)
else:
    st.warning("No guests match the current filters.")

# =============================================================================
# GUEST TABLE
# =============================================================================

st.divider()
st.subheader("📋 Guest List")

df = pd.DataFrame(filtered_guests)
if not df.empty:
    p_order = {"High": 0, "Medium": 1, "Low": 2}
    df["_p"] = df["priority"].map(p_order)
    df = df.sort_values(["side", "_p", "group", "name"]).drop("_p", axis=1)

    def color_side(val):
        if val == "Rafael": return "background:#bbdefb; color:#0d47a1"
        if val == "Catarina": return "background:#f8bbd9; color:#ad1457"
        return "background:#e1bee7; color:#7b1fa2"
    def color_priority(val):
        if val == "High": return "background:#c8e6c9; color:#2e7d32"
        if val == "Medium": return "background:#fff9c4; color:#f57f17"
        return "background:#ffcdd2; color:#c62828"

    styled = df.style.map(color_side, subset=["side"]).map(color_priority, subset=["priority"])
    st.dataframe(styled, hide_index=True)
else:
    st.info("No guests to display")

st.divider()
st.caption("💒 Built by OpenClaw 🦞 | Rafael & Catarina | v2.0.0 — D3.js visualization")
