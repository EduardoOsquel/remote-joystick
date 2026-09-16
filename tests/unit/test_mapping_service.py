from remote_joystick.models.device import AxisConfig, ButtonMapping, DeviceState, PovMapping
from remote_joystick.services.mapping import MappingService


def test_mapping_service_applies_axis_button_and_pov_transforms() -> None:
    service = MappingService(
        axis_mapping=[
            AxisConfig(physical_axis=0, vjoy_axis=0, invert=True, dead_zone=0.05, saturation=1.0),
            AxisConfig(physical_axis=1, vjoy_axis=1, invert=False, dead_zone=0.1, saturation=0.8),
        ],
        button_mapping=[
            ButtonMapping(physical_button=0, vjoy_button=1),
            ButtonMapping(physical_button=1, vjoy_button=2),
        ],
        pov_mapping=[
            PovMapping(physical_pov=0, vjoy_pov=0, safe_value=-1),
        ],
    )

    state = DeviceState(
        logical_id="phys-1",
        physical_id="phys-1",
        name="Stick A",
        sequence=1,
        timestamp_ms=1000,
        axes=[0.06, 0.6],
        buttons=[True, False],
        povs=[18000],
        connected=True,
        channel=1,
    )

    mapped = service.map_state(state)

    assert mapped.axes[0] == -0.06
    assert mapped.axes[1] == 0.48
    assert mapped.buttons[0] is True
    assert mapped.buttons[1] is False
    assert mapped.povs[0] == 18000
