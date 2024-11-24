import os
import time

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

from visca_over_ip.exceptions import ViscaException
from numpy import interp

from config import ips, sensitivity_tables, Camera
from startup_shutdown import shut_down, configure
from controller import GameController, ButtonFunction, AxisFunction


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


last_focus_time = None

def update_focus(controller: GameController, camera: Camera):
    """Reads the state of the bumpers and toggles manual focus, focuses near, or focuses far."""
    global last_focus_time
    time_since_last_adjust = time.time() - last_focus_time if last_focus_time else 30

    focus_near = controller.is_button_pressed(ButtonFunction.FOCUS_NEAR)
    focus_far = controller.is_button_pressed(ButtonFunction.FOCUS_FAR)
    manual_focus = camera.get_focus_mode() == 'manual'

    if focus_near and focus_far and time_since_last_adjust > .4:
        last_focus_time = time.time()
        if manual_focus:
            camera.set_focus_mode('auto')
            print('Auto focus')
        else:
            camera.set_focus_mode('manual')
            print('Manual focus')

    elif focus_far and manual_focus and time_since_last_adjust > .1:
        last_focus_time = time.time()

        camera.manual_focus(-1)
        time.sleep(.01)
        camera.manual_focus(0)

    elif focus_near and manual_focus and time_since_last_adjust > .1:
        last_focus_time = time.time()

        camera.manual_focus(1)
        time.sleep(.01)
        camera.manual_focus(0)


def connect_to_camera(cam_index, current_camera=None) -> Camera:
    """Connects to the camera specified by cam_index and returns it"""
    if current_camera:
        current_camera.zoom(0)
        current_camera.pantilt(0, 0)
        current_camera.close_connection()

    camera = Camera(ips[cam_index])

    try:
        camera.zoom(0)
    except ViscaException:
        pass

    print(f"Camera {cam_index + 1}")

    return camera


def main_loop(controller: GameController, camera: Camera):
    invert_tilt = False

    while True:
        for pressed_button in controller.get_button_presses():
            if pressed_button == ButtonFunction.EXIT:
                shut_down(controller, camera)

            elif pressed_button.value in ButtonFunction.CAM_SELECTS.value:
                camera = connect_to_camera(pressed_button.value, current_camera=camera)

            elif pressed_button == ButtonFunction.INVERT_TILT:
                invert_tilt = not invert_tilt
                print('Tilt', 'inverted' if not invert_tilt else 'not inverted')

        update_focus(controller, camera)

        for short_press in controller.get_button_short_presses():
            if short_press.value in ButtonFunction.PRESETS.value:
                camera.recall_preset(short_press.value)

        for long_press in controller.get_button_long_presses():
            if long_press.value in ButtonFunction.PRESETS.value:
                camera.save_preset(long_press.value)

        if controller.get_axis(AxisFunction.BRIGHTNESS_UP) > .9:
            camera.increase_exposure_compensation()

        if controller.get_axis(AxisFunction.BRIGHTNESS_DOWN) > .9:
            camera.decrease_exposure_compensation()

        camera.pantilt(
            pan_speed=joy_pos_to_cam_speed(controller.get_axis(AxisFunction.PAN), 'pan'),
            tilt_speed=joy_pos_to_cam_speed(controller.get_axis(AxisFunction.TILT), 'tilt', not invert_tilt)
        )
        time.sleep(0.03)
        camera.zoom(joy_pos_to_cam_speed(controller.get_axis(AxisFunction.ZOOM), 'zoom'))


if __name__ == "__main__":
    print('Welcome to VISCA Joystick!')
    cont = GameController()

    while True:
        try:
            configure(cont)
            cam = connect_to_camera(0)
            break
        except Exception as exc:
            print(exc)
            print('Initialization error. Check that all network equipment is connected and powered on.')
            input('Press enter to retry: ')

    cont.print_mappings()

    while True:
        try:
            main_loop(cont, cam)

        except Exception as exc:
            print(exc)
