
import serial
import time
import plotly.graph_objects as go
import sys

# Configuration
serial_port = ""
baud_rate = 0
capture_duration = 0  # seconds

if serial_port == "":
    print("Please set serial_port (e.g COM0 or /dev/ttyUSB0)")
    sys.exit(1)

if baud_rate == 0:
    print("Please set baud_rate in bits per second (e.g 115200)")
    sys.exit(1)

if capture_duration == 0:
    print("Please set capture_duration in seconds (e.g 5)")
    sys.exit(1)

timestamps = []
values = []

with serial.Serial(serial_port, baud_rate, timeout=0.1) as ser:
    # Allow Arduino to reset
    time.sleep(2)
    ser.reset_input_buffer()

    print(f"Capturing GPIO data for {capture_duration} seconds...")

    start_time = time.monotonic()

    while time.monotonic() - start_time < capture_duration:
        data = ser.read(1)

        # Ignore anything other than '0' or '1'
        if data not in (b'0', b'1'):
            continue

        timestamp = time.monotonic() - start_time

        timestamps.append(timestamp)
        values.append(int(data))

print(f"Captured {len(values)} samples.")

# Plotly graph
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=timestamps,
    y=values,
    mode="lines",
    line=dict(shape="hv", width=2),
    name="GPIO",
    hovertemplate="Time: %{x:.4f} s<br>GPIO: %{y}<extra></extra>"
))

fig.update_layout(
    title="Digital Signal Capture",
    xaxis_title="Time (seconds)",
    yaxis_title="GPIO state",
    template="plotly_dark",
    hovermode="x unified",
    width=1200,
    height=500
)

fig.update_xaxes(
    range=[0, capture_duration],
    showgrid=True,
    gridcolor="rgba(128,128,128,0.2)"
)

fig.update_yaxes(
    range=[-0.2, 1.2],
    tickvals=[0, 1],
    showgrid=True
)

fig.show()
