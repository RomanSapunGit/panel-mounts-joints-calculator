# Solar Support Planner

This project calculates the optimal placement of mounts and joints for solar panels on a roof with a rafter grid. It respects the following rules:

- Mounts must sit on rafters.
- Maximum spacing between mounts (`MAX_SPAN`) is enforced.
- Mounts cannot exceed cantilever limits from panel edges (`CANTILEVER_LIMIT`).
- Joints are calculated where panels touch horizontally, vertically, or at corners.
- All constants are configurable for flexibility.

---

## Project Structure

```
solar_support/
├── main.py              # Core classes: Panel, RafterGrid, MountCalculator, JointCalculator, SolarSupportPlanner
├── tests/
│   ├──__init__.py
│   └── test_planner.py  # Test suite using pytest
└── run_example.py       # Example script to run the planner
```

---


## Mount Placement Rules

1. **Mounts are always placed on rafters.**  
2. **Edge cantilever:**  
   - Normally, the first and last mount should be within `CANTILEVER_LIMIT` from the panel edges.  
   - **If no rafter exists within the cantilever limit**, the closest valid rafter is used instead.  
     Example:  
     - Panel right edge at x=135.  
     - Cantilever limit = 16.  
     - Nearest rafter = 117 (distance 17.7 > 16).  
     - Mount is placed on rafter 117, even though it exceeds the cantilever limit.  
3. **Spacing between mounts** cannot exceed `MAX_SPAN`. Additional mounts are added on intermediate rafters as needed.  
4. **No mounts are placed outside the panel’s edge clearance.**

---

## Setup

1. **Install Python 3.10+** (or newer).

2. **Install pytest** for running the test suite:

```
pip install pytest
```

---

## Running the Application

1. Edit `run_example.py` or create a new script to define panel positions and constants

2. Run the script:

```
python run_example.py
```

This prints the calculated mount and joint positions for the given panels.

---

## Running Tests

The project includes a test suite using `pytest`. To verify that everything works:

1. From the project root, run:

```
pytest tests/
```

2. To see detailed output:

```
pytest -v tests/
```

The tests verify that:

- All mounts are on valid rafters.
- Mounts respect edge clearance.
- Mount spacing does not exceed `MAX_SPAN`.
- Cantilever rules are respected.
- Joints are correctly created for horizontally, vertically, and corner-adjacent panels.

---

## Configuration

All key constants are injected via the `SolarSupportPlanner` constructor, including:

- `width`: Panel width.
- `height`: Panel height.
- `spacing`: Distance between rafters.
- `first_rafter`: X-coordinate of the first rafter.
- `edge_clearance`: Minimum distance from panel edge to rafter.
- `max_span`: Maximum spacing between mounts.
- `cantilever_limit`: Maximum distance a mount can be from a panel edge.
- `joint_tolerance`: Maximum misalignment for panels to still form a joint.

This allows testing different roof layouts and panel sizes without modifying the core code.
