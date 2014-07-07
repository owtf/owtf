#!/usr/bin/env python
"""

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
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.  Manager Process

"""

import os
import sys
import time
import signal
import logging
import multiprocessing

from framework.lib.exceptions import InvalidWorkerReference


class Worker(multiprocessing.Process):
    def __init__(self, CoreObj, input_q, output_q):
        multiprocessing.Process.__init__(self)
        self.Core = CoreObj
        self.input_q = input_q
        self.output_q = output_q
        #self.status = status
        #self.output_status = False

    def run(self):
        # When run for the first time, put something into output queue ;)
        self.output_q.put('Started')
        while True:
            try:
                try:
                    work = self.input_q.get()
                except Exception,e:
                    log("exception while get" + str(e))
                    continue
                    #if work is empty this means no work is there
                if work == ():
                    sys.exit()
                target, plugin = work
                pluginDir = self.Core.PluginHandler.GetPluginGroupDir(plugin['group'])
                self.Core.PluginHandler.SwitchToTarget(target)
                self.Core.PluginHandler.ProcessPlugin(pluginDir, plugin)
                self.output_q.put('done')
                #self.output_status = True
            except KeyboardInterrupt:
                self.Core.log("I am worker with pid: " + str(self.pid) + " & my master doesn't need me anymore")
                sys.exit()

class WorkerManager(object):
    def __init__(self,CoreObj):
        self.Core = CoreObj
        self.worklist = []          #List of unprocessed (plugin*target)
        self.workers = []                #list of worker and work (worker, work)
        self.processes_limit = int(self.Core.DB.Config.Get('PROCESS_PER_CORE'))*multiprocessing.cpu_count()
        self.spawn_workers()
        #self.accept_input=True
        #self.status={}

    def fill_work_list(self, targets, plugins):
        # Targets are only target_ids and plugins are plugin_dicts
        for plugin in plugins:
            for target in targets:
                self.worklist.append((target["ID"], plugin)) # Only target_id, since it is only used to switch target db context

    def filter_work_list(self, targets, plugins):
        for target,plugin in self.worklist:
            if (target in targets) or (plugin in plugins):
                self.worklist.remove((target, plugin))

    def get_work_list(self):
        return(self.worklist)

    #returns next work that can be done depending on RAM state and availability of targets
    def get_task(self):
        if len(self.worklist):
            free_mem = self.Core.Shell.shell_exec("free -m | grep Mem | sed 's/  */#/g' | cut -f 4 -d#")
            if int(free_mem) > int(self.Core.DB.Config.Get('MIN_RAM_NEEDED')):
                for target,plugin in self.worklist:
                    #check if target is being used or not because we dont want to run more than one plugin on one target at one time
                    #check if RAM can withstand this plugin(training data from history of that plugin)
                    if not self.is_target_in_use(target):
                        self.worklist.remove((target,plugin))
                        return (target,plugin)
            else:
                self.Core.log("Not enough memory to execute a plugin")
        return None
    
    #this function spawns the worker process and give them intitial work
    def spawn_workers(self):
        #check if maximum limit of processes has reached
        while (len(self.workers) < self.processes_limit):
            self.spawn_worker()
        if not len(self.workers):
            self.Core.Error.FrameworkAbort("Zero worker processes created because of lack of memory")

    def spawn_worker(self):
        w = Worker(self.Core, multiprocessing.Queue(), multiprocessing.Queue())
        self.workers.append({
                                "worker":w,
                                "work":(),
                                "busy":False,
                                "paused":False
                            })
        w.start()

    def replace_worker(self, index):
        w = Worker(self.Core, multiprocessing.Queue(), multiprocessing.Queue())
        self.workers[index] = { "worker":w, "work":(), "busy":False, "paused":False }
        w.start()

    def is_target_in_use(self, target):
        for item in self.workers:
            try:
                if target == item["work"][0]:
                    return True
            except IndexError: # This happens at the spawning of processes
                pass
        return False

    #this function manages workers, it polls on each queue of worker and check if it has done his work and then 
    # give it new process if there is one
    def manage_workers(self):
        k = 0
        # Loop while there is some work in worklist
        while (k < self.processes_limit):
            if (not self.workers[k]["worker"].output_q.empty()) or (not self.workers[k]["worker"].is_alive()):
                if self.workers[k]["worker"].is_alive():
                    # Assign target and plugin from tuple work and empty the tuple
                    #(target,plugin), self.workers[k]["work"] = self.workers[k]["work"], ()
                    self.workers[k]["work"] = ()
                    self.workers[k]["busy"] = False # Worker is IDLE
                else:
                    self.replace_worker(k)
                work_to_assign = self.get_task()
                if work_to_assign:
                    trash_can = self.workers[k]["worker"].output_q.get()
                    #assign work to worker,set target to used,and process to busy
                    self.workers[k]["worker"].input_q.put(work_to_assign)
                    self.workers[k]["work"] = work_to_assign
                    self.workers[k]["busy"] = True
            k += 1

    # This function waits for each worker to complete his work and send it Poision Pill(emtpy work)
    def poison_pill_to_workers(self):
        for item in self.workers:
            #check if process is doing some work
            if item["busy"]:
                if item["paused"]:
                    self.signal_process(item["worker"].pid, signal.SIGCONT)
                trash = item["worker"].output_q.get()
                item["busy"] = False
                item["work"] = ()
            item["worker"].input_q.put(())

    # Joins all the workers
    def join_workers(self):
        for item in self.workers:
            item["worker"].join()

    def clean_up(self):
        #self.ProcessManager.manageProcess()
        self.poison_pill_to_workers()
        self.join_workers()

    #This function empties the pending work list and aborts all processes                 
    def exit(self):
        # As worklist is emptied, aborting of plugins will result in killing of workers
        self.worklist=[] # It is a list
        for item in self.workers:
            work = item["work"]
            if work==():
                continue
            self.signal_process(item["worker"].pid, signal.SIGINT)
            
    #this function kills all children of a process and abort that process        
    def signal_process(self, pid, psignal):
        # Child processes are handled at shell level :P
        # self.Core.KillChildProcesses(pid,signal.SIGINT)
        try: 
        # This will kick the exception handler if plugin is running, so plugin is killed
        # Else, the worker dies :'(
            os.kill(pid , psignal)
        except Exception,e:
            log("Error while trying to abort Worker process " + str(e))
    
    #this function itrates over pending list and removes the tuple having target as selected one
    def stop_target(self, target_id):
        for target,plugin in self.worklist:
            if target==target1:
                self.worklist.remove((target,plugin))
        self.abort_worker(item["worker"].pid)

