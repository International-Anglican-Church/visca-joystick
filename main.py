import time

import pygame
from visca_over_ip import Camera
from numpy import interp

pygame.display.init()
pygame.joystick.init()

SENSITIVITY = [
    [0, .8, 1],
    [0, 12, 24]
]

j = pygame.joystick.Joystick(0)
ips = [f'172.16.0.20{idx}' for idx in range(1, 4)]
camera_index = 0

NUM_AXES = 12
axes_state = {idx: 0 for idx in range(NUM_AXES)}


def get_pantilt_speed(axis_position: float) -> int:
    sign = -1 if axis_position >= 0 else 1  # Invert

    return sign * round(
        interp(abs(axis_position), *SENSITIVITY)
    )


cam = None
while True:
    button_presses = pygame.event.get(eventtype=pygame.JOYBUTTONDOWN)

    update_cam = False
    for event in button_presses:
        if event.dict['button'] == 3:
            exit(0)

        if event.dict['button'] == 5:
            update_cam = True
            camera_index += 1
        if event.dict['button'] == 3:
            update_cam = True
            camera_index -= 1

    if update_cam or cam is None:
        if camera_index >= len(ips):
            camera_index = 0
        if camera_index < 0:
            camera_index = len(ips) - 1

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

    for axis, value in axes_state.items():
        if abs(value) < .05:
            axes_state[axis] = 0

    cam.pantilt(
        pan_speed=get_pantilt_speed(axes_state[0]),
        tilt_speed=get_pantilt_speed(axes_state[1])
    )
    time.sleep(0.07)

    cam.zoom(round(-7 * axes_state[5]))
    time.sleep(0.07)
