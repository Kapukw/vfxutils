import sys
import subprocess

from Queue import Queue
from threading import Thread

import maya.utils

g_jobQueue = None
g_workThread = None

def add_job(cmd_string, callback):
    global g_jobQueue
    global g_workThread

    if g_jobQueue != None and g_jobQueue.empty():
        g_jobQueue = None
        if g_workThread != None:
            g_workThread.join()
            g_workThread = None

    if g_jobQueue is None:
        g_jobQueue = Queue()
        g_jobQueue.put((cmd_string, callback))
        g_workThread = Thread(target=do_job, args=(g_jobQueue,))
        g_workThread.start()
    else:
        g_jobQueue.put((cmd_string, callback))

def do_job(queue):
    while not queue.empty():
        cmd_string, callback = queue.get()
        sys.stdout.write("\nCMD: {}\n".format(cmd_string))
        subprocess.call(cmd_string, shell=True)
        maya.utils.executeDeferred(callback)
        queue.task_done()
