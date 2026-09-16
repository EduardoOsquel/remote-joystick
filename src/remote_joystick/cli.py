from __future__ import annotations

import argparse
import json
import sys

from remote_joystick.config import Config
from remote_joystick.input.simulator import SimulatorInputDevice
from remote_joystick.logging_config import configure_logging
from remote_joystick.transport.receiver import UDPReceiver
from remote_joystick.transport.sender import UDPSender


def _load_config(path: str | None) -> Config:
    config_path = path or "config.toml"
    cfg = Config.load(config_path)
    cfg.validate()
    return cfg


def list_inputs(_args: argparse.Namespace) -> int:
    sim = SimulatorInputDevice(device_count=2)
    for device in sim.list_devices():
        print(device)
    sim.close()
    return 0


def list_vjoy(_args: argparse.Namespace) -> int:
    print("No vJoy devices are configured or available in this scaffold build.")
    return 0


def sender(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    configure_logging(config.application.log_level)
    sender_transport = UDPSender(config.network.target_host, config.network.port, config.security.shared_key.encode("utf-8"))
    sim = SimulatorInputDevice(device_count=2)
    try:
        for channel in (1, 2):
            state = sim.read_state(channel)
            print(json.dumps({"channel": channel, "axes": state.axes, "buttons": state.buttons, "povs": state.povs}, default=str))
    finally:
        sim.close()
        sender_transport.close()
    return 0


def receiver(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    configure_logging(config.application.log_level)
    receiver_transport = UDPReceiver(config.network.bind_host, config.network.port, config.security.shared_key.encode("utf-8"))
    try:
        packet = receiver_transport.recv(timeout=0.1)
        print(packet)
    finally:
        receiver_transport.close()
    return 0


def simulate(args: argparse.Namespace) -> int:
    sim = SimulatorInputDevice(device_count=args.devices)
    for channel in range(1, args.devices + 1):
        print(sim.read_state(channel))
    sim.close()
    return 0


def doctor(_args: argparse.Namespace) -> int:
    print("Doctor checks are scaffolded; physical joystick and vJoy integration will be added in later phases.")
    return 0


def gui(_args: argparse.Namespace) -> int:
    print("GUI is not implemented yet; this is a console-first scaffold.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="remote-joystick")
    subparsers = parser.add_subparsers(dest="command", required=True)

    cmd = subparsers.add_parser("list-inputs")
    cmd.set_defaults(func=list_inputs)

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
