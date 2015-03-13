import sys, pygame, time
import pyganim
from pympler import asizeof
from pygame import gfxdraw

REC_RECORDING = 0
REC_PLAYING = 1
REC_STOPPED = 2

class Recording():
	""" Records events for auto-play """
	def __init__(self, t):
		self.start_time = t
		self.end_time = 0
		self.events = []
		self.last_start = 0.0
		self.play_start = 0
		self.play_end = 0
		self.play_offset = 0.0
		self.state = REC_RECORDING

	def event(self, e):
		if(self.state != REC_RECORDING): return
		tup = (self.diff_time, e)
		self.events.append(tup)
		print("Record event:" + str(tup))

	def new_frame(self, t):
		if(self.state != REC_RECORDING): return
		self.diff_time = t - self.start_time
		#print("Recording new frame, dif = " + str(self.diff_time))

	def print(self):
		#print(asizeof.asizeof(self.events)/len(self.events))
		for e in self.events:
			print(e)

	def get_all(self):
		return [e[1] for e in self.events]

	def play(self, play_start, play_end):
		print('Recording PLAY start = {0} end = {1}'.format(play_start,
			play_end))
		self.state = REC_PLAYING
		self.play_start = play_start
		self.play_end = play_end
		self.last_start = play_start
		self.print()

	def finish(self, t):
		self.state = REC_STOPPED
		self.end_time = t
		#TODO: Al terminar la grabación avisar a SVT

	def get(self, t):
		if(self.state != REC_PLAYING): return []
		#print('Recording GET')
		start_get = self.last_start
		end_get = self.play_start + (t - self.play_end)
		self.last_start = end_get
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

		#print(str(start) + " -> " + str(end))
		el = []
		for e in self.events[start:end+1]:
			print("Replay event:" + str(e))
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

	def update_position(self, t):
		dif_t = t - self.last_time
		if dif_t > 1:
			print("ERROR: dif_t:" + str(dif_t))
		self.last_time = t
		self.rx += self.vx * dif_t
		self.ry += self.vy * dif_t
		#print('SpriteT absolute position ' + str((self.rx, self.ry)))

	def send_to_time(self, from_time, to_time):
		self.last_time += (to_time - from_time)

	def load_image(self, f):
		img = pygame.image.load(f)
		img = img.convert()
		img.set_colorkey(img.get_at((0,0)), pygame.RLEACCEL)
		return img
	
	def update(self, t):
		scr_pos = self.cam.get_screen_position(self.rx, self.ry)
		self.rect.bottomleft = scr_pos

		label = terminus.render(str((self.rx, self.ry, self.last_time, t)), 1, (255,0,0))
		screen.blit(label, scr_pos)

		screen.blit(self.surf, self.rect)
	
	def clone(self):
		d = {}
		d['r'] = (self.rx, self.ry)
		d['v'] = (self.vx, self.vy)
		d['last_time'] = self.last_time
		return d

	def restore(self, d):
		self.rx, self.ry = d['r']
		self.vx, self.vy = d['v']
		self.last_time = d['last_time']

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

	def clone(self):
		d = {}
		d['block'] = self.obj_block
		return d
	
	def restore(self, d):
		self.obj_block = d['block']


class Boy(SpriteT):
	def __init__(self, t, eventd, cam, svt):
		SpriteT.__init__(self, t)
		self.img = self.load_image("../img/boy2.gif")
		self.eventd = eventd
		self.fr = 0.0
		self.fps = 1
		#self.rx = 106
		#self.ry = 110
		#self.disabled = False
		self.i = -1
		self.cam = cam
		self.rect = pygame.Rect((0,0), (13, 21))
		self.frame(0)
		self.svt = svt
		self.future_time = 0

	def activate(self, t):
		self.eventd.active_boy = self
		self.svt.new_boy(self, t)

	def frame(self, n):
		self.fr = (self.fr + n) % 13
		self.surf = self.img.subsurface(self.fr*13, 0,
			self.rect.w, self.rect.h)
		#self.rect = pygame.Rect(self.rx, self.ry, 13, 21)

	def do_action(self, e):
		self.eventd.event(e)

	def event(self, e, t, from_obj):
		if(from_obj != None): return False
		#if(self.disabled): return False
		#print('Boy'+str(self.i)+' event '+ str(e) +' from '
		#	+str(from_obj) + ' at ' + str(t))
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
		self.update_position(t)
		return True

	def _draw_axis(self):
		w, h = screen.get_size()
		#cx, cy = self.cam.get_position()
		#pyx = w-cx
		#pyy = h-cy
		pos = self.cam.get_screen_position(0,0)
		pygame.draw.line(pygame.display.get_surface(),
			(50,0,0), (pos[0], 0), (pos[0], h), 1)
		pygame.draw.line(pygame.display.get_surface(),
			(50,0,0), (0, pos[1]), (w, pos[1]), 1)

	def clone(self):
		d = {}
		d['fr'] = self.fr
		#d['BlockState'] = BlockState.clone(self)
		d['SpriteT'] = SpriteT.clone(self)
		return d

	def restore(self, d):
		self.fr = d['fr']
		#BlockState.restore(self, d['BlockState'])
		SpriteT.restore(self, d['SpriteT'])
		

	def update(self, t):
		#if(self.disabled): return
		#print('Boy update')
		self.update_position(t)
		self.frame(self.vx)
		self.cam.update()
		self._draw_axis()

		SpriteT.update(self, t)
		##w, h = screen.get_size()
		abs_pos = (self.rx, self.ry)
		#rel_pos = self.cam.get_relative_position(self.rx, self.ry)
		scr_pos = self.cam.get_screen_position(self.rx, self.ry)
		##print('Boy rect: ' + str(self.rect))
		#
		#print('Boy absolute position ' + str(abs_pos))
		#print('Boy relative position ' + str(rel_pos))
		#print('Boy screen position ' + str(scr_pos))

		#self._draw_axis()
		#
		#r = self.rect
		##r.left += cx
		##r.bottom += cy
		#r.bottomleft = scr_pos
		#screen.blit(self.surf, r)
		#print("x:"+str(self.rx)+" y:"+str(self.ry))

	#def disable(self):
	#	self.disabled = True
	#def enable(self):
	#	self.disabled = False

