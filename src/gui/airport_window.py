import pandas as pd
from sql.queries import get_airport_traffic_stats
from gui.base import VisualizationWindow


def update_traffic(canvas, f):
    airport = f.get('airport') or None
    d_from = f.get('date_from') or None
    d_to = f.get('date_to') or None

    data = get_airport_traffic_stats(airport, d_from, d_to)
    canvas.axes.cla()

    if not data:
        canvas.axes.text(0.5, 0.5, 'No data available', ha='center', va='center', fontsize=12)
        canvas.draw()
        return

    df = pd.DataFrame(data, columns=['id', 'wylot', 'przylot', 'ruch'])
    df_sorted = df.sort_values(by='ruch', ascending=False)
    df_top = df_sorted.head(20).sort_values(by='ruch', ascending=True)

    bars = canvas.axes.barh(df_top['id'], df_top['ruch'], color='#2ca02c', alpha=0.7)

    num_items = len(df_top)
    if num_items >= 20:
        canvas.axes.set_title("Top 20 Most Active Airports", fontsize=12, fontweight='bold')
    else:
        canvas.axes.set_title(f"Activity of all {num_items} Airports", fontsize=12, fontweight='bold')

    canvas.axes.set_xlabel("Number of Operations")
    canvas.axes.set_ylabel("Airport Code")
    canvas.axes.grid(axis='x', linestyle='--', alpha=0.5)

    for bar in bars:
        width = bar.get_width()
        canvas.axes.text(width + 0.1, bar.get_y() + bar.get_height() / 2,
                         f'{int(width)}', ha='left', va='center', fontsize=9)

    canvas.figure.tight_layout()
    canvas.draw()


class AirportWindow(VisualizationWindow):
    def __init__(self, parent=None):
        super().__init__(
            title="Airport traffic",
            update_func=update_traffic,
            filter_map={"Airport": "airport", "From": "date_from", "To": "date_to"},
            defaults={"airport": "", "date_from": "2026-01-01", "date_to": "2030-01-01"},
            parent=parent
        )
