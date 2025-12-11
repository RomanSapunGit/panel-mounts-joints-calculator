from decimal import Decimal
from typing import List, Dict

from panel import Panel
from services.joint_calculator import JointCalculator
from services.mount_calculator import MountCalculator
from services.rafter_grid import RafterGrid


class SolarSupportPlanner:
    """
    Main planner that calculates both mounts and joints for a list of panels.
    """

    def __init__(self, panels: List[Dict[str, float]],
                 width: Decimal = Decimal("44.7"),
                 height: Decimal = Decimal("71.1"),
                 spacing: Decimal = Decimal("16"),
                 first_rafter: Decimal = Decimal("5"),
                 edge_clearance: Decimal = Decimal("2"),
                 max_span: Decimal = Decimal("48"),
                 cantilever_limit: Decimal = Decimal("16"),
                 joint_tolerance: Decimal = Decimal("1.0")):

        self.panels = [Panel(p["x"], p["y"], width, height) for p in panels]
        self.rafter_grid = RafterGrid(spacing=spacing, first_rafter=first_rafter, edge_clearance=edge_clearance)
        self.mount_calculator = MountCalculator(self.rafter_grid, max_span, cantilever_limit)
        self.joint_calculator = JointCalculator(width, joint_tolerance)

    def plan_supports(self) -> Dict[str, List[Dict[str, Decimal]]]:
        """
        Calculate mounts per row and joints for all panels.
        """
        tolerance = Decimal("0.1")
        rows: Dict[Decimal, List[Panel]] = {}

        for p in self.panels:
            row_key = None
            for key in rows.keys():
                if abs(key - p.y) <= tolerance:
                    row_key = key
                    break

            if row_key is None:
                rows[p.y] = [p]
            else:
                rows[row_key].append(p)

        mounts = [
            mount
            for row_panels in rows.values()
            for mount in self.mount_calculator.calculate_row_mounts(row_panels)
        ]

        joints = self.joint_calculator.calculate_joints(self.panels)

        mounts.sort(key=lambda m: (m["y"], m["x"]))
        joints.sort(key=lambda j: (j["y"], j["x"]))

        return {"mounts": mounts, "joints": joints}
