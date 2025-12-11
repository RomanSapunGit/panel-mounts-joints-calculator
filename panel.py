from decimal import Decimal


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
