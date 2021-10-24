import time

import pygame
from visca_over_ip import Camera

pygame.display.init()
pygame.joystick.init()

j = pygame.joystick.Joystick(0)
cam = Camera('172.16.0.203')

NUM_AXES = 12
axes_state = {idx: 0 for idx in range(NUM_AXES)}


while True:
    if any(event.dict['button'] == 3 for event in pygame.event.get(eventtype=pygame.JOYBUTTONDOWN)):
        exit(0)

    events = pygame.event.get(eventtype=pygame.JOYAXISMOTION)

    for event in events:
        axes_state[event.dict['axis']] = event.value

    for axis, value in axes_state.items():
        if abs(value) < .05:
            axes_state[axis] = 0

    cam.pantilt(
        pan_speed=round(-24 * axes_state[0]),
        tilt_speed=round(-24 * axes_state[1])
    )
