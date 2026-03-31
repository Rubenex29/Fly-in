from typing import Any, Optional, Union
import heapq


class ParserError(Exception):
    pass


class Connection:
    def __init__(
        self,
        zone1: "Zone",
        zone2: "Zone",
        metadata: Optional[str],
    ) -> None:
        self.zone1 = zone1
        self.zone2 = zone2
        self.max_link_capacity = 1
        self.metadata = metadata
        self.connection_metadata()

    def connection_metadata(self) -> None:
        max_link_capacity = 1
        if self.metadata:
            for item in self.metadata.split(","):
                key, value = item.split("=")
                if key.strip() == "max_link_capacity":
                    if int(value.strip()) < 1:
                        raise ParserError("max_link_capacity must" +
                                          "be at least 1")
                    max_link_capacity = int(value.strip())
                else:
                    raise ParserError("Invalid metadata" +
                                      f"connection key: {key}")
        self.max_link_capacity = max_link_capacity

    def get_other_zone(self, zone: "Zone") -> "Zone":
        if zone == self.zone1:
            return self.zone2
        if zone == self.zone2:
            return self.zone1
        raise ParserError("Zone is not part of this connection")


class Zone:
    def __init__(
        self,
        name: str,
        x: int | str,
        y: int | str,
        loc: str,
        metadata: Optional[Union[str, dict[str, Any]]],
        zone_type: str = "normal",
    ) -> None:
        self.name = name
        self.x = int(x)
        self.y = int(y)
        self.loc = loc
        self.metadata = metadata
        self.zone_type = zone_type
        self.connections: list[Any] = []

    def zone_metadata(self) -> None:
        # i want to set default values for all the metadata keys,
        # and then override them with the values from the input
        # warmimg: only 4 types of "zone" are allowed:
        # normal, blocked, restricted, and priority
        # how can i enforce this? maybe i can raise
        # an error if the value is not one of these?
        metadata_dict = {"zone": "normal", "color": "Red", "max_drones": 1}
        zone_lst = ["normal", "blocked", "restricted", "priority"]
        if self.metadata:
            value: Any = None
            if isinstance(self.metadata, str):
                for item in self.metadata.split(" "):
                    key, value = item.split("=")
                    key = key.strip()
                    if key not in metadata_dict:
                        raise ParserError(f"Invalid metadata key: {key}")
                    if "zone" in key and value not in zone_lst:
                        raise ParserError(f"Invalid zone type: {value}")
                    if key.strip() == "max_drones":
                        value = int(value.strip())
                        if value < 1:
                            raise ParserError("max_drones must be at least 1")
                    # remove first char of key
                    key1 = key[0]
                    if key1 == "z":
                        self.zone_type = value.strip()
                    metadata_dict[key.strip()] = value
        if self.loc == "end" or self.loc == "start":
            metadata_dict.update({"max_drones": float("inf")})
        self.metadata = metadata_dict


class Drone:
    def __init__(self, id: int) -> None:
        self.id = id
        self.started = False
        self.finished = False
        self.current_zone: Optional[Zone] = None
        self.path: list[Zone] = []
        self.waiting = 0
        self.destination_zone: Optional[Zone] = None
        self.turns_to_arrive = 0
        self.just_arrived = False
        self.turns = 0


