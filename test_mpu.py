#!/usr/bin/env python3
import smbus2, time, math

bus = smbus2.SMBus(1)
MPU = 0x68

# Wake up MPU6050
bus.write_byte_data(MPU, 0x6B, 0)
time.sleep(0.1)
print("MPU6050 initialized")

def read_word(reg):
    high = bus.read_byte_data(MPU, reg)
    low  = bus.read_byte_data(MPU, reg + 1)
    val  = (high << 8) + low
    if val >= 0x8000:
        val = -((65535 - val) + 1)
    return val

print("Reading data... (Ctrl+C to stop)\n")
try:
    while True:
        ax = read_word(0x3B) / 16384.0
        ay = read_word(0x3D) / 16384.0
        az = read_word(0x3F) / 16384.0
        gx = read_word(0x43) / 131.0
        gy = read_word(0x45) / 131.0
        gz = read_word(0x47) / 131.0

        pitch = math.atan2(ay, az) * 180 / math.pi
        roll  = math.atan2(-ax, az) * 180 / math.pi

        print(f"Accel: x={ax:6.2f} y={ay:6.2f} z={az:6.2f} g  |  Gyro: x={gx:7.2f} y={gy:7.2f} z={gz:7.2f} deg/s  |  Pitch:{pitch:6.1f} Roll:{roll:6.1f}")
        time.sleep(0.2)
except KeyboardInterrupt:
    print("Done")
