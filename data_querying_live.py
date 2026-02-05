import json
import time
import requests
import pandas as pd
from shapely.geometry import shape

BOUNDARY_FILE = './data/canary_extent.geojson'
OUTPUT_FILE = './data/flights_data.parquet'
DURATION = 600   # seconds to poll (adjust as needed)
INTERVAL = 10    # seconds between polls


def load_bounds(filename):
    print(f"Loading boundary from {filename}...")
    with open(filename, 'r') as f:
        geo = json.load(f)
    geom = geo['features'][0]['geometry']
    poly = shape(geom)
    minx, miny, maxx, maxy = poly.bounds  # (min lon, min lat, max lon, max lat)
    lamin, lomin, lamax, lomax = miny, minx, maxy, maxx
    print(f"Bounds loaded: lamin={lamin}, lomin={lomin}, lamax={lamax}, lomax={lomax}")
    return lamin, lomin, lamax, lomax  # lamin, lomin, lamax, lomax


def poll_opensky(lamin, lomin, lamax, lomax, duration=DURATION, interval=INTERVAL):
    print(f"Starting OpenSky polling for {duration}s with interval {interval}s...")
    records = []
    url = "https://opensky-network.org/api/states/all"
    # compute number of polls
    n_polls = max(1, int(duration // interval))
    if duration % interval:
        n_polls += 1

    # try to use tqdm if available
    try:
        from tqdm import tqdm
        use_tqdm = False
    except Exception:
        use_tqdm = False

    session = requests.Session()
    error_count = 0

    iterator = range(n_polls)
    if use_tqdm:
        iterator = tqdm(iterator, desc="Polling OpenSky", unit="iter")

    for i in iterator:
        try:
            resp = session.get(
                url,
                params={"lamin": lamin, "lomin": lomin, "lamax": lamax, "lomax": lomax},
                timeout=15,
            )
            resp.raise_for_status()
            j = resp.json()
            # ts = int(time.time())
            ts = pd.to_datetime(time.time(), unit='s')
            n_states = 0
            for s in j.get("states", []):
                callsign = (s[1] or "").strip()
                altitude = s[7] if s[7] is not None else s[13]
                groundspeed = s[9]
                records.append({
                    "timestamp": ts,
                    "icao24": s[0],
                    "callsign": callsign,
                    "lon": s[5],
                    "lat": s[6],
                    "baro_altitude": s[7],
                    "geo_altitude": s[13],
                    "groundspeed": groundspeed,
                })
                # print per-state info
                print(f"Poll {i+1}/{n_polls} state {n_states+1}: callsign='{callsign}', altitude={altitude}, groundspeed={groundspeed}")
                n_states += 1
            if use_tqdm:
                iterator.set_postfix(records=len(records))
            else:
                print(f"Poll {i+1}/{n_polls}: retrieved {n_states} states (total records={len(records)})")
        except Exception as e:
            error_count += 1
            if use_tqdm:
                iterator.set_postfix(error=f"{error_count} errs")
            else:
                print(f"Poll {i+1}/{n_polls} error: {e!r}")
        time.sleep(interval)

    print(f"Finished polling. Total records: {len(records)}. Errors: {error_count}")
    return records


def save_records(records, out_path=OUTPUT_FILE):
    print(f"Saving {len(records)} records to {out_path} ...")
    df = pd.DataFrame.from_records(records)
    if df.empty:
        # write empty placeholder parquet so downstream code can run
        df = pd.DataFrame(columns=['timestamp', 'icao24', 'callsign', 'lon', 'lat',
                                   'baro_altitude', 'geo_altitude', 'groundspeed'])
    try:
        df.to_parquet(out_path, index=False)
        print(f"Saved parquet: {out_path}")
    except Exception as e:
        print(f"Parquet save failed ({e!r}), falling back to CSV.")
        csv_path = out_path.replace('.parquet', '.csv')
        df.to_csv(csv_path, index=False)
        print(f"Saved CSV: {csv_path}")


def main():
    lamin, lomin, lamax, lomax = load_bounds(BOUNDARY_FILE)
    records = poll_opensky(lamin, lomin, lamax, lomax)
    save_records(records)


if __name__ == "__main__":
    main()