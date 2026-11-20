
#!/usr/bin/env python3
import subprocess, os, sys, json, time
from PIL import Image
from datetime import datetime

BRIDGE_URL = 'http://172.18.0.1:9000/snapshot.jpg'
FRAME_DIR = '/home/spark/frames'
LOG_FILE = '/home/spark/automation/automation.log'
os.makedirs(FRAME_DIR, exist_ok=True)
os.makedirs('/home/spark/automation', exist_ok=True)

def grab_frame():
    path = os.path.join(FRAME_DIR, f'{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg')
    try:
        r = subprocess.run(['curl', '-s', '-o', path, BRIDGE_URL], capture_output=True, timeout=5)
        if r.returncode == 0 and os.path.getsize(path) > 100:
            return path
        return None
    except:
        return None

def analyze_frame(frame_path):
    img = Image.open(frame_path)
    img = img.convert('RGB')
    width, height = img.size
    pixels = img.load()
    total_r, total_g, total_b, count = 0, 0, 0, 0
    for y in range(0, height, 4):
        for x in range(0, width, 4):
            r, g, b = pixels[x, y]
            total_r += r
            total_g += g
            total_b += b
            count += 1
    avg_r = total_r / count
    avg_g = total_g / count
    avg_b = total_b / count
    brightness = (avg_r + avg_g + avg_b) / 3 / 255.0
    ui_pixels = 0
    for y in range(0, height, 4):
        for x in range(0, width, 4):
            r, g, b = pixels[x, y]
            if r > 200 or g > 200 or b > 200:
                ui_pixels += 1
    ui_ratio = ui_pixels / count
    is_dark = brightness < 0.3
    has_ui = ui_ratio > 0.05
    return {
        'brightness': round(brightness, 2),
        'ui_ratio': round(ui_ratio, 3),
        'is_dark': is_dark,
        'has_ui': has_ui,
        'avg_color': (round(avg_r), round(avg_g), round(avg_b)),
        'dimensions': f'{width}x{height}'
    }

def send_input(keys):
    for key in keys:
        subprocess.run(['xdotool', 'keydown', key], capture_output=True)
        time.sleep(0.05)
    for key in keys:
        subprocess.run(['xdotool', 'keyup', key], capture_output=True)

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def navigate(direction):
    key_map = {'up': 'Up', 'down': 'Down', 'left': 'Left', 'right': 'Right', 'enter': 'Return', 'escape': 'Escape'}
    key = key_map.get(direction.lower(), direction)
    log(f'Navigating: {direction}')
    send_input([key])
    time.sleep(0.5)

def game_loop():
    log('Automation framework started')
    log(f'Bridge: {BRIDGE_URL}')
    counter = 0
    print('=== GTA 6 AUTOMATION ===')
    print('Commands: up, down, left, right, enter, escape, screenshot, status, quit')
    while True:
        try:
            frame = grab_frame()
            if frame:
                counter += 1

                info = analyze_frame(frame)
                print(f'\n[Frame {counter}] {info["dimensions"]} | Bright: {info["brightness"]} | UI: {info["ui_ratio"]}')
                if info['is_dark'] and not info['has_ui']:
                    print('  State: Dark/Gameplay')
                elif info['has_ui']:
                    print('  State: Menu UI detected')
                else:
                    print('  State: Light screen')
                cmd = input('>>> ').strip().lower()
                if cmd in ['up', 'down', 'left', 'right', 'enter', 'escape']:
                    navigate(cmd)
                elif cmd == 'screenshot':
                    print(f'  Latest: {frame}')
                elif cmd == 'status':
                    print(f'  {json.dumps(info, indent=2)}')
                elif cmd == 'quit':
                    break
                else:
                    print(f'  Unknown: {cmd}')
            else:
                print(f'  Frame {counter}: FAILED')
        except KeyboardInterrupt:
            print('\nStopped')
            break

if name == 'main':
    game_loop()
