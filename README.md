*This project has been created as part of the 42 curriculum by rumontei.*

# Fly-in

## Description

Fly-in is a pathfinding and traffic-scheduling simulation where multiple drones must travel from a single start hub to an end hub through a constrained graph of zones and connections.

The project goal is to minimize movement cost and avoid congestion while respecting map constraints such as:

- blocked zones,
- restricted zones,
- priority zones,
- per-zone capacity (`max_drones`),
- per-connection constraints (`max_link_capacity`, parsed and validated).

At runtime, the program parses `input.txt`, builds the graph, validates it, computes movement decisions turn by turn, and prints a visual turn-based trace of drone activity.

## Instructions

### Requirements

- Python 3 (tested with `python3`)
- `make` (optional but recommended)

### Run with Makefile

```bash
make run
```

### Run directly

```bash
python3 Fly-in.py
```

### Input file

The simulator reads from `input.txt` at the repository root.

To test another map quickly, replace the input file content with one of the maps available under:

- `maps/easy/`
- `maps/medium/`
- `maps/hard/`
- `maps/challenger/`

## Algorithm Choices and Implementation Strategy

The implementation uses a graph-based model:

- `Zone` nodes represent hubs with coordinates, type, and metadata.
- `Connection` edges represent links between zones.
- `Drone` objects keep per-drone runtime state.
- `Field` orchestrates parsing, validation, pathfinding, and simulation.

### Parsing and validation

1. Parse hubs and connections from `input.txt`.
2. Validate schema and metadata values.
3. Reject invalid maps (duplicate nodes/edges, missing references, invalid capacities, etc.).
4. Verify at least one traversable route from start to end.

### Pathfinding strategy

The route search is based on A* (`find_shortest_path`) with:

- **g-score**: accumulated movement cost,
- **heuristic**: Manhattan distance,
- **tie-break rule**: favor paths crossing more priority zones when costs are equal.

Movement cost combines:

- base entry cost by zone type (`normal`, `priority`, `restricted`, `blocked`),
- dynamic traffic penalty (congestion-aware), considering:
	- current demand for a zone,
	- zone capacity,
	- overload escalation,
	- zone-type bias.

This strategy reduces naive greedy movement and improves global traffic distribution across turns.

### Turn simulation strategy

Each turn is processed in phases:

1. Advance drones already in transit.
2. Compute movement intents from active drones.
3. Build occupancy map for zones.
4. Execute moves only if capacity rules are respected.

This phased approach avoids inconsistent states and makes capacity handling deterministic.

## Visual Representation

The project uses a text-based visual representation in the terminal.

For each turn, the simulator prints a concise movement log like:

- `Turn N: D1-zoneA D2-zoneB ... Total moved: X`

At the end, it prints summary metrics:

- total cost,
- average turns per drone.

How this improves user experience:

- Makes the simulation easy to follow turn by turn.
- Shows congestion effects and bottlenecks explicitly.
- Helps debug map design and algorithm behavior without external GUI tools.

## Resources

Classic references used for the topic:

- A* Search Algorithm (overview): https://en.wikipedia.org/wiki/A*_The simulator reads from `input.txt` at the repository root.
search_algorithm
- Graph theory basics: https://en.wikipedia.org/wiki/Graph_theory
- Python `heapq` (priority queues): https://docs.python.org/3/library/heapq.html
- Python typing: https://docs.python.org/3/library/typing.html

### AI Usage Disclosure

AI was used to support algorithm-oriented development tasks, mainly:

- refining and comparing pathfinding strategies,
- improving congestion penalty design,
- discussing edge cases in turn scheduling and metadata validation,
- reviewing code clarity and documentation wording.

In this project, AI assistance was specifically used in the implemented algorithmic parts (pathfinding and movement-cost logic), while final integration and validation decisions remained manual.
