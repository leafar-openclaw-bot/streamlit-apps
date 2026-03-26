"""
Wedding Guest Network Visualizer
PyVis force graph: Groom/Bride → Social Group hubs → Guests.
Built by OpenClaw 🦞
"""
# v8.0.0 — Archive system, RSVP tracking, CSV download, improved group hub layout

import io
import json
import math
import pathlib
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pyvis.network import Network
from supabase import create_client, Client

st.set_page_config(page_title="Wedding Guest Network", page_icon="💒", layout="wide")

# =============================================================================
# PASSWORD GATE — blocks access until the shared password is entered
# =============================================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("💒 Wedding Guest Network")
    # Guard: secrets not yet configured on Streamlit Cloud
    if "auth" not in st.secrets or "password" not in st.secrets["auth"]:
        st.error(
            "⚠️ App secrets are not configured. "
            "Go to **Manage app → Settings → Secrets** and add:\n\n"
            "```toml\n[auth]\npassword = \"your-password\"\n\n"
            "[supabase]\nurl = \"https://...\"\nkey = \"eyJ...\"\n```"
        )
        st.stop()
    st.markdown("##### Please enter the access password")
    pw = st.text_input("Password", type="password", placeholder="Enter password…")
    if pw:
        if pw == st.secrets["auth"]["password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password. Try again.")
    st.stop()

# =============================================================================
# SUPABASE CLIENT
# =============================================================================

@st.cache_resource
def get_supabase() -> Client:
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"],
    )

def load_guests() -> list[dict]:
    """Fetch all guests from Supabase, ordered by name."""
    rows = get_supabase().table("guests").select("*").order("name").execute().data
    # Supabase returns groups as a Python list already (PostgreSQL text[])
    for r in rows:
        r.setdefault("rsvp", "Pending")
        r.setdefault("archived", False)
    return rows

def save_guest(guest: dict) -> None:
    """Upsert a single guest record."""
    row = {k: guest[k] for k in ("name", "groups", "priority", "notes", "rsvp", "archived") if k in guest}
    get_supabase().table("guests").upsert(row, on_conflict="name").execute()

def delete_guest(name: str) -> None:
    """Delete a guest by name."""
    get_supabase().table("guests").delete().eq("name", name).execute()

def archive_guest(name: str, archived: bool) -> None:
    """Set the archived flag for a guest by name."""
    get_supabase().table("guests").update({"archived": archived}).eq("name", name).execute()

# =============================================================================
# GROUP DATA — groups table drives the network hubs
# =============================================================================

def load_groups() -> list[dict]:
    """Fetch all groups from Supabase, ordered by name."""
    return get_supabase().table("groups").select("*").order("name").execute().data

def save_group(group: dict) -> None:
    """Upsert a group record (match on name)."""
    row = {k: group[k] for k in ("name", "side", "color") if k in group}
    get_supabase().table("groups").upsert(row, on_conflict="name").execute()

def delete_group_record(name: str) -> None:
    """Delete a group record from Supabase (guest cascade handled separately)."""
    get_supabase().table("groups").delete().eq("name", name).execute()

# =============================================================================
# GUEST DATA — loaded from Supabase (falls back to guests.json for local dev)
# =============================================================================

_GUESTS_FILE = pathlib.Path(__file__).parent / "guests.json"

