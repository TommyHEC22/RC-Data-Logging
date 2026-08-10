def convert_file_to_csv(filepath):



    import struct
    import numpy as np
    import pandas as pd
    import sys
    import os



    # ── paths ──────────────────────────────────────────────────────────────────────
    INPUT_FILE  = filepath
    OUTPUT_FILE = os.path.splitext(filepath)[0] + '.csv'

    # ── CLF format notes ───────────────────────────────────────────────────────────
    # Header: 16 bytes (magic "TLLOG\0" + version + padding)
    # Records: 8 bytes each
    #   [0]  0xFE  – record start marker
    #   [1]  TAG   – channel identifier
    #   [2]  0x04  – always 0x04
    #   [3]  0xFE  – secondary marker (NOT part of the value)
    #   [4:8]      – signed little-endian int32 payload
    #
    # The old code read bytes [3:7] for the int32, which included the 0xFE marker
    # byte and shifted everything by one, producing garbage values.  The correct
    # window is bytes [4:8].  No division-by-2 is applied.

    HEADER_SIZE  = 16
    RECORD_SIZE  = 8
    RECORD_DTYPE = np.dtype([
        ('mark0', 'u1'), ('tag', 'u1'), ('mark1', 'u1'), ('mark2', 'u1'),
        ('val',   '<i4'),
    ])

    # ── channel map ────────────────────────────────────────────────────────────────
    # tag -> (column_name, scale_factor)
    # Scaled value = raw_int32 * scale_factor
    # Special cases handled separately: duty cycles, raw wheel speeds, date/time.
    TAG_MAP = {
        0x02: ('Laptrig status',            1.0      ),  # integer 0/1
        0x03: ('Laptrig width',             1/128.0  ),  # seconds
        0x04: ('Laptrig period',            1/128.0  ),  # seconds
        0x05: ('Speed all',                 1/100.0  ),  # km/h
        0x06: ('Distance',                  1/100.0  ),  # m (cumulative)
        0x0B: ('Speed motor',               1/10.0   ),  # km/h
        0x0C: ('Speed RL',                  1/10.0   ),  # km/h
        0x0D: ('Speed RR',                  1/10.0   ),  # km/h
        0x10: ('RPM',                       1.0      ),  # integer
        0x1B: ('Temp sensor',               1/10.0   ),  # °C
        0x1F: ('Steering',                  1/10.0   ),  # µs (servo pulse width)
        0x20: ('Throttle and brake',        1/10.0   ),  # µs
        0x21: ('Beacon',                    1.0      ),  # integer
        0x22: ('Steering width',            1/128.0  ),
        0x23: ('Throttle and brake width',  1/128.0  ),
        0x29: ('Acceleration X',            1/1000.0 ),  # g
        0x2A: ('Acceleration Y',            1/1000.0 ),  # g
        0x2B: ('Acceleration Z',            1/1000.0 ),  # g
        0x33: ('Gyro Roll',                 1/10.0   ),  # deg/s
        0x34: ('Gyro Pitch',                1/10.0   ),  # deg/s
        0x35: ('Gyro Yaw',                  1/10.0   ),  # deg/s
        # Raw wheel-speed counts: 999999 means sensor absent (kept as-is)
        0x6F: ('Speed motor raw value',     1.0      ),
        0x70: ('Speed RL raw value',        1.0      ),
        0x71: ('Speed RR raw value',        1.0      ),
        # Duty cycles: 99999 raw = no signal -> displayed as 999.99
        0xA1: ('Speed motor duty cycle',    1/1000.0 ),  # %
        0xA2: ('Speed RL duty cycle',       1/1000.0 ),  # %
        0xA3: ('Speed RR duty cycle',       1/1000.0 ),  # %
    }

    DUTY_TAGS      = {0xA1, 0xA2, 0xA3}
    DUTY_INVALID   = 99999      # raw value meaning "no signal"
    DUTY_SENTINEL  = 999.99     # value written to CSV when invalid

    # Channels that should default to 0 when never seen in a file
    # (rather than staying NaN, which is confusing for integer status fields)
    ZERO_DEFAULT_COLS = {
        'Laptrig status', 'Laptrig width', 'Laptrig period', 'Beacon',
    }

    # ── lap detection constants ────────────────────────────────────────────────────
    # The Laptrig system works as follows:
    #
    #   - There can be multiple physical loop detectors on track (main line + sectors).
    #   - Each detector is identified by the MEDIAN transponder period recorded during
    #     the pulse. The transponder fires at a fixed blink rate per loop frequency.
    #     In practice two clusters are seen: ~0.586s (main) and ~1.047s (sector).
    #     These map to different AMB/MyLaps loop frequencies.
    #
    #   - Each detector can double-fire within ~100ms (bounce). We debounce within
    #     500ms per sensor type.
    #
    #   - The LAP TIMER increments only when the MAIN line detector fires (not sectors).
    #     A 'sector' crossing is any pulse cluster whose inter-loop gap to the previous
    #     main crossing is < MIN_LAP_MS (i.e. it can't be a full lap on its own).
    #
    #   - If only one detector is present all pulses are treated as main line.
    #
    # Minimum plausible lap time. Any gap shorter than this between same-type pulses
    # is treated as a double-fire / bounce and debounced away.
    LAP_DEBOUNCE_MS = 500

    # Minimum gap between two successive main-line crossings to count as a real lap.
    # Shorter gaps mean the pulse belongs to a sector loop, not the main line.
    MIN_LAP_MS = 5_000   # 5 seconds – shorter than any real RC lap


    # ── output column order (matches official TestLogger export) ───────────────────
    COLUMN_ORDER = [
        'Timestamp',
        'Lap',
        'Laptrig status', 'Laptrig width', 'Laptrig period',
        'Speed all', 'Distance',
        'Date and time',
        'Speed motor', 'Speed RL', 'Speed RR',
        'RPM',
        'Temp sensor',
        'Steering', 'Throttle and brake',
        'Steering width', 'Throttle and brake width',
        'Acceleration X', 'Acceleration Y', 'Acceleration Z',
        'Gyro Roll', 'Gyro Pitch', 'Gyro Yaw',
        'Beacon',
        'Speed motor raw value', 'Speed RL raw value', 'Speed RR raw value',
        'Speed motor duty cycle', 'Speed RL duty cycle', 'Speed RR duty cycle',
    ]


    def _extract_pulses(records) -> list:
        """
        Walk the raw record array and return a list of complete Laptrig pulses.
        Each pulse: dict with ts_start, ts_end, duration_ms, med_period_s.
        The median transponder period is used to fingerprint which physical loop fired.
        """
        tags = records['tag'].astype(np.uint8)
        vals = records['val'].astype(np.int32)

        pulses = []
        last_ts    = 0
        in_pulse   = False
        pulse_start = 0
        periods    = []

        for t, v in zip(tags, vals):
            t, v = int(t), int(v)
            if t == 0x01:
                last_ts = v
            elif t == 0x02:
                if v == 1 and not in_pulse:
                    in_pulse    = True
                    pulse_start = last_ts
                    periods     = []
                elif v == 0 and in_pulse:
                    in_pulse = False
                    med_p = round(sorted(periods)[len(periods) // 2] / 128.0, 4) if periods else 0.0
                    pulses.append({
                        'ts':       pulse_start,
                        'ts_end':   last_ts,
                        'dur_ms':   last_ts - pulse_start,
                        'med_p_s':  med_p,
                    })
            elif t == 0x04 and in_pulse:
                periods.append(v)

        return pulses


    def _identify_main_crossings(pulses: list) -> list:
        """
        Given the full pulse list, return timestamps (ms) of MAIN LINE crossings only.

        Strategy
        --------
        1. Discard very short pulses that are clearly electrical noise (dur < 4 ms).
        2. Cluster pulses by their median transponder period. The cluster whose
        representative period is lowest (or, if only one cluster, all pulses)
        is treated as the main line.  Sectors have a distinctly higher period.
        3. Within each cluster apply LAP_DEBOUNCE_MS so double-fires merge.
        4. Re-classify any 'main' crossing that occurs < MIN_LAP_MS after the
        previous accepted main crossing as a sector (it must belong to a second
        physical loop sitting close to the main line).
        """
        # Step 1 – drop pure noise
        meaningful = [p for p in pulses if p['dur_ms'] >= 4]
        if not meaningful:
            return []

        # Step 2 – cluster by median transponder period
        # Use a simple gap: if a pulse's med_p_s differs from the smallest seen by > 30%
        # it belongs to a different sensor.
        periods = sorted(set(round(p['med_p_s'], 2) for p in meaningful if p['med_p_s'] > 0))
        if len(periods) >= 2:
            main_period = periods[0]   # shortest transponder period = main line
            # Tolerance: anything within 20% of main_period is "main"
            main_tol = main_period * 1.20
            main_pulses   = [p for p in meaningful if p['med_p_s'] <= main_tol or p['med_p_s'] == 0.0]
            # If filtering removes almost everything, fall back to using all pulses
            if len(main_pulses) < 2:
                main_pulses = meaningful
        else:
            main_pulses = meaningful

        # Step 3 – debounce within main cluster
        debounced = []
        last_accepted = -LAP_DEBOUNCE_MS - 1
        for p in sorted(main_pulses, key=lambda x: x['ts']):
            if p['ts'] - last_accepted > LAP_DEBOUNCE_MS:
                debounced.append(p['ts'])
                last_accepted = p['ts']

        # Step 4 – drop any crossing that is too close to the previous one
        # (these are sector loops sitting just past the main line)
        main_crossings = []
        for ts in debounced:
            if not main_crossings or (ts - main_crossings[-1]) >= MIN_LAP_MS:
                main_crossings.append(ts)

        return main_crossings


    def _add_lap_number(df: pd.DataFrame, records) -> pd.DataFrame:
        """
        Add a Lap column derived from the raw CLF records.

        Lap 0  = out-lap (before first main-line crossing).
        Lap 1+ = each subsequent main-line crossing increments the lap counter.

        The lap increments at the FIRST timestamp row that meets or exceeds the
        crossing timestamp, so the row where the car crosses the line is the first
        row of the new lap.
        """
        main_crossings = _identify_main_crossings(_extract_pulses(records))

        timestamps = df['Timestamp'].to_numpy()
        lap_col    = np.zeros(len(timestamps), dtype=np.int64)
        lap_number = 0
        cross_idx  = 0

        for i, ts in enumerate(timestamps):
            while cross_idx < len(main_crossings) and ts >= main_crossings[cross_idx]:
                lap_number += 1
                cross_idx  += 1
            lap_col[i] = lap_number

        df.insert(1, 'Lap', lap_col)

        return df


    def parse_clf(filepath: str) -> pd.DataFrame:
        #print(f"Reading {filepath} ...")
        with open(filepath, 'rb') as f:
            raw_bytes = f.read()

        total_bytes = len(raw_bytes)
        payload_bytes = total_bytes - HEADER_SIZE
        n_records = payload_bytes // RECORD_SIZE

        #print(f"  File size : {total_bytes:,} bytes")
        #print(f"  Records   : {n_records:,}")

        # Parse all records in one vectorised pass
        records = np.frombuffer(
            raw_bytes, dtype=RECORD_DTYPE,
            count=n_records, offset=HEADER_SIZE,
        )
        tags = records['tag'].astype(np.uint8)
        vals = records['val'].astype(np.int32)     # correct signed int32 payload

        # ── build rows ─────────────────────────────────────────────────────────────
        # State dictionary carries the last-seen value for every channel.
        # Channels in ZERO_DEFAULT_COLS start at 0 so they are never NaN in the output
        # even if the tag never appears in this particular file.
        #
        # A row is only emitted when at least one sensor value has changed since the
        # last emitted row. This collapses duplicate rows that appear when the logger
        # timestamps faster than the sensors update (e.g. 500 Hz timestamps but
        # 100 Hz sensor data produces 5 identical rows which collapse to 1).
        all_col_names = [info[0] for info in TAG_MAP.values()]
        state: dict = {
            name: (0 if name in ZERO_DEFAULT_COLS else None)
            for name in all_col_names
        }
        date_time_val  = None
        pending_ts     = None
        last_emitted   = None   # snapshot of state at the last emitted row
        rows           = []

        #print("Parsing records ...")
        for tag, val in zip(tags, vals):
            tag = int(tag)
            val = int(val)

            if tag == 0x01:
                # Emit a row only if sensor state changed since the last emit
                if pending_ts is not None and state != last_emitted:
                    row = {'Timestamp': pending_ts, 'Date and time': date_time_val}
                    row.update(state)
                    rows.append(row)
                    last_emitted = state.copy()
                pending_ts = val

            elif tag == 0x07:
                # Unix epoch (date + time)
                date_time_val = val

            elif tag in TAG_MAP:
                col_name, scale = TAG_MAP[tag]

                if tag in DUTY_TAGS:
                    state[col_name] = DUTY_SENTINEL if val == DUTY_INVALID else round(val * scale, 3)
                else:
                    state[col_name] = round(val * scale, 6) if scale != 1.0 else val

        # Flush final pending row if it differs from the last emitted
        if pending_ts is not None and state != last_emitted:
            row = {'Timestamp': pending_ts, 'Date and time': date_time_val}
            row.update(state)
            rows.append(row)

        #print(f"  Output rows: {len(rows):,}")

        df = pd.DataFrame(rows)

        # Derive lap number from raw records (needs pulse-level data, not row-level)
        df = _add_lap_number(df, records)

        # Apply column order, keeping only columns that actually exist
        ordered = [c for c in COLUMN_ORDER if c in df.columns]
        df = df[ordered]

        return df


    def main():
        in_file  = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE
        out_file = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_FILE

        if not os.path.isfile(in_file):
            #print(f"ERROR: input file not found: {in_file}")
            sys.exit(1)

        df = parse_clf(in_file)
        df.to_csv(out_file, index=False)
        #print(f"\nSaved → {out_file}")
        #print(f"Rows: {len(df):,}   Columns: {len(df.columns)}")
        #print()
        #print(df.head(3).to_string())

    main()

    return OUTPUT_FILE