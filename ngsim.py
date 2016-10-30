#!/usr/bin/env python

"""
Copyright 2011 FG - http://worldofpiggy.wordpress.com
HO-NG Hearer-Only Naming Game simulator 
"""

from pylab import *
import subprocess
import os
from multiprocessing import Process
import sys
from collections import deque
from Queue import Queue
import time
import random
from matplotlib.colors import rgb2hex




################   Globals   #############################
N    = 4                     # default number of agents
iter = 0                     # num of iterations

verbose   = False
graphics  = True
conswords = {}               # consensus word table
Agents    = []

##########################################################


# work in progress
class Stats():
	""" Statistics """
	def __init__(self, fname):
		self.success = 0
		self.fail    = 0
		self.iter    = 1   # single iteration
		self.frame   = 0   # iteration frame 
		self.numwords = 0
		self.record = ""   # |iter |Succ| Fail| SRate | FRate | 
		self.FILE = open("exp_"+fname+".log", "w")
		self.WORDFILE = open("words_"+fname+".log", "w")
		
	def updateTotalWords(self, num):
		self.numwords+=num

	def updateIter(self):
		self.iter += 1

	def updateSuccess(self):
		self.success += 1
		
	def updateFail(self):
		self.fail += 1

	def saveRecord(self):
		self.record = str(self.iter)+"\t" + str(self.success) + "\t" + str(self.fail) + "\t" + str(self.success/float(self.iter)*100)+"\t"+ str(self.fail/float(self.iter)*100)+ "\n"
		self.FILE.write(self.record)
		
	def saveWords(self):
		self.record = str(self.frame) + "\t" + str(self.numwords)+"\n"
		self.WORDFILE.write(self.record)
		


class Agent():
	"""Symmetric Agent (producer and consumer)
	Agent produces words to her neighboors' buffer
	Agent consumes words from her local queue
	"""
	
	def __init__(self, id, stat, limit=5,immune=False):
		self.id = id
		self.immune = immune  	# committed agent immune to influence
		self.friends = list()	# agent's neighboors (Agent instances)
		self.words = list()     # agent's knowledge
		self.wordsin = 0        # num words in dictionary and conswords  
		self.buffer = Queue()   # request queue ([speaker1,word1], [speaker2,word2],... )
		self.limit = limit
		self.stats = stat

		# visualization properties
		self.colour = 'b'       # regular nodes are blue (not immune)

		if self.immune:         # immune nodes are red
			self.colour = 'r'

                ####### TODO add probabilistic parameters ############
		#
		#
		######################################################
	

	def run(self):
		global iter
		iter+=1    # increment iteration num
		self.stats.updateIter()
		
		while self.buffer.qsize():
			data = self.buffer.get()
			#data is a list where data[0] <- speaker data[1] <- word
			# check if data has a word in self.words
			# if self.words contains data(word), keep it and delete the rest
			# if data(word) is not in self.words append it to self.words

                        global conswords
			
			if(data[1] in self.words):       # word is in dictionary
				self.colour = 'g'        
				
				if verbose:
					print "Successful communication"
					
				# update global table of potential words
				if data[1] in conswords:
					conswords[data[1]] += 1
					self.colour = 'r'

				# if there are observed words, update conswords
				# because they will be deleted
				for w in self.words:
				    if w in conswords: 
					conswords[w] -= 1
					
				# words are deleted
				self.words = list()
				# only successul word is present now
				self.words.append(data[1])

				# update stats
				self.stats.updateSuccess()
				
			else: 
				if verbose:
					print "Communication failed...adding new word"
				
				# update stats
				self.stats.updateFail()
				
				# a committed agent will never add new word (got influenced)
				# TODO will add a new word with a small probability
				
				if not self.immune:               # regular agent
					#self.colour = 'b'
					
					# update global table of potential words
					if data[1] in conswords:
						conswords[data[1]] += 1
						self.wordsin = conswords[data[1]]
						#self.colour = '#eead0e'     # orange here 
						#self.colour = rgb2hex(cm.jet(self.wordsin/100.)[:3])
						
					self.words.append(data[1])
                                    
		#update friends and words
		self.numfriends = len(self.friends)
		self.numwords = len(self.words)

		# color depends on how many potential words are in agent's dictionary
		for w in self.words:
			if w in conswords:
				self.wordsin+=1
		
		converted = float((int(self.wordsin) / (int(self.numwords)+1))) *100 
		if ( converted < 10):
			self.colour = '#7eb6ff'     # light blue
		elif (converted > 33) and (converted < 50):
			self.colour = '#eead0e'     # orange here 
		#elif (converted > 50):
		#	self.colour = 'r'           # red 
		if self.numwords < 3:               # if low threshold, red
			self.colour = 'r' 
			
		#if there are friends, select one
		# TODO select friend according to a PDF
		if self.numfriends > 0 :
			i = random.randint(0,self.numfriends-1)
			friend = self.friends[i]

			#if there are words select one and talk
			# TODO select word according to a PDF
			if self.numwords > 0:
				i = random.randint(0, self.numwords-1)
				word = self.words[i]
				data = [self, word]   	# [speaker,word] to produce to friend's queue
				friend.buffer.put(data)
                        if verbose:
                            print "Agent_%s spoke %s to Agent_%s" % (self.id, word, friend.id)
		
		#count total words summing up from each agent
		self.stats.saveRecord()  # write this record on file 
		
	# generates up to limit words as in <prefix><num>
	def createWords(self, limit=10, prefix="topic"):
		for i in range(0, limit):
			self.words.append(prefix + str(i))

