from __future__ import annotations

import msvcrt
import re
import sys
import time
from pathlib import Path

try:
    import serial
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "pyserial is required. Install it with: pip install pyserial"
    ) from exc


PORT = "COM9"
BAUD_RATE = 115200
OUTPUT_DIR = Path(__file__).resolve().parent
PROMPT = "> "


def next_listen_file(folder: Path) -> Path:
    index = 1
    while (folder / f"Listen_{index}.txt").exists():
        index += 1
    return folder / f"Listen_{index}.txt"


def write_listen_block(handle, message: str, packet_number: str, rssi: str) -> None:
    handle.write("///////////\n")
    handle.write(f"{message}\n")
    handle.write("////////\n")
    handle.write("Data:\n")
    handle.write(f"Packet_Num= {packet_number}\n")
    handle.write(f"RSSI = {rssi}\n")
    handle.write(".\n\n")
    handle.flush()


def print_prompt() -> None:
    sys.stdout.write(PROMPT)
    sys.stdout.flush()


def main() -> None:
    try:
        ser = serial.Serial(PORT, BAUD_RATE, timeout=0.05)
    except serial.SerialException as exc:
        print(f"Error opening serial port {PORT}: {exc}")
        return

    output_dir = OUTPUT_DIR
    log_handle = None
    listen_active = False
    pending_message = None
    input_buffer = ""
    serial_buffer = ""

    print(f"Connected to {PORT} at {BAUD_RATE} baud")
    print("Type commands and press Enter. Use listen to start logging and q to stop listening.")
    print_prompt()

    try:
        while True:
            while msvcrt.kbhit():
                char = msvcrt.getwch()

                if char in ("\r", "\n"):
                    line = input_buffer.strip()
                    input_buffer = ""
                    print()

                    if line:
                        ser.write((line + "\n").encode("utf-8"))

                        if line.lower() == "q":
                            if listen_active and log_handle is not None:
                                log_handle.close()
                                log_handle = None
                                listen_active = False
                                pending_message = None
                                print("Exiting listen mode")
                        elif line.lower() == "listen":
                            print("Sent listen")
                        else:
                            print(f"Sent {line}")

                    print_prompt()
                    continue

                if char == "\003":
                    raise KeyboardInterrupt

                if char == "\b":
                    if input_buffer:
                        input_buffer = input_buffer[:-1]
                        sys.stdout.write("\b \b")
                        sys.stdout.flush()
                    continue

                if char.isprintable():
                    input_buffer += char
                    sys.stdout.write(char)
                    sys.stdout.flush()

            data = ser.read(4096)
            if data:
                serial_buffer += data.decode("utf-8", errors="replace")

                while "\n" in serial_buffer:
                    line, serial_buffer = serial_buffer.split("\n", 1)
                    line = line.rstrip("\r")

                    if not line.strip():
                        continue

                    print()
                    print(line)

                    if "Listening... press q to quit" in line and not listen_active:
                        log_path = next_listen_file(output_dir)
                        log_handle = open(log_path, "w", encoding="utf-8", newline="\n")
                        listen_active = True
                        pending_message = None
                        print(f"Logging listen session to {log_path.name}")

                    elif line.startswith("Got message: "):
                        pending_message = line.removeprefix("Got message: ").strip()

                    elif (line.startswith(", RSSI:") or line.startswith("RSSI:")) and listen_active and log_handle:
                        if pending_message is not None:
                            rssi = line.split(":", 1)[1].strip()
                            match = re.search(r"#\s*(\d+)", pending_message)
                            packet_number = match.group(1) if match else "Unknown"
                            write_listen_block(log_handle, pending_message, packet_number, rssi)
                            pending_message = None

                    elif "Exiting listen mode" in line:
                        if log_handle is not None:
                            log_handle.close()
                            log_handle = None
                        listen_active = False
                        pending_message = None
                        print("Listen log closed")

                    print_prompt()

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nExiting.")
    finally:
        if log_handle is not None:
            log_handle.close()
        ser.close()


if __name__ == "__main__":
    main()
