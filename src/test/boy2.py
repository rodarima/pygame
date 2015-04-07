import sys, pygame
from pygame import gfxdraw

pygame.init()

size = width, height = 640, 480

boy_head = 10

screen = pygame.display.set_mode(size)

clock = pygame.time.Clock()
W = (255,255,255)
while 1:
	screen.fill((0,0,0))

	boy = pygame.Surface((100,100))
	#Head
	gfxdraw.aaellipse(boy, 50, 50, 5, 6, W)
	gfxdraw.vline(boy, 50, 50+6, 50+6+3, W)
	gfxdraw.aaellipse(boy, 50, 50+6+10+3, 5, 10, W)
	gfxdraw.vline(boy, 50, 50+6, 50+6+3, W)

	screen.blit(boy, (50, 50, 50, 50))
	pygame.display.flip()
	clock.tick(30)
