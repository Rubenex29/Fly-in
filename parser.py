class Zone:
    def __init__(self, name, x, y, zone_type="normal", max_drones=1):
        self.name = name
        self.x = int(x)
        self.y = int(y)
        self.zone_type = zone_type
        self.max_drones = max_drones
        self.connections = []


class Field:
    def __init__(self):
        self.zones = []

    def parse_input(self):
        with open("input.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("start_hub") \
                    or line.startswith("end_hub") \
                        or line.startswith("hub"):
                    name, x, y = line.split()[1:4]
                    if " " in name or "-" in name:
                        raise ValueError("Zone name cannot contain" +
                                         f"spaces or dashes: {name}")
                    for z in self.zones:
                        if z.name == name:
                            raise ValueError("Duplicate " +
                                             f"zone name: {name}")
                    if line.startswith("start_hub"):
                        start_hub = Zone(name, x, y, "start")
                        self.zones.append(start_hub)
                    elif line.startswith("end_hub"):
                        end_hub = Zone(name, x, y, "end")
                        self.zones.append(end_hub)
                    elif line.startswith("hub"):
                        zone = Zone(name, x, y, "normal", 1)
                        self.zones.append(zone)
                elif line.startswith("connection"):
                    # connection: start-waypoint1
                    zone1_name, zone2_name = line.split()[1].split("-")
                    # find the zones with the given names
                    # and add the connection
                    zone1 = next((z for z in self.zones
                                  if z.name == zone1_name), None)
                    zone2 = next((z for z in self.zones
                                  if z.name == zone2_name), None)
                    if zone1 and zone2:
                        zone1.connections.append(zone2)
                        zone2.connections.append(zone1)

        return self.zones

    def verify_connection(self):
        # check if we cam go from start to end using all connections
        start = [z for z in self.zones if z.zone_type == "start"]
        end = [z for z in self.zones if z.zone_type == "end"]
        if len(start) != 1 or len(end) != 1:
            raise ValueError("Start or end zone not found")
        visited = set()
        stack = [start[0]]
        while stack:
            current_zone = stack.pop()

            if current_zone in visited:
                continue

            visited.add(current_zone)

            if current_zone == end[0]:
                return True

            for neighbor in current_zone.connections:
                stack.append(neighbor)
        return False


# testing
try:
    a = Field()
    a.parse_input()
    for zone in a.zones:
        print(
            f"Zone: {zone.name}, Type: {zone.zone_type}, Connections:"
            + f"{[z.name for z in zone.connections]}"
        )
    print(f"Connection valid: {a.verify_connection()}")
except Exception as e:
    print(f"Error: {e}")
