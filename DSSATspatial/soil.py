import os
import sys
from rosetta import rosetta, SoilData
from .partypes import NumberType, DescriptionType, Record, CodeType

DSSAT_MODULE_PATH = os.path.dirname(__file__)

SURF_PARS_1 = ["name", "soil_data_source", "soil_clasification", "soil_depth", "soil_series_name"]
SURF_PARS_2 = ['site', 'country', 'lat', 'long', 'scs_family']
SURF_PARS_3 = ['scom', 'salb', 'slu1', 'sldr', 'slro', 'slnf', 'slpf', 'smhb', 'smpx', 'smke']
PROF_PARS_1 = ['slb', 'slmh', 'slll', 'sdul', 'ssat', 'srgf', 'ssks', 'sbdm', 'sloc', 'slcl', 'slsi', 'slcf', 'slni', 'slhw', 'slhb', 'scec', 'sadc']
PROF_PARS_2 = ['slb', 'slpx', 'slpt', 'slpo', 'caco3', 'slal', 'slfe', 'slmn', 'slbs', 'slpa', 'slpb', 'slke', 'slmg', 'slna', 'slsu', 'slec', 'slca']

pars_fmt = {
    'name': '<11', 'soil_data_source': '<11', 'soil_clasification': '<6',
    'soil_depth': '>4.0f', 'soil_series_name': '<64', 'site': '<11',
    'country': '<11', 'lat': '>8.3f', 'long': '>8.3f', 'scs_family': '<64',
    'scom': '>5', 'salb': '>5.2f', 'slu1': '>5.1f', 'sldr': '>5.2f',
    'slro': '>5.0f', 'slnf': '>5.2f', 'slpf': '>5.2f', 'smhb': '>5',
    'smpx': '>5', 'smke': '>5',
    'slb': '>5.0f', 'slmh': '<5', 'slll': '>5.3f', 'sdul': '>5.3f',
    'ssat': '>5.3f', 'srgf': '>5.3f', 'ssks': '>5.2f', 'sbdm': '>5.2f',
    'sloc': '>5.2f', 'slcl': '>5.1f', 'slsi': '>5.1f', 'slcf': '>5.1f',
    'slni': '>5.3f', 'slhw': '>5.1f', 'slhb': '>5.1f', 'scec': '>5.1f',
    'sadc': '>5.1f',
    'slpx': '>5.1f', 'slpt': '>5.1f', 'slpo': '>5.1f', 'caco3': '>5.2f',
    'slal': '>5.2f', 'slfe': '>5.2f', 'slmn': '>5.2f', 'slbs': '>5.2f',
    'slpa': '>5.2f', 'slpb': '>5.2f', 'slke': '>5.2f', 'slmg': '>5.2f',
    'slna': '>5.2f', 'slsu': '>5.2f', 'slec': '>5.2f', 'slca': '>5.2f'
}

def format_val(val, fmt):
    if val is None or val == "-99" or val == -99 or str(val).strip() == "":
        width = int(fmt[1:].split('.')[0])
        return format(-99, f'>{width}.0f')[:width]
    
    fmt_core = fmt[1:]
    width = int(fmt_core.split('.')[0])
    
    if 'f' in fmt_core:
        try:
            return format(float(val), fmt_core)[:width]
        except ValueError:
            return format(-99, f'>{width}.0f')[:width]
    else:
        if fmt[0] == '<':
            return f"{str(val):<{width}}"[:width]
        else:
            return f"{str(val):>{width}}"[:width]

def van_genuchten(theta_r, theta_s, alpha, n, h):
    alpha = 10**alpha 
    n = 10**n
    m = 1 - 1/n 
    theta = theta_r + (theta_s - theta_r)/(1 + abs(alpha * h)**n)**m
    return theta

def estimate_from_texture(slcl, slsi, sbdm=None, sloc=None):
    if sbdm and sbdm != "-99":
        soil_data = SoilData.from_array([[100 - float(slcl) - float(slsi), float(slsi), float(slcl), float(sbdm)]])
        vangenuchten_pars, _, _ = rosetta(3, soil_data)
    else:
        soil_data = SoilData.from_array([[100 - float(slcl) - float(slsi), float(slsi), float(slcl)]])
        vangenuchten_pars, _, _ = rosetta(2, soil_data)
        
    vangenuchten_pars = vangenuchten_pars[0]
    ssat = vangenuchten_pars[1]
    ssks = (10**vangenuchten_pars[-1]) / 24
    slll = van_genuchten(*vangenuchten_pars[:-1], h=1500)
    sdul = van_genuchten(*vangenuchten_pars[:-1], h=33)
    
    if (not sbdm or sbdm == "-99") and sloc and sloc != "-99":
        sbdm = 1.386 - 0.078 * float(sloc) + 0.001 * float(slsi) + 0.001 * float(slcl)
        
    return {"ssat": ssat, "ssks": ssks, "slll": slll, "sdul": sdul, "sbdm": sbdm}

