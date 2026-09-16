from __future__ import annotations

import argparse
import json
import sys

from remote_joystick.config import Config
from remote_joystick.input.simulator import SimulatorInputDevice
from remote_joystick.input.windows import WindowsJoystickInputDevice
from remote_joystick.logging_config import configure_logging
from remote_joystick.output.debug import DebugOutputDevice
from remote_joystick.output.vigem import ViGEmOutputDevice
from remote_joystick.services.bridge import BridgeService
from remote_joystick.transport.receiver import UDPReceiver
from remote_joystick.transport.sender import UDPSender

# Backward-compatible alias kept for existing tests and older code paths while the
# active implementation is now ViGEmBus-oriented.
VJoyOutputDevice = ViGEmOutputDevice


def _load_config(path: str | None) -> Config:
    config_path = path or "config.toml"
    cfg = Config.load(config_path)
    cfg.validate()
    return cfg


def list_inputs(_args: argparse.Namespace) -> int:
    input_device = WindowsJoystickInputDevice()
    devices = input_device.list_devices()
    if not devices:
        print("No Windows joystick devices detected.")
    else:
        for device in devices:
            print(device)
    input_device.close()
    return 0


def list_vigem(_args: argparse.Namespace) -> int:
    output_device = ViGEmOutputDevice(device_id=1)
    print(f"ViGEm output backend initialized: {type(output_device.backend).__name__}")
    backend = output_device.backend
    status = getattr(backend, "status_message", None)
    if status is None:
        status = "The ViGEmBus DLL is not installed on the receiver machine." if not getattr(backend, "is_available", True) else "ViGEmBus DLL detected and available on the receiver machine."
    print(status)
    return 0


def list_vjoy(_args: argparse.Namespace) -> int:
    output_device = VJoyOutputDevice(device_id=1)
    print(f"ViGEm output backend initialized: {type(output_device.backend).__name__}")
    backend = output_device.backend
    status = getattr(backend, "status_message", None)
    if status is None:
        status = "The actual vJoy DLL is still a manual installation requirement on the receiver machine." if not getattr(backend, "is_available", True) else "vJoy DLL detected and available on the receiver machine."
    print(status)
    return 0


def sender(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    configure_logging(config.application.log_level)
    input_device = WindowsJoystickInputDevice()
    debug_output = DebugOutputDevice()
    bridge = BridgeService(input_device, debug_output)
    try:
        devices = input_device.list_devices()
        if not devices:
            print("No Windows joystick devices detected for sending.")
            return 0

        for device in devices:
            try:
                state = bridge.write_next(device.channel)
                print(json.dumps({"channel": device.channel, "name": state.name, "axes": state.axes, "buttons": state.buttons, "povs": state.povs}, default=str))
            except ValueError as exc:
                print(f"Skipping channel {device.channel}: {exc}")
    finally:
        bridge.close()
    return 0


def receiver(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    configure_logging(config.application.log_level)
    receiver_transport = UDPReceiver(config.network.bind_host, config.network.port, config.security.shared_key.encode("utf-8"))
    output_device = ViGEmOutputDevice(device_id=1)
    try:
        packet = receiver_transport.recv(timeout=0.1)
        if packet is None:
            print("No UDP packet received yet.")
        else:
            print(packet)
            output_device.reset_to_safe_state("packet received")
    finally:
        receiver_transport.close()
        output_device.close()
    return 0


def simulate(args: argparse.Namespace) -> int:
    sim = SimulatorInputDevice(device_count=args.devices)
    for channel in range(1, args.devices + 1):
        print(sim.read_state(channel))
    sim.close()
    return 0


def doctor(_args: argparse.Namespace) -> int:
    print("Doctor checks are scaffolded; physical joystick and ViGEmBus integration will be added in later phases.")
    return 0


def gui(_args: argparse.Namespace) -> int:
    print("GUI is not implemented yet; this is a console-first scaffold.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="remote-joystick")
    subparsers = parser.add_subparsers(dest="command", required=True)

    cmd = subparsers.add_parser("list-inputs")
    cmd.set_defaults(func=list_inputs)

    cmd = subparsers.add_parser("list-vigem")
    cmd.set_defaults(func=list_vigem)

    cmd = subparsers.add_parser("list-vjoy")
    cmd.set_defaults(func=list_vjoy)

    cmd = subparsers.add_parser("sender")
    cmd.add_argument("--config", default="config.toml")
    cmd.set_defaults(func=sender)

    cmd = subparsers.add_parser("receiver")
    cmd.add_argument("--config", default="config.toml")
    cmd.set_defaults(func=receiver)

    cmd = subparsers.add_parser("simulate")
    cmd.add_argument("--devices", type=int, default=2)
    cmd.set_defaults(func=simulate)

    cmd = subparsers.add_parser("doctor")
    cmd.set_defaults(func=doctor)

    cmd = subparsers.add_parser("gui")
    cmd.set_defaults(func=gui)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:  # pragma: no cover - CLI safety
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
