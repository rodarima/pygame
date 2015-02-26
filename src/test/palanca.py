import sys, pygame
pygame.init()

size = width, height = 640, 480
speed = [2, 2]
black = 0, 0, 0
n = False

screen = pygame.display.set_mode(size)

machine = pygame.image.load("palanca.gif").convert()
machine.set_colorkey((0,0,0))
x = 0
anim = 0
fr = 0
clock = pygame.time.Clock()
while 1:

    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                n = True

    if n and (anim == 0):
        anim = 1
    elif n and (anim == 2):
        anim = 3

    n = False

    if anim == 1:
        if fr < 8:
            fr += 1
        else:
            fr = 8
            anim = 2
    elif anim == 3:
        if fr > 0:
            fr -= 1
        else:
            fr = 0
            anim = 0


    screen.fill(black)
    screen.blit(machine.subsurface(13*fr, 0, 13, 13), (320, 240, 13, 13))
    pygame.display.flip()
    clock.tick(30)
