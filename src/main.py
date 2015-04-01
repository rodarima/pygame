import sys, pygame, time
import pyganim
from pympler import asizeof
from pygame import gfxdraw

FPS = 50
REC_RECORDING = 0
REC_WAITING = 1
REC_PLAYING = 2
REC_STOPPED = 3

class Recording():
	""" Records events for auto-play """
	def __init__(self, t, svt):
		self.start_time = t
		self.end_time = 0
		self.events = []

		self.last_start = 0.0
		self.play_start = 0
		self.play_end = 0
		self.play_offset = 0.0

		self.state = REC_RECORDING
		self.svt = svt

	def event(self, t, e):
		if(self.state != REC_RECORDING): return
		tup = (t, e)
		self.events.append(tup)
		#print("Record event:" + str(tup))

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

	def play(self, play_start):
		print('Recording PLAY start = {0}'.format(play_start))
		if self.end_time < play_start:
			self.state = REC_STOPPED
			print('Recording STOPPED')
		elif self.start_time < play_start:
			self.state = REC_PLAYING
			print('Recording PLAYING')
		else:
			self.state = REC_WAITING
			print('Recording WAITING')
		self.play_start = play_start
		self.last_start = play_start
		#self.print()

	def finish(self, t):
		self.state = REC_STOPPED
		self.end_time = t

	def get(self, t):
		if(self.state in (REC_RECORDING, REC_STOPPED)):
			return []
		elif self.state == REC_WAITING:
			if t >= self.start_time:
				self.svt.start_record(self)
				self.state = REC_PLAYING
			# Si aún no ha comenzado la reproducción, no hacer nada
			else: return[]

		#TODO: WAITING -> PLAYING

		#print('Recording GET')
		start_get = self.last_start
		end_get = t
		self.last_start = end_get

		# Al terminar la grabación, detenerse y avisar a SVT
		if start_get > self.end_time:
			self.state = REC_STOPPED
			self.svt.end_record(self)

		#if start_get > t:
		#	return []

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
			#print("Replay event:" + str(e))
			el.append(e[1])
		return el

class SpriteT(pygame.sprite.Sprite):
	""" Almacena la velocidad y posición de un Sprite """
	def __init__(self, t):
		pygame.sprite.Sprite.__init__(self);
		self.last_time = t
		self.ax = 0.0
		self.ay = 0.0
		self.vx = 0.0
		self.vy = 0.0
		self.rx = 0.0
		self.ry = 0.0

	def set_position(self, rx, ry):
		self.rx = rx
		self.ry = ry

	def update_position(self, t):
		dif_t = t - self.last_time
		if dif_t > 1:
			print("ERROR: dif_t:" + str(dif_t) + ' en boy'+str(self.i))
			sys.exit()
		self.last_time = t
		self.rx += self.vx * dif_t + (dif_t**2 * self.ax / 2)
		self.ry += self.vy * dif_t + (dif_t**2 * self.ay / 2)

		self.vx += (dif_t * self.ax)
		self.vy += (dif_t * self.ay)

		#print('SpriteT absolute position ' + str((self.rx, self.ry)))

	def load_image(self, f):
		img = pygame.image.load(f)
		img = img.convert()
		img.set_colorkey(img.get_at((0,0)), pygame.RLEACCEL)
		return img

	def update(self, t):
		scr_pos = self.cam.get_screen_position(self.rx, self.ry)
		self.rect.bottomleft = scr_pos

		#label = terminus.render(str((self.rx, self.ry, self.last_time, t)), 1, (255,0,0))
		#screen.blit(label, scr_pos)

		#screen.blit(self.surf, self.rect)

	def clone(self):
		d = {}
		d['r'] = (self.rx, self.ry)
		d['v'] = (self.vx, self.vy)
		d['a'] = (self.ax, self.ay)
		d['last_time'] = self.last_time
		return d

	def restore(self, d):
		self.rx, self.ry = d['r']
		self.vx, self.vy = d['v']
		self.ax, self.ay = d['a']
		self.last_time = d['last_time']

class BlockState():

	def __init__(self):
		self.obj_block = None

	def block(self, obj):
		self.obj_block = obj

	def unblock(self):
		self.obj_block = None

	def blocked(self):
		return (self.obj_block != None)

	def is_blocked_by(self, o):
		return (self.obj_block == o)

	def clone(self):
		d = {}
		d['block'] = self.obj_block
		return d

	def restore(self, d):
		self.obj_block = d['block']


