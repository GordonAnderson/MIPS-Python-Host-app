import tkinter as tk
from tkinter import ttk

import MIPSobjects
import Util
#
# DIO channel objects
#
class DIOchannel:
    def __init__(self, parent, name, MIPSname, channel, comm, x, y):
        self.master = parent
        self.name = name
        self.MIPSname = MIPSname
        self.channel = channel
        self.cp = comm
        # get background color from parent if avalible
        try: bg = self.master.cget('bg')
        except: bg ="gray92"
        self.frame = tk.Frame(self.master, bg=bg)
        self.frame.place(x=x,y=y,width=150,height=25)
        Util.CreateToolTip(self.frame, self.MIPSname + ' DIO channel ' + self.channel)
        self.state = tk.StringVar()
        self.state.set('0')
        if channel >= 'Q': self.chkDIO = tk.Checkbutton(self.frame, text=self.name, variable=self.state, onvalue='1', offvalue='0',bg=bg, command=self.EntryChange, state='disable')
        else: self.chkDIO = tk.Checkbutton(self.frame, text=self.name, variable=self.state, onvalue='1', offvalue='0',bg=bg, command=self.EntryChange)
        self.chkDIO.config(disabledforeground = 'black')
        self.chkDIO.place(x=0,y=0)
        self.readCMD = "GDIO," + self.channel
        self.writeCMD = "SDIO," + self.channel + ','
        # build full name
        self.fullname = self.name
        while parent != None:
            try:
                if parent.GetObjectName() != "":
                    self.fullname = parent.GetObjectName() + '.' + self.fullname
            except: pass
            parent = parent.master
    def EntryChange(self):
        if self.channel >= 'Q': return
        self.cp.SendCommand(self.writeCMD + self.state.get() + '\n')
    def Update(self):
        res = self.cp.SendMessage(self.readCMD + '\n')
        if res=="" or res==None: return
        if res == '1': self.chkDIO.select()
        if res == '0': self.chkDIO.deselect()
    def Report(self):
        return self.fullname + ',' + self.state.get()
    def SetValues(self, strVals):
        if strVals.startswith(self.fullname):
            if self.channel >= 'Q': return False
            tokens = strVals.split(',')
            if len(tokens) < 2: return False
            if tokens[1] == '1': self.chkDIO.select()
            elif tokens[1] == '0': self.chkDIO.deselect()
            else: return False
            self.EntryChange()
            return True
        return False
    def ProcessCommand(self, cmd):
        if cmd.startswith(self.fullname):
            if cmd == self.fullname: return(self.state.get())
            resList = cmd.split("=")
            if len(resList) == 2:
                if self.channel >= 'Q': return '?'
                if resList[1] == '1': self.chkDIO.select()
                elif resList[1] == '0': self.chkDIO.deselect()
                else: return '?'
                return ""
            return '?'
        else: return '?'
    def AutoUpdate(self, interval):
        self.interval = interval
        if self.interval == 0: return
        self.master.after(self.interval, lambda: self.AutoUpdate(self.interval))
        self.Update()

