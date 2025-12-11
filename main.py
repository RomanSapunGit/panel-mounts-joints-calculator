import math
from decimal import Decimal
from typing import List, Dict


class Panel:
    """
    Represents a solar panel with a position and dimensions.

    Attributes:
        x (Decimal): Left edge x-coordinate of the panel.
        y (Decimal): Top edge y-coordinate of the panel.
        width (Decimal): Width of the panel.
        height (Decimal): Height of the panel.
    """

    def __init__(self, x: float, y: float, width: Decimal, height: Decimal):
        self.x = Decimal(str(x))
        self.y = Decimal(str(y))
        self.width = width
        self.height = height

    @property
    def end_x(self) -> Decimal:
        return self.x + self.width

    @property
    def end_y(self) -> Decimal:
        return self.y + self.height

    @property
    def center_y(self) -> Decimal:
        return self.y + self.height / 2


class RafterGrid:
    """
    Represents the underlying rafter grid of a roof.

    Supports calculation of rafters that intersect a given panel while respecting edge clearance.

    Attributes:
        spacing (Decimal): Distance between rafters.
        first_rafter (Decimal): X-coordinate of the first rafter.
        edge_clearance (Decimal): Minimum distance between panel edge and rafter.
    """

    def __init__(self, spacing: Decimal = Decimal("16"),
                 first_rafter: Decimal = Decimal("5"),
                 edge_clearance: Decimal = Decimal("2")):
        self.spacing = spacing
        self.first_rafter = first_rafter
        self.edge_clearance = edge_clearance

    def rafters_within_panel(self, panel: Panel) -> list[Decimal]:
        """
        Returns all rafter x-coordinates that lie within a panel's bounds
        respecting the edge clearance.
        Args:
            panel (Panel): The panel to check.
        Returns:
            List[Decimal]: List of x-coordinates of rafters inside the panel.
        """
        positions = []

        n = max(0, math.ceil((panel.x + self.edge_clearance - self.first_rafter) / self.spacing))
        candidate = self.first_rafter + n * self.spacing

        while candidate <= panel.end_x - self.edge_clearance:
            positions.append(candidate)
            candidate += self.spacing

        return positions


class MountCalculator:
    """
    Calculates mounts per row of panels to satisfy cantilever and span rules.
    """

    def __init__(self, rafter_grid, max_span: Decimal, cantilever_limit: Decimal):
        self.rafter_grid = rafter_grid
        self.max_span = max_span
        self.cantilever_limit = cantilever_limit

    def calculate_row_mounts(self, panels_in_row: list) -> list[dict]:
        """
        Calculate mounts for a row of panels, enforcing cantilever per row.
        """
        if not panels_in_row:
            return []

        row_start_x, row_end_x = self._get_row_bounds(panels_in_row)
        row_center_y = self._get_row_center_y(panels_in_row)

        rafters = self._get_candidate_rafters(row_start_x, row_end_x)
        if not rafters:
            return [{"x": (row_start_x + row_end_x) / 2, "y": row_center_y}]

        first_rafter = self._adjust_first_rafter(row_start_x, row_end_x, rafters)
        rafters = [r for r in rafters if r >= first_rafter]

        mounts = self._place_mounts_along_row(rafters, row_center_y, row_start_x, row_end_x)

        return mounts

    @staticmethod
    def _get_row_bounds(panels_in_row: list) -> tuple[Decimal, Decimal]:
        start_x = min(p.x for p in panels_in_row)
        end_x = max(p.end_x for p in panels_in_row)
        return start_x, end_x

    @staticmethod
    def _get_row_center_y(panels_in_row: list) -> float:
        return sum(p.center_y for p in panels_in_row) / len(panels_in_row)

    def _get_candidate_rafters(self, row_start_x: Decimal, row_end_x: Decimal) -> list[Decimal]:
        return self.rafter_grid.rafters_within_panel(
            Panel(float(row_start_x), 0, row_end_x - row_start_x, Decimal("0"))
        )

    def _adjust_first_rafter(self, row_start_x: Decimal, row_end_x: Decimal, rafters: list[Decimal]) -> Decimal:
        """
        Adjusts first rafter if needed to satisfy cantilever at row end.
        """
        first_rafter = rafters[0]
        rafter_spacing = self.rafter_grid.spacing

        num_rafters_needed = math.ceil((row_end_x - first_rafter) / rafter_spacing) + 1
        last_rafter = first_rafter + (num_rafters_needed - 1) * rafter_spacing

        if row_end_x - last_rafter > self.cantilever_limit:
            shift = row_end_x - last_rafter
            if shift > self.cantilever_limit:
                raise ValueError(
                    f"Cannot satisfy cantilever for row: row_end_x={row_end_x}, "
                    f"last rafter={last_rafter}, cantilever={self.cantilever_limit}"
                )
            first_rafter += shift

        return first_rafter

    def _place_mounts_along_row(self, rafters: list[Decimal], row_center_y: Decimal,
                                row_start_x: Decimal, row_end_x: Decimal) -> list[dict]:
        """
        Place mounts along the row, enforcing max span and cantilever.
        """
        mounts = [{"x": rafters[0], "y": row_center_y}]
        last_x = rafters[0]

        for rafter in rafters[1:]:
            while rafter - last_x > self.max_span:
                next_mount = last_x + self.max_span
                next_mount = min(rafters, key=lambda r: abs(r - next_mount))
                if next_mount <= last_x:
                    break
                mounts.append({"x": next_mount, "y": row_center_y})
                last_x = next_mount

            mounts.append({"x": rafter, "y": row_center_y})
            last_x = rafter

        if row_end_x - last_x > self.cantilever_limit:
            last_mount = min(rafters, key=lambda r: abs(r - row_end_x))
            mounts.append({"x": last_mount, "y": row_center_y})

        mounts = sorted({(m["x"], m["y"]): m for m in mounts}.values(), key=lambda m: m["x"])
        return mounts


