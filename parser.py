from typing import List, Dict, Any

class Field:
    def __init__(self):
        self.start_hub: Dict[Any, Any] = {}
        self.end_hub: Dict[Any, Any] = {}
        self.hublist: List[Dict[Any, Any]] = []

    def parse_input(self):
        with open('input.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                if line == '\n':
                    continue
                if line.startswith('nb_drones') or line.startswith('start_hub') or line.startswith('end_hub') or line.startswith('hub'):
                    zone_name = line.split(' ')[1].strip()
                    if "-"
                line = line.strip()
                if line.startswith('nb_drones'):
                    self.nb_drones = int(line.split(': ')[1].strip())
                elif line.startswith('start_hub'):
                    self.start_hub = {line.split(' ')[1].strip():
                                      (int(line.split(' ')[2].strip()),
                                       int(line.split(' ')[3].strip()),
                                       line.split(' ')[4].strip())}
                elif line.startswith('end_hub'):
                    self.end_hub = {line.split(' ')[1].strip():
                                    (int(line.split(' ')[2].strip()),
                                     int(line.split(' ')[3].strip()),
                                     line.split(' ')[4].strip())}
                elif line.startswith('hub'):
                    self.hublist.append({line.split(' ')[1].strip():
                                         (int(line.split(' ')[2].strip()),
                                          int(line.split(' ')[3].strip()),
                                          line.split(' ')[4].strip())})
#testing
a = Field()
a.parse_input()
print(a.nb_drones)
print(a.start_hub)
print(a.end_hub)
print(a.hublist)