#			
# returns Agents, an array of initialized agents
#                        
def initNG(stat, num=N, cmatrix=identity(N, int16), committed=zeros(N,int16), subject=list(), amount=list()):
	
	print "Creating agents"
	# create agents and append to agents list
	for i in range(num):
		agent = Agent(i, stat)
		Agents.append(agent)

	print "Creating friends according to connection matrix"
	# create agents' friends according to connection matrix
	for i in range(num):
		for j in range(num):
			if (i!=j):
				if (cmatrix[i][j] == 1):
					Agents[i].friends.append(Agents[j])
	
	print "Setting immune agents"
	# create immune agents according to committed list				
	for i in range(num):
		if (committed[i] == 1):
			Agents[i].immune = True
	
	print "Creating dictionaries"
	if (len(amount)==len(subject))and (len(amount)==num):
		for i in range(num):
			Agents[i].createWords(amount[i], prefix=subject[i])
			
	
	return Agents


# TODO work in progress
def createGrid(n,shape='square'):
	xsize = ysize = int(sqrt(n))
	step = 1./xsize
	posxx = array( range(n), dtype='float64')
	posyy = array( range(n), dtype='float64')
	
	posxx = [0,.2,.4,.6,.8,0,.2,.4,.6,.8,0,.2,.4,.6,.8,0,.2,.4,.6,.8,0,.2,.4,.6,.8]
	posyy = [0,0,0,0,0,.2,.2,.2,.2,.2,.2,.4,.4,.4,.4,.4,.6,.6,.6,.6,.6,.8,.8,.8,.8,.8]
	
	val = 0
	for i in range(n):
		if (i%xsize == 0):
			val = 0
		posxx[i] = val
		val = val+step
	
	val = 0

	for i in range(n):
		posyy[i] = val
		if(i%xsize == 0):
			val = val + step
			
	return(posxx,posyy)
	


