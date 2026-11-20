from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QLabel)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

from gui.airport_window import AirportWindow
from gui.continents_window import ContinentsWindow
from gui.health_window import HealthWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flight Analytics - Main Menu")
        self.resize(450, 320)

        # Słownik przechowujący otwarte instancje okien (zapobiega ich zamknięciu przez Garbage Collector)
        self.windows = {}

        self._setup_menu_bar()
        self._setup_central_ui()

    def _setup_menu_bar(self):
        menu_bar = self.menuBar()

        # Menu główne: Widoki / Raporty
        reports_menu = menu_bar.addMenu("&Reports")

        airport_action = QAction("Airport Traffic", self)
        airport_action.setShortcut("Ctrl+1")
        airport_action.triggered.connect(lambda: self.open_window("airport", AirportWindow))
        reports_menu.addAction(airport_action)

        continents_action = QAction("Continent Distribution", self)
        continents_action.setShortcut("Ctrl+2")
        continents_action.triggered.connect(lambda: self.open_window("continents", ContinentsWindow))
        reports_menu.addAction(continents_action)

        health_action = QAction("System Health Report", self)
        health_action.setShortcut("Ctrl+3")
        health_action.triggered.connect(lambda: self.open_window("health", HealthWindow))
        reports_menu.addAction(health_action)

        reports_menu.addSeparator()

        open_all_action = QAction("Open All Windows", self)
        open_all_action.setShortcut("Ctrl+Shift+A")
        open_all_action.triggered.connect(self.open_all_windows)
        reports_menu.addAction(open_all_action)

        # Menu: Plik
        file_menu = menu_bar.addMenu("&File")
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _setup_central_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 30, 40, 30)

        header = QLabel("Aviation Data Dashboard")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        btn_airport = QPushButton("✈  Airport Traffic")
        btn_airport.setMinimumHeight(40)
        btn_airport.clicked.connect(lambda: self.open_window("airport", AirportWindow))
        layout.addWidget(btn_airport)

        btn_continents = QPushButton("🌍  Continent Distribution")
        btn_continents.setMinimumHeight(40)
        btn_continents.clicked.connect(lambda: self.open_window("continents", ContinentsWindow))
        layout.addWidget(btn_continents)

        btn_health = QPushButton("🩺  System Health Report")
        btn_health.setMinimumHeight(40)
        btn_health.clicked.connect(lambda: self.open_window("health", HealthWindow))
        layout.addWidget(btn_health)

        layout.addStretch()

    def open_window(self, key, window_cls):
        # Tworzy okno tylko raz przy pierwszym kliknięciu (lazy loading)
        if key not in self.windows or self.windows[key] is None:
            self.windows[key] = window_cls()

        win = self.windows[key]
        win.show()
        win.raise_()
        win.activateWindow()

    def open_all_windows(self):
        self.open_window("airport", AirportWindow)
        self.open_window("continents", ContinentsWindow)
        self.open_window("health", HealthWindow)

    def closeEvent(self, event):
        # Zamknięcie menu głównego zamyka również wszystkie otwarte okna podrzędne
        for win in self.windows.values():
            if win is not None:
                win.close()
        event.accept()
