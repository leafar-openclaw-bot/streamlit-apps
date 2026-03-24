"""
Wedding Guest Network Visualizer v3
D3.js force graph with group cluster nodes (squares) + bidirectional selection.
Built by OpenClaw 🦞
"""
# v3.3.0 — Floating node edit panel; guest data loaded from guests.json

import json
import math
import pathlib
import streamlit as st
import pandas as pd

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

def get_group_color(g):
    return GROUP_COLORS.get(g, "#757575")

PRIORITY_SIZE = {"High": 14, "Medium": 10, "Low": 6}

ALL_GROUPS = sorted([
    "Family", "Basic School", "Secondary School", "University",
    "Reboleira Parish", "Erasmus Milan", "Erasmus Netherlands",
    "Work (Planos Ótimos)", "Work (Sonant)", "Special (Reciprocity)",
    "Friends", "Common Friends", "Work", "Other"
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

    # Add Guest
    with st.form("add_guest_form", clear_on_submit=True):
        st.subheader("➕ Add New Guest")
        new_name = st.text_input("Name", placeholder="Full name", label_visibility="collapsed")
        new_side = st.selectbox("Side", ["Rafael", "Catarina", "Common"])
        new_groups = st.multiselect("Groups", ALL_GROUPS, default=["Family"])
        new_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        new_notes = st.text_input("Notes", placeholder="Optional notes", label_visibility="collapsed")
        add_submitted = st.form_submit_button("Add Guest")
        if add_submitted and new_name:
            names = [g["name"] for g in st.session_state.guests]
            if new_name in names:
                st.error(f"⚠️ {new_name} already exists!")
            else:
                st.session_state.guests.append({
                    "name": new_name, "side": new_side, "groups": new_groups,
                    "priority": new_priority, "notes": new_notes
                })
                st.success(f"✅ Added {new_name}")

        # Hidden signals from D3 floating edit panel
        guest_signal = st.text_input("Guest signal (from graph)", value="",
                                      label_visibility="hidden", key="guest_signal",
                                      args=(), kwargs={})
        edit_data = st.text_area("Edit data (from floating panel)", value="",
                                  label_visibility="hidden", key="edit_data",
                                  args=(), kwargs={})

        # Process floating panel save action
        if edit_data:
            try:
                edit = json.loads(edit_data)
                if edit.get("action") == "save_edit":
                    original_name = edit.get("originalName")
                    real = next((g for g in st.session_state.guests if g["name"] == original_name), None)
                    if real:
                        real["priority"] = edit.get("priority", "Medium")
                        real["groups"] = edit.get("groups", real["groups"])
                        real["notes"] = edit.get("notes", "")
                        st.session_state.selected_guest = None
                        st.rerun()
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        # Process graph node click → set selected guest
        if guest_signal and not edit_data:
            found = next((g for g in st.session_state.guests if g["name"] == guest_signal.strip()), None)
            if found:
                st.session_state.selected_guest = found
                # Clear the signal so it doesn't re-trigger
                st.session_state["guest_signal"] = ""

    st.divider()

    # Filters
    st.subheader("🔍 Filters")
    filter_side = st.multiselect("Side", ["Rafael", "Catarina", "Common"],
                                  default=["Rafael", "Catarina", "Common"])
    filter_priority = st.multiselect("Priority", ["High", "Medium", "Low"],
                                     default=["High", "Medium", "Low"])
    filter_group = st.multiselect("Group", ALL_GROUPS, default=ALL_GROUPS)

    st.divider()

    # Stats
    st.subheader("📊 Statistics")
    total = len(st.session_state.guests)
    high = len([g for g in st.session_state.guests if g["priority"] == "High"])
    rafael_n = len([g for g in st.session_state.guests if g["side"] == "Rafael"])
    Catarina_n = len([g for g in st.session_state.guests if g["side"] == "Catarina"])
    common_n = len([g for g in st.session_state.guests if g["side"] == "Common"])
    st.metric("Total", total)
    st.metric("High Priority", high)
    col1, col2 = st.columns(2)
    with col1: st.metric("🔵 Rafael", rafael_n)
    with col2: st.metric("🩷 Catarina", Catarina_n)
    st.metric("🟣 Common", common_n)

    st.divider()

    # Edit Panel
    selected = st.session_state.selected_guest
    if selected:
        st.subheader(f"✏️ Edit: {selected['name']}")
        real = next((g for g in st.session_state.guests if g["name"] == selected["name"]), None)
        if real:
            with st.form("edit_form", clear_on_submit=True):
                edit_priority = st.selectbox("Priority", ["High", "Medium", "Low"],
                                              index=["High", "Medium", "Low"].index(real["priority"]))
                edit_groups = st.multiselect("Groups", ALL_GROUPS, default=real["groups"])
                edit_notes = st.text_input("Notes", value=real["notes"], label_visibility="collapsed")
                c1, c2 = st.columns(2)
                save_btn = c1.form_submit_button("💾 Save")
                del_btn = c2.form_submit_button("🗑️ Delete", type="secondary")
                if save_btn:
                    real["priority"] = edit_priority
                    real["groups"] = edit_groups
                    real["notes"] = edit_notes
                    st.success("💾 Saved!")
                    st.session_state.selected_guest = None
                    st.rerun()
                if del_btn:
                    st.session_state.guests = [g for g in st.session_state.guests if g["name"] != real["name"]]
                    st.success(f"🗑️ Deleted {real['name']}")
                    st.session_state.selected_guest = None
                    st.rerun()
        else:
            st.warning("Guest not found.")
            if st.button("Clear selection"):
                st.session_state.selected_guest = None
                st.rerun()
    else:
        st.subheader("✏️ Edit Guest")
        st.caption("Click a node or row to edit")

# =============================================================================
# MAIN
# =============================================================================

st.title("💒 Wedding Guest Network")
st.caption("🟠 Squares = social life events (fixed clusters) · ● Circles = people (draggable) · Click to select & edit")

# Filter
filtered = [
    g for g in st.session_state.guests
    if g["side"] in filter_side
    and g["priority"] in filter_priority
    and any(grp in filter_group for grp in g["groups"])
]

hl = st.session_state.selected_guest
st.caption(f"Showing {len(filtered)} of {len(st.session_state.guests)} guests")

# =============================================================================
# D3 VISUALIZATION
# =============================================================================

def build_d3(guests, highlighted_name):
    nodes = []
    links = []
    group_ids = []

    # Centers
    nodes.append({"id": "__Rafael__", "name": "Rafael", "label": "Rafael",
                  "type": "center", "side": "Rafael", "groups": [],
                  "priority": "High", "notes": "Groom",
                  "size": 32, "color": "#0D47A1"})
    nodes.append({"id": "__Catarina__", "name": "Catarina", "label": "Catarina",
                  "type": "center", "side": "Catarina", "groups": [],
                  "priority": "High", "notes": "Bride",
                  "size": 32, "color": "#AD1457"})

    # Groups
    all_grps = sorted(set(grp for g in guests for grp in g["groups"]))
    rafael_grps = [g for g in all_grps if g not in ["Friends", "Work", "Common Friends"]]
    Catarina_grps = [g for g in all_grps if g in ["Friends", "Work"]]
    common_grps = [g for g in all_grps if "Common" in g]

    def fan_placement(groups_list, cx_ratio, cy, radius, start_a=-65, end_a=65):
        result = {}
        for i, g in enumerate(groups_list):
            angle = start_a + (i / max(len(groups_list) - 1, 1)) * (end_a - start_a)
            rad = math.pi * (0.5 + angle / 180)
            result[g] = {"xr": cx_ratio, "yr": cy, "r": radius, "angle": angle}
        return result

    rafael_fan = fan_placement(rafael_grps, 0.22, 0.52, 210)
    Catarina_fan = fan_placement(Catarina_grps, 0.78, 0.52, 190)
    common_fan = {"Common Friends": {"xr": 0.5, "yr": 0.18, "r": 0, "angle": 0}}

    all_fans = {**rafael_fan, **Catarina_fan, **common_fan}

    for grp, pos in all_fans.items():
        color = get_group_color(grp)
        gid = f"__group__{grp}"
        side = "Rafael" if grp not in ["Friends", "Work"] else "Catarina" if grp != "Common Friends" else "Common"
        nodes.append({"id": gid, "name": grp, "label": grp, "type": "group",
                      "side": side, "groups": [grp], "priority": "High", "notes": "",
                      "size": 20, "color": color,
                      "fx": pos["xr"], "fy": pos["yr"], "fixed": True})
        group_ids.append(gid)

    # People
    for g in guests:
        side = g["side"]
        size = PRIORITY_SIZE.get(g["priority"], 8)
        primary = g["groups"][0] if g["groups"] else "Family"
        color = get_group_color(primary)
        is_hl = g["name"] == highlighted_name

        nodes.append({"id": g["name"], "name": g["name"], "label": g["name"],
                      "type": "person", "side": side, "groups": g["groups"],
                      "priority": g["priority"], "notes": g["notes"],
                      "size": size, "color": color,
                      "fx": None, "fy": None, "highlighted": is_hl})

        for grp in g["groups"]:
            links.append({"source": g["name"], "target": f"__group__{grp}",
                          "color": get_group_color(grp), "width": 0.9, "opacity": 0.4})

        if side == "Rafael":
            links.append({"source": g["name"], "target": "__Rafael__",
                          "color": "#1565C0", "width": 0.4, "opacity": 0.15})
        elif side == "Catarina":
            links.append({"source": g["name"], "target": "__Catarina__",
                          "color": "#AD1457", "width": 0.4, "opacity": 0.15})
        elif side == "Common":
            links.append({"source": g["name"], "target": "__Rafael__",
                          "color": "#7B1FA2", "width": 0.5, "opacity": 0.2})
            links.append({"source": g["name"], "target": "__Catarina__",
                          "color": "#7B1FA2", "width": 0.5, "opacity": 0.2})

    nodes_json = json.dumps(nodes)
    links_json = json.dumps(links)
    group_ids_json = json.dumps(group_ids)
    hl_json = json.dumps(highlighted_name or "")
    all_groups_json = json.dumps(GROUP_COLORS)

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0E1117;font-family:'Segoe UI',Arial,sans-serif;overflow:hidden;width:100%;height:700px}}
svg{{width:100%;height:700px;display:block}}
.link{{fill:none}}
.node-person circle{{stroke:rgba(255,255,255,0.2);stroke-width:1.5px;cursor:pointer;transition:stroke .15s}}
.node-person:hover circle{{stroke:white;stroke-width:2.5px}}
.node-person text{{font-size:7px;fill:#aaa;pointer-events:none;text-anchor:middle;dominant-baseline:middle;font-weight:400;text-shadow:0 1px 4px rgba(0,0,0,.9)}}
.node-center circle{{stroke:rgba(255,255,255,.5);stroke-width:3px;cursor:grab}}
.node-center text{{font-size:11px;fill:white;font-weight:700;text-shadow:0 1px 6px rgba(0,0,0,.8);pointer-events:none;text-anchor:middle;dominant-baseline:middle}}
.node-group rect{{stroke-opacity:.6;stroke-width:2px;cursor:grab;fill-opacity:.7;rx:5}}
.node-group text{{font-size:9px;fill:white;font-weight:600;pointer-events:none;text-anchor:middle;dominant-baseline:middle;text-shadow:0 1px 4px rgba(0,0,0,.8)}}
.hl circle{{stroke:#FFD700!important;stroke-width:3.5px!important;filter:drop-shadow(0 0 8px #FFD700)!important}}
.sel circle{{stroke:#00E5FF!important;stroke-width:3.5px!important;filter:drop-shadow(0 0 10px #00E5FF)!important}}
#tooltip{{position:fixed;background:rgba(14,14,24,.97);border:1px solid rgba(255,255,255,.15);border-radius:8px;padding:10px 14px;font-size:12px;color:#e0e0e0;pointer-events:none;opacity:0;transition:opacity .15s;z-index:9999;max-width:260px;box-shadow:0 4px 24px rgba(0,0,0,.6);line-height:1.7}}
#tooltip b{{color:white;font-size:13px}}
.tip-hi{{color:#4CAF50}}.tip-med{{color:#FFC107}}.tip-lo{{color:#f44336}}
#legend{{position:fixed;top:14px;right:14px;background:rgba(14,17,23,.88);border:1px solid rgba(255,255,255,.1);border-radius:8px;padding:10px 14px;font-size:11px;color:#b0b0b0;z-index:999}}
.lg{{font-weight:700;color:white;margin-bottom:6px}}
.li{{display:flex;align-items:center;gap:7px;margin-bottom:3px}}
.ld{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.ls{{width:10px;height:10px;border-radius:3px;flex-shrink:0}}
</style></head><body>
<svg id="graph"></svg>
<div id="tooltip"><b id="tt-name"></b><br><span id="tt-info"></span><div style="font-size:10px;color:#888;margin-top:3px">Click to select</div></div>
<div id="legend">
  <div class="lg">Legend</div>
  <div class="li"><div class="ls" style="background:#0D47A1"></div> 🔵 Rafael (Groom)</div>
  <div class="li"><div class="ls" style="background:#AD1457"></div> 🩷 Catarina (Bride)</div>
  <div class="li"><div class="ls" style="background:#7B1FA2"></div> 🟣 Common Friends</div>
  <div class="li"><div class="ls" style="background:#F57F17;opacity:.8"></div> 🟠 Group (square = fixed)</div>
  <div class="li"><div class="ld" style="background:#1976D2"></div> ● Person</div>
  <div class="li"><div class="ld" style="background:#FFD700"></div> ⭐ Highlighted</div>
</div>
<script>
// Load D3 dynamically with fallback CDNs
(function(){{
  var cdns = [
    "https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js",
    "https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js",
    "https://unpkg.com/d3@7.9.0/dist/d3.min.js"
  ];
  var idx = 0;
  function tryLoad(){{
    if(idx >= cdns.length){{
      document.body.innerHTML='<div style="color:red;padding:20px">Failed to load D3.js from all CDNs</div>';
      return;
    }}
    var s=document.createElement("script");
    s.src=cdns[idx++];
    s.onerror=tryLoad;
    s.onload=init;
    document.head.appendChild(s);
  }}
  tryLoad();
}})();
</script>
<script>
const nodes = {nodes_json};
const links = {links_json};
const groupIds = {group_ids_json};
const hlName = {hl_json} || null;

function W(){{return document.documentElement.clientWidth||window.innerWidth||800}}
function H(){{return document.documentElement.clientHeight||window.innerHeight||700}}

function init() {{

// Set fixed positions (ratios → pixels)
nodes.forEach(n => {{
  if(n.id==='__Rafael__'){{n.fx=W()*.25;n.fy=H()*.5;n.fixed=true}}
  if(n.id==='__Catarina__'){{n.fx=W()*.75;n.fy=H()*.5;n.fixed=true}}
}});
groupIds.forEach(id => {{
  const n=nodes.find(n=>n.id===id);
  if(!n)return;
  const xr=n.fx,yr=n.fy;
  if(xr&&yr){{n.fx=xr*W();n.fy=yr*H();n.fixed=true}}
}});

const svg=d3.select("#graph");
const sim=d3.forceSimulation(nodes)
  .force("link",d3.forceLink(links).id(d=>d.id)
    .distance(d=>{{
      const s=d.source?.type||d.source?.id?.includes('__')?'group':'person';
      const t=d.target?.type||d.target?.id?.includes('__')?'group':'person';
      if(s==='group'||t==='group')return 95;
      if(s==='center'||t==='center')return 140;
      return 75;
    }}).strength(.3))
  .force("charge",d3.forceManyBody()
    .strength(d=>{{if(d.type==='center')return-1200;if(d.type==='group')return-550;return-65}})
    .distanceMax(400))
  .force("center",d3.forceCenter(W()/2,H()/2).strength(.03))
  .force("collision",d3.forceCollide().radius(d=>d.size+15).strength(.8))
  .force("x",d3.forceX(W()/2).strength(d=>d.type==='center'?.3:d.type==='group'?.1:.008))
  .force("y",d3.forceY(H()/2).strength(d=>d.type==='center'?.12:d.type==='group'?.08:.004))
  .alphaDecay(.012).velocityDecay(.4);

const lnk=svg.append("g").selectAll("line").data(links).join("line")
  .attr("class","link").attr("stroke",d=>d.color)
  .attr("stroke-width",d=>d.width).attr("stroke-opacity",d=>d.opacity);

// Group nodes (squares)
const grpG=svg.append("g").selectAll("g").data(nodes.filter(d=>d.type==="group")).join("g")
  .attr("class","node-group")
  .call(d3.drag()
    .on("start",(e,d)=>{{if(!e.active)sim.alphaTarget(.2).restart();d.fx=d.x;d.fy=d.y}})
    .on("drag",(e,d)=>{{d.fx=e.x;d.fy=e.y}})
    .on("end",(e,d)=>{{if(!e.active)sim.alphaTarget(0);d.fx=d.x;d.fy=d.y}}));
grpG.append("rect")
  .attr("x",d=>-(d.size+5)).attr("y",d=>-(d.size+5))
  .attr("width",d=>(d.size+5)*2).attr("height",d=>(d.size+5)*2)
  .attr("fill",d=>d.color).attr("stroke",d=>d.color);
grpG.append("text").attr("dy",d=>d.size+14)
  .text(d=>d.label.length>16?d.label.substring(0,14)+"…":d.label);

// Person nodes (circles)
const perG=svg.append("g").selectAll("g").data(nodes.filter(d=>d.type==="person")).join("g")
  .attr("class",d=>"node-person"+(d.name===hlName?" hl":""))
  .call(d3.drag()
    .on("start",(e,d)=>{{if(!e.active)sim.alphaTarget(.25).restart();d.fx=d.x;d.fy=d.y}})
    .on("drag",(e,d)=>{{d.fx=e.x;d.fy=e.y}})
    .on("end",(e,d)=>{{if(!e.active)sim.alphaTarget(0);d.fx=null;d.fy=null}}));
perG.append("circle").attr("r",d=>d.size).attr("fill",d=>d.color);
perG.append("text").attr("dy",d=>(d.size||6)+11)
  .text(d=>d.label.length>18?d.label.substring(0,16)+"…":d.label)
  .style("display",d=>d.size>=10?"block":"none");

// Center nodes
const cenG=svg.append("g").selectAll("g").data(nodes.filter(d=>d.type==="center")).join("g")
  .attr("class",d=>"node-center"+(d.name===hlName?" hl":""))
  .call(d3.drag()
    .on("start",(e,d)=>{{if(!e.active)sim.alphaTarget(.25).restart();d.fx=d.x;d.fy=d.y}})
    .on("drag",(e,d)=>{{d.fx=e.x;d.fy=e.y}})
    .on("end",(e,d)=>{{if(!e.active)sim.alphaTarget(0);d.fx=d.x;d.fy=d.y}}));
cenG.append("circle").attr("r",d=>d.size).attr("fill",d=>d.color)
  .style("filter","drop-shadow(0 0 10px rgba(255,255,255,.4))");
cenG.append("text").attr("dy",d=>d.size+14).text(d=>d.label);

// Tooltip
const tt=document.getElementById("tooltip");
const ttN=document.getElementById("tt-name"),ttI=document.getElementById("tt-info");
perG.on("mouseover",(e,d)=>{{
  tt.style.opacity="1";
  ttN.textContent=d.name;
  const pcls=d.priority==='High'?'tip-hi':d.priority==='Medium'?'tip-med':'tip-lo';
  ttI.innerHTML=`Side:<b> ${{d.side}}</b> | Priority:<span class="${{pcls}}"> ${{d.priority}}</span><br>Groups:${{d.groups.join(', ')}}<br>${{d.notes||''}}`;
}})
.on("mousemove",e=>{{tt.style.left=(e.pageX+14)+"px";tt.style.top=(e.pageY-10)+"px"}})
.on("mouseout",()=>{{tt.style.opacity="0"}});

// Click person → select
perG.on("click",(e,d)=>{{
  perG.classed("hl",n=>n.name===d.name);
  cenG.classed("hl",n=>n.name===d.name);
  if(window.parent!==window){{try{{window.parent.postMessage({{type:"guest_select",guestName:d.name}}, "*")}}catch(e){{}}}}
  tt.style.opacity="1";ttN.textContent=d.name;
  const pcls=d.priority==='High'?'tip-hi':d.priority==='Medium'?'tip-med':'tip-lo';
  ttI.innerHTML=`Side:<b> ${{d.side}}</b> | Priority:<span class="${{pcls}}"> ${{d.priority}}</span><br>Groups:${{d.groups.join(', ')}}<br>${{d.notes||''}}`;
}});

// Click group → highlight people in that group
grpG.on("click",(e,d)=>{{
  perG.classed("hl",n=>n.groups.includes(d.name));
  tt.style.opacity="1";ttN.textContent=d.name;
  const cnt=nodes.filter(n=>n.type==="person"&&n.groups.includes(d.name)).length;
  ttI.textContent=cnt+" people — click again to clear";
}});
grpG.on("mousemove",e=>{{tt.style.left=(e.pageX+14)+"px";tt.style.top=(e.pageY-10)+"px"}});
grpG.on("mouseout",()=>{{tt.style.opacity="0"}});

// ============================================================
// FLOATING EDIT PANEL (SVG overlay via foreignObject)
// ============================================================
let selNode = null;
const PANEL_W = 220, PANEL_H = 280;
const allGroups = {all_groups_json};
const PRIORITY_OPTS = ["High","Medium","Low"];

function buildPanelContent(guest) {{
  const grps = guest.groups || [];
  const pri = guest.priority || "Medium";
  return `
    <div style="font-family:'Segoe UI',Arial,sans-serif;background:rgba(14,17,23,0.97);border:1px solid rgba(255,255,255,0.2);border-radius:10px;padding:14px;width:${{PANEL_W}}px;color:#e0e0e0;box-shadow:0 8px 32px rgba(0,0,0,0.7);">
      <div style="font-size:13px;font-weight:700;color:white;margin-bottom:10px;border-bottom:1px solid rgba(255,255,255,0.1);padding-bottom:8px;">✏️ Edit Guest</div>
      <div style="font-size:12px;color:#aaa;margin-bottom:2px;">Name</div>
      <div style="font-size:14px;font-weight:600;color:white;margin-bottom:10px;word-break:break-word;">${{guest.name}}</div>
      <div style="font-size:11px;color:#aaa;margin-bottom:4px;">Priority</div>
      <select id="edit-priority" style="width:100%;padding:5px 8px;background:#1e1e2e;color:white;border:1px solid rgba(255,255,255,0.15);border-radius:6px;font-size:12px;margin-bottom:10px;cursor:pointer;">
        ${{PRIORITY_OPTS.map(p=>`<option value="${{p}}" ${{p===pri?'selected':''}}>${{p}}</option>`).join('')}}
      </select>
      <div style="font-size:11px;color:#aaa;margin-bottom:4px;">Groups</div>
      <div style="max-height:80px;overflow-y:auto;background:#1e1e2e;border:1px solid rgba(255,255,255,0.1);border-radius:6px;padding:6px;margin-bottom:10px;">
        ${{Object.keys(allGroups).map(g=>`
          <label style="display:flex;align-items:center;gap:6px;padding:2px 0;font-size:11px;cursor:pointer;">
            <input type="checkbox" class="grp-cb" value="${{g}}" ${{grps.includes(g)?'checked':''}} style="cursor:pointer">
            <span style="width:8px;height:8px;border-radius:2px;background:${{allGroups[g]}};flex-shrink:0"></span>
            ${{g}}
          </label>
        `).join('')}}
      </div>
      <div style="font-size:11px;color:#aaa;margin-bottom:4px;">Notes</div>
      <input id="edit-notes" type="text" value="${{guest.notes||''}}" placeholder="Optional notes..."
        style="width:100%;padding:5px 8px;background:#1e1e2e;color:white;border:1px solid rgba(255,255,255,0.15);border-radius:6px;font-size:12px;margin-bottom:10px;box-sizing:border-box;" />
      <div style="display:flex;gap:6px;">
        <button id="edit-save" style="flex:1;padding:7px;background:#1565C0;color:white;border:none;border-radius:6px;cursor:pointer;font-size:12px;font-weight:600;">💾 Save</button>
        <button id="edit-close" style="flex:1;padding:7px;background:#333;color:#ccc;border:none;border-radius:6px;cursor:pointer;font-size:12px;">Close</button>
      </div>
    </div>
  `;
}}

const editPanelG = svg.append("g").attr("class","edit-panel").style("display","none");
let fo = null;

function showEditPanel(nodeX, nodeY) {{
  if (!selNode) return;
  const guest = selNode;
  let px = nodeX + 30;
  let py = nodeY - PANEL_H / 2;
  if (px + PANEL_W > W() - 10) px = nodeX - PANEL_W - 30;
  if (py < 10) py = 10;
  if (py + PANEL_H > H() - 10) py = H() - PANEL_H - 10;
  editPanelG.selectAll("*").remove();
  fo = editPanelG.append("foreignObject")
    .attr("x", px).attr("y", py)
    .attr("width", PANEL_W).attr("height", PANEL_H)
    .style("overflow", "visible");
  const div = fo.append("xhtml:div")
    .attr("xmlns","http://www.w3.org/1999/xhtml")
    .html(buildPanelContent(guest));
  div.select("#edit-save").on("click", () => {{
    const newPri = div.select("#edit-priority").node().value;
    const newNotes = div.select("#edit-notes").node().value;
    const newGrps = [];
    div.selectAll(".grp-cb").each(function() {{
      if (d3.select(this).node().checked) newGrps.push(d3.select(this).node().value);
    }});
    const form = parent.document.getElementById("streamlit-edit-data");
    if (form) {{
      form.value = JSON.stringify({{
        action: "save_edit",
        originalName: guest.name,
        priority: newPri,
        groups: newGrps,
        notes: newNotes
      }});
      const formEl = form.closest("form");
      if (formEl) {{
        const btn = formEl.querySelector("[data-testid=\"stFormSubmitButton\"]");
        if (btn) btn.click();
        else formEl.submit();
      }}
    }}
    hideEditPanel();
  }});
  div.select("#edit-close").on("click", hideEditPanel);
  editPanelG.style("display", null);
}}

function hideEditPanel() {{
  editPanelG.selectAll("*").remove();
  selNode = null;
  perG.classed("sel", false);
  perG.classed("hl", false);
}}

perG.on("click",(e,d)=>{{
  e.stopPropagation();
  selNode = d;
  perG.classed("hl", n => n.name === d.name);
  perG.classed("sel", n => n.name === d.name);
  showEditPanel(d.x || e.pageX, d.y || e.pageY);
  const sig = parent.document.getElementById("streamlit-guest-signal");
  if (sig) sig.value = d.name;
}});

svg.on("click", () => {{ hideEditPanel(); }});
grpG.on("click", null);
cenG.on("click", null);

grpG.on("click",(e,d)=>{{
  e.stopPropagation();
  const isHl = perG.classed("hl") && perG.filter(n=>n.groups.includes(d.name)).size() > 0;
  perG.classed("hl", n => !isHl && n.groups.includes(d.name));
  if (isHl) {{ hideEditPanel(); }}
}});

window.addEventListener("message",e=>{{
  if(e.data?.type==="highlight"){{
    perG.classed("hl",d=>d.name===e.data.guestName);
    cenG.classed("hl",d=>d.name===e.data.guestName);
  }}
  if(e.data?.type==="clear"){{
    perG.classed("hl",false);cenG.classed("hl",false);perG.classed("sel",false);
    hideEditPanel();
  }}
}});

sim.on("tick",()=>{{
  lnk.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y)
     .attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);
  grpG.attr("transform",d=>`translate(${{d.x}},${{d.y}})`);
  perG.attr("transform",d=>`translate(${{d.x}},${{d.y}})`);
  cenG.attr("transform",d=>`translate(${{d.x}},${{d.y}})`);
  if (selNode && editPanelG.style("display") !== "none") {{
    const nx = selNode.x || 0, ny = selNode.y || 0;
    let px = nx + 30, py = ny - PANEL_H/2;
    if (px + PANEL_W > W() - 10) px = nx - PANEL_W - 30;
    if (py < 10) py = 10;
    if (py + PANEL_H > H() - 10) py = H() - PANEL_H - 10;
    editPanelG.select("foreignObject").attr("x", px).attr("y", py);
  }}
}});

window.addEventListener("resize",()=>{{
  const w=W(),h=H();
  sim.force("center",d3.forceCenter(w/2,h/2).strength(.03));
  nodes.forEach(n=>{{
    if(n.id==='__Rafael__'){{n.fx=w*.25;n.fy=h*.5}}
    if(n.id==='__Catarina__'){{n.fx=w*.75;n.fy=h*.5}}
  }});
  sim.alpha(.2).restart();
}});

}} // end init
</script></body></html>"""
    return html


# Render
if filtered:
    st.components.v1.html(build_d3(filtered, (st.session_state.selected_guest or {}).get("name")), height=720, scrolling=False)
else:
    st.warning("No guests match the current filters.")

# =============================================================================
# GUEST TABLE with clickable rows → bidirectional highlight
# =============================================================================

st.divider()
st.subheader("📋 Guest List — click a row to highlight")

df_rows = []
for g in filtered:
    df_rows.append({
        "Name": g["name"],
        "Side": g["side"],
        "Groups": ", ".join(g["groups"]),
        "Priority": g["priority"],
        "Notes": g["notes"]
    })

if df_rows:
    df_disp = pd.DataFrame(df_rows)
    p_ord = {"High": 0, "Medium": 1, "Low": 2}
    df_disp["_p"] = df_disp["Priority"].map(p_ord)
    df_disp = df_disp.sort_values(["Side", "_p", "Groups", "Name"]).drop("_p", axis=1)

    def bg_name(val):
        sel = st.session_state.selected_guest
        if val == (sel or {}).get("name"):
            return "background:#00E5FF;color:#003366;font-weight:bold"
        return ""
    def bg_pri(val):
        if val == "High": return "background:#c8e6c9;color:#2e7d32"
        if val == "Medium": return "background:#fff9c4;color:#f57f17"
        return "background:#ffcdd2;color:#c62828"

    styled = df_disp.style.map(bg_name, subset=["Name"]).map(bg_pri, subset=["Priority"])
    st.dataframe(styled, hide_index=True)
    st.caption("Click a row or node to highlight · Edit panel appears floating near the node")
else:
    st.info("No guests to display")

st.divider()
st.caption("💒 Built by OpenClaw 🦞 | Rafael & Catarina | v3.3.0 — Floating node edit panel")