class Wall(pygame.sprite.Sprite):
	def __init__(self, pos, size, cam):
		pygame.sprite.Sprite.__init__(self);
		self.pos = pos
		self.rx = pos[0]
		self.ry = pos[1]
		self.size = size
		self.surf = pygame.Surface(size)
		self.surf.fill((100,100,100))
		self.cam = cam
		self.rect = pygame.Rect((0,0),(size))

		scr_pos = self.cam.get_screen_position(self.pos[0], self.pos[1])
		self.rect.bottomleft = scr_pos

	def update(self, rel_t):
		scr_pos = self.cam.get_screen_position(self.pos[0], self.pos[1])
		self.rect.bottomleft = scr_pos
		screen.blit(self.surf, self.rect)

	#def clone(self): return None
	#def restore(self, d): pass

class Gravity:
	def __init__(self, om):
		self.k = 0.05
		self.g = -9.81 * self.k
		self.om = om
		self.falling = False

	def update_velocity(self, rel_t):

		#print('vy = ' + str(self.vy))
		max_y = self.om.collide_walls(self)
		if max_y == None:
			if not self.falling:
				self.ay = self.g
				print('Falling')
				self.falling = True
		elif self.falling and self.vy < 0:
			print('ry = ' + str(self.ry))
			print('Stop falling max_y = ' + str(max_y))
			self.falling = False
			self.ay = 0
			self.vy = 0
			self.ry = max_y

	def clone(self):
		d = {}
		d['falling'] = self.falling
		return d

	def restore(self, d):
		self.falling = d['falling']

KEY_JUMP = pygame.K_UP
KEY_ACTION = pygame.K_DOWN

