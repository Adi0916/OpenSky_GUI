import pandas as pd
from sql.queries import get_continent_distribution_stats, get_continent_names
from gui.base import VisualizationWindow


def update_distribution(canvas, f):
    hidden = f.get('hidden_continents', [])
    data = get_continent_distribution_stats(exclude_list=hidden)
    canvas.axes.cla()

    if data:
        df = pd.DataFrame(data, columns=['cont', 'count'])
        canvas.axes.pie(
            df['count'], labels=df['cont'], autopct='%1.1f%%',
            pctdistance=0.8, startangle=140
        )
        canvas.figure.tight_layout()
    else:
        canvas.axes.text(0.5, 0.5, 'No data available', ha='center', va='center')
    canvas.draw()


class ContinentsWindow(VisualizationWindow):
    def __init__(self, parent=None):
        all_continents = [c[0] for c in get_continent_names()]
        super().__init__(
            title="Continent distribution",
            update_func=update_distribution,
            filter_map={},
            checkboxes=all_continents,
            parent=parent
        )
