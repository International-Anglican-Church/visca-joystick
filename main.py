import pygame

pygame.display.init()
pygame.joystick.init()

j = pygame.joystick.Joystick(0)

NUM_AXES = 6
axes_state = {idx: 0 for idx in range(NUM_AXES)}

while True:
    events = pygame.event.get(eventtype=pygame.JOYBUTTONDOWN)
    if events:
        print('\nDown')
        print(events)

    events = pygame.event.get(eventtype=pygame.JOYAXISMOTION)

    for event in events:
        if abs(axes_state[event.dict['axis']] - event.value) > .01:
            print(event)

        axes_state[event.dict['axis']] = event.value