class SoilProfile(Record):
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

    def __init__(self, raw_block: str, max_depth: float, **kwargs):
        super().__init__()
        for name, value in kwargs.items():
            self.__setitem__(name, value)
        
        self.table = [{"slb": max_depth}]
        self["soil_depth"] = max_depth
        self.raw_block = raw_block

    def __setitem__(self, key, value):
        if key == "name":
            assert len(value) == 10, "Soil profile Name must be 10 characters long"
        super().__setitem__(key, value)
    
    def _write_sol(self):
        return self.raw_block
    
    @property
    def str(self):
        return self['name']

    @classmethod
    def from_block(cls, soil_id, header_lines, block_lines):
        kwargs = {'name': soil_id}
        valid_lines = [line for line in block_lines if line.strip() and not line.startswith('!') and not line.startswith('@')]
        
        formatted_lines = ["*SOILS: General DSSAT Soil Input File\n\n"]
        formatted_lines.append(block_lines[0]) 
        
        formatted_lines.append("@SITE        COUNTRY          LAT     LONG SCS FAMILY\n")
        formatted_lines.append(valid_lines[1] + ("\n" if not valid_lines[1].endswith("\n") else ""))
        
        scom_tokens = valid_lines[2].strip().split()
        scom_dict = {par: (scom_tokens[i] if i < len(scom_tokens) else "-99") for i, par in enumerate(SURF_PARS_3)}
        
        formatted_lines.append("@ SCOM  SALB  SLU1  SLDR  SLRO  SLNF  SLPF  SMHB  SMPX  SMKE\n")
        scom_str = " " + " ".join([format_val(scom_dict[par], pars_fmt[par]) for par in SURF_PARS_3]) + "\n"
        formatted_lines.append(scom_str)
        
        formatted_lines.append("@  SLB  SLMH  SLLL  SDUL  SSAT  SRGF  SSKS  SBDM  SLOC  SLCL  SLSI  SLCF  SLNI  SLHW  SLHB  SCEC  SADC\n")
        
        tier1_lines = []
        tier2_lines = []
        parsing_tier1 = False
        parsing_tier2 = False
        
        for line in block_lines:
            if '@  SLB  SLMH' in line:
                parsing_tier1 = True
                parsing_tier2 = False
                continue
            if '@  SLB  SLPX' in line:
                parsing_tier1 = False
                parsing_tier2 = True
                continue
            if line.startswith('@'):
                parsing_tier1 = False
                parsing_tier2 = False
                continue
                
            if line.strip() and not line.startswith('!'):
                if parsing_tier1:
                    tier1_lines.append(line)
                elif parsing_tier2:
                    tier2_lines.append(line)
        
        max_depth = 0.0
        
        for layer in tier1_lines:
            tokens = layer.strip().split()
            layer_dict = {par: (tokens[i] if i < len(tokens) else "-99") for i, par in enumerate(PROF_PARS_1)}
            
            try:
                max_depth = max(max_depth, float(layer_dict['slb']))
            except ValueError:
                pass
            
            missing_hydro = layer_dict['slll'] == "-99" or layer_dict['sdul'] == "-99" or layer_dict['ssat'] == "-99"
            valid_texture = layer_dict['slcl'] != "-99" and layer_dict['slsi'] != "-99"
            
            if missing_hydro and valid_texture:
                estimates = estimate_from_texture(
                    slcl=layer_dict['slcl'], 
                    slsi=layer_dict['slsi'], 
                    sbdm=layer_dict['sbdm'], 
                    sloc=layer_dict['sloc']
                )
                for key, val in estimates.items():
                    if val is not None:
                        layer_dict[key] = val

            layer_str = " " + " ".join([format_val(layer_dict[par], pars_fmt[par]) for par in PROF_PARS_1]) + "\n"
            formatted_lines.append(layer_str)
            
        if tier2_lines:
            formatted_lines.append("@  SLB  SLPX  SLPT  SLPO CACO3  SLAL  SLFE  SLMN  SLBS  SLPA  SLPB  SLKE  SLMG  SLNA  SLSU  SLEC  SLCA\n")
            for layer in tier2_lines:
                tokens = layer.strip().split()
                layer_dict = {par: (tokens[i] if i < len(tokens) else "-99") for i, par in enumerate(PROF_PARS_2)}
                layer_str = " " + " ".join([format_val(layer_dict[par], pars_fmt[par]) for par in PROF_PARS_2]) + "\n"
                formatted_lines.append(layer_str)
        
        raw_string = "".join(formatted_lines)
        return cls(raw_string, max_depth, **kwargs)

    @classmethod
    def from_file(cls, profile: str, file: str):
        if not os.path.exists(file):
            print(f"Error: The original primary source data file '{file}' cannot be accessed.")
            sys.exit(1)
            
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
            print(f"Error: {profile} profile not in {file} file")
            sys.exit(1)
            
        return cls.from_block(profile, [], block_lines)