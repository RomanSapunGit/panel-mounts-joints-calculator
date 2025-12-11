from decimal import Decimal

from main import SolarSupportPlanner

TEST_WIDTH = Decimal("44.7")
TEST_HEIGHT = Decimal("71.1")
TEST_SPACING = Decimal("16")
TEST_FIRST_RAFTER = Decimal("5")
TEST_EDGE_CLEARANCE = Decimal("2")
TEST_MAX_SPAN = Decimal("48")
TEST_CANTILEVER_LIMIT = Decimal("16")
TEST_JOINT_TOLERANCE = Decimal("1.0")


def test_mounts_on_rafters_only():
    """All mounts must sit exactly on rafter x-coordinates."""
    panels = [{"x": 90.1, "y": 0}]
    planner = SolarSupportPlanner(
        panels,
        width=TEST_WIDTH,
        height=TEST_HEIGHT,
        spacing=TEST_SPACING,
        first_rafter=TEST_FIRST_RAFTER,
        edge_clearance=TEST_EDGE_CLEARANCE,
        max_span=TEST_MAX_SPAN,
        cantilever_limit=TEST_CANTILEVER_LIMIT,
        joint_tolerance=TEST_JOINT_TOLERANCE
    )
    result = planner.plan_supports()
    mounts = result["mounts"]

    first_rafter = TEST_FIRST_RAFTER
    spacing = TEST_SPACING
    end_x = Decimal(str(panels[0]["x"])) + TEST_WIDTH
    allowed_rafters = []
    r = first_rafter
    while r <= end_x:
        allowed_rafters.append(r)
        r += spacing

    for m in mounts:
        assert m["x"] in allowed_rafters, f"Mount not on a rafter: {m}"


def test_edge_clearance_respected():
    """No mount should be within 2 units of the left or right panel edge."""
    panels = [{"x": 0, "y": 0}]
    planner = SolarSupportPlanner(
        panels,
        width=TEST_WIDTH,
        height=TEST_HEIGHT,
        spacing=TEST_SPACING,
        first_rafter=TEST_FIRST_RAFTER,
        edge_clearance=TEST_EDGE_CLEARANCE,
        max_span=TEST_MAX_SPAN,
        cantilever_limit=TEST_CANTILEVER_LIMIT,
        joint_tolerance=TEST_JOINT_TOLERANCE
    )
    mounts = planner.plan_supports()["mounts"]

    left = Decimal("0")
    right = left + TEST_WIDTH

    for m in mounts:
        assert m["x"] >= left + TEST_EDGE_CLEARANCE
        assert m["x"] <= right - TEST_EDGE_CLEARANCE


def test_cantilever_limit_per_row():
    panels_data = [
        {"x": 0, "y": 0},
        {"x": 45.0, "y": 0},
        {"x": 90.0, "y": 0},
    ]

    planner = SolarSupportPlanner(
        panels=panels_data,
        width=Decimal("44.7"),
        height=Decimal("71.1"),
        spacing=Decimal("16"),
        first_rafter=Decimal("2"),
        edge_clearance=Decimal("2"),
        max_span=Decimal("48"),
        cantilever_limit=Decimal("16")
    )

    result = planner.plan_supports()
    mounts = result["mounts"]

    # Row bounds
    row_start_x = min(p["x"] for p in panels_data)
    row_end_x = max(Decimal(p["x"]) + Decimal("44.7") for p in panels_data)

    # First mount cantilever
    first_mount_x = min(m["x"] for m in mounts)
    assert first_mount_x - Decimal(row_start_x) <= planner.mount_calculator.cantilever_limit, \
        f"First mount too far from row start: {first_mount_x}"

    # Last mount cantilever
    last_mount_x = max(m["x"] for m in mounts)
    assert row_end_x - last_mount_x <= planner.mount_calculator.cantilever_limit, \
        f"Last mount too far from row end: {row_end_x - last_mount_x}"

    # Span between consecutive mounts
    sorted_mounts = sorted(mounts, key=lambda m: m["x"])
    for i in range(1, len(sorted_mounts)):
        span = sorted_mounts[i]["x"] - sorted_mounts[i - 1]["x"]
        assert span <= planner.mount_calculator.max_span, f"Span too large between mounts: {span}"

    # Optional: print mounts
    print("Mounts:", mounts)


def test_cantilever_best_effort_rule():
    """If no rafter exists inside the cantilever limit, the closest rafter must be used."""
    panels = [{"x": 90.1, "y": 0}]
    planner = SolarSupportPlanner(
        panels,
        width=TEST_WIDTH,
        height=TEST_HEIGHT,
        spacing=TEST_SPACING,
        first_rafter=TEST_FIRST_RAFTER,
        edge_clearance=TEST_EDGE_CLEARANCE,
        max_span=TEST_MAX_SPAN,
        cantilever_limit=TEST_CANTILEVER_LIMIT,
        joint_tolerance=TEST_JOINT_TOLERANCE
    )
    mounts = planner.plan_supports()["mounts"]
    xs = [m["x"] for m in mounts]

    assert Decimal("117") in xs


