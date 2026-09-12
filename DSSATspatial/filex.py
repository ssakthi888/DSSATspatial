from datetime import date
from .partypes import (
    DateType, CodeType, NumberType, Record, TabularRecord, DescriptionType,
    FACTOR_LEVELS, clean_comments, parse_pars_line
)
from .crop import (
    Maize, Wheat, Sorghum, PearlMillet, Sugarbeet, Rice, Alfalfa, Bermudagrass,
    Soybean, Canola, Sunflower, Potato, Tomato, Cabbage, Sugarcane, DryBean,
    Cassava, SweetCorn, Cotton, Peanut
)
from .weather import ProcessWTH
from .soil import SoilProfile
from .utils import detect_encoding

CROP_OBJECTS = {
    "MZ": Maize, 'WH': Wheat, 'SG': Sorghum, 'ML': PearlMillet, 'BS': Sugarbeet,
    'RI': Rice, 'SW': SweetCorn, 'AL': Alfalfa, 'BM': Bermudagrass, 
    'SB': Soybean, 'CN': Canola, 'SU': Sunflower, 'PT': Potato, 'TM': Tomato,
    'CB': Cabbage, 'SC': Sugarcane, 'BN': DryBean, 'CS': Cassava, 'CO': Cotton,
    "PN": Peanut  # <-- ADD THIS LINE
}

class Planting(Record):
    prefix = "p"
    dtypes = {
        "pdate": DateType, "edate": DateType, "ppop": NumberType, 
        "ppoe": NumberType, "plme": CodeType, "plds": CodeType, 
        "plrs": NumberType, "plrd": NumberType, "pldp": NumberType, 
        "plwt": NumberType, "page": NumberType, "penv": NumberType, 
        "plph": NumberType, "sprl": NumberType, "plname": DescriptionType
    }
    pars_fmt = {
        "pdate": "%y%j", "edate": "%y%j", "ppop": ">5.1f", "ppoe": ">5.1f", 
        "plme": ">5", "plds": ">5", "plrs": ">5.0f", "plrd": ">5.0f", 
        "pldp": ">5.1f", "plwt": ">5.1f", "page": ">5.0f", "penv": ">5.1f", 
        "plph": ">5.0f", "sprl": ">5.0f", "plname": ">29"
    }
    # Typehints must be in order following DSSAT column order
    def __init__(self, pdate:date, ppop:float, plrs:float, 
                ppoe:float=None, plds:str="R", plrd:float=0, plme:str="S", 
                pldp:float=5, plwt:float=None, page:float=None, penv:float=None, 
                plph:float=None, sprl:float=0, edate:date=None, plname:str=None):
        super().__init__()
        kwargs = {
            "pdate": pdate, "edate": edate, "ppop": ppop, "ppoe": ppoe, 
            "plme": plme, "plds": plds, "plrs": plrs, "plrd": plrd, "pldp": pldp,
            "plwt": plwt, "page": page, "penv": penv, "plph": plph, "sprl": sprl, 
            "plname": plname
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)


class Cultivar(Record):
    prefix = "c"
    dtypes = {
        "cr": CodeType, "ingeno": DescriptionType, "cname": DescriptionType
    }
    pars_fmt = {
        "cr": ">2", "ingeno": ">6", "cname": "<16"
    }
    def __init__(self, cr:str, ingeno:str, cname:str=None):
        super().__init__()
        kwargs = {
            'cr': cr, 'ingeno': ingeno, 'cname': cname, 
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)
        # The crop attribute stores the Crop object
        self.__crop = CROP_OBJECTS[cr.upper()](ingeno)
    
    @property
    def crop(self):
        return self.__crop


class Harvest(Record):
    prefix = "h"
    dtypes = {
        "hdate": DateType, "hstg": CodeType, "hcom": CodeType,
        "hsize": CodeType, "hpc": NumberType, "hbpc": NumberType, 
        "hname": DescriptionType
    }
    pars_fmt = {
        "hdate": "%y%j", "hstg": ">5", "hcom": ">5", "hsize": ">5", 
        "hpc": ">5.1f", "hbpc": ">5.1f", "hname": "<25"
    }
    def __init__(self, hdate:date, hstg:str=None, hcom:str=None, hsize:str=None,
                hpc:float=None, hbpc:float=None, hname:str=None):
        super().__init__()
        kwargs = {
            "hdate": hdate, "hstg": hstg, "hcom": hcom, "hsize": hsize, 
            "hpc": hpc, "hbpc": hbpc, "hname": hname
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)


class InitialConditionsLayer(Record):
    prefix = "c"
    dtypes = {
        "icbl": NumberType, "sh2o": NumberType, "snh4": NumberType, 
        "sno3": NumberType
    }
    pars_fmt = {
        "icbl": ">5.0f", "sh2o": ">5.3f", "snh4": ">5.1f", "sno3": ">5.1f"
    }
    table_index = "icbl" # Index when buliding table
    def __init__(self, icbl:float, sh2o:float, snh4:float=None, 
                sno3:float=None):
        super().__init__()
        kwargs = {"icbl": icbl, "sh2o": sh2o, "snh4": snh4, "sno3": sno3}
        for name, value in kwargs.items():
            super().__setitem__(name, value)
        return