def _load_initial() -> list[dict]:
    try:
        return load_guests()
    except Exception:
        pass
    # Fallback: local JSON (local development without credentials)
    st.session_state["_db_offline"] = True
    with open(_GUESTS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    for g in data:
        if "groups" not in g:
            g["groups"] = [g.pop("group")] if "group" in g else []
        g.setdefault("rsvp", "Pending")
        g.setdefault("archived", False)
    return data

# =============================================================================
# COLOR SCHEME
# =============================================================================

GROUP_HUB_COLORS = {
    "Family":                  "#1565C0",
    "Basic School":            "#2E7D32",
    "Secondary School":        "#00838F",
    "University":              "#283593",
    "Reboleira Parish":        "#E65100",
    "Erasmus Milan":           "#B71C1C",
    "Erasmus Netherlands":     "#F57F17",
    "Work (Planos Ótimos)":    "#4A148C",
    "Work (Sonant)":           "#1B5E20",
    "Special (Reciprocity)":   "#827717",
    "Friends":                 "#AD1457",
    "Work":                    "#BF360C",
    "Common Friends":          "#6A1B9A",
}

def _lighter(hex_color: str, factor: float = 0.45) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "#{:02x}{:02x}{:02x}".format(
        int(r + (255 - r) * factor),
        int(g + (255 - g) * factor),
        int(b + (255 - b) * factor),
    )

GROUP_GUEST_COLORS = {k: _lighter(v) for k, v in GROUP_HUB_COLORS.items()}

SIDE_BORDER = {"Rafael": "#90CAF9", "Catarina": "#F48FB1", "Common": "#CE93D8"}
SIDE_SHAPE  = {"Rafael": "square", "Catarina": "diamond", "Common": "hexagon"}

PRIORITY_SIZE = {"High": 28, "Medium": 18, "Low": 11}

RSVP_BORDER = {"Confirmed": "#4CAF50", "Declined": "#EF5350", "Pending": "#FFB300"}

ALL_GROUPS = sorted([
    "Family", "Basic School", "Secondary School", "University",
    "Reboleira Parish", "Erasmus Milan", "Erasmus Netherlands",
    "Work (Planos Ótimos)", "Work (Sonant)", "Special (Reciprocity)",
    "Friends", "Common Friends", "Work", "Other",
])

# Default side assignment for the built-in groups (used when seeding a blank DB)
_DEFAULT_GROUP_SIDES = {
    "Family":                "Common",
    "Basic School":          "Rafael",
    "Secondary School":      "Rafael",
    "University":            "Common",
    "Reboleira Parish":      "Rafael",
    "Erasmus Milan":         "Rafael",
    "Erasmus Netherlands":   "Rafael",
    "Work (Planos Ótimos)":  "Rafael",
    "Work (Sonant)":         "Rafael",
    "Special (Reciprocity)": "Rafael",
    "Friends":               "Catarina",
    "Work":                  "Catarina",
    "Common Friends":        "Common",
    "Other":                 "Rafael",
}

def _load_initial_groups() -> list[dict]:
    """Load groups from Supabase. If the table is empty, seed it from defaults."""
    try:
        rows = load_groups()
        if rows:
            return rows
        # Empty DB — seed with built-in defaults
        defaults = [
            {"name": name, "color": color, "side": _DEFAULT_GROUP_SIDES.get(name, "Rafael")}
            for name, color in GROUP_HUB_COLORS.items()
        ]
        for g in defaults:
            save_group(g)
        return defaults
    except Exception:
        pass
    # DB offline — return in-memory defaults
    return [
        {"name": name, "color": color, "side": _DEFAULT_GROUP_SIDES.get(name, "Rafael")}
        for name, color in GROUP_HUB_COLORS.items()
    ]

def _get_hub_colors() -> dict:
    return {g["name"]: g.get("color", "#607D8B") for g in st.session_state.get("groups", [])}

def _get_guest_colors() -> dict:
    return {name: _lighter(col) for name, col in _get_hub_colors().items()}

def _get_all_groups() -> list[str]:
    return sorted(g["name"] for g in st.session_state.get("groups", []))

def _get_side_map() -> dict:
    return {g["name"]: g.get("side", "Rafael") for g in st.session_state.get("groups", [])}

def _derive_side(groups: list) -> str:
    """Compute the DB 'side' value from a guest's group membership (for schema compat)."""
    sm = _get_side_map()
    sides = {sm.get(grp, "Rafael") for grp in groups}
    if "Rafael" in sides and "Catarina" in sides:
        return "Common"
    if sides == {"Catarina"}:
        return "Catarina"
    return "Rafael"

def _guest_persons(guest: dict) -> set:
    """Return the set of persons ('Rafael'/'Catarina'/'Common') a guest touches via groups."""
    sm = _get_side_map()
    return {sm.get(grp, "Rafael") for grp in guest.get("groups", [])} or {"Rafael"}

# =============================================================================
# BRIDGE COMPONENT — receives inline popup edits from JS via sessionStorage
# =============================================================================

_BRIDGE_DIR = pathlib.Path(__file__).parent / "bridge"
_BRIDGE = components.declare_component("wgn_bridge", path=str(_BRIDGE_DIR))

# Render bridge (invisible) and pick up any pending guest edits from the popup
_pending_raw = _BRIDGE(key="wgn_bridge")
if _pending_raw and isinstance(_pending_raw, str):
    try:
        updated = json.loads(_pending_raw)
        for u in (updated if isinstance(updated, list) else [updated]):
            g = next((x for x in st.session_state.get("guests", []) if x["name"] == u.get("name")), None)
            if g:
                for k in ("priority", "groups", "notes", "rsvp", "archived"):
                    if k in u:
                        g[k] = u[k]
                save_guest(g)   # persist to Supabase
    except Exception:
        pass

# =============================================================================
# SESSION STATE
# =============================================================================

if "guests" not in st.session_state:
    st.session_state.guests = _load_initial()
if "groups" not in st.session_state:
    st.session_state.groups = _load_initial_groups()

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.title("💒 Guest Management")
    if st.session_state.get("_db_offline"):
        st.warning("⚠️ Database not connected — changes won't be saved. Check Supabase secrets.")

    with st.form("add_guest_form", clear_on_submit=True):
        st.subheader("Add New Guest")
        new_name     = st.text_input("Name", placeholder="Full name")
        _dyn_groups  = _get_all_groups()
        new_groups   = st.multiselect("Groups", _dyn_groups, default=["Family"] if "Family" in _dyn_groups else _dyn_groups[:1])
        new_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        new_notes    = st.text_input("Notes", placeholder="Optional notes")
        if st.form_submit_button("Add Guest") and new_name:
            names = [g["name"] for g in st.session_state.guests]
            if new_name in names:
                st.error(f"Already exists: {new_name}")
            else:
                new_guest = {
                    "name": new_name, "groups": new_groups,
                    "priority": new_priority, "notes": new_notes,
                    "rsvp": "Pending", "archived": False,
                }
                st.session_state.guests.append(new_guest)
                try:
                    save_guest(new_guest)
                except Exception as e:
                    st.warning(f"Saved locally but DB write failed: {e}")
                st.success(f"Added {new_name}")

    st.divider()
    st.subheader("Filters")
    filter_person   = st.multiselect("Connected to", ["Rafael", "Catarina", "Common"],
                                      default=["Rafael", "Catarina", "Common"])
    filter_priority = st.multiselect("Priority", ["High", "Medium", "Low"],
                                      default=["High", "Medium", "Low"])
    _dyn_all        = _get_all_groups()
    filter_group    = st.multiselect("Group", _dyn_all, default=_dyn_all)
    filter_rsvp     = st.multiselect("RSVP", ["Confirmed", "Pending", "Declined"],
                                      default=["Confirmed", "Pending", "Declined"])

    st.divider()
    st.subheader("Statistics")
    gs = st.session_state.guests
    non_archived_gs = [g for g in gs if not g.get("archived", False)]
    archived_gs = [g for g in gs if g.get("archived", False)]
    st.metric("Total", len(non_archived_gs))
    st.metric("High Priority", sum(1 for g in non_archived_gs if g["priority"] == "High"))
    c1, c2 = st.columns(2)
    c1.metric("→ Rafael",   sum(1 for g in non_archived_gs if "Rafael"   in _guest_persons(g)))
    c2.metric("→ Catarina", sum(1 for g in non_archived_gs if "Catarina" in _guest_persons(g)))

    # RSVP stats
    st.markdown(
        f"✅ Conf. **{sum(1 for g in non_archived_gs if g.get('rsvp') == 'Confirmed')}** &nbsp; "
        f"⏳ Pend. **{sum(1 for g in non_archived_gs if g.get('rsvp', 'Pending') == 'Pending')}** &nbsp; "
        f"❌ Decl. **{sum(1 for g in non_archived_gs if g.get('rsvp') == 'Declined')}**"
    )

    # Download CSV
    csv_guests = non_archived_gs
    csv_rows = [
        {
            "Name": g["name"],
            "Connected to": ", ".join(sorted(_guest_persons(g))),
            "Groups": ", ".join(g["groups"]),
            "Priority": g["priority"],
            "RSVP": g.get("rsvp", "Pending"),
            "Notes": g.get("notes", ""),
        }
        for g in csv_guests
    ]
    csv_buf = io.StringIO()
    pd.DataFrame(csv_rows).to_csv(csv_buf, index=False)
    st.download_button(
        "📥 Download guest list (CSV)",
        data=csv_buf.getvalue(),
        file_name="wedding_guests.csv",
        mime="text/csv",
    )

    # Archived guests expander
    if archived_gs:
        with st.expander(f"📦 Archived ({len(archived_gs)})"):
            for ag in archived_gs:
                col1, col2 = st.columns([3, 1])
                col1.write(ag["name"])
                if col2.button("↩ Restore", key=f"restore_{ag['name']}"):
                    ag["archived"] = False
                    save_guest(ag)
                    st.rerun()

# =============================================================================
# MAIN
# =============================================================================

filtered = [
    g for g in st.session_state.guests
    if not g.get("archived", False)
    and bool(_guest_persons(g) & set(filter_person))
    and g["priority"] in filter_priority
    and any(grp in filter_group for grp in g.get("groups", []))
    and g.get("rsvp", "Pending") in filter_rsvp
]

archived_count = sum(1 for g in st.session_state.guests if g.get("archived", False))

st.title("💒 Wedding Guest Network")
st.caption(
    "⬜ Square = Rafael's groups  ·  ◇ Diamond = Catarina's  ·  ⬡ Hexagon = Common  ·  "
    "Click a guest to view/edit  ·  Double-click a group to collapse/expand"
)
caption_text = f"Showing {len(filtered)} of {len(non_archived_gs)} guests"
if archived_count > 0:
    caption_text += f"  ·  {archived_count} archived"
st.caption(caption_text)

# =============================================================================
# BUILD PYVIS NETWORK
# =============================================================================

def build_network(guests: list) -> Network:
    net = Network(
        height="760px", width="100%",
        bgcolor="#1e1e1e", font_color="white",
        directed=False, notebook=False,
        cdn_resources="in_line",
    )

    net.set_options(json.dumps({
        "nodes": {
            "borderWidth": 3,
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
                "springLength": 130,
                "springConstant": 0.35,
                "nodeDistance": 280,
                "damping": 0.5,
            },
            "stabilization": {"iterations": 600, "updateInterval": 20},
        },
        "interaction": {
            "hover": False,
            "tooltipDelay": 99999,
        },
    }))

    for node_id, label, bg, border, x in [
        ("__Rafael__",   "Rafael\n(Groom)",   "#0D47A1", "#90CAF9", -420),
        ("__Catarina__", "Catarina\n(Bride)",  "#AD1457", "#F48FB1",  420),
    ]:
        net.add_node(node_id, label=label,
                     color={"background": bg, "border": border,
                            "highlight": {"background": bg, "border": "#ffffff"}},
                     size=52, shape="dot",
                     font={"size": 14, "bold": True, "color": "white"},
                     title="", x=x, y=0, physics=False)

    hub_colors   = _get_hub_colors()
    guest_colors = _get_guest_colors()
    side_map     = _get_side_map()   # explicit side from groups table — no inference

    all_grps = sorted(set(grp for g in guests for grp in g.get("groups", [])))

    def grp_side(grp: str) -> str:
        return side_map.get(grp, "Rafael")

    grp_side_map = {grp: grp_side(grp) for grp in all_grps}
    rafael_grps   = [g for g in all_grps if grp_side_map[g] == "Rafael"]
    catarina_grps = [g for g in all_grps if grp_side_map[g] == "Catarina"]
    common_grps   = [g for g in all_grps if grp_side_map[g] == "Common"]

    def arc_span_deg(n: int) -> float:
        return min(170.0, max(0.0, (n - 1) * 22.0))

    hub_positions: dict = {
        "__Rafael__":   {"x": -420, "y": 0},
        "__Catarina__": {"x":  420, "y": 0},
    }

    def add_group_arc(group_list, cx, cy, radius, center_deg):
        n = len(group_list)
        if n == 0:
            return
        span = arc_span_deg(n)
        for i, grp in enumerate(group_list):
            angle_deg = center_deg if n == 1 else center_deg - span / 2 + span * i / (n - 1)
            px = int(cx + radius * math.cos(math.radians(angle_deg)))
            py = int(cy + radius * math.sin(math.radians(angle_deg)))
            hub_positions[f"__group__{grp}"] = {"x": px, "y": py}
            side   = grp_side_map.get(grp, "Rafael")
            bg     = hub_colors.get(grp, "#607D8B")
            net.add_node(
                f"__group__{grp}", label=grp,
                color={"background": bg, "border": SIDE_BORDER[side],
                       "highlight": {"background": bg, "border": "#ffffff"}},
                size=26, shape=SIDE_SHAPE[side],
                font={"size": 11, "color": "white"},
                title="", x=px, y=py, physics=False,
            )

    add_group_arc(rafael_grps,   -420, 0, 500, 180)
    add_group_arc(catarina_grps,  420, 0, 500,   0)
    add_group_arc(common_grps,      0, 0, 580, 270)

    # Hub edges: driven by the GROUP's side, not the guest's side
    added_hub_edges: set = set()
    for grp in all_grps:
        gid = f"__group__{grp}"
        gs  = grp_side_map.get(grp, "Rafael")
        if gs in ("Rafael", "Common") and ("R", grp) not in added_hub_edges:
            net.add_edge("__Rafael__", gid, color="#42A5F5", width=2)
            added_hub_edges.add(("R", grp))
        if gs in ("Catarina", "Common") and ("C", grp) not in added_hub_edges:
            net.add_edge("__Catarina__", gid, color="#F48FB1", width=2)
            added_hub_edges.add(("C", grp))

    for g in guests:
        primary    = g["groups"][0] if g["groups"] else "Family"
        node_color = guest_colors.get(primary, "#90A4AE")
        rsvp_color = RSVP_BORDER.get(g.get("rsvp", "Pending"), "#FFB300")
        net.add_node(
            g["name"], label=g["name"],
            color={"background": node_color, "border": rsvp_color,
                   "highlight": {"background": node_color, "border": "#ffffff"}},
            size=PRIORITY_SIZE.get(g["priority"], 14),
            shape="dot",
            font={"size": 11, "color": "white"},
            title="",
        )
        for grp in g["groups"]:
            net.add_edge(f"__group__{grp}", g["name"],
                         color={"color": node_color, "opacity": 0.6}, width=1)

    return net, hub_positions


