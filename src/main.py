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
	""" Almacena la velocidad y posición de un Sprite """
	def __init__(self, t):
		pygame.sprite.Sprite.__init__(self);
		self.last_time = t
		self.vx = 0.0
		self.vy = 0.0
		self.rx = 0.0
		self.ry = 0.0

	def set_time(self, t):
		self.last_time = t
	def set_velocity(self, vx, vy):
		#XXX: Ignore last velocity?
		self.vx = vx
		self.vy = vy
	
	def set_position(self, rx, ry):
		self.rx = rx
		self.ry = ry
		self.rect.left = rx
		self.rect.bottom = ry

	def update_position(self, t):
		dif_t = t - self.last_time
		#print("dif_t:" + str(dif_t))
		self.last_time = t
		self.rx += self.vx * dif_t
		self.ry += self.vy * dif_t
		self.rect.left = self.rx
		self.rect.bottom = self.ry

	def load_image(self, f):
		img = pygame.image.load(f)
		img = img.convert()
		#img.set_colorkey(img.get_at((0,0)), pygame.RLEACCEL)
		return img

class BlockState():

	def __init__(self):
		self.obj_block = -1
	
	def block(self, obj):
		self.obj_block = obj

	def unblock(self):
		self.obj_block = -1

	def blocked(self):
		return (self.obj_block != -1)

	def is_blocked_by(self, n):
		return (self.obj_block == n)

class Boy(SpriteT):
	def __init__(self, t, eventd, cam):
		SpriteT.__init__(self, t)
		self.img = self.load_image("../img/boy2.gif")
		self.eventd = eventd
		self.fr = 0.0
		self.fps = 1
		#self.rx = 106
		#self.ry = 110
		self.disabled = False
		self.i = -1
		self.cam = cam
		self.rect = pygame.Rect((0,0), (13, 21))
		self.frame(0)

	def frame(self, n):
		self.fr = (self.fr + n) % 13
		self.surf = self.img.subsurface(self.fr*13, 0,
			self.rect.w, self.rect.h)
		#self.rect = pygame.Rect(self.rx, self.ry, 13, 21)

	def do_action(self, e):
		self.eventd.event(e)

	def event(self, e, from_obj):
		if(from_obj != None): return False
		if(self.disabled): return False
		print('Boy'+str(self.i)+' event '+ str(e) +' from ' +str(from_obj))
		if e.type == pygame.KEYDOWN:
			if e.key == pygame.K_LEFT: self.vx = -1
			elif e.key == pygame.K_RIGHT: self.vx = 1
			elif e.key == pygame.K_DOWN: self.vy = -1
			elif e.key == pygame.K_UP: self.vy = 1
			elif e.key == pygame.K_SPACE: self.eventd.event(e, self)
		elif e.type == pygame.KEYUP:
			if e.key == pygame.K_LEFT: self.vx = 0
			elif e.key == pygame.K_RIGHT: self.vx = 0
			elif e.key == pygame.K_DOWN: self.vy = 0
			elif e.key == pygame.K_UP: self.vy = 0
			elif e.key == pygame.K_SPACE: self.eventd.event(e, self)
		return True

	def _draw_axis(self):
		w, h = screen.get_size()
		#cx, cy = self.cam.get_position()
		#pyx = w-cx
		#pyy = h-cy
		pos = self.cam.get_screen_position(0,0)
		pygame.draw.line(pygame.display.get_surface(),
			(255,0,0), (pos[0], 0), (pos[0], h), 1)
		pygame.draw.line(pygame.display.get_surface(),
			(255,0,0), (0, pos[1]), (w, pos[1]), 1)
		

	def update(self, t):
		if(self.disabled): return
		#print('Boy update')
		self.update_position(t * self.fps)
		self.frame(self.vx)
		self.cam.update()
		#w, h = screen.get_size()
		abs_pos = (self.rx, self.ry)
		rel_pos = self.cam.get_relative_position(self.rx, self.ry)
		scr_pos = self.cam.get_screen_position(self.rx, self.ry)
		#print('Boy rect: ' + str(self.rect))
		
		print('Boy absolute position ' + str(abs_pos))
		print('Boy relative position ' + str(rel_pos))
		print('Boy screen position ' + str(scr_pos))

		self._draw_axis()
		
		r = self.rect
		#r.left += cx
		#r.bottom += cy
		r.bottomleft = scr_pos
		screen.blit(self.surf, r)
		#print("x:"+str(self.rx)+" y:"+str(self.ry))

	def disable(self):
		self.disabled = True
	def enable(self):
		self.disabled = False

MACHINE_OFF = 0
MACHINE_TIMER0 = 1
MACHINE_TIMER1 = 2
MACHINE_ON = 3

