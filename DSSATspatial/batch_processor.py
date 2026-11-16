#batch_processor.py
#created and modified by sakthivel sivakumar

#import libraries
import os
import sys
import glob
import shutil
import re
import warnings
import tempfile
import threading
import pandas as pd
import pyarrow.parquet as pq
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import zipfile

# Import base DSSAT classes
from . import filex, ProcessWTH, SoilProfile, crop
from contextlib import redirect_stdout
from . import partypes
from .run import DSSAT

# Global Execution Constants
FERT_MATERIAL = {'N': 'FE005', 'P': 'FE010', 'K': 'FE016'}

# 1. Environment Setup
def prepare_workspace(sim_dir, is_batch=True):
    # Ensure base simulation directory exists safely
    os.makedirs(sim_dir, exist_ok=True)
    
    # Initialize DSSATspatial base parameters to prevent first-run crashes
    partypes.CODE_VARS['smodel'] = []
    from contextlib import redirect_stdout
    with open(os.devnull, 'w') as null_out, redirect_stdout(null_out):
        dummy_dssat = DSSAT()
        dummy_dssat.close()

    # If it is a single run, stop here and avoid clutter
    if not is_batch:
        return None, None, None, None

    # For batch runs, generate the full logging/archive hierarchy
    base_name = os.path.basename(sim_dir)
    log_dir = os.path.join(sim_dir, "logs")
    archive_dir = os.path.join(sim_dir, f"{base_name}_ARCHIVE")
    failed_log = os.path.join(sim_dir, f"{base_name}_Failed_Treatments.txt")
    output_csv = os.path.join(sim_dir, f"{base_name}_Summary.csv")

    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(archive_dir, exist_ok=True)
    
    # Purge orphaned execution folders and temporary paths from aborted runs
    for item in os.listdir(sim_dir):
        item_path = os.path.join(sim_dir, item)
        if os.path.isdir(item_path):
            if re.match(r'^T_\d+$', item) or item in ['Success_Temp', 'Error_Temp']:
                shutil.rmtree(item_path, ignore_errors=True)
        
    return log_dir, archive_dir, failed_log, output_csv


# 2. Weather Processing
def get_weather_ids_from_master(xlsx_path, sheet_name, id_column):
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
    weather_ids = df[id_column].dropna().astype(str).str.strip().unique().tolist()
    if not weather_ids:
        raise ValueError(f"No weather IDs found in column '{id_column}' of sheet '{sheet_name}'")
    return weather_ids

def get_wth_files_for_ids(folder_path, weather_ids):
    wth_files = []
    missing_ids = []
    for weather_id in weather_ids:
        candidate_path = os.path.join(folder_path, f"{weather_id}.WTH")
        if os.path.exists(candidate_path):
            wth_files.append(candidate_path)
        else:
            missing_ids.append(weather_id)
    if missing_ids:
        print(f"Warning: {len(missing_ids)} weather IDs have no matching .WTH file: {missing_ids}")
    if not wth_files:
        raise FileNotFoundError(f"No matching .WTH files found in: {folder_path}")
    return wth_files

def load_single_station(wth_path):
    station_name = os.path.splitext(os.path.basename(wth_path))[0]
    station = ProcessWTH.from_files([wth_path])
    return station_name, station

def load_weather_stations_parallel(wth_files, max_workers):
    stations = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(load_single_station, path): path for path in wth_files}
        for future in as_completed(futures):
            station_name, station = future.result()
            stations[station_name] = station
    return stations

# 3. Soil Processing
def get_soil_ids(xlsx_path, sheet_name, id_column):
    if not os.path.exists(xlsx_path):
        raise FileNotFoundError(f"Master xlsx not located at: {xlsx_path}")
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
    return df[id_column].dropna().astype(str).str.strip().unique().tolist()

def index_soil_blocks(sol_path):
    with open(sol_path, "r") as f:
        lines = f.readlines()

    header_lines = []
    blocks = {}
    current_id = None
    current_lines = []
    start_idx = 0
    
    if lines and lines[0].startswith("*"):
        header_lines.append(lines[0])
        start_idx = 1

    for line in lines[start_idx:]:
        if line.startswith("*"):
            if current_id is not None:
                blocks[current_id] = current_lines
            token = line[1:].split()[0] if line[1:].split() else ""
            current_id = token
            current_lines = [line]
        else:
            if current_id is not None:
                current_lines.append(line)
            else:
                header_lines.append(line)

    if current_id is not None:
        blocks[current_id] = current_lines

    return header_lines, blocks

def load_single_soil_from_block(soil_id, header_lines, block_lines):
    try:
        # Calls the new in-memory instantiation method we will build in soil.py
        soil_obj = SoilProfile.from_block(soil_id, header_lines, block_lines)
        return soil_id, soil_obj, None
    except Exception as e:
        return soil_id, None, e

