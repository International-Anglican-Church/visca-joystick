import platform
import os
import time

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame
from visca_over_ip import Camera
from visca_over_ip.exceptions import ViscaException
from numpy import interp


print('Pan & Tilt: Left stick | Invert tilt: Click left stick')
print('Zoom: Right stick | Toggle manual focus: Click right stick')
print('Brightness: Up: Right Trigger, Down: Left Trigger')
print('Select camera 1: X, 2: ◯, 3: △')
print('Exit: Options')

SENSITIVITY = {
    'pan_tilt': {'joy': [0, 0.07, 0.3, .9, 1], 'cam': [0, 0, 2, 12, 24]},
    'zoom': {'joy': [0, 0.1, 1], 'cam': [0, 0, 7]},
    'focus': {'joy': [0, 0.1, 0.11, 0.85, 1], 'cam': [0, 0, 1, 1, 2]}
}

ips = [f'172.16.0.20{idx}' for idx in range(1, 4)]

mappings = {
    'cam_select': {1: 0, 2: 1, 3: 2},
    'movement': {'pan': 0, 'tilt': 1, 'zoom': 5, 'focus': 2},
    'brightness': {'up': 7, 'down': 6},
    'other': {'exit': 9, 'invert_tilt': 10, 'configure': 3, 'manual_focus': 11}
}
if platform.system() != 'Linux':
    mappings['other'] = {'exit': 6, 'invert_tilt': 7, 'configure': 3, 'manual_focus': 8}
    mappings['movement']['zoom'] = 3
    mappings['movement']['focus'] = 2
    mappings['brightness'] = {'up': 10, 'down': 9}
    mappings['cam_select'] = {0: 0, 1: 1, 3: 2}

camera_index = 0
invert_tilt = True
cam = None
joystick = None
joystick_reset_time = None
manual_focus = [False] * len(ips)


def joystick_init():
    global joystick, joystick_reset_time

    pygame.joystick.quit()
    pygame.display.quit()

    pygame.display.init()
    pygame.joystick.init()
    joystick = pygame.joystick.Joystick(0)

    joystick_reset_time = time.time() + 120


def joy_pos_to_cam_speed(axis_position: float, sensitivity_mapping: dict, invert=True) -> int:
    sign = 1 if axis_position >= 0 else -1
    if invert:
        sign *= -1

    return sign * round(
        interp(abs(axis_position), sensitivity_mapping['joy'], sensitivity_mapping['cam'])
    )


def configure():
    global cam

    print('Press triangle to configure cameras or any other button to skip')
    while not pygame.event.peek(eventtype=pygame.JOYBUTTONDOWN):
        time.sleep(0.05)

    event = pygame.event.get(eventtype=pygame.JOYBUTTONDOWN)[0]
    if event.dict['button'] == mappings['other']['configure']:
        print(f'Configuring...')

        for ip in ips:
            cam = Camera(ip)
            cam.set_power(True)
            cam._sock.close()

        time.sleep(20)

        for ip in ips:
            cam = Camera(ip)
            cam.recall_preset(8)
            cam._sock.close()

        time.sleep(2)
        cam = None


def shut_down():
    global cam
    if cam is not None:
        cam._sock.close()

    print('Press triangle to shut down cameras or any other button to leave them on')
    while not pygame.event.peek(eventtype=pygame.JOYBUTTONDOWN):
        time.sleep(0.05)

    event = pygame.event.get(eventtype=pygame.JOYBUTTONDOWN)[0]
    if event.dict['button'] == mappings['other']['configure']:
        for ip in ips:
            cam = Camera(ip)
            cam.set_power(False)
            cam._sock.close()

    exit(0)


joystick_init()
configure()


while True:
    button_presses = pygame.event.get(eventtype=pygame.JOYBUTTONDOWN)

    update_cam = False
    for event in button_presses:
        btn_no = event.dict['button']
        if btn_no == mappings['other']['exit']:
            shut_down()

        elif btn_no in mappings['brightness']:
            brightness_direction = mappings['brightness'][btn_no]

        elif btn_no in mappings['cam_select']:
            update_cam = True
            camera_index = mappings['cam_select'][btn_no]

        elif btn_no == mappings['other']['manual_focus']:
            manual_focus[camera_index] = not manual_focus[camera_index]
            if manual_focus[camera_index] is True and cam is not None:
                cam.focus_mode('manual')
                print('Manual focus')

            elif manual_focus[camera_index] is False and cam is not None:
                cam.focus_mode('auto')
                print('Auto focus')

        elif btn_no == mappings['other']['invert_tilt']:
            invert_tilt = not invert_tilt
            print('Tilt', 'inverted' if not invert_tilt else 'not inverted')

    if update_cam or cam is None:
        if cam:
            cam.zoom(0)
            cam.pantilt(0, 0)
            cam._sock.close()

        cam = Camera(ips[camera_index])

        try:
            cam.zoom(0)
        except ViscaException:
            pass

        print(f"Camera {camera_index + 1}")

        update_cam = False

    if joystick.get_button(mappings['brightness']['up']):
        cam.increase_exposure_compensation()

    if joystick.get_button(mappings['brightness']['down']):
        cam.decrease_exposure_compensation()

    cam.pantilt(
        pan_speed=joy_pos_to_cam_speed(
            joystick.get_axis(mappings['movement']['pan']),
            SENSITIVITY['pan_tilt']),
        tilt_speed=joy_pos_to_cam_speed(
            joystick.get_axis(mappings['movement']['tilt']),
            SENSITIVITY['pan_tilt'], invert_tilt)
    )
    time.sleep(0.03)
    cam.zoom(joy_pos_to_cam_speed(joystick.get_axis(mappings['movement']['zoom']), SENSITIVITY['zoom']))

    if manual_focus[camera_index]:
        time.sleep(0.03)
        cam.manual_focus(joy_pos_to_cam_speed(joystick.get_axis(mappings['movement']['focus']), SENSITIVITY['focus']))

    if time.time() >= joystick_reset_time:
        joystick_init()