def inject_interactions(html: str, guests: list, hub_positions: dict) -> str:
    """
    Inject into the PyVis HTML:
    - Network title overlay
    - Physics controls panel (real-time sliders)
    - Inline-editable click popup (view + edit mode)
    - Rigid drag (hub moves guests; root moves hubs+guests)
    - Double-click group: collapse / expand members
    """
    guests_map         = {g["name"]: g for g in guests}
    guests_json        = json.dumps(guests_map,       ensure_ascii=False)
    hub_colors_json    = json.dumps(_get_hub_colors(),   ensure_ascii=False)
    guest_colors_json  = json.dumps(_get_guest_colors(), ensure_ascii=False)
    priority_json      = json.dumps(PRIORITY_SIZE,        ensure_ascii=False)
    all_groups_json    = json.dumps(_get_all_groups(),    ensure_ascii=False)
    rsvp_colors_json   = json.dumps(RSVP_BORDER,          ensure_ascii=False)
    hub_positions_json = json.dumps(hub_positions,        ensure_ascii=False)

    code = f"""
<style>
/* ── Network canvas: needs relative positioning for overlays ── */
#mynetwork {{ position: relative !important; }}

/* ── Title overlay ── */
#gn-title {{
  position: absolute; top: 14px; left: 50%; transform: translateX(-50%);
  color: #fff; font-family: Arial, sans-serif; font-size: 17px; font-weight: bold;
  background: rgba(0,0,0,0.45); padding: 5px 18px; border-radius: 20px;
  pointer-events: none; white-space: nowrap; z-index: 200;
  letter-spacing: .3px;
}}

/* ── Physics controls panel ── */
#gn-ctrl {{
  position: absolute; bottom: 14px; right: 14px;
  background: rgba(20,20,20,0.88); border: 1px solid #444;
  border-radius: 10px; color: #ccc; font-family: Arial, sans-serif;
  font-size: 12px; z-index: 300; min-width: 220px;
  box-shadow: 0 4px 16px rgba(0,0,0,.5);
}}
#gn-ctrl-hdr {{
  padding: 8px 14px; cursor: pointer; font-weight: bold; font-size: 13px;
  color: #eee; display: flex; justify-content: space-between; align-items: center;
  user-select: none;
}}
#gn-ctrl-hdr:hover {{ color: #fff; }}
#gn-ctrl-body {{ padding: 10px 14px 12px; display: none; }}
.gn-sl-row {{
  display: grid; grid-template-columns: 1fr 120px 32px;
  align-items: center; gap: 6px; margin: 6px 0;
}}
.gn-sl-row span:first-child {{ color: #999; font-size: 11px; }}
.gn-sl-row input[type=range] {{
  width: 100%; accent-color: #1E88E5; cursor: pointer;
}}
.gn-sl-row span:last-child {{
  text-align: right; color: #90CAF9; font-size: 11px; min-width: 30px;
}}
#gn-ctrl-btns {{ display: flex; gap: 6px; margin-top: 10px; }}
.gn-ctrl-btn {{
  flex: 1; padding: 5px; border: 1px solid #555; border-radius: 5px;
  background: #2a2a2a; color: #ccc; font-size: 11px; cursor: pointer;
}}
.gn-ctrl-btn:hover {{ background: #333; color: #fff; }}

/* ── Popup container ── */
#gn-popup {{
  display:none; position:fixed;
  background:#242424; border:1px solid #555; border-radius:10px;
  padding:18px 20px 16px; color:#eee; font-family:Arial,sans-serif;
  font-size:13px; width:290px; z-index:9999;
  box-shadow:0 8px 32px rgba(0,0,0,.7);
}}
#gn-popup h3 {{ margin:0 0 10px; font-size:16px; color:#fff; padding-right:22px; line-height:1.3; }}
#gn-x {{ position:absolute; top:11px; right:14px; cursor:pointer; color:#666; font-size:20px; user-select:none; }}
#gn-x:hover {{ color:#aaa; }}
/* ── View mode ── */
.gn-field  {{ display:flex; gap:8px; align-items:baseline; margin:5px 0; }}
.gn-lbl    {{ color:#888; font-size:11px; text-transform:uppercase; letter-spacing:.5px; min-width:58px; flex-shrink:0; }}
.gn-val    {{ color:#eee; }}
.gn-High   {{ color:#81c784; font-weight:bold; }}
.gn-Medium {{ color:#fff176; font-weight:bold; }}
.gn-Low    {{ color:#ef9a9a; font-weight:bold; }}
.gn-Rafael   {{ color:#90caf9; }}
.gn-Catarina {{ color:#f48fb1; }}
.gn-Common   {{ color:#ce93d8; }}
.gn-notes  {{ font-style:italic; color:#bbb; }}
.gn-rsvp-Confirmed {{ color: #4CAF50; font-weight: bold; }}
.gn-rsvp-Declined  {{ color: #EF5350; font-weight: bold; }}
.gn-rsvp-Pending   {{ color: #FFB300; font-weight: bold; }}
.gn-danger {{ background: #b71c1c; color: #fff; }}
.gn-danger:hover {{ background: #c62828; }}
/* ── Edit mode ── */
.gn-row    {{ display:flex; flex-direction:column; gap:3px; margin:6px 0; }}
.gn-row label {{ color:#888; font-size:11px; text-transform:uppercase; letter-spacing:.5px; }}
.gn-row input, .gn-row select {{
  background:#333; border:1px solid #555; border-radius:5px;
  color:#eee; font-size:13px; padding:5px 8px; width:100%; box-sizing:border-box;
}}
.gn-row input:focus, .gn-row select:focus {{ outline:none; border-color:#1E88E5; }}
#gn-eg-list {{ display:flex; flex-wrap:wrap; gap:6px; padding:4px 0; }}
#gn-eg-list label {{
  display:flex; align-items:center; gap:5px; cursor:pointer;
  background:#2a2a2a; border:1px solid #555; border-radius:14px;
  padding:3px 10px; font-size:12px; color:#ccc; transition:border-color .15s;
}}
#gn-eg-list label:hover {{ border-color:#1E88E5; }}
#gn-eg-list input[type=checkbox] {{ display:none; }}
#gn-eg-list input[type=checkbox]:checked + span {{
  font-weight:bold; color:#fff;
}}
#gn-eg-list label:has(input:checked) {{
  background:#1E3A5F; border-color:#1E88E5; color:#fff;
}}
/* ── Buttons ── */
.gn-btn-row {{ display:flex; gap:8px; margin-top:14px; }}
.gn-btn    {{ flex:1; padding:8px; border:none; border-radius:6px; cursor:pointer; font-size:12px; font-weight:bold; }}
.gn-primary   {{ background:#1565C0; color:#fff; }}
.gn-primary:hover {{ background:#1976D2; }}
.gn-secondary {{ background:#333; color:#aaa; }}
.gn-secondary:hover {{ background:#444; }}
</style>

<!-- Title overlay (injected into #mynetwork after load) -->
<div id="gn-title" style="display:none">&#128146; Rafael &amp; Catarina &mdash; Wedding Guest Network</div>

<!-- Physics controls panel -->
<div id="gn-ctrl">
  <div id="gn-ctrl-hdr" onclick="gnCtrlToggle()">
    <span>&#9881; Physics</span><span id="gn-ctrl-arrow">&#9660;</span>
  </div>
  <div id="gn-ctrl-body">
    <div class="gn-sl-row">
      <span>Spring length</span>
      <input type="range" id="ctrl-sl" min="30" max="300" value="130" step="5" oninput="gnApplyPhysics()">
      <span id="ctrl-sl-v">130</span>
    </div>
    <div class="gn-sl-row">
      <span>Spring strength</span>
      <input type="range" id="ctrl-sc" min="5" max="100" value="35" step="5" oninput="gnApplyPhysics()">
      <span id="ctrl-sc-v">0.35</span>
    </div>
    <div class="gn-sl-row">
      <span>Node repulsion</span>
      <input type="range" id="ctrl-nd" min="50" max="600" value="280" step="10" oninput="gnApplyPhysics()">
      <span id="ctrl-nd-v">280</span>
    </div>
    <div class="gn-sl-row">
      <span>Center pull</span>
      <input type="range" id="ctrl-cg" min="0" max="50" value="0" step="1" oninput="gnApplyPhysics()">
      <span id="ctrl-cg-v">0.00</span>
    </div>
    <div class="gn-sl-row">
      <span>Damping</span>
      <input type="range" id="ctrl-dm" min="10" max="95" value="50" step="5" oninput="gnApplyPhysics()">
      <span id="ctrl-dm-v">0.50</span>
    </div>
    <div id="gn-ctrl-btns">
      <button class="gn-ctrl-btn" onclick="network.stabilize(300)">&#8635; Re-stabilize</button>
      <button class="gn-ctrl-btn" id="gn-pause-btn" onclick="gnTogglePhysics()">&#10074;&#10074; Pause</button>
      <button class="gn-ctrl-btn" onclick="gnFitView()">&#8982; Fit</button>
    </div>
  </div>
</div>

<!-- Popup HTML -->
<div id="gn-popup">
  <span id="gn-x" onclick="gnClose()">&#215;</span>
  <h3 id="gn-name"></h3>

  <!-- View mode -->
  <div id="gn-view">
    <div class="gn-field"><span class="gn-lbl">Groups</span><span class="gn-val" id="gn-vgroups"></span></div>
    <div class="gn-field"><span class="gn-lbl">Priority</span><span class="gn-val" id="gn-vpriority"></span></div>
    <div class="gn-field"><span class="gn-lbl">RSVP</span><span class="gn-val" id="gn-vrsvp"></span></div>
    <div class="gn-field" id="gn-vnotes-row" style="display:none">
      <span class="gn-lbl">Notes</span><span class="gn-val gn-notes" id="gn-vnotes"></span>
    </div>
    <div class="gn-btn-row">
      <button class="gn-btn gn-primary" onclick="gnStartEdit()">&#9998;&nbsp;Edit</button>
      <button class="gn-btn gn-secondary" onclick="gnClose()">Close</button>
    </div>
    <div class="gn-btn-row" style="margin-top:5px">
      <button class="gn-btn gn-danger" style="font-size:11px" onclick="gnArchive()">&#128230;&nbsp;Archive guest</button>
    </div>
  </div>

  <!-- Edit mode -->
  <div id="gn-edit" style="display:none">
    <div class="gn-row">
      <label>Priority</label>
      <select id="gn-ep">
        <option value="High">High</option>
        <option value="Medium">Medium</option>
        <option value="Low">Low</option>
      </select>
    </div>
    <div class="gn-row">
      <label>RSVP</label>
      <select id="gn-er">
        <option value="Pending">Pending</option>
        <option value="Confirmed">Confirmed</option>
        <option value="Declined">Declined</option>
      </select>
    </div>
    <div class="gn-row">
      <label>Groups</label>
      <div id="gn-eg-list"></div>
    </div>
    <div class="gn-row">
      <label>Notes</label>
      <input id="gn-en" type="text" placeholder="Optional notes">
    </div>
    <div class="gn-btn-row">
      <button class="gn-btn gn-primary"   onclick="gnSave()">&#128190;&nbsp;Save</button>
      <button class="gn-btn gn-secondary" onclick="gnCancelEdit()">Cancel</button>
    </div>
  </div>
</div>

<script>
// ── Lookup tables (from Python) ──────────────────────────────────────────────
var _GN           = {guests_json};
var _HUB_COLORS   = {hub_colors_json};
var _GUEST_COLORS = {guest_colors_json};
var _PSIZES       = {priority_json};
var _ALL_GROUPS   = {all_groups_json};
var _RSVP_COLORS  = {rsvp_colors_json};
var _HUB_POS      = {hub_positions_json};

// ── Build group checkboxes on load ───────────────────────────────────────────
(function gnBuildGroupList() {{
  var list = document.getElementById("gn-eg-list");
  _ALL_GROUPS.forEach(function(grp) {{
    var lbl = document.createElement("label");
    var cb  = document.createElement("input");
    cb.type = "checkbox"; cb.value = grp;
    var sp  = document.createElement("span");
    sp.textContent = grp;
    lbl.appendChild(cb);
    lbl.appendChild(sp);
    list.appendChild(lbl);
  }});
}})();

// ── Popup state ──────────────────────────────────────────────────────────────
var _gnSel    = null;
var _gnOutside= null;

function gnClose() {{
  document.getElementById("gn-popup").style.display = "none";
  _gnSel = null;
  if (_gnOutside) {{ document.removeEventListener("mousedown", _gnOutside); _gnOutside = null; }}
  network.unselectAll();
}}

function gnPosition(sx, sy) {{
  var popup = document.getElementById("gn-popup");
  var pw = 296, ph = popup.offsetHeight || 240;
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

  // View mode fields
  document.getElementById("gn-vgroups").textContent = (g.groups || []).join(", ");
  var pEl = document.getElementById("gn-vpriority");
  pEl.textContent = g.priority; pEl.className = "gn-val gn-" + g.priority;
  var rEl = document.getElementById("gn-vrsvp");
  rEl.textContent = g.rsvp || "Pending";
  rEl.className = "gn-val gn-rsvp-" + (g.rsvp || "Pending");
  var nRow = document.getElementById("gn-vnotes-row");
  if (g.notes) {{
    document.getElementById("gn-vnotes").textContent = g.notes;
    nRow.style.display = "flex";
  }} else {{
    nRow.style.display = "none";
  }}

  // Show view, hide edit
  document.getElementById("gn-view").style.display = "block";
  document.getElementById("gn-edit").style.display = "none";

  var popup = document.getElementById("gn-popup");
  popup.style.display = "block";
  gnPosition(sx, sy);

  // Close on click outside
  if (_gnOutside) document.removeEventListener("mousedown", _gnOutside);
  setTimeout(function() {{
    _gnOutside = function(e) {{
      if (!document.getElementById("gn-popup").contains(e.target)) gnClose();
    }};
    document.addEventListener("mousedown", _gnOutside);
  }}, 100);
}}

function gnStartEdit() {{
  var g = _GN[_gnSel];
  if (!g) return;
  document.getElementById("gn-ep").value = g.priority;
  document.getElementById("gn-er").value = g.rsvp || "Pending";
  var curGroups = new Set(g.groups || []);
  document.querySelectorAll("#gn-eg-list input[type=checkbox]").forEach(function(cb) {{
    cb.checked = curGroups.has(cb.value);
  }});
  document.getElementById("gn-en").value = g.notes || "";
  document.getElementById("gn-view").style.display = "none";
  document.getElementById("gn-edit").style.display = "block";
  // Reposition popup since height changed
  setTimeout(function() {{
    var popup = document.getElementById("gn-popup");
    var rect = document.getElementById("mynetwork").getBoundingClientRect();
    var nodePos = network.getPositions([_gnSel])[_gnSel];
    var dom = network.canvasToDOM(nodePos);
    gnPosition(rect.left + dom.x, rect.top + dom.y);
  }}, 10);
}}

function gnCancelEdit() {{
  document.getElementById("gn-view").style.display = "block";
  document.getElementById("gn-edit").style.display = "none";
}}

function gnArchive() {{
  if (!_gnSel) return;
  var g = _GN[_gnSel];
  if (!g) return;
  if (!confirm("Archive '" + g.name + "'?\\nThey will be hidden from the network.\\nRestore them from the sidebar.")) return;
  g.archived = true;
  nodes.update({{id: _gnSel, hidden: true}});
  network.getConnectedEdges(_gnSel).forEach(function(eId) {{
    edges.update({{id: eId, hidden: true}});
  }});
  gnClose();
  try {{
    window.parent.sessionStorage.setItem("wgn_save", JSON.stringify([g]));
  }} catch(e) {{}}
}}

function gnSave() {{
  var g = _GN[_gnSel];
  if (!g) return;
  var newPriority = document.getElementById("gn-ep").value;
  var newRsvp     = document.getElementById("gn-er").value;
  var newGroups = [];
  document.querySelectorAll("#gn-eg-list input[type=checkbox]:checked").forEach(function(cb) {{
    newGroups.push(cb.value);
  }});
  var newNotes    = document.getElementById("gn-en").value;

  // Update in-memory record
  g.priority = newPriority;
  g.rsvp     = newRsvp;
  g.groups   = newGroups;
  g.notes    = newNotes;

  // Update vis.js node appearance immediately
  var primary   = newGroups[0] || "Family";
  var nodeColor = _GUEST_COLORS[primary] || "#90A4AE";
  var hubColor  = _HUB_COLORS[primary]  || "#607D8B";
  nodes.update({{
    id: _gnSel,
    size:  _PSIZES[newPriority] || 14,
    color: {{ background: nodeColor, border: _RSVP_COLORS[newRsvp] || "#FFB300",
              highlight: {{ background: nodeColor, border: "#ffffff" }} }}
  }});

  // Update view mode fields
  document.getElementById("gn-name").textContent = g.name;
  document.getElementById("gn-vgroups").textContent = (g.groups || []).join(", ");
  var pEl = document.getElementById("gn-vpriority");
  pEl.textContent = g.priority; pEl.className = "gn-val gn-" + g.priority;
  var rEl2 = document.getElementById("gn-vrsvp");
  rEl2.textContent = g.rsvp; rEl2.className = "gn-val gn-rsvp-" + g.rsvp;
  var nRow = document.getElementById("gn-vnotes-row");
  if (g.notes) {{
    document.getElementById("gn-vnotes").textContent = g.notes;
    nRow.style.display = "flex";
  }} else {{
    nRow.style.display = "none";
  }}

  // Persist only the changed guest to sessionStorage → bridge picks up → Python reruns
  try {{
    window.parent.sessionStorage.setItem("wgn_save", JSON.stringify([g]));
  }} catch(e) {{}}

  // Return to view mode
  gnCancelEdit();
}}

// ── Rigid dragging ──────────────────────────────────────────────────────────
var _dId = null, _dGroupIds = [], _dStart = {{}}, _dPointerStart = null, _dPhysics = [];

function _toCanvas(sx, sy) {{
  var rect = document.getElementById("mynetwork").getBoundingClientRect();
  return network.DOMtoCanvas({{ x: sx - rect.left, y: sy - rect.top }});
}}

function _collectGuests(hubId, ids, pos) {{
  network.getConnectedNodes(hubId).forEach(function(gId) {{
    if (!gId.startsWith("__") && ids.indexOf(gId) < 0) {{
      var nd = nodes.get(gId);
      if (nd && !nd.hidden) {{ ids.push(gId); _dStart[gId] = {{ x:pos[gId].x, y:pos[gId].y }}; }}
    }}
  }});
}}

network.on("dragStart", function(p) {{
  if (!p.nodes.length) return;
  _dId = p.nodes[0]; _dGroupIds = []; _dStart = {{}}; _dPhysics = [];
  var pos = network.getPositions();
  _dPointerStart = _toCanvas(p.event.center.x, p.event.center.y);
  _dStart[_dId] = {{ x: pos[_dId].x, y: pos[_dId].y }};

  if (_dId === "__Rafael__" || _dId === "__Catarina__") {{
    network.getConnectedNodes(_dId).forEach(function(hubId) {{
      if (!hubId.startsWith("__group__")) return;
      if (_dGroupIds.indexOf(hubId) < 0) {{ _dGroupIds.push(hubId); _dStart[hubId] = {{ x:pos[hubId].x, y:pos[hubId].y }}; }}
      _collectGuests(hubId, _dGroupIds, pos);
    }});
  }} else if (_dId.startsWith("__group__")) {{
    _collectGuests(_dId, _dGroupIds, pos);
  }}

  _dPhysics = _dGroupIds.filter(function(id) {{ return !id.startsWith("__"); }});
  if (_dPhysics.length) nodes.update(_dPhysics.map(function(id) {{ return {{id:id, physics:false}}; }}));
}});

network.on("drag", function(p) {{
  if (!p.nodes.length || !_dGroupIds.length || !_dPointerStart) return;
  var cur = _toCanvas(p.event.center.x, p.event.center.y);
  var dx = cur.x - _dPointerStart.x, dy = cur.y - _dPointerStart.y;
  nodes.update(_dGroupIds.map(function(id) {{
    return {{ id:id, x: _dStart[id].x + dx, y: _dStart[id].y + dy }};
  }}));
}});

network.on("dragEnd", function() {{
  if (_dPhysics.length) nodes.update(_dPhysics.map(function(id) {{ return {{id:id, physics:true}}; }}));
  _dId = null; _dGroupIds = []; _dStart = {{}}; _dPointerStart = null; _dPhysics = [];
}});

// ── Collapse / expand on double-click ───────────────────────────────────────
var _collapsed = {{}}, _collData = {{}};

network.on("doubleClick", function(p) {{
  gnClose();
  // physics:false nodes aren't in vis.js's spatial index until dragged,
  // so p.nodes may be empty — fall back to raw DOM hit-test.
  var id = (p.nodes && p.nodes.length > 0)
    ? p.nodes[0]
    : network.getNodeAt(p.pointer.DOM);
  if (!id || !id.toString().startsWith("__group__")) return;
  var nd = nodes.get(id);
  var baseLabel = nd ? nd.label.replace(/\\n\\(\\d+\\)$/, "") : id.replace("__group__","");

  if (_collapsed[id]) {{
    var info = _collData[id] || {{ nodeIds:[], edgeIds:[] }};
    nodes.update(info.nodeIds.map(function(n) {{ return {{id:n, hidden:false}}; }}));
    edges.update(info.edgeIds.map(function(e) {{ return {{id:e, hidden:false}}; }}));
    nodes.update({{ id:id, label:baseLabel }});
    _collapsed[id] = false; delete _collData[id];
  }} else {{
    var guestIds = network.getConnectedNodes(id).filter(function(g) {{ return !g.startsWith("__"); }});
    var edgeIds = [];
    guestIds.forEach(function(gId) {{
      network.getConnectedEdges(gId).forEach(function(eId) {{
        if (edgeIds.indexOf(eId) < 0) edgeIds.push(eId);
      }});
    }});
    _collData[id] = {{ nodeIds:guestIds, edgeIds:edgeIds }};
    _collapsed[id] = true;
    nodes.update(guestIds.map(function(n) {{ return {{id:n, hidden:true}}; }}));
    edges.update(edgeIds.map(function(e) {{ return {{id:e, hidden:true}}; }}));
    nodes.update({{ id:id, label: baseLabel + "\\n(" + guestIds.length + ")" }});
  }}
}});

// ── Select node → show popup ────────────────────────────────────────────────
network.on("selectNode", function(p) {{
  if (!p.nodes.length) return;
  var id = p.nodes[0];
  if (id.startsWith("__")) {{ gnClose(); return; }}
  var nodePos = network.getPositions([id])[id];
  var dom  = network.canvasToDOM(nodePos);
  var rect = document.getElementById("mynetwork").getBoundingClientRect();
  gnShow(id, rect.left + dom.x, rect.top + dom.y);
}});

// ── Initialise hub positions (Python-computed arcs) ──────────────────────────
// Sets x/y before vis.js stabilization runs. No fixed:{{}} so hubs remain
// draggable and double-clickable; physics:false keeps them from being
// pushed around by the force simulation after they're placed.
(function gnInitHubPositions() {{
  var updates = [];
  for (var id in _HUB_POS) {{
    var p = _HUB_POS[id];
    updates.push({{id: id, x: p.x, y: p.y, physics: false}});
  }}
  nodes.update(updates);
}})();

// ── Mount title + controls inside #mynetwork after DOM ready ────────────────
(function mountOverlays() {{
  var mn = document.getElementById("mynetwork");
  if (!mn) {{ setTimeout(mountOverlays, 80); return; }}
  mn.style.position = "relative";
  mn.appendChild(document.getElementById("gn-title"));
  mn.appendChild(document.getElementById("gn-ctrl"));
  document.getElementById("gn-title").style.display = "block";
}})();

// ── Physics controls ────────────────────────────────────────────────────────
var _physicsOn = true;

function gnCtrlToggle() {{
  var body  = document.getElementById("gn-ctrl-body");
  var arrow = document.getElementById("gn-ctrl-arrow");
  var open  = body.style.display !== "none";
  body.style.display  = open ? "none"  : "block";
  arrow.innerHTML     = open ? "&#9660;" : "&#9650;";
}}

function gnApplyPhysics() {{
  var sl = parseInt(document.getElementById("ctrl-sl").value);
  var sc = parseInt(document.getElementById("ctrl-sc").value) / 100;
  var nd = parseInt(document.getElementById("ctrl-nd").value);
  var cg = parseInt(document.getElementById("ctrl-cg").value) / 100;
  var dm = parseInt(document.getElementById("ctrl-dm").value) / 100;
  document.getElementById("ctrl-sl-v").textContent = sl;
  document.getElementById("ctrl-sc-v").textContent = sc.toFixed(2);
  document.getElementById("ctrl-nd-v").textContent = nd;
  document.getElementById("ctrl-cg-v").textContent = cg.toFixed(2);
  document.getElementById("ctrl-dm-v").textContent = dm.toFixed(2);
  network.setOptions({{ physics: {{ repulsion: {{
    springLength: sl, springConstant: sc,
    nodeDistance: nd, centralGravity: cg, damping: dm
  }} }} }});
}}

function gnTogglePhysics() {{
  _physicsOn = !_physicsOn;
  network.setOptions({{ physics: {{ enabled: _physicsOn }} }});
  document.getElementById("gn-pause-btn").innerHTML =
    _physicsOn ? "&#10074;&#10074; Pause" : "&#9654; Resume";
}}

function gnFitView() {{
  network.fit({{ animation: {{ duration: 500, easingFunction: "easeInOutQuad" }} }});
}}
</script>
"""
    return html.replace("</body>", code + "\n</body>")


