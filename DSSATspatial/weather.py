#weather.py
#created and modified by sakthivel sivakumar

#import libraries
import os
from .partypes import (
    NumberType, Record, DescriptionType, parse_pars_line
)

class WeatherStation(Record):
    dtypes = {
        "insi": DescriptionType, 'lat': NumberType, 'long': NumberType, 
        'elev': NumberType, 'tav': NumberType, 'amp': NumberType,  
        'refht': NumberType, 'wndht': NumberType, "cco2": NumberType
    }
    pars_fmt = {
        "insi": '>4', 'lat': '>8.3f', 'long': '>8.3f', 'elev': '>5.0f', 
        'tav': '>5.1f', 'amp': '>5.1f', 'refht': '>5.1f', 'wndht': '>5.1f',
        'cco2': '>5.1f'
    }
    def __init__(self, lat:float, long:float, insi:str="WSTA", elev:float=None, 
                 tav:float=None, amp:float=None, refht:float=None, wndht:float=None, 
                 cco2:float=None, filename:str=None):
        super().__init__()
        kwargs = {
            "insi": insi, 'lat': lat, 'long': long, 'elev': elev, 'tav': tav, 
            'amp': amp, 'refht': refht, 'wndht': wndht, 'cco2': cco2
        }
        for name, value in kwargs.items():
            super().__setitem__(name, value)
        # Store the authentic base filename for FileX injection
        self.filename = filename
    
    def _write_section(self):
        raise NotImplementedError
    
    def __setitem__(self, key, value):
        if key == "insi":
            assert len(value.strip()) == 4, "INSI must be a 4-character code"
        super().__setitem__(key, value)

    @property
    def str(self):
        # Primary: Return the exact base filename of the authentic .WTH file
        if getattr(self, 'filename', None):
            return self.filename[:8]
            
        # Fallback: DSSAT naming convention (INSI + YY + NN)
        wth_year = getattr(self, 'wth_year', 2000) 
        wth_len = getattr(self, 'wth_len', 1)      
        wth_filename = f'{self["insi"]}{str(wth_year)[-2:]}{wth_len:02d}'
        
        return wth_filename
        
    @classmethod
    def from_files(cls, files:list[str]):
        assert len(files) > 0, "files can't be an empty list"
        
        # In a batch-processing spatial grid, we map a single WTH file per grid point
        wth_file = files[0]
        
        # Extract the raw base filename without extension (e.g., 'ACSA0101')
        base_filename = os.path.splitext(os.path.basename(wth_file))[0]
        
        sta_pars = {}
        with open(wth_file, "r") as f:
            for line in f:
                if "@ INSI" in line:
                    sta_pars = parse_pars_line(f.readline()[2:], cls.pars_fmt)
                    break
        
        sta_pars["filename"] = base_filename
        return cls(**sta_pars)