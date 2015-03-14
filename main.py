import pygame, pypong, sys
from pypong.player import QLearningPlayer, BasicAIPlayer, KeyboardPlayer, MousePlayer
    
def run():
    configuration = {
        'screen_size': (686,488),
        'paddle_image': 'assets/paddle.png',
        'paddle_left_position': 84.,
        'paddle_right_position': 594.,
        'paddle_velocity': 6.,
        'paddle_bounds': (0, 488), # This sets the upper and lower paddle boundary.The original game didn't allow the paddle to touch the edge, 
        'line_image': 'assets/dividing-line.png',
        'ball_image': 'assets/ball.png',
        'ball_velocity': 4.,
        'ball_velocity_bounce_multiplier': 1.105,
        'ball_velocity_max': 32.,
        'score_left_position': (141, 30),
        'score_right_position': (473, 30),
        'digit_image': 'assets/digit_%i.png',
        'sound_missed': 'assets/missed-ball.wav',
        'sound_paddle': 'assets/bounce-paddle.wav',
        'sound_wall': 'assets/bounce-wall.wav',
        'sound': False,
    }
    pygame.mixer.pre_init(22050, -16, 2, 1024)
    pygame.init()
    display_surface = pygame.display.set_mode(configuration['screen_size'])
    output_surface = display_surface.copy().convert_alpha()
    output_surface.fill((0,0,0))
    #~ debug_surface = output_surface.copy()
    #~ debug_surface.fill((0,0,0,0))
    debug_surface = None
    clock = pygame.time.Clock()
    input_state = {'key': None, 'mouse': None}
    
    # Prepare game
    #~ player_left = KeyboardPlayer(input_state, pygame.K_w, pygame.K_s)
    #~ player_right = MousePlayer(input_state)
    savefile=None
    loadfile=None
    stateSpase="PP_BV_BVR"
    if(len(sys.argv)>1):
        stateSpase=sys.argv[1]
        if(len(sys.argv)>2):
            savefile=sys.argv[2]
            if(len(sys.argv)>3):
                loadfile=sys.argv[3]
    player_left = QLearningPlayer(stateSpase, savefile, loadfile)
    player_right = BasicAIPlayer()
    game = pypong.Game(player_left, player_right, configuration)
    
    if savefile==None:
        savefile="no_save"
    logFileName = stateSpase+"_"+savefile+".log"
    # Main game loop
    timestamp = 1
    counter = 0
    while game.running:
        #clock.tick(60)
        counter += 1
        now = pygame.time.get_ticks()
        if timestamp > 0 and timestamp < now:
            timestamp = now + 5000
            #print clock.get_fps()
        #input_state['key'] = pygame.key.get_pressed()
        #input_state['mouse'] = pygame.mouse.get_pos()
        game.update()
        if(counter%50000 == 0 or counter%2000000 < 3000):
            print float(game.score_left.score)/(game.score_right.score+1), game.player_left.countNonZero/game.player_left.updateCount
            print game.player_left.lastAction, game.player_left.lastActionQValues
            print game.player_left.lastState
            game.draw(output_surface)
            #~ pygame.surfarray.pixels_alpha(output_surface)[:,::2] = 12
            display_surface.blit(output_surface, (0,0))
            if debug_surface:
                display_surface.blit(debug_surface, (0,0))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    game.running = False
        
if __name__ == '__main__': run()