class InitialConditions(TabularRecord):
    prefix = "c"
    dtypes = {
        "pcr": CodeType, "icdat": DateType, "icrt": NumberType, 
        "icnd": NumberType, "icrn": NumberType, "icre": NumberType,
        "icwd": NumberType, "icres": NumberType, "icren": NumberType,
        "icrep": NumberType, "icrip": NumberType, "icrid": NumberType,
        "icname": DescriptionType
    }
    pars_fmt = {
        "pcr": ">5", "icdat": "%y%j", "icrt": ">5.0f", "icnd": ">5.0f", 
        "icrn": ">5.0f", "icre": ">5.0f", "icwd": ">5.0f", "icres": ">5.0f", 
        "icren": ">5.2f", "icrep": ">5.0f", "icrip": ">5.0f", "icrid": ">5.0f",
        "icname": "<25"
    }
    table_dtype = InitialConditionsLayer
    def __init__(self, pcr:str, icdat:date=None, icrt:float=None, 
                icnd:float=None, icrn:float=None, icre:float=None, 
                icwd:float=None, icres:float=None, icren:float=None,
                icrep:float=None, icrip:float=None, icrid:float=None,
                icname:str=None, table:list[InitialConditionsLayer]=None):
        super().__init__()
        kwargs = {
            "pcr": pcr, "icdat": icdat, "icrt": icrt, "icnd": icnd, 
            "icrn": icrn, "icre": icre, "icwd": icwd, "icres": icres, 
            "icren": icren, "icrep": icrep, "icrip": icrip, "icrid": icrid,
            "icname": icname
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)
        self.table = table
        return


class FertilizerEvent(Record):
    prefix = "f"
    dtypes = {
        "fdate": DateType, "fmcd": CodeType, "facd": CodeType, 
        "fdep": NumberType, "famn": NumberType, "famp": NumberType,
        "famk": NumberType, "famc": NumberType, "famo": NumberType,
        "focd": CodeType, "fername": DescriptionType
    }
    pars_fmt = {
        "fdate": "%y%j", "fmcd": ">5", "facd": ">5", "fdep": ">5.0f", 
        "famn": ">5.1f", "famp": ">5.1f", "famk": ">5.1f", "famc": ">5.1f",
        "famo": ">5.1f", "focd": ">5", "fername": "<16"
    }
    table_index = None
    def __init__(self, fdate:date, fmcd:str, facd:str, fdep:float, famn:float, 
                famp:float=None, famk:float=None, famc:float=None, famo:float=None,
                focd:str=None, fername:str=None):
        super().__init__()
        kwargs = {
            "fdate": fdate, "fmcd": fmcd, "facd": facd, "fdep": fdep, 
            "famn": famn, "famp": famp, "famk": famk, "famc": famc, 
            "famo": famo, "focd": focd, "fername": fername
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)
        return

class Fertilizer(TabularRecord):
    prefix = "f"
    dtypes = {}
    pars_fmt = {}
    table_dtype = FertilizerEvent
    def __init__(self, table=list[FertilizerEvent]):
        super().__init__()
        self.table = table


class SoilAnalysisLayer(Record):
    prefix = "a"
    dtypes = {
        "sabl": NumberType, "sadm": NumberType, "saoc": NumberType, 
        "sani": NumberType, "saphw": NumberType, "saphb": NumberType,
        "sapx": NumberType, "sake": NumberType, "sasc": NumberType
    }
    pars_fmt = {
        "sabl": ">5.0f", "sadm": ">5.1f", "saoc": ">5.2f", "sani": ">5.2f",
        "saphw": ">5.1f", "saphb": ">5.1f", "sapx": ">5.1f", "sake": ">5.1f",
        "sasc": ">5.2f"
    }
    table_index = "sabl" # Index when buliding table
    def __init__(self, sabl:float, sadm:float=None, saoc:float=None, 
                sani:float=None, saphw:float=None, saphb:float=None,
                sapx:float=None, sake:float=None, sasc:float=None):
        super().__init__()
        kwargs = {"sabl": sabl, "sadm": sadm, "saoc": saoc, "sani": sani,
                "saphw": saphw, "saphb": saphb, "sapx": sapx, "sake": sake,
                "sasc": sasc}
        for name, value in kwargs.items():
            super().__setitem__(name, value)
        return

class SoilAnalysis(TabularRecord):
    prefix = "a"
    dtypes = {
        "sadat": DateType, "smhb": CodeType, "smpx": CodeType, 
        "smke": CodeType, "saname": DescriptionType
    }
    pars_fmt = {
        "sadat": "%y%j", "smhb": ">5", "smpx": ">5", "smke": ">5", 
        "saname": "<16"
    }
    table_dtype = SoilAnalysisLayer
    def __init__(self, sadat:date, table:list[SoilAnalysisLayer],
                smhb:str=None, smpx:str=None, smke:str=None, saname:str=None):
        super().__init__()
        kwargs = {
            "sadat": sadat, "smhb": smhb, "smpx": smpx, "smke": smke, 
            "saname": saname
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)
        self.table = table


class IrrigationEvent(Record):
    prefix = "i"
    dtypes = {
        "idate": DateType, "irop": CodeType, "irval": NumberType, 
    }
    pars_fmt = {
        "idate": "%y%j", "irop": ">5", "irval": ">5.1f"
    }
    table_index = None
    def __init__(self, idate:date, irval:float, irop:str=None):
        super().__init__()
        kwargs = {"idate": idate, "irop": irop, "irval": irval}
        for name, value in kwargs.items():
            super().__setitem__(name, value)
        return

