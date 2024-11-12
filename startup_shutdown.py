import time

from visca_over_ip import Camera

from config import ips
from controller import GameController, ButtonFunction


def configure(controller: GameController):
    """Allows the user to configure the cameras or skip this step
    If the user chooses to configure the cameras, they are powered on and preset 9 is recalled
    """
    print(f'Press {controller.get_button_name(ButtonFunction.CONFIRM)} to configure cameras or any other button to skip')
    if controller.wait_for_button_press() == ButtonFunction.CONFIRM:
        print(f'Configuring...')

        for ip in ips:
            cam = Camera(ip)
            cam.set_power(True)
            cam.close_connection()

        time.sleep(20)

        for ip in ips:
            cam = Camera(ip)
            cam.recall_preset(8)
            cam.close_connection()

        time.sleep(2)


def shut_down(controller: GameController, current_camera: Camera):
    """Shuts down the program.
    The user is asked if they want to shut down the cameras as well.
    """
    if current_camera is not None:
        current_camera.close_connection()

    print(f'Press {controller.get_button_name(ButtonFunction.CONFIRM)} to shut down cameras or any other button to leave them on')
    if controller.wait_for_button_press() == ButtonFunction.CONFIRM:
        for ip in ips:
            cam = Camera(ip)
            cam.set_power(False)
            cam.close_connection()

    exit(0)