class DIO:
    def __init__(self, parent, MIPSname, comm):
        self.master = parent
        self.MIPSname = MIPSname
        self.cp = comm
        self.ch = []
        self.frameDO = MIPSobjects.LabelFrame(parent,'Digital outputs', 180, 250)
        self.frameDO.place(x=20,y=20)
        self.frameDO.config(bg='gray89')
        for i in range (1,9):
            self.ch.append(DIOchannel(self.frameDO, chr(ord('A')+i-1), MIPSname, chr(ord('A')+i-1), self.cp, 10, 10 + 25 * (i-1)))
        for i in range (9,17):
            self.ch.append(DIOchannel(self.frameDO, chr(ord('A')+i-1), MIPSname, chr(ord('A')+i-1), self.cp, 120, 10 + 25 * (i-9)))
        self.frameDI = MIPSobjects.LabelFrame(parent,'Digital inputs', 100, 250)
        self.frameDI.place(x=250,y=20)
        self.frameDI.config(bg='gray89')
        for i in range (1,9):
            self.ch.append(DIOchannel(self.frameDI, chr(ord('Q')+i-1), MIPSname, chr(ord('Q')+i-1), self.cp, 30, 10 + 25 * (i-1)))
        self.ch.append(MIPSobjects.Ccontrol(self.master, 'TrigOut High', MIPSname, 'Button', '', 'TRIGOUT_HIGH', '', '', self.cp, 380,20))
        self.ch.append(MIPSobjects.Ccontrol(self.master, 'TrigOut Low', MIPSname, 'Button', '', 'TRIGOUT_LOW', '', '', self.cp, 380,45))
        self.ch.append(MIPSobjects.Ccontrol(self.master, 'TrigOut Pulse', MIPSname, 'Button', '', 'TRIGOUT_PULSE', '', '', self.cp, 380,70))
        self.ch.append(MIPSobjects.Ccontrol(self.master, 'AuxOut High', MIPSname, 'Button', '', 'AUXOUT_HIGH', '', '', self.cp, 560,20))
        self.ch.append(MIPSobjects.Ccontrol(self.master, 'AuxOut Low', MIPSname, 'Button', '', 'AUXOUT_LOW', '', '', self.cp, 560,45))
        self.ch.append(MIPSobjects.Ccontrol(self.master, 'AuxOut Pulse', MIPSname, 'Button', '', 'AUXOUT_PULSE', '', '', self.cp,560, 70))
        self.frameUI = MIPSobjects.LabelFrame(parent,'Remote UI navigation', 330, 160)
        self.frameUI.place(x=380,y=110)
        self.frameUI.config(bg='gray89')
        # '\u2191\u21E7\u2193\u21E9'
        self.nav = []
        self.nav.append(ttk.Button(self.frameUI, text='\u21E7', command=lambda: self.cp.SendString(str(chr(31)))))
        self.nav[-1].place(x=220, y=0, width = 50)
        self.nav.append(ttk.Button(self.frameUI, text='\u2191', command=lambda: self.cp.SendString(str(chr(30)))))
        self.nav[-1].place(x=220, y=25, width = 50)
        self.nav.append(ttk.Button(self.frameUI, text='Select', command=lambda: self.cp.SendString(str(chr(9)))))
        self.nav[-1].place(x=200, y=57)
        self.nav.append(ttk.Button(self.frameUI, text='\u2193', command=lambda: self.cp.SendString(str(chr(28)))))
        self.nav[-1].place(x=220, y=90, width = 50)
        self.nav.append(ttk.Button(self.frameUI, text='\u21E9', command=lambda: self.cp.SendString(str(chr(29)))))
        self.nav[-1].place(x=220, y=115, width = 50)
        for n in self.nav:
            n.config(state='disabled')
        self.state = tk.StringVar()
        self.state.set('0')
        self.chkEna = tk.Checkbutton(self.frameUI, text='Enable\nremote\nnavigation', variable=self.state, onvalue='1',offvalue='0', bg='gray89', command=self.navEnaCB)
        self.chkEna.config(disabledforeground='black')
        self.chkEna.place(x=25, y=40)
        self.frameFREQ = MIPSobjects.LabelFrame(parent,'Trigger output frequency generator', 690, 120)
        self.frameFREQ.place(x=20,y=300)
        self.frameFREQ.config(bg='gray89')
        self.ch.append(MIPSobjects.Ccontrol(self.frameFREQ, 'Frequency', MIPSname, 'LineEdit', 'GFREQ', 'SFREQ_', '', 'Hz', self.cp, 20, 20))
        self.ch.append(MIPSobjects.Ccontrol(self.frameFREQ, 'Pulse width', MIPSname, 'LineEdit', 'GWIDTH', 'SWIDTH_', '', 'uS', self.cp, 20, 50))
        self.cycles = MIPSobjects.Ccontrol(self.frameFREQ, 'Cycle count', '', 'LineEdit', 'Cycles', 'Cycles', '', '', None, 450, 20)
        self.cycles.SetValues('Trigger output frequency generator.Cycle count,1')
        ttk.Button(self.frameFREQ, text='Generate', command=self.generateBurst).place(x=550, y=50, width = 100)
    def generateBurst(self):
        self.cp.SendCommand('BURST,' + self.cycles.Report().split(',')[-1] + '\n')
    def navEnaCB(self):
        if self.state.get() == '1':
            for n in self.nav:
                n.config(state='normal')
            self.cp.SendCommand('SSERIALNAV,TRUE\n')
        if self.state.get() == '0':
            for n in self.nav:
                n.config(state='disabled')
    def open(self):
        for c in self.ch:
            c.AutoUpdate(2000)
    def close(self):
        for c in self.ch:
            c.AutoUpdate(0)