class Irrigation(TabularRecord):
    prefix = "i"
    dtypes = {
        "efir": NumberType, "idep": NumberType, "ithr": NumberType,
        "iept": NumberType, "ioff": CodeType, "iame": CodeType,
        "iamt": NumberType, "irname": DescriptionType
    }
    pars_fmt = {
        "efir": ">5.2f", "idep": ">5.0f", "ithr": ">5.0f", "iept": ">5.0f",
        "ioff": ">5", "iame": ">5", "iamt": ">5.0f", "irname": "<16"
    }
    table_dtype = IrrigationEvent
    def __init__(self, table=list[IrrigationEvent], efir:float=1,
                    idep:float=None, ithr:float=None, iept:float=None,
                    ioff:str=None, iame:str=None, iamt:float=None, 
                    irname:str=None):
        super().__init__()
        kwargs = {
            "efir": efir, "idep": idep, "ithr": ithr, "iept": iept,
            "ioff": ioff, "iame": iame, "iamt": iamt, "irname": irname
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)
        self.table = table


class ResidueEvent(Record):
    prefix = "r"
    dtypes = {
        "rdate": DateType, "rcod": CodeType, "ramt": NumberType,
        "resn": NumberType, "resp": NumberType, "resk": NumberType,
        "rinp": NumberType, "rdep": NumberType, "rmet": CodeType,
        "rename": DescriptionType
    }
    pars_fmt = {
        "rdate": "%y%j", "rcod": ">5", "ramt": ">5.0f", "resn": ">5.2f",
        "resp": ">5.2f", "resk": ">5.2f", "rinp": ">5.0f", "rdep": ">5.0f",
        "rmet": ">5", "rename": "<16"
    }
    table_index = None
    def __init__(self, rdate:date, rcod:str, ramt:float, resn:float,
                resp:float, resk:float, rinp:float, rdep:float, rmet:str,
                rename:str=None):
        super().__init__()
        kwargs = {
            "rdate": rdate, "rcod": rcod, "ramt": ramt, "resn": resn,
            "resp": resp, "resk": resk, "rinp": rinp, "rdep": rdep,
            "rmet": rmet, "rename": rename
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)

class Residue(TabularRecord):
    prefix = "r"
    dtypes = {}
    pars_fmt = {}
    table_dtype = ResidueEvent
    def __init__(self, table=list[ResidueEvent]):
        super().__init__()
        self.table = table
    

class ChemicalEvent(Record):
    prefix = "c"
    dtypes = {
        "cdate": DateType, "chcod": CodeType, "chamt": NumberType,
        "chme": CodeType, "chdep": NumberType, "cht": CodeType,
        "chname": DescriptionType
    }
    pars_fmt = {
        "cdate": "%y%j", "chcod": ">5", "chamt": ">5.2f", "chme": ">5",
        "chdep": ">5.0f", "cht": ">5", "chname": "<16"
    }
    table_index = None
    def __init__(self, cdate:date, chcod:str, chamt:float, chme:str,
                chdep:float=None, cht:str=None, chname:str=None):
        super().__init__()
        kwargs = {
            "cdate": cdate, "chcod": chcod, "chamt": chamt, "chdep": chdep,
            "chme": chme, "cht": cht, "chname": chname
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)
    
class Chemical(TabularRecord):
    prefix = "c"
    dtypes = {}
    pars_fmt = {}
    table_dtype = ChemicalEvent
    def __init__(self, table=list[ChemicalEvent]):
        super().__init__()
        self.table = table


class TillageEvent(Record):
    prefix = "t"
    dtypes = {
        "tdate": DateType, "timpl": CodeType, "tdep": NumberType,
        "tname": DescriptionType
    }
    pars_fmt = {
        "tdate": "%y%j", "timpl": ">5", "tdep": ">5.0f", "tname": "<16"
    }
    table_index = None
    def __init__(self, tdate:date, timpl:str=None, tdep:float=None, 
                tname:str=None):
        super().__init__()
        kwargs = {
            "tdate": tdate, "timpl": timpl, "tdep": tdep, "tname": tname
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value) 


class Tillage(TabularRecord):
    prefix = "t"
    dtypes = {}
    pars_fmt = {}
    table_dtype = TillageEvent
    def __init__(self, table=list[TillageEvent]):
        super().__init__()
        self.table = table
    

