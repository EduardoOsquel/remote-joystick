# Fase 5: captura real y salida a vJoy

## Objetivo

Implementar la toma real de estados del joystick físico en Windows y la escritura de esos estados a un dispositivo vJoy en el PC receptor, manteniendo la arquitectura del proyecto intacta.

## Qué está ya hecho

- Capa de configuración y validación
- Protocolo UDP + HMAC
- Simulador de dos joysticks
- Servicios de puente y mapeo
- CLI con integración de entrada Windows y salida vJoy

## Cambios clave realizados

- Se reemplaza el stub de entrada por un adaptador basado en WinMM (`joyGetNumDevs` / `joyGetDevCapsW` / `joyGetPosEx`).
- Se reemplaza el stub de salida por un backend que intenta cargar `vJoyInterface.dll` y escribir ejes, botones y POV cuando el DLL está presente.
- Se conserva el comportamiento seguro cuando no hay hardware o no está instalado vJoy.

## Limitaciones reales

- La captura real solo funciona en Windows.
- La salida real a vJoy requiere la instalación manual de vJoy en el PC receptor y la presencia de `vJoyInterface.dll`.
- Si el DLL o el hardware no existen, el backend no falla de forma destructiva: se queda en modo no-op y el sistema sigue siendo ejecutable.

## Siguientes pasos recomendados

1. Instalar vJoy en el receptor.
2. Verificar en `Device Manager` o la herramienta del fabricante que los dispositivos están disponibles.
3. Probar la CLI con el hardware conectado.
4. Ajustar mapeos ejes/botones según cada HOTAS.
5. Añadir soporte de dos joysticks en paralelo con un canal por dispositivo.
6. Introducir gestión de latencia y heartbeat en la capa de red.

## Comandos útiles

- `python -m remote_joystick.cli list-inputs`
- `python -m remote_joystick.cli list-vjoy`
- `python -m remote_joystick.cli sender --config config.example.toml`
- `python -m remote_joystick.cli receiver --config config.example.toml`