def initialize_all_soils_in_memory(ids, header_lines, blocks, stop_on_error=False, max_workers=4, show_sample_errors=5):
    soils = {}
    errors = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for soil_id in ids:
            if soil_id in blocks:
                futures[executor.submit(load_single_soil_from_block, soil_id, header_lines, blocks[soil_id])] = soil_id
            else:
                errors.append((soil_id, ValueError(f"Soil ID {soil_id} not found in master .SOL")))
                
        for future in as_completed(futures):
            soil_id, soil_obj, error = future.result()
            if error is not None:
                errors.append((soil_id, error))
                if stop_on_error:
                    raise error
            else:
                soils[soil_id] = soil_obj

    failed = [soil_id for soil_id, _ in errors]
    if errors:
        print(f"\nSample errors (showing up to {show_sample_errors}):")
        for soil_id, error in errors[:show_sample_errors]:
            print(f"  {soil_id}: {type(error).__name__}: {error}")
    return soils, failed

def run_batch_soil_load(master_xlsx_path, master_sheet_name, master_id_column, sol_file_path, max_workers=4):
    # Fetch required IDs and index the master file into memory dicts
    ids = get_soil_ids(master_xlsx_path, master_sheet_name, master_id_column)
    header_lines, blocks = index_soil_blocks(sol_file_path)

    missing = [sid for sid in ids if sid not in blocks]
    if missing:
        print(f"{len(missing)} IDs not found in master .SOL:", missing)

    # Pass the memory blocks directly to the threaded initializer
    soils, failed = initialize_all_soils_in_memory(
        ids=ids, 
        header_lines=header_lines, 
        blocks=blocks, 
        stop_on_error=False, 
        max_workers=max_workers
    )

    return soils

def load_weather(xlsx_path, sheet_name, id_column, folder_path, max_workers=4):
    # Extract unique station identifiers from the experimental matrix
    weather_ids = get_weather_ids_from_master(xlsx_path, sheet_name, id_column)
    # Resolve physical file paths for valid station records
    wth_files = get_wth_files_for_ids(folder_path, weather_ids)
    # Concurrently parse and ingest meteorological records into memory
    stations = load_weather_stations_parallel(wth_files, max_workers)
    return stations

def load_soil(xlsx_path, sheet_name, id_column, sol_file_path, max_workers=4):
    # Concurrently parse and ingest pedological profiles matching treatment records
    soils = run_batch_soil_load(xlsx_path, sheet_name, id_column, sol_file_path, max_workers)
    return soils

# load treatments
def load_management_file(filex_path):
    all_treatments = filex.read_filex(filex_path)
    treatments = {}
    for treatment_num in all_treatments:
        treatments[treatment_num] = all_treatments[treatment_num]
    return treatments


# run treatment
def clone_record(record):
    new_record = object.__new__(type(record))
    for attr_name, attr_value in vars(record).items():
        if attr_name.endswith('__data'):
            attr_value = dict(attr_value)
        new_record.__dict__[attr_name] = attr_value
    return new_record

def convert_to_yyddd(date_val):
    date_str = str(int(float(date_val)))
    if len(date_str) == 8:
        date_obj = datetime.strptime(date_str, "%Y%m%d")  # yyyymmdd
    elif len(date_str) == 7:
        date_obj = datetime.strptime(date_str, "%Y%j")  # yyyyddd
    elif len(date_str) == 5:
        date_obj = datetime.strptime(date_str, "%y%j")  # yyddd
    else:
        raise ValueError(f"Unexpected date format: {date_str}")
    yy = date_obj.year % 100
    doy = date_obj.timetuple().tm_yday
    return f"{yy:02d}{doy:03d}"

def parse_planting_date(date_val):
    date_str = str(int(float(date_val)))
    if len(date_str) == 8:
        return datetime.strptime(date_str, "%Y%m%d").date()  # yyyymmdd
    elif len(date_str) == 7:
        return datetime.strptime(date_str, "%Y%j").date()  # yyyyddd
    elif len(date_str) == 5:
        return datetime.strptime(date_str, "%y%j").date()  # yyddd
    else:
        raise ValueError(f"Unexpected planting_date format: {date_str}")

def build_tillage_section(row):
    # Process explicit calendar TDATE if present
    if 'TDATE' in row and pd.notna(row['TDATE']) and str(row['TDATE']).strip():
        tdate = parse_planting_date(row['TDATE'])
        # Since TIMPL and TDEP were skipped in excel, hardcode standard defaults
        timpl = 'TI003'
        tdep = 20.0
        tillage_event = filex.TillageEvent(tdate=tdate, timpl=timpl, tdep=tdep)
        return filex.Tillage(table=[tillage_event])
    return None

