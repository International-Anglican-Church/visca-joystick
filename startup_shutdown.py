import time

import pygame
from visca_over_ip import Camera

from config import mappings, ips


def configure():
    """Allows the user to configure the cameras or skip this step
    If the user chooses to configure the cameras, they are powered on and preset 9 is recalled
    """
    print('Press triangle to configure cameras or any other button to skip')
    while not pygame.event.peek(eventtype=pygame.JOYBUTTONDOWN):
        time.sleep(0.05)

    event = pygame.event.get(eventtype=pygame.JOYBUTTONDOWN)[0]
    if event.dict['button'] == mappings['other']['configure']:
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


def shut_down(current_camera: Camera):
    """Shuts down the program.
    The user is asked if they want to shut down the cameras as well.
    """
    if current_camera is not None:
        current_camera.close_connection()

    print('Press triangle to shut down cameras or any other button to leave them on')
    while not pygame.event.peek(eventtype=pygame.JOYBUTTONDOWN):
        time.sleep(0.05)

    event = pygame.event.get(eventtype=pygame.JOYBUTTONDOWN)[0]
    if event.dict['button'] == mappings['other']['configure']:
        for ip in ips:
            cam = Camera(ip)
            cam.set_power(False)
            cam.close_connection()

    exit(0)