class Machine(SpriteT, BlockState):

	def __init__(self, t, eventd, cam):
		SpriteT.__init__(self, t)
		BlockState.__init__(self)
		self.img = self.load_image("../img/machine.gif")
		self.eventd = eventd
		self.imgx = 0
		self.imgy = 0
		self.imgw = 22
		self.imgh = 32
		self.img_frames = 4
		self.img_frame = 0
		self.state = MACHINE_OFF
		self.timer_time = 10.0
		self.timer_step = 0.5
		self.timer_start = 0.0
		self.action = 0
		self.rect = pygame.Rect((0,0), (self.imgw, self.imgh))
		self.i = -1
		self.cam = cam
		
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
	
	def event(self, e, from_obj):
		print('Machine event from ' + str(from_obj.i))
		if not ((e.type == pygame.KEYDOWN) and (e.key == pygame.K_SPACE)):
			return False
		if(self.blocked() == False):
			self.block(from_obj.i)
			if self.state == MACHINE_OFF:
				self.action = 1
				return True
		elif self.is_blocked_by(from_obj.i):
			print('Unblocking machine from ' + str(from_obj.i))
			self.unblock()
			self.poweroff()
			return True

		return False

	def program(self, t):
		print("Machine programming")
		self.timer_start = t
		self.state = MACHINE_TIMER0

	def update_timer(self, t):
		dif_t = t - self.timer_start
		#print(dif_t)
		if dif_t > self.timer_time:
			self.poweron()
		else:
			inc = int(1 + dif_t / self.timer_step) % 2
			self.state = MACHINE_TIMER0 + inc

	def poweron(self):
		self.state = MACHINE_ON
		print("Machine powered on")

	def poweroff(self):
		self.state = MACHINE_OFF
		print("Machine powered off")

	def update(self, t):
		#print('Machine update')
		if(self.action and self.state == MACHINE_OFF):
			self.action = 0
			self.program(t)
		if(self.state in (MACHINE_TIMER0, MACHINE_TIMER1)):
			self.update_timer(t)
		self.frame()
		print('Machine rect: ' + str(self.rect))
		if self.blocked():
			pygame.draw.rect(self.surf, (255,0,0), (0, 0,
				self.imgw, self.imgh), 1)

		scr_pos = self.cam.get_screen_position(self.rx, self.ry)
		#rect = pygame.Rect(self.rx + cx, self.ry + cy, self.imgw, self.imgh)
		r = self.rect
		r.bottomleft = scr_pos
		screen.blit(self.surf, r)

class Event:
	def __init__(self, position, e):
		self.position = position
		self.e = e

class EventControl:
	def __init__(self, t):
		self.raw_events = []
		self.key_events = []
		self.now = t

	def _update(self, now):
		#print('EventControl updated')
		self.raw_events = pygame.event.get()
		self.now = now

	def _filter_key_events(self):
		for e in self.raw_events:
			if e.type in (pygame.KEYDOWN, pygame.KEYUP):
				self.key_events.append(e)

	def get_keyboard(self):
		self.key_events = []
		self._filter_key_events()
		#if(self.key_events != []):
		#	print(self.key_events)
		return self.key_events

	def dispatch(self, t):
		#print('EventControl dispatched')
		self._update(t)
		self._filter_key_events()
		for e in self.raw_events:
			if e.type == pygame.QUIT:
				print('Exiting')
				sys.exit()


class EventDaemon:

	def __init__(self, event_control, om):
		self.eventlist = []
		self.event_control = event_control
		self.active_boy = None
		self.object_manager = om

	def event(self, e, obj_from):
		self.eventlist.append((e, obj_from))

	def get(self):
		l = self.eventlist
		self.eventlist = []
		return l

	def set_active_boy(self, boy):
		self.active_boy = boy

	def _dispatch_keyboard(self):
		if(self.active_boy == None): return
		
		for event in self.event_control.get_keyboard():
			self.active_boy.event(event, None)

	def dispatch(self, t):
		#print('EventDaemon dispatched')
		self.event_control.dispatch(t)
		self._dispatch_keyboard()
		for elem in self.get():
			e = elem[0]
			from_obj = elem[1]
			l = self.object_manager.collide(from_obj)
			for obj in l:
				print('Sending event to:' + str(obj))
				if obj.event(e, from_obj) == True: break

class ObjectManager:
	"""Permite encontrar objetos por la posicion"""
	def __init__(self):
		self.objects = [] #pygame.sprite.Group()
		self.i = 0

	def add(self, obj):
		obj.i = self.i
		self.i += 1
		self.objects.append(obj)

	def collide(self, obj):
		return pygame.sprite.spritecollide(obj, self.objects, False)

	def update(self, t):
		#TODO: Actualizar primero el personaje activo
		for obj in self.objects:
			#print('Updating object: ' + str(obj))
			obj.update(t)

