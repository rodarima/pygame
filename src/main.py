
# Encoding: utf-8

from __future__ import division
import sys, pygame, time, os
from pygame import gfxdraw

FPS = 50
REC_RECORDING = 0
REC_WAITING = 1
REC_PLAYING = 2
REC_STOPPED = 3

EVENTCODE_OFF = 0
EVENTCODE_ON = 1
EVENTCODE_DIE = 2
EVENTCODE_COLLIDE = 3
EVENTCODE_INCOHERENCE = 4
EVENTCODE_PAUSE = 5
EVENTCODE_RESET = 6

MACHINE_OFF = 0
MACHINE_TIMER0 = 1
MACHINE_TIMER1 = 2
MACHINE_ON = 3

KEY_JUMP = pygame.K_UP
KEY_ACTION = pygame.K_DOWN
KEY_OK = pygame.K_SPACE

# Center window
os.environ['SDL_VIDEO_CENTERED'] = '1'


class Recording():
	""" Records events for auto-play """
	def __init__(self, t, svt):
		self.start_time = t
		self.end_time = 0
		self.events = []
		self.i = -1

		self.last_start = 0.0
		self.play_start = 0
		self.play_end = 0
		self.play_offset = 0.0

		self.state = REC_RECORDING
		self.svt = svt

	def restart(self, t):
		self.start_time = t
		self.end_time = 0
		self.events = []
		self.last_start = 0.0
		self.play_start = 0
		self.play_end = 0
		self.play_offset = 0.0
		self.state = REC_RECORDING

	def event(self, t, e):
		if(self.state != REC_RECORDING): return
		tup = (t, e)
		self.events.append(tup)
		#print "Record event:" + str(tup

	def new_frame(self, t):
		if(self.state != REC_RECORDING): return
		self.diff_time = t - self.start_time
		#print "Recording new frame, dif = " + str(self.diff_time)

	def _print(self):
		for e in self.events:
			print e

	def get_all(self):
		return [e[1] for e in self.events]

	def play(self, play_start):
#		print 'Recording PLAY start = {0}'.format(play_start)
		if self.end_time < play_start:
			self.state = REC_STOPPED
			print 'Recording STOPPED'
		elif self.start_time < play_start:
			self.state = REC_PLAYING
			print 'Recording PLAYING'
		else:
			self.state = REC_WAITING
			print 'Recording WAITING'
		self.play_start = play_start
		self.last_start = play_start

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

		#print 'Recording GET'
		start_get = self.last_start
		end_get = t
		self.last_start = end_get

		# Al terminar la grabación, detenerse y avisar a SVT
		if start_get > self.end_time:
			self.state = REC_STOPPED
			self.svt.end_record(self)

		#if start_get > t:
		#	return []

#		print "start:"+str(start_get)
#		print "end:"+str(end_get)

		# "Premature optimization is the root of all evil" - Donald Knuth
		#return [e[1] for e in self.events if e[0] >= start_get e[0] < end_get]
		start = -1
		end = -1
		for i in range(len(self.events)):
			e = self.events[i]
			if(e[0] > end_get and i == 0): break
			if(e[0] >= start_get and start == -1):
#				print "Got start:" + str(i)
				start = i
			if(e[0] < end_get and start != -1):
#				print "Got end:" + str(i)
				end = i
			if(e[0] >= end_get and start != -1):
				break
			#if(start != -1 and end != -1):
			#	break

		#print str(start) + " -> " + str(end)
		el = []
		for e in self.events[start:end+1]:
			#print "Replay event:" + str(e)
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
#		if dif_t > 1:
#			print "ERROR: dif_t:" + str(dif_t) + ' en boy'+str(self.i)
#			sys.exit('BUG')
		self.last_time = t
		self.rx += self.vx * dif_t + (dif_t**2 * self.ax / 2)
		self.ry += self.vy * dif_t + (dif_t**2 * self.ay / 2)

		self.vx += (dif_t * self.ax)
		self.vy += (dif_t * self.ay)

		#print 'SpriteT absolute position ' + str((self.rx, self.ry))

	@staticmethod
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
		scr_pos = self.cam.get_screen_position(self.rx, self.ry)
		self.rect.bottomleft = scr_pos

		print 'spriteT:\trestoring obj{} at ({}, {}'.format(
			self.i, self.rx, self.ry)

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

class Collider:
	def collide(self, obj):
		raise NotImplemented()


class Wall(pygame.sprite.Sprite, Collider):
	def __init__(self, pos, size, cam):
		pygame.sprite.Sprite.__init__(self);
		self.pos = pos
		self.i = -1
		self.rx = pos[0]
		self.ry = pos[1]
		self.size = size
		self.surf = pygame.Surface(size)
		self.surf.fill((100,100,100))
		self.cam = cam
		self.rect = pygame.Rect((0,0),(size))

		scr_pos = self.cam.get_screen_position(self.pos[0], self.pos[1])
		self.rect.bottomleft = scr_pos

	def collide(self, obj):
		return pygame.sprite.collide_rect(obj, self)

	def update(self, rel_t):
		scr_pos = self.cam.get_screen_position(self.pos[0], self.pos[1])
		self.rect.bottomleft = scr_pos
		screen.blit(self.surf, self.rect)

	#def clone(self): return None
	#def restore(self, d): pass

class LogicConnector:
	'Send every input event to all output objects'
	def __init__(self):
		self.inlist = []
		self.outlist = []

	def event(self, e, rel_t, from_obj):
		if not (from_obj in self.inlist): return False

		for obj in self.outlist:
			obj.event(e, rel_t, from_obj)

	def add_in(self, obj):
		self.inlist.append(obj)

	def add_out(self, obj):
		self.outlist.append(obj)


class LeverButton(pygame.sprite.Sprite):

	LEVER_OFF = 0
	LEVER_ON = 1

	def __init__(self, pos, eventd, cam, svt, om):
		pygame.sprite.Sprite.__init__(self);
		self.img = SpriteT.load_image(self, "../img/lever.gif")
		self.eventd = eventd
		self.imgx = 0
		self.imgy = 0
		self.imgw = 13
		self.imgh = 14
		self.frames = 9
		self.frame = 0
		self.state = self.LEVER_OFF
		self.boy = None
		self.target = None
		self.pos = pos
		self.rect = pygame.Rect(self.pos, (self.imgw, self.imgh))
		self.i = -1
		self.cam = cam
		self.svt = svt
		self.om = om
		self.surf = self.img.subsurface(
			self.frame * self.imgw + self.imgx,
			self.imgy,
			self.imgw,
			self.imgh)

