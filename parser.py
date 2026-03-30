from typing import Optional
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
        metadata: Optional[str],
        zone_type: str = "normal",
    ) -> None:
        self.name = name
        self.x = int(x)
        self.y = int(y)
        self.loc = loc
        self.metadata = metadata
        self.zone_type = zone_type
        self.connections = []

    def zone_metadata(self) -> None:
        # i want to set default values for all the metadata keys,
        # and then override them with the values from the input
        # warmimg: only 4 types of "zone" are allowed:
        # normal, blocked, restricted, and priority
        # how can i enforce this? maybe i can raise
        # an error if the value is not one of these?
        metadata_dict = {"zone": "normal", "color": None, "max_drones": 1}
        zone_lst = ["normal", "blocked", "restricted", "priority"]
        if self.metadata:
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
        self.metadata = metadata_dict


class Drone:
    def __init__(self, id: int) -> None:
        self.id = id
        self.started = False
        self.finished = False
        self.current_zone: Optional[Zone] = None
        self.path = []
        self.waiting = 0
        self.destination_zone: Optional[Zone] = None
        self.turns_to_arrive = 0


class Field:
    def __init__(self) -> None:
        self.zones = []

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
        # custo para ENTRAR numa zona
        if zone.zone_type == "blocked":
            return 10**9  # efetivamente impossível
        if zone.zone_type == "restricted":
            return 2  # 1 turno de espera + 1 de avanço
        return 1      # normal / priority

    def _heuristic(self, zone: "Zone", end_zone: "Zone") -> int:
        """
        Heurística admissível (Manhattan) com custo mínimo por passo = 1.
        """
        return abs(zone.x - end_zone.x) + abs(zone.y - end_zone.y)

    def find_shortest_path(
        self,
        start_zone: Zone,
        end_zone: Zone,
    ) -> Optional[list[Zone]]:
        """
        A*:
        1) Minimiza turnos totais (g)
        2) Em empate, prefere mais zonas priority
        """
        if start_zone == end_zone:
            return [start_zone]

        tie = 0

        # custos conhecidos
        g_score: dict[Zone, int] = {start_zone: 0}
        neg_prio_score: dict[Zone, int] = {start_zone: 0}  # mais priority => menor valor

        # para reconstruir caminho
        came_from: dict[Zone, Zone] = {}

        # heap: (f, g, -priority_count, tie, current_zone)
        open_heap: list[tuple[int, int, int, int, Zone]] = []
        f0 = self._heuristic(start_zone, end_zone)
        heapq.heappush(open_heap, (f0, 0, 0, tie, start_zone))

        while open_heap:
            f, g, neg_prio, _, current = heapq.heappop(open_heap)

            # ignora entrada antiga (stale)
            if g != g_score.get(current, float("inf")):
                continue
            if neg_prio != neg_prio_score.get(current, float("inf")):
                continue

            if current == end_zone:
                # reconstruir caminho
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

                step_cost = self._entry_turn_cost(neighbor)
                tentative_g = g + step_cost
                tentative_neg_prio = neg_prio - (
                    1 if neighbor.zone_type == "priority" else 0
                )

                old_g = g_score.get(neighbor, float("inf"))
                old_neg_prio = neg_prio_score.get(neighbor, float("inf"))

                # melhor se menor custo; em empate, mais priority
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
        turn = 0

        while any(not d.finished for d in self.drones):
            turn += 1
            print(f"Turn {turn}: ", end="")

            # 1. Drones que estavam em trânsito avançam
            for d in self.drones:
                if d.turns_to_arrive > 0:
                    d.turns_to_arrive -= 1
                    if d.turns_to_arrive == 0:
                        d.current_zone = d.destination_zone
                        if d.current_zone == end_zone:
                            d.finished = True

            # 2. Mapear ocupação ATUAL (apenas quem já está fisicamente na zona)
            occupancy = {z: 0 for z in self.zones}
            for d in self.drones:
                if d.started and not d.finished and d.turns_to_arrive == 0:
                    occupancy[d.current_zone] += 1

            # 3. Processar intenção de movimento
            for d in self.drones:
                if d.finished or d.turns_to_arrive > 0:
                    continue

                if not d.started:
                    # Lógica de entrada no sistema (Start Hub)
                    max_start = start_zone.metadata.get("max_drones", 1)
                    if occupancy[start_zone] < max_start:
                        d.started = True
                        d.current_zone = start_zone
                        occupancy[start_zone] += 1
                        print(f"D{d.id}->{start_zone.name} ", end="")
                    continue

                # Planejar próximo passo usando A*
                path = self.find_shortest_path(d.current_zone, end_zone)
                if path and len(path) > 1:
                    next_zone = path[1]

                    # Regra VII.3: Drones saindo liberam capacidade no mesmo turno
                    # Como processamos um por um, subtraímos quem está saindo
                    max_cap = next_zone.metadata.get("max_drones", 1)

                    if occupancy[next_zone] < max_cap:
                        # Executa movimento
                        cost = self._entry_turn_cost(next_zone)
                        occupancy[d.current_zone] -= 1  # Libera a atual

                        if cost > 1:  # Zona Restrita (2 turnos)
                            d.destination_zone = next_zone
                            d.turns_to_arrive = cost - 1  # Fica em trânsito
                            d.current_zone = None  # Ocupa a "conexão", não a zona
                        else:
                            d.current_zone = next_zone
                            occupancy[next_zone] += 1
                            if d.current_zone == end_zone:
                                d.finished = True

                        print(f"D{d.id}->{next_zone.name} ", end="")
            print()


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
