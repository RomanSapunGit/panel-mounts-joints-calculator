from decimal import Decimal

from main import SolarSupportPlanner

panels = [
    {"x": 0, "y": 0},
    {"x": 45, "y": 0},
    {"x": 0, "y": 70},
]

planner = SolarSupportPlanner(
    panels,
    width=Decimal("44.7"),
    height=Decimal("71.1"),
    spacing=Decimal("16"),
    first_rafter=Decimal("5"),
    edge_clearance=Decimal("2"),
    max_span=Decimal("48"),
    cantilever_limit=Decimal("16"),
    joint_tolerance=Decimal("1.0")
)

result = planner.plan_supports()

print("Mounts:")
for m in result["mounts"]:
    print(f"  x={m['x']}, y={m['y']}")

print("\nJoints:")
for j in result["joints"]:
    print(f"  x={j['x']}, y={j['y']}")