class Boy(SpriteT, Gravity):
	def __init__(self, t, eventd, cam, svt, om):
		SpriteT.__init__(self, t)
		Gravity.__init__(self, om)
		self.img = self.load_image("../img/boy2.gif")
		self.eventd = eventd
		self.fr = 0.0
		#self.fps = 1
		#self.rx = 106
		#self.ry = 110
		self.disabled = False
		self.i = -1
		self.cam = cam
		self.rect = pygame.Rect((0,0), (13, 21))
		self.svt = svt
		self.flipped = False

		self.frame(0)

	def activate(self, t):
		self.eventd.active_boy = self
		self.svt.new_boy(self, t)

	def frame(self, n):
		self.fr = (self.fr + n) % 13
		self.surf = self.img.subsurface(self.fr*13, 0,
			self.rect.w, self.rect.h)

		if self.vx < 0: self.flipped = True
		elif self.vx > 0: self.flipped = False

		if self.flipped:
			self.surf = pygame.transform.flip(
				self.surf, True, False)

		#self.rect = pygame.Rect(self.rx, self.ry, 13, 21)

	def do_action(self, e):
		self.eventd.event(e)

	def event(self, e, t, from_obj):
		if(from_obj != None): return False
		if(self.disabled): return False
		#print('Boy'+str(self.i)+' event '+ str(e) +' from '
		#	+str(from_obj) + ' at ' + str(t))
		if e.type == pygame.KEYDOWN:
			if e.key == pygame.K_LEFT: self.vx = -1.5
			elif e.key == pygame.K_RIGHT: self.vx = 1.5
			#elif e.key == pygame.K_DOWN: self.vy = -1
			elif e.key == KEY_JUMP:
				if not self.falling: self.vy = 7
			elif e.key == KEY_ACTION: self.eventd.event(e, self)
		elif e.type == pygame.KEYUP:
			if e.key == pygame.K_LEFT: self.vx = 0
			elif e.key == pygame.K_RIGHT: self.vx = 0
			#elif e.key == pygame.K_DOWN: self.vy = 0
			#elif e.key == KEY_JUMP: self.vy = 0
			elif e.key == KEY_ACTION: self.eventd.event(e, self)
		#self.update_position(t)
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
		d['disabled'] = self.disabled
		d['flipped'] = self.flipped
		#d['BlockState'] = BlockState.clone(self)
		d['SpriteT'] = SpriteT.clone(self)
		d['Gravity'] = Gravity.clone(self)
		return d

	def restore(self, d):
		self.fr = d['fr']
		self.disabled = d['disabled']
		self.flipped = d['flipped']
		#BlockState.restore(self, d['BlockState'])
		SpriteT.restore(self, d['SpriteT'])
		Gravity.restore(self, d['Gravity'])

	def recalc(self, t):
		'Actualiza la posición del chico'
		if(self.disabled): return
		#print('Boy update')
		Gravity.update_velocity(self, t)
		if self.vy < -30: sys.exit()
		self.update_position(t)
		if self.vx != 0:	fn = +1
		else: fn = 0
		self.frame(fn)
		self.cam.update()
		SpriteT.update(self, t)

	def draw(self, t):
		if(self.disabled): return
		scr_pos = self.cam.get_screen_position(self.rx, self.ry)
		name = terminus.render(str(self.i), 1, (255,0,0))
		screen.blit(name, (scr_pos[0]+5, scr_pos[1]-self.rect.h-15))

		screen.blit(self.surf, self.rect)

	def update(self, t):
		if(self.disabled): return
		self.recalc(t)
		self.draw(t)
		#self._draw_axis()
		#SpriteT.update(self, t)
		##w, h = screen.get_size()
		#abs_pos = (self.rx, self.ry)
		#rel_pos = self.cam.get_relative_position(self.rx, self.ry)
		#scr_pos = self.cam.get_screen_position(self.rx, self.ry)
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

	def disable(self):
		self.disabled = True
	def enable(self):
		self.disabled = False

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
		self.timer_time = 1.0 * FPS
		self.timer_step = 0.2 * FPS
		self.timer_start = 0.0
		self.action = 0
		self.rect = pygame.Rect((0,0), (self.imgw, self.imgh))
		self.i = -1
		self.cam = cam
		self.svt = svt

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
		if not ((e.type == pygame.KEYDOWN) and (e.key == KEY_ACTION)):
			return False

		if self.state == MACHINE_OFF:
			if self.blocked() == True:
				print(str(t)+
					':ERROR, máquina bloqueada y apagada')
				sys.exit()
			else:
				print('Machine blocking from boy' +
					str(from_obj.i))
				self.block(from_obj)
				self.action = 1
		else: #Encendida o encendiendo
			if not self.blocked():
				print(str(t)+
					':ERROR, máquina desbloqueada y encendida')
				sys.exit()
			if self.is_blocked_by(from_obj):
				print('Machine unblocking from boy' +
					str(from_obj.i))
				self.unblock()
				self.poweroff(from_obj, t)
			elif self.obj_block.disabled:
				self.unblock()
				self.poweroff(from_obj, t)
			else: return False

		return True

	def program(self, t):
		print(str(t)+":Machine programming")
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
		print(str(t) + ":Machine powered on")
		self.svt.on(self, t)

	def poweroff(self, boy, t):
		st = self.state
		self.state = MACHINE_OFF
		print(str(t) + ":Machine powered off")
		if st == MACHINE_ON:
			if boy == self.eventd.active_boy:
				print(str(t) + ":Travelling")
				self.svt.off(self, t)

	def draw(self, t):
		scr_pos = self.cam.get_screen_position(self.rx, self.ry)
		abs_pos = (self.rx, self.ry)
		if self.blocked() and not self.obj_block.disabled:
			n = self.obj_block.i
			name = terminus.render(str(n), 1, (255,0,0))
			screen.blit(name, (scr_pos[0]+12, scr_pos[1]-self.rect.h-15))
		screen.blit(self.surf, self.rect)

	def update(self, t):
		#print('Machine update')
		if(self.action and self.state == MACHINE_OFF):
			self.action = 0
			self.program(t)
		if(self.state in (MACHINE_TIMER0, MACHINE_TIMER1)):
			self.update_timer(t)
		self.frame()
		#print('Machine rect: ' + str(self.rect))
		#if self.blocked():
		#	pygame.draw.rect(self.surf, (100,0,0), (0, 0,
		#		self.imgw, self.imgh), 1)


		#print('Machine screen position: ' + str(scr_pos))
		#print('Machine absolute position: ' + str(abs_pos))

		#rect = pygame.Rect(self.rx + cx, self.ry + cy, self.imgw, self.imgh)
		#r = self.rect
		#r.bottomleft = scr_pos
		#screen.blit(self.surf, r)
		self.update_position(t)
		SpriteT.update(self, t)
		self.draw(t)

	def clone(self):
		d = {}
		d['state'] = self.state
		d['timer_start'] = self.timer_start

		d['BlockState'] = BlockState.clone(self)
		d['SpriteT'] = SpriteT.clone(self)
		return d

	def restore(self, d):
		self.state = d['state']
		self.timer_start = d['timer_start']

		BlockState.restore(self, d['BlockState'])
		SpriteT.restore(self, d['SpriteT'])

class Event:
	def __init__(self, position, e):
		self.position = position
		self.e = e