def build_sdate(row, buffer_days):
    planting_date = parse_planting_date(row['planting_date'])
    min_das = 0
        
    # Check Fertilizer
    for col in ['N_application', 'P_application', 'K_application']:
        f_events = parse_nutrient_schedule(row.get(col, ''))
        if f_events:
            min_das = min(min_das, min([das for das, kg in f_events]))
            
    # Check Irrigation
    i_events = parse_irrigation_schedule(row.get('IRRIG_SCHEDULE', ''))
    if i_events:
        min_das = min(min_das, min([das for das, mm in i_events]))

    # Calculate simulation start date accommodating the earliest event plus buffer
    sim_start = planting_date + timedelta(days=min_das - buffer_days)
    yy = sim_start.year % 100
    doy = sim_start.timetuple().tm_yday
    return f"{yy:02d}{doy:03d}"

def set_start_date(simulation_controls, sdate):
    simulation_controls['general']['sdate'] = sdate
    simulation_controls['general']['start'] = 'S'
    return simulation_controls

def build_planting(row, base_treatment):
    base_p = base_treatment['Planting']
    planting_date = convert_to_yyddd(row['planting_date'])
    
    def get_val(col, default):
        val = row.get(col, default)
        return default if pd.isna(val) else val
        
    planting = filex.Planting(
        pdate=planting_date,
        ppop=get_val('PLPOP', base_p['ppop']),
        ppoe=get_val('PPOE', base_p['ppoe']),
        plme=str(get_val('PLME', base_p['plme'])).strip().upper(),
        plds=str(get_val('PLDS', base_p['plds'])).strip().upper(),
        plrs=get_val('PLRS', base_p['plrs']),
        plrd=get_val('PLRD', base_p['plrd']),
        pldp=get_val('PLDP', base_p['pldp']),
        page=get_val('PAGE', base_p.get('page', -99)),
        plwt=base_p.get('plwt', -99)  # strictly inherited from the master RIX file
    )
    return planting

def parse_irrigation_schedule(schedule_str):
    events = []
    if pd.isna(schedule_str) or str(schedule_str).strip().lower() in ['', 'nan']:
        return events
    for pair in str(schedule_str).split(';'):
        pair = pair.strip()
        if not pair:
            continue
        # Use rsplit to safely handle negative DAS values like -1-17
        das_str, mm_str = pair.rsplit('-', 1)
        events.append((int(das_str), float(mm_str)))
    return events

def build_irrigation_section(row):
    schedule_str = row.get('IRRIG_SCHEDULE', '')
    if pd.isna(schedule_str) or str(schedule_str).strip().lower() in ['', 'nan']:
        return None
    planting_date = parse_planting_date(row['planting_date'])
    irrigation_events = [
        filex.IrrigationEvent(idate=planting_date + timedelta(days=das), irval=mm, irop='IR001')
        for das, mm in parse_irrigation_schedule(schedule_str)
    ]
    return filex.Irrigation(table=irrigation_events, iame='IR001')

def apply_irrigation_mode(row, simulation_controls):
    irr_mode = str(row.get('Irrigation', '')).strip().upper()
    schedule_str = row.get('IRRIG_SCHEDULE', '')
    if pd.isna(schedule_str) or str(schedule_str).strip().lower() in ['', 'nan']:
        has_schedule = False
    else:
        has_schedule = True
    if irr_mode == 'IR' and has_schedule:
        simulation_controls['management']['irrig'] = 'R'  # Scheduled
    elif irr_mode == 'IR':
        simulation_controls['management']['irrig'] = 'A'  # Automatic
    elif irr_mode == 'RF':
        simulation_controls['management']['irrig'] = 'N'  # Rainfed
    return simulation_controls

def parse_nutrient_schedule(schedule_str):
    events = []
    if pd.isna(schedule_str) or str(schedule_str).strip().lower() in ['', 'nan']:
        return events
    for pair in str(schedule_str).split(';'):
        pair = pair.strip()
        if not pair:
            continue
        # Use rsplit to safely handle negative DAS values like -1-17
        das_str, kg_str = pair.rsplit('-', 1)
        events.append((int(das_str), float(kg_str)))
    return events

