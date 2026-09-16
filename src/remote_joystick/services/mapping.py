from __future__ import annotations

from remote_joystick.mapping.axis_mapping import normalize_axis
from remote_joystick.models.device import AxisConfig, ButtonMapping, DeviceState, PovMapping


class MappingService:
    def __init__(
        self,
        axis_mapping: list[AxisConfig] | None = None,
        button_mapping: list[ButtonMapping] | None = None,
        pov_mapping: list[PovMapping] | None = None,
    ) -> None:
        self.axis_mapping = axis_mapping or []
        self.button_mapping = button_mapping or []
        self.pov_mapping = pov_mapping or []

    def map_state(self, state: DeviceState) -> DeviceState:
        mapped_axes = list(state.axes)
        for mapping in self.axis_mapping:
            index = mapping.physical_axis
            if 0 <= index < len(state.axes):
                value = state.axes[index]
                value = normalize_axis(value, invert=mapping.invert, dead_zone=mapping.dead_zone, saturation=mapping.saturation)
                mapped_axes[index] = value

        mapped_buttons = list(state.buttons)
        for mapping in self.button_mapping:
            index = mapping.physical_button
            if 0 <= index < len(state.buttons):
                mapped_buttons[index] = bool(state.buttons[index])
                if mapping.vjoy_button != mapping.physical_button:
                    if mapping.vjoy_button < len(mapped_buttons):
                        mapped_buttons[mapping.vjoy_button] = bool(state.buttons[index])

        mapped_povs = list(state.povs)
        for mapping in self.pov_mapping:
            index = mapping.physical_pov
            if 0 <= index < len(state.povs):
                mapped_povs[index] = int(state.povs[index])

        return DeviceState(
            logical_id=state.logical_id,
            physical_id=state.physical_id,
            name=state.name,
            sequence=state.sequence,
            timestamp_ms=state.timestamp_ms,
            axes=mapped_axes,
            buttons=mapped_buttons,
            povs=mapped_povs,
            connected=state.connected,
            channel=state.channel,
        )