#		self.update_frame()

	def update_frame(self):
		if(self.state == self.LEVER_OFF and self.frame != 0):
			self.frame -= 1
		elif(self.state == self.LEVER_ON and self.frame != self.frames-1):
			self.frame += 1

		#print 'leverbutton{}:\tframe = {}'.format(self.i, self.frame)

		self.surf = self.img.subsurface(
			self.frame * self.imgw + self.imgx,
			self.imgy,
			self.imgw,
			self.imgh)

	def set_target(self, obj):
		self.target = obj

	def action(self, t):
		if(self.target == None): return

		if self.state == self.LEVER_OFF:
			code = EVENTCODE_OFF
		else:
			code = EVENTCODE_ON

		d = {}
		d['code'] = code
		ev = pygame.event.Event(pygame.USEREVENT, d)
		self.eventd.event_to(ev, self, self.target, t)

	def pull(self, t, from_obj):
		if self.boy == None:
			self.boy = from_obj
			self.state = self.LEVER_ON
			print 'leverbutton{}:\tboy{} pulls the lever'.format(
				self.i, self.boy.i)
		elif self.boy == self.eventd.active_boy:
			print 'leverbutton{}:\taltered past detected'.format(
				self.i)
			print 'leverbutton{}:\tboy{} wants to change state'.format(
				self.i, from_obj.i)
			self.svt.level_event(t, EVENTCODE_INCOHERENCE)
		else:
			print 'leverbutton{}:\tignoring event from unknown boy{}'.format(
				self.i, from_obj.i)
			return False

	def release(self, t, from_obj):
		if self.boy != from_obj:
#			if self.boy == self.eventd.active_boy:
#				print 'leverbutton{}:\taltered past detected'.format(
#					self.i)
#				print 'leverbutton{}:\tboy{} wants to change state'.format(
#					self.i, from_obj.i)
#				sys.exit('BUG')
#			else:
			print 'leverbutton{}:\tignoring event from unknown boy{}'.format(
				self.i, from_obj.i)
			return False
		elif self.boy == from_obj:
			print 'leverbutton{}:\tboy{} releases the lever'.format(
				self.i, self.boy.i)
			self.boy = None
			self.state = self.LEVER_OFF

	def event(self, e, rel_t, from_obj):
		print 'leverbutton{}:\tevent at t={}'.format(self.i, rel_t)

		if e.key != KEY_ACTION:
			print 'leverbutton{}:\tignoring unknown key'.format(self.i)
			return False

		if not isinstance(from_obj, Boy):
			print 'leverbutton{}:\tevent not from boy'.format(self.i)
			return False


		if e.type == pygame.KEYDOWN:
			self.pull(rel_t, from_obj)
		elif e.type == pygame.KEYUP:
			self.release(rel_t, from_obj)
		else:
			print 'leverbutton{}:\tignoring unknown event type'.format(self.i)
			return False


		print 'leverbutton{}:\tstate now {}'.format(self.i, self.state)
		#TODO: Solo enviar acción cuando realmente hace falta
		self.action(rel_t)

		return True

	def collide_boy(self, rel_t):
		lobj = self.om.collide(self)
		if(self.boy not in lobj):
			print 'leverbutton{}:\tboy{} leaving'.format(self.i, self.boy.i)
			print 'leverbutton{}:\tboy{} at {},{}'.format(
				self.i, self.boy.i, self.boy.rx,self.boy.ry)
			self.boy = None
			self.state = self.LEVER_OFF
			self.action(rel_t)

	def update(self, rel_t):
		#Recalc position for camera
		scr_pos = self.cam.get_screen_position(self.pos[0], self.pos[1])
		self.rect.bottomleft = scr_pos

		#Comprobar que el personaje sigue activando la palanca
		if(self.boy != None):
			self.collide_boy(rel_t)

		#Set frame
		self.update_frame()

		#Draw
		screen.blit(self.surf, self.rect)

	def clone(self):
		d = {}
		d['frame'] = self.frame
		d['state'] = self.state
		d['boy'] = self.boy
		return d

	def restore(self, d):
		self.frame = d['frame']
		self.state = d['state']
		self.boy = d['boy']
		print 'leverbutton{}:\trestoring state {}'.format(self.i, self.state)
#		print 'leverbutton{}:\trestoring state {}'.format(self.i, self.frame)

class PlatformSimple(pygame.sprite.Sprite, Collider):

	PLATFORM_INACTIVE = 0
	PLATFORM_ACTIVE = 1

	def __init__(self, pos, size, cam):
		pygame.sprite.Sprite.__init__(self);
		self.state = self.PLATFORM_INACTIVE
		self.pos = pos
		self.i = -1
		self.cam = cam
		self.surf = pygame.Surface(size)
		self.surf.fill((100,100,100))
		self.rect = pygame.Rect((0,0), size)
		self.rx, self.ry = pos

	def collide(self, obj):
		if self.state == self.PLATFORM_INACTIVE: return False
		elif self.state == self.PLATFORM_ACTIVE:
			return pygame.sprite.collide_rect(obj, self)

	def event(self, e, rel_t, from_obj):
		print 'platform{}:\tevent at t={}'.format(self.i, rel_t)

		if e.type != pygame.USEREVENT:
			print 'platform{}:\tignoring no user event'.format(self.i)
			return False

		print 'platform{}:\tevent:'.format(self.i)
		print str(e)

		if e.code == EVENTCODE_OFF:
			self.state = self.PLATFORM_INACTIVE
		elif e.code == EVENTCODE_ON:
			self.state = self.PLATFORM_ACTIVE
		else:
			print 'platform{}:\tignoring unknown event code'.format(self.i)
			return False


		print 'platform{}:\tstate now {}'.format(self.i, self.state)

		return True

	def update(self, rel_t):

		# No hacer nada si está desactivada
		if(self.state != self.PLATFORM_ACTIVE):
			return

		#Recalc position for camera
		scr_pos = self.cam.get_screen_position(self.pos[0], self.pos[1])
		self.rect.bottomleft = scr_pos

		#Draw
		screen.blit(self.surf, self.rect)

	def clone(self):
		d = {}
		d['state'] = self.state
		return d

	def restore(self, d):
		self.state = d['state']
		print 'platform{}:\tstate after restore {}'.format(self.i, self.state)

class Gravity:
	def __init__(self, om):
		#self.k = 0.05
		self.k = 0.001*FPS
		self.g = -9.81 * self.k
		self.om = om
		self.falling = False

	def update_velocity(self, rel_t):

		max_y = self.om.colliders(self)
		if max_y == None:
			if not self.falling:
				self.ay = self.g
				print 'obj{}:\t\tfalling at t={}'.format(self.i, rel_t)
				self.falling = True
#			print 'obj{}:\t\tfalling vy={}'.format(self.i, self.vy)
#TODO: Atrapar caída sólo si la base se encuentra por debajo, y ha pasado por
#encima de las esquinas del suelo
		elif self.falling and self.vy < 0:
			print 'obj{}:\t\tfalling ry={}'.format(self.i, self.ry)
			print 'obj{}:\t\tstop falling max_y={}'.format(self.i, max_y)
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

