import tkinter as tk

import MIPSobjects
import Util

#
# DCbias channel objects
#
# DCBchannel
# DCBenable
# DCBoffset
#

# todo:
#   - Add the linked DCBias channels
class DCBchannel:
    def __init__(self, parent, name, MIPSname, channel, comm, units, x, y):
        self.master = parent
        self.name = name
        self.MIPSname = MIPSname
        self.channel = channel
        self.units = units
        self.cp = comm
        self.interval = 0
        self.isShutdown = False
        self.activeVoltage = 0.0
        self.currentV = 0.0
        self.linkedDCB = []
        # get background color from parent if avalible
        try: bg = self.master.cget('bg')
        except: bg ="gray92"
        self.frame = tk.Frame(self.master, bg=bg)
        self.frame.place(x=x,y=y,width=350,height=25)
        self.lblName = tk.Label(self.frame, text=self.name, bg=bg)
        self.lblName.place(x=0,y=0)
        Util.CreateToolTip(self.lblName, self.MIPSname + " Channel " + str(self.channel))
        self.entDCBchan = tk.Entry(self.frame, width = 10, bd =0, relief=tk.FLAT)
        self.entDCBchan.place(x=100,y=0)
        self.entDCBchan.bind("<Return>", self.EntryChange)
        self.entDCBchan.bind("<FocusOut>", self.EntryChange)
        self.entDCBchan.bind("<Up>", self.UpArrow)
        self.entDCBchan.bind("<Down>", self.DownArrow)
        reg = self.entDCBchan.register(self.KeyCheck)
        self.entDCBchan.config(validate="key",validatecommand=(reg, '%P'))
        self.entRB = tk.Entry(self.frame, width = 10, bd =0,disabledforeground='black', relief=tk.FLAT)
        self.entRB.place(x=200,y=0)
        self.entRB.config(state='disabled')
        self.lblUnits = tk.Label(self.frame, text=self.units , bg=bg)
        self.lblUnits.place(x=300,y=0)
        self.readCMD = "GDCB," + str(self.channel)
        self.writeCMD = "SDCB," + str(self.channel) + ","
        self.readRB = "GDCBV," + str(self.channel)
        # build full name
        self.fullname = self.name
        while parent != None:
            try:
                if parent.GetObjectName() != "":
                    self.fullname = parent.GetObjectName() + '.' + self.fullname
            except: pass
            parent = parent.master
    def KeyCheck(self, input):
        if input[-1:].isdigit() or (input[-1:] == "") or (input[-1:] == ".") or (input[-1:] == "-"): return True
        else: return False
    def EntryChange(self, event):
        if self.cp.SendCommand(self.writeCMD + self.entDCBchan.get() + '\n'):
            self.currentV = float(self.entDCBchan.get())
    def UpArrow(self, event):
        # On a MAC event.state will define the  shift, control, option, and command keys
        # as bit masks:
        # Shift = 0x01
        # Control = (can't use unless I can stop system processing of key
        # Option = 0x10
        # Command = 0x08
        # event.widget defined what control caused this event
        if self.isShutdown: return
        if self.isShutdown: return
        if self.entDCBchan.get() == '': return
        delta = 1.0
        if (event.state & 0x01) != 0: delta *= 10
        elif (event.state & 0x10) != 0: delta /= 10
        fval = float(self.entDCBchan.get()) + delta
        self.entDCBchan.delete(0, 'end')
        self.entDCBchan.insert(0, '{:.2f}'.format(fval))
        self.EntryChange(None)
    def DownArrow(self, event):
        if self.isShutdown: return
        if self.entDCBchan.get() == '': return
        delta = -1.0
        if (event.state & 0x01) != 0: delta *= 10
        elif (event.state & 0x10) != 0: delta /= 10
        fval = float(self.entDCBchan.get()) + delta
        self.entDCBchan.delete(0, 'end')
        self.entDCBchan.insert(0, '{:.2f}'.format(fval))
        self.EntryChange(None)
    def Update(self):
        if MIPSobjects.entryBoxUpdate(self.entDCBchan, self.readCMD + '\n', self.cp): self.currentV = float(self.entDCBchan.get())
        if MIPSobjects.entryBoxUpdate(self.entRB, self.readRB + '\n', self.cp):
            verr = abs(self.currentV - float(self.entRB.get()))
            if (verr > 2.0) and (verr > abs(self.currentV / 100.0)): self.entRB.config(disabledbackground="red")
            else: self.entRB.config(disabledbackground="green2")
        res = self.cp.SendMessage(self.readRB + '\n')
        if res=="" or res==None: return
        self.entRB.delete(0,'end')
        self.entRB.insert(0,res)
        verr = abs(self.currentV - float(res))
        if (verr > 2.0) and (verr > abs(self.currentV / 100.0)): self.entRB.config(bg="red")
        else: self.entRB.config(bg="green2")
    def Report(self):
        if self.isShutdown: res = str(self.activeVoltage)
        else: res = self.entDCBchan.get()
        return self.fullname + ',' + res + ',' + self.entRB.get()
    def SetValues(self, strVals):
        if strVals.startswith(self.fullname):
            tokens = strVals.split(',')
            if len(tokens) < 2: return False
            self.currentV = float(tokens[1])
            if self.isShutdown:
                self.activeVoltage = self.currentV
            else:
                self.entDCBchan.delete(0, 'end')
                self.entDCBchan.insert(0, tokens[1])
                self.EntryChange(None)
            return True
        return False
    def ProcessCommand(self, cmd):
        if cmd.startswith(self.fullname):
            if cmd == self.fullname: return(self.entDCBchan.get())
            if cmd == (self.fullname + '.readback'): return(self.entRB.get())
            resList = cmd.split("=")
            if len(resList) == 2:
                self.entDCBchan.delete(0, 'end')
                self.entDCBchan.insert(0, resList[1])
                self.EntryChange(None)
                return ""
            return '?'
        else: return '?'
    def Shutdown(self):
        if self.isShutdown: return
        self.isShutdown = True
        self.activeVoltage = float(self.entDCBchan.get())
        self.entDCBchan.delete(0, 'end')
        self.entDCBchan.insert(0, '0')
        self.EntryChange(None)
    def Restore(self):
        if not self.isShutdown: return
        self.isShutdown = False
        self.entDCBchan.delete(0, 'end')
        self.entDCBchan.insert(0, '{:.2f}'.format(self.activeVoltage))
        self.EntryChange(None)
    def AutoUpdate(self, interval):
        self.interval = interval
        if self.interval == 0: return
        self.master.after(self.interval, lambda: self.AutoUpdate(self.interval))
        self.Update()