class Field:
    def __init__(self) -> None:
        self.zones: list[Zone] = []

    def parse_input(self) -> list[Zone]:
        with open("input.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("nb_drones"):
                    nb_drones = int(line.split()[1])
                    if nb_drones < 1:
                        raise ParserError("Number of drones " +
                                          "must be at least 1")
                    self.drones = [Drone(i + 1) for i in range(nb_drones)]
                if line.startswith("start_hub") \
                    or line.startswith("end_hub") \
                        or line.startswith("hub"):
                    name, x, y = line.split()[1:4]

                    if " " in name or "-" in name:
                        raise ParserError("Zone name cannot contain" +
                                          f"spaces or dashes: {name}")
                    for z in self.zones:
                        if z.name == name:
                            raise ParserError("Duplicate " +
                                              f"zone name: {name}")
                    if line.startswith("start_hub"):
                        loc = "start"
                    elif line.startswith("end_hub"):
                        loc = "end"
                    elif line.startswith("hub"):
                        loc = "mid"
                    if line.count("[") == 1 and line.count("]") == 1:
                        metadata = line.split("[")[1].split("]")[0]
                    else:
                        metadata = None
                    self.zones.append(Zone(name, x, y, loc, metadata))
                elif line.startswith("connection"):
                    # connection: start-waypoint1
                    zone1_name, zone2_name = line.split()[1].split("-")
                    if line.count("[") == 1 and line.count("]") == 1:
                        metadata = line.split("[")[1].split("]")[0]
                    else:
                        metadata = None
                    # find the zones with the given names
                    # and add the connection
                    zone1 = next((z for z in self.zones
                                  if z.name == zone1_name), None)
                    zone2 = next((z for z in self.zones
                                  if z.name == zone2_name), None)
                    if not zone1 or not zone2:
                        raise ParserError("Connection references " +
                                          f"undefined zone: {line}")
                    if any((conn.zone1 == zone1 and conn.zone2 == zone2)
                           or (conn.zone1 == zone2 and conn.zone2 == zone1)
                           for conn in zone1.connections):
                        raise ParserError("Duplicate connection: " +
                                          f"{zone1_name} - {zone2_name}")
                    if zone1 and zone2:
                        connection = Connection(zone1, zone2, metadata)
                        zone1.connections.append(connection)
                        zone2.connections.append(connection)

        return self.zones

    def verify_connection(self) -> None:
        # check if we can go from start to end using all connections
        start = [z for z in self.zones if z.loc == "start"]
        end = [z for z in self.zones if z.loc == "end"]
        if len(start) != 1 or len(end) != 1:
            raise ValueError("Must have exactly one start and one end hub")
        visited = set()
        stack = [start[0]]
        path = False
        while stack:
            current_zone = stack.pop()

            if current_zone in visited:
                continue

            visited.add(current_zone)

            if current_zone == end[0]:
                path = True
                return

            for connection in current_zone.connections:
                neighbor = connection.get_other_zone(current_zone)
                if neighbor.metadata["zone"] == "blocked":
                    continue
                stack.append(neighbor)
        if not path:
            raise ParserError("No valid path from start to end")

    def find_possible_connections(self, zone: Zone) -> list[Connection]:
        possible_connections = []
        for connection in zone.connections:
            possible_connections.append(connection)
        return possible_connections

    def _entry_turn_cost(self, zone: "Zone") -> int:
        # cost to ENTER a zone
        if zone.zone_type == "blocked":
            return 10**9  # effectively impossible
        if zone.zone_type == "restricted":
            return 2  # 1 turn waiting + 1 moving forward
        return 1      # normal / priority

    def _heuristic(self, zone: "Zone", end_zone: "Zone") -> int:
        """
        Admissible heuristic (Manhattan) with minimum step cost = 1.
        """
        return abs(zone.x - end_zone.x) + abs(zone.y - end_zone.y)

    def find_shortest_path(
        self,
        start_zone: Zone,
        end_zone: Zone,
        traffic: dict[str, int]
    ) -> Optional[list[Zone]]:
        """
        A*:
        1) Minimizes total turns (g)
        2) On ties, prefers more priority zones
        """
        if start_zone == end_zone:
            return [start_zone]

        tie = 0

        # known costs
        g_score: dict[Zone, int] = {start_zone: 0}
        # more priority => lower value
        neg_prio_score: dict[Zone, int] = {start_zone: 0}

        # to reconstruct the path
        came_from: dict[Zone, Zone] = {}

        # heap: (f, g, -priority_count, tie, current_zone)
        open_heap: list[tuple[int, int, int, int, Zone]] = []
        f0 = self._heuristic(start_zone, end_zone)
        heapq.heappush(open_heap, (f0, 0, 0, tie, start_zone))

        while open_heap:
            f, g, neg_prio, _, current = heapq.heappop(open_heap)

            # ignore stale entry
            if g != g_score.get(current, float("inf")):
                continue
            if neg_prio != neg_prio_score.get(current, float("inf")):
                continue

            if current == end_zone:
                # reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path

            for connection in current.connections:
                neighbor = connection.get_other_zone(current)
                if neighbor.zone_type == "blocked":
                    continue
                penalty = traffic.get(neighbor.name, 0) * 2
                step_cost = self._entry_turn_cost(neighbor) + penalty
                tentative_g = g + step_cost
                tentative_neg_prio = neg_prio - (
                    1 if neighbor.zone_type == "priority" else 0
                )

                old_g = g_score.get(neighbor, float("inf"))
                old_neg_prio = neg_prio_score.get(neighbor, float("inf"))

                # better if lower cost; on tie, more priority zones
                if (tentative_g, tentative_neg_prio) < (old_g, old_neg_prio):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    neg_prio_score[neighbor] = tentative_neg_prio
                    tie += 1
                    new_f = tentative_g + self._heuristic(neighbor, end_zone)
                    heapq.heappush(
                        open_heap,
                        (new_f, tentative_g, tentative_neg_prio,
                         tie, neighbor),
                    )

        return None

    def simulate_turns(self) -> None:
        end_zone = next(z for z in self.zones if z.loc == "end")
        start_zone = next(z for z in self.zones if z.loc == "start")

        # Turn 0: Initial positioning
        for d in self.drones:
            d.started = True
            d.current_zone = start_zone
            d.just_arrived = False
        turn = 0
        total_cost = 0
        traffic_count = {z.name: 0 for z in self.zones}
        while any(not d.finished for d in self.drones):
            turn += 1
            moved_this_turn = []

            # Reset previous turn's just_arrived flag for all drones
            for d in self.drones:
                d.just_arrived = False

            # PHASE 1: In-transit drones advance/arrive
            for d in self.drones:
                if d.turns_to_arrive > 0:
                    d.turns_to_arrive -= 1
                    if d.turns_to_arrive == 0:
                        d.current_zone = d.destination_zone
                        # Prevents moving again this turn
                        d.just_arrived = True
                        if d.current_zone:
                            moved_this_turn.append(f"D{d.id}-" +
                                                   f"{d.current_zone.name}")
                        if d.current_zone == end_zone:
                            d.finished = True

            # PHASE 2: Movement intents
            intents = {}
            for d in self.drones:
                # If finished, flying, or just landed, DO NOT move.
                if d.finished or d.turns_to_arrive > 0 or d.just_arrived \
                     or d.current_zone is None:
                    continue
                path = self.find_shortest_path(d.current_zone,
                                               end_zone, traffic_count)
                if path and len(path) > 1:
                    next_zone = path[1]
                    traffic_count[next_zone.name] += 1
                    intents[d] = next_zone
            traffic_count = {z.name: 0 for z in self.zones}

            # PHASE 3: Map base occupancy
            occupancy = {z: 0 for z in self.zones}
            for d in self.drones:
                if d.started and not d.finished and \
                   d.turns_to_arrive == 0 and d.current_zone:
                    # If it does not want to move (or cannot)
                    # it keeps occupying space
                    if d not in intents:
                        occupancy[d.current_zone] += 1

            # PHASE 4: Execute moves respecting capacity
            for d, next_zone in intents.items():
                metadata = next_zone.metadata
                if isinstance(metadata, dict):
                    max_cap = metadata.get("max_drones", 1)
                else:
                    max_cap = 1

                if occupancy[next_zone] < max_cap:
                    # Has space: move the drone
                    occupancy[next_zone] += 1
                    cost = self._entry_turn_cost(next_zone)
                    total_cost += cost
                    d.turns += 1
                    if cost > 1:  # Restricted zone (2 turns)
                        d.destination_zone = next_zone
                        d.turns_to_arrive = cost - 1
                        if d.current_zone is not None:
                            connection_name = \
                                f"{d.current_zone.name}-{next_zone.name}"
                        moved_this_turn.append(f"D{d.id}-{connection_name}")
                        d.current_zone = None  # Stays on the connection
                    else:  # Normal/Priority zone (1 turn)
                        d.current_zone = next_zone
                        if d.current_zone == end_zone:
                            d.finished = True
                        moved_this_turn.append(f"D{d.id}-{next_zone.name}")
                else:
                    # No space: drone fails to move and stays in place
                    if d.current_zone:
                        occupancy[d.current_zone] += 1

            # Print strictly formatted output
            if moved_this_turn:
                print(f"Turn {turn}: {' '.join(moved_this_turn)} " +
                      f"Total moved: {len(moved_this_turn)}")
        print(f"Turns with total cost {total_cost}")
        total = 0
        for d in self.drones:
            total += d.turns
        print(f"Average number of turns per drone: {total / len(self.drones)}")


# testing
try:
    a = Field()
    a.parse_input()
    for zone in a.zones:
        zone.zone_metadata()
    a.verify_connection()
    a.simulate_turns()
except ParserError as e:
    print(f"Parser Error: {e}")