def test_span_limit_enforced():
    """No consecutive mounts should be more than MAX_SPAN apart."""
    panels = [{"x": 0, "y": 0}]
    planner = SolarSupportPlanner(
        panels,
        width=TEST_WIDTH,
        height=TEST_HEIGHT,
        spacing=TEST_SPACING,
        first_rafter=TEST_FIRST_RAFTER,
        edge_clearance=TEST_EDGE_CLEARANCE,
        max_span=TEST_MAX_SPAN,
        cantilever_limit=TEST_CANTILEVER_LIMIT,
        joint_tolerance=TEST_JOINT_TOLERANCE
    )
    mounts = planner.plan_supports()["mounts"]
    xs = sorted([m["x"] for m in mounts])

    for i in range(1, len(xs)):
        assert xs[i] - xs[i - 1] <= TEST_MAX_SPAN


def test_horizontal_joint_created():
    """Two horizontally adjacent panels with <1 unit gap must produce a joint."""
    panels = [
        {"x": 0, "y": 0},
        {"x": float(TEST_WIDTH) - 0.5, "y": 0},  # horizontal gap <1
    ]
    planner = SolarSupportPlanner(
        panels,
        width=TEST_WIDTH,
        height=TEST_HEIGHT,
        spacing=TEST_SPACING,
        first_rafter=TEST_FIRST_RAFTER,
        edge_clearance=TEST_EDGE_CLEARANCE,
        max_span=TEST_MAX_SPAN,
        cantilever_limit=TEST_CANTILEVER_LIMIT,
        joint_tolerance=TEST_JOINT_TOLERANCE
    )
    joints = planner.plan_supports()["joints"]

    assert any(j["x"] == TEST_WIDTH for j in joints)


def test_vertical_joint_created():
    """Two vertically adjacent panels with <1 unit gap must produce a joint."""
    panels = [
        {"x": 0, "y": 0},
        {"x": 0, "y": float(TEST_HEIGHT) - 0.5},  # vertical gap <1
    ]
    planner = SolarSupportPlanner(
        panels,
        width=TEST_WIDTH,
        height=TEST_HEIGHT,
        spacing=TEST_SPACING,
        first_rafter=TEST_FIRST_RAFTER,
        edge_clearance=TEST_EDGE_CLEARANCE,
        max_span=TEST_MAX_SPAN,
        cantilever_limit=TEST_CANTILEVER_LIMIT,
        joint_tolerance=TEST_JOINT_TOLERANCE
    )
    joints = planner.plan_supports()["joints"]

    assert any(j["y"] == TEST_HEIGHT for j in joints)


def test_shared_2x2_joint_created():
    """If a 2×2 square of panels touches, the shared corner joint must exist."""
    panels = [
        {"x": 0, "y": 0},
        {"x": float(TEST_WIDTH) - 0.3, "y": 0},
        {"x": 0, "y": float(TEST_HEIGHT) - 0.4},
        {"x": float(TEST_WIDTH) - 0.3, "y": float(TEST_HEIGHT) - 0.4},
    ]
    planner = SolarSupportPlanner(
        panels,
        width=TEST_WIDTH,
        height=TEST_HEIGHT,
        spacing=TEST_SPACING,
        first_rafter=TEST_FIRST_RAFTER,
        edge_clearance=TEST_EDGE_CLEARANCE,
        max_span=TEST_MAX_SPAN,
        cantilever_limit=TEST_CANTILEVER_LIMIT,
        joint_tolerance=TEST_JOINT_TOLERANCE
    )
    joints = planner.plan_supports()["joints"]

    assert any(
        j["x"] == TEST_WIDTH and j["y"] == TEST_HEIGHT
        for j in joints
    )


def test_full_scenario_matches_expected():
    """Validate the entire mount + joint configuration for the provided dataset."""
    panels = [
        {"x": 0, "y": 0}, {"x": 45.05, "y": 0}, {"x": 90.1, "y": 0},
        {"x": 0, "y": 71.6}, {"x": 135.15, "y": 0}, {"x": 135.15, "y": 71.6},
        {"x": 0, "y": 143.2}, {"x": 45.05, "y": 143.2}, {"x": 135.15, "y": 143.2},
        {"x": 90.1, "y": 143.2}
    ]
    planner = SolarSupportPlanner(
        panels,
        width=TEST_WIDTH,
        height=TEST_HEIGHT,
        spacing=TEST_SPACING,
        first_rafter=TEST_FIRST_RAFTER,
        edge_clearance=TEST_EDGE_CLEARANCE,
        max_span=TEST_MAX_SPAN,
        cantilever_limit=TEST_CANTILEVER_LIMIT,
        joint_tolerance=TEST_JOINT_TOLERANCE
    )
    result = planner.plan_supports()

    mounts = result["mounts"]
    joints = result["joints"]

    assert len(mounts) >= 25
    assert len(joints) >= 10

    assert any(m["x"] == Decimal("117") and m["y"] == Decimal("35.55") for m in mounts)
    assert any(j["x"] == Decimal("157.5") and j["y"] == Decimal("71.1") for j in joints)
