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
num_senders = 20  # Adjust this if needed

app = Dash(__name__)
app.title = "COOJA Live Queue & Reception Monitor"

app.layout = html.Div([
    html.H2(f"Live TSCH Queue Fill & Node 16 Reception ({logfile})"),
    dcc.Graph(id='live-graph'),
    dcc.Interval(id='interval-component', interval=10 * 1000, n_intervals=0)
])

@app.callback(Output('live-graph', 'figure'), [Input('interval-component', 'n_intervals')])
def update_graph(n):
    queue1_per_minute = defaultdict(list)
    queue2_per_minute = defaultdict(list)
    recv_per_minute = defaultdict(int)
    avg_sent_per_minute = defaultdict(float)
    confirmed_sent_per_minute = defaultdict(set)
    last_sent_message = {}

    total_sent_messages = 0
    total_received_messages = 0

    try:
        with open(logfile, 'r') as file:
            lines = list(file)

        for i, line in enumerate(lines):
            tick_match = re.match(r'^(\d+)', line)
            if not tick_match:
                continue
            tick = int(tick_match.group(1))
            minute = tick // 1_000_000 // 60

            # Queue fill
            match_queue = re.search(fr'queue\s+(\d+)/{queue}\s+(\d+)/{queue}', line)
            if match_queue:
                q1 = int(match_queue.group(1))
                q2 = int(match_queue.group(2))
                queue1_per_minute[minute].append(q1)
                queue2_per_minute[minute].append(q2)

            # Sending message: record latest msg ID per node
            send_match = re.match(r'^\d+\s+(\d+)\s+Sending message: \'Msg (.+?)\' to', line)
            if send_match:
                node = send_match.group(1)
                msg_id = send_match.group(2).strip()
                last_sent_message[node] = msg_id
                total_sent_messages += 1
                avg_sent_per_minute[minute] += 1 / num_senders

            # TSCH send packet: count only unique (node, msg_id)
            tsch_match = re.match(r'^\d+\s+(\d+)\s+\[INFO: TSCH\s+\] send packet to 0001.0001.0001.0001', line)
            if tsch_match:
                node = tsch_match.group(1)
                if node in last_sent_message:
                    msg_id = last_sent_message[node]
                    confirmed_sent_per_minute[minute].add((node, msg_id))

            # Received by node 16
            match_recv = re.match(r'^(\d+)\s+16\s+Data received from .*?: \'Msg ', line)
            if match_recv:
                recv_per_minute[minute] += 1
                total_received_messages += 1

    except FileNotFoundError:
        return go.Figure()

    # Compute success rate
    success_rate = (total_received_messages / total_sent_messages * 100) if total_sent_messages > 0 else 0

    # Combine and aggregate data
    all_minutes = sorted(set(queue1_per_minute) |
                         set(queue2_per_minute) |
                         set(recv_per_minute) |
                         set(avg_sent_per_minute) |
                         set(confirmed_sent_per_minute))

    records = []
    for minute in all_minutes:
        #avg_q1 = sum(queue1_per_minute[minute]) / len(queue1_per_minute[minute]) if queue1_per_minute[minute] else 0
        #avg_q2 = sum(queue2_per_minute[minute]) / len(queue2_per_minute[minute]) if queue2_per_minute[minute] else 0
        received = recv_per_minute.get(minute, 0)
        avg_q1 = max(queue1_per_minute[minute]) if queue1_per_minute[minute] else 0
        avg_q2 = max(queue2_per_minute[minute]) if queue2_per_minute[minute] else 0
        confirmed = len(confirmed_sent_per_minute.get(minute, set())) / num_senders
        avg_sent = avg_sent_per_minute.get(minute, 0)

        records.append({
            "Minute": minute,
            "Avg Queue 1": avg_q1,
            "Avg Queue 2": avg_q2,
            "Messages Received (Node 16)": received,
            "Avg Sent": avg_sent,
            "Confirmed Sent": confirmed
        })

    df = pd.DataFrame(records)

    # === Plotting ===
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Minute"], y=df["Avg Queue 1"],
                             mode="lines+markers", name="Avg Queue 1",
                             line=dict(color="blue", dash="dot"), yaxis="y1"))
    fig.add_trace(go.Scatter(x=df["Minute"], y=df["Avg Queue 2"],
                             mode="lines+markers", name="Avg Queue 2",
                             line=dict(color="red", dash="dot"), yaxis="y1"))
    fig.add_trace(go.Scatter(x=df["Minute"], y=df["Messages Received (Node 16)"],
                             mode="lines+markers", name="Messages Received (Node 16)",
                             line=dict(color="green", width=3), yaxis="y2"))
    fig.add_trace(go.Scatter(x=df["Minute"], y=df["Confirmed Sent"],
                             mode="lines+markers", name="Avg Confirmed Sent",
                             line=dict(color="orange", dash="dash"), yaxis="y2"))
    fig.add_trace(go.Scatter(x=df["Minute"], y=df["Avg Sent"],
                             mode="lines+markers", name="Avg Sent",
                             line=dict(color="purple", dash="dot"), yaxis="y2"))

    fig.update_layout(
        title=f"Received Messages per Minute({logfile})",
        xaxis=dict(title="Time (minutes)"),
        yaxis=dict(title=f"Avg Queue Fill (0–{queue})", side="left"),
        yaxis2=dict(title="Messages / Minute", overlaying="y", side="right"),
        legend_title_text="Legend",
        template="plotly_white",
        height=650,
        annotations=[
            dict(
                xref='paper', yref='paper',
                x=0.135, y=1.09,
                xanchor='center', yanchor='top',
                text=f"📦 Sent: {total_sent_messages} | ✅ Received: {total_received_messages} | 📈 Success rate: {success_rate:.1f}%",
                showarrow=False,
                font=dict(size=14)
            )
        ]
    )

    return fig

if __name__ == "__main__":
    app.run(debug=True)
