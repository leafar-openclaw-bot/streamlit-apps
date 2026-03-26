"""
Tests for wedding-guest-network — pure Python logic only.
No Streamlit runtime, no network calls, no database.
"""
import json, sys, types, pathlib
import pytest

HERE = pathlib.Path(__file__).parent.parent  # apps/wedding-guest-network
GUESTS_FILE = HERE / "guests.json"

# ---------------------------------------------------------------------------
# Pull only the pure helpers out of streamlit_app.py by exec-ing a stripped
# version that skips every st.* top-level call.
# ---------------------------------------------------------------------------

def _build_pure_namespace():
    import math as _math, json as _json

    # ── session_state: dict with attribute access ────────────────────────────
    class _SS(dict):
        def __getattr__(self, k):
            try: return self[k]
            except KeyError: raise AttributeError(k)
        def __setattr__(self, k, v): self[k] = v

    class _StopExecution(BaseException):
        pass

    class _SecretsDict(dict):
        """Pretend all top-level keys exist so the password gate doesn't crash."""
        def __contains__(self, key): return True
        def __getitem__(self, key):
            # Return a nested dict for any secrets section
            return {"password": "__test__", "url": "http://test", "key": "test"}

    # ── Real ModuleType for streamlit so sub-imports work ────────────────────
    st_mod = types.ModuleType("streamlit")
    st_mod.set_page_config = lambda **kw: None
    st_mod.session_state   = _SS()
    st_mod.secrets         = _SecretsDict()
    st_mod.cache_resource  = lambda f: f
    st_mod.cache_data      = lambda f: f
    st_mod.stop            = lambda: (_ for _ in ()).throw(_StopExecution())
    for _attr in ("title","markdown","error","warning","text_input","rerun",
                  "selectbox","multiselect","metric","divider","subheader",
                  "caption","info","success","form","form_submit_button"):
        setattr(st_mod, _attr, lambda *a, **kw: None)

    comp_v1 = types.ModuleType("streamlit.components.v1")
    comp_v1.declare_component = lambda *a, **kw: (lambda **kw2: None)
    comp_v1.html = lambda *a, **kw: None

    comp_mod = types.ModuleType("streamlit.components")
    comp_mod.v1 = comp_v1
    st_mod.components = comp_mod

    supabase_mod = types.ModuleType("supabase")
    supabase_mod.create_client = lambda url, key: None
    supabase_mod.Client = object

    pyvis_mod     = types.ModuleType("pyvis")
    pyvis_net_mod = types.ModuleType("pyvis.network")
    pyvis_net_mod.Network = object
    pyvis_mod.network = pyvis_net_mod

    pd_mod = types.ModuleType("pandas")

    for name, mod in [
        ("streamlit",              st_mod),
        ("streamlit.components",   comp_mod),
        ("streamlit.components.v1",comp_v1),
        ("supabase",               supabase_mod),
        ("pyvis",                  pyvis_mod),
        ("pyvis.network",          pyvis_net_mod),
        ("pandas",                 pd_mod),
    ]:
        sys.modules[name] = mod

    # Extract only the pure helper section (color constants + _lighter + lookups).
    # These live between the COLOR SCHEME and BRIDGE COMPONENT sections and have
    # no Streamlit dependencies — so we exec just those lines.
    src_lines = (HERE / "streamlit_app.py").read_text(encoding="utf-8").splitlines()
    start = next(i for i, l in enumerate(src_lines) if "GROUP_HUB_COLORS = {" in l)
    end   = next(i for i, l in enumerate(src_lines) if "_BRIDGE_DIR" in l)
    pure_src = "\n".join(src_lines[start:end])

    ns: dict = {"__name__": "__helpers__", "__file__": str(HERE / "streamlit_app.py")}
    exec(compile(pure_src, str(HERE / "streamlit_app.py"), "exec"), ns)
    return ns


_ns = _build_pure_namespace()
_lighter          = _ns["_lighter"]
GROUP_HUB_COLORS  = _ns["GROUP_HUB_COLORS"]
GROUP_GUEST_COLORS= _ns["GROUP_GUEST_COLORS"]
PRIORITY_SIZE     = _ns["PRIORITY_SIZE"]
ALL_GROUPS        = _ns["ALL_GROUPS"]
SIDE_BORDER       = _ns["SIDE_BORDER"]
SIDE_SHAPE        = _ns["SIDE_SHAPE"]


# ---------------------------------------------------------------------------
# _lighter()
# ---------------------------------------------------------------------------

