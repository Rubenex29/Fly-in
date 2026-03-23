class ParserError(Exception):
    pass


class Connection:
    def __init__(self, zone1, zone2, metadata):
        self.zone1 = zone1
        self.zone2 = zone2
        self.max_link_capacity = 1
        self.metadata = metadata
        self.connection_metadata()

    def connection_metadata(self):
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

    def get_other_zone(self, zone):
        if zone == self.zone1:
            return self.zone2
        if zone == self.zone2:
            return self.zone1
        raise ParserError("Zone is not part of this connection")


class Zone:
    def __init__(self, name, x, y, loc, metadata, zone_type="normal"):
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
                if key == "zone" and value not in zone_lst:
                    raise ParserError(f"Invalid zone type: {value}")
                if key.strip() == "max_drones":
                    value = int(value.strip())
                    if value < 1:
                        raise ParserError("max_drones must be at least 1")
                metadata_dict[key.strip()] = value
        self.metadata = metadata_dict


class Drone:
    def __init__(self, id):
        self.id = id
        self.finished = False
        self.current_zone = Zone
        self.path = []


class Field:
    def __init__(self):
        self.zones = []

    def parse_input(self):
        with open("input.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("nb_drones"):
                    nb_drones = int(line.split()[1])
                    if nb_drones < 1:
                        raise ParserError("Number of drones " +
                                          "must be at least 1")
                    self.drones = [Drone(i) for i in range(nb_drones)]
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

    def verify_connection(self):
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
                stack.append(neighbor)
        if not path:
            raise ParserError("No valid path from start to end")

    def simulate_turns(self):
        # this is where the main logic of the simulation will go
        pass


# testing
try:
    a = Field()
    a.parse_input()
    for zone in a.zones:
        print(
            f"Zone: {zone.name}, Type: {zone.zone_type}"
        )
    a.verify_connection()
    for zone in a.zones:
        zone.zone_metadata()
        print(
            f"Zone: {zone.name}, Metadata: {zone.metadata}"
        )
    for zone in a.zones:
        for con in zone.connections:
            if con.zone1 == zone:
                print(
                    f"Connection: {con.zone1.name} - {con.zone2.name}, " +
                    f"Max Link Capacity: {con.max_link_capacity}"
                )
except ParserError as e:
    print(f"Parser Error: {e}")
