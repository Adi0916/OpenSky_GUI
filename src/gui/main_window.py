import json
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QFrame, QDateEdit, QTimeEdit,
    QLineEdit, QSizePolicy
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtWebEngineWidgets import QWebEngineView

from gui.airport_window import AirportWindow
from gui.continents_window import ContinentsWindow
from gui.health_window import HealthWindow

from sql.queries import get_flights_for_map

MAP_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<title>Flights Map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html, body, #map { height: 100%; margin: 0; padding: 0; background: #1e2229; }
  .pin-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .pin-dot {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    border: 2.5px solid #ffffff;
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.75);
  }
  .arrow-icon {
    font-size: 18px;
    font-weight: bold;
    text-shadow: 0 0 3px #ffffff, 0 0 6px #ffffff;
  }
</style>
</head>
<body>
<div id="map"></div>
<script>
  const map = L.map('map', { worldCopyJump: true }).setView([25, 10], 2);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '© OpenStreetMap'
  }).addTo(map);

  const flightLayer = L.layerGroup().addTo(map);

  // Paleta dobrze rozróżnialnych kolorów (niebieski, zielony i kolejne)
  const ROUTE_COLORS = [
    '#1e88e5', // niebieski
    '#2e7d32', // zielony
    '#e53935', // czerwony
    '#8e24aa', // fioletowy
    '#fb8c00', // pomarańczowy
    '#00897b', // morski / turkusowy
    '#3949ab', // indygo
    '#c0ca33', // limonkowy
    '#d81b60', // różowy
    '#6d4c41', // brązowy
    '#039be5', // jasny niebieski
    '#43a047'  // jasny zielony
  ];

  // Krok względnie pierwszy z długością palety (12 -> 5), żeby sąsiednie indeksy
  // przeskakiwały daleko po palecie i nie powtarzały się szybko
  function pickColor(index, prevColor) {
    let color = ROUTE_COLORS[(index * 5) % ROUTE_COLORS.length];
    if (color === prevColor) {
      color = ROUTE_COLORS[(index * 5 + 1) % ROUTE_COLORS.length];
    }
    return color;
  }

  function createPinIcon(color) {
    return L.divIcon({
      className: 'pin-wrapper',
      html: `<div class="pin-dot" style="background-color: ${color};"></div>`,
      iconSize: [18, 18],
      iconAnchor: [9, 9]
    });
  }

  function bearingDeg(lat1, lon1, lat2, lon2) {
    const toRad = d => d * Math.PI / 180;
    const toDeg = r => r * 180 / Math.PI;
    const dLon = toRad(lon2 - lon1);
    const y = Math.sin(dLon) * Math.cos(toRad(lat2));
    const x = Math.cos(toRad(lat1)) * Math.sin(toRad(lat2)) -
              Math.sin(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.cos(dLon);
    return (toDeg(Math.atan2(y, x)) + 360) % 360;
  }

  // Kąt w pikselach na aktualnym widoku mapy (0° = w prawo, zgodnie z ruchem wskazówek zegara)
  function screenAngleDeg(lat1, lon1, lat2, lon2) {
    const pt1 = map.latLngToLayerPoint([lat1, lon1]);
    const pt2 = map.latLngToLayerPoint([lat2, lon2]);
    const dx = pt2.x - pt1.x;
    const dy = pt2.y - pt1.y;
    return Math.atan2(dy, dx) * (180 / Math.PI);
  }

  function renderFlights(flights) {
    flightLayer.clearLayers();
    let prevColor = null;

    flights.forEach((f, idx) => {
      const fromLat = Number(f.from_lat);
      const fromLon = Number(f.from_lon);
      const toLat = Number(f.to_lat);
      const toLon = Number(f.to_lon);

      if ([fromLat, fromLon, toLat, toLon].some(Number.isNaN)) {
        return;
      }

      const color = pickColor(idx, prevColor);
      prevColor = color;

      const p1 = [fromLat, fromLon];
      const p2 = [toLat, toLon];
      const popupHtml = `<b>${f.callsign || 'Flight'}</b><br>${f.from_code || '?'} → ${f.to_code || '?'}<br><small>${f.time || ''}</small>`;

      // 1. Linia przerywana łącząca pinezki z pobranych współrzędnych
      const dashedLine = L.polyline([p1, p2], {
        color: color,
        weight: 2.5,
        opacity: 0.9,
        dashArray: '8, 8'
      }).addTo(flightLayer);
      dashedLine.bindPopup(popupHtml);

      // 2. Pinezki wylotu i przylotu
      const pinIcon = createPinIcon(color);
      L.marker(p1, { icon: pinIcon })
        .bindPopup(`<b>Wylot: ${f.from_code || '?'}</b><br>${popupHtml}`)
        .addTo(flightLayer);

      L.marker(p2, { icon: pinIcon })
        .bindPopup(`<b>Przylot: ${f.to_code || '?'}</b><br>${popupHtml}`)
        .addTo(flightLayer);

      // 3. Strzałka w połowie trasy wyliczona z pobranych współrzędnych (p1 -> p2)
      const midLat = (fromLat + toLat) / 2;
      const midLon = (fromLon + toLon) / 2;
      const angle = screenAngleDeg(fromLat, fromLon, toLat, toLon);

      const arrowIcon = L.divIcon({
        className: '',
        html: `<div class="arrow-icon" style="color: ${color}; transform: rotate(${angle}deg); line-height: 20px; text-align: center;">➤</div>`,
        iconSize: [20, 20],
        iconAnchor: [10, 10]
      });

      L.marker([midLat, midLon], { icon: arrowIcon, interactive: false }).addTo(flightLayer);
    });
  }

</script>
</body>
</html>
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flight Analytics - Main Menu")
        self.resize(1280, 760)
        self.windows = {}

        self._setup_menu_bar()
        self._setup_ui()

    def _setup_menu_bar(self):
        menu_bar = self.menuBar()

        reports_menu = menu_bar.addMenu("&Reports")

        airport_action = QAction("Airport Traffic", self)
        airport_action.triggered.connect(lambda: self.open_window("airport", AirportWindow))
        reports_menu.addAction(airport_action)

        continents_action = QAction("Continent Distribution", self)
        continents_action.triggered.connect(lambda: self.open_window("continents", ContinentsWindow))
        reports_menu.addAction(continents_action)

        health_action = QAction("System Health Report", self)
        health_action.triggered.connect(lambda: self.open_window("health", HealthWindow))
        reports_menu.addAction(health_action)

        file_menu = menu_bar.addMenu("&File")
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Mapa po lewej / środku
        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.web_view.setHtml(MAP_HTML)
        # Po załadowaniu strony z mapą od razu pobierz dane z bazy dla domyślnych filtrów
        self.web_view.loadFinished.connect(lambda ok: self.apply_flight_filters() if ok else None)
        root_layout.addWidget(self.web_view, stretch=1)

        # 2. Prawy panel: przyciski raportów + rozwijane ustawienia filtrów lotów
        right_panel = QFrame()
        right_panel.setFixedWidth(290)
        right_panel.setStyleSheet("background-color: #2b2f36; color: #f0f0f0;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        btn_airport = QPushButton("✈  Airport Traffic")
        btn_airport.setMinimumHeight(38)
        btn_airport.clicked.connect(lambda: self.open_window("airport", AirportWindow))
        right_layout.addWidget(btn_airport)

        btn_continents = QPushButton("🌍  Continent Distribution")
        btn_continents.setMinimumHeight(38)
        btn_continents.clicked.connect(lambda: self.open_window("continents", ContinentsWindow))
        right_layout.addWidget(btn_continents)

        btn_health = QPushButton("🩺  System Health Report")
        btn_health.setMinimumHeight(38)
        btn_health.clicked.connect(lambda: self.open_window("health", HealthWindow))
        right_layout.addWidget(btn_health)

        # Przycisk otwierający/zamykający ustawienia filtrów po prawej stronie
        self.btn_toggle_filters = QPushButton("⚙  Flight Filters")
        self.btn_toggle_filters.setCheckable(True)
        self.btn_toggle_filters.setChecked(True)
        self.btn_toggle_filters.setMinimumHeight(38)
        self.btn_toggle_filters.clicked.connect(self._toggle_filter_drawer)
        right_layout.addWidget(self.btn_toggle_filters)

        # Panel filtrów (dzień, godzina od-do, opcjonalny kod lotniska)
        self.filter_box = QFrame()
        self.filter_box.setStyleSheet("""
            QFrame { background-color: #353a42; border-radius: 6px; padding: 6px; }
            QLineEdit, QDateEdit, QTimeEdit {
                background-color: #1f2328; color: white; border: 1px solid #555; padding: 4px;
            }
            QPushButton { background-color: #3b82f6; color: white; padding: 6px; border-radius: 4px; }
        """)
        filter_layout = QVBoxLayout(self.filter_box)
        filter_layout.setSpacing(8)

        filter_layout.addWidget(QLabel("Flight day:"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate().addDays(-1))  # wczorajszy dzień
        self.date_edit.setDisplayFormat("dd-MM-yyyy")
        filter_layout.addWidget(self.date_edit)

        filter_layout.addWidget(QLabel("Hour from:"))
        self.time_from = QTimeEdit()
        self.time_from.setTime(QTime(15, 0))  # 15:00
        self.time_from.setDisplayFormat("HH:mm")
        filter_layout.addWidget(self.time_from)

        filter_layout.addWidget(QLabel("Hour to:"))
        self.time_to = QTimeEdit()
        self.time_to.setTime(QTime(16, 0))  # 16:00
        self.time_to.setDisplayFormat("HH:mm")
        filter_layout.addWidget(self.time_to)

        filter_layout.addWidget(QLabel("Airport (ICAO, optional):"))
        self.airport_input = QLineEdit()
        self.airport_input.setPlaceholderText("e.g. EPKK, WAW")
        filter_layout.addWidget(self.airport_input)

        btn_apply = QPushButton("Show on map")
        btn_apply.clicked.connect(self.apply_flight_filters)
        filter_layout.addWidget(btn_apply)

        right_layout.addWidget(self.filter_box)
        right_layout.addStretch()

        root_layout.addWidget(right_panel)

    def _toggle_filter_drawer(self, checked: bool):
        self.filter_box.setVisible(checked)

    def apply_flight_filters(self):
            day_str = self.date_edit.date().toString("yyyy-MM-dd")
            t_from = self.time_from.time().toString("HH:mm")
            t_to = self.time_to.time().toString("HH:mm")
            airport = self.airport_input.text().strip().upper() or None

            dt_from = f"{day_str} {t_from}:00"
            dt_to = f"{day_str} {t_to}:59"

            flights = get_flights_for_map(dt_from=dt_from, dt_to=dt_to, airport_code=airport)
            payload = json.dumps(flights)
            self.web_view.page().runJavaScript(f"renderFlights({payload});")

    def open_window(self, key, window_cls):
        if key not in self.windows or self.windows[key] is None:
            self.windows[key] = window_cls()
        win = self.windows[key]
        win.show()
        win.raise_()
        win.activateWindow()

    def closeEvent(self, event):
        for win in self.windows.values():
            if win is not None:
                win.close()
        event.accept()