def build_fertilizer_section(row, fert_material):
    fert_flag = str(row.get('Fertilizer', '')).strip().lower()
    if fert_flag != 'yes':
        return None, 'N'  # no fertilizer block, N/P/K columns not read
    planting_date = parse_planting_date(row['planting_date'])
    fert_events = []
    for nutrient, col in [('N', 'N_application'), ('P', 'P_application'), ('K', 'K_application')]:
        for das, kg in parse_nutrient_schedule(row.get(col, '')):
            event_kwargs = {
                'fdate': planting_date + timedelta(days=das),
                'fmcd': fert_material[nutrient],
                'facd': 'AP001',
                'fdep': 0.0,
                'famn': 0.0, 'famp': 0.0, 'famk': 0.0
            }
            event_kwargs[f'fam{nutrient.lower()}'] = kg
            fert_events.append(filex.FertilizerEvent(**event_kwargs))
    return filex.Fertilizer(table=fert_events), 'R'

def set_nyears(simulation_controls, nyears):
    simulation_controls['general']['nyers'] = nyears
    return simulation_controls

def build_run_kwargs(row, weather_code, soil_code, cultivar_key, treatments, stations, soils, crop_objects, fert_material, buffer_days):
    trt_num = int(row.get('treatment', 1))
    base_treatment = treatments.get(trt_num, treatments.get(1))
    
    field = clone_record(base_treatment['Field'])
    field['wsta'] = stations[weather_code]
    field['id_soil'] = soils[soil_code]
    run_kwargs = {'field': field, 'cultivar': crop_objects[cultivar_key]}
    
    # Inject all factor blocks from the master RIX file
    for key, arg_name in [
        ('Chemical', 'chemical'),
        ('SoilAnalysis', 'soil_analysis'),
        ('InitialConditions', 'initial_conditions'),
        ('Residue', 'residue'),
        ('Harvest', 'harvest'),
        ('Irrigation', 'irrigation'),
        ('Fertilizer', 'fertilizer'),
        ('Tillage', 'tillage')
    ]:
        if key in base_treatment:
            run_kwargs[arg_name] = clone_record(base_treatment[key])

    run_kwargs['planting'] = build_planting(row, base_treatment)

    # Excel scheduling overlay
    irrigation_section = build_irrigation_section(row)
    if irrigation_section is not None:
        run_kwargs['irrigation'] = irrigation_section

    fertilizer_section, ferti_flag = build_fertilizer_section(row, fert_material)
    if fertilizer_section is not None:
        run_kwargs['fertilizer'] = fertilizer_section

    tillage_section = build_tillage_section(row)
    if tillage_section is not None:
        run_kwargs['tillage'] = tillage_section

    if 'SimulationControls' in base_treatment:
        sim_controls = clone_record(base_treatment['SimulationControls'])
        sim_controls['general'] = clone_record(sim_controls['general'])
        sim_controls['options'] = clone_record(sim_controls['options'])
        sim_controls['methods'] = clone_record(sim_controls['methods'])
        sim_controls['management'] = clone_record(sim_controls['management'])
        sim_controls = apply_irrigation_mode(row, sim_controls)
        sim_controls['management']['ferti'] = ferti_flag
        
        # 1. Harvest Mode Logic (Falls back to FileX if empty in Excel)
        harv_mode_val = str(row.get('Harvest_mode', '')).strip().upper()
        if harv_mode_val in ['M', 'R', 'A']:
            sim_controls['management']['harvs'] = harv_mode_val
        
        # If mode is R, calculate exactly when to harvest based on HDATE_DAS
        if sim_controls['management']['harvs'] == 'R' and 'HDATE_DAS' in row and pd.notna(row['HDATE_DAS']) and str(row['HDATE_DAS']).strip():
            if 'harvest' in run_kwargs and run_kwargs['harvest'].table:
                new_pdate = parse_planting_date(row['planting_date'])
                harvest_date = new_pdate + timedelta(days=int(float(row['HDATE_DAS'])))
                run_kwargs['harvest'].table[0]['hdate'] = harvest_date

        # 2. Dynamic Options and Methods Overrides (Falls back to FileX if empty in Excel)
        if 'CO2' in row and pd.notna(row['CO2']) and str(row['CO2']).strip():
            sim_controls['options']['co2'] = str(row['CO2']).strip().upper()
        if 'EVAPO' in row and pd.notna(row['EVAPO']) and str(row['EVAPO']).strip():
            sim_controls['methods']['evapo'] = str(row['EVAPO']).strip().upper()
        if 'INFIL' in row and pd.notna(row['INFIL']) and str(row['INFIL']).strip():
            sim_controls['methods']['infil'] = str(row['INFIL']).strip().upper()
        if 'PHOTO' in row and pd.notna(row['PHOTO']) and str(row['PHOTO']).strip():
            sim_controls['methods']['photo'] = str(row['PHOTO']).strip().upper()
        
        # Base SDATE from explicit Excel override or fallback to dynamic calculation
        if 'SDATE' in row and pd.notna(row['SDATE']) and str(row['SDATE']).strip():
            sim_start = parse_planting_date(row['SDATE'])
            sdate_str = f"{sim_start.year % 100:02d}{sim_start.timetuple().tm_yday:03d}"
        else:
            sdate_str = build_sdate(row, buffer_days)
            sim_start = datetime.strptime(sdate_str, "%y%j").date()
            
            # Override to 7 days before Tillage if Tillage is present and earlier
            if 'tillage' in run_kwargs and run_kwargs['tillage'].table:
                till_dates = []
                for evt in run_kwargs['tillage'].table:
                    if hasattr(evt['tdate'], 'year') and evt['tdate'].year < 9000:
                        pure_date = datetime(evt['tdate'].year, evt['tdate'].month, evt['tdate'].day).date()
                        till_dates.append(pure_date)
                        
                if till_dates:
                    earliest_till = min(till_dates)
                    if earliest_till < sim_start:
                        sim_start = earliest_till - timedelta(days=buffer_days)
                        sdate_str = f"{sim_start.year % 100:02d}{sim_start.timetuple().tm_yday:03d}"
                        
        sim_controls = set_nyears(sim_controls, int(row['NYEARS']))
        sim_controls = set_start_date(sim_controls, sdate_str)
        run_kwargs['simulation_controls'] = sim_controls
        
    return run_kwargs