class Boy(SpriteT, Gravity):
	def __init__(self, t, eventd, cam, svt, om):
		SpriteT.__init__(self, t)
		Gravity.__init__(self, om)
		self.img = self.load_image(self, "../img/boy2.gif")
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

	def _do_action(self, e, t):
		print 'boy{}:\t\tdoing action at t={}'.format(self.i, t)
		self.eventd.event(e, self, t)

	def event(self, e, t, from_obj):
		print 'boy{}:\t\tnew event t={}'.format(self.i, t)
		if(from_obj != None):
			print 'boy{}:\t\tevent not for me'.format(self.i)
			return False
		if(self.disabled): return False
		#print 'Boy'+str(self.i)+' event '+ str(e +' from '
		#	+str(from_obj) + ' at ' + str(t)

		if e.type == pygame.KEYDOWN:
			if e.key == pygame.K_LEFT: self.vx = -1.5/50*FPS

			elif e.key == pygame.K_RIGHT: self.vx = 1.5/50*FPS
			#elif e.key == pygame.K_DOWN: self.vy = -1

			elif e.key == KEY_JUMP:
				if not self.falling: self.vy = 7/50*FPS

			elif e.key == KEY_ACTION:
				self._do_action(e, t)

		elif e.type == pygame.KEYUP:
			if e.key == pygame.K_LEFT: self.vx = 0

			elif e.key == pygame.K_RIGHT: self.vx = 0
			#elif e.key == pygame.K_DOWN: self.vy = 0
			#elif e.key == KEY_JUMP: self.vy = 0
			elif e.key == KEY_ACTION:
				self._do_action(e, t)


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
		#print 'Boy update'
		Gravity.update_velocity(self, t)
		if self.vy < -30*FPS/50:
			self.svt.level_event(t, EVENTCODE_DIE)
		self.update_position(t)
		self.cam.update()
		SpriteT.update(self, t)

	def collide_boys(self, t):
		if self != self.eventd.active_boy: return
		objlist = self.om.collide(self)

		for obj in objlist:
			if obj == self: continue
			if isinstance(obj, Boy) and obj.disabled == False:
				self.svt.level_event(t, EVENTCODE_COLLIDE)
				break

	def draw(self, t):
		if(self.disabled): return
		# FIXME: Lugar poco apropiado para esta comprobación
		self.collide_boys(t)
#		scr_pos = self.cam.get_screen_position(self.rx, self.ry)
#		name = terminus.render(str(self.i), 1, (255,0,0))
#		screen.blit(name, (scr_pos[0]+5, scr_pos[1]-self.rect.h-15))

		if self.vx != 0:	fn = +1
		else: fn = 0
		self.frame(fn)
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
		##print 'Boy rect: ' + str(self.rect)
		#
		#print 'Boy absolute position ' + str(abs_pos)
		#print 'Boy relative position ' + str(rel_pos)
		#print 'Boy screen position ' + str(scr_pos)

		#self._draw_axis()
		#
		#r = self.rect
		##r.left += cx
		##r.bottom += cy
		#r.bottomleft = scr_pos
		#screen.blit(self.surf, r)
		#print "x:"+str(self.rx)+" y:"+str(self.ry)

	def disable(self):
		self.disabled = True
	def enable(self):
		self.disabled = False


class Machine(SpriteT, BlockState):

	def __init__(self, t, eventd, cam, svt):
		SpriteT.__init__(self, t)
		BlockState.__init__(self)
		self.img = self.load_image(self, "../img/machine.gif")
		self.eventd = eventd
		self.imgx = 0
		self.imgy = 0
		self.imgw = 22
		self.imgh = 32
		self.img_frames = 4
		self.img_frame = 0
		self.state = MACHINE_OFF
		self.timer_time = 3.0 * 50
		self.timer_step = 0.5 * 50
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
		#print 'Machine event from ' + str(from_obj.i) + ' at ' + str(t)
		if not ((e.type == pygame.KEYDOWN) and (e.key == KEY_ACTION)):
			print 'machine{}:\tignoring unknown event key'.format(self.i)
			return False

		print 'machine{}:\tnew event t={}'.format(self.i, t)

		if self.state == MACHINE_OFF:
			if self.blocked() == True:
				print str(t+
					':BUG, máquina bloqueada y apagada')
				sys.exit('BUG')
			else:
				print 'machine{}:\tprogramming from i={} at t={}'.format(self.i,
					from_obj.i, t)
				#self.block(from_obj)
				#self.action = 1
				self.program(t)
		elif self.state == MACHINE_ON:
			#if not self.blocked():
			#	print str(t+
			#		':ERROR, máquina desbloqueada y encendida')
			if self.blocked():
				if self.is_blocked_by(from_obj):
				#	or from_obj == self.eventd.active_boy:
					print 'machine{}:\tunblocking from {}'.format(self.i, from_obj.i)
					self.unblock()
					self.poweroff(from_obj, t)
				elif (not self.is_blocked_by(from_obj)) and\
					from_obj != self.eventd.active_boy:
					#print 'machine{}:\taltered past detected'.format(self.i)
					print 'machine{}:\tblocked by boy{} but not for boy{}'.format(
						self.i, self.obj_block.i, from_obj.i)
					return False
				else:
					print 'machine{}:\tyou can not use this machine!!!'.format(self.i)
					print 'machine{}:\tonly boy{} can use me!!!'.format(
						self.i, self.obj_block.i)
					return False
			else:	#La máquina está desbloqueada, está libre
				if from_obj != self.eventd.active_boy:
					print 'machine{}:\taltered past detected'.format(self.i)
					print 'machine{}:\tunblocked but not blocked by boy{}'.format(
						self.i, from_obj.i)
					self.svt.level_event(t, EVENTCODE_INCOHERENCE)
				else:
					print 'machine{}:\tpowering off by boy{}'.format(
						self.i, from_obj.i)
					self.poweroff(from_obj, t)
		else: #Encendiendo
			if from_obj != self.eventd.active_boy:
				print 'machine{}:\taltered past detected'.format(self.i)
				print 'machine{}:\talready powering on'.format(self.i)
				self.svt.level_event(t, EVENTCODE_INCOHERENCE)
			else:
				print 'machine{}:\tyou cannot use me while powering'.format(
					self.i)

#			elif self.obj_block.disabled:
#				self.unblock()
#				self.poweroff(from_obj, t)
#			elif from_obj != self.eventd.active_boy and \
#				self.is_blocked_by(self.eventd.active_boy):
#				print 'machine{}:\taltered past detected'.format(self.i)
#				sys.exit('')
#				return False
#			else:
#				print 'machine{}:\tignoring event'.format(self.i)
#				return False


		return True

	def program(self, t):
		print "machine{}:\tprogramming t={}".format(self.i, t)
		self.timer_start = t
		self.state = MACHINE_TIMER0

	def update_timer(self, t):
		dif_t = t - self.timer_start
		#print dif_t
		if dif_t > self.timer_time:
			self.poweron(t)
		else:
			inc = int(1 + dif_t / self.timer_step) % 2
			self.state = MACHINE_TIMER0 + inc

	def poweron(self, t):
		self.state = MACHINE_ON
		#Crear un evento de encendido
		print "machine{}:\tpowered on at t={}".format(self.i, t)
		self.svt.on(self, t)

	def poweroff(self, boy, t):
		previous_state = self.state
		self.state = MACHINE_OFF
		print "machine{}:\tpowered off at t={}".format(self.i, t)

		if previous_state == MACHINE_ON:
			if boy == self.eventd.active_boy:
				print "machine{}:\ttravelling at t={}".format(self.i, t)
				self.svt.off(self, t)

	def draw(self, t):
		scr_pos = self.cam.get_screen_position(self.rx, self.ry)
		abs_pos = (self.rx, self.ry)