class EventControl:
	def __init__(self):
		self.raw_events = []
		self.key_events = []

	def _filter_key_events(self):
		self.raw_events = pygame.event.get()
		self.key_events = []
		for e in self.raw_events:
			if e.type in (pygame.KEYDOWN, pygame.KEYUP):
				self.key_events.append(e)

	def get_keyboard(self):
		return self.key_events

	def dispatch(self):
		#print('EventControl dispatched')
		self._filter_key_events()
		for e in self.raw_events:
			if e.type == pygame.QUIT:
				print('Exiting')
				sys.exit()


class EventDaemon:

	def __init__(self, event_control, om):
		self.eventlist = []
		self.ec = event_control
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

	def _dispatch_keyboard(self, rel_t):
		if(self.active_boy == None): return

		for event in self.ec.get_keyboard():
			self.active_boy.event(event, rel_t, None)
			self.svt.key_event(event, rel_t)

	def dispatch(self, rel_t):
		#print('EventDaemon dispatched')
		self.ec.dispatch()
		self._dispatch_keyboard(rel_t)
		for elem in self.get():
			e = elem[0]
			from_obj = elem[1]
			l = self.object_manager.collide(from_obj)
			#if l != []:
			#	print('Lista de objetos al colisionar: ' +
			#		str(l))
			for obj in l:
				#print('Sending event to:' + str(obj))
				if obj.event(e, rel_t, from_obj) == True: break


class ObjectManager:
	"""Permite encontrar objetos por la posicion"""
	def __init__(self):
		self.objects = [] #pygame.sprite.Group()
		self.boyi = 1
		self.walls = [] #pygame.sprite.Group()

	def set_eventd(self, eventd):
		self.eventd = eventd

	def add(self, obj):
		if isinstance(obj, Boy):
			obj.i = self.boyi
			self.boyi += 1
		self.objects.append(obj)

	def collide(self, obj):
		#for o in self.objects:
		#	print(str(o.rect))
		return pygame.sprite.spritecollide(obj, self.objects, False)

	def update(self, rel_t):

		self.eventd.active_boy.recalc(rel_t)
		for obj in self.objects+self.walls:
			#print('Updating object: ' + str(obj))
			if(obj != self.eventd.active_boy):
				obj.update(rel_t)
		#self.eventd.active_boy.update(rel_t)
		self.eventd.active_boy.recalc(rel_t)
		self.eventd.active_boy.draw(rel_t)

	def disable_boys(self):
		for obj in self.objects:
			if isinstance(obj, Boy):
				obj.disable()
				print('Disable boy' + str(obj.i))

	def restore_boy(self, d, boy):
		for t in d['l']:
			if t[0] == boy:
				t[0].restore(t[1])

	def add_wall(self, obj):
		self.walls.append(obj)

	def collide_walls(self, obj):
		l = pygame.sprite.spritecollide(obj, self.walls, False)
		if l != []:
			max_y = l[0].ry
			for o in l:
				if o.ry > max_y: max_y = o.ry
			#print(str(l))
			return max_y
		else:
			return None

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
		cy = hm - 0*ry - hb/2

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
		self.inc_t = 0

	def rel(self, absolute_t):
		'Obtiene el tiempo relativo a t'
		return absolute_t - self.inc_t

	def travel(self, time_now, time_past):
		'Viaja al pasado en el tiempo'
		print(str(time_now)+':Travelling from {0} to {1}'.format(
			time_now, time_past))
		self.inc_t += time_now - time_past


	def find_last_machine(self, m):
		last = None
		for t in self.clonelist:
			if t[0] == m:
				if last == None: last = t
				elif last[2] < t[2]:
					last = t
		return last

	def find_boy(self, boy):
		# FIXME: Y si existen varias grabaciones para un mismo personaje?
		for t in self.recordlist:
			if t[0] == boy:
				return t
	def find_rec(self, rec):
		for t in self.recordlist:
			if t[1] == rec:
				return t

	def on(self, machine, rel_t):
		print(str(rel_t)+':SVT on m'+str(machine.i))
		clone = self.om.clone()
		boy_clone = self.eventd.active_boy.clone()
		item = (machine, clone, rel_t, boy_clone)
		self.clonelist.append(item)
		#print('Lista de clones ' + str(self.clonelist))

	def rec_play(self, rel_t):
		'Pone todas las grabaciones a reproducirse en rel_t'
		for t in self.recordlist:
			t[1].play(rel_t)

	def print_time(self, rel_t):
		label = font_time.render('Time: ' + str(int(rel_t/FPS)), 1, (100,100,100))
		screen.blit(label, (280, 30))

	def enable_machines(self, m):
		'Activa todas las máquinas excepto la actual'

	def off(self, machine, rel_t):
		'Viaje en el tiempo'
		tm = self.find_last_machine(machine)
		tb = self.find_boy(self.eventd.active_boy)

		oldboy = tb[0]
		machine = tm[0]
		rec = tb[1]
		start = tm[2]

		self.travel(rel_t, start)

		rec.finish(rel_t)

		self.om.disable_boys()

		print('Restaurando '+str(tm[1]))
		self.om.restore(tm[1])
		oldboy.update(start)
		machine.update(start)

		self.rec_play(start)

		#print('Lista de grabaciones ' + str(self.recordlist))

		#print('Velocidad de boy al restaurarlo: ' +
		#	str((oldboy.vx, oldboy.vy)))

		#print('Rel_t ' + str(rel_t) + ' restaurando ' + str(tm[1]))

		b = Boy(start, self.eventd, self.cam, self, self.om)
		# TODO: Ajustar esta posicion para que quede en el centro
		b.set_position(machine.rx +7, machine.ry)
		self.om.add(b)

		self.cam.follow(b)
		b.activate(start)

	def new_boy(self, boy, rel_t):
		if self.eventd.active_boy == None: return
		if boy.i != self.eventd.active_boy.i: return

		rec = Recording(rel_t, self)
		clone = boy.clone()
		self.recordlist.append((boy, rec, clone))
		#print(self.recordlist)

	def update(self, abs_t):
		'Actualiza todo el juego usando el tiempo absoluto'
		rel_t = self.rel(abs_t)
		self.eventd.dispatch(rel_t)
		# El tiempo puede cambiar ahora despues de actualizar eventd
		rel_t = self.rel(abs_t)
		self.dispatch(rel_t)
		self.om.update(rel_t)
		self.print_time(rel_t)

	def dispatch(self, rel_t):
		'Envía los eventos de las grabaciones a los personajes'

		#print(str(rel_t)+':Enviando eventos grabados a los personajes')
		for tup in self.recordlist:
			eventl = tup[1].get(rel_t)
			#print(eventl)
			for ev in eventl:
				tup[0].event(ev, rel_t, None)
				#print(str(rel_t)+':Enviado a boy'+str(tup[0].i))

	def key_event(self, e, rel_t):
		'Envía los eventos del teclado a las grabaciones'
		for tup in self.recordlist:
			eventl = tup[1].event(rel_t, e)

	def end_record(self, rec):
		'Al terminar una grabación, quitar al personaje'
		tup = self.find_rec(rec)
		boy = tup[0]
		boy.disable()

		#TODO Reactivar objetos bloqueados

	def start_record(self, rec):
		'Al comienzo de una grabación, restaurar el personaje'
		tup = self.find_rec(rec)
		boy = tup[0]
		boy.restore(tup[2])
		boy.enable()
		print('Starting record for boy' + str(boy.i))

