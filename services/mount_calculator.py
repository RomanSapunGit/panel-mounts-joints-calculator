import math
from decimal import Decimal

from panel import Panel


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