class TestLighter:
    def test_output_is_valid_hex(self):
        assert _lighter("#1565C0").startswith("#")
        assert len(_lighter("#1565C0")) == 7

    def test_lightened_channels_are_gte_original(self):
        orig = "#1565C0"
        lit  = _lighter(orig)
        r0,g0,b0 = int(orig[1:3],16), int(orig[3:5],16), int(orig[5:7],16)
        r1,g1,b1 = int(lit[1:3],16),  int(lit[3:5],16),  int(lit[5:7],16)
        assert r1 >= r0 and g1 >= g0 and b1 >= b0

    def test_factor_zero_unchanged(self):
        assert _lighter("#AD1457", factor=0.0) == "#AD1457".lower() or \
               _lighter("#AD1457", factor=0.0) == "#AD1457"

    def test_factor_one_gives_white(self):
        assert _lighter("#000000", factor=1.0) == "#ffffff"

    def test_all_hub_colors_produce_valid_hex(self):
        for name, color in GROUP_HUB_COLORS.items():
            result = _lighter(color)
            assert result.startswith("#") and len(result) == 7, \
                f"Bad result for group {name!r}"


# ---------------------------------------------------------------------------
# Color consistency
# ---------------------------------------------------------------------------

class TestColors:
    def test_every_hub_has_a_guest_color(self):
        for grp in GROUP_HUB_COLORS:
            assert grp in GROUP_GUEST_COLORS, f"Missing guest color for {grp!r}"

    def test_guest_colors_lighter_than_hub(self):
        for grp in GROUP_HUB_COLORS:
            hub_r   = int(GROUP_HUB_COLORS[grp][1:3], 16)
            guest_r = int(GROUP_GUEST_COLORS[grp][1:3], 16)
            assert guest_r >= hub_r, f"{grp}: guest color not lighter than hub"

    def test_all_hex_colors_six_digits(self):
        for d in (GROUP_HUB_COLORS, GROUP_GUEST_COLORS, SIDE_BORDER):
            for key, val in d.items():
                assert val.startswith("#") and len(val) == 7, \
                    f"{key!r} has malformed color {val!r}"


# ---------------------------------------------------------------------------
# Priority sizes
# ---------------------------------------------------------------------------

class TestPrioritySize:
    def test_high_gt_medium_gt_low(self):
        assert PRIORITY_SIZE["High"] > PRIORITY_SIZE["Medium"] > PRIORITY_SIZE["Low"]

    def test_all_sizes_positive(self):
        for priority, size in PRIORITY_SIZE.items():
            assert size > 0, f"Priority {priority!r} has non-positive size {size}"


# ---------------------------------------------------------------------------
# Side lookups
# ---------------------------------------------------------------------------

class TestSideLookups:
    SIDES = ("Rafael", "Catarina", "Common")
    VALID_SHAPES = {"dot", "square", "diamond", "hexagon", "star", "triangle", "ellipse"}

    def test_all_sides_have_border_color(self):
        for side in self.SIDES:
            assert side in SIDE_BORDER

    def test_all_sides_have_shape(self):
        for side in self.SIDES:
            assert side in SIDE_SHAPE

    def test_shapes_are_valid_vis_types(self):
        for side, shape in SIDE_SHAPE.items():
            assert shape in self.VALID_SHAPES, f"Side {side!r} has unknown shape {shape!r}"


# ---------------------------------------------------------------------------
# guests.json schema
# ---------------------------------------------------------------------------

class TestGuestsJson:
    @pytest.fixture(scope="class")
    def guests(self):
        with open(GUESTS_FILE, encoding="utf-8") as f:
            return json.load(f)

    REQUIRED   = {"name", "side", "groups", "priority"}
    SIDES      = {"Rafael", "Catarina", "Common"}
    PRIORITIES = {"High", "Medium", "Low"}
    RSVP_VALS  = {"Confirmed", "Pending", "Declined"}

    def test_file_not_empty(self, guests):
        assert len(guests) > 0

    def test_required_fields_present(self, guests):
        for g in guests:
            missing = self.REQUIRED - g.keys()
            assert not missing, f"{g.get('name','?')} missing fields: {missing}"

    def test_valid_sides(self, guests):
        for g in guests:
            assert g["side"] in self.SIDES, \
                f"{g['name']} has invalid side: {g['side']!r}"

    def test_valid_priorities(self, guests):
        for g in guests:
            assert g["priority"] in self.PRIORITIES, \
                f"{g['name']} has invalid priority: {g['priority']!r}"

    def test_valid_rsvp(self, guests):
        for g in guests:
            rsvp = g.get("rsvp", "Pending")
            assert rsvp in self.RSVP_VALS, \
                f"{g['name']} has invalid rsvp: {rsvp!r}"

    def test_archived_is_bool(self, guests):
        for g in guests:
            if "archived" in g:
                assert isinstance(g["archived"], bool), \
                    f"{g['name']} archived field is not bool: {g['archived']!r}"

    def test_groups_is_list(self, guests):
        for g in guests:
            assert isinstance(g["groups"], list), \
                f"{g['name']} groups is not a list"

    def test_no_duplicate_names(self, guests):
        names = [g["name"] for g in guests]
        dupes = [n for n in set(names) if names.count(n) > 1]
        assert not dupes, f"Duplicate guest names: {dupes}"

    def test_groups_are_known(self, guests):
        known = set(ALL_GROUPS)
        for g in guests:
            unknown = set(g["groups"]) - known
            assert not unknown, \
                f"{g['name']} has unknown groups: {unknown}"
