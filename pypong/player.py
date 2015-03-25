import pygame, random, math, datetime, pickle

def mean(data):
    """Return the sample arithmetic mean of data."""
    n = len(data)
    if n < 1:
        raise ValueError('mean requires at least one data point')
    return sum(data)/float(n) # in Python 2 use sum(data)/float(n)

def meanStdev(data):
    """Calculates the population standard deviation."""
    n = len(data)
    if n < 2:
        raise ValueError('variance requires at least two data points')
    c = mean(data)
    ss = sum((x-c)**2 for x in data)
    pvar = ss/n # the population variance
    return c, pvar**0.5

class AdaptiveQLearningPlayer(object):
    def __init__(self):
        self.minSplitHistory = 10000
        self.wins = 0
        self.loses = 0
        self.hits = 0
        self.splits = 0
        self.qTree = {'l':False, 'p':"1", 'i':1, 't':0.5, 'c':[{'l':True, 'v':[0,0,0], 'h':[[],[],[]], 'p':"1-|"},{'l':True, 'v':[0,0,0], 'h':[[],[],[]], 'p':"1+|"}]}
        self.lastState = None
        self.lastAction = None
        self.lastVars = None
        self.alpha = 0.9
        self.discount = 0.99
        self.actions = [0,1,2]
        self.reward = 0
        self.updateCount=0.0
        self.countNonZero=0.0
        self.lastActionQValues=[]
        self.randActionOdds = 2.0;
        
    def update(self, paddle, game):
        vars = self.getVars(paddle, game)
        state = self.getState(vars)
        action = random.choice([a for a in self.actions if state['v'][a] == max(state['v'])])
        if(random.randrange(int(self.randActionOdds))==1):
            self.randActionOdds+=0.01
            action = random.choice(self.actions)
            
        if max(state['v'])>0 or min(state['v'])<0:
            self.countNonZero += 1
        
        self.updateCount += 1
            
        paddle.direction = action-1
        #paddle.direction = random.choice([-1, 0, 1])
        if(self.lastState != None):
            lastQValue = self.lastState['v'][self.lastAction]
            deltaQ = self.alpha*(self.reward + self.discount*max(state['v']) - lastQValue)
            self.lastState['v'][self.lastAction] += deltaQ
            self.lastState['h'][self.lastAction].append((self.lastVars,deltaQ))
            self.splitIfNeeded(self.lastState,self.lastAction)
        
        self.lastVars = vars
        self.lastState = self.getState(vars)
        self.lastAction = action
            #self.lastActionQValues = state['v']
            #self.lastActionQValues = state['v']
        self.reward = 0

    def hit(self):
        self.hits+=1
        self.reward = 5
            
    def lost(self):
        self.loses+=1
        self.reward = -100
        
    def won(self):
        self.wins+=1
        self.reward = 100
        
    def getVars(self, paddle, game):
        return ((float(game.ball.rect.x)-game.bounds.x)/game.bounds.w, 
                (float(game.ball.rect.centery) - game.paddle_left.rect.centery)/(2*game.bounds.h)+0.5, 
                game.ball.velocity_vec[0]/(2*game.configuration['ball_velocity_max'])+0.5,
                game.ball.velocity_vec[1]/(2*game.configuration['ball_velocity_max'])+0.5,
                (float(game.paddle_left.rect.y)-game.paddle_left.bounds_y[0])/(game.paddle_left.bounds_y[1]-game.paddle_left.rect.h),
                (float(game.paddle_right.rect.y)-game.paddle_right.bounds_y[0])/(game.paddle_right.bounds_y[1]-game.paddle_right.rect.h))
        
    def getState(self, vars, root=None):
        if root == None:
            root = self.qTree
        if(root['l']):
            return root
        else:
            v=list(vars)
            if vars[root['i']] < root['t']:
                v[root['i']] /= root['t']
                r=root['c'][0]
            else:
                v[root['i']] = (v[root['i']]-root['t'])/(1-root['t'])
                r=root['c'][1]
                
            return self.getState(v, r)

    def splitIfNeeded(self, state, action):
        if(len(state['h'][action])>self.minSplitHistory):
            vars,dq = zip(*state['h'][action])
            mue, sig = meanStdev(dq)
            if(abs(mue)<2*sig):
                vn = zip(*[vars[i] for i in range(len(dq)) if dq[i]<0])
                vp = zip(*[vars[i] for i in range(len(dq)) if dq[i]>=0])
                vi=None
                if len(vp) == 0 or len(vp[0]) < 2:
                    pass
                    #mueN, sigN = zip(*[(meanStdev(v)) for v in vn])
                    #vi=sigN.index(max(sigN))
                    #thresh = mueN[vi]
                elif len(vn) == 0 or len(vn[0]) < 2:
                    pass
                    #mueP, sigP = zip(*[(meanStdev(v)) for v in vp])
                    #vi=sigP.index(max(sigP))
                    #thresh = mueP[vi]
                else:   
                    mueN, sigN = zip(*[(meanStdev(v)) for v in vn])
                    mueP, sigP = zip(*[(meanStdev(v)) for v in vp])

                    nn=len(vn[0])
                    np=len(vp[0])
                    tStats = [(mueN[i]-mueP[i])/math.sqrt(sigN[i]*sigN[i]/nn+sigP[i]*sigP[i]/np+0.00001) for i in range(len(mueN))]
                    maxTStat = max(tStats)
                    if maxTStat>0.1:
                        vi=tStats.index(maxTStat)
                        thresh = (mueN[vi] + mueP[vi])/2
                        
                if vi!=None:
                    self.split(state,vi,thresh)
                else:
                    state['h']=[[],[],[]]
    
    def split(self,state,vi,thresh):
        self.splits+=1
        state['l']=False
        state['i'] = vi
        state['t'] = thresh
        state['c'] = [{'l':True, 'v':state['v'], 'h':[[],[],[]], 'p':state['p']+str(vi)+"-|"},{'l':True, 'v':state['v'], 'h':[[],[],[]], 'p':state['p']+str(vi)+"+|"}]
        del state['h']
        del state['v']
        
