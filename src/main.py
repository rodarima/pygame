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
		self.play_offset = 0.0

	def event(self, e):
		tup = (self.diff_time, e)
		self.events.append(tup)
#		print("Record event:" + str(tup))

	def new_frame(self):
		self.diff_time = time.perf_counter() - self.start_time
	
	def print(self):
		print(asizeof.asizeof(self.events)/len(self.events))
		for e in self.events:
			print(e)
	
	def get_all(self):
		return [e[1] for e in self.events]

	def play(self, t):
		self.play_start = t
		self.last_get = t

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
			if(e[0] < end_get and start != -1):
#				print("Got end:" + str(i))
				end = i
			if(e[0] >= end_get and start != -1):
				break
			#if(start != -1 and end != -1):
			#	break

#		print(str(start) + " -> " + str(end))
		el = []
		for e in self.events[start:end+1]:
#			print("Replay event:" + str(e))
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
		self.mod_velocity = 1.0

	def set_time(self, t):
		self.last_time = t
	def set_velocity(self, vx, vy):
		#Ignore last velocity?
		self.vx = vx
		self.vy = vy

	def set_mod_velocity(self, mod_velocity):
		self.mod_velocity = mod_velocity
	
	def set_position(self, rx, ry):
		self.rx = rx
		self.ry = ry

	def update_position(self, t):
		dif_t = t - self.last_time
		print("dif_t:" + str(dif_t))
		self.last_time = t
		self.rx += self.vx * dif_t
		self.ry += self.vy * dif_t

	def load_image(self, f):
		img = pygame.image.load(f)
		img = img.convert()
		img.set_colorkey(img.get_at((0,0)), pygame.RLEACCEL)
		return img

class Boy(SpriteT):
	def __init__(self, t):
		SpriteT.__init__(self, t)
		self.img = self.load_image("../img/boy2.gif")
		self.fr = 0.0
		self.fps = 30
		self.rx = 106
		self.ry = 110
		self.disabled = False
		self.frame(0)

	def frame(self, n):
		self.fr = (self.fr + n) % 13
		self.surf = self.img.subsurface(self.fr*13, 0, 13, 21)
		self.rect = pygame.Rect(self.rx, self.ry, 13, 21)

	def event(self, e):
		if(self.disabled): return
		if e.type == pygame.KEYDOWN:
			if e.key == pygame.K_LEFT: self.vx = -1
			elif e.key == pygame.K_RIGHT: self.vx = 1
			elif e.key == pygame.K_UP: self.vy = -1
			elif e.key == pygame.K_DOWN: self.vy = 1
		elif e.type == pygame.KEYUP:
			if e.key == pygame.K_LEFT: self.vx = 0
			elif e.key == pygame.K_RIGHT: self.vx = 0
			elif e.key == pygame.K_UP: self.vy = 0
			elif e.key == pygame.K_DOWN: self.vy = 0

	def update(self, t):
		if(self.disabled): return
		self.update_position(t*self.fps)
		self.frame(self.vx)
		screen.blit(self.surf, (self.rx, self.ry, 13, 21))
		#print("x:"+str(self.rx)+" y:"+str(self.ry))

	def disable(self):
		self.disabled = True
	def enable(self):
		self.disabled = False

MACHINE_OFF = 0
MACHINE_TIMER0 = 1
MACHINE_TIMER1 = 2
MACHINE_ON = 3

class Machine(SpriteT):

	def __init__(self, t):
		SpriteT.__init__(self, t)
		self.img = self.load_image("../img/machine.gif")
		self.mx = 100
		self.my = 100
		self.imgx = 0
		self.imgy = 0
		self.imgw = 22
		self.imgh = 32
		self.img_frames = 4
		self.img_frame = 0
		self.state = MACHINE_OFF
		self.timer_time = 2.0
		self.timer_step = 0.5
		self.timer_start = 0.0
		self.action = 0
		self.rect = pygame.Rect(self.mx, self.my, self.imgw, self.imgh)
		
		self.frame()

	def frame(self):
		self.surf = self.img.subsurface(
			self.state * self.imgw + self.imgx,
			self.imgy,
			self.imgw,
			self.imgh)

#	def event(self, e):
#		if e.type == pygame.USEREVENT and e.name == 'action':
#			if self.state == MACHINE_OFF:
#				self.action = 1
	
	def event(self):
		if self.state == MACHINE_OFF:
			self.action = 1

	def program(self, t):
		self.timer_start = t
		self.state = MACHINE_TIMER0

	def update_timer(self, t):
		dif_t = t - self.timer_start
		#print(dif_t)
		if dif_t > self.timer_time:
			self.poweron()
		else:
			inc = int(dif_t / self.timer_step) % 2
			self.state = MACHINE_TIMER0 + inc

	def poweron(self):
		self.state = MACHINE_ON
		print("Machine powered on")

	def update(self, t):
		if(self.action and self.state == MACHINE_OFF):
			self.action = 0
			self.program(t)
		if(self.state in (MACHINE_TIMER0, MACHINE_TIMER1)):
			self.update_timer(t)
		self.frame()
		screen.blit(self.surf, (self.mx, self.my, self.imgw, self.imgh))
		
	
		

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
machine = Machine(fr)
use_record = False

clock = pygame.time.Clock()
recording = Recording()
saved_pos = (0,0)
saved_vel = (0,0)
saved_time = 0
saved = False
while 1:
	t = time.perf_counter()
	
	

	if use_record:
		for event in recording.get():
			if event.type == pygame.KEYDOWN:
				if(event.key == pygame.K_e):
					if(pygame.sprite.collide_rect(boy1, machine)):
						machine.event()
			boy1.event(event)
	else: recording.new_frame()
	
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			sys.exit()
		elif event.type == pygame.KEYDOWN:
			if(not use_record and event.key != pygame.K_SPACE):
				recording.event(event)
			if(event.key == pygame.K_e):
				if(pygame.sprite.collide_rect(boy, machine)):
					machine.event()
		elif event.type == pygame.KEYUP:
			if(not use_record and event.key != pygame.K_SPACE):
				recording.event(event)
			if(not use_record and event.key == pygame.K_SPACE):
				recording.print()
				use_record = True
				recording.play(saved_time)
				boy.set_position(106,110)
				boy.set_velocity(0,0)
				machine.state = MACHINE_OFF
				boy1 = Boy(t)
				boy1.rx = saved_pos[0]
				boy1.ry = saved_pos[1]
				# TODO: Reparar velocidad al aparecer de nuevo
				#boy1.vx = saved_vel[0]
				#boy1.vy = saved_vel[1]
				#boy.disable()
		boy.event(event)

	screen.fill((0,0,0))

	#floor1 = pygame.Surface((200, 1))
	#pygame.draw.line(floor1, (255,255,255), (0, 0), (200, 0), 1)
	#screen.blit(floor1, (0, 50, 200, 1))
	if use_record:
		boy1.update(t)
		#if machine.state == MACHINE_ON:
		#	boy.enable()
	elif machine.state == MACHINE_ON and not saved:
		print("Time saved:" + str(t))
		saved = True
		saved_pos = (boy.rx, boy.ry)
		saved_vel = (boy.vx, boy.vy)
		saved_time = t
	boy.update(t)
	#boy.update(fr)
	machine.update(t)
	pygame.display.update()
	pygame.display.flip()

	clock.tick(30)
	fr += 1