class Field(Record):
    prefix = "l"
    dtypes = {
        "id_field": DescriptionType, "wsta": (DescriptionType, ProcessWTH), 
        "flsa": NumberType, "flob": NumberType, "fldt": CodeType, 
        "fldd": NumberType, "flds": NumberType, "flst": CodeType, 
        "sltx": CodeType, "sldp": NumberType, "id_soil": (DescriptionType, SoilProfile), 
        "flname": DescriptionType, "xcrd": NumberType, "ycrd": NumberType, 
        "elev": NumberType, "area": NumberType, "slen": NumberType, 
        "flwr": NumberType, "slas": NumberType, "flhst": CodeType, 
        "fhdur": NumberType
    }
    pars_fmt = {
        "id_field": ">8", "wsta": ".<8", "flsa": ">5.0f", "flob": ">5.0f", 
        "fldt": ">5", "fldd": ">5.0f", "flds": ">5.0f", "flst": ">5", 
        "sltx": "<5", "sldp": ">5.0f", "id_soil": "<10", "flname": "<32", 
        "xcrd": ".>15.2f", "ycrd": ".>15.2f", "elev": ".>9.0f", 
        "area": ".>17.0f", "slen": ".>5.0f", "flwr": ".>5.1f", 
        "slas": ".>5.0f", "flhst": ">5", "fhdur": ">5.0f"
    }
    n_tiers = 2
    def __init__(self, id_field:str, wsta:str, id_soil:str, flsa:float=None,
                flob:float=None, fldt:str=None, fldd:float=None, 
                flds:float=None, flst:str=None, sltx:str=None, 
                sldp:float=None, flname:str=None, xcrd:float=None, 
                ycrd:float=None, elev:float=None, area:float=None, 
                slen:float=None, flwr:float=None, slas:float=None, 
                flhst:str=None, fhdur:float=None):
        super().__init__()
        if fldt is None:
            fldt = "DR000"
        kwargs = {
            "id_field": id_field, "wsta": wsta, "flsa": flsa, "flob": flob, 
            "fldt": fldt, "fldd": fldd, "flds": flds, "flst": flst, 
            "sltx": sltx, "sldp": sldp, "id_soil": id_soil, "flname": flname, 
            "xcrd": xcrd, "ycrd": ycrd, "elev": elev, "area": area, 
            "slen": slen, "flwr": flwr, "slas": slas, "flhst": flhst, 
            "fhdur": fhdur
        }
        for name, value in kwargs.items():
            self.__setitem__(name, value)
        self.__tier1 = [
            "id_field", "wsta", "flsa", "flob", "fldt", "fldd", "flds", 
            "flst", "sltx", "sldp", "id_soil", "flname"
        ]
        self.__tier2 = [
            "xcrd", "ycrd", "elev", "area", "slen", "flwr", "slas", "flhst",
            "fhdur"
        ]
    
    def _write_section(self):
        out_str = "*FIELDS\n"
        for tiers in (self.__tier1, self.__tier2):
            header = ["@"+self.prefix.upper()]
            values = []
            for key in tiers:
                fmt = self.pars_fmt[key]
                if fmt == "%y%j":
                    fmt = ">5"
                if fmt[0] == ".":
                    leading = "."
                    fmt = fmt[1:]
                else:
                    leading = ""
                fmt = leading + fmt.split(".")[0]
                header.append(format(key.upper(), fmt))
                values.append(self[key].str)
            out_str += " ".join(header) + "\n" + " 1 " + " ".join(values) + "\n"
        return out_str
    
    def __setitem__(self, key, value):
        if key == "id_field":
            assert len(value) == 8, "id_field must be a 8 character string"
        # if (key == "wsta") and isinstance(value, ProcessWTH):
        #     self.dtypes["wsta"] = ProcessWTH
        if (key == "id_soil") and isinstance(value, SoilProfile):
            # self.dtypes["id_soil"] = SoilProfile
            self["sldp"] = value.table[-1]["slb"]
        super().__setitem__(key, value)


class SCGeneral(Record):
    prefix = "n"
    dtypes = {
        "nyers": NumberType, "nreps": NumberType, "start": CodeType,
        "sdate": DateType, "rseed": NumberType, "sname": DescriptionType,
        "smodel": CodeType
    }
    pars_fmt = {
        "nyers": ">5.0f", "nreps": ">5.0f", "start": ">5",
        "sdate": "%y%j", "rseed": ">5.0f", "sname": "<25",
        "smodel": ">8"
    }
    def __init__(self, sdate:date, nyers:int=1, nreps:int=1, start:str="S", 
                rseed:int=2150, sname:str=None, smodel:str=None):
        super().__init__()
        kwargs = {
            "nyers": nyers, "nreps": nreps, "start": start, "sdate": sdate,
            "rseed": rseed, "sname": sname, "smodel": smodel
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)
        return
    

class SCOptions(Record):
    prefix = "n"
    dtypes = {
        "water": CodeType, "nitro": CodeType, "symbi": CodeType,
        "phosp": CodeType, "potas": CodeType, "dises": CodeType,
        "chem": CodeType, "till": CodeType, "co2": CodeType
    }
    pars_fmt = {
        "water": ">5", "nitro": ">5", "symbi": ">5",
        "phosp": ">5", "potas": ">5", "dises": ">5",
        "chem": ">5", "till": ">5", "co2": ">5"
    }
    def __init__(self, water:str="Y", nitro:str="Y", symbi:str="N",
                phosp:str="N", potas:str="N", dises:str="N", 
                chem:str="N", till:str="N", co2:str="M"):
        super().__init__()
        kwargs = {
            "water": water, "nitro": nitro, "symbi": symbi,
            "phosp": phosp, "potas": potas, "dises": dises,
            "chem": chem, "till": till, "co2": co2
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)
    

class SCMethods(Record):
    prefix = "n"
    dtypes = {
        "wther": CodeType, "incon": CodeType, "light": CodeType,
        "evapo": CodeType, "infil": CodeType, "photo": CodeType,
        "hydro": CodeType, "nswit": CodeType, "mesom": CodeType,
        "mesev": CodeType, "mesol": CodeType
    }
    pars_fmt = {
        "wther": ">5", "incon": ">5", "light": ">5",
        "evapo": ">5", "infil": ">5", "photo": ">5",
        "hydro": ">5", "nswit": ">5", "mesom": ">5",
        "mesev": ">5", "mesol": ">5"
    }
    def __init__(self, wther:str="M", incon:str="M", light:str="E",
                evapo:str="R", infil:str="R", photo:str="C", hydro:str="R",
                nswit:str="1", mesom:str="P", mesev:str="R", mesol:str="1"):
        super().__init__()
        kwargs = {
            "wther": wther, "incon": incon, "light": light, "evapo": evapo,
            "infil": infil, "photo": photo, "hydro": hydro, "nswit": nswit,
            "mesom": mesom, "mesev": mesev, "mesol": mesol
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)
    

class SCManagement(Record):
    prefix = "n"
    dtypes = {
        "plant": CodeType, "irrig": CodeType, "ferti": CodeType,
        "resid": CodeType, "harvs": CodeType, 
    }
    pars_fmt = {
        "plant": ">5", "irrig": ">5", "ferti": ">5",
        "resid": ">5", "harvs": ">5", 
    }
    def __init__(self, plant:str="R", irrig:str="D", ferti:str="D",
                resid:str="D", harvs:str="A"):
        super().__init__()
        kwargs = {
            "plant": plant, "irrig": irrig, "ferti": ferti, "resid": resid,
            "harvs": harvs, 
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)
    