MACHINE_OFF = 0
MACHINE_TIMER0 = 1
MACHINE_TIMER1 = 2
MACHINE_ON = 3

class Machine(SpriteT, BlockState):

	def __init__(self, t, eventd, cam, svt):
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
		self.timer_time = 3.0 * 30
		self.timer_step = 0.5 * 30
		self.timer_start = 0.0
		self.action = 0
		self.rect = pygame.Rect((0,0), (self.imgw, self.imgh))
		self.i = -1
		self.cam = cam
		self.svt = svt
		self.t = t
		
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
	
	def event(self, e, t, from_obj):
		#print('Machine event from ' + str(from_obj.i) + ' at ' + str(t))
		if not ((e.type == pygame.KEYDOWN) and (e.key == pygame.K_SPACE)):
			return False
		if(self.blocked() == False):
			print('Machine blocking from ' + str(from_obj.i))
			self.block(from_obj.i)
			if self.state == MACHINE_OFF:
				self.action = 1
				return True
		elif self.is_blocked_by(from_obj.i):
			print('Machine unblocking from ' + str(from_obj.i))
			self.unblock()
			self.poweroff(from_obj)
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
			self.poweron(t)
		else:
			inc = int(1 + dif_t / self.timer_step) % 2
			self.state = MACHINE_TIMER0 + inc

	def poweron(self, t):
		self.state = MACHINE_ON
		#Crear un evento de encendido
		print("Machine powered on")
		self.svt.on(self, t)

	def poweroff(self, boy):
		self.state = MACHINE_OFF
		print("Machine powered off")
		if boy == self.eventd.active_boy:
			self.svt.off(self, self.t)

	def update(self, t):
		#print('Machine update')
		self.t = t
		if(self.action and self.state == MACHINE_OFF):
			self.action = 0
			self.program(t)
		if(self.state in (MACHINE_TIMER0, MACHINE_TIMER1)):
			self.update_timer(t)
		self.frame()
		#print('Machine rect: ' + str(self.rect))
		if self.blocked():
			pygame.draw.rect(self.surf, (100,0,0), (0, 0,
				self.imgw, self.imgh), 1)

		scr_pos = self.cam.get_screen_position(self.rx, self.ry)
		abs_pos = (self.rx, self.ry)
		
		#print('Machine screen position: ' + str(scr_pos))
		#print('Machine absolute position: ' + str(abs_pos))

		#rect = pygame.Rect(self.rx + cx, self.ry + cy, self.imgw, self.imgh)
		#r = self.rect
		#r.bottomleft = scr_pos
		#screen.blit(self.surf, r)
		self.update_position(t)
		SpriteT.update(self, t)

	def clone(self):
		d = {}
		d['state'] = self.state
		d['t'] = self.t
		d['timer_start'] = self.timer_start

		d['BlockState'] = BlockState.clone(self)
		d['SpriteT'] = SpriteT.clone(self)
		return d

	def restore(self, d):
		self.state = d['state']
		self.t = d['t']
		self.timer_start = d['timer_start']

		BlockState.restore(self, d['BlockState'])
		SpriteT.restore(self, d['SpriteT'])
		
		

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

	def set_svt(self, svt):
		self.svt = svt

	def event(self, e, obj_from):
		self.eventlist.append((e, obj_from))

	def get(self):
		l = self.eventlist
		self.eventlist = []
		return l

	def _dispatch_keyboard(self, t):
		if(self.active_boy == None): return
		
		for event in self.event_control.get_keyboard():
			self.active_boy.event(event, t, None)
			self.svt.key_event(event, t)

	def dispatch(self, t):
		#print('EventDaemon dispatched')
		self.event_control.dispatch(t)
		self._dispatch_keyboard(t)
		for elem in self.get():
			e = elem[0]
			from_obj = elem[1]
			l = self.object_manager.collide(from_obj)
			if l != []:
				print('Lista de objetos al colisionar: ' +
					str(l))
			for obj in l:
				print('Sending event to:' + str(obj))
				if obj.event(e, t, from_obj) == True: break
			

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
		#for o in self.objects:
		#	print(str(o.rect))
		return pygame.sprite.spritecollide(obj, self.objects, False)

	def update(self, t):
		#TODO: Actualizar primero el personaje activo
		
		for obj in self.objects:
			#print('Updating object: ' + str(obj))
			obj.update(t)

	def clone(self):
		d = {}
		l = []
		for obj in self.objects:
			l.append((obj, obj.clone()))
		d['l'] = l
		return d

	def restore(self, d):
		for t in d['l']:
			t[0].restore(t[1])
		


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
		#print('Camera update '+str(self.camera))


	def get_relative_position(self, rx, ry):
		return (rx+self.camera[0], ry+self.camera[1])
	
	def get_screen_position(self, rx, ry):
		w, h = screen.get_size()
		return (rx+self.camera[0], h-(ry+self.camera[1]))