#		if self.blocked():
#			n = self.obj_block.i
#			name = terminus.render(str(n), 1, (255,0,0))
#			screen.blit(name, (scr_pos[0]+12, scr_pos[1]-self.rect.h-15))
		screen.blit(self.surf, self.rect)

	def update(self, t):
		#print 'Machine update'
		#if(self.action and self.state == MACHINE_OFF):
		#	self.action = 0
		#	self.program(t)
		if(self.state in (MACHINE_TIMER0, MACHINE_TIMER1)):
			self.update_timer(t)
		self.frame()
		#print 'Machine rect: ' + str(self.rect)
		#if self.blocked():
		#	pygame.draw.rect(self.surf, (100,0,0), (0, 0,
		#		self.imgw, self.imgh), 1)


		#print 'Machine screen position: ' + str(scr_pos)
		#print 'Machine absolute position: ' + str(abs_pos)

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

class MachineStart(Machine):
	def __init__(self, t, eventd, cam, svt):
		Machine.__init__(self, t, eventd, cam, svt)
		self.state = MACHINE_ON

		# Send event to myself to clone the world
		d = {}
		d['code'] = MACHINE_ON
		ev = pygame.event.Event(pygame.USEREVENT, d)
		self.eventd.event_to(ev, self, self, t)

	def event(self, e, t, from_obj):
		if(from_obj != self):
			print "machine{}:\tignoring all external events".format(self.i)
			return False

		if not (e.type == pygame.USEREVENT and e.code == MACHINE_ON):
			print "machine{}:\tignoring unknown event".format(self.i)
			return False

		self.svt.on(self, t)
		return True


class MachineExit:

	def __init__(self, pos, cam, eventd, level):
		self.img = SpriteT.load_image(self, "../img/machine.gif")
		self.rx, self.ry = pos
		self.imgx = 0
		self.imgy = 0
		self.imgw = 22
		self.imgh = 32
		self.img_frames = 4
		self.img_frame = 3
		self.state = MACHINE_ON
		self.rect = pygame.Rect((0,0), (self.imgw, self.imgh))
		self.i = -1
		self.cam = cam
		self.eventd = eventd
		self.level = level

		self.frame()

	def frame(self):
		self.surf = self.img.subsurface(
			self.state * self.imgw + self.imgx,
			self.imgy,
			self.imgw,
			self.imgh)

	def event(self, e, t, from_obj):
		#print 'Machine event from ' + str(from_obj.i) + ' at ' + str(t)
		if not ((e.type == pygame.KEYDOWN) and (e.key == KEY_ACTION)):
			print 'machine{}:\tignoring unknown event key'.format(self.i)
			return False

		if(from_obj != self.eventd.active_boy):
			print 'machine{}:\tignoring unknown boy{}'.format(
				self.i, from_obj.i)
			return False

		print 'machine{}:\tnew event t={}'.format(self.i, t)
		print 'machine{}:\tend of level'.format(self.i)


		# Send event to GameLogic to start a new level
		d = {}
		d['code'] = MACHINE_OFF
		ev = pygame.event.Event(pygame.USEREVENT, d)
		self.eventd.event_to(ev, self, self.level, t)

		return True

	def draw(self, t):
		scr_pos = self.cam.get_screen_position(self.rx, self.ry)
		self.rect.bottomleft = scr_pos
		screen.blit(self.surf, self.rect)

	def update(self, t):
		self.draw(t)

	def clone(self): return None
	def restore(self, d): pass


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
		#print 'EventControl dispatched'
		self._filter_key_events()
		for e in self.raw_events:
			if e.type == pygame.QUIT or\
				(e.type == pygame.KEYDOWN and e.key == pygame.K_q):
				print 'Exiting'
				sys.exit('')


class EventDaemon:

	def __init__(self, event_control, om):
		self.eventlist = []
		self.event_to_list = []
		self.ec = event_control
		self.active_boy = None
		self.object_manager = om

	def set_svt(self, svt):
		self.svt = svt

	def event(self, e, obj_from, t):
		print 'eventd:\t\tnew event at t={} from i={}'.format(t,obj_from.i)
		self.eventlist.append((e, obj_from, t))

	def event_to(self, e, obj_from, obj_dst, t):
		print 'eventd:\t\tnew event at t={} from obj{} to obj{}'.format(
			t, obj_from.i, obj_dst)
#		obj_dst.event(e, t, obj_from)
		self.event_to_list.append((e, obj_from, obj_dst, t))

#	def get(self):
#		l = self.eventlist
#		self.eventlist = []
#		return l

	def _dispatch_keyboard(self, rel_t):
		if(self.active_boy == None): return

		for event in self.ec.get_keyboard():
			print 'eventd:\t\tkey event. Sending at {} to active boy'.format(rel_t)
			self.active_boy.event(event, rel_t, None)
			self.svt.key_event(event, rel_t)

	def dispatch(self, rel_t):
#		print 'eventd:\t\tdispatch frame t={}'.format(rel_t)
		self.ec.dispatch()
		self._dispatch_keyboard(rel_t)
		for elem in self.eventlist:
			e = elem[0]
			from_obj = elem[1]
			e_t = elem[2]
			l = self.object_manager.collide(from_obj)
			#if l != []:
			#	print 'Lista de objetos al colisionar: ' +
			#		str(l)
			for obj in l:
				if rel_t != e_t:
					print 'eventd:\t\tBUG:Offending time {} != {}'.format(rel_t, e_t)
					print str(elem)
					sys.exit('')
				print 'eventd:\t\tsending event from {} at {} to {}'.format(
					from_obj.i, rel_t, obj.i)
				if obj.event(e, rel_t, from_obj) == True: break
#		if self.eventlist != []:
#			print "eventd:\t\tno more events"
		self.eventlist = []


		for elem in self.event_to_list:
			e, fr, to, et = elem
			to.event(e, et, fr)
		self.event_to_list = []


class ObjectManager:
	"""Permite encontrar objetos por la posicion"""
	def __init__(self):
		self.objects = [] #pygame.sprite.Group()
		self.i = 1
		self.walls = [] #pygame.sprite.Group()

	def set_eventd(self, eventd):
		self.eventd = eventd

	def add(self, obj):
		obj.i = self.i
		self.i += 1
		self.objects.append(obj)

	def collide(self, obj):
		#for o in self.objects:
		#	print str(o.rect)
		return pygame.sprite.spritecollide(obj, self.objects, False)

	def update(self, rel_t):

		self.eventd.active_boy.recalc(rel_t)
		for obj in self.objects+self.walls:
			#print 'Updating object: ' + str(obj)
			if(obj != self.eventd.active_boy):
				obj.update(rel_t)
		#self.eventd.active_boy.update(rel_t)
		self.eventd.active_boy.recalc(rel_t)
		self.eventd.active_boy.draw(rel_t)

	def disable_boys(self):
		for obj in self.objects:
			if isinstance(obj, Boy):
				obj.disable()
				print 'om:\t\tdisable boy{}'.format(obj.i)

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
			#print str(l)
			return max_y
		else:
			return None

	def colliders(self, obj):
		list_collide = []
		max_y = None
		for wall in self.walls:
			if(wall.collide(obj)):
				if(max_y == None): max_y = wall.ry
				elif wall.ry > max_y: max_y = wall.ry
				list_collide.append(wall)
		return max_y

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
		print 'camera:\t\tnow following boy{}'.format(obj.i)
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

		#print 'Camera obj position '+str((self.obj.rx, self.obj.ry))
		#print 'Camera obj relative to '+str(self.obj_coord)
		#print 'Camera screen center '+str((wm, hm))
		cx = wm - rx - wb/2
		cy = hm - 0 * ry - hb/2

		self.camera = (int(cx), int(cy))
		#print 'camera:\t\tupdate'
		#print 'Camera update '+str(self.camera)


	def get_relative_position(self, rx, ry):
		return (rx+self.camera[0], ry+self.camera[1])

	def get_screen_position(self, rx, ry):
		w, h = screen.get_size()
		return (rx+self.camera[0], h-(ry+self.camera[1]))

