
import serial
import time
import matplotlib.pyplot as plt

# Configuration
SERIAL_PORT = "/dev/ttyUSB1"
BAUD_RATE = 115200
CAPTURE_DURATION = 10  # seconds

timestamps = []
values = []

with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1) as ser:
    # Allow Arduino to reset
    time.sleep(2)
    ser.reset_input_buffer()

    print(f"Capturing GPIO data for {CAPTURE_DURATION} seconds...")

    start_time = time.monotonic()

    while time.monotonic() - start_time < CAPTURE_DURATION:
        # Read one byte at a time
        data = ser.read(1)

        # Ignore anything other than '0' or '1'
        if data not in (b'0', b'1'):
            continue

        timestamp = time.monotonic() - start_time

        timestamps.append(timestamp)
        values.append(int(data))

print(f"Captured {len(values)} samples.")

# Plot
fig, ax = plt.subplots(figsize=(12, 5))

ax.step(timestamps, values, where="post", linewidth=1.5)

ax.set_title("ESP32 GPIO 2 - Digital Signal Capture")
ax.set_xlabel("Time (seconds)")
ax.set_ylabel("GPIO state")

ax.set_xlim(0, CAPTURE_DURATION)
ax.set_ylim(-0.2, 1.2)
ax.set_yticks([0, 1])

ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