class SCOutputs(Record):
    prefix = "n"
    dtypes = {
        'fname': CodeType, 'ovvew': CodeType, 'sumry': CodeType, 
        'fropt': NumberType, 'grout': CodeType, 'caout': CodeType, 
        'waout': CodeType, 'niout': CodeType, 'miout': CodeType,
        'diout': CodeType, 'vbose': CodeType, 'chout': CodeType, 
        'opout': CodeType, 'fmopt': CodeType
    }
    pars_fmt = {
        'fname': ">5", 'ovvew': ">5", 'sumry': ">5", 'fropt': ">5.0f", 
        'grout': ">5", 'caout': ">5", 'waout': ">5", 'niout': ">5", 
        'miout': ">5", 'diout': ">5", 'vbose': ">5", 'chout': ">5", 
        'opout': ">5", 'fmopt': ">5"
    }
    def __init__(self, fname:str="N", ovvew:str="Y", sumry:str="Y", 
                fropt:int=1, grout:str="Y", caout:str="Y", waout:str="N",
                niout:str="N", miout:str="N", diout:str="N", vbose:str="Y",
                chout:str="N", opout:str="N", fmopt:str="A"):
        super().__init__()
        kwargs = {
            'fname': fname, 'ovvew': ovvew, 'sumry': sumry, 'fropt': fropt, 
            'grout': grout, 'caout': caout, 'waout': waout, 'niout': niout, 
            'miout': miout, 'diout': diout, 'vbose': vbose, 'chout': chout, 
            'opout': opout, 'fmopt': fmopt
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)
    

class AMPlanting(Record):
    prefix = "n"
    dtypes = {
        'pfrst': DateType, 'plast': DateType, 'ph2ol': NumberType, 
        'ph2ou': NumberType, 'ph2od': NumberType, 'pstmx': NumberType, 
        'pstmn': NumberType,
    }
    pars_fmt = {
        'pfrst': "%y%j", 'plast': "%y%j", 'ph2ol': ">5.0f", 
        'ph2ou': ">5.0f", 'ph2od': ">5.0f", 'pstmx': ">5.0f", 
        'pstmn': ">5.0f",
    }
    def __init__(self, pfrst:date, plast:date, ph2ol:float=40, 
                ph2ou:float=100, ph2od:float=30, pstmx:float=30,
                pstmn:float=10):
        super().__init__()
        kwargs = {
            'pfrst': pfrst, 'plast': plast, 'ph2ol': ph2ol, 
            'ph2ou': ph2ou, 'ph2od': ph2od, 'pstmx': pstmx, 
            'pstmn': pstmn
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)
    

class AMIrrigation(Record):
    prefix = "n"
    dtypes = {
        'imdep': NumberType, 'ithrl': NumberType, 'ithru': NumberType, 
        'iroff': CodeType, 'imeth': CodeType, 'iramt': NumberType, 
        'ireff': NumberType,
    }
    pars_fmt = {
        'imdep': ">5.0f", 'ithrl': ">5.0f", 'ithru': ">5.0f", 
        'iroff': ">5", 'imeth': ">5", 'iramt': ">5.0f", 
        'ireff': ">5.2f",
    }
    def __init__(self, imdep:float=30, ithrl:float=50, ithru:float=100, 
                iroff:str="IB001", imeth:str="IB001", iramt:float=10,
                ireff:float=1.):
        super().__init__()
        kwargs = {
            'imdep': imdep, 'ithrl': ithrl, 'ithru': ithru, 
            'iroff': iroff, 'imeth': imeth, 'iramt': iramt, 
            'ireff': ireff,
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)
    

class AMNitrogen(Record):
    prefix = "n"
    dtypes = {
        'nmdep': NumberType, 'nmthr': NumberType, 'namnt': NumberType, 
        'ncode': CodeType, 'naoff': CodeType, 
    }
    pars_fmt = {
        'nmdep': ">5.0f", 'nmthr': ">5.0f", 'namnt': ">5.0f", 
        'ncode': ">5", 'naoff': ">5", 
    }
    def __init__(self, nmdep:float=30, nmthr:float=50, namnt:float=25, 
                ncode:str="IB001", naoff:str="IB001"):
        super().__init__()
        kwargs = {
            'nmdep': nmdep, 'nmthr': nmthr, 'namnt': namnt, 
            'ncode': ncode, 'naoff': naoff
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)
    

class AMResidues(Record):
    prefix = "n"
    dtypes = {
        'ripcn': NumberType, 'rtime': NumberType, 'ridep': NumberType, 
    }
    pars_fmt = {
        'ripcn': ">5.0f", 'rtime': ">5.0f", 'ridep': ">5.0f", 
    }
    def __init__(self, ripcn:float=100, rtime:float=1, ridep:float=20):
        super().__init__()
        kwargs = {
            'ripcn': ripcn, 'rtime': rtime, 'ridep': ridep, 
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)
    