class Scene:
	def __init__(self, ec):
		self.ec = ec

	def update(self, *args):
		'Update all scene at each frame'
		raise NotImplemented()

class SceneStart(Scene):
	def __init__(self, ec, logic):
		Scene.__init__(self, ec)
		self.logic = logic
		self.img = SpriteT.load_image(self, "../img/title.png")
		print 'SceneStart'

	def update(self):
		screen.fill((0, 0, 0))

		screen.blit(self.img, (0, 0))

		self.ec.dispatch()
		l = self.ec.get_keyboard()
		for e in l:
			if e.type == pygame.KEYDOWN:
				self.logic.pop_scene()
				break

class SceneControls(Scene):
	def __init__(self, ec, logic):
		Scene.__init__(self, ec)
		self.logic = logic
		self.img = SpriteT.load_image(self, "../img/controls.png")
		print 'SceneControls'

	def update(self):
		screen.fill((0, 0, 0))

		screen.blit(self.img, (0, 0))

		self.ec.dispatch()
		l = self.ec.get_keyboard()
		for e in l:
			if e.type == pygame.KEYDOWN:
				self.logic.pop_scene()
				break


class SceneFailure(Scene):
	def __init__(self, ec, text, logic):
		Scene.__init__(self, ec)
		self.logic = logic
		self.text = text
		print 'SceneFailure:' + self.text

	def update(self):
		w, h = screen.get_size()
#		screen.fill((0, 0, 0, 200))

		sh = 50
		s = pygame.Surface((w,sh))
		s.set_alpha(128)
		s.fill((0,0,0))

		screen.blit(s, (0, 0))

		label = font_title.render(self.text, 1, (100,100,100))
		screen.blit(label, (w/2-label.get_width()/2, sh/2-label.get_height()/2))

		self.ec.dispatch()
		l = self.ec.get_keyboard()
		for e in l:
			if e.type == pygame.KEYDOWN and e.key == KEY_OK:
				self.logic.pop_scene()
				break

class Level(Scene):
	def __init__(self, ec, logic):
		Scene.__init__(self, ec)
		self.logic = logic
		self.om = ObjectManager()
		self.eventd = EventDaemon(self.ec, self.om)

		self.camera = Camera()
		self.svt = SVT(self.om, self.eventd, self.camera, self)
		self.eventd.set_svt(self.svt)
		self.om.set_eventd(self.eventd)
		self.frame = 0

	def update(self):
		'Update level at each frame'
		screen.fill((0, 0, 0))
		self.svt.update(self.frame)
		self.frame += 1

	def event(self, e, rel_t, from_obj):
		print 'level:\t\tevent from obj{}'.format(from_obj.i)

		if e.type != pygame.USEREVENT:
			print 'level1:\t\tignoring no user event'
			return False

		#Receive exit event from MachineExit
		if(e.code == EVENTCODE_OFF):
			print 'level1:\t\tevent off received: level complete'
			self.logic.next_level()
			return True
		elif(e.code == EVENTCODE_DIE):
			print 'level1:\t\tevent die received, restarting level'
			self.logic.restart_level('Has muerto.')
		elif(e.code == EVENTCODE_COLLIDE):
			print 'level1:\t\tevent collide received, restarting level'
			self.logic.restart_level('Has colisionado con tu clon.')
		elif(e.code == EVENTCODE_INCOHERENCE):
			print 'level1:\t\tevent incoherence received, restarting level'
			self.logic.restart_level('Has alterado el pasado.')

		# End level, and go to the next.
		return True

class Level1(Level):
	def __init__(self, ec, logic):
		Level.__init__(self, ec, logic)

		#Frame set at Level
		t = self.frame

		w0 = Wall((-100, 0), (150, 1), self.camera)
		self.om.add_wall(w0)

		w1 = Wall((150, 0), (50, 1), self.camera)
		self.om.add_wall(w1)

		m0 = Machine(t, self.eventd, self.camera, self.svt)
		m0.set_position(-50-7, 0)
		self.om.add(m0)

		#Save reference on exit machine for compare later
		self.m1 = MachineExit((180, 0), self.camera, self.eventd, self)
		self.om.add(self.m1)

		self.m2 = MachineStart(t, self.eventd, self.camera, self.svt)
		self.m2.set_position(-7, 0)
		self.om.add(self.m2)

		ps0 = PlatformSimple((80, 0), (40, 1), self.camera)
		self.om.add(ps0)
		self.om.add_wall(ps0)

		lb0 = LeverButton((-30-50, 0), self.eventd, self.camera, self.svt, self.om)
		lb0.set_target(ps0)
		self.om.add(lb0)

		b0 = Boy(t, self.eventd, self.camera, self.svt, self.om)
		b0.set_position(0, 0)
		self.om.add(b0)

		self.camera.follow(b0)
		b0.activate(t)

class Level2(Level):
	def __init__(self, ec, logic):
		Level.__init__(self, ec, logic)

		#Frame set at Level
		t = self.frame

		w0 = Wall((0, 0), (200, 1), self.camera)
		self.om.add_wall(w0)

		w1 = Wall((450, 0), (100, 1), self.camera)
		self.om.add_wall(w1)

		m0 = Machine(t, self.eventd, self.camera, self.svt)
		m0.set_position(100-7, 0)
		self.om.add(m0)

		#Save reference on exit machine for compare later
		self.m1 = MachineExit((500, 0), self.camera, self.eventd, self)
		self.om.add(self.m1)

		self.m2 = MachineStart(t, self.eventd, self.camera, self.svt)
		self.m2.set_position(150-7, 0)
		self.om.add(self.m2)

		ps0 = PlatformSimple((250-20, 0), (50+40, 1), self.camera)
		self.om.add(ps0)
		self.om.add_wall(ps0)

		lb0 = LeverButton((50, 0), self.eventd, self.camera, self.svt, self.om)
		lb0.set_target(ps0)
		self.om.add(lb0)

		ps1 = PlatformSimple((350-20, 0), (50+40, 1), self.camera)
		self.om.add(ps1)
		self.om.add_wall(ps1)

		lb1 = LeverButton((70, 0), self.eventd, self.camera, self.svt, self.om)
		lb1.set_target(ps1)
		self.om.add(lb1)

		b0 = Boy(t, self.eventd, self.camera, self.svt, self.om)
		b0.set_position(150, 0)
		self.om.add(b0)

		self.camera.follow(b0)
		b0.activate(t)

