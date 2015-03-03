import sys, pygame, time
from pympler import asizeof

class Recording():
	def __init__(self):
		self.start_time = time.perf_counter()
		self.events = []
		self.last_get = 0.0

	def event(self, e):
		self.events.append((self.diff_time, e))

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
		print("start:"+str(start_get))
		print("end:"+str(end_get))

		# "Premature optimization is the root of all evil" - Donald Knuth
		#return [e[1] for e in self.events if e[0] >= start_get e[0] < end_get]
		start = -1
		end = -1
		for i in range(len(self.events)):
			e = self.events[i]
			if(e[0] > end_get and i == 0): break
			if(e[0] >= start_get and start == -1):
				print("Got start:" + str(i))
				start = i
			if(e[0] > end_get and end == -1):
				print("Got end:" + str(i))
				end = i
			if(start != -1 and end != -1):
				break

		print(str(start) + " -> " + str(end))
		el = []
		for e in self.events[start:end]:
			print("Adding:" + str(e))
			el.append(e[1])
		return el


pygame.init()

size = width, height = 640, 480
speed = [2, 2]
black = 0, 0, 0
n = False

screen = pygame.display.set_mode(size)

boy = pygame.image.load("../img/boy2.gif")
boy.set_colorkey((0,0,0))
boy = boy.subsurface(0, 0, 13, 21)
x = 30
y = 30
dx = 0
dy = 0
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
			if(not use_record):
				recording.event(event)
			if event.key == pygame.K_SPACE:
				recording.print()
			elif event.key == pygame.K_LEFT:
				dx -= 1
			elif event.key == pygame.K_RIGHT:
				dx += 1
			elif event.key == pygame.K_UP:
				dy -= 1
			elif event.key == pygame.K_DOWN:
				dy += 1
		elif event.type == pygame.KEYUP:
			if(not use_record):
				recording.event(event)
			if event.key == pygame.K_SPACE:
				recording.print()
				use_record = not use_record
				recording.play()
				x = 30
				y = 30
			elif event.key == pygame.K_LEFT:
				dx = 0
			elif event.key == pygame.K_RIGHT:
				dx = 0
			elif event.key == pygame.K_UP:
				dy = 0
			elif event.key == pygame.K_DOWN:
				dy = 0
			

	x += dx
	y += dy

	screen.fill((0,0,0))
	screen.blit(boy, (x, y, 13, 21))
	pygame.display.flip()

	clock.tick(30)



