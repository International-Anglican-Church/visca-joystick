import time

import pygame
from visca_over_ip import Camera
from numpy import interp

pygame.display.init()
pygame.joystick.init()

print('Pan & Tilt: Left stick | Invert tilt: Click left stick')
print('Select camera 1: X, 2: O, 3: △')
print('Exit: Options')

SENSITIVITY = [
    [0, 0.07, 0.3, .8, 1],
    [0, 0, 2, 12, 24]
]

j = pygame.joystick.Joystick(0)
ips = [f'172.16.0.20{idx}' for idx in range(1, 4)]
camera_mappings = {1: 0, 2: 1, 3: 2}
camera_index = 0

invert_tilt = True

NUM_AXES = 12
axes_state = {idx: 0 for idx in range(NUM_AXES)}


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
        if btn_no == 9:
            exit(0)

        elif btn_no in camera_mappings:
            update_cam = True
            camera_index = camera_mappings[btn_no]

        elif btn_no == 10:
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


    events = pygame.event.get(eventtype=pygame.JOYAXISMOTION)

    for event in events:
        axes_state[event.dict['axis']] = event.value

    cam.pantilt(
        pan_speed=get_pantilt_speed(axes_state[0]),
        tilt_speed=get_pantilt_speed(axes_state[1], invert_tilt)
    )
    time.sleep(0.07)

    cam.zoom(round(-7 * axes_state[5]))
    time.sleep(0.07)