# =============================================================================
# RENDER NETWORK
# =============================================================================

if filtered:
    net, hub_positions = build_network(filtered)
    html = net.generate_html()
    html = inject_interactions(html, filtered, hub_positions)
    components.html(html, height=820, scrolling=False)
else:
    st.warning("No guests match the current filters.")

# =============================================================================
# GUEST TABLE
# =============================================================================

st.divider()
st.subheader("Guest List")

df_rows = [
    {"Name": g["name"], "Connected to": ", ".join(sorted(_guest_persons(g))),
     "Groups": ", ".join(g["groups"]),
     "Priority": g["priority"],
     "RSVP": g.get("rsvp", "Pending"),
     "Notes": g.get("notes", "")}
    for g in filtered
]

if df_rows:
    df    = pd.DataFrame(df_rows)
    p_ord = {"High": 0, "Medium": 1, "Low": 2}
    df["_p"] = df["Priority"].map(p_ord)
    df = df.sort_values(["Connected to", "_p", "Groups", "Name"]).drop("_p", axis=1)

    def color_priority(v):
        if v == "High":   return "background-color:#c8e6c9;color:#2e7d32"
        if v == "Medium": return "background-color:#fff9c4;color:#f57f17"
        return "background-color:#ffcdd2;color:#c62828"

    def color_rsvp(v):
        if v == "Confirmed": return "background-color:#c8e6c9;color:#2e7d32"
        if v == "Declined":  return "background-color:#ffcdd2;color:#c62828"
        return "background-color:#fff9c4;color:#f57f17"

    st.dataframe(
        df.style
          .map(color_priority, subset=["Priority"])
          .map(color_rsvp, subset=["RSVP"]),
        hide_index=True,
    )
