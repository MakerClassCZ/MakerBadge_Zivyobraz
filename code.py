
import displayio
import wifi
import socketpool
import adafruit_requests
import os
import time
from mb_setup import setup, get_battery
import alarm
import microcontroller

(display, touch, led_matrix, colors) = setup()

# Connect to WiFi
wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))

print("Conencted:", wifi.radio.ap_info.ssid)

rssi = wifi.radio.ap_info.rssi
mac_addr = ":".join([f"{i:02x}" for i in wifi.radio.mac_address])

battery_voltage = get_battery()
print("Battery voltage: ", battery_voltage)

URL = f"http://cdn.zivyobraz.eu/index.php?mac={mac_addr}&timestamp_check=1&rssi={rssi}&v={battery_voltage}&x={display.width}&y={display.height}&c=BW&fw=1"

def parse_bmp(bmp_data):

    if bmp_data[:2] != b'BM':
        print(bmp_data[:50])
        # temporary fix
        if bmp_data[:4] == b'Nepl':
            print("Fix invalid BMP header")
            bmp_data = bmp_data[12:]            
        else:
            return displayio.Bitmap(1, 1, 1)

    image_offset = int.from_bytes(bmp_data[10:14], 'little')
    
    width = int.from_bytes(bmp_data[18:22], 'little')
    height = int.from_bytes(bmp_data[22:26], 'little')
    
    padding = (4 - ((width // 8) % 4)) % 4
    
    image_bitmap = displayio.Bitmap(width, height, 2)

    data_pointer = image_offset
    for y in range(height - 1, -1, -1):  # Start from the bottom row
        for x in range(width // 8):  # 1 byte = 8 pixels
            if data_pointer < len(bmp_data):
                byte = bmp_data[data_pointer]
                
                mask = 0b10000000
                for bit in range(8):
                    j = y * width + x * 8 + bit
                    if j < width * height:
                        image_bitmap[j] = (byte & mask) >> (7 - bit)
                    mask >>= 1

                data_pointer += 1
        data_pointer += padding

    return image_bitmap

  
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool)

print("zivyobraz URL:", URL)
resp = requests.get(URL)

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

    bitmap = parse_bmp(resp.content)
    palette = displayio.Palette(2)
    palette[0] = 0x000000
    palette[1] = 0xFFFFFF

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