class Game:

	def level1(self, t, eventd, camera, om, svt):
		w0 = Wall((-50, 0), (400, 1), camera)
		om.add_wall(w0)

		w1 = Wall((50, 50), (200, 1), camera)
		om.add_wall(w1)

		w2 = Wall((350+40, 0), (200, 1), camera)
		om.add_wall(w2)

		m0 = Machine(t, eventd, camera, svt)
		m0.set_position(100, 0)
		om.add(m0)

		m1 = Machine(t, eventd, camera, svt)
		m1.set_position(200, 0)
		om.add(m1)

		m2 = Machine(t, eventd, camera, svt)
		m2.set_position(300, 0)
		om.add(m2)

		m3 = Machine(t, eventd, camera, svt)
		m3.set_position(500, 0)
		om.add(m3)

		b0 = Boy(t, eventd, camera, svt, om)
		b0.set_position(0, 0)
		om.add(b0)

		camera.follow(b0)
		b0.activate(t)

	def play(self):
		#t = time.perf_counter()
		frame = 0
		t = frame
		clock = pygame.time.Clock()
		om = ObjectManager()
		eventctrl = EventControl()
		eventd = EventDaemon(eventctrl, om)
		camera = Camera()
		svt = SVT(om, eventd, camera)
		eventd.set_svt(svt)
		om.set_eventd(eventd)

		self.level1(t, eventd, camera, om, svt)

		while True:
			#print("-- Loop start --")

			#t = time.perf_counter()
			t = frame

			screen.fill((0, 0, 0))

			svt.update(t)

			pygame.display.update()
			pygame.display.flip()

			#print("-- Loop end --")

			clock.tick(FPS)
			frame += 1


pygame.init()
font_time = pygame.font.SysFont("terminus", 30)
terminus = pygame.font.SysFont("terminus", 16)
screen = pygame.display.set_mode((320*2, 240*2))


if __name__ == '__main__':
	game = Game()
	game.play()