class DCBoffset:
    def __init__(self, parent, name, MIPSname, channel, comm, units, x, y):
        self.master = parent
        self.name = name
        self.MIPSname = MIPSname
        self.channel = channel
        self.units = units
        self.cp = comm
        # get background color from parent if avalible
        try: bg = self.master.cget('bg')
        except: bg ="gray92"
        self.frame = tk.Frame(self.master, bg=bg)
        self.frame.place(x=x,y=y,width=250,height=25)
        self.lblName = tk.Label(self.frame, text=self.name, bg=bg)
        self.lblName.place(x=0,y=0)
        Util.CreateToolTip(self.lblName, "Offset/range control " + self.MIPSname)
        self.entDCBoff = tk.Entry(self.frame, width = 10, bd =0, relief=tk.FLAT)
        self.entDCBoff.place(x=100,y=0)
        self.entDCBoff.bind("<Return>", self.EntryChange)
        self.entDCBoff.bind("<FocusOut>", self.EntryChange)
        reg = self.entDCBoff.register(self.KeyCheck)
        self.entDCBoff.config(validate="key",validatecommand=(reg, '%P'))
        self.lblUnits = tk.Label(self.frame, text=self.units , bg=bg)
        self.lblUnits.place(x=200,y=0)
        self.readCMD = "GDCBOF," + str(self.channel)
        self.writeCMD = "SDCBOF," + str(self.channel) + ","
        # build full name
        self.fullname = self.name
        while parent != None:
            try:
                if parent.GetObjectName() != "":
                    self.fullname = parent.GetObjectName() + '.' + self.fullname
            except: pass
            parent = parent.master
    def KeyCheck(self, input):
        if input[-1:].isdigit() or (input[-1:] == "") or (input[-1:] == ".") or (input[-1:] == "-"): return True
        else: return False
    def EntryChange(self, event):
        self.cp.SendCommand(self.writeCMD + self.entDCBoff.get() + '\n')
    def Update(self):
        MIPSobjects.entryBoxUpdate(self.entDCBoff, self.readCMD + '\n', self.cp)
    def Report(self):
        return self.fullname + ',' + self.entDCBoff.get()
    def SetValues(self, strVals):
        if strVals.startswith(self.fullname):
            tokens = strVals.split(',')
            if len(tokens) < 2: return False
            self.entDCBoff.delete(0, 'end')
            self.entDCBoff.insert(0, tokens[1])
            self.EntryChange(None)
            return True
        return False
    def ProcessCommand(self, cmd):
        if cmd.startswith(self.fullname):
            if cmd == self.fullname: return(self.entDCBoff.get())
            resList = cmd.split("=")
            if len(resList) == 2:
                self.entDCBoff.delete(0, 'end')
                self.entDCBoff.insert(0, resList[1])
                self.EntryChange(None)
                return ""
            return '?'
        else: return '?'
    def AutoUpdate(self, interval):
        self.interval = interval
        if self.interval == 0: return
        self.master.after(self.interval, lambda: self.AutoUpdate(self.interval))
        self.Update()

