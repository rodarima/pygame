import sys, pygame, time
from pympler import asizeof

class Recording():
	def __init__(self):
		self.t = time.perf_counter()
		self.events = []

	def event(self, e):
		self.t = time.perf_counter()
		self.events.append((self.t, e))

	def new_frame(self):
		self.t = time.perf_counter()
	
	def print(self):
		print(asizeof.asizeof(self.events)/len(self.events))
		for e in self.events:
			print(e)



pygame.init()

size = width, height = 640, 480
speed = [2, 2]
black = 0, 0, 0
n = False

screen = pygame.display.set_mode(size)

clock = pygame.time.Clock()
recording = Recording()
while 1:
	recording.new_frame()

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			sys.exit()
		elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
			recording.event(event)
			if event.key == pygame.K_SPACE:
				recording.print()

	clock.tick(30)



