from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QLineEdit, QPushButton, QLabel, QGridLayout, QCheckBox)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ChartCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure(figsize=(5, 4), dpi=100)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class VisualizationWindow(QMainWindow):
    def __init__(self, title, update_func, filter_map, defaults=None, checkboxes=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 600)
        self.update_func = update_func
        self.filter_map = filter_map
        self.defaults = defaults or {}
        self.checkboxes = {}

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        self.inputs = {}
        grid = QGridLayout()
        for i, (label, param_key) in enumerate(filter_map.items()):
            grid.addWidget(QLabel(label), i // 2, (i % 2) * 2)
            input_box = QLineEdit()
            if param_key in self.defaults:
                input_box.setText(str(self.defaults[param_key]))
            grid.addWidget(input_box, i // 2, (i % 2) * 2 + 1)
            self.inputs[param_key] = input_box
        layout.addLayout(grid)

        if checkboxes:
            cb_layout = QGridLayout()
            for i, cb_name in enumerate(checkboxes):
                cb = QCheckBox(cb_name)
                cb.setChecked(True)
                cb_layout.addWidget(cb, i // 3, i % 3)
                self.checkboxes[cb_name] = cb
            layout.addLayout(cb_layout)

        self.canvas = ChartCanvas()
        layout.addWidget(self.canvas)
        self.canvas.mpl_connect('resize_event', lambda event: self.canvas.draw())

        btn = QPushButton(f"Refresh {title}")
        btn.clicked.connect(self.run_update)
        layout.addWidget(btn)

        self.run_update()

    def run_update(self):
        vals = {k: self.inputs[k].text() if self.inputs[k].text() else None for k in self.inputs}
        vals['hidden_continents'] = [name for name, cb in self.checkboxes.items() if not cb.isChecked()]
        self.update_func(self.canvas, vals)
