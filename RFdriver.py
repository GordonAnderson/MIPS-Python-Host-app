import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import MIPSobjects
import Util

#
# RF channel objects
#
class RFchannel:
    def __init__(self, parent, name, MIPSname, channel, comm, x, y):
        self.master = parent
        self.name = name
        self.MIPSname = MIPSname
        self.kind = 'RFchannel'
        self.channel = channel
        self.cp = comm
        self.hidden = False
        self.x=x
        self.y=y
        self.isShutdown = False
        self.activeSetpoint = 0
        self.activeDrive = 0
        self.isShutdown = False
        self.bg = 'gray89'
        self.frame = MIPSobjects.LabelFrame(self.master, name, 200,225)
        self.frame.place(x=x,y=y)
        self.frame.config(bg=self.bg)
        # Entry box labels
        tk.Label(self.frame, text='Drive', bg=self.bg).place(x=0,y=0)
        tk.Label(self.frame, text='Setpoint', bg=self.bg).place(x=0,y=25)
        tk.Label(self.frame, text='Freq', bg=self.bg).place(x=0,y=50)
        tk.Label(self.frame, text='RF+', bg=self.bg).place(x=0,y=75)
        tk.Label(self.frame, text='RF-', bg=self.bg).place(x=0,y=100)
        tk.Label(self.frame, text='Power', bg=self.bg).place(x=0,y=125)
        # Entry box units
        tk.Label(self.frame, text='%', bg=self.bg).place(x=160,y=0)
        tk.Label(self.frame, text='Vp-p', bg=self.bg).place(x=160, y=25)
        tk.Label(self.frame, text='Hz', bg=self.bg).place(x=160, y=50)
        tk.Label(self.frame, text='Vp-p', bg=self.bg).place(x=160, y=75)
        tk.Label(self.frame, text='Vp-p', bg=self.bg).place(x=160, y=100)
        tk.Label(self.frame, text='W', bg=self.bg).place(x=160, y=125)
        # Entry boxes
        self.entDrive = tk.Entry(self.frame, width = 10, bd =0, relief=tk.FLAT)
        self.entDrive.place(x=60,y=0)
        self.entDrive.bind("<Return>", self.EntryChange)
        self.entDrive.bind("<FocusOut>", self.EntryChange)
        self.entSetpoint = tk.Entry(self.frame, width = 10, bd =0, relief=tk.FLAT)
        self.entSetpoint.place(x=60,y=25)
        self.entSetpoint.bind("<Return>", self.EntryChange)
        self.entSetpoint.bind("<FocusOut>", self.EntryChange)
        self.entFreq = tk.Entry(self.frame, width = 10, bd =0, relief=tk.FLAT)
        self.entFreq.place(x=60,y=50)
        self.entFreq.bind("<Return>", self.EntryChange)
        self.entFreq.bind("<FocusOut>", self.EntryChange)
        self.entRFP = tk.Entry(self.frame, width = 10, bd =0,disabledforeground='black', relief=tk.FLAT)
        self.entRFP.place(x=60,y=75)
        self.entRFP.config(state='disabled')
        self.entRFN = tk.Entry(self.frame, width = 10, bd =0,disabledforeground='black', relief=tk.FLAT)
        self.entRFN.place(x=60,y=100)
        self.entRFN.config(state='disabled')
        self.entPWR = tk.Entry(self.frame, width = 10, bd =0,disabledforeground='black', relief=tk.FLAT)
        self.entPWR.place(x=60,y=125)
        self.entPWR.config(state='disabled')
        # Open / closed loop options
        self.Mode = tk.StringVar()
        self.Mode.set("MANUAL")
        self.rbOpen = tk.Radiobutton(self.frame, text="Open loop", variable=self.Mode, value="MANUAL", bg=self.bg, command=self.rbChange)
        self.rbOpen.place(x=0,y=150)
        self.rbClosed = tk.Radiobutton(self.frame, text="Closed loop", variable=self.Mode, value="AUTO",bg=self.bg, command=self.rbChange)
        self.rbClosed.place(x=100,y=150)
        # Tune and Retune buttons
        self.btTune = ttk.Button(self.frame, text="Tune", command=self.Tune)
        self.btTune.place(x=10, y=175, width=80)
        self.btRetune = ttk.Button(self.frame, text="Retune", command=self.Retune)
        self.btRetune.place(x=110, y=175, width=80)
        # build full name
        self.fullname = self.name
        while parent != None:
            try:
                if parent.GetObjectName() != "":
                    self.fullname = parent.GetObjectName() + '.' + self.fullname
            except:
                pass
            parent = parent.master
    def hide(self, flag):
        self.hidden = flag
        if flag: self.frame.place(x=-1000,y=-1000)
        else: self.frame.place(x=self.x,y=self.y)
    def isHidden(self):
        return self.hidden
    def rbChange(self):
        if self.cp == None: return
        self.cp.SendCommand('SRFMODE,' + str(self.channel) + ',' + self.Mode.get() + '\n')
    def Tune(self):
        MsgBox = tk.messagebox.askquestion('Tune RF head',
                                           'This function will tune the RF head attached to ' + self.MIPSname + ' channel ' + str(self.channel) + '. '
                                           'Make sure the RF head is attached and connected to your system as needed. '
                                           'This process can take up to 3 minutes, Continue? '
                                           , icon='warning')
        if MsgBox == 'no': return
        # Put channel in manual mode and set drive to 0
        if self.cp == None: return
        self.cp.SendCommand('SRFMODE,' + str(self.channel) + ',MANUAL\n')
        self.cp.SendCommand('SRFDRV,' + str(self.channel) + ',0\n')
        # Issue the tune command
        self.cp.SendCommand('TUNERFCH,' + str(self.channel) + '\n')
    def Retune(self):
        return
    def EntryChange(self, event):
        cmd = ''
        if event.widget == self.entDrive:
            cmd = 'SRFDRV,' + str(self.channel) + ',' + self.entDrive.get()
        elif event.widget == self.entSetpoint:
            cmd = 'SRFVLT,' + str(self.channel) + ',' + self.entSetpoint.get()
        elif event.widget == self.entFreq:
            cmd = 'SRFFRQ,' + str(self.channel) + ',' + self.entFreq.get()
        if self.cp == None: return
        if cmd != '': self.cp.SendCommand(cmd + '\n')
    def Update(self):
        MIPSobjects.entryBoxUpdate(self.entDrive, 'GRFDRV,' + str(self.channel) + '\n', self.cp)
        MIPSobjects.entryBoxUpdate(self.entSetpoint, 'GRFVLT,' + str(self.channel) + '\n', self.cp)
        MIPSobjects.entryBoxUpdate(self.entFreq, 'GRFFRQ,' + str(self.channel) + '\n', self.cp)
        MIPSobjects.entryBoxUpdate(self.entRFP, 'GRFPPVP,' + str(self.channel) + '\n', self.cp)
        MIPSobjects.entryBoxUpdate(self.entRFN, 'GRFPPVN,' + str(self.channel) + '\n', self.cp)
        MIPSobjects.entryBoxUpdate(self.entPWR, 'GRFPWR,' + str(self.channel) + '\n', self.cp)
    def Report(self):
        if self.isShutdown:
            drive = str(self.activeDrive)
            setpoint = str(self.activeSetpoint)
        else:
            drive = self.entDrive.get()
            setpoint = self.entSetpoint.get()
        return self.fullname + ',' + drive + ',' + self.entFreq.get() + ',' + setpoint \
               + ',' + self.entRFP.get() + ',' + self.entRFN.get() + ',' + self.entPWR.get()
    def SetValues(self, strVals):
        if strVals.startswith(self.fullname):
            tokens = strVals.split(',')
            if len(tokens) < 4: return False
            if self.isShutdown:
                self.activeDrive = float(tokens[1])
                self.activeSetpoint = float(tokens[3])
            else:
                self.entDrive.delete(0, 'end')
                self.entDrive.insert(0, tokens[1])
                self.entDrive.event_generate('<FocusOut>')
                self.entSetpoint.delete(0, 'end')
                self.entSetpoint.insert(0, tokens[3])
                self.entSetpoint.event_generate('<FocusOut>')
            self.entFreq.delete(0, 'end')
            self.entFreq.insert(0, tokens[2])
            self.entFreq.event_generate('<FocusOut>')
            return True
        return False
    def ProcessCommand(self, cmd):
        if cmd.startswith(self.fullname):
            if cmd == self.fullname + '.Drive': return(self.entDrive.get())
            if cmd == self.fullname + '.Setpoint': return(self.entSetpoint.get())
            if cmd == self.fullname + '.Freq': return(self.entFreq.get())
            if cmd == self.fullname + '.RF+': return(self.entRFP.get())
            if cmd == self.fullname + '.RF-': return(self.entRFN.get())
            if cmd == self.fullname + '.Power': return(self.entPWR.get())
            resList = cmd.split("=")
            if len(resList) == 2:
                if resList[0] + '.Drive':
                    self.entDrive.delete(0, 'end')
                    self.entDrive.insert(0, resList[1])
                    self.entDrive.event_generate('<FocusOut>')
                    return ""
                if resList[0] + '.Freq':
                    self.entFreq.delete(0, 'end')
                    self.entFreq.insert(0, resList[1])
                    self.entFreq.event_generate('<FocusOut>')
                    return ""
                if resList[0] + '.Setpoint':
                    self.entSetpoint.delete(0, 'end')
                    self.entSetpoint.insert(0, resList[1])
                    self.entSetpoint.event_generate('<FocusOut>')
                    return ""
            return '?'
        else: return '?'
    def Shutdown(self):
        if self.isShutdown: return
        self.isShutdown = True
        self.activeDrive = float(self.entDrive.get())
        self.entDrive.delete(0, 'end')
        self.entDrive.insert(0, '0')
        self.entDrive.event_generate('<FocusOut>')
        self.activeSetpoint = float(self.entSetpoint.get())
        self.entSetpoint.delete(0, 'end')
        self.entSetpoint.insert(0, '0')
        self.entSetpoint.event_generate('<FocusOut>')
    def Restore(self):
        if not self.isShutdown: return
        self.isShutdown = False
        self.entDrive.delete(0, 'end')
        self.entDrive.insert(0, '{:.2f}'.format(self.activeDrive))
        self.entDrive.event_generate('<FocusOut>')
        self.entSetpoint.delete(0, 'end')
        self.entSetpoint.insert(0, '{:.2f}'.format(self.activeSetpoint))
        self.entSetpoint.event_generate('<FocusOut>')
    def AutoUpdate(self, interval):
        self.interval = interval
        if self.interval == 0: return
        self.master.after(self.interval, lambda: self.AutoUpdate(self.interval))
        self.Update()

class RFdriver:
    def __init__(self, parent, num, MIPSname, comm):
        self.master = parent
        self.MIPSname = MIPSname
        self.cp = comm
        self.ch = []
        self.num = num
    def open(self):
        if self.num > 0: self.ch.append(RFchannel(self.master, "RF channel 1", self.MIPSname, 1, self.cp, 70, 40))
        if self.num > 1: self.ch.append(RFchannel(self.master, "RF channel 2", self.MIPSname, 2, self.cp, 70, 300))
        if self.num > 2: self.ch.append(RFchannel(self.master, "RF channel 3", self.MIPSname, 3, self.cp, 420, 40))
        if self.num > 3: self.ch.append(RFchannel(self.master, "RF channel 4", self.MIPSname, 4, self.cp, 420, 300))
        for c in self.ch:
            c.AutoUpdate(2000)
    def close(self):
        for c in self.ch:
            c.AutoUpdate(0)
        for c in self.ch:
            c.frame.destroy()
        self.ch.clear()
