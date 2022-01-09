import platform

from visca_over_ip import CachingCamera as Camera
# from visca_over_ip import Camera

num_cams = 3

sensitivity_tables = {
    'pan_tilt': {'joy': [0, 0.07, 0.3, .9, 1], 'cam': [0, 0, 2, 12, 24]},
    'zoom': {'joy': [0, 0.07, 1], 'cam': [0, 0, 7]},
}

ips = [f'172.16.0.20{idx + 1}' for idx in range(num_cams)]

if platform.system() == 'Linux':
    mappings = {
        'cam_select': {1: 0, 2: 1, 3: 2},
        'movement': {'pan': 0, 'tilt': 1, 'zoom': 5},
        'brightness': {'up': 4, 'down': 3},
        'focus': {'near': 4, 'far': 5},
        'other': {'exit': 9, 'invert_tilt': 10, 'configure': 3}
    }
else:
    mappings = {
        'cam_select': {0: 0, 1: 1, 3: 2},
        'movement': {'pan': 0, 'tilt': 1, 'zoom': 3},
        'brightness': {'up': 4, 'down': 5},
        'focus': {'near': 4, 'far': 5},
        'other': {'exit': 6, 'invert_tilt': 7, 'configure': 3}
    }


help_text = """Pan & Tilt: Left stick | Invert tilt: Click left stick'
Zoom: Right stick
Brightness: Up: Right trigger, Down: Left trigger
Manual focus: Left and right bumpers
Select camera 1: X, 2: ◯, 3: △
Exit: Options"""
