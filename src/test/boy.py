import sys, pygame
pygame.init()

size = width, height = 640, 480
speed = [2, 2]
black = 0, 0, 0
n = False

screen = pygame.display.set_mode(size)

boy = pygame.image.load("boy2.gif")
boy.set_colorkey((0,0,0))
machine = pygame.image.load("machine.gif")
machine.set_colorkey((0,0,0))
palanca = pygame.image.load("palanca.gif")
palanca.set_colorkey((0,0,0))

x = 0
anim = 0
fr = 0
t = 0
xw = 10
d = 0
_d = 0
o = 1
p = 0
fp = 0
m = 0
fm = 0
clock = pygame.time.Clock()
while 1:

    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                n = True
            elif event.key == pygame.K_RIGHT:
                d = 1
            elif event.key == pygame.K_LEFT:
                d = -1
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_RIGHT:
                d = 0
            elif event.key == pygame.K_LEFT:
                d = 0
    if d != 0: _d = d

    if d != 0:
        xw = (xw + d -200) % 200 +200
        fr = (fr + 1) % 13
    else:
        fr = 0

    if n and xw > 350 and xw < 390:
        p ^= 1
    
    if n and xw > 300 and xw < 320:
        m ^= 1
    
    
    if p:
        if fp < 8: fp += 1
    else:
        if fp > 0: fp -= 1
    
    if m:
        if fm < 3: fm += 1
    else:
        if fm > 0: fm -= 1

    n = False

    screen.fill(black)
    screen.blit(machine.subsurface(fm*22, 0, 22, 32), (320, 240-32, 22, 32))
    screen.blit(palanca.subsurface(fp*13, 0, 13, 13), (320+50, 240-13-1, 13, 13))
    boy2 = boy.subsurface(13*fr, 0, 13, 21)
    if _d == -1: boy2 = pygame.transform.flip(boy2, True, False)

    screen.blit(boy2, (xw, 240-21-1, 13, 21))
    pygame.display.flip()
    clock.tick(30)
