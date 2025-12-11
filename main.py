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
    Calculates the placement of mounts for panels on rafters.

    Attributes:
        rafter_grid (RafterGrid): The underlying rafter grid.
        width (Decimal): Panel width (used for center calculations).
        max_span (Decimal): Maximum allowed distance between mounts.
        cantilever_limit (Decimal): Maximum distance a mount can be from panel edge.
    """

    def __init__(self, rafter_grid: RafterGrid,
                 width: Decimal,
                 max_span: Decimal,
                 cantilever_limit: Decimal):
        self.rafter_grid = rafter_grid
        self.width = width
        self.max_span = max_span
        self.cantilever_limit = cantilever_limit

    def calculate_mounts(self, panel: Panel) -> list[dict]:
        """
        Calculate the mount positions for a single panel.

        Rules:
            - If no rafter intersects the panel, place one mount at the panel center.
            - Ensure mounts are within MAX_SPAN from each other.
            - Respect cantilever limit at panel edges.

        Args:
            panel (Panel): The panel to calculate mounts for.

        Returns:
            List[dict]: List of mounts with 'x' and 'y' coordinates.
        """
        rafters = self.rafter_grid.rafters_within_panel(panel)

        if not rafters:
            return [{"x": panel.x + self.width / 2, "y": panel.center_y}]

        mounts = [{"x": min(rafters, key=lambda r: abs(r - panel.x)), "y": panel.center_y}]
        last_x = mounts[-1]["x"]

        for rafter in rafters[1:]:
            while rafter - last_x > self.max_span:
                next_mount = min(rafters, key=lambda r: abs(last_x + self.max_span - r))
                if next_mount != last_x:
                    mounts.append({"x": next_mount, "y": panel.center_y})
                    last_x = next_mount
            mounts.append({"x": rafter, "y": panel.center_y})
            last_x = rafter

        if panel.end_x - last_x > self.cantilever_limit:
            closest = min(rafters, key=lambda r: abs(panel.end_x - r))
            if closest != last_x:
                mounts.append({"x": closest, "y": panel.center_y})

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

    All key constants (panel dimensions, rafter spacing, edge clearance, etc.) are injected
    via the constructor for flexibility and testability.
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
        self.mount_calculator = MountCalculator(self.rafter_grid, width, max_span, cantilever_limit)
        self.joint_calculator = JointCalculator(width, joint_tolerance)

    def plan_supports(self) -> Dict[str, List[Dict[str, Decimal]]]:
        """
        Calculate the complete layout of mounts and joints for all panels.

        Returns:
            Dict[str, List[Dict[str, Decimal]]]:
                'mounts' -> list of mount coordinates,
                'joints' -> list of joint coordinates
        """
        mounts = []
        for panel in self.panels:
            mounts.extend(self.mount_calculator.calculate_mounts(panel))
        joints = self.joint_calculator.calculate_joints(self.panels)
        mounts.sort(key=lambda m: (m["y"], m["x"]))
        joints.sort(key=lambda j: (j["y"], j["x"]))
        return {"mounts": mounts, "joints": joints}
