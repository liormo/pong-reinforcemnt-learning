import pygame, random, math, datetime, pickle

class QLearningPlayer(object):
    def __init__(self, savefile, loadfile):
        self.qValues = {}
        self.lastState = None
        self.lastAction = None
        self.alpha = 0.2
        self.discount = 0.9
        self.actions = [-1, 0, 1]
        self.reward = 0
        self.updateCount=0.0
        self.countNonZero=0.0
        self.lastActionQValues=[]
        self.getState = self.getStateBP_PP_VR
        self.savefile = savefile
        if loadfile!=None:
            self.loadQTable(loadfile)
        
    def update(self, paddle, game):
        state = self.getState(paddle, game)
        
        
        actionQValues = [self.getQValue(state, a) for a in self.actions]
        
        action = random.choice([a for a in self.actions if self.getQValue(state, a) == max(actionQValues)])
        if(random.randrange(210)==1):
            action = random.choice(self.actions)
            
            
        if max(actionQValues)>0 or min(actionQValues)<0:
            self.countNonZero += 1
        
        self.updateCount += 1
        if self.savefile!=None and self.updateCount%5000000==0:
            self.writeQTableToFile()
            
            
        paddle.direction = action
        #paddle.direction = random.choice([-1, 0, 1])
        lastQValue = self.getQValue(self.lastState, self.lastAction)
        self.qValues[(self.lastState, self.lastAction)] = float(lastQValue + self.alpha*(self.reward + self.discount*max(actionQValues) - lastQValue))
        self.lastState = state
        self.lastAction = action
        self.lastActionQValues = actionQValues
        self.reward = 0

    def hit(self):
        self.reward = 5
            
    def lost(self):
        # If we lose, randomise the bias again
        self.bias = random.random() - 0.5
        self.reward = -100
        
    def won(self):
        self.reward = 10
        
    def getQValue(self, state, action):
        if (state, action) in self.qValues:
            return self.qValues[(state, action)]
            
        return 0
        
    # PP=paddle position
    # BP=ball position
    # VR=variable resolution
    def getStateBP_PP(self, paddle, game):
        return (game.ball.rect.x, game.ball.rect.y, paddle.rect.y)

    def getStateBP_PP_VR(self, paddle, game):
        if(game.ball.rect.x<game.paddle_left.rect.right):
            state="lost"
        else:
            resolution = math.floor((max(1,game.ball.rect.x-game.paddle_left.rect.right+1)*100)**(1.0/3))-3
            state = (resolution, math.floor(game.ball.rect.y/(1+((resolution**2)/100))), math.floor(paddle.rect.y/resolution))  
        return state      
        
        
    def writeQTableToFile(self):
        print "writing"
        f=open(self.savefile,'w')
        pickle.dump(self.qValues, f)
        f.close()
        print "writen"
        
    def loadQTable(self, fileName):
        f=open(fileName, 'r')
        self.qValues = pickle.load(f)
        f.close()

class BasicAIPlayer(object):
    def __init__(self):
        self.bias = random.random() - 0.5
        self.hit_count = 0
        
    def update(self, paddle, game):
        # Dead simple AI, waits until the ball is on its side of the screen then moves the paddle to intercept.
        # A bias is used to decide which edge of the paddle is going to be favored.
        if (paddle.rect.x < game.bounds.centerx and game.ball.rect.x < game.bounds.centerx) or (paddle.rect.x > game.bounds.centerx and game.ball.rect.x > game.bounds.centerx):
            delta = (paddle.rect.centery + self.bias * paddle.rect.height) - game.ball.rect.centery 
            if abs(delta) > paddle.velocity:
                if delta > 0:
                    paddle.direction = -1
                else:
                    paddle.direction = 1
            else:
                paddle.direction = 0
        else:
            paddle.direction = 0

    def hit(self):
        self.hit_count += 1
        if self.hit_count > 6:
            self.bias = random.random() - 0.5 # Recalculate our bias, this game is going on forever
            self.hit_count = 0
            
    def lost(self):
        # If we lose, randomise the bias again
        self.bias = random.random() - 0.5
        
    def won(self):
        pass
        
class KeyboardPlayer(object):
    def __init__(self, input_state, up_key=None, down_key=None):
        self.input_state = input_state
        self.up_key = up_key
        self.down_key = down_key
        
    def update(self, paddle, game):
        if self.input_state['key'][self.up_key]:
            paddle.direction = -1
        elif self.input_state['key'][self.down_key]:
            paddle.direction = 1
        else:
            paddle.direction = 0

    def hit(self):
        pass

    def lost(self):
        pass
        
    def won(self):
        pass
        
class MousePlayer(object):
    def __init__(self, input_state):
        self.input_state = input_state
        pygame.mouse.set_visible(False)
        
    def update(self, paddle, game):
        centery = paddle.rect.centery/int(paddle.velocity)
        mousey = self.input_state['mouse'][1]/int(paddle.velocity)
        if centery > mousey:
            paddle.direction = -1
        elif centery < mousey:
            paddle.direction = 1
        else:
            paddle.direction = 0

    def hit(self):
        pass

    def lost(self):
        pass

    def won(self):
        pass
