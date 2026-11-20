import pandas as pd
from sql.queries import get_system_health_report
from gui.base import VisualizationWindow


def update_health(canvas, f):
    data = get_system_health_report(f.get('status'))
    canvas.axes.cla()

    if not data:
        canvas.axes.text(0.5, 0.5, 'No health data available', ha='center', va='center')
        canvas.draw()
        return

    df = pd.DataFrame(data, columns=['id', 'date', 'recv', 'saved', 'status', 'err'])
    df = df.sort_values(by='id', ascending=True).tail(15)

    time_labels = [str(d).split('T')[1][:8] for d in df['date']]
    max_recv = df['recv'].max() if df['recv'].max() > 0 else 100

    bars = canvas.axes.barh(range(len(df)), df['recv'], color='#4a90e2', alpha=0.7)

    canvas.figure.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.15)
    canvas.axes.set_yticks(range(len(df)))
    canvas.axes.set_yticklabels(time_labels, fontsize=8)
    canvas.axes.set_xlim(0, max_recv * 1.05)

    for i, bar in enumerate(bars):
        status = df.iloc[i]['status']
        canvas.axes.text(max_recv * 0.02, i, status,
                         va='center', fontsize=7, fontweight='bold', color='black')

    canvas.axes.set_title("Recent Activity", fontsize=12, fontweight='bold')
    canvas.axes.set_xlabel("Records Received")
    canvas.draw()


class HealthWindow(VisualizationWindow):
    def __init__(self, parent=None):
        super().__init__(
            title="System health report",
            update_func=update_health,
            filter_map={"Status": "status"},
            defaults={"status": ""},
            parent=parent
        )

