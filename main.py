import os
import time

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame
from visca_over_ip.exceptions import ViscaException
from numpy import interp

from config import ips, mappings, sensitivity_tables, help_text, Camera, long_press_time
from startup_shutdown import shut_down, configure


invert_tilt = True
cam = None
joystick = None
joystick_reset_time = None
last_focus_time = None
button_down_time = {key: None for key in mappings['preset']}


def joystick_init(print_battery=False):
    """Initializes pygame and the joystick.
    This is done occasionally because pygame seems to put the controller to sleep otherwise
    :param print_battery: If set to True, the battery charge status of the joystick will be printed out
    """
    global joystick, joystick_reset_time

    pygame.joystick.quit()
    pygame.display.quit()

    pygame.display.init()
    pygame.joystick.init()
    joystick = pygame.joystick.Joystick(0)

    if print_battery:
        print('Joystick battery is', joystick.get_power_level())

    joystick_reset_time = time.time() + 20


def joy_pos_to_cam_speed(axis_position: float, table_name: str, invert=True) -> int:
    """Converts from a joystick axis position to a camera speed using the given mapping

    :param axis_position: the raw value of an axis of the joystick -1 to 1
    :param table_name: one of the keys in sensitivity_tables
    :param invert: if True, the sign of the output will be flipped
    :return: an integer which can be fed to a Camera driver method
    """
    sign = 1 if axis_position >= 0 else -1
    if invert:
        sign *= -1

    table = sensitivity_tables[table_name]

    return sign * round(
        interp(abs(axis_position), table['joy'], table['cam'])
    )


def update_focus():
    """Reads the state of the bumpers and toggles manual focus, focuses near, or focuses far."""
    global last_focus_time
    time_since_last_adjust = time.time() - last_focus_time if last_focus_time else 30

    focus_near = joystick.get_button(mappings['focus']['near'])
    focus_far = joystick.get_button(mappings['focus']['far'])
    manual_focus = cam.get_focus_mode() == 'manual'

    if focus_near and focus_far and time_since_last_adjust > .4:
        last_focus_time = time.time()
        if manual_focus:
            cam.set_focus_mode('auto')
            print('Auto focus')
        else:
            cam.set_focus_mode('manual')
            print('Manual focus')

    elif focus_far and manual_focus and time_since_last_adjust > .1:
        last_focus_time = time.time()

        cam.manual_focus(-1)
        time.sleep(.01)
        cam.manual_focus(0)

    elif focus_near and manual_focus and time_since_last_adjust > .1:
        last_focus_time = time.time()

        cam.manual_focus(1)
        time.sleep(.01)
        cam.manual_focus(0)


def update_brightness():
    if joystick.get_axis(mappings['brightness']['up']) > .9:
        cam.increase_exposure_compensation()

    if joystick.get_axis(mappings['brightness']['down']) > .9:
        cam.decrease_exposure_compensation()


def connect_to_camera(cam_index) -> Camera:
    """Connects to the camera specified by cam_index and returns it"""
    global cam

    if cam:
        cam.zoom(0)
        cam.pantilt(0, 0)
        cam.close_connection()

    cam = Camera(ips[cam_index])

    try:
        cam.zoom(0)
    except ViscaException:
        pass

    print(f"Camera {cam_index + 1}")

    return cam


def handle_button_presses():
    global invert_tilt, cam

    for event in pygame.event.get(eventtype=pygame.JOYBUTTONDOWN):
        btn_no = event.dict['button']
        if btn_no == mappings['other']['exit']:
            shut_down(cam)

        elif btn_no in mappings['cam_select']:
            cam = connect_to_camera(mappings['cam_select'][btn_no])

        elif btn_no == mappings['other']['invert_tilt']:
            invert_tilt = not invert_tilt
            print('Tilt', 'inverted' if not invert_tilt else 'not inverted')


def handle_preset_buttons():
    """Distinguishes between short presses and long presses for recalling and saving presets"""
    global cam, button_down_time

    for event in pygame.event.get(eventtype=pygame.JOYBUTTONUP):
        btn_no = event.dict['button']

        if btn_no in mappings['preset']:
            cam.recall_preset(mappings['preset'][btn_no])

    for btn_no in mappings['preset']:
        if joystick.get_button(btn_no):
            if button_down_time[btn_no] is None:
                button_down_time[btn_no] = time.time()

            elif time.time() - button_down_time[btn_no] > long_press_time:
                cam.save_preset(mappings['preset'][btn_no])

        else:
            button_down_time[btn_no] = None


def main_loop():
    while True:
        handle_button_presses()
        update_brightness()
        update_focus()
        handle_preset_buttons()

        cam.pantilt(
            pan_speed=joy_pos_to_cam_speed(joystick.get_axis(mappings['movement']['pan']), 'pan'),
            tilt_speed=joy_pos_to_cam_speed(joystick.get_axis(mappings['movement']['tilt']), 'tilt', invert_tilt)
        )
        time.sleep(0.03)
        cam.zoom(joy_pos_to_cam_speed(joystick.get_axis(mappings['movement']['zoom']), 'zoom'))

        if time.time() >= joystick_reset_time:
            joystick_init()


if __name__ == "__main__":
    print(help_text)
    joystick_init(print_battery=True)
    configure()
    cam = connect_to_camera(0)

    while True:
        try:
            main_loop()

        except Exception as exc:
            print(exc)
