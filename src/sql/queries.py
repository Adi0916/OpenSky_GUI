import logging
from sql.database import connect_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

#1: Najnowsze pozycje samolotów

def get_live_radar_data(country_name=None, continent_name=None, on_ground=None):

    query = '''
        SELECT
            a.icao24,
            a.callsign,
            c.country_name,
            ct.continent_name,
            l.latitude,
            l.longitude,
            l.baro_altitude,
            l.velocity,
            l.on_ground,
            l.time_pos
        FROM aircraft a
        JOIN location l ON a.icao24 = l.aircraft_id
        LEFT JOIN country c ON a.country_id = c.country_id
        LEFT JOIN continent ct ON c.continent_id = ct.continent_id
        INNER JOIN (
            -- Podzapytanie wyciągające tylko najświeższy timestamp dla każdego samolotu
            SELECT aircraft_id, MAX(time_pos) as max_time
            FROM location
            GROUP BY aircraft_id
        ) latest ON l.aircraft_id = latest.aircraft_id AND l.time_pos = latest.max_time
        WHERE l.latitude IS NOT NULL AND l.longitude IS NOT NULL
    '''
    params = []

    if country_name:
        query += " AND c.country_name = ?"
        params.append(country_name)
    if continent_name:
        query += " AND ct.continent_name = ?"
        params.append(continent_name)
    if on_ground is not None:
        query += " AND l.on_ground = ?"
        params.append(1 if on_ground else 0)

    with connect_db() as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchall()


#2: Statystyki ruchu na lotniskach

def get_airport_traffic_stats(airport_code=None, date_from=None, date_to=None):

    query = '''
        SELECT
            id_lotniska,
            COUNT(DISTINCT wylot_id) as liczba_wylotów,
            COUNT(DISTINCT przylot_id) as liczba_przylotów,
            (COUNT(DISTINCT wylot_id) + COUNT(DISTINCT przylot_id)) as całkowity_ruch
        FROM (
            SELECT departure_airport_id as id_lotniska, flight_id as wylot_id, NULL as przylot_id, departure_date_time as dt FROM flight_data
            UNION ALL
            SELECT arrival_airport_id as id_lotniska, NULL as wylot_id, flight_id as przylot_id, arrival_date_time as dt FROM flight_data
        )
        WHERE id_lotniska IS NOT NULL
    '''
    params = []

    if airport_code:
        query += " AND id_lotniska = ?"
        params.append(airport_code)
    if date_from:
        query += " AND dt >= ?"
        params.append(date_from)
    if date_to:
        query += " AND dt <= ?"
        params.append(date_to)

    query += " GROUP BY id_lotniska ORDER BY całkowity_ruch DESC"

    with connect_db() as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchall()


#3: Historia trasy konkretnego samolotu

def get_aircraft_trajectory(icao24, time_from=None):

    query = '''
        SELECT latitude, longitude, baro_altitude, velocity, time_pos
        FROM location
        WHERE aircraft_id = ?
    '''
    params = [icao24]

    if time_from:
        query += " AND time_pos >= ?"
        params.append(time_from)

    query += " ORDER BY time_pos ASC"

    with connect_db() as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchall()


#4: Udział procentowy kontynentów lub kategorii w globalnym ruchu

def get_continent_distribution_stats(exclude_list=None):
    if exclude_list is None:
        exclude_list = []

    # Tworzymy placeholder dla każdego elementu w liście (np. ?, ?, ?)
    placeholders = ', '.join(['?'] * len(exclude_list))

    query = '''
        SELECT
            COALESCE(ct.continent_name, 'Unknown') as continent,
            COUNT(a.icao24) as aircraft_count
        FROM aircraft a
        LEFT JOIN country c ON a.country_id = c.country_id
        LEFT JOIN continent ct ON c.continent_id = ct.continent_id
    '''

    # Jeśli są kontynenty do wykluczenia, dodajemy warunek WHERE
    if exclude_list:
        query += f" WHERE COALESCE(ct.continent_name, 'Unknown') NOT IN ({placeholders})"

    query += " GROUP BY continent ORDER BY aircraft_count DESC"

    with connect_db() as conn:
        cursor = conn.execute(query, exclude_list)
        return cursor.fetchall()

# Pobranie nazw kontynentów do filtrowania

def get_continent_names():
    query = '''
        SELECT
            DISTINCT(continent_name)
        FROM continent
        ORDER BY continent_name
    '''
    with connect_db() as conn:
        cursor = conn.execute(query)
        return cursor.fetchall()


#5: Raport techniczny

def get_system_health_report(status_filter=None):

    query = '''
        SELECT log_id, imported_at, records_received, records_saved, status, error_message
        FROM import_log
        WHERE 1=1
    '''
    params = []

    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)

    query += " ORDER BY log_id DESC LIMIT 50"

    with connect_db() as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchall()

#6: Trasy lotów do wyświetlenia na mapie (wylot -> przylot z koordynatami)

def get_flights_for_map(
    dt_from=None,
    dt_to=None,
    airport_code=None,
    skip_same_location=None,
):
    query = '''
        SELECT
            COALESCE(ac.callsign, f.aircraft_id) AS callsign,
            f.departure_airport_id AS from_code,
            f.arrival_airport_id AS to_code,
            dep.latitude AS from_lat,
            dep.longitude AS from_lon,
            arr.latitude AS to_lat,
            arr.longitude AS to_lon,
            f.departure_date_time AS dep_time
        FROM flight_data f
        JOIN airport dep ON f.departure_airport_id = dep.icao_code
        JOIN airport arr ON f.arrival_airport_id = arr.icao_code
        LEFT JOIN aircraft ac ON f.aircraft_id = ac.icao24
        WHERE dep.latitude IS NOT NULL
          AND dep.longitude IS NOT NULL
          AND arr.latitude IS NOT NULL
          AND arr.longitude IS NOT NULL
    '''
    params = []

    if skip_same_location:
        query += '''
          AND f.departure_airport_id != f.arrival_airport_id
          AND NOT (dep.latitude = arr.latitude AND dep.longitude = arr.longitude)
        '''

    # W etl.py daty zapisywane są jako ISO (np. '2026-11-19T15:10:00+00:00'),
    # więc ujednolicenie 'T' na spację ułatwia porównanie z 'YYYY-MM-DD HH:MM:SS'
    if dt_from:
        query += " AND REPLACE(f.departure_date_time, 'T', ' ') >= ?"
        params.append(dt_from)
    if dt_to:
        query += " AND REPLACE(f.departure_date_time, 'T', ' ') <= ?"
        params.append(dt_to)
    if airport_code:
        query += " AND (f.departure_airport_id = ? OR f.arrival_airport_id = ?)"
        params.append(airport_code)

    query += " ORDER BY f.departure_date_time DESC LIMIT 300"

    with connect_db() as conn:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

    return [
        {
            "callsign": r[0],
            "from_code": r[1],
            "to_code": r[2],
            "from_lat": r[3],
            "from_lon": r[4],
            "to_lat": r[5],
            "to_lon": r[6],
            "time": r[7],
        }
        for r in rows
    ]