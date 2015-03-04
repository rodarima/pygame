import sys, pygame, time
import pyganim
from pympler import asizeof
from pygame import gfxdraw

class Recording():
	""" Records events for auto-play """
	def __init__(self):
		self.start_time = time.perf_counter()
		self.events = []
		self.last_get = 0.0

	def event(self, e):
		tup = (self.diff_time, e)
		self.events.append(tup)
		print("Record event:" + str(tup))

	def new_frame(self):
		self.diff_time = time.perf_counter() - self.start_time
	
	def print(self):
		print(asizeof.asizeof(self.events)/len(self.events))
		for e in self.events:
			print(e)
	
	def get_all(self):
		return [e[1] for e in self.events]

	def play(self):
		self.play_start = time.perf_counter()
		self.last_get = 0.0

	def get(self):
		start_get = self.last_get
		end_get = time.perf_counter() - self.play_start
		self.last_get = end_get
#		print("start:"+str(start_get))
#		print("end:"+str(end_get))

		# "Premature optimization is the root of all evil" - Donald Knuth
		#return [e[1] for e in self.events if e[0] >= start_get e[0] < end_get]
		start = -1
		end = -1
		for i in range(len(self.events)):
			e = self.events[i]
			if(e[0] > end_get and i == 0): break
			if(e[0] >= start_get and start == -1):
#				print("Got start:" + str(i))
				start = i
			if(e[0] > end_get and end == -1):
#				print("Got end:" + str(i))
				end = i
			if(start != -1 and end != -1):
				break

#		print(str(start) + " -> " + str(end))
		el = []
		for e in self.events[start:end]:
			print("Replay event:" + str(e))
			el.append(e[1])
		return el

class SpriteT(pygame.sprite.Sprite):
	
	def __init__(self, t):
		pygame.sprite.Sprite.__init__(self);
		self.last_time = t
		self.vx = 0.0
		self.vy = 0.0
		self.rx = 0.0
		self.ry = 0.0

	def set_velocity(self, vx, vy):
		#Ignore last velocity?
		self.vx = vx
		self.vy = vy
	
	def set_position(self, x, y):
		self.x = x
		self.y = y

	def update_position(self, t):
		dif_t = t - self.last_time
		self.last_time = t
		self.rx += self.vx * dif_t
		self.ry += self.vy * dif_t

class Boy(SpriteT):
	def __init__(self, t):
		SpriteT.__init__(self, t)
		self.img = self.load_image("../img/boy2.gif")
		self.fr = 0
		self.frame(0)

	def load_image(self, f):
		img = pygame.image.load(f)
		img = img.convert()
		img.set_colorkey(img.get_at((0,0)), pygame.RLEACCEL)
		return img

	def frame(self, n):
		self.fr = (self.fr + n) % 13
		self.surf = self.img.subsurface(self.fr*13, 0, 13, 21)

	def event(self, e):
		if e.type == pygame.KEYDOWN:
			if e.key == pygame.K_LEFT: self.vx = -1
			elif e.key == pygame.K_RIGHT: self.vx = 1
			elif e.key == pygame.K_UP: self.vy = 1
			elif e.key == pygame.K_DOWN: self.vy = -1
		elif e.type == pygame.KEYUP:
			if e.key == pygame.K_LEFT: self.vx = 0
			elif e.key == pygame.K_RIGHT: self.vx = 0
			elif e.key == pygame.K_UP: self.vy = 0
			elif e.key == pygame.K_DOWN: self.vy = 0

	def update(self, t):
		self.update_position(t)
		self.frame(self.vx)
		screen.blit(self.surf, (self.rx, -self.ry, 13, 21))

		
	
		

pygame.init()

size = width, height = 320, 240
speed = [2, 2]
black = 0, 0, 0
n = False

screen = pygame.display.set_mode(size)

#boy = pygame.image.load("../img/boy2.gif")
#boy.set_colorkey((0,0,0))
#boy = boy.subsurface(0, 0, 13, 21)
#x = 30
#y = 30
#dx = 0
#dy = 0
fr = 0
boy = Boy(fr)
use_record = 0

clock = pygame.time.Clock()
recording = Recording()
while 1:

	if use_record: source_events = recording.get()
	else:
		source_events = pygame.event.get()
		recording.new_frame()
	

	for event in source_events:
		if event.type == pygame.QUIT:
			sys.exit()
		elif event.type == pygame.KEYDOWN:
			if(not use_record and event.key != pygame.K_SPACE):
				recording.event(event)
		elif event.type == pygame.KEYUP:
			if(not use_record and event.key != pygame.K_SPACE):
				recording.event(event)
			if event.key == pygame.K_SPACE:
				recording.print()
				use_record = not use_record
				recording.play()
				x = 30
				y = 30
		boy.event(event)

	screen.fill((0,0,0))

	#floor1 = pygame.Surface((200, 1))
	#pygame.draw.line(floor1, (255,255,255), (0, 0), (200, 0), 1)
	#screen.blit(floor1, (0, 50, 200, 1))

	boy.update(fr)
	pygame.display.update()
	pygame.display.flip()

	clock.tick(30)
	fr += 1