#--------------------------------------------------- API Methods ----------------------------------------------------
# PSEUDO_INDEX = INDEX + 1

    def get_worker_details(self, pseudo_index = None):
        if pseudo_index:
            try:
                temp_dict = dict(self.workers[pseudo_index-1])
                temp_dict["worker"] = temp_dict["worker"].pid
                temp_dict["id"] = pseudo_index
                return(temp_dict)
            except IndexError:
                raise InvalidWorkerReference("No worker process with id: " + str(pseudo_index))
        else:
            worker_temp_list = []
            for i in range(0,len(self.workers)):
                temp_dict = dict(self.workers[i])
                temp_dict["worker"] = temp_dict["worker"].pid
                temp_dict["id"] = i+1 # Zero-Index is not human friendly
                worker_temp_list.append(temp_dict)
            return(worker_temp_list)

    def get_worker_dict(self, pseudo_index):
        try:
            return(self.workers[pseudo_index-1])
        except IndexError:
            raise InvalidWorkerReference("No worker process with id: " + str(pseudo_index))

    def pause_worker(self, pseudo_index):
        worker_dict = self.get_worker_dict(pseudo_index)
        if not worker_dict["paused"]:
            self.signal_process(worker_dict["worker"].pid, signal.SIGSTOP)
            worker_dict["paused"] = True

    def resume_worker(self, pseudo_index):
        worker_dict = self.get_worker_dict(pseudo_index)
        if worker_dict["paused"]:
            self.signal_process(worker_dict["worker"].pid, signal.SIGCONT)
            worker_dict["paused"] = False

    def abort_worker(self, pseudo_index):
        worker_dict = self.get_worker_dict(pseudo_index)
        self.signal_process(worker_dict["worker"].pid, signal.SIGINT)