class Camera:
	def __init__(self):
		self.obj = None
		self.screen_size = screen.get_size()
		self.camera = (0, 0)

	def follow(self, obj):
		self.obj = obj

	def update(self):
		if self.obj == None: return

		w, h = screen.get_size()
		wm = w/2
		hm = h/2
		#El personaje ha de estar en el centro de la pantalla
		wb, hb = self.obj.rect.size
		rx = self.obj.rx
		ry = self.obj.ry
		
		#print('Camera obj position '+str((self.obj.rx, self.obj.ry)))
		#print('Camera obj relative to '+str(self.obj_coord))
		#print('Camera screen center '+str((wm, hm)))
		cx = wm - rx - wb/2
		cy = hm - ry - hb/2

		self.camera = (int(cx), int(cy))
		print('Camera update '+str(self.camera))


	def get_relative_position(self, rx, ry):
		return (rx+self.camera[0], ry+self.camera[1])
	
	def get_screen_position(self, rx, ry):
		w, h = screen.get_size()
		return (rx+self.camera[0], h-(ry+self.camera[1]))


pygame.init()
screen = pygame.display.set_mode((320, 240))

def main():
	#t = time.perf_counter()
	frame = 0
	t = frame
	clock = pygame.time.Clock()
	om = ObjectManager()
	eventctrl = EventControl(t)
	eventd = EventDaemon(eventctrl, om)
	camera = Camera()
	
	m0 = Machine(t, eventd, camera)
	m0.set_position(50, 0)
	om.add(m0)
	
	b0 = Boy(t, eventd, camera)
	b0.set_position(0, 0)
	om.add(b0)

	camera.follow(b0)
	eventd.set_active_boy(b0)

	while True:
		#print("-- Loop start --")

		#t = time.perf_counter()
		t = frame
		
		screen.fill((100, 100, 100))
		eventd.dispatch(t)
		om.update(t)
		pygame.display.update()
		pygame.display.flip()
		
		#print("-- Loop end --")
		
		clock.tick(30)
		frame += 1

if __name__ == '__main__':
	main()

#pygame.init()
#
#size = width, height = 320, 240
#speed = [2, 2]
#black = 0, 0, 0
#n = False
#
#screen = pygame.display.set_mode(size)
#
##boy = pygame.image.load("../img/boy2.gif")
##boy.set_colorkey((0,0,0))
##boy = boy.subsurface(0, 0, 13, 21)
##x = 30
##y = 30
##dx = 0
##dy = 0
#fr = 0
#boy = Boy(fr)
#machine = Machine(fr)
#use_record = False
#
#clock = pygame.time.Clock()
#recording = Recording()
#saved_pos = (0,0)
#saved_vel = (0,0)
#saved_time = 0
#saved = False
#
#eventd = EventDaemon
#
#while 1:
#	t = time.perf_counter()
#	
#	
#
#	if use_record:
#		for event in recording.get():
#			if event.type == pygame.KEYDOWN:
#				if(event.key == pygame.K_e):
#					if(pygame.sprite.collide_rect(boy1, machine)):
#						machine.event()
#			boy1.event(event)
#	else: recording.new_frame()
#	
#	for event in pygame.event.get():
#		if event.type == pygame.QUIT:
#			sys.exit()
#		elif event.type == pygame.KEYDOWN:
#			if(not use_record and event.key != pygame.K_SPACE):
#				recording.event(event)
#			if(event.key == pygame.K_e):
#				if(pygame.sprite.collide_rect(boy, machine)):
#					machine.event()
#		elif event.type == pygame.KEYUP:
#			if(not use_record and event.key != pygame.K_SPACE):
#				recording.event(event)
#			if(not use_record and event.key == pygame.K_SPACE):
#				recording.print()
#				use_record = True
#				recording.play(saved_time)
#				boy.set_position(106,110)
#				boy.set_velocity(0,0)
#				machine.state = MACHINE_OFF
#				boy1 = Boy(t)
#				boy1.rx = saved_pos[0]
#				boy1.ry = saved_pos[1]
#				# TODO: Reparar velocidad al aparecer de nuevo
#				#boy1.vx = saved_vel[0]
#				#boy1.vy = saved_vel[1]
#				#boy.disable()
#		boy.event(event)
#
#	screen.fill((0,0,0))
#
#	#floor1 = pygame.Surface((200, 1))
#	#pygame.draw.line(floor1, (255,255,255), (0, 0), (200, 0), 1)
#	#screen.blit(floor1, (0, 50, 200, 1))
#	if use_record:
#		boy1.update(t)
#		#if machine.state == MACHINE_ON:
#		#	boy.enable()
#	elif machine.state == MACHINE_ON and not saved:
#		print("Time saved:" + str(t))
#		saved = True
#		saved_pos = (boy.rx, boy.ry)
#		saved_vel = (boy.vx, boy.vy)
#		saved_time = t
#	boy.update(t)
#	#boy.update(fr)
#	machine.update(t)
#	pygame.display.update()
#	pygame.display.flip()
#
#	clock.tick(30)
#	fr += 1
#


