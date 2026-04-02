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

## Algorithm Overview

This project simulates drone movement on a graph of hubs and connections, with capacity constraints and turn-based execution.

### 1. Input parsing and validation

The program reads `input.txt` and builds:

- **Zones (hubs)**: `start`, `end`, and intermediate hubs.
- **Connections** between zones.
- **Metadata** for zones and connections, including:
  - `zone` type (`normal`, `restricted`, `blocked`, `priority`)
  - `max_drones` (zone capacity)
  - `max_link_capacity` (connection capacity)
- **Drones** from `nb_drones`.

Validation includes:

- exactly one start and one end hub;
- valid metadata formats and values;
- no duplicate zone names or duplicate undirected connections;
- at least one traversable path from start to end (`verify_connection` with DFS).

---

### 2. Pathfinding strategy (A*)

Each drone plans movement using A* (`find_shortest_path`).

#### Cost model

For a candidate neighbor zone:

- `step_cost = entry_cost + traffic_penalty`
- `entry_cost`:
  - `normal` / `priority`: `1`
  - `restricted`: `2`
  - `blocked`: effectively impossible (`10**9`)

#### Traffic penalty

`_traffic_penalty(zone, traffic)` uses predicted demand (`pressure`) for that zone:

- `pressure` is the number of drones currently intending to enter that zone in the current planning phase;
- penalty grows with pressure and grows faster when pressure exceeds capacity (`max_drones`);
- restricted zones receive an additional bias penalty.

`pressure` can be greater than `max_drones` because multiple drones may intend the same destination before hard capacity checks are applied.

#### Heuristic

A* uses Manhattan distance:

`h(n) = |x_n - x_end| + |y_n - y_end|`

with total priority key:

`f(n) = g(n) + h(n)`

---

### 3. Priority and tie-breaking in A*

The open set stores tuples:

`(f, g, neg_prio, tie, zone)`

Heap ordering in Python is lexicographic, so the expansion order is:

1. lower `f`
2. then lower `g`
3. then lower `neg_prio` (more priority zones visited is better)
4. then lower `tie` (deterministic insertion order)

Although `f` may not be used later in expressions, it is actively used by `heapq` to choose which node is popped first.

---

### 4. Why stale-entry checks are required

Because `heapq` does not support in-place key decrease, improved states are pushed as new entries.  
Older entries for the same zone remain in the heap.

The checks:

- `if g != g_score[current]: continue`
- `if neg_prio != neg_prio_score[current]: continue`

discard outdated entries when they are popped later.

So the algorithm does **not** remove bad entries immediately; it ignores them safely when they reach the top.

---

### 5. Meaning of A* score tables

- `g_score[zone]`: best known real cost from start to `zone`.
- `neg_prio_score[zone]`: best known secondary score (priority preference).
- `g`, `neg_prio` popped from heap: values of the specific candidate state currently being evaluated.

For a first-time-discovered neighbor:

- `old_g` and `old_neg_prio` default to infinity (`dict.get(..., inf)`),
- so the new candidate is accepted.

---

### 6. Turn simulation and hard constraints

Simulation (`simulate_turns`) runs in turns with four phases:

1. advance in-transit drones;
2. build intents using A*;
3. compute current occupancy;
4. execute allowed moves.

Important distinction:

- A* and penalties are **soft guidance** (planning preference).
- Capacity checks in phase 4 are **hard rules**:
  - connection limit: `max_link_capacity`
  - zone limit: `max_drones`

Therefore, multiple drones may intend the same destination, but only allowed moves are committed.

---

### 7. Scope of traffic prediction

`traffic_count` is used as a per-turn prediction signal during intent generation.  
It represents immediate expected pressure, not a full future global traffic forecast across all subsequent turns.

For observability, reset timing matters:

- if reset before printing, printed values appear as zeros;
- reset should be positioned consistently with intended debug output.

---

### 8. Determinism notes

When costs are equal, outcome depends on deterministic tie-breaking (`tie`) and insertion order.  
This prevents unstable behavior between runs with identical input.

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

## Detailed Control Flow (Loops and Conditions)

This section explains the practical meaning of each major loop and condition in the algorithm.

### A) Connectivity validation (`verify_connection`)

The code performs a DFS from `start` to ensure `end` is reachable.

#### Main loop
- `while stack:`  
  Continues while there are zones left to explore.

#### Per-node logic
- `current_zone = stack.pop()`  
  Takes one zone from the stack.

- `if current_zone in visited: continue`  
  If already explored, skip it.  
  This prevents repeated work and avoids infinite loops in cyclic graphs.

- `visited.add(current_zone)`  
  Marks zone as explored.

