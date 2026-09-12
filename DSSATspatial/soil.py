#soil.py
#created and modified by sakthivel sivakumar

#import libraries
import os
from .partypes import (
    NumberType, DescriptionType, Record,
    CodeType, parse_pars_line
)

DSSAT_MODULE_PATH = os.path.dirname(__file__)

SURF_PARS_1 = [
    "name", "soil_data_source", "soil_clasification", "soil_depth", 
    "soil_series_name"
]
SURF_PARS_2 = ['site', 'country', 'lat', 'long', 'scs_family']
SURF_PARS_3 = [
    'scom', 'salb', 'slu1', 'sldr', 'slro', 'slnf', 'slpf', 'smhb', 
    'smpx', 'smke'
]
PROF_PARS_1 = [
    'slb', 'slmh', 'slll', 'sdul', 'ssat', 'srgf', 'ssks', 'sbdm', 'sloc', 
    'slcl', 'slsi', 'slcf', 'slni', 'slhw', 'slhb', 'scec', 'sadc'
]
PROF_PARS_2 = [
    'slb', 'slpx', 'slpt', 'slpo', 'caco3', 'slal', 'slfe', 'slmn', 'slbs', 
    'slpa', 'slpb', 'slke', 'slmg', 'slna', 'slsu', 'slec', 'slca'
]

class SoilProfile(Record):  # Downgraded from TabularRecord to bypass strict object typing
    prefix = None
    dtypes = {
        'name': DescriptionType, 'soil_data_source': DescriptionType, 
        'soil_clasification': DescriptionType, 'soil_depth': NumberType, 
        'soil_series_name': DescriptionType, 'site': DescriptionType, 
        'country': DescriptionType, 'lat': NumberType, 'long': NumberType, 
        'scs_family': DescriptionType, 'scom': DescriptionType, 'salb': NumberType, 
        'slu1': NumberType, 'sldr': NumberType, 'slro': NumberType, 
        'slnf': NumberType, 'slpf': NumberType, 'smhb': CodeType, 
        'smpx': CodeType, 'smke': CodeType
    }
    pars_fmt = {
        'name': '<11', 'soil_data_source': "<11", 'soil_clasification': '<6', 
        'soil_depth': '>4.0f', 'soil_series_name': '<64', 'site': '<11', 
        'country': '<11', 'lat': '>8.3f', 'long': '>8.3f', 'scs_family': '<64', 
        'scom': '>5', 'salb': '>5.2f', 'slu1': '>5.1f', 'sldr': '>5.2f', 
        'slro': '>5.0f', 'slnf': '>5.2f', 'slpf': '>5.2f', 'smhb': '>5', 
        'smpx': '>5', 'smke': '>5'
    }

    def __init__(self, raw_block: str, max_depth: float, **kwargs):
        super().__init__()
        for name, value in kwargs.items():
            self.__setitem__(name, value)
        
        # MOCK TABLE: Satisfies filex.py depth query (value.table[-1]["slb"])
        self.table = [{"slb": max_depth}]
        self["soil_depth"] = max_depth
        
        # Cache raw string block for immediate dumping
        self.raw_block = raw_block

    def __setitem__(self, key, value):
        if key == "name":
            assert len(value) == 10, "Soil profile Name must be 10 characters long"
        super().__setitem__(key, value)
    
    def _write_sol(self):
        # Override to dump the raw text directly into the simulation folder
        return self.raw_block
    
    @property
    def str(self):
        return self['name']

    @classmethod
    def from_block(cls, soil_id, header_lines, block_lines):
        kwargs = {}
        valid_lines = [line for line in block_lines if line.strip() and not line.startswith('!') and not line.startswith('@')]
        
        if len(valid_lines) >= 3:
            kwargs.update(parse_pars_line(valid_lines[0][1:], {par: cls.pars_fmt[par] for par in SURF_PARS_1}))
            if "soil_depth" in kwargs:
                del kwargs["soil_depth"]
            kwargs.update(parse_pars_line(valid_lines[1][1:], {par: cls.pars_fmt[par] for par in SURF_PARS_2}))
            kwargs.update(parse_pars_line(valid_lines[2][1:], {par: cls.pars_fmt[par] for par in SURF_PARS_3}))
        
        # Extract max depth (SLB) from the final layer in the Tier 1 array
        max_depth = 0.0
        layer_lines = []
        parsing_layers = False
        
        for line in block_lines:
            if '@  SLB  SLMH' in line:
                parsing_layers = True
                continue
            if parsing_layers:
                if line.startswith('@'):
                    break
                if line.strip() and not line.startswith('!'):
                    layer_lines.append(line)
                    
        if layer_lines:
            try:
                # Target the first 6 characters of the line to extract the SLB float
                max_depth = float(layer_lines[-1][:6].strip())
            except ValueError:
                pass
                
        # Reconstruct exactly what DSSAT expects to read natively
        raw_string = "*SOILS: General DSSAT Soil Input File\n\n" + "".join(block_lines)
        
        return cls(raw_string, max_depth, **kwargs)

    @classmethod
    def from_file(cls, profile: str, file: str):
        with open(file, "r") as f:
            lines = f.readlines()
            
        block_lines = []
        in_profile = False
        
        for line in lines:
            if line.startswith('*' + profile):
                in_profile = True
            if in_profile:
                if line.startswith('*') and not line.startswith('*' + profile):
                    break
                block_lines.append(line)
                
        if not block_lines:
            raise ValueError(f"{profile} profile not in {file} file")
            
        return cls.from_block(profile, [], block_lines)