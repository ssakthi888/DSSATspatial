
import os
from rosetta import rosetta, SoilData
from .partypes import (
    NumberType, DescriptionType, Record, TabularRecord,
    CodeType, parse_pars_line, clean_comments
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

SOIL_LAB = {
    'BLK': (20, 2, 6), 
    'YBR': (51, 17, 35),
    'RBR': (41, 34, 30),
    'DBR': (31, 17, 17),
    'GRE': (61, 2, 6),
    'YLW': (71, 14, 50)
}

def van_genuchten(theta_r, theta_s, alpha, n, h):
    alpha = 10**alpha 
    n = 10**n
    m = 1 - 1/n 
    theta = theta_r + (theta_s - theta_r)/(1 + abs(alpha * h)**n)**m
    return theta

def sloc_from_color(L:float, a:float, b:float):
    return max(7.18 - 0.095*L - 0.164*a - 0.038*b, 0)

def estimate_from_texture(slcl, slsi, sbdm=None, sloc=None):
    if sbdm:
        soil_data = SoilData.from_array(
            [[100 - slcl - slsi, slsi, slcl, sbdm]]
        )
        vangenuchten_pars, _, _ = rosetta(3, soil_data)
    else:
        soil_data = SoilData.from_array(
            [[100 - slcl - slsi, slsi, slcl]]
        )
        vangenuchten_pars, _, _ = rosetta(2, soil_data)
        
    vangenuchten_pars = vangenuchten_pars[0]
    ssat = vangenuchten_pars[1]
    ssks = (10**vangenuchten_pars[-1]) / 24
    slll = van_genuchten(*vangenuchten_pars[:-1], h=1500)
    sdul = van_genuchten(*vangenuchten_pars[:-1], h=33)
    if (not sbdm) and sloc:
        sbdm = 1.386 - 0.078*sloc + 0.001*slsi + 0.001*slcl
    return {"ssat": ssat, "ssks": ssks, "slll": slll, "sdul": sdul, "sbdm": sbdm}

class SoilLayer(Record):
    prefix = None
    dtypes = {
        'slb': NumberType, 'slmh': DescriptionType, 'slll': NumberType,
        'sdul': NumberType, 'ssat': NumberType, 'srgf': NumberType, 
        'ssks': NumberType, 'sbdm': NumberType, 'sloc': NumberType, 
        'slcl': NumberType, 'slsi': NumberType, 'slcf': NumberType, 
        'slni': NumberType, 'slhw': NumberType, 'slhb': NumberType, 
        'scec': NumberType, 'sadc': NumberType,

        'slpx': NumberType, 'slpt': NumberType, 'slpo': NumberType, 
        'caco3': NumberType, 'slal': NumberType, 'slfe': NumberType, 
        'slmn': NumberType, 'slbs': NumberType, 'slpa': NumberType, 
        'slpb': NumberType, 'slke': NumberType, 'slmg': NumberType, 
        'slna': NumberType, 'slsu': NumberType, 'slec': NumberType, 
        'slca': NumberType
    }
    pars_fmt = {
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
    n_tiers = 2
    table_index = "slb"
    def __init__(self, slb:float, slll:float, sdul:float, ssat:float, srgf:float, 
                 sbdm:float, sloc:float, ssks:float=None, slmh:str=None, 
                 slcl:float=None, slsi:float=None, slcf:float=None,
                 slni:float=None, slhw:float=None, slhb:float=None, 
                 scec:float=None, sadc:float=None, slpx:float=None, 
                 slpt:float=None, slpo:float=None, caco3:float=None,
                 slal:float=None, slfe:float=None, slmn:float=None,
                 slbs:float=None, slpa:float=None, slpb:float=None, 
                 slke:float=None, slmg:float=None, slna:float=None, 
                 slsu:float=None, slec:float=None, slca:float=None):
        super().__init__()
        kwargs = {
            'slb': slb, 'slmh': slmh, 'slll': slll, 'sdul': sdul, 
            'ssat': ssat, 'srgf': srgf, 'ssks': ssks, 'sbdm': sbdm, 
            'sloc': sloc, 'slcl': slcl, 'slsi': slsi, 'slcf': slcf, 
            'slni': slni, 'slhw': slhw, 'slhb': slhb, 'scec': scec, 
            'sadc': sadc, 
            
            'slpx': slpx, 'slpt': slpt, 'slpo': slpo, 'caco3': caco3, 
            'slal': slal, 'slfe': slfe, 'slmn': slmn, 'slbs': slbs, 
            'slpa': slpa, 'slpb': slpb, 'slke': slke, 'slmg': slmg, 
            'slna': slna, 'slsu': slsu, 'slec': slec, 'slca': slca
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)


class SoilProfile(TabularRecord):
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
    table_dtype = SoilLayer
    code:str
    def __init__(self, table:list[SoilLayer], name:str, salb:float,slu1:float,
                 sldr:float, slro:float, slnf:float, slpf:float, 
                 soil_data_source:str=None, soil_clasification:str=None, 
                 soil_series_name:str=None, site:str=None, country:str=None, 
                 lat:float=None, long:float=None, scs_family:str=None, 
                 scom:float=None, smhb:str=None, smpx:str=None,smke:str=None):
        super().__init__()
        kwargs = {
            'name': name, 'soil_data_source': soil_data_source, 
            'soil_clasification': soil_clasification, 'soil_depth': 0,
            'soil_series_name': soil_series_name, 'site': site, 
            'country': country, 'lat': lat, 'long': long, 'scs_family': scs_family, 
            'scom': scom, 'salb': salb, 'slu1': slu1, 'sldr': sldr, 'slro': slro, 
            'slnf': slnf, 'slpf': slpf, 'smhb': smhb, 'smpx': smpx, 'smke': smke
        }
        for name, value in kwargs.items():
            self.__setitem__(name, value)
        self.table = table
        self["soil_depth"] = self.table[-1]["slb"]

    def _write_section(self):
        raise NotImplementedError
    
    def _write_row(self):
        raise NotImplementedError

    def __setitem__(self, key, value):
        if key == "name":
            assert len(value) == 10, \
                "Soil profile Name must be 10 characters long"
        super().__setitem__(key, value)
    
    def _write_table(self):
        return
    
    def _write_sol(self):
        out_str = "*SOILS: General DSSAT Soil Input File\n\n"
        out_str += "*"+" ".join([
            self[name].str for name in SURF_PARS_1
            if name != "table"
        ])
        out_str += "\n@SITE        COUNTRY          LAT     LONG SCS FAMILY\n"
        out_str += " "+" ".join([
            self[name].str for name in SURF_PARS_2
            if name != "table"
        ])
        out_str += "\n@ SCOM  SALB  SLU1  SLDR  SLRO  SLNF  SLPF  SMHB  SMPX  SMKE\n"
        out_str += " "+" ".join([
            self[name].str for name in SURF_PARS_3
            if name != "table"
        ])
        out_str += "\n@  SLB  SLMH  SLLL  SDUL  SSAT  SRGF  SSKS  SBDM  SLOC  SLCL  SLSI  SLCF  SLNI  SLHW  SLHB  SCEC  SADC\n"
        for layer in self.table:
            out_str += " "+" ".join([
                layer[name].str for name in PROF_PARS_1
                if name != "table"
            ])
            out_str += "\n"
        out_str += "@  SLB  SLPX  SLPT  SLPO CACO3  SLAL  SLFE  SLMN  SLBS  SLPA  SLPB  SLKE  SLMG  SLNA  SLSU  SLEC  SLCA\n"
        for layer in self.table:
            out_str += " "+" ".join([
                layer[name].str for name in PROF_PARS_2
                if name != "table"
            ])
            out_str += "\n"
        return out_str
    
    @property
    def str(self):
        return self['name']

    @classmethod
    def from_file(cls, profile:str, file:str):
        profile_lines = []
        with open(file, "r") as f:
            for line in f:
                if profile in line[:12]:
                    profile_lines.append(line)
                    continue
                if profile_lines and (not line.strip()):
                    break
                if line[0] == "!":
                    continue
                if profile_lines:
                    profile_lines.append(line)
            assert profile_lines, f"{profile} profile not in {file} file"

        # First row of parameters
        kwargs = parse_pars_line(
            profile_lines[0][1:], 
            {par: cls.pars_fmt[par] for par in SURF_PARS_1}
        )
        del kwargs["soil_depth"]
        # Second row of parameters
        kwargs = {**kwargs, **parse_pars_line(
            profile_lines[2][1:], 
            {par: cls.pars_fmt[par] for par in SURF_PARS_2}
        )}
        # Third row of parameters
        kwargs = {**kwargs, **parse_pars_line(
            profile_lines[4][1:], 
            {par: cls.pars_fmt[par] for par in SURF_PARS_3}
        )}
        # Soil profile values
        level_1_index = profile_lines.index(
            filter(lambda x: 'SLLL  SDUL  SSAT' in x, profile_lines).__next__()
        )
        try:
           level_2_index = profile_lines.index(
                filter(lambda x: '@  SLB  SLPX ' in x, profile_lines).__next__()
            )
        except StopIteration:
            level_2_index = len(profile_lines)
        level_1_pars = profile_lines[level_1_index:level_2_index]
        level_2_pars = profile_lines[level_2_index:]
        if not level_2_pars:
            level_2_pars = ["\n"] * len(level_1_pars)
        pars = [
            f"{l1.rstrip()}{l2[6:]}" 
            for l1, l2 in zip(level_1_pars, level_2_pars)
        ]
        table = []
        for line in pars[1:]:
            table.append(cls.table_dtype(
                **parse_pars_line(line[1:], cls.table_dtype.pars_fmt)
            ))
        
        kwargs['table'] = table
        return cls(**kwargs)