class AMHarvest(Record):
    prefix = "n"
    dtypes = {
        'hfrst': NumberType, 'hlast': DateType, 'hpcnp': NumberType, 
        'hpcnr': NumberType, 'hmfrq': NumberType, 'hmgdd': NumberType, 
        'hmcut': NumberType, 'hmmow': NumberType, 'hrspl': NumberType, 
        'hmvs': NumberType
    }
    pars_fmt = {
        'hfrst': ">5.0f", 'hlast': "%y%j", 'hpcnp': ">5.0f", 'hpcnr': ">5.0f", 
        'hmfrq': ">5.0f", 'hmgdd': ">5.0f", 'hmcut': ">5.2f", 'hmmow': ">5.0f", 
        'hrspl': ">5.0f", 'hmvs': ">5.0f"
    }
    def __init__(self, hfrst:date, hlast:date, hpcnp:float=100, hpcnr:float=0,
                hmfrq:float=None, hmgdd:float=None, hmcut:float=None,
                hmmow:float=None, hrspl:float=None, hmvs:float=None):
        hfrst = 0 # Option not implemented yet on the GUI
        super().__init__()
        kwargs = {
            'hfrst': hfrst, 'hlast': hlast, 'hpcnp': hpcnp, 'hpcnr': hpcnr,
            'hmfrq': hmfrq, 'hmgdd': hmgdd, 'hmcut': hmcut, 'hmmow': hmmow, 
            'hrspl': hrspl, 'hmvs': hmvs
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)
    

class SimulationControls:
    dtypes = {
        "general": SCGeneral, "options": SCOptions, 
        "methods": SCMethods, "management": SCManagement, 
        "outputs": SCOutputs, "planting": AMPlanting,
        "irrigation": AMIrrigation, "nitrogen": AMNitrogen,
        "residues": AMResidues, "harvest": AMHarvest
    }
    def __init__(self, general:SCGeneral, options:SCOptions=None, 
                methods:SCMethods=None, management: SCManagement=None, 
                outputs:SCOutputs=None, planting:AMPlanting=None, 
                irrigation:AMIrrigation=None, nitrogen:AMNitrogen=None,
                residues:AMResidues=None, harvest:AMHarvest=None):
        # Set default values if not passed as parameters
        if not options: 
            options = SCOptions()
        if not methods: 
            methods = SCMethods()
        if not management: 
            management = SCManagement()
        if not outputs: 
            outputs = SCOutputs()
        # Same with Automatic management
        if not planting: 
            planting = AMPlanting(pfrst=general["sdate"], plast=general["sdate"])
        if not irrigation:
            irrigation = AMIrrigation()
        if not nitrogen:
            nitrogen = AMNitrogen()
        if not residues:
            residues = AMResidues()
        if not harvest:
            harvest = AMHarvest(hfrst=general["sdate"], hlast=general["sdate"])
        
        self.__data = {
            "general": general, "options": options, "methods": methods,
            "management": management, "outputs": outputs, "planting": planting,
            "irrigation": irrigation, "nitrogen": nitrogen, "residues": residues,
            "harvest": harvest
        }
        return
    
    def __setitem__(self, key, value):
        if key not in self.__data.keys():
            raise KeyError
        if not isinstance(value, self.dtypes[key]):
            raise TypeError
        self.__data[key] = value

    def __getitem__(self, key):
        key = key.lower()
        return self.__data[key]
    
    def __repr__(self):
        kws = [f"{key}={value!r}" for key, value in self.__data.items()]
        return "{}({})".format(type(self).__name__, ", ".join(kws))
    
    def _write_section(self):
        out_str = "*SIMULATION CONTROLS\n"
        out_str += "@N GENERAL     NYERS NREPS START SDATE RSEED SNAME.................... SMODEL\n"
        out_str += f" 1 GE          {self.__data['general']._write_row()}"
        out_str += "@N OPTIONS     WATER NITRO SYMBI PHOSP POTAS DISES  CHEM  TILL   CO2\n"
        out_str += f" 1 OP          {self.__data['options']._write_row()}"
        out_str += "@N METHODS     WTHER INCON LIGHT EVAPO INFIL PHOTO HYDRO NSWIT MESOM MESEV MESOL\n"
        out_str += f" 1 ME          {self.__data['methods']._write_row()}"
        out_str += "@N MANAGEMENT  PLANT IRRIG FERTI RESID HARVS\n"
        out_str += f" 1 MA          {self.__data['management']._write_row()}"
        out_str += "@N OUTPUTS     FNAME OVVEW SUMRY FROPT GROUT CAOUT WAOUT NIOUT MIOUT DIOUT VBOSE CHOUT OPOUT FMOPT\n"
        out_str += f" 1 OU          {self.__data['outputs']._write_row()}"
        out_str += f"\n@  AUTOMATIC MANAGEMENT\n"
        out_str += "@N PLANTING    PFRST PLAST PH2OL PH2OU PH2OD PSTMX PSTMN\n"
        out_str += f" 1 PL          {self.__data['planting']._write_row()}"
        out_str += "@N IRRIGATION  IMDEP ITHRL ITHRU IROFF IMETH IRAMT IREFF\n"
        out_str += f" 1 IR          {self.__data['irrigation']._write_row()}"
        out_str += "@N NITROGEN    NMDEP NMTHR NAMNT NCODE NAOFF\n"
        out_str += f" 1 NI          {self.__data['nitrogen']._write_row()}"
        out_str += "@N RESIDUES    RIPCN RTIME RIDEP\n"
        out_str += f" 1 RE          {self.__data['residues']._write_row()}"
        out_str += "@N HARVEST     HFRST HLAST HPCNP HPCNR\n"
        out_str += f" 1 HA          {self.__data['harvest']._write_row()}"
        return out_str
    

