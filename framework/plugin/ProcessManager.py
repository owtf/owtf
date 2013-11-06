#!/usr/bin/env python
'''
owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
Manager Process
'''
import curses
from framework.lib.general import *
import fcntl
import logging
import multiprocessing
import Queue
import os
import re
import select
import signal
import sys
import termios
from threading import Thread
import time

class ProcessManager:
    def __init__(self,CoreObj):
        self.Core = CoreObj
        self.worklist = []          #List of unprocessed (plugin*target)
        self.running_plugin={}      #list of all running plugins indexed by pids of processes handling it
        self.target_used={}         #list whether a plugin is running on a target r not at this time
        self.numprocess=0           #number of processes
        self.workers = []                #list of workers
        self.input_queues = []                 #list of queues
        self.output_queues = []
        self.busy_processes = []         #list whether a process is busy or not
        self.accept_input=True
        self.status={}
    
    def startinput(self):
        """
        this function initializes input thread for taking input from user to stop some plugin etc
        """
        self.inputqueue = multiprocessing.Queue()
        self.inputthread = Thread(target=self.keyinput, args=(self.inputqueue,))
        self.inputthread.start()    
    
    #this function gets all the targets from Plugin order and fill it to the worklist
    def fillWorkList(self,pluginGroup,targetList):
        for plugin in self.Core.Config.Plugin.GetOrder(pluginGroup):
            for target in targetList:
                self.target_used[target]=False
                self.worklist.append((target,plugin))
    
    #returns next work that can be done depending on RAM state and availability of targets
    def get_task(self):
        free_mem = self.Core.Shell.shell_exec("free -m | grep Mem | sed 's/  */#/g' | cut -f 4 -d#")
        for target,plugin in self.worklist:
            #check if target is being used or not because we dont want to run more than one plugin on one target at one time
            #check if RAM can withstand this plugin(training data from history of that plugin)
            if (self.target_used[target]==False) and (int(free_mem)>int(self.Core.Config.Get('MIN_RAM_NEEDED'))):
                self.worklist.remove((target,plugin))
                return (target,plugin)
        return ()
    
    #this function spawns the worker process and give them intitial work
    def spawnWorkers(self,Status):
        #check if maximum limit of processes has reached
        self.status = Status
        while (self.numprocess<(int(self.Core.Config.Get('PROCESS_PER_CORE'))*multiprocessing.cpu_count())):
            work = self.get_task()
            
            #if there is no work left return
            if work==():
                break
            #mark the target as used as one target is probes once simultaneously
            self.target_used[work[0]]=True
            #queues to communicate to workes
            self.input_queues.append(multiprocessing.Queue())
            self.output_queues.append(multiprocessing.Queue())

            #spawn workers     
            p = multiprocessing.Process(target=self.worker, args=(self.input_queues[self.numprocess],self.output_queues[self.numprocess],1,Status))
            self.input_queues[self.numprocess].put(work)                               
            p.start()
            self.workers.append(p)              
            self.running_plugin[p.pid] = work
            self.busy_processes.append(True)
            self.numprocess=self.numprocess+1
     
    def update_status(self,status):
        self.status['SomeAborted'] = self.status['SomeAborted'] or status['SomeAborted']
        self.status['SomeSuccessful'] = self.status['SomeSuccessful'] or status['SomeSuccessful']
        self.status['AllSkipped'] = self.status['AllSkipped'] and status['AllSkipped']
            
    #this function manages workers, it polls on each queue of worker and check if it has done his work and then 
    # give it new process if there is one
    def manageProcess(self):
        k=0
        #loop while there is some work in worklist
        while k<self.numprocess and len(self.worklist)>0:
            #if worker k has completed its work
            if self.output_queues[k].empty()==False:
                status = self.output_queues[k].get()
                self.update_status(status)
                target,plugin =  self.running_plugin[self.workers[k].pid]
                self.running_plugin[self.workers[k].pid] = ()
                #worker is idle
                self.busy_processes[k]=False
                #target is not being probed
                self.target_used[target]=False
                work_to_assign = self.get_task()
                if work_to_assign!=():
                    #assign work to worker,set target to used,and process to busy
                    self.input_queues[k].put(work_to_assign)
                    self.target_used[work_to_assign[0]]=True
                    self.running_plugin[self.workers[k].pid] = work_to_assign
                    self.busy_processes[k]=True
            k=(k+1)%self.numprocess
            time.sleep(0.05)
            
    #This function waits for each worker to complete his work and send it Poision Pill(emtpy work)
    def poisonPillToWorkers(self):
        for i in range(self.numprocess):
            #check if process is doing some work
            if self.busy_processes[i]==True:
                status = self.output_queues[i].get()
                self.update_status(status)
                self.busy_processes[i] = False
                self.running_plugin[self.workers[i].pid] = ()
            self.input_queues[i].put(())
    #joins all the workers
    def joinWorker(self):
        for i in range(self.numprocess):
            self.workers[i].join()            
        self.inputqueue.put("end")
        self.inputthread.join()
        return self.status
    #this function is used by workers to get new task
    def get_new_task(self,queue,output_queue,start,status):
        if start==0:
            output_queue.put(status)
        work1 = queue.get()
        return work1
    
    #worker code
    def worker(self,input_queue,output_queue,start,status):
        
        while True:
            # work has been completed. Put that into queue and wait for new work to be assigned
            try:
                work = self.get_new_task(input_queue,output_queue,start,status)
            except Exception,e:
                log("exception while get" + str(e))
                continue
                #if work is empty this means no work is there
            if work == ():
                sys.exit()
            target,plugin = work
            pluginGroup = plugin['Group']
            pluginDir = self.Core.PluginHandler.GetPluginGroupDir(pluginGroup)
            self.Core.PluginHandler.SwitchToTarget(target)
            self.Core.PluginHandler.ProcessPlugin( pluginDir, plugin, status )      
            start=0
            
    #this function takes input from user to stop a process etc
    def keyinput(self,q):
        fd = sys.stdin.fileno()
        oldterm = termios.tcgetattr(fd)
        newattr = oldterm[:]
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, newattr)
        oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
        i=0
        try:
            while 1:
                if q.empty()==False:
                    self.Core.showOutput=True
                    break
                #Poll on stdin every 0.5 seconds (Taken from w3af)
                r, w, e = select.select([fd], [], [],0.5)
                if r and self.accept_input:
                    c = sys.stdin.read(1)
                    #if user presses 's' Then stops output,input and go to htop like interface 
                    if c=="s":
                        self.Core.showOutput=False
                        self.accept_input = False
                        self.stop_process()
                        self.Core.showOutput=True
                        self.accept_input = True
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
 
    def stop_process(self):
        #starts curses
        stdscr = curses.initscr()
        curses.noecho()
        curses.raw()
        #refresh screen after ever 1 secs
        stdscr.timeout(1000)
        selected = 0
        i=0
        stdscr.refresh()
        height,width = stdscr.getmaxyx()
        stdscr.keypad(1)
        i = self.refreshScreen(height, stdscr, selected)
       
        while 1:
            c = stdscr.getch()
            #Exit this curses if user presses 's'
            if c == ord('s'):
                self.exitCurses(stdscr)
                self.showOutput=True
                self.accept_input = True
                return
            #Move selected one down
            elif c==curses.KEY_DOWN:
                if(selected != (i-1)):
                    selected = selected+1
            
            #move selected one up
            elif c==curses.KEY_UP:
                if(selected != 0):
                    selected = selected-1
            
            #exit owtf on pressing 'e'
            elif c==ord('e'):
                self.exitCurses(stdscr)
                self.exitOwtf()
                self.Core.showOutput=True
                self.accept_input = True
                return
            
            #remove target from pending work list and then abort the plugin
            elif c==ord('t'):
                self.exitCurses(stdscr)
                self.stopTarget(selected)
                selected=0
                self.Core.showOutput=True
                self.accept_input = True
                return
            
            #abort the selected plugin
            elif c== ord('p'):
                k=0
                self.exitCurses(stdscr)
                self.abortPlugin(selected)
                selected=0
                self.Core.showOutput=True
                self.accept_input = True
                return  
                      

            i=0
            stdscr.clear()
            i=self.refreshScreen(height, stdscr, selected)

    #this function iterates over running plugin list and show it on curses screen
    def refreshScreen(self,height,stdscr,selected):
        i=0
        stdscr.refresh()
        stdscr.addstr(0,0,"PID\t\t\tTarget\t\t\tPlugin")
        for pid in self.running_plugin:
            work = self.running_plugin[pid]
            if work==():
                continue
            plugin = work[1]
            if selected == i:
                stdscr.addstr(0+(i+1), 0,str(pid) +"\t\t" +work[0]+"\t\t"+plugin['Title']+" ("+plugin['Type']+")",curses.A_STANDOUT)
            else:
                stdscr.addstr(0+(i+1)*1, 0,str(pid )+"\t\t" +work[0]+"\t\t"+plugin['Title']+" ("+plugin['Type']+")")    
            i=i+1    
        stdscr.addstr(height-1,0,"e Exit Owtf\tp Stop Plugin\tt Stop Tests for Target")
        stdscr.refresh()
        return i
    #This function empties the pending work list and aborts all processes                 
    def exitOwtf(self):
        self.worklist={}
        for pid in self.running_plugin:
            work = self.running_plugin[pid]
            if work==():
                continue
            self.abortWorker(pid)
            
    #this function kills all children of a process and abort that process        
    def abortWorker(self,pid):
        self.Core.KillChildProcesses(pid,signal.SIGINT)
        try:  
            os.kill(pid,signal.SIGINT)
        except:
            pass
    
    #This function aborts selected plugin
    def abortPlugin(self,selected):
        k=0
        for pid in self.running_plugin:
            work = self.running_plugin[pid]
            if work==():
                continue
            if k==selected:
                break
            k = k+1
        self.abortWorker(pid)
    
    #this function itrates over pending list and removes the tuple having target as selected one
    def stopTarget(self,selected):
        k=0
        for pid in self.running_plugin:
            work = self.running_plugin[pid]
            if work==():
                continue
            if k==selected:
                break
            k = k+1
        target1,plugin1= work
        for target,plugin in self.worklist:
            if target==target1:
                self.worklist.remove((target,plugin))
        self.abortWorker(pid)
        
    def exitCurses(self,stdscr):
        curses.nocbreak()
        stdscr.keypad(0)
        curses.echo()
        curses.endwin()