class ThreadLogRouter:
    def __init__(self):
        self.local = threading.local()  # each thread sees its own registered file

    def register(self, file_handle):
        self.local.file_handle = file_handle

    def write(self, message):
        handle = getattr(self.local, "file_handle", None)
        if handle is not None:
            handle.write(message)
        else:
            sys.__stdout__.write(message)  # fallback if called outside a worker thread

    def flush(self):
        handle = getattr(self.local, "file_handle", None)
        if handle is not None:
            handle.flush()

def treatment_done(sim_folder):
    success_files = ['OVERVIEW.OUT', 'PlantGro.OUT', 'Summary.OUT']
    issue_files = ['WARNING.OUT', 'ERROR.OUT']
    has_success = all(os.path.exists(os.path.join(sim_folder, f)) for f in success_files)
    has_issue = all(os.path.exists(os.path.join(sim_folder, f)) for f in issue_files)
    return has_success or has_issue

def run_single_treatment(row, pad_width, sim_dir, wth_folder_path, treatments, stations, soils, crop_objects, fert_material, buffer_days):
    weather_code = str(row['weather']).strip()
    soil_code = str(row['soil']).strip()
    cultivar_key = str(row['cultivar']).strip()
    run_label = f"T_{int(row['treatment']):0{pad_width}d}"
    sim_folder = os.path.join(sim_dir, run_label)

    if treatment_done(sim_folder):
        print(f"{run_label} already completed, skipping.")
        return run_label, None, "SKIPPED"

    try:
        run_kwargs = build_run_kwargs(row, weather_code, soil_code, cultivar_key, treatments, stations, soils, crop_objects, fert_material, buffer_days)
        dssat = DSSAT(sim_folder)

        # Inject the master weather directory path into the execution arguments
        run_kwargs['wth_dir'] = wth_folder_path
        run_kwargs['verbose'] = False  # Suppress default run.py output

        results = dssat.run_treatment(**run_kwargs)
        
        # Extract dataset metadata for the custom header
        trt_num = int(row['treatment'])
        cultivar = str(row['cultivar']).strip()
        soil = str(row['soil']).strip()
        wsta = str(row['weather']).strip()
        
        # Filter and inject custom log output
        if hasattr(dssat, 'stdout') and dssat.stdout:
            header = f"\n--- TRT: {trt_num} | CULTIVAR: {cultivar} | SOIL: {soil} | WSTA: {wsta} ---"
            print(header)
            
            for line in dssat.stdout.split('\n'):
                # Skip blank lines and repetitive execution banners
                if not line.strip() or "COPYRIGHT" in line or "DSSAT" in line or "====" in line:
                    continue
                
                # Replace the generic "1" run and treatment identifiers with the true treatment number
                # Matches the leading run format (e.g., "  1 SG   1" -> " 23 SG  23")
                clean_line = re.sub(r'^\s*1\s+([A-Z]{2})\s+1', f"{trt_num:>3} \\1 {trt_num:>3}", line)
                print(clean_line)

        return run_label, results, None
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        print(error_msg)
        return run_label, None, error_msg