class Treatment(Record):
    prefix = "n"
    dtypes = {
        'r': NumberType, 'o': NumberType, "c": NumberType,
        'tname': DescriptionType, "cu": NumberType, "fl": NumberType,
        "sa": NumberType, "ic": NumberType, "mp": NumberType, "mi": NumberType,
        "mf": NumberType, "mr": NumberType, "mc": NumberType, "mt": NumberType,
        "me": NumberType, "mh": NumberType, "sm": NumberType
    }
    pars_fmt = {
        'r': ">1.0f", 'o': ">1.0f", "c": ">1.0f",
        'tname': ".<25", "cu": ">2.0f", "fl": ">2.0f",
        "sa": ">2.0f", "ic": ">2.0f", "mp": ">2.0f", "mi": ">2.0f",
        "mf": ">2.0f", "mr": ">2.0f", "mc": ">2.0f", "mt": ">2.0f",
        "me": ">2.0f", "mh": ">2.0f", "sm": ">2.0f"
    }
    def __init__(self, **kwargs):
        assert all([par in kwargs for par in self.pars_fmt.keys()])
        super().__init__()
        kwargs = {par: kwargs[par] for par in self.pars_fmt.keys()}
        kwargs["o"] = kwargs["c"] = kwargs["me"] = 0
        for name, value in kwargs.items():
            super().__setitem__(name, value)


class MowEvent(Record):
    prefix = 'trno '
    dtypes = {
        'date': DateType, 'mow': NumberType, 'rsplf': NumberType, 
        'mvs': NumberType, 'rsht': NumberType
    }
    pars_fmt = {
        'date': '%y%j', 'mow': '>5.0f', 'rsplf': '>5.0f', 
        'mvs': '>5.0f', 'rsht': '>5.1f'
    }
    def __init__(self, date:date, mow:float, rsplf:float, mvs:float, rsht:float):
        super().__init__()
        kwargs = {
            "date": date, "mow": mow, "rsplf": rsplf, "rsht": rsht, 'mvs': mvs
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value) 


class Mow(TabularRecord):
    prefix = "trno "
    dtypes = {}
    pars_fmt = {}
    table_dtype = MowEvent
    def __init__(self, table=list[MowEvent]):
        super().__init__()
        self.table = table

    @classmethod
    def from_file(cls, file):
        """
        Creates and return a Mow instance from a mow file.
        """
        encoding = detect_encoding(file)
        with open(file, 'r', encoding=encoding) as f:
            lines = f.readlines()
        lines = clean_comments(lines)
        lines = filter(lambda x: '@TRNO' not in x, lines)
        events = {}
        for line in lines:
            if len(line.strip()) > 10:
                pars = parse_pars_line(line[7:], cls.table_dtype.pars_fmt)
                level = int(line[:6])
                events[level] = events.get(level, []) + [cls.table_dtype(**pars)]
        events = {k: cls(v) for k, v in events.items()}
        return events


def get_header_range(l, h, pars_fmt):
    h_fmt = pars_fmt[h]
    # For the case of fields that have leading points, like those in 
    # field section
    if h_fmt[0] == ".": 
        h_fmt = h_fmt[1:]
    if h_fmt[0] == "<":
        start = l.lower().find(h)
        end = start + int(h_fmt[1:].split(".")[0])
    elif h_fmt[0] == ">":
        end = l.lower().find(h) + len(h)
        start = end - int(h_fmt[1:].split(".")[0])
    elif h_fmt[0] == "%":
        start = l.lower().find(h)
        end = start + 5 # Assuming all dates in FileX are a 5 character string
    else:
        raise ValueError("Variable format must be right or left justified")
    return (start, end)


