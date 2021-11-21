import platform
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame
from visca_over_ip import Camera
from numpy import interp

pygame.display.init()
pygame.joystick.init()
j = pygame.joystick.Joystick(0)

print('Pan & Tilt: Left stick | Invert tilt: Click left stick')
print('Zoom: Right stick')
print('Brightness: Up: Right Trigger, Down: Left Trigger')
print('Select camera 1: X, 2: ◯, 3: △')
print('Exit: Options')

SENSITIVITY = [
    [0, 0.07, 0.3, .9, 1],
    [0, 0, 2, 12, 24]
]

ips = [f'172.16.0.20{idx}' for idx in range(1, 4)]

mappings = {
    'cam_select': {1: 0, 2: 1, 3: 2},
    'movement': {'pan': 0, 'tilt': 1, 'zoom': 5},
    'brightness': {7: 1, 6: -1},
    'other': {'exit': 9, 'invert_tilt': 10}
}
if platform.system() != 'Linux':
    mappings['other']['exit'] = 6
    mappings['movement']['zoom'] = 3

NUM_AXES = 12
axes_state = {idx: 0 for idx in range(NUM_AXES)}
brightness_direction = 0

camera_index = 0
invert_tilt = True

def get_pantilt_speed(axis_position: float, invert=True) -> int:
    sign = 1 if axis_position >= 0 else -1
    if invert:
        sign *= -1

    return sign * round(
        interp(abs(axis_position), *SENSITIVITY)
    )


cam = None
while True:
    button_presses = pygame.event.get(eventtype=pygame.JOYBUTTONDOWN)

    update_cam = False
    for event in button_presses:
        btn_no = event.dict['button']
        if btn_no == mappings['other']['exit']:
            exit(0)

        elif btn_no in mappings['brightness']:
            brightness_direction = mappings['brightness'][btn_no]

        elif btn_no in mappings['cam_select']:
            update_cam = True
            camera_index = mappings['cam_select'][btn_no]

        elif btn_no == mappings['other']['invert_tilt']:
            invert_tilt = not invert_tilt
            print('Tilt', 'inverted' if not invert_tilt else 'not inverted')

    if update_cam or cam is None:
        if cam:
            cam.zoom_stop()
            cam.pantilt_stop()
            cam._sock.close()

        cam = Camera(ips[camera_index])
        print(f"Camera {camera_index + 1}")

        update_cam = False

    if any(event.dict['button'] in mappings['brightness'] for event in pygame.event.get(eventtype=pygame.JOYBUTTONUP)):
        brightness_direction = 0

    if brightness_direction == -1:
        cam.decrease_excomp()
    elif brightness_direction == 1:
        cam.increase_excomp()

    events = pygame.event.get(eventtype=pygame.JOYAXISMOTION)

    for event in events:
        axes_state[event.dict['axis']] = event.value

    cam.pantilt(
        pan_speed=get_pantilt_speed(axes_state[mappings['movement']['pan']]),
        tilt_speed=get_pantilt_speed(axes_state[mappings['movement']['tilt']], invert_tilt)
    )

    cam.zoom(round(-7 * axes_state[mappings['movement']['zoom']]))
