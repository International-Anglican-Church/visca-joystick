import platform
import os
import time

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame
from visca_over_ip import Camera
from visca_over_ip.exceptions import ViscaException
from numpy import interp


print('Pan & Tilt: Left stick | Invert tilt: Click left stick')
print('Zoom: Right stick')
print('Brightness: Up: Right trigger, Down: Left trigger')
print('Manual focus: Left and right bumpers')
print('Select camera 1: X, 2: ◯, 3: △')
print('Exit: Options')

SENSITIVITY = {
    'pan_tilt': {'joy': [0, 0.07, 0.3, .9, 1], 'cam': [0, 0, 2, 12, 24]},
    'zoom': {'joy': [0, 0.07, 1], 'cam': [0, 0, 7]},
}

ips = [f'172.16.0.20{idx}' for idx in range(1, 4)]

mappings = {
    'cam_select': {1: 0, 2: 1, 3: 2},
    'movement': {'pan': 0, 'tilt': 1, 'zoom': 5, 'focus': 2},
    'brightness': {'up': 7, 'down': 6},
    'focus': {'near': 4, 'far': 5},
    'other': {'exit': 9, 'invert_tilt': 10, 'configure': 3}
}
if platform.system() != 'Linux':
    mappings['other'] = {'exit': 6, 'invert_tilt': 7, 'configure': 3}
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
    """Initializes pygame and the joystick.
    This is done occasionally because pygame seems to put the controller to sleep otherwise
    """
    global joystick, joystick_reset_time

    pygame.joystick.quit()
    pygame.display.quit()

    pygame.display.init()
    pygame.joystick.init()
    joystick = pygame.joystick.Joystick(0)

    joystick_reset_time = time.time() + 120


def joy_pos_to_cam_speed(axis_position: float, table_name: str, invert=True) -> int:
    """Converts from a joystick axis position to a camera speed using the given mapping

    :param axis_position: the raw value of an axis of the joystick -1 to 1
    :param table_name: one of the keys in the SENSITIVITY table
    :param invert: if True, the sign of the output will be flipped
    :return: an integer which can be fed to a Camera driver method
    """
    sign = 1 if axis_position >= 0 else -1
    if invert:
        sign *= -1

    table = SENSITIVITY[table_name]

    return sign * round(
        interp(abs(axis_position), table['joy'], table['cam'])
    )


def configure():
    """Allows the user to configure the cameras or skip this step
    If the user chooses to configure the cameras, they are powered on and preset 9 is recalled
    """
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
    """Shuts down the program.
    The user is asked if they want to shut down the cameras as well.
    """
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


def update_focus():
    """Reads the state of the bumpers and toggles manual focus, focuses near, or focuses far."""
    focus_near = joystick.get_button(mappings['focus']['near'])
    focus_far = joystick.get_button(mappings['focus']['far'])

    if focus_near and focus_far:
        manual_focus[camera_index] = not manual_focus[camera_index]
        if manual_focus[camera_index]:
            cam.focus_mode('manual')
            print('Manual focus')
        else:
            cam.focus_mode('auto')
            print('Auto focus')

    elif focus_far and manual_focus[camera_index]:
        cam.manual_focus(-1)
    elif focus_near and manual_focus[camera_index]:
        cam.manual_focus(1)
    elif manual_focus[camera_index]:
        cam.manual_focus(0)


def connect_to_camera(cam_index: int) -> Camera:
    """Connects to the camera specified by cam_index and returns it"""
    global cam

    if cam:
        cam.zoom(0)
        cam.pantilt(0, 0)
        cam._sock.close()

    cam = Camera(ips[cam_index])

    try:
        cam.zoom(0)
    except ViscaException:
        pass

    print(f"Camera {cam_index + 1}")

    return cam


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

        elif btn_no == mappings['other']['invert_tilt']:
            invert_tilt = not invert_tilt
            print('Tilt', 'inverted' if not invert_tilt else 'not inverted')

    if update_cam or cam is None:
        cam = connect_to_camera(camera_index)
        update_cam = False

    if joystick.get_button(mappings['brightness']['up']):
        cam.increase_exposure_compensation()

    if joystick.get_button(mappings['brightness']['down']):
        cam.decrease_exposure_compensation()

    update_focus()

    cam.pantilt(
        pan_speed=joy_pos_to_cam_speed(joystick.get_axis(mappings['movement']['pan']), 'pan_tilt'),
        tilt_speed=joy_pos_to_cam_speed(joystick.get_axis(mappings['movement']['tilt']), 'pan_tilt', invert_tilt)
    )
    time.sleep(0.03)
    cam.zoom(joy_pos_to_cam_speed(joystick.get_axis(mappings['movement']['zoom']), 'zoom'))

    if time.time() >= joystick_reset_time:
        joystick_init()