- `if current_zone == end[0]: return`  
  If end is reached, connectivity is confirmed.

#### Neighbor expansion
- For each connection from `current_zone`, obtain `neighbor`.
- `if neighbor.metadata["zone"] == "blocked": continue`  
  Blocked zones are not traversable for connectivity purposes.
- Otherwise, push neighbor into `stack`.

If DFS finishes without finding end, parser raises:
- `ParserError("No valid path from start to end")`.

---

### B) A* pathfinding (`find_shortest_path`)

A* finds a low-cost path considering:
- entry cost by zone type,
- dynamic traffic penalty,
- heuristic distance to goal.

#### Main frontier loop
- `while open_heap:`  
  Process candidate zones ordered by `(f, g, neg_prio, tie, zone)`.

- `f, g, neg_prio, _, current = heapq.heappop(open_heap)`  
  Retrieves the current best candidate by heap order.

#### Stale-entry filtering
- `if g != g_score.get(current, inf): continue`
- `if neg_prio != neg_prio_score.get(current, inf): continue`

These conditions skip outdated heap entries.  
Reason: Python `heapq` does not decrease priority in place; better states are pushed again, old ones remain and must be ignored when popped.

#### Goal check
- `if current == end_zone:` reconstruct and return path.

#### Neighbor loop
- `for connection in current.connections:` evaluates each adjacent zone.

- `if neighbor.zone_type == "blocked": continue`  
  Blocked zones are excluded from A* expansion.

- Compute candidate scores:
  - `tentative_g = g + step_cost`
  - `tentative_neg_prio = neg_prio - 1` if neighbor is `priority`, else unchanged.

- Read previous best:
  - `old_g = g_score.get(neighbor, inf)`
  - `old_neg_prio = neg_prio_score.get(neighbor, inf)`

#### Improvement condition
- `if (tentative_g, tentative_neg_prio) < (old_g, old_neg_prio):`
  Update only if:
  1. lower real cost `g`, or
  2. same `g` but better priority tie-break (`neg_prio` lower).

If true, algorithm updates:
- `came_from[neighbor]`
- `g_score[neighbor]`
- `neg_prio_score[neighbor]`
- pushes a new heap entry with updated `f`.

If heap empties with no goal, returns `None`.

---

### C) Turn simulation (`simulate_turns`)

The simulation runs until all drones finish.

#### Global loop
- `while any(not d.finished for d in self.drones):`
  Continue while at least one drone is unfinished.

---

#### Phase 1: advance drones already in transit
- For each drone:
  - `if d.turns_to_arrive > 0:` decrement remaining travel turns.
  - When reaches zero:
    - assign `current_zone = destination_zone`,
    - set `just_arrived = True` (cannot move again this same turn),
    - if end reached: `finished = True`.

---

#### Phase 2: build movement intents
- Drones are sorted by heuristic distance to end (closer first).
- Per drone, skip intent generation if:
  - `d.finished` (already done),
  - `d.turns_to_arrive > 0` (still flying),
  - `d.just_arrived` (landed this turn),
  - `d.current_zone is None` (currently on link / no zone).

- If valid:
  - run A* from current zone to end using current traffic snapshot,
  - if path exists and has next step, register intent for `next_zone`,
  - increase `traffic_count[next_zone.name]` as predicted pressure.

---

#### Phase 3: base occupancy map
- Initialize `occupancy` for all zones.
- For drones that remain stationary this turn (`d not in intents`), increment occupancy of their current zone.
- This models space already occupied before new movements are accepted.

---

#### Phase 4: apply intents with hard constraints
For each `(drone, next_zone)` intent:
- Find the corresponding connection and link id.
- Read destination capacity (`max_drones`).

Movement is allowed only if both conditions hold:
1. link usage this turn `< conn.max_link_capacity`
2. destination occupancy `< max_drones`

If both pass:
- consume link slot,
- increase destination occupancy,
- add movement cost,
- update drone state:
  - restricted (`cost > 1`): drone stays in transit (`current_zone = None`, `turns_to_arrive > 0`)
  - normal/priority (`cost == 1`): immediate arrival to `next_zone`.

If condition fails:
- drone does not move and remains occupying its current zone.

---

### D) Practical meaning of “already visited zone”

There are two “already seen” notions in the project:

1. **DFS (`verify_connection`)**  
   `if current_zone in visited: continue`  
   Means: zone already fully explored for connectivity check.

2. **A* (`find_shortest_path`)**  
   A zone may appear multiple times in heap via different paths.  
   The stale-entry checks skip older, worse versions of the same zone state.

Both mechanisms prevent redundant processing and keep search behavior correct.