class Level3(Level):
	def __init__(self, ec, logic):
		Level.__init__(self, ec, logic)

		#Frame set at Level
		t = self.frame

		# Walls
		w0 = Wall((0, 0), (50, 1), self.camera)
		self.om.add_wall(w0)

		w1 = Wall((150, 0), (125, 1), self.camera)
		self.om.add_wall(w1)

#		w2 = Wall((300, 0), (50, 1), self.camera)
#		self.om.add_wall(w2)

		w3 = Wall((375, 0), (50, 1), self.camera)
		self.om.add_wall(w3)

		w4 = Wall((525, 0), (50, 1), self.camera)
		self.om.add_wall(w4)


		#Machines
		m1 = Machine(t, self.eventd, self.camera, self.svt)
		m1.set_position(0-7, 0)
		self.om.add(m1)

		m0 = Machine(t, self.eventd, self.camera, self.svt)
		m0.set_position(250-7, 0)
		self.om.add(m0)

		#Exit machine
		self.m1 = MachineExit((550-7, 0), self.camera, self.eventd, self)
		self.om.add(self.m1)

		#Start machine
		self.m2 = MachineStart(t, self.eventd, self.camera, self.svt)
		self.m2.set_position(200-7, 0)
		self.om.add(self.m2)

		#Platforms
		ps0 = PlatformSimple((75, 0), (50, 1), self.camera)
		self.om.add(ps0)
		self.om.add_wall(ps0)

		ps1 = PlatformSimple((300, 0), (50, 1), self.camera)
		self.om.add(ps1)
		self.om.add_wall(ps1)

		ps2 = PlatformSimple((450, 0), (50, 1), self.camera)
		self.om.add(ps2)
		self.om.add_wall(ps2)

		#Levers
		lc0 = LogicConnector()

		lb0 = LeverButton((175, 0), self.eventd, self.camera, self.svt, self.om)
		lb0.set_target(lc0)
		self.om.add(lb0)

		lc0.add_in(lb0)
		lc0.add_out(ps0)
		lc0.add_out(ps1)

		lb1 = LeverButton((400, 0), self.eventd, self.camera, self.svt, self.om)
		lb1.set_target(ps2)
		self.om.add(lb1)

		#Boy
		b0 = Boy(t, self.eventd, self.camera, self.svt, self.om)
		b0.set_position(200, 0)
		self.om.add(b0)

		self.camera.follow(b0)
		b0.activate(t)


class Level4(Level):
	def __init__(self, ec, logic):
		Level.__init__(self, ec, logic)

		#Frame set at Level
		t = self.frame

		# Walls
		w0 = Wall((0, 0), (300, 1), self.camera)
		self.om.add_wall(w0)

		w1 = Wall((525, 150), (50, 1), self.camera)
		self.om.add_wall(w1)

		m0 = Machine(t, self.eventd, self.camera, self.svt)
		m0.set_position(200-7, 0)
		self.om.add(m0)

		#Exit machine
		me = MachineExit((550-7, 150), self.camera, self.eventd, self)
		self.om.add(me)

		#Start machine
		ms = MachineStart(t, self.eventd, self.camera, self.svt)
		ms.set_position(150-7, 0)
		self.om.add(ms)

		#Platforms
		ps0 = PlatformSimple((325, 50), (75, 1), self.camera)
		self.om.add(ps0)
		self.om.add_wall(ps0)

		ps1 = PlatformSimple((375, 100), (75, 1), self.camera)
		self.om.add(ps1)
		self.om.add_wall(ps1)

		ps2 = PlatformSimple((425, 50), (75, 1), self.camera)
		self.om.add(ps2)
		self.om.add_wall(ps2)

		ps3 = PlatformSimple((475, 100), (75, 1), self.camera)
		self.om.add(ps3)
		self.om.add_wall(ps3)

#		#Levers
		lb0 = LeverButton((25, 0), self.eventd, self.camera, self.svt, self.om)
		lb0.set_target(ps0)
		self.om.add(lb0)

		lb1 = LeverButton((50, 0), self.eventd, self.camera, self.svt, self.om)
		lb1.set_target(ps1)
		self.om.add(lb1)

		lb2 = LeverButton((75, 0), self.eventd, self.camera, self.svt, self.om)
		lb2.set_target(ps2)
		self.om.add(lb2)

		lb3 = LeverButton((100, 0), self.eventd, self.camera, self.svt, self.om)
		lb3.set_target(ps3)
		self.om.add(lb3)

		#Boy
		b0 = Boy(t, self.eventd, self.camera, self.svt, self.om)
		b0.set_position(150, 0)
		self.om.add(b0)

		self.camera.follow(b0)
		b0.activate(t)


class Level5(Level):
	def __init__(self, ec, logic):
		Level.__init__(self, ec, logic)

		#Frame set at Level
		t = self.frame

		# Walls
		self.om.add_wall(Wall((0, 150), (50, 1), self.camera))
		self.om.add_wall(Wall((225, 0), (100, 1), self.camera))
		self.om.add_wall(Wall((400, 0), (100, 1), self.camera))
		self.om.add_wall(Wall((575, 100), (50, 1), self.camera))


		# Machines
		m0 = Machine(t, self.eventd, self.camera, self.svt)
		m0.set_position(450-7, 0)
		self.om.add(m0)

		m1 = Machine(t, self.eventd, self.camera, self.svt)
		m1.set_position(225-7, 0)
		self.om.add(m1)

		m2 = Machine(t, self.eventd, self.camera, self.svt)
		m2.set_position(0-7, 150)
		self.om.add(m2)

		#Exit machine
		me = MachineExit((600-7, 100), self.camera, self.eventd, self)
		self.om.add(me)

		#Start machine
		ms = MachineStart(t, self.eventd, self.camera, self.svt)
		ms.set_position(475-7, 0)
		self.om.add(ms)

		#Platforms
		ps0 = PlatformSimple((75, 150), (25, 1), self.camera)
		self.om.add(ps0)
		self.om.add_wall(ps0)

		ps1 = PlatformSimple((125, 100), (25, 1), self.camera)
		self.om.add(ps1)
		self.om.add_wall(ps1)

		ps2 = PlatformSimple((175, 50), (25, 1), self.camera)
		self.om.add(ps2)
		self.om.add_wall(ps2)

		ps3 = PlatformSimple((350, 0), (25, 1), self.camera)
		self.om.add(ps3)
		self.om.add_wall(ps3)

		ps4 = PlatformSimple((525, 0), (25, 1), self.camera)
		self.om.add(ps3)
		self.om.add_wall(ps3)

#		#Levers
		lb0 = LeverButton((250, 0), self.eventd, self.camera, self.svt, self.om)
		lb0.set_target(ps0)
		self.om.add(lb0)

		lb1 = LeverButton((265, 0), self.eventd, self.camera, self.svt, self.om)
		lb1.set_target(ps1)
		self.om.add(lb1)

		lb2 = LeverButton((280, 0), self.eventd, self.camera, self.svt, self.om)
		lb2.set_target(ps2)
		self.om.add(lb2)

		lb3 = LeverButton((425, 0), self.eventd, self.camera, self.svt, self.om)
		lb3.set_target(ps3)
		self.om.add(lb3)

		lb4 = LeverButton((25, 150), self.eventd, self.camera, self.svt, self.om)
		lb4.set_target(ps4)
		self.om.add(lb4)

		#Boy
		b0 = Boy(t, self.eventd, self.camera, self.svt, self.om)
		b0.set_position(475, 0)
		self.om.add(b0)

		self.camera.follow(b0)
		b0.activate(t)


