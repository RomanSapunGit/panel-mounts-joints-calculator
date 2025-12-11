import math
from decimal import Decimal

from panel import Panel


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
