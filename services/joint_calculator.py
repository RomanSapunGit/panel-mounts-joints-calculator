from decimal import Decimal
from typing import List, Dict

from panel import Panel


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
