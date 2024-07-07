# telemetry.py
import threading
import random
import time
import serial
import math
from shared_data import shared_data
from enum import IntEnum


CRSF_SYNC = 0xC8

class PacketsTypes(IntEnum):
    GPS = 0x02
    VARIO = 0x07
    BATTERY_SENSOR = 0x08
    BARO_ALT = 0x09
    HEARTBEAT = 0x0B
    VIDEO_TRANSMITTER = 0x0F
    LINK_STATISTICS = 0x14
    RC_CHANNELS_PACKED = 0x16
    ATTITUDE = 0x1E
    FLIGHT_MODE = 0x21
    DEVICE_INFO = 0x29
    CONFIG_READ = 0x2C
    CONFIG_WRITE = 0x2D
    RADIO_ID = 0x3A

def crc8_dvb_s2(crc, a) -> int:
  crc = crc ^ a
  for ii in range(8):
    if crc & 0x80:
      crc = (crc << 1) ^ 0xD5
    else:
      crc = crc << 1
  return crc & 0xFF

def crc8_data(data) -> int:
    crc = 0
    for a in data:
        crc = crc8_dvb_s2(crc, a)
    return crc

def crsf_validate_frame(frame) -> bool:
    return crc8_data(frame[2:-1]) == frame[-1]

def signed_byte(b):
    return b - 256 if b >= 128 else b

def packCrsfToBytes(channels) -> bytes:
    # channels is in CRSF format! (0-1984)
    # Values are packed little-endianish such that bits BA987654321 -> 87654321, 00000BA9
    # 11 bits per channel x 16 channels = 22 bytes
    if len(channels) != 16:
        raise ValueError('CRSF must have 16 channels')
    result = bytearray()
    destShift = 0
    newVal = 0
    for ch in channels:
        # Put the low bits in any remaining dest capacity
        newVal |= (ch << destShift) & 0xff
        result.append(newVal)

        # Shift the high bits down and place them into the next dest byte
        srcBitsLeft = 11 - 8 + destShift
        newVal = ch >> (11 - srcBitsLeft)
        # When there's at least a full byte remaining, consume that as well
        if srcBitsLeft >= 8:
            result.append(newVal & 0xff)
            newVal >>= 8
            srcBitsLeft -= 8

        # Next dest should be shifted up by the bits consumed
        destShift = srcBitsLeft

    return result

def channelsCrsfToChannelsPacket(channels) -> bytes:
    result = bytearray([CRSF_SYNC, 24, PacketsTypes.RC_CHANNELS_PACKED]) # 24 is packet length
    result += packCrsfToBytes(channels)
    result.append(crc8_data(result[2:]))
    return result

def handleCrsfPacket(ptype, data):
    if ptype == PacketsTypes.RADIO_ID and data[5] == 0x10:
        #print(f"OTX sync")
        pass
    elif ptype == PacketsTypes.LINK_STATISTICS:
        shared_data.rssi1 = signed_byte(data[3])
        shared_data.rssi2 = signed_byte(data[4])
        shared_data.lq = data[5]
        shared_data.snr = signed_byte(data[6])
        antenna = data[7]
        shared_data.mode = data[8]
        power = data[9]
        # telemetry strength
        downlink_rssi = signed_byte(data[10])
        downlink_lq = data[11]
        downlink_snr = signed_byte(data[12])
        shared_data.last_time_telemetry = time.time()
        if shared_data.printtele: print(f"RSSI={shared_data.rssi1}/{shared_data.rssi2}dBm LQ={shared_data.lq:03} mode={shared_data.mode}") # ant={antenna} snr={snr} power={power} drssi={downlink_rssi} dlq={downlink_lq} dsnr={downlink_snr}")
    
    elif ptype == PacketsTypes.ATTITUDE:
        shared_data.pitch = int.from_bytes(data[3:5], byteorder='big', signed=True) / 10000.0
        shared_data.roll = int.from_bytes(data[5:7], byteorder='big', signed=True) / 10000.0
        shared_data.yaw = int.from_bytes(data[7:9], byteorder='big', signed=True) / 10000.0
        shared_data.last_time_telemetry = time.time()
        if shared_data.printtele: print(f"Attitude: Pitch={shared_data.pitch:0.2f} Roll={shared_data.roll:0.2f} Yaw={shared_data.yaw:0.2f} (rad)")

    elif ptype == PacketsTypes.FLIGHT_MODE:
        shared_data.flightmode = ''.join(map(chr, data[3:-2]))
        shared_data.last_time_telemetry = time.time()
        if shared_data.printtele: print(f"Flight Mode: {shared_data.flightmode}")

    elif ptype == PacketsTypes.BATTERY_SENSOR:
        shared_data.vbat = int.from_bytes(data[3:5], byteorder='big', signed=True) / 10.0
        shared_data.curr = int.from_bytes(data[5:7], byteorder='big', signed=True) / 10.0
        shared_data.mah = data[7] << 16 | data[8] << 7 | data[9]
        shared_data.pct = data[10]
        shared_data.last_time_telemetry = time.time()
        if shared_data.printtele: print(f"Battery: {shared_data.vbat:0.2f}V {shared_data.curr:0.1f}A {shared_data.mah}mAh {shared_data.pct}%")

    elif ptype == PacketsTypes.BARO_ALT:
        shared_data.baro_alt = int.from_bytes(data[3:7], byteorder='big', signed=True) / 100.0
        shared_data.last_time_telemetry = time.time()
        if shared_data.printtele: print(f"Baro Altitude: {shared_data.baro_alt}m")

    elif ptype == PacketsTypes.DEVICE_INFO:
        packet = ' '.join(map(hex, data))
        shared_data.last_time_telemetry = time.time()
        if shared_data.printtele: print(f"Device Info: {packet}")

    elif data[2] == PacketsTypes.GPS:
        shared_data.got_gps = True
        shared_data.pos_uav.lat = int.from_bytes(data[3:7], byteorder='big', signed=True) / 1e7
        shared_data.pos_uav.lon = int.from_bytes(data[7:11], byteorder='big', signed=True) / 1e7
        shared_data.gspd = int.from_bytes(data[11:13], byteorder='big', signed=True) / 36.0
        shared_data.hdg =  int.from_bytes(data[13:15], byteorder='big', signed=True) / 100.0
        shared_data.pos_uav.alt = int.from_bytes(data[15:17], byteorder='big', signed=True) - 1000
        shared_data.sats = data[17]
        shared_data.last_time_telemetry = time.time()
        if shared_data.printtele: print(f"GPS: Pos={shared_data.latitude} {shared_data.longitude} GSpd={shared_data.gspd:0.1f}m/s Hdg={shared_data.hdg:0.1f} Alt={shared_data.alt}m Sats={shared_data.sats}")

    elif ptype == PacketsTypes.VARIO:
        shared_data.vspd = int.from_bytes(data[3:5], byteorder='big', signed=True) / 10.0
        shared_data.last_time_telemetry = time.time()
        if shared_data.printtele: print(f"VSpd: {shared_data.vspd:0.1f}m/s")

    elif ptype == PacketsTypes.RC_CHANNELS_PACKED:
        #print(f"Channels: (data)")
        pass

    else:
        packet = ' '.join(map(hex, data))
        print(f"Unknown 0x{ptype:02x}: {packet}")