class GameLogic:
	def __init__(self):
		self.ec = EventControl()
		self.exit = False
		self.levels = [Level1, Level2, Level3, Level4, Level5]
		self.levelnum = 0
		self.level = None
		self.scenes = []
		self.init_level()
		self.scenes.append(self.level)
		self.scenes.append(SceneControls(self.ec, self))
		self.scenes.append(SceneStart(self.ec, self))

	def play(self):
		clock = pygame.time.Clock()

		while not self.exit:

			# Get last scene
			scene = self.scenes[-1]
			scene.update()

			pygame.display.update()
			pygame.display.flip()

			clock.tick(50)

	def next_level(self):
		'Replace actual level by the next one'

		print 'GameLogic next_level() called'

		self.levelnum += 1

		if(self.levelnum >= len(self.levels)):
			print 'End of game!!'
			sys.exit('')

		print 'GameLogic starting level {}', self.levelnum+1

		self.init_level()

		if(self.scenes == []): self.scenes.append(self.level)
		else: self.scenes[0] = self.level

	def init_level(self):
		self.level = self.levels[self.levelnum](self.ec, self)

	def restart_level(self, text):
		self.level = self.levels[self.levelnum](self.ec, self)
		self.scenes[-1] = self.level
		failure = SceneFailure(self.ec, text, self)
		self.scenes.append(failure)

	def pop_scene(self):
		self.scenes.pop()



# SVT = Sistema de viajes temporales
class SVT:
	def __init__(self, om, eventd, cam, level):
		self.recordlist = []	#Grabaciones por personaje
		self.clonelist = []		#Clones al encender las máquinas
		self.blocklist = []		#Máquinas que han de bloquearse

		self.i = -1
		self.level = level
		self.om = om
		self.eventd = eventd
		self.cam = cam
		self.inc_t = 0
		self.travels = []
		self.clones = []

	def rel(self, absolute_t):
		'Obtiene el tiempo relativo a t'
		return absolute_t - self.inc_t

	def travel(self, time_now, time_past):
		'Viaja al pasado en el tiempo'
		print 'svt:\t\ttraveling {} <--------------------- {}'.format(
			time_past, time_now)
		self.inc_t += time_now - time_past


	def find_last_machine(self, m):
		'Encuentra la última clonación producida por una máquina'
		last = None
		for t in self.clonelist:
			if t[0] == m:
				if last == None: last = t
				elif last[4] < t[4]:
					last = t
		return last

	def find_last_clone(self):
		'Encuentra la última clonación producida por cualquier máquina'
		last = None
		for t in self.clonelist:
			if last == None: last = t
			elif last[4] < t[4]:
				last = t
		return last

	def find_boy(self, boy):
		'Encuentra la grabación correspondiente a un personaje'
		entry = None
		for t in self.recordlist:
			if t[0] == boy:
				if entry != None:
					print 'svt:\t\tBUG:multiple records'
					sys.exit('BUG')
				entry = t

		return entry

	def find_rec(self, rec):
		for t in self.recordlist:
			if t[1] == rec:
				return t

	#def do_travel():

#	def do_clones():
#		'Realiza las clonaciones pendientes'
#		for cl in self.clones:
#			machine = cl[0]
#			rel_t = cl[1]
#
#
#		self.clones = []

	def on(self, machine, rel_t):
		print 'svt:\t\tcloning world, by machine{} powered on at t={}'.format(
			machine.i, rel_t)
		clone = self.om.clone()
		boy_clone = self.eventd.active_boy.clone()
		abs_t = rel_t + self.inc_t
		item = (machine, clone, rel_t, boy_clone, abs_t)
		self.clonelist.append(item)
		#print 'Lista de clones ' + str(self.clonelist)

	def rec_play(self, rel_t):
		'Pone todas las grabaciones a reproducirse en rel_t'
		print 'svt:\t\tall recording started at t={}'.format(
			rel_t)
		for t in self.recordlist:
			t[1].play(rel_t)

	def print_time(self, rel_t):
		w, h = screen.get_size()
		timestr = "%0.1f" % (rel_t/FPS)
		label = font_time.render(timestr, 1, (100,100,100))
#		screen.blit(label, (280, 30))
		screen.blit(label, (w/2-30, h-20-label.get_height()/2))

	def enable_machines(self, m):
		'Activa todas las máquinas excepto la actual'

	#def block_machine(self, entry, machine)

	def off(self, machine, rel_t):
		'Viaje en el tiempo'
		tm = self.find_last_machine(machine)
		tb = self.find_boy(self.eventd.active_boy)

		oldboy = tb[0]
		machine = tm[0]
		oldrec = tb[1]
		start = tm[2]

		self.travel(rel_t, start)

		oldrec.finish(rel_t)

		self.om.disable_boys()

		print 'svt:\t\trestoring previous clone'
		#print str(tm[1])
		self.om.restore(tm[1])

		#TODO: Por que hace falta actualizar ahora?
