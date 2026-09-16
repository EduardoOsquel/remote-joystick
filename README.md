# remote-joystick

Remote joystick streaming for Windows over Tailscale.

This project is designed for a very specific setup: one or more physical HOTAS devices on a sender PC, transmitted over Tailscale to a receiver PC, and exposed as vJoy devices for games such as Star Citizen.

## Purpose

The goal is to let a real joystick or HOTAS be captured on one Windows machine and re-created on another Windows machine as a virtual joystick, without requiring direct USB sharing or a full driver stack on the sender side.

## Current status

The project has already implemented the foundation and the hardware-facing layers that were planned in the earlier phases:

### Implemented

- Configuration loader and validation
- Binary UDP protocol with packet encoding/decoding
- HMAC-based authenticity checks for packet integrity
- Local simulator for testing without hardware
- Windows joystick discovery and polling using WinMM APIs
- vJoy output backend with a safe no-op mode when the DLL is unavailable
- Bridge service for normalizing input state into a transportable model
- Mapping service for axis, button and POV transformations
- CLI commands for listing devices and running sender/receiver simulation paths

### Still pending

- Real end-to-end Tailscale test with two PCs
- Real vJoy installation and verification on the receiver machine
- Live validation with physical HOTAS devices
- Multi-device channel routing for two simultaneous stick inputs
- Rate limit and heartbeat tuning for stable network behavior
- Robust error recovery and reconnection logic
- GUI layer, if later desired

## Scope

This project targets only:

- Physical HID/DirectInput joystick detection on Windows
- Two selected devices at a time
- Packetized UDP state transmission over Tailscale
- Independent vJoy outputs on the receiver side
- CLI-first operation for now
- Debug simulation without hardware

This project does not implement generic USB forwarding, keyboards, mice, audio, video, Linux/macOS support, or cloud-hosted services.

## Architecture

The current flow is:

- Input layer reads physical Windows joysticks or a simulator
- Mapping layer normalizes axes/buttons/POV values
- Protocol layer serializes and validates UDP packets
- Sender/receiver transport handles data exchange over the network
- Output layer writes to vJoy or debug output

## Requirements

- Windows 10 or 11 64-bit
- Python 3.12
- Tailscale installed and running on both PCs
- vJoy installed manually on the receiver
- PySide6 included for future GUI work

## Installation

1. Create a virtual environment.
2. Install the project in editable mode:

   python -m pip install -e .[dev]

3. Copy the sample config and edit it:

   copy config.example.toml config.toml

## Manual vJoy setup

Install vJoy on the receiver machine manually. After installation, verify that the virtual devices are available and can be acquired by the OS before using the receiver-side output layer.

## CLI usage

From the project root:

### List connected Windows joysticks

python -m remote_joystick.cli list-inputs

### List vJoy backend status

python -m remote_joystick.cli list-vjoy

### Run sender simulation / local sender path

python -m remote_joystick.cli sender --config config.example.toml

### Run receiver path

python -m remote_joystick.cli receiver --config config.example.toml

### Simulate devices without hardware

python -m remote_joystick.cli simulate --devices 2

## Local simulation

The simulator lets you test the pipeline locally without a physical joystick:

python -m remote_joystick.cli simulate --devices 2

This is useful for validating the bridge, protocol and mapping logic before using hardware.

## Test commands

pytest
ruff check .
mypy src

## Recommended next implementation steps

1. Validate the sender on a real Windows PC with physical HOTAS devices.
2. Validate the receiver on a Windows PC with a working vJoy installation.
3. Confirm Tailscale connectivity and packet flow between both machines.
4. Add final channel routing for two simultaneous joystick inputs.
5. Tune mapping profiles and dead zones for each device model.
6. Add heartbeat, timeout recovery and network diagnostics.
7. Optionally add a GUI once the CLI path is fully proven.

## Notes

The project is currently in a hardware-ready state at the implementation level: the key Windows input, mapping, and vJoy output pieces are in place and validated at the unit/test level. Real hardware validation remains the next required step before the system is considered fully complete end-to-end.
