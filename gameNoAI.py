import pygame
import neat
import time
import os
import random
pygame.font.init()

WIN_WIDTH = 500
WIN_HEIGHT = 800

BIRD_IMGS = [
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png"))),
]     #Doubling size of each img
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))
STAT_FONT = pygame.font.SysFont("comicsans", 50)

class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0     #Keep track when we last jumped
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5        #Main ref point in pygame window is top left. Negative velocity @ middle of window makes upward motion
        self.tick_count = 0     #reset counter tracking when jump happenned
        self.height = self.y

    def move(self):     #can use while true, bird.move() to test the movement func and adjust
        self.tick_count += 1
        d = self.vel*self.tick_count + 1.5*self.tick_count**2       #calc how many pixels up to move this frame, using phys parab equation
        
        if d >= 16:     #Set terminal veloc for moving down (dont want infin acceleration)
            d = 16

        if d < 0:       #Fine tune movement, just add 2 more pixels of movement if we're moving up; can be changed
            d -= 2

        self.y = self.y + d
        if d < 0 or self.y < self.height + 50:      #if moving up or the current y-pos is less than the original height + 50
            if self.tilt < self.MAX_ROTATION:       #if tilt isn't max, go to max (point up)
                self.tilt = self.MAX_ROTATION       #pos tilt is counter  clockwise
        else:                                       #otherwise tilt down
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1     #keep track of how many ticks of the image of the bird we've shown

        if self.img_count < self.ANIMATION_TIME:       #swap between the 3 bird images based on counter
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0
        
        if self.tilt <= -80:        #if pointing down, don't flap.
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        rotated_image = pygame.transform.rotate(self.img, self.tilt)      #rotates from top left hand corner, not center
        new_rect = rotated_image.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center)    #get rect using center of orig image
        win.blit(rotated_image, new_rect.topleft)       #draw to window

    def get_mask(self):     #used when doing collisions with objects
        return pygame.mask.from_surface(self.img)



class Pipe:
    GAP = 200       #how much space b/w pipe
    VEL =  5

    def __init__(self, x):
        self.x = x
        self.height = 0     #this is where bottom edge of top pipe lies

        self.top = 0        #where draw top pipe
        self.bottom = 0     #where draw bottom pipe
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)     #Flip pip eover and store it
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False     #track if bird passed thru
        self.set_height()       #define where top and bottom pipes, and how tall they are

    def set_height(self):
        self.height = random.randrange(40, 450)
        self.top = self.height - self.PIPE_TOP.get_height()     #find the top edge of the top pipe (do bottom edge of top pipe minus height of top pipe = get coord of top of top pipe)
        self.bottom = self.height + self.GAP                    #remember, subtract height means go up; self.bottom is the top edge of bottom pipe

    def move(self):     #move to left
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))         #draw top pipe using its top
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))   #draw bottom pip using its top

    def collide(self, bird):        #use mask to get pixel-perfect collision, not by boundingrect
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        
        top_offset = (self.x - bird.x, self.top - round(bird.y))    #offset from top pipe (w/ its top edge) to bird
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))      #offset from bottom pipe (w/ its top edge) to bird

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)     #tell point of overlap b/w bird mask and bot pipe; returns None if no collision
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:      #if either collision exists
            return True
        
        return False
    


class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):     #have 2 bases side by side. 
        self.x1 -= self.VEL     #x1 is left edge of left base
        self.x2 -= self.VEL     #x2 left edge of right base

        if self.x1 + self.WIDTH < 0:            #if left base is completely offscreen to left
            self.x1 = self.x2 + self.WIDTH      #move x1 (and left base) to right edge of right base; now prev right base is on the left

        if self.x2 + self.WIDTH < 0:            #if x2 base is completely offscreen to left
            self.x2 = self.x1 + self.WIDTH      #move it to the right edge of the x1 base

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))



def draw_window(win, bird, pipes, base, score):
    win.blit(BG_IMG, (0,0))     #draw bg using top left corner coords
    for pipe in pipes:          #have list of pipes bcx will keep adding more
        pipe.draw(win)

    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    base.draw(win)
    bird.draw(win)
    pygame.display.update()



def main():     #runs main loop of game
    bird = Bird(230, 350)
    base = Base(730)
    pipes = [Pipe(650)]     #have list of pipes bcx will keep adding more
    score = 0

    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))  #init game window
    clock = pygame.time.Clock()
    run = True

    while run:
        clock.tick(30)      #run at most 30 ticks per second
        for event in pygame.event.get():        #keeps track of user events (run mouse, button, etc)
            if event.type == pygame.QUIT:       #if clicked red x on window
                run = False
        #bird.move()


        #Pipe management
        add_pipe = False    #flag checking if need add a new pipe (old one done)
        rem = []            #list of pipes to be removed (they're offscreen)
        for pipe in pipes:
            if pipe.collide(bird):
                pass
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:        #if completely offscreen to the left
                rem.append(pipe)

            if not pipe.passed and pipe.x < bird.x:         #if bird went thru and havent set 'passed' flag yet, set it true
                pipe.passed = True
                add_pipe = True
            pipe.move()

        if add_pipe:
            score += 1
            pipes.append(Pipe(650))

        for r in rem:
            pipes.remove(r)



        #Bird movement
        if bird.y + bird.img.get_height() >= 730:       # if bot of bird touching ground
            pass

        base.move()
        draw_window(win, bird, pipes, base, score)

    pygame.quit()
    quit()


main()