class QLearningPlayer(object):
    def __init__(self, getState, savefile, loadfile):
        self.wins = 0
        self.loses = 0
        self.hits = 0
        self.qValues = {}
        self.lastState = None
        self.lastAction = None
        self.alpha = 0.4
        self.discount = 0.998
        self.actions = [-1, 0, 1]
        self.reward = 0
        self.updateCount=0.0
        self.countNonZero=0.0
        self.lastActionQValues=[]
        self.getState = eval("self.getState"+getState)
        self.savefile = savefile
        self.randActionOdds = 10.0;
        if loadfile!=None:
            self.loadQTable(loadfile)
        
    def update(self, paddle, game):
        state = self.getState(paddle, game)
        
        
        actionQValues = [self.getQValue(state, a) for a in self.actions]
        
        action = random.choice([a for a in self.actions if self.getQValue(state, a) == max(actionQValues)])
        if(random.randrange(int(self.randActionOdds))==1):
            self.randActionOdds+=0.1
            action = random.choice(self.actions)
            
            
        if max(actionQValues)>0 or min(actionQValues)<0:
            self.countNonZero += 1
        
        self.updateCount += 1
        
        if self.savefile!=None and self.updateCount%50000000==0:
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
        self.hits+=1
        self.reward = 5
            
    def lost(self):
        self.loses+=1
        self.reward = -100
        
    def won(self):
        self.wins+=1
        self.reward = 100
        
    def getQValue(self, state, action):
        if (state, action) in self.qValues:
            return self.qValues[(state, action)]
            
        return 0
        
    # PP=paddle position
    # BP=ball position
    # BV=ball velocety
    # VR=variable resolution
    # BVR=better variable resolution
    def getStateBP_PP(self, paddle, game):
        if(game.ball.rect.x<paddle.rect.right):
            return "lost"
        else:
            resolution = 5
            return (math.floor(game.ball.rect.x/resolution), math.floor(game.ball.rect.y/resolution), math.floor(paddle.rect.y/resolution))

    def getStateBP_PP_VR(self, paddle, game):
        if(game.ball.rect.x<game.paddle_left.rect.right):
            state="lost"
        else:
            resolution = math.floor((max(1,game.ball.rect.x-game.paddle_left.rect.right+1)*100)**(1.0/3))-3
            state = (resolution, math.floor(game.ball.rect.y/(max(.5,resolution-5)*2)), math.floor(paddle.rect.y/resolution))  
        return state      
 
 
    def getStateBP_PP_BV_VR(self, paddle, game):
        if(game.ball.rect.x<game.paddle_left.rect.right):
            state="lost"
        else:
            resolution = math.floor((max(1,game.ball.rect.x-game.paddle_left.rect.right+1)*100)**(1.0/3))-3
            state = (resolution, math.floor(game.ball.rect.y/resolution), math.floor(paddle.rect.y/resolution), math.floor(game.ball.velocity_vec[0]), math.floor(game.ball.velocity_vec[1])) 
             
        return state  

    def getStateBP_PP_BV_BVR(self, paddle, game):
        if(game.ball.rect.x<game.paddle_left.rect.right-10):
            state="lost"
        elif(game.ball.velocity_vec[0]>0):
            state="away"
        else:
            xval = min(26,math.floor((max(1,min(0,game.ball.rect.x-game.paddle_left.rect.right)+1)*70)**(1.0/3))-2)
            relativeY = game.ball.rect.centery-game.paddle_left.rect.centery
            yval = math.copysign(1,relativeY)*min(14,math.floor((80*abs(relativeY))**(1.0/3))-2)
            state = (xval, math.floor(yval/xval), math.floor(paddle.rect.y/xval), math.floor(game.ball.velocity_vec[0]), math.floor(game.ball.velocity_vec[1])) 
             
        return state      
        
    def getStateBP_PP_BV_BVR1(self, paddle, game):
        if(game.ball.rect.x<game.paddle_left.rect.right-10):
            state="lost"
        else:
            xval = min(26,math.floor((max(1,min(0,game.ball.rect.x-game.paddle_left.rect.right)+1)*70)**(1.0/3))-2)
            relativeY = game.ball.rect.centery-game.paddle_left.rect.centery
            yval = math.copysign(1,relativeY)*min(14,math.floor((80*abs(relativeY))**(1.0/3))-2)
            if(game.ball.velocity_vec[0]>0):
                state=("a",math.floor(0.125*xval), math.floor(0.125*yval/xval), math.floor(0.125*paddle.rect.y/xval), math.floor(game.ball.velocity))
            else:
                state = (xval, math.floor(yval/xval), math.floor(paddle.rect.y/xval), math.floor(game.ball.velocity_vec[0]), math.floor(game.ball.velocity_vec[1])) 
             
        return state         
        
    def getStateBP_PP_BV_BVR2(self, paddle, game):
        if(game.ball.rect.x<game.paddle_left.rect.right-10):
            state="lost"
        else:
            xval = min(26,math.floor((max(1,min(0,game.ball.rect.x-game.paddle_left.rect.right)+1)*70)**(1.0/3))-2)
            relativeY = game.ball.rect.centery-game.paddle_left.rect.centery
            yval = math.copysign(1,relativeY)*min(14,math.floor((80*abs(relativeY))**(1.0/3))-2)
            state = (xval, math.floor(yval/xval), math.floor(paddle.rect.y/xval), math.floor(game.ball.velocity_vec[0]), math.floor(game.ball.velocity_vec[1])) 
             
        return state      

    def getStateMOSTLY_UP_DOWN(self, paddle, game):
        if(game.ball.rect.x<game.paddle_left.rect.right-10):
            state="lost"
        else:
            if game.ball.velocity_vec[0]<0 and (game.paddle_left.rect.right-game.ball.rect.x)/game.ball.velocity_vec[0]<5 and (game.ball.rect.centery-game.paddle_left.rect.centery)<game.paddle_left.rect.height/2:
                state = (game.ball.rect.x, game.ball.rect.centery, game.paddle_left.rect.centery, game.paddle_right.rect.centery, math.floor(game.ball.velocity_vec[0]*2), math.floor(game.ball.velocity_vec[1]*2))
            else:
                state = self.getStateUP_DOWN(paddle, game)
        return state 
        
        
    def getStateUP_DOWN(self, paddle, game):
        if(game.ball.rect.x<game.paddle_left.rect.right-10):
            state="lost"
        else:
            if game.ball.rect.centery<game.paddle_left.rect.centery-10:
                state = -1
            elif game.ball.rect.centery>game.paddle_left.rect.centery+10:
                state = 1
            else:
                state = 0
             
        return state               
        
    def writeQTableToFile(self):
        print "writing"
        f=open(self.savefile+".qtable",'w')
        pickle.dump(self.qValues, f)
        f.close()
        print "writen"
        
    def loadQTable(self, fileName):
        f=open(fileName+".qtable", 'r')
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
