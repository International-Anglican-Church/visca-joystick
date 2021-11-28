import platform
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame
from visca_over_ip import Camera
from visca_over_ip.exceptions import ViscaException
from numpy import interp

pygame.display.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)

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
    'brightness': {'up': 7, 'down': 6},
    'other': {'exit': 9, 'invert_tilt': 10}
}
if platform.system() != 'Linux':
    mappings['other'] = {'exit': 6, 'invert_tilt': 7}
    mappings['movement']['zoom'] = 3
    mappings['brightness'] = {'up': 10, 'down': 9}
    mappings['cam_select'] = {0: 0, 1: 1, 3: 2}

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
            cam.zoom(0)
            cam.pantilt(0, 0)
            cam._sock.close()

        cam = Camera(ips[camera_index])
        print(f"Camera {camera_index + 1}")

        try:
            cam.zoom(0)
        except ViscaException:
            pass

        update_cam = False

    if joystick.get_button(mappings['brightness']['up']):
        cam.increase_exposure_compensation()

    if joystick.get_button(mappings['brightness']['down']):
        cam.decrease_exposure_compensation()

    cam.pantilt(
        pan_speed=get_pantilt_speed(joystick.get_axis(mappings['movement']['pan'])),
        tilt_speed=get_pantilt_speed(joystick.get_axis(mappings['movement']['tilt']), invert_tilt)
    )

    cam.zoom(round(-7 * joystick.get_axis(mappings['movement']['zoom'])))