#		oldboy.update(start)
#		machine.update(start)

		self.rec_play(start)

		#print 'Lista de grabaciones ' + str(self.recordlist)

		#print 'Velocidad de boy al restaurarlo: ' +
		#	str((oldboy.vx, oldboy.vy))

		#print 'Rel_t ' + str(rel_t) + ' restaurando ' + str(tm[1])

		b = Boy(start, self.eventd, self.cam, self, self.om)
		# TODO: Ajustar esta posicion para que quede en el centro
		b.set_position(machine.rx +7, machine.ry)
		self.om.add(b)

		self.cam.follow(b)
		b.activate(start)

		new_entry = self.find_boy(b)
		newrec = new_entry[1]
		#Bloquear la máquina al restaurarla.
		print 'svt:\t\tadding machine{} to blocklist'.format(machine.i)
		self.blocklist.append((machine, newrec, oldrec))

		# Y bloquearla de inmediato, ya que rec no avisará, pues ya ha
		# comenzado.
		self.block_machine(newrec)

	def new_boy(self, boy, rel_t):
		if self.eventd.active_boy == None: return
		if boy.i != self.eventd.active_boy.i: return

		rec = Recording(rel_t, self)
		rec.i = boy.i
		boy_clone = boy.clone()
		print 'svt:\t\tcloning boy{}'.format(boy.i)
		#print str(boy_clone)
		self.recordlist.append((boy, rec, boy_clone))
		#print self.recordlist

	def update(self, abs_t):
		'Actualiza todo el juego usando el tiempo absoluto'
		rel_t = self.rel(abs_t)
		self.om.update(rel_t)
		self.dispatch(rel_t)
		self.eventd.dispatch(rel_t)
		# El tiempo puede cambiar ahora despues de actualizar eventd
		rel_t = self.rel(abs_t)
		self.print_time(rel_t)

	def dispatch(self, rel_t):
		'Envía los eventos de las grabaciones a los personajes'

		#print str(rel_t)+':Enviando eventos grabados a los personajes'
		for tup in self.recordlist:
			eventl = tup[1].get(rel_t)
			#print eventl
			for ev in eventl:
				boy = tup[0]
				print 'svt:\t\tsending recorded event to boy{}'.format(boy.i)
				boy.event(ev, rel_t, None)
				#print str(rel_t)+':Enviado a boy'+str(tup[0].i)

	def key_event(self, e, rel_t):
		'Envía los eventos del teclado a las grabaciones'
		for tup in self.recordlist:
			eventl = tup[1].event(rel_t, e)

	def end_record(self, rec):
		'Al terminar una grabación, quitar al personaje'
		tup = self.find_rec(rec)
		boy = tup[0]
		boy.disable()

		# Desbloquear la máquina
		# TODO: Ya había sido desbloqueada por la propia máquina?
		block = self.find_block_by_end_rec(rec)
		machine = block[0]
		print 'svt:\t\tunblocking machine{}'.format(machine.i)
		machine.unblock()

	def find_block_by_start_rec(self, rec):
		for t in self.blocklist:
			if t[1] == rec:
				return t
		return None

	def find_block_by_end_rec(self, rec):
		for t in self.blocklist:
			if t[2] == rec:
				return t
		return None

	def print_blocklist(self):
		print 'svt:\t\tblocklist:'
		for t in self.blocklist:
			machine = t[0]
			start_rec = t[1]
			end_rec = t[2]
			start_entry = self.find_rec(start_rec)
			end_entry = self.find_rec(end_rec)
			start_boy = start_entry[0]
			end_boy = end_entry[0]
			print '\tmachine{}, start rec{} boy{}, end rec{} boy{}'.format(
				machine.i, start_rec.i, start_boy.i,
				end_rec.i, end_boy.i)

	def block_machine(self, rec):
		# Bloquear la máquina
		print 'svt:\t\tblock_machine'
		self.print_blocklist()
		block = self.find_block_by_start_rec(rec)
		if(block == None):
			print 'svt:\t\tno need to block machine for rec{}'.format(rec.i)
			return

		machine = block[0]
		end_rec = block[2]
		end_entry = self.find_rec(end_rec)
		block_boy = end_entry[0]
		print 'svt:\t\tblocking machine{} by boy{}'.format(machine.i, block_boy.i)
		machine.block(block_boy)

	def start_record(self, rec):
		'Al comienzo de una grabación, restaurar el personaje'
		tup = self.find_rec(rec)
		boy = tup[0]
		boy_clone = tup[2]
		print 'svt:\t\tstarting previous recording of boy{}'.format(boy.i)
		print 'svt:\t\trestoring previous clone of boy{}'.format(boy.i)
		print str(boy_clone)

		print 'svt:\t\tstarting recording for boy{}'.format(boy.i)
		boy.enable()
		boy.restore(boy_clone)

		#Block machine by the boy who activated in the past
		self.block_machine(rec)

	def level_event(self, rel_t, code):
		print 'svt:\t\tsending event code = {} to level'.format(code)

		d = {}
		d['code'] = code
		ev = pygame.event.Event(pygame.USEREVENT, d)
		self.eventd.event_to(ev, self, self.level, rel_t)


#		# Find boy rec and restart it
#		rec_entry = self.find_boy(boy)
#		rec = rec_entry[1]
#
#		clone_entry = self.find_last_clone()
#		# Al menos ha de existir la primera clonación hecha por MachineStart
#		if clone_entry == None:
#			print 'svt:\t\tno clones found. BUG'
#			sys.exit('BUG')
#
#		tm = clone_entry
#		tb = rec_entry
#
#		oldboy = tb[0]
#		machine = tm[0]
#		oldrec = tb[1]
#		start = tm[2]
#
#		self.travel(rel_t, start)
#
#		self.om.disable_boys()
#
#		print 'svt:\t\trestoring previous clone'
#		#print str(tm[1])
#		self.om.restore(tm[1])
#
#		self.rec_play(start)
#
#		#Reset the recording for the active boy
#		rec.restart(rel_t)
#
#		#Bloquear la máquina. Si es MachineStart no se bloqueará
#		self.block_machine(rec)


#class Game:
#
#	def level_test(self, t, eventd, camera, om, svt):
#		w0 = Wall((-50, 0), (400, 1), camera)
#		om.add_wall(w0)
#
#		w1 = Wall((50, 50), (200, 1), camera)
#		om.add_wall(w1)
#
#		w2 = Wall((350+40, 0), (200, 1), camera)
#		om.add_wall(w2)
#
#		m0 = Machine(t, eventd, camera, svt)
#		m0.set_position(100, 0)
#		om.add(m0)
#
#		m1 = Machine(t, eventd, camera, svt)
#		m1.set_position(200, 0)
#		om.add(m1)
#
#		m2 = Machine(t, eventd, camera, svt)
#		m2.set_position(300, 0)
#		om.add(m2)
#
#		m3 = Machine(t, eventd, camera, svt)
#		m3.set_position(500, 0)
#		om.add(m3)
#
#		lb0 = LeverButton((70, 0), eventd, camera, svt, om)
#		om.add(lb0)
#
#		b0 = Boy(t, eventd, camera, svt, om)
#		b0.set_position(0, 0)
#		om.add(b0)
#
#		camera.follow(b0)
#		b0.activate(t)
#
#	def level1(self, t, eventd, camera, om, svt):
#		w0 = Wall((-50, 0), (100, 1), camera)
#		om.add_wall(w0)
#
#		w1 = Wall((150, 0), (50, 1), camera)
#		om.add_wall(w1)
#
#		m0 = Machine(t, eventd, camera, svt)
#		m0.set_position(-7, 0)
#		om.add(m0)
#
#		m1 = MachineExit((180, 0), camera, eventd)
#		om.add(m1)
#
#		ps0 = PlatformSimple((80, 0), (40, 1), camera)
#		om.add_wall(ps0)
#
#		lb0 = LeverButton((-30, 0), eventd, camera, svt, om)
#		lb0.set_target(ps0)
#		om.add(lb0)
#
#		b0 = Boy(t, eventd, camera, svt, om)
#		b0.set_position(0, 0)
#		om.add(b0)
#
#		camera.follow(b0)
#		b0.activate(t)
#
#	def play(self):
#		#t = time.perf_counter()
#		frame = 0
#		t = frame
#		clock = pygame.time.Clock()
#		om = ObjectManager()
#		eventctrl = EventControl()
#		eventd = EventDaemon(eventctrl, om)
#		camera = Camera()
#		svt = SVT(om, eventd, camera)
#		eventd.set_svt(svt)
#		om.set_eventd(eventd)
#
#		self.level1(t, eventd, camera, om, svt)
#
#		while True:
#			#print "-- Loop start --"
#
#			#t = time.perf_counter()
#			t = frame
#
#			screen.fill((0, 0, 0))
#
#			svt.update(t)
#
#			pygame.display.update()
#			pygame.display.flip()
#
#			#print "-- Loop end --"
#
#			clock.tick(50)
#			frame += 1


pygame.init()
font_time = pygame.font.SysFont("Ubuntu Mono", 30)
terminus = pygame.font.SysFont("terminus", 16)
font_title = pygame.font.SysFont("Sans Serif", 30)
screen = pygame.display.set_mode((320*2, 240*2))


if __name__ == '__main__':
	game = GameLogic()
	game.play()
