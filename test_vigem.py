import ctypes
import math
import time

PATH = r"C:\Python\remote-joystick\runtime\vigem\ViGEmClient.dll"
VIGEM_ERROR_NONE = 0x20000000

class XUSB_REPORT(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]

print(f"Cargando DLL:\n{PATH}")
dll = ctypes.WinDLL(PATH)
print("DLL cargada correctamente.")

dll.vigem_alloc.restype = ctypes.c_void_p
dll.vigem_connect.argtypes = [ctypes.c_void_p]
dll.vigem_connect.restype = ctypes.c_uint32
dll.vigem_target_x360_alloc.restype = ctypes.c_void_p
dll.vigem_target_add.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
dll.vigem_target_add.restype = ctypes.c_uint32
dll.vigem_target_x360_update.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(XUSB_REPORT)]
dll.vigem_target_x360_update.restype = ctypes.c_uint32
dll.vigem_target_free.argtypes = [ctypes.c_void_p]
dll.vigem_disconnect.argtypes = [ctypes.c_void_p]

client = dll.vigem_alloc()
print(f"client = {hex(ctypes.c_void_p(client).value)}")

connect_result = dll.vigem_connect(client)
print(f"connect = {hex(connect_result)}")
if connect_result != VIGEM_ERROR_NONE:
    raise RuntimeError(f"vigem_connect falló: {hex(connect_result)}")

target = dll.vigem_target_x360_alloc()
print(f"target = {hex(ctypes.c_void_p(target).value)}")

add_result = dll.vigem_target_add(client, target)
print(f"add = {hex(add_result)}")
if add_result != VIGEM_ERROR_NONE:
    raise RuntimeError(f"vigem_target_add falló: {hex(add_result)}")

print("============================================")
print("PRUEBA LIVE DE VI GEM INICIADA")
print("============================================")
print("El controlador virtual queda conectado mientras se ejecuta este bucle.")
print("Abre Device Manager y mira si aparece 'Xbox 360 para Windows'.")
print("Pulsa Ctrl+C para terminar.")

tick = 0
try:
    while True:
        report = XUSB_REPORT()
        report.wButtons = 0x1000  # A
        report.bLeftTrigger = 0
        report.bRightTrigger = 0

        # Ejes con movimiento oscilante
        report.sThumbLX = int(math.sin(tick / 10.0) * 32767)
        report.sThumbLY = int(math.cos(tick / 10.0) * 32767)
        report.sThumbRX = int(math.sin(tick / 7.0) * 16383)
        report.sThumbRY = int(math.cos(tick / 7.0) * 16383)

        update_result = dll.vigem_target_x360_update(client, target, ctypes.pointer(report))
        if update_result != VIGEM_ERROR_NONE:
            print(f"update = {hex(update_result)}")
            break

        print(f"tick={tick:03d} lx={report.sThumbLX} ly={report.sThumbLY} btn={report.wButtons:#x}")
        tick += 1
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nInterrumpido por el usuario.")

finally:
    print("Liberando target...")
    dll.vigem_target_free(target)
    dll.vigem_disconnect(client)
    print("Target liberado correctamente.")