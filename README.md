# remote-joystick

Remote joystick streaming for Windows over Tailscale.

This project is intentionally scoped to a small, explicit setup: two physical devices on the sender side, two vJoy outputs on the receiver side, with a simple binary UDP protocol and a CLI-first architecture.

## Purpose

The goal is to allow two real HOTAS or game joysticks on one Windows PC to be streamed to another Windows PC and exposed as two independent vJoy devices for Star Citizen.

## Scope

This project targets only:

- Physical HID/DirectInput joystick detection on Windows
- Two selected devices at a time
- Packetized UDP state transmission over Tailscale
- Independent vJoy outputs for channels 1 and 2
- CLI-based operation first, with GUI later
- Debug simulation without hardware

This project does not implement USB/IP, keyboards, mice, audio, video, generic USB forwarding, Linux/macOS support, or cloud services.

## Architecture

The codebase is organized in phases around clear interfaces. The general flow is:

- Input layer reads either physical joysticks or a simulator
- Mapping layer normalizes and transforms axes/buttons/POV values
- Protocol layer encodes and validates UDP packets
- Send or receive service handles timeouts and state management
- Output layer writes to vJoy or a debug sink

## Requirements

- Windows 10 or 11 64-bit
- Python 3.12
- Tailscale installed and running on both systems
- vJoy installed manually on the receiver
- PySide6 for GUI only

## Installation

1. Create a virtual environment.
2. Install the package in editable mode:

   pip install -e .[dev]

3. Copy the sample config and edit it:

   copy config.example.toml config.toml

## Manual vJoy setup

Install vJoy on the receiver machine manually, then create two devices in the vJoy configuration utility. Confirm that they can be acquired and visible in the system.

## Local simulation

Run the simulated sender and a local receiver on the same machine:

python -m remote_joystick.cli sender --config config.example.toml
python -m remote_joystick.cli receiver --config config.example.toml

For a pure simulation mode:

python -m remote_joystick.cli simulate --devices 2

## Test commands

pytest
ruff check .
mypy src

## Notes

This is a proof-of-concept scaffold for the first three phases: configuration, protocol, and simulator. Physical joystick support and vJoy integration are not yet implemented.