def run_worker(worker_id, treatments_chunk, pad_width, stdout_router, progress_bar, progress_lock, worker_pad, log_dir, 
               sim_dir, wth_folder_path, treatments, stations, soils, crop_objects, fert_material, buffer_days,
               xlsx_path=None, sheet_name=None):
    worker_tag = f"worker_{worker_id:0{worker_pad}d}"
    output_path = os.path.join(log_dir, f"{worker_tag}_output.txt")
    error_path = os.path.join(log_dir, f"{worker_tag}_errors.txt")
    
    worker_results = {}
    worker_failures = {}
    worker_skipped = []

    with open(output_path, "a", encoding="utf-8") as output_handle:
        output_handle.write(f"\n--- NEW EXECUTION START ---\n")
        output_handle.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output_handle.write(f"Input Excel File: {xlsx_path}\n")
        output_handle.write(f"Master Sheetname: {sheet_name}\n")
        output_handle.write(f"Input WTH Folder: {wth_folder_path}\n")
        output_handle.write(f"---------------------------\n\n")

        stdout_router.register(output_handle)  # from now on, this thread's prints go here

        for row in treatments_chunk:
            run_label, result, error = run_single_treatment(row, pad_width, sim_dir, wth_folder_path, treatments, stations, soils, crop_objects, fert_material, buffer_days)
            if error == "SKIPPED":
                worker_skipped.append(run_label)
            elif error is None:
                worker_results[run_label] = result
            else:
                worker_failures[run_label] = error
                with open(error_path, "a", encoding="utf-8") as f:
                    f.write(f"{run_label}: {error}\n")
            with progress_lock:
                progress_bar.update(1)

    return worker_results, worker_failures, worker_skipped

def parse_summary_out(filepath):
    # Parses a single Summary.OUT file: finds the @ header line and the data rows below it
    try:
        with open(filepath, "r") as f:
            lines = f.readlines()
        header_idx = None
        for i, line in enumerate(lines):
            if line.startswith("@"):
                header_idx = i
                break
        if header_idx is None:
            return None  # no header found, skip this file
        header = lines[header_idx].lstrip("@").split()
        data_rows = []
        for line in lines[header_idx + 1:]:
            if line.strip() == "" or line.startswith("*") or line.startswith("!"):
                continue
            values = line.split()
            if len(values) != len(header):
                continue  # malformed row, skip quietly
            data_rows.append(values)
        if not data_rows:
            return None
        return pd.DataFrame(data_rows, columns=header)
    except Exception as e:
        # Catches zero-byte file I/O errors or structural pandas exceptions silently
        return None

def extract_treatment_number(folder_name):
    # Folder name is like "T_001" -> extract the numeric part -> 1
    try:
        return int(folder_name.split('_')[1])
    except (IndexError, ValueError):
        return None

def load_treatment_cultivar_map(master_xlsx, master_sheet):
    master_df = pd.read_excel(master_xlsx, sheet_name=master_sheet)
    master_df.columns = master_df.columns.str.strip()
    return dict(zip(master_df['treatment'].astype(int), master_df['cultivar']))

def run_dssat(row_number, xlsx_path, sheet_name, sim_dir, wth_folder, treatments, stations, soils, crops, sdate_buffer=7, fert_material=FERT_MATERIAL): 
   
    # 1. Load the master dataframe
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
    
    # 2. Automatically calculate pad_width based on max treatment number
    pad_width = len(str(int(df['treatment'].max())))
    
    # 3. Convert user's 1-based row number to 0-based pandas index
    if row_number < 1 or row_number > len(df):
        raise ValueError(f"Row number {row_number} is out of bounds. Must be between 1 and {len(df)}.")
    
    row_index = row_number - 1
    row = df.iloc[row_index]
    
    # 4. Execute the simulation
    prepare_workspace(sim_dir, is_batch=False)
    
    # Wrapper to suppress console prints strictly for this execution
    original_stdout = sys.stdout
    with open(os.devnull, 'w') as devnull:
        sys.stdout = devnull
        try:
            result = run_single_treatment(row, pad_width, sim_dir, wth_folder, treatments, stations, soils, crops, fert_material, sdate_buffer)
        finally:
            sys.stdout = original_stdout
            
    if result[2] is not None and result[2] != "SKIPPED":
        print(f"\n[EXECUTION FAILED] {result[0]} encountered an error:")
        print(result[2])
                
    return result


