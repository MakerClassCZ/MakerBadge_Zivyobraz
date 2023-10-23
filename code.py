from mb_setup import setup, get_battery
import adafruit_requests
import displayio
import wifi
import socketpool
import os
import time
import alarm
import microcontroller

# zivyobraz API version
version = "2.0"

(display, touch, led_matrix, colors) = setup(touch_enable=False, led_enable=False)

# Connect to WiFi
wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))

print("Connected:", wifi.radio.ap_info.ssid)

rssi = wifi.radio.ap_info.rssi
mac_addr = ":".join([f"{i:02x}" for i in wifi.radio.mac_address])
print("MAC address: ", mac_addr)

battery_voltage = get_battery()
print("Battery voltage: ", battery_voltage)

URL = f"http://cdn.zivyobraz.eu/index.php?mac={mac_addr}&timestamp_check=1&rssi={rssi}&v={battery_voltage}&x={display.width}&y={display.height}&c=BW&fw={version}"

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool)

print("zivyobraz URL:", URL)
resp = requests.get(URL)

with requests.get(URL, stream=True) as resp:

    # Get headers
    try:
        sleep_time = int(resp.headers['sleep'])*60
        timestamp = int(resp.headers['timestamp'])
    except:
        sleep_time = 60*60
        timestamp = 0

    # Get previous timestamp from NVM
    bytes_timestamp = microcontroller.nvm[0:4]
    timestamp_old = int.from_bytes(bytes_timestamp, 'little')

    print(sleep_time, timestamp, timestamp_old)

    if timestamp != timestamp_old:

        print("New image available!")
        
        # Read header - image format
        chunk_size = 2
        chunk = b''
        while len(chunk) < chunk_size:
            chunk += resp.iter_content(chunk_size=chunk_size-len(chunk)).__next__()
        
        if chunk != b'Z2':
            if chunk == b'BM':
                print("For v1.0 BMP use old version")
            elif chunk == b'Z1':
                print("Z1 compression not supported yet")
            else:
                print("Unknown image format:", chunk)
        
        # Process image if it is Z2 RLE format    
        else:
            bitmap = displayio.Bitmap(display.width, display.height, 2)
            palette = displayio.Palette(2)
            palette[0] = colors['white']
            palette[1] = colors['black']

            # position in bitmap
            i = 0
            for chunk in resp.iter_content(chunk_size=512):
                for byte in chunk:
                    count = byte & 0b00111111
                    pixel_color = (byte & 0b11000000) >> 6
                    for _ in range(count):
                        bitmap[i] = pixel_color
                        i += 1

            tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
            group = displayio.Group()
            group.append(tile_grid)
            display.show(group)
            display.refresh()

            while display.busy:
                pass

        bytes_timestamp = timestamp.to_bytes(4, 'little')
        microcontroller.nvm[0:4] = bytes_timestamp

    else:
        print("No new image - doesn't refresh display")
    
time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleep_time)
print(f"Good night for {sleep_time}s!")
alarm.exit_and_deep_sleep_until_alarms(time_alarm)