class DCBenable:
    def __init__(self, parent, name, MIPSname, comm, x, y):
        self.master = parent
        self.name = name
        self.MIPSname = MIPSname
        self.cp = comm
        # get background color from parent if avalible
        try: bg = self.master.cget('bg')
        except: bg ="gray92"
        self.frame = tk.Frame(self.master, bg=bg)
        self.frame.place(x=x,y=y,width=150,height=25)
        Util.CreateToolTip(self.frame, 'Enables all DC bias channels on ' + self.MIPSname)
        self.state = tk.StringVar()
        self.state.set('OFF')
        self.chkPWR = tk.Checkbutton(self.frame, text=self.name, variable=self.state, onvalue='ON', offvalue='OFF',bg=bg, command=self.EntryChange)
        self.chkPWR.place(x=0,y=0)
        self.readCMD = "GDCPWR"
        self.writeCMD = "SDCPWR,"
        # build full name
        self.fullname = self.name
        while parent != None:
            try:
                if parent.GetObjectName() != "":
                    self.fullname = parent.GetObjectName() + '.' + self.fullname
            except: pass
            parent = parent.master
    def EntryChange(self):
        self.cp.SendCommand(self.writeCMD + self.state.get() + '\n')
    def Update(self):
        res = self.cp.SendMessage(self.readCMD + '\n')
        if res=="" or res==None: return
        if res == 'ON': self.chkPWR.select()
        if res == 'OFF': self.chkPWR.deselect()
    def Report(self):
        return self.fullname + ',' + self.state.get()
    def SetValues(self, strVals):
        if strVals.startswith(self.fullname):
            tokens = strVals.split(',')
            if len(tokens) < 2: return False
            if tokens[1] == 'ON': self.chkPWR.select()
            elif tokens[1] == 'OFF': self.chkPWR.deselect()
            else: return False
            return True
        return False
    def ProcessCommand(self, cmd):
        if cmd.startswith(self.fullname):
            if cmd == self.fullname: return(self.state.get())
            resList = cmd.split("=")
            if len(resList) == 2:
                if resList[1] == 'ON': self.chkPWR.select()
                elif resList[1] == 'OFF': self.chkPWR.deselect()
                else: return '?'
                return ""
            return '?'
        else: return '?'
    def AutoUpdate(self, interval):
        self.interval = interval
        if self.interval == 0: return
        self.master.after(self.interval, lambda: self.AutoUpdate(self.interval))
        self.Update()

class DCBias:
    def __init__(self, parent, num, MIPSname, comm):
        self.master = parent
        self.MIPSname = MIPSname
        self.cp = comm
        self.ch = []
        self.num = num
    def open(self):
        if self.num > 0:
            self.ch.append(DCBenable(self.master, "Enable Pwr supply", self.MIPSname, self.cp, 20, 20))
            for i in range(1,9):
                self.ch.append(DCBchannel(self.master, "CH" + str(i), self.MIPSname, i, self.cp, "V", 20, 50 + i * 25))
            self.ch.append(DCBoffset(self.master, "OFF 1-8", self.MIPSname, 1, self.cp, "V", 20, 275))
        if self.num > 8:
            for i in range(9,17):
                self.ch.append(DCBchannel(self.master, "CH" + str(i), self.MIPSname, i, self.cp, "V", 20, 300 + (i-8) * 25))
            self.ch.append(DCBoffset(self.master, "OFF 9-16", self.MIPSname, 1, self.cp, "V", 20, 525))
        if self.num > 16:
            for i in range(17,25):
                self.ch.append(DCBchannel(self.master, "CH" + str(i), self.MIPSname, i, self.cp, "V", 400, 50 + (i-16) * 25))
            self.ch.append(DCBoffset(self.master, "OFF 17-24", self.MIPSname, 1, self.cp, "V", 400, 275))
        if self.num > 24:
            for i in range(25,33):
                self.ch.append(DCBchannel(self.master, "CH" + str(i), self.MIPSname, i, self.cp, "V", 400, 300 + (i-24) * 25))
            self.ch.append(DCBoffset(self.master, "OFF 25-32", self.MIPSname, 1, self.cp, "V", 400, 525))
        for c in self.ch:
            c.AutoUpdate(2000)
    def close(self):
        for c in self.ch:
            c.AutoUpdate(0)
        for c in self.ch:
            c.frame.destroy()
        self.ch.clear()

