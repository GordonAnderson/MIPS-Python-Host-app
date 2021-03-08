import tkinter as tk
from tkinter import filedialog
import code
import threading
import inspect
import ctypes
import time
import queue
import sys
import os

class Console(tk.Frame):
    def __init__(self, parent, _locals, exit_callback):
        tk.Frame.__init__(self, parent, bg="gray95")
        self.parent = parent
        self.exit_callback = exit_callback
        self.destroyed = False
        self.state = 0
        self.real_std_in_out = (sys.stdin, sys.stdout, sys.stderr)
        sys.stdout = self
        sys.stderr = self
        sys.stdin = self
        self.stdin_buffer = queue.Queue()
        self.createWidgets()
        self.consoleThread = threading.Thread(target=lambda: self.run_interactive_console(_locals))
        self.consoleThread.start()
    def run_interactive_console(self, _locals):
        try:
            code.interact(local=_locals)
        except SystemExit:
            if not self.destroyed:
                self.after(0, self.exit_callback)
    def destroy(self):
        self.stdin_buffer.put("\n\nexit()\n")
        self.destroyed = True
        sys.stdin, sys.stdout, sys.stderr = self.real_std_in_out
        super().destroy()
    def enter(self, event):
        input_line = self.ttyText.get("input_start", "end")
        self.ttyText.mark_set("input_start", "end-1c")
        self.ttyText.mark_gravity("input_start", "left")
        self.stdin_buffer.put(input_line)
    def write(self, string):
        self.ttyText.insert('end', string)
        self.ttyText.mark_set("input_start", "end-1c")
        self.ttyText.see('end')
    def createWidgets(self):
        self.ttyText = tk.Text(self.parent, wrap='word', bg="gray95")
        self.ttyText.pack(expand=1, fill="both")
        self.ttyText.bind("<Return>", self.enter)
        self.ttyText.mark_set("input_start", "end-1c")
        self.ttyText.mark_gravity("input_start", "left")
    def flush(self):
        pass
    def readline(self):
        line = self.stdin_buffer.get()
        return line
def _async_raise(tid, exctype):
    '''Raises an exception in the threads with id tid'''
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised (not instances)")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid),ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # "if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
        raise SystemError("PyThreadState_SetAsyncExc failed")

class Interpreter(code.InteractiveInterpreter):
    def write(self, data):
        print(data)

class Script:
    def __init__(self, parent, locals):
        self.parent = parent
        self.locals = locals
        self.aborted = False
        # determine if application is a script file or frozen exe
        if getattr(sys, 'frozen', False):
            self.application_path = os.path.dirname(sys.executable)
        elif __file__:
            self.application_path = os.path.dirname(__file__)
    def runInterpreter(self,source):
        try:
            Interpreter(self.locals).runcode(source)
        except Exception as e:
            pass
    def execute(self):
        sourcelist = self.sourcebox.get("1.0",tk.END)
        source = ''.join(sourcelist)
        self.thredInterpreter = threading.Thread(target=self.runInterpreter, args=(source,))
        self.thredInterpreter.start()
        self.statusbar.configure(text=" Script running...")
        while self.thredInterpreter.is_alive():
            time.sleep(.1)
            self.parent.update()
        if self.aborted: self.statusbar.configure(text=" Script aborted")
        else: self.statusbar.configure(text=" Script finished")
        self.aborted = False
    def abort(self):
        if self.thredInterpreter.is_alive():
            _async_raise(self.thredInterpreter.ident,SystemError)
            self.aborted = True
    def load(self):
        filename = filedialog.askopenfilename(initialdir=self.application_path, title="Select script file to load",
                                              filetypes=(("script files", "*.py"), ("all files", "*.*")))
        if filename != "":
            with open(filename, 'r') as file:
                data = file.read()
                file.close()
                self.sourcebox.delete("1.0", "end")
                self.sourcebox.insert(tk.END, data)
                self.application_path=os.path.dirname(os.path.abspath(filename))
    def save(self):
        filename =  filedialog.asksaveasfilename(initialdir =self.application_path,title = "Select file to save script",filetypes = (("script files","*.py"),("all files","*.*")))
        if filename != "":
            with open(filename, 'w') as file:
                file.write(self.sourcebox.get("1.0", "end"))
                file.close()
                self.application_path = os.path.dirname(os.path.abspath(filename))
    def show(self):
        self.root = tk.Toplevel(self.parent)
        self.root.geometry('600x620')
        self.root.resizable(0, 0)
        self.root.title("Scripting")
        self.statusbar = tk.Label(self.root, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(self.root, text="Script source code:").place(x=0, y=0)
        self.sourcebox = tk.Text(self.root, bg="gray95")
        self.sourcebox.place(x=0, y=20, width=600, height=350)
        self.loadBT = tk.Button(self.root, text=" Load ", command=self.load)
        self.loadBT.place(x=10, y=370)
        self.saveBT = tk.Button(self.root, text=" Save ", command=self.save)
        self.saveBT.place(x=100, y=370)
        self.executeBT = tk.Button(self.root, text=" Execute ", command=self.execute)
        self.executeBT.place(x=440, y=370)
        self.abortBT = tk.Button(self.root, text=" Abort ", command=self.abort)
        self.abortBT.place(x=540, y=370)
        tk.Label(self.root, text="Console:").place(x=0, y=400)
        self.consolebox = tk.Text(self.root, bg="gray95")
        self.consolebox.place(x=0, y=420, width=600, height=180)
        Console(self.consolebox, self.locals, self.consolebox.destroy)
        self.root.mainloop()