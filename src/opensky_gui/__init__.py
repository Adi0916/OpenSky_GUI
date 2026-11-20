import sys
import threading
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from sql.scheduler import start_scheduler


def run_scheduler_in_background():
    try:
        start_scheduler()
    except Exception as e:
        print(f"Scheduler error: {e}")


def main():
    app = QApplication(sys.argv)

    # Uruchomienie schedulera w wątku w tle (daemon=True zamknie go przy wyjściu z programu)
    scheduler_thread = threading.Thread(target=run_scheduler_in_background, daemon=True)
    scheduler_thread.start()

    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()