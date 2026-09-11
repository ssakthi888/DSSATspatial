#soil.py
#created and modified by sakthivel sivakumar

import os

DSSAT_MODULE_PATH = os.path.dirname(__file__)

class SoilProfile:
    def __init__(self, raw_lines: list[str]):
        self.raw_lines = raw_lines
        self.sldp = 0.0
        
        # Read from the bottom of the block to find the last data layer and extract its depth
        for line in reversed(self.raw_lines):
            if line.strip() and not line.startswith("@") and not line.startswith("*"):
                try:
                    self.sldp = float(line.split()[0])
                    break
                except (ValueError, IndexError):
                    continue
        
        # Mock table attribute to satisfy filex.py depth extraction (value.table[-1]["slb"])
        self.table = [{"slb": self.sldp}]
        
        # Extract the profile name from the first line (e.g., *IB00000001)
        first_line = self.raw_lines[0]
        self.name = first_line.split()[0].replace("*", "") if self.raw_lines else "UNKNOWN"

    def _write_sol(self):
        out_str = "*SOILS: General DSSAT Soil Input File\n\n"
        out_str += "".join(self.raw_lines)
        return out_str
        
    @property
    def str(self):
        return self.name