##############################################################               
# Simulation of num regular agents and imm committed agents
#############################################################
def main(num, imm, duration, stat):
    success = 1
    failure = 0
    consensus = 0.0
    global conswords     
    global Agents

    print "\n\n-----------------------------------------------------------------------"
    print "--  NamingGame simulation of %d regular agents and %d immune agents  " % (num, imm)
    print "--  Copyright 2011 FG - http://worldofpiggy.wordpress.com            "
    print "-----------------------------------------------------------------------\n"

    # TODO to initNG
    numag = num            # number of agents
    numim = imm            # number of immune
    
    #set graphical common properties 
    movietime = duration   # number of seconds 
    fps = 7
    frames = movietime*fps
    
    sub = []

    for i in range(numag):
	    sub.append(str(i))
    quantity = random_integers(10,100, numag)
    immune = zeros(numag,int16)   
    
    for i in range(numim):
	    immune[i]= 1
   
    # TODO what's the best topology to reach consensus faster 
    # connectivity graph: this is one of the most influential
   
    # fully connected graph
    # connect = ones((numag,numag), int16)        
    # init game
    Agents = initNG(stat, num=numag, cmatrix=connect, committed=immune, subject=sub, amount=quantity)

    #init conswords structure to count words of consensus
    print "Creating list of potential words to consensus"
    for agent in Agents:
        if agent.immune:
            for w in agent.words:
                conswords[w] = 0
	    #print "Words candidates to consensus"
	    #print conswords
	
    quit = False
    
    # TODO frame iteration here 
    # for each frame, scan all agents and draw the graph
    # update specific graph properties within the agents loop
    
    # common graphical properties
    #handles = []
    #posx, posy = createGrid(len(Agents))
    #posx, posy = rand(2, len(Agents))        # position vector of agents in graph
    posx = uniform(.0, 3., len(Agents))
    posy = uniform(.0, 3., len(Agents))
      
    #props = dict( alpha=0.5, edgecolors='none' )
    s = 12.0 * rand(len(Agents))
    
    # scatter size
    lower = min(quantity)
    upper = max(quantity)
    
    print "Running simulation... (this will take a while)"
    for i in range(frames):
	    stat.numwords = 0   # reset numwords for this iteration 
	    stat.frame += 1     # update frame number
	    #stat.saveRecord()   # write this record on file 
		
	    for index, a in enumerate(Agents):
		    a.run()
		    stat.updateTotalWords(a.numwords)     # count total words at this iter            
		    
		    # graphical update size of current agent
		    size = 24 * a.numwords/upper
		   
		    # some dumb normalisation 
		    if size<7:
			    size=4
		    if size>8:
		        size=8
		    
		    s[index] = size
		    
		    if a.immune:
			    mark = '^'
		    else: 
			    mark = 'o'

		    grid(True)
		    plt.plot(posx[index], posy[index], c=a.colour, alpha=0.4, ms=s[index], marker=mark)
		    plt.axis([0, 3, 0, 3])
		    plt.title('Population dynamics of the Naming-Game model')
		    #plt.text(0.1, 0., str(iter)+'')
		    
	    stat.saveWords()
	    filename = str(numag)+'_'+str(numim)+ str('_%03d' % i) + '.png'
	    savefig(filename, dpi=100)
 	    clf()
	    
	    # some feedback to the poor waiting scientist
	    percent = 1+i*100/frames
	    sys.stdout.write("\r\x1b[K"+"Processing "+ percent.__str__()+"%")
   
	    sys.stdout.flush()
 	    	    
	    imgfiles = str(numag)+'_'+str(numim)+ '*.png'
	    videofile  = str(numag)+'_'+str(numim)+ '.avi'


    command = ('mencoder',
           str('mf://')+str(imgfiles),
           '-mf',
           str('type=png:w=800:h=600:fps=')+str(fps),
           '-ovc',
           'lavc',
           '-lavcopts',
           'vcodec=mpeg4',
           '-oac',
           'copy',
           '-o',
	   videofile)

    print "\n\nRendering video:\n%s\n\n" % ' '.join(command)
    subprocess.check_call(command)
    
    print "\n\nDeleting temporary files\n"
    if os.name == 'posix':
	    rmcmd = str('rm ') + str(imgfiles)
    elif os.name == 'nt':
	    rmcmd = str('del ') + str(imgfiles)
	    
    os.system(rmcmd)
    
    print "\n\n Rendering is complete. Play file '%s'" % videofile
    


if __name__ == '__main__':
    if (len(sys.argv) <3):
	    print "\n\nPlease run ./NGsim <agents> <seconds> \n\n"
	    
    else:
	    global posx
	    global posy

	    total     = int(sys.argv[1]) 
	    lenght    = int(sys.argv[2]) 
	    
	    # topology is common to all simulations
	    connect = reshape(random_integers(0,1,size=total*total),(total,total))
	    
	    # positions should also be computed once for all simulations
	    #posx = uniform(.0, 3., total)
	    #posy = uniform(.0, 3., total)
	    
	    # run simulation on the same topology with 8%, 9%, 15% committed agents
	    s0 = Stats(str(total)+"_"+str(8))
	    s1 = Stats(str(total)+"_"+str(9))
	    s2 = Stats(str(total)+"_"+str(15))
	    
	    main(total, total*2/100, lenght,s0)
	    main(total, total*8/100, lenght,s1)
	    main(total, total*10/100, lenght,s2)
	    
	    s0.FILE.close()
	    s1.FILE.close()
	    s2.FILE.close()
	    
	    print "Bye!\n"
	    