def read_filex(filexpath):
    with open(filexpath, "r") as f:
        lines = f.readlines()
    lookup = "section"
    vals_dict = {}
    table_values = []
    vals = {}
    experiment = {}
    add_tier = False
    for l in lines:
        l = l.replace("\n", "")
        if len(l.strip()) < 2:
            if lookup == 'table header': # In case Table is not there
                experiment[section_cls.__name__] = vals_dict
                vals_dict = {}
                del level
            if lookup == "table values":
                if only_table:
                    for level, val in vals.items():
                        vals_dict[level] = section_cls(table=val)
                else:
                    vals["table"] = table_values
                    vals_dict[level] = section_cls(**vals)
                experiment[section_cls.__name__] = vals_dict
                vals_dict = {}
                table_values = []
                del level
            if lookup == "values":
                experiment[section_cls.__name__] = vals_dict
                vals_dict = {}
                del level
            if lookup == "simulation controls": 
                continue
            else:
                lookup = "section"
            vals = {}
            add_tier = False
            
            continue
        elif l[0] == "!":
            continue
        elif lookup == "header":
            if l[0] == "@":
                header = l.replace(".", " ").lower().split()
                header_start_end = {}
                start_i = 0
                for h in header[1:]:
                    header_start_end[h] = get_header_range(
                        l[start_i:], h, section_cls.pars_fmt
                    )
                    header_start_end[h] = (
                        header_start_end[h][0] + start_i,
                        header_start_end[h][1] + start_i
                    )
                    start_i = header_start_end[h][1]
                lookup = "values"
                continue
        elif lookup == "table header":
            if l[0] == "@":
                table_header = l.replace(".", " ").lower().split()
                table_header_start_end = {
                    h: get_header_range(l, h, section_cls.table_dtype.pars_fmt) 
                    for h in table_header[1:]
                }
                lookup = "table values"
                continue
        elif lookup == "values":
            # Special case for Field tier 2
            if (l[:2] == "@L"):
                add_tier = True
                header = l.replace(".", " ").lower().split()
                header_start_end = {
                    h: get_header_range(l, h, section_cls.pars_fmt) 
                    for h in header[1:]
                }
                continue
            vals = {
                key: l[header_start_end[key][0]:header_start_end[key][1]]
                for key in header[1:]
            }
            level = int(l[:2])
            if hasattr(section_cls, "table_dtype"):
                lookup = "table header"
            else:
                if add_tier:
                    for key, val in vals.items():
                        vals_dict[level][key] = val
                else:
                    vals_dict[level] = section_cls(**vals)
            continue                
        elif lookup == "table values":
            if l[0] == "@":
                vals["table"] = table_values
                vals_dict[level] = section_cls(**vals)
                table_values = []
                lookup = "values"
                del level
                continue
            row = section_cls.table_dtype(**{
                key: l[table_header_start_end[key][0]:
                    table_header_start_end[key][1]]
                for key in table_header[1:]
            })
            if only_table:
                level = int(l[:2])
                vals[level] = vals.get(level, []) + [row]
            table_values.append(row)
        elif lookup == "simulation controls":
            if l[0] == "@": # Header 
                if "AUTOMATIC" in l:
                    continue
                header = l.replace(".", " ").lower().split()
                simcon_dtype = SimulationControls.dtypes[header[1]]
                header_start_end = {
                    h: get_header_range(
                        l, h, simcon_dtype.pars_fmt
                    ) 
                    for h in header[2:]
                }
            else: # Values
                vals = {
                    key: l[header_start_end[key][0]:header_start_end[key][1]]
                    for key in header[2:]
                }
                level = int(l[:2])
                if sim_controls_dict.get(level, False):
                    sim_controls_dict[level][header[1]] = simcon_dtype(**vals)
                else:
                    sim_controls_dict[level] = {
                        header[1]: simcon_dtype(**vals)
                    }
            
        elif lookup == "section":
            if l[:6] == "*TREAT":
                section_cls = Treatment
            elif l[:6] == "*PLANT":
                section_cls = Planting
            elif l[:6] == "*CULTI":
                section_cls = Cultivar
            elif l[:6] == "*HARVE":
                section_cls = Harvest
            elif l[:6] == "*INITI":
                section_cls = InitialConditions
            elif l[:6] == "*FERTI":
                section_cls = Fertilizer
            elif l[:6] == "*SOIL ":
                section_cls = SoilAnalysis
            elif l[:6] == "*IRRIG":
                section_cls = Irrigation
            elif l[:6] == "*RESID":
                section_cls = Residue
            elif l[:6] == "*CHEMI":
                section_cls = Chemical
            elif l[:6] == "*TILLA":
                section_cls = Tillage
            elif l[:6] == "*FIELD": 
                section_cls = Field
            elif l[:6] == "*SIMUL":
                section_cls = SimulationControls
                sim_controls_dict = {}
                # Simulation Controls must be the last section
            else:
                continue
            # Some sections are only tables, for those go directly to table
            # header
            only_table = len(section_cls.dtypes) == 0
            if only_table:
                lookup = "table header"
                vals = {}
            else:
                lookup = "header"
                if section_cls.__name__ == "SimulationControls":
                    lookup = "simulation controls"
        else:
            raise ValueError
    
    # Build the treatments dictionary
    treatments = {}
    for n, treatment in experiment["Treatment"].items():
        treatments[n] = {}
        for factor, f in FACTOR_LEVELS.items():
            if factor in experiment:
                level = experiment[factor].get(treatment[f], False)
                if level:
                    treatments[n][factor] = level
        treatments[n]["SimulationControls"] = sim_controls_dict.get(
            treatment["sm"], False
        )
        assert treatments[n]["SimulationControls"]
        treatments[n]["SimulationControls"] = SimulationControls(
            **treatments[n]["SimulationControls"]
        )
    return treatments
        
def create_filex(field:Field, cultivar:Cultivar, planting:Planting, 
                simulation_controls:SimulationControls, harvest:Harvest=None,
                initial_conditions:InitialConditions=None, 
                fertilizer:Fertilizer=None, soil_analysis:SoilAnalysis=None, 
                irrigation:Irrigation=None, residue:Residue=None, 
                chemical:Chemical=None, tillage:Tillage=None):
    
    experiment_name = field["id_field"][:4] +\
        simulation_controls["general"]["sdate"].strftime('%y01') + cultivar.code
    
    treatment = Treatment(**{
        "r": 1, "o": 0, "c": 0, "tname": "DSSATspatial", "cu": 1, "fl": 1, 
        "mp": 1, 'sm': 1, 'me': 0,
        "sa": 1 if soil_analysis else 0,  
        "ic": 1 if initial_conditions else 0,
        'mi': 1 if irrigation else 0,
        'mf': 1 if fertilizer else 0,
        'mr': 1 if residue else 0,
        'mc': 1 if chemical else 0,
        'mt': 1 if tillage else 0,
        'mh': 1 if harvest else 0
    })
    
    # Aggregate string components sequentially into a list
    file_blocks = [
        f"*EXP.DETAILS: {experiment_name}\n\n",
        treatment._write_section() + "\n",
        cultivar._write_section() + "\n",
        field._write_section() + "\n",
        planting._write_section() + "\n"
    ]
    
    if soil_analysis: file_blocks.append(soil_analysis._write_section() + "\n")
    if initial_conditions: file_blocks.append(initial_conditions._write_section() + "\n")
    if irrigation: file_blocks.append(irrigation._write_section() + "\n")
    if fertilizer: file_blocks.append(fertilizer._write_section() + "\n")
    if residue: file_blocks.append(residue._write_section() + "\n")
    if chemical: file_blocks.append(chemical._write_section() + "\n")
    if tillage: file_blocks.append(tillage._write_section() + "\n")
    if harvest: file_blocks.append(harvest._write_section() + "\n")
    
    file_blocks.append(simulation_controls._write_section())

    # Compile final payload in a single memory allocation
    return "".join(file_blocks)
    
    