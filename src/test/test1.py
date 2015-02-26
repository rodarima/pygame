import sys, pygame
pygame.init()

size = width, height = 640, 480
speed = [2, 2]
black = 0, 0, 0
n = False

screen = pygame.display.set_mode(size)

machine = pygame.image.load("machine.gif").convert()
machine.set_colorkey((0,0,0))
x = 0
p = 0
fr = 0
t = 0
clock = pygame.time.Clock()
while 1:

    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                n = True

    if n:
        fr = 0
        n = False
        p = (p + 1) % 3


    fr += 1
    if p == 0:
        x = p*22
    elif p == 1:
        if t == 10:
            p = 2
            x = 3*22
            fr = 0
            t = 0
        else:
            if fr < 10:
                x = 1*22
            elif fr < 20:
                x = 2*22
            else:
                fr = 0
                t += 1
    elif p == 2:
        x = 3*22
        t = 0



    screen.fill(black)
    screen.blit(machine.subsurface(x, 0, 22, 32), (320, 240, 16, 32))
    pygame.display.flip()
    clock.tick(30)