# SVT = Sistema de viajes temporales
class SVT:
	def __init__(self, om, eventd, cam):
		self.recordlist = []
		self.clonelist = []
		self.om = om
		self.eventd = eventd
		self.cam = cam

	def find_machine(self, m):
		# FIXME: Y si existen varias copias para una misma máquina?
		for t in self.clonelist:
			if t[0] == m:
				return t


	def find_boy(self, boy):
		# FIXME: Y si existen varias grabaciones para un mismo personaje?
		for t in self.recordlist:
			if t[0] == boy:
				return t

	def on(self, machine, t):
		clone = self.om.clone()
		item = (machine, clone, t)
		self.clonelist.append(item)
		print('Lista de clones ' + str(self.clonelist))
	
	def off(self, machine, t):
		tm = self.find_machine(machine)
		tb = self.find_boy(self.eventd.active_boy)

		oldboy = tb[0]
		machine = tm[0]
		rec = tb[1]
		start = tm[2]

		rec.finish(t)
		rec.play(start, t)
		self.om.restore(tm[1])
		oldboy.send_to_time(start, t)
		print('Olb boy last_time ' + str(oldboy.last_time))
		oldboy.update(t)
		machine.send_to_time(start, t)
		machine.update(t)
		
		print('Lista de grabaciones ' + str(self.recordlist))

		print('Velocidad de boy al restaurarlo: ' +
			str((oldboy.vx, oldboy.vy)))

		print(str(t) + 'Restaurando ' + str(tm[1]))
		
		b = Boy(t, self.eventd, self.cam, self)
		# TODO: Ajustar esta posicion para que quede en el centro
		b.set_position(machine.rx, machine.ry)
		self.om.add(b)
		
		self.cam.follow(b)
		b.activate(t)
		
		

	def new_boy(self, boy, t):
		if self.eventd.active_boy == None: return
		if boy.i != self.eventd.active_boy.i: return

		rec = Recording(t)
		rec.new_frame(t)
		self.recordlist.append((boy, rec))
		#print(self.recordlist)

	def dispatch(self, t):
		'Envía los eventos de las grabaciones a los personajes'
		for tup in self.recordlist:
			eventl = tup[1].get(t)
			tup[1].new_frame(t)
			#print(eventl)
			for ev in eventl:
				tup[0].event(ev, t, None)

	def key_event(self, e, t):
		'Envía los eventos del teclado a las grabaciones'
		for tup in self.recordlist:
			eventl = tup[1].event(e)
		
		

pygame.init()
terminus = pygame.font.SysFont("monospace", 15)
screen = pygame.display.set_mode((320*2, 240*2))

def level1(t, eventd, camera, om, svt):
	m0 = Machine(t, eventd, camera, svt)
	m0.set_position(50, 0)
	om.add(m0)

	#floor0 = Sprite
	
	b0 = Boy(t, eventd, camera, svt)
	b0.set_position(0, 0)
	om.add(b0)

	camera.follow(b0)
	b0.activate(t)

def main():
	#t = time.perf_counter()
	frame = 0
	t = frame
	clock = pygame.time.Clock()
	om = ObjectManager()
	eventctrl = EventControl(t)
	eventd = EventDaemon(eventctrl, om)
	camera = Camera()
	svt = SVT(om, eventd, camera)
	eventd.set_svt(svt)

	level1(t, eventd, camera, om, svt)

	while True:
		#print("-- Loop start --")

		#t = time.perf_counter()
		t = frame
		
		screen.fill((0, 0, 0))
		eventd.dispatch(t)
		svt.dispatch(t)
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