def run_spatial_batch(xlsx_path, sheet_name, sim_dir, wth_folder, treatments, stations, soils, crops, 
                      max_workers=8, batch_size=100, compress=True, sdate_buffer=7, 
                      fert_material=FERT_MATERIAL, columns_to_keep=None, summary_filename="Summary.OUT"):
    
    # Automatically prepare directories and derive internal paths
    log_dir, archive_dir, failed_log, output_csv = prepare_workspace(sim_dir,is_batch=True)

    # Consolidates batch chunking, parallel execution, extraction, and archiving
    master_df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
    master_df.columns = master_df.columns.str.strip()
    total_rows = len(master_df)
    pad_width = len(str(int(master_df['treatment'].max())))
    worker_pad = len(str(max_workers))
    
    cultivar_map = load_treatment_cultivar_map(xlsx_path, sheet_name)
    
    # 1. State-Tracking: Scan existing archives for completed treatments  
    import glob # Force the import directly in the local scope 
    completed_treatments = set()
    existing_zips = glob.glob(os.path.join(archive_dir, "Success_Batch_*.zip"))
    batch_offset = len(existing_zips)
    
    trt_pattern = re.compile(r'T_(\d+)/')
    for zip_path in existing_zips:
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                for name in z.namelist():
                    match = trt_pattern.search(name)
                    if match:
                        completed_treatments.add(int(match.group(1)))
        except zipfile.BadZipFile:
            continue
            
    # 2. Filter the master dataframe to exclude completed treatments
    if completed_treatments:
        master_df = master_df[~master_df['treatment'].isin(completed_treatments)]
        total_rows = len(master_df)
        print(f"Resuming execution: Skipped {len(completed_treatments)} completed treatments. {total_rows} remaining.")
        
    def consolidate_summary():
        batch_csv_files = sorted(glob.glob(os.path.join(archive_dir, "Success_Batch_*.csv")))
        if batch_csv_files:
            if os.path.exists(output_csv):
                os.remove(output_csv)
            
            merged_master_df = pd.concat([pd.read_csv(f) for f in batch_csv_files], ignore_index=True)
            
            if columns_to_keep:
                for col in columns_to_keep:
                    if col not in merged_master_df.columns:
                        merged_master_df[col] = None
                merged_master_df = merged_master_df[columns_to_keep]
            
            merged_master_df.to_csv(output_csv, index=False)
            print(f"Master summary successfully consolidated.")

    if total_rows == 0:
        print("All treatments are already completed. Rebuilding master summary CSV...")
        consolidate_summary()
        return

    if batch_size is None:
        batch_size = total_rows

    console_stdout = sys.stdout
    stdout_router = ThreadLogRouter()
    sys.stdout = stdout_router
    progress_lock = threading.Lock()
    progress_bar = tqdm(total=total_rows, desc="Simulating Treatments", file=console_stdout)
    
    batches = [master_df.iloc[i:i + batch_size] for i in range(0, total_rows, batch_size)]
    archive_threads = []
    
    try:
        for batch_idx, batch_df in enumerate(batches, start=batch_offset + 1):
            rows = [row for _, row in batch_df.iterrows()]
            worker_chunks = [rows[worker_id::max_workers] for worker_id in range(max_workers)]
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(
                        run_worker, worker_id + 1, chunk, pad_width, stdout_router, 
                        progress_bar, progress_lock, worker_pad, log_dir, sim_dir, 
                        wth_folder, treatments, stations, soils, crops, 
                        fert_material, sdate_buffer, xlsx_path, sheet_name
                    )
                    for worker_id, chunk in enumerate(worker_chunks) if chunk
                ]
                for future in as_completed(futures):
                    _ = future.result()
            
            batch_dfs = []
            failed_list = []
            # Isolate temporary directories per batch to prevent async I/O race conditions
            success_temp = os.path.join(sim_dir, f"Success_Temp_{batch_idx:04d}")
            error_temp = os.path.join(sim_dir, f"Error_Temp_{batch_idx:04d}")
            os.makedirs(success_temp, exist_ok=True)
            os.makedirs(error_temp, exist_ok=True)
            
            for row in rows:
                trt_num = int(row['treatment'])
                run_label = f"T_{trt_num:0{pad_width}d}"
                sim_folder = os.path.join(sim_dir, run_label)
                
                if not os.path.exists(sim_folder):
                    continue
                    
                summary_file = os.path.join(sim_folder, summary_filename)
                is_success = False
                
                if os.path.exists(summary_file):
                    df = parse_summary_out(summary_file)
                    is_complete = False
                    
                    if df is not None:
                        expected_nyears = int(row['NYEARS'])
                        
                        # Primary: Row-count validation
                        if len(df) >= expected_nyears:
                            is_complete = True
                        elif not df.empty:
                            # Secondary: Timestamp-based validation accommodating late-season overflow
                            start_year = parse_planting_date(row['planting_date']).year
                            expected_final_year = str(start_year + expected_nyears - 1)
                            expected_overflow_year = str(start_year + expected_nyears)
                            
                            # Scan the last row for the expected final year or the overflow year string
                            last_row_str = " ".join(df.iloc[-1].astype(str))
                            if (expected_final_year in last_row_str) or (expected_overflow_year in last_row_str):
                                is_complete = True

                        if is_complete:
                            cultivar_name = cultivar_map.get(trt_num, "UNKNOWN")
                            df.insert(0, "Treatment", trt_num)
                            df.insert(1, "cultivar", cultivar_name)
                            
                            wsta_col = next((col for col in df.columns if "WSTA" in col.upper()), None)
                            if wsta_col is not None:
                                gcodes = df[wsta_col].astype(str).str[:4]
                                
                                # Create a mapping from the 4-character prefix to coordinates
                                lat_map = {k[:4]: float(v["lat"]) for k, v in stations.items()}
                                lon_map = {k[:4]: float(v["long"]) for k, v in stations.items()}
                                
                                df.insert(2, "GCODE", gcodes)
                                df.insert(3, "Latitude", gcodes.map(lambda g: lat_map.get(g)))
                                df.insert(4, "Longitude", gcodes.map(lambda g: lon_map.get(g)))
                            else:
                                df.insert(2, "GCODE", None)
                                df.insert(3, "Latitude", None)
                                df.insert(4, "Longitude", None)
                                
                            # Keep all columns for the individual batch files
                            batch_dfs.append(df)
                            is_success = True
                
                if is_success:
                    shutil.move(sim_folder, os.path.join(success_temp, run_label))
                else:
                    failed_list.append(str(trt_num))
                    shutil.move(sim_folder, os.path.join(error_temp, run_label))
            
            if batch_dfs:
                merged_df = pd.concat(batch_dfs, ignore_index=True)
                
                # Save the batch CSV with all columns intact
                batch_csv_path = os.path.join(archive_dir, f"Success_Batch_{batch_idx:04d}.csv")
                merged_df.to_csv(batch_csv_path, index=False)
            
            if failed_list:
                with open(failed_log, "a") as f:
                    for f_trt in failed_list:
                        f.write(f"{f_trt}\n")
            
            if compress:
                def background_archive_and_clean(archive_path, temp_path):
                    if os.path.exists(temp_path) and os.listdir(temp_path):
                        shutil.make_archive(archive_path, 'zip', temp_path)
                    shutil.rmtree(temp_path, ignore_errors=True)

                # Dispatch independent I/O threads and track them for synchronization
                t_success = threading.Thread(
                    target=background_archive_and_clean, 
                    args=(os.path.join(archive_dir, f"Success_Batch_{batch_idx:04d}"), success_temp)
                )
                t_error = threading.Thread(
                    target=background_archive_and_clean, 
                    args=(os.path.join(archive_dir, f"Error_Batch_{batch_idx:04d}"), error_temp)
                )
                t_success.start()
                t_error.start()
                archive_threads.extend([t_success, t_error])
            else:
                # Bypass compression entirely; retain raw folders
                if os.path.exists(success_temp) and os.listdir(success_temp):
                    os.rename(success_temp, os.path.join(archive_dir, f"Success_Batch_{batch_idx:04d}"))
                else:
                    shutil.rmtree(success_temp, ignore_errors=True)
                    
                if os.path.exists(error_temp) and os.listdir(error_temp):
                    os.rename(error_temp, os.path.join(archive_dir, f"Error_Batch_{batch_idx:04d}"))
                else:
                    shutil.rmtree(error_temp, ignore_errors=True)

        # Synchronize: Wait for all background compression threads to finish before CSV aggregation
        for t in archive_threads:
            t.join()

        # Execute the consolidated summary generation
        consolidate_summary()
            
    finally:
        sys.stdout = console_stdout
        progress_bar.close()