else:
    st.info("No guests to display.")

st.divider()

# =============================================================================
# SOCIAL GROUP MANAGEMENT
# =============================================================================

st.subheader("⚡ Social Group Management")
st.caption("Groups define the hub nodes in the network. Assigning a side controls which arc the hub appears on.")

_grps = st.session_state.groups
SIDES = ["Rafael", "Catarina", "Common"]

# ── Group table ───────────────────────────────────────────────────────────────
if _grps:
    swatch_rows = "".join(
        f"<tr style='line-height:1.8'>"
        f"<td style='padding:2px 10px 2px 0'>"
        f"<span style='display:inline-block;width:18px;height:18px;border-radius:4px;"
        f"background:{g['color']};vertical-align:middle'></span></td>"
        f"<td style='padding:2px 14px 2px 0'>{g['name']}</td>"
        f"<td style='padding:2px 0;color:#aaa'>{g.get('side','Rafael')}</td>"
        f"</tr>"
        for g in sorted(_grps, key=lambda x: (x.get("side","Rafael"), x["name"]))
    )
    st.markdown(
        f"<table style='font-size:13px;border-collapse:collapse'>"
        f"<tr><th style='text-align:left;padding:2px 10px 6px 0;color:#888'>Color</th>"
        f"<th style='text-align:left;padding:2px 14px 6px 0;color:#888'>Name</th>"
        f"<th style='text-align:left;padding:2px 0 6px;color:#888'>Side</th></tr>"
        f"{swatch_rows}</table>",
        unsafe_allow_html=True,
    )
