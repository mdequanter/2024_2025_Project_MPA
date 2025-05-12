from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import re
from collections import defaultdict
import argparse

# === Configuration ===
parser = argparse.ArgumentParser(description="Parse COOJA test log.")
parser.add_argument("input_path", help="Path to the COOJA log file")
args = parser.parse_args()

logfile = args.input_path
queue = 64
included_nodes = {'26', '6', '16', '25', '3'}
fixed_colors = {
    '3': 'blue',
    '6': 'red',
    '16': 'black',
    '25': 'orange',
    '26': 'brown',
    'received': 'green'
}

app = Dash(__name__)
app.title = "TSCH Queue Fill Selected Nodes"

app.layout = html.Div([
    html.H2(f"TSCH Queue Fill (Nodes 3, 6, 16, 25, 26) - {logfile}"),
    html.Button("Update", id="update-button", n_clicks=0),
    dcc.Graph(id='live-graph')
])

@app.callback(Output('live-graph', 'figure'), [Input('update-button', 'n_clicks')])
def update_graph(n):
    queue_per_node_per_minute = defaultdict(lambda: defaultdict(list))
    recv_per_minute = defaultdict(int)
    total_sent_messages = 0
    total_received_messages = 0

    try:
        with open(logfile, 'r') as file:
            lines = list(file)

        for line in lines:
            tick_match = re.match(r'^(\d+)', line)
            if not tick_match:
                continue
            tick = int(tick_match.group(1))
            minute = tick // 1_000_000 // 60

            # Per-node queue fill (only for selected nodes)
            queue_match = re.match(r'^\d+\s+(\d+)\s+.*?queue\s+(\d+)/\d+\s+(\d+)/\d+', line)
            if queue_match:
                node = queue_match.group(1)
                if node in included_nodes:
                    q1 = int(queue_match.group(2))
                    q2 = int(queue_match.group(3))
                    queue_per_node_per_minute[node][minute].append((q1 + q2) / 2)

            # Message received
            match_recv = re.match(r'^(\d+)\s+16\s+Data received from .*?: \'Msg ', line)
            if match_recv:
                recv_per_minute[minute] += 1
                total_received_messages += 1

            # Message sent
            match_sent = re.search(r"Sending message: 'Msg ", line)
            if match_sent:
                total_sent_messages += 1

    except FileNotFoundError:
        return go.Figure()

    fig = go.Figure()

    # Plot each selected node's average queue fill
    for node in sorted(included_nodes):
        if node in queue_per_node_per_minute:
            minute_data = queue_per_node_per_minute[node]
            minutes = sorted(minute_data.keys())
            avg_fills = [sum(vals) / len(vals) for m, vals in sorted(minute_data.items())]
            fig.add_trace(go.Scatter(
                x=minutes,
                y=avg_fills,
                mode="lines+markers",
                name=f"Node {node}",
                line=dict(color=fixed_colors.get(node, 'gray')),
                yaxis="y1"
            ))

    # Received messages
    df_recv = pd.DataFrame({
        "Minute": list(recv_per_minute.keys()),
        "Received": list(recv_per_minute.values())
    }).sort_values("Minute")

    fig.add_trace(go.Scatter(
        x=df_recv["Minute"],
        y=df_recv["Received"],
        mode="lines+markers",
        name="Messages Received (Node 16)",
        line=dict(color=fixed_colors['received'], width=3),
        yaxis="y2"
    ))

    success_rate = (total_received_messages / total_sent_messages * 100) if total_sent_messages > 0 else 0

    fig.update_layout(
        title=f"Queue Fill (Nodes 3, 6, 16, 25, 26) and Received Messages ({logfile})",
        xaxis=dict(title="Time (minutes)"),
        yaxis=dict(title=f"Queue Fill (0–{queue})", side="left"),
        yaxis2=dict(title="Messages Received", overlaying="y", side="right"),
        legend_title_text="Legend",
        template="plotly_white",
        height=650,
        annotations=[
            dict(
                xref='paper', yref='paper',
                x=0.1, y=1.1,
                xanchor='left', yanchor='top',
                text=f"📦 Sent: {total_sent_messages} | ✅ Received: {total_received_messages} | 📈 Success rate: {success_rate:.1f}%",
                showarrow=False,
                font=dict(size=14)
            )
        ]
    )

    return fig

if __name__ == "__main__":
    app.run(debug=True)