class JointCalculator:
    """
    Calculates joint locations between panels.

    Attributes:
        width (Decimal): Panel width (used for vertical joint calculation).
        tolerance (Decimal): Maximum misalignment to still consider panels adjacent.
    """

    def __init__(self, width: Decimal, tolerance: Decimal = Decimal("1.0")):
        self.width = width
        self.tolerance = tolerance

    def calculate_joints(self, panels: List[Panel]) -> List[Dict[str, Decimal]]:
        """
        Calculate all joints between panels.

        Checks three types of joints:
            - Horizontal joints: panels aligned along y-axis
            - Vertical joints: panels aligned along x-axis
            - Corner joints: panels touching at a corner

        Args:
            panels (List[Panel]): List of all panels.

        Returns:
            List[Dict[str, Decimal]]: List of joint coordinates.
        """
        joints = []
        seen = set()
        n = len(panels)

        for i in range(n):
            for j in range(i + 1, n):
                p1, p2 = panels[i], panels[j]

                joints.extend(self._horizontal_joint(p1, p2, seen))
                joints.extend(self._vertical_joint(p1, p2, seen))
                joints.extend(self._corner_joint(p1, p2, seen))

        return joints

    def _horizontal_joint(self, p1, p2, seen):
        """Check for horizontal joint between two panels."""
        joints = []
        if abs(p1.y - p2.y) <= self.tolerance and abs(p1.end_x - p2.x) < Decimal("1"):
            joint_x = p1.end_x
            joint_y = p1.center_y
            if (joint_x, joint_y) not in seen:
                joints.append({"x": joint_x, "y": joint_y})
                seen.add((joint_x, joint_y))
        return joints

    def _vertical_joint(self, p1, p2, seen):
        """Check for vertical joint between two panels."""
        joints = []
        if abs(p1.x - p2.x) <= self.tolerance and abs(p1.end_y - p2.y) < Decimal("1"):
            joint_x = p1.x + self.width / 2
            joint_y = p1.end_y
            if (joint_x, joint_y) not in seen:
                joints.append({"x": joint_x, "y": joint_y})
                seen.add((joint_x, joint_y))
        return joints

    @staticmethod
    def _corner_joint(p1, p2, seen):
        """Check for corner joint between two panels."""
        joints = []
        if abs(p1.end_x - p2.x) < Decimal("1") and abs(p1.end_y - p2.y) < Decimal("1"):
            joint_x = p1.end_x
            joint_y = p1.end_y
            if (joint_x, joint_y) not in seen:
                joints.append({"x": joint_x, "y": joint_y})
                seen.add((joint_x, joint_y))
        return joints


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