def crsf_telemetry(app):

    with serial.Serial(shared_data.telem_port, shared_data.telem_baud, timeout=2) as ser:
        input_buffer = bytearray()
        while True:
            if ser.in_waiting > 0:
                input_buffer.extend(ser.read(ser.in_waiting))
            else:
                time.sleep(0.020)

            while len(input_buffer) > 2:
                # This simple parser works with malformed CRSF streams
                # it does not check the first byte for SYNC_BYTE, but
                # instead just looks for anything where the packet length
                # is 4-64 bytes, and the CRC validates
                expected_len = input_buffer[1] + 2
                if expected_len > 64 or expected_len < 4:
                    input_buffer = bytearray()
                elif len(input_buffer) >= expected_len:
                    single = input_buffer[:expected_len] # copy out this whole packet
                    input_buffer = input_buffer[expected_len:] # and remove it from the buffer

                    if not crsf_validate_frame(single): # single[-1] != crc:
                        packet = ' '.join(map(hex, single))
                        print(f"crc error: {packet}")
                    else:
                        handleCrsfPacket(single[2], single)
                else:
                    break

def dummy_telemetry(app):
    while True:
        shared_data.flightmode = "ANGLE" if random.random() > 0.5 else "HORIZON"
        shared_data.speed = random.randint(100, 300)
        shared_data.pitch = random.uniform(-1, 1)
        shared_data.roll = random.uniform(-1, 1)
        shared_data.pos_uav.lat += random.uniform(-0.001, 0.001)  # Update latitude
        shared_data.pos_uav.lon += random.uniform(-0.001, 0.001)  # Update longitude
        shared_data.pos_uav.alt += random.randint(1, 2)
        shared_data.baro_alt = shared_data.pos_uav.alt
        shared_data.vbat -= 0.01
        shared_data.mah = round(5000.0 * (((shared_data.vbat/shared_data.scells)-3.5) / 0.7),1)
        shared_data.pct = round(100.0 * (((shared_data.vbat/shared_data.scells)-3.5) / 0.7),2)
        shared_data.yaw += random.randint(-5, 5)
        shared_data.lq = random.randint(0, 100)
        shared_data.rssi1 = random.uniform(-110, -10)
        shared_data.last_time_telemetry = time.time()
        time.sleep(1)

def start_data_thread(app):
    if shared_data.telemetry == "random":
        threading.Thread(target=dummy_telemetry, args=(app,), daemon=True).start()
        shared_data.video_source = "video.mp4"
        shared_data.pos_uav.lat = 36.52982407028365
        shared_data.pos_uav.lon = -83.21680266631701
        shared_data.pos_uav.alt = random.randint(50, 500)
        shared_data.vbat = 12.6
        shared_data.mah = 5000.0
        shared_data.pct = 100
        shared_data.got_gps = True

    elif shared_data.telemetry == "crsf":
        threading.Thread(target=crsf_telemetry, args=(app,), daemon=True).start()