else:
    st.info("No groups configured.")

st.write("")

col_add, col_edit = st.columns(2)

# ── Add group ─────────────────────────────────────────────────────────────────
with col_add:
    with st.expander("➕ Add Group"):
        with st.form("add_group_form"):
            ng_name  = st.text_input("Name", placeholder="e.g. Tennis Club")
            ng_side  = st.selectbox("Side", SIDES)
            ng_color = st.color_picker("Colour", "#607D8B")
            if st.form_submit_button("Add"):
                if not ng_name.strip():
                    st.error("Name is required.")
                elif ng_name in {g["name"] for g in _grps}:
                    st.error(f"'{ng_name}' already exists.")
                else:
                    ng = {"name": ng_name.strip(), "side": ng_side, "color": ng_color}
                    st.session_state.groups.append(ng)
                    try:
                        save_group(ng)
                    except Exception as e:
                        st.warning(f"DB error: {e}")
                    st.rerun()

# ── Edit / Delete group ───────────────────────────────────────────────────────
with col_edit:
    with st.expander("✏️ Edit / Delete Group"):
        if _grps:
            eg_name = st.selectbox(
                "Select group",
                [g["name"] for g in sorted(_grps, key=lambda x: x["name"])],
                key="eg_select",
            )
            eg = next(g for g in _grps if g["name"] == eg_name)

            with st.form("edit_group_form"):
                new_eg_name  = st.text_input("Name",   value=eg["name"])
                new_eg_side  = st.selectbox("Side", SIDES, index=SIDES.index(eg.get("side", "Rafael")))
                new_eg_color = st.color_picker("Colour", value=eg.get("color", "#607D8B"))
                if st.form_submit_button("💾 Save"):
                    old_name = eg_name
                    new_name = new_eg_name.strip()
                    if not new_name:
                        st.error("Name is required.")
                    else:
                        if new_name != old_name:
                            # Rename in all guests (session + DB)
                            for guest in st.session_state.guests:
                                if old_name in guest.get("groups", []):
                                    guest["groups"] = [
                                        new_name if gr == old_name else gr
                                        for gr in guest["groups"]
                                    ]
                                    try:
                                        save_guest(guest)
                                    except Exception:
                                        pass
                            # Delete old record; upsert will create new name
                            try:
                                delete_group_record(old_name)
                            except Exception:
                                pass
                            eg["name"] = new_name
                        eg["side"]  = new_eg_side
                        eg["color"] = new_eg_color
                        try:
                            save_group(eg)
                        except Exception as e:
                            st.warning(f"DB error: {e}")
                        st.rerun()

            if st.button(f"🗑️ Delete '{eg_name}'", type="secondary", key="del_grp_btn"):
                # Remove group from all guests
                for guest in st.session_state.guests:
                    if eg_name in guest.get("groups", []):
                        guest["groups"] = [gr for gr in guest["groups"] if gr != eg_name]
                        try:
                            save_guest(guest)
                        except Exception:
                            pass
                st.session_state.groups = [g for g in _grps if g["name"] != eg_name]
                try:
                    delete_group_record(eg_name)
                except Exception as e:
                    st.warning(f"DB error: {e}")
                st.rerun()
        else:
            st.info("No groups to edit.")

st.divider()
st.caption("Built by OpenClaw 🦞 | Rafael & Catarina | v9.0.0")