def add_cultivar(cultivar_dict, crop_name):
    # Fetch crop class dynamically
    crop_class = getattr(crop, crop_name)
    updated_cultivars = {}
    
    # Fetch fallback code directly from native CUL file to bypass instantiation errors
    fallback_code = crop_class.cultivar_list()[0]
    
    for key, params in cultivar_dict.items():
        # 1. ALWAYS instantiate with the native fallback code so it doesn't crash
        crop_obj = crop_class(fallback_code)
        
        # 2. Overwrite the internal cultivar code with the user-defined code
        user_code = params.get("code", fallback_code)
        if hasattr(crop_obj, "_Crop__cultivar"):
            crop_obj._Crop__cultivar._code = user_code
        
        # 3. Enforce default ecotype
        eco_val = params.get("eco#", params.get("ECO#", "DFAULT"))
        if hasattr(crop_obj['eco#'], '_code'):
            crop_obj['eco#']._code = eco_val
        else:
            crop_obj['eco#'] = eco_val
            
        # 4. Dynamically map parameters, skipping initialization keys
        for param_key, param_value in params.items():
            param_lower = param_key.lower()
            if param_lower not in ["code", "eco#"]:
                crop_obj[param_lower] = param_value
                
        updated_cultivars[key] = crop_obj
        
    return updated_cultivars