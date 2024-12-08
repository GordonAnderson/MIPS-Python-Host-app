import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog

import MIPSobjects
import Util

class Event:
    def __init__(self):
        self.Name = ""
        self.Signal = ""
        self.Channel = ""
        self.Start = "0"
        self.Width = "0"
        self.StartT = 0.0
        self.WidthT = 0.0
        self.Value = 0.0
        self.ValueOff = 0.0

def Split(str, delim):
    s = ""
    reslist = []
    for c in str:
        if(c == " "): continue
        if(delim.__contains__(c)):
            if(s != ""): reslist.append(s)
            s = ""
            reslist.append(c)
        else: s += c
    if(s != ""): reslist.append(s)
    return reslist

def isNumber(val):
    try:
        #f = val.toFloat()
        float(val)
        return True
    except:
        return False

def calculateTime(events, val):
    sign = 1
    result = 0

    reslist = Split(val,"+-")
    for res in reslist:
        if isNumber(res): result += sign * float(res)
        elif(res == "+"): sign = 1
        elif(res == "-"): sign = -1
        else:
            for evt in events:
                name = evt.Name
                name.replace(" ","")
                if(res == name):
                    result += sign * calculateTime(events, evt.Start)
                    break
                if(res == (name + ".Start")):
                    result += sign * calculateTime(events, evt.Start)
                    break
                if(res == (name + ".Width")):
                    result += sign * calculateTime(events, evt.Width)
                    break
    return result

class TimingControl:
    def __init__(self, parent, name, MIPSname, comm, x, y):
        self.master = parent
        self.name = name
        self.MIPSname = MIPSname
        self.kind = 'Timing'
        self.cp = comm
        self.FrameCtAdj = 1
        self.AlwaysGenerate = False
        self.TG = TimingGenerator(parent,name,MIPSname, comm)
        # Create and place the trame
        self.bg = 'gray89'
        self.frame = MIPSobjects.LabelFrame(self.master, name, 140,120)
        self.frame.place(x=x,y=y)
        self.frame.config(bg=self.bg)
        # Create the Edit, Trigger, and Abort buttons
        self.btEdit = ttk.Button(self.frame, text="Edit", command=self.Edit)
        self.btEdit.place(x=20, y=10, width=100)
        self.btTrigger = ttk.Button(self.frame, text="Trigger", command=self.Trigger)
        self.btTrigger.place(x=20, y=40, width=100)
        self.btAbort = ttk.Button(self.frame, text="Abort", command=self.Abort)
        self.btAbort.place(x=20, y=70, width=100)
    def Edit(self):
        self.TG.hide(False)
    def Trigger(self):
        pass
    def Abort(self):
        pass

class TimingGenerator:
    def __init__(self, parent, name, MIPSname, comm):
        self.master = parent
        self.name = name
        self.MIPSname = MIPSname
        self.cp = comm
        self.frameCtAdj = 1
        self.Events = []
        self.signals = {}
        self.create()
    def clearEvent(self):
        self.entEvtName.delete(0, 'end')
        self.entEvtStart.delete(0, 'end')
        self.entEvtWidth.delete(0, 'end')
        self.entEvtValue.delete(0, 'end')
        self.entEvtValueOff.delete(0, 'end')
        self.comboEvtSig.set("")
    def selectEvent(self, name):
        # find event in list of events
        evt = self.findEvent(name)
        if (evt == None): return
        self.clearEvent()
        self.entEvtName.insert(0, evt.Name)
        self.entEvtStart.insert(0, evt.Start)
        self.entEvtWidth.insert(0, evt.Width)
        self.entEvtValue.insert(0, evt.Value)
        self.entEvtValueOff.insert(0, evt.ValueOff)
        self.comboEvtSig.set(evt.Signal)
    def findEvent(self,name):
        for e in self.Events:
            if(e.Name == name): return e
        return None
    def updateEvents(self):
        self.comboEvent['values'] = ("", "New event", "Rename event", "Delete current")
        for evt in self.Events:
            self.comboEvent['values'] = tuple(list(self.comboEvent['values']) + [str(evt.Name)])
    def addSignal(self, name, channel):
        self.signals.update({name: channel})
        self.comboEvtSig['values'] = list(self.signals.keys())
    def hide(self,state):
        if state: self.root.withdraw()
        else:
            self.root.deiconify()
            self.root.focus()
    def convertToCount(self, val):
        result = calculateTime(self.Events,val)
        if(self.TM.get()):
            global clock
            clock = self.comboClkSource.get()
            print(clock)
            if isNumber(clock) == False: clock = self.entExtClock.get()
            print(result * float(clock)/1000.0)
            return result * float(clock)/1000.0
        return result
    def Generate(self):
        maxCount = self.convertToCount(str(self.entFrmWidth.get()))
        maxEventCount = 0
        global revt
        revt = Event()
        revt.Name = ""
        global FrameStartT
        global timeFlag
        for evt in self.Events:
            # If this is a Repeat event then make a copy
            if (evt.Name == "Repeat"):
                revt = evt
                evt.StartT = int(evt.Start)
                evt.WidthT = int(evt.Width)
            if(evt.Channel == ""): continue
            evt.StartT = self.convertToCount(evt.Start)
            evt.WidthT = self.convertToCount(evt.Width)
            if ((abs(evt.StartT) + abs(evt.WidthT)) > maxEventCount): maxEventCount = abs(evt.StartT) + abs(evt.WidthT)
        FrameStartT = 0
        table = ""
        if self.comboTrgSource.get() == "Software": table = "STBLDAT;0:[A:" + str(int(self.entFrmAcc.get()) + self.frameCtAdj)
        else: table = "STBLDAT;0:[A:" + self.entFrmAcc.get()
        for i in range(int(abs(maxCount))):
            if ((revt.Name == "Repeat") and (i > 0) and (int(revt.Width) > 0)):
                if (i % int(self.convertToCount(revt.Width))) == 0:
                    for evt in self.Events:
                        if evt.Name == "Repeat":
                            if self.convertToCount(evt.StartT + evt.WidthT) < abs(maxCount):
                                evt.StartT += evt.Width
                                evt.Start = evt.StartT
                    for evt in self.Events:
                        if evt.Channel == "": continue
                        evt.StartT = self.convertToCount(evt.Start)
                        evt.WidthT = self.convertToCount(evt.Width)
            timeFlag = False
            for evt in self.Events:
                if evt.Channel == "": continue
                global Chan
                Chan = evt.Channel
                if evt.Width.upper() == "INIT": Chan = str(int(Chan) + 128 + 64)
                if evt.Width.upper() == "RAMP": Chan = str(int(Chan) + 128)
                if int(abs(evt.StartT)) == i:
                    if timeFlag == False:
                        table += "," + str(int(evt.StartT))
                        timeFlag = True
                    if Chan == "c":
                        if evt.Signal == "ARBct":
                            table += ":" + Chan + ":A"
                        else: table += ":" + Chan + ":T"
                    else: table += ":" + Chan + ":" + str(evt.Value)
                if int(abs(evt.StartT + evt.WidthT)) == i:
                    if abs(evt.WidthT) > 0:
                        if timeFlag == False:
                            table += "," + str(int(evt.StartT + evt.WidthT))
                            timeFlag = True
                        table += ":" + Chan + ":" + evt.ValueOff
            if((abs(maxCount) == i) or ((maxEventCount < i) and (revt.Name != "Repeat"))):
                if timeFlag == False:
                    table += "," + str(int(maxCount))
                    timeFlag = True
                table += ":];";
                break
        self.entTable.delete(0, 'end')
        self.entTable.insert(0,table)
        if (revt.Name == "Repeat"):
            for evt in self.Events:
                if (evt.Name == "Repeat"): evt = revt
    def Load(self):
        pass
    def Save(self):
        pass
    def create(self):
        def on_closing():
            self.hide(True)
        def EntryChange(event):
            evt = self.findEvent(self.entEvtName.get())
            if(evt == None): return
            print("event changed")
            evt.Start = self.entEvtStart.get()
            evt.Width = self.entEvtWidth.get()
            evt.Value = self.entEvtValue.get()
            evt.ValueOff = self.entEvtValueOff.get()
            evt.Signal = self.comboEvtSig.get()
            evt.Channel = self.signals[self.comboEvtSig.get()]
        def eventChanged(event):
            if(self.comboEvent.get() == "New event"):
                self.comboEvent.set("")
                newEvent = simpledialog.askstring(title="New event", prompt="Enter new event name:")
                if(newEvent != None):
                    if(self.findEvent(newEvent) == None):
                        # Create the event and add to event list
                        evt = Event()
                        evt.Name = newEvent
                        self.Events.append(evt)
                        self.comboEvent['values'] = tuple(list(self.comboEvent['values']) + [str(newEvent)])
                        self.selectEvent(newEvent)
                        return
                    else:
                        # Event name alreay exists, display error
                        tk.messagebox.showerror('Name error', 'Event name alreay exists!', icon='error')
                        return
            if (self.comboEvent.get() == "Rename event"):
                evt = self.findEvent(self.entEvtName.get())
                if (evt != None):
                    newName = simpledialog.askstring(title="New event", prompt="Enter new event name:")
                    if(newName != None):
                        i = self.Events.index(evt)
                        self.Events[i].Name = newName
                        self.updateEvents()
                        self.comboEvent.set("")
                        self.clearEvent()
                else:
                    self.comboEvent.set("")
                    self.clearEvent()
            if (self.comboEvent.get() == "Delete current"):
                evt = self.findEvent(self.entEvtName.get())
                if(evt != None):
                    self.Events.remove(evt)
                    self.updateEvents()
                    self.comboEvent.set("")
                    self.clearEvent()
                else:
                    self.comboEvent.set("")
                    self.clearEvent()
            self.selectEvent(self.comboEvent.get())
        # get background color from parent if avalible
        try: self.bg = self.master.cget('bg')
        except: self.bg ="gray92"
        self.root = tk.Toplevel(self.master, bg=self.bg)
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        self.root.withdraw()
        self.root.geometry('665x255')
        self.root.resizable(0, 0)
        self.root.title(self.name + ' editor')
        # Dialog labels
        tk.Label(self.root, text="Select event", bg=self.bg).place(x=10, y=5)
        tk.Label(self.root, text="Ext Clock Freq", bg=self.bg).place(x=465, y=35)
        tk.Label(self.root, text="Clock source", bg=self.bg).place(x=465, y=65)
        tk.Label(self.root, text="Trigger source", bg=self.bg).place(x=465, y=95)
        tk.Label(self.root, text="Mux order", bg=self.bg).place(x=465, y=125)
        tk.Label(self.root, text="Table", bg=self.bg).place(x=5, y=225)
        # Dialog controls
        self.comboEvent = ttk.Combobox(self.root, width=12)
        self.comboEvent.place(x=100, y=5)
        self.comboEvent['values'] = ("", "New event", "Rename event", "Delete current")
        self.comboEvent.bind('<<ComboboxSelected>>', eventChanged)
        self.comboClkSource = ttk.Combobox(self.root, width=8)
        self.comboClkSource.place(x=560, y=65)
        self.comboClkSource['values'] = ("Ext", "ExtN", "ExtS", "42000000", "10500000", "2625000", "656250")
        self.comboClkSource.set("656250")
        self.comboTrgSource = ttk.Combobox(self.root, width=8)
        self.comboTrgSource.place(x=560, y=95)
        self.comboTrgSource['values'] = ("Software", "Edge", "Pos", "Neg")
        self.comboTrgSource.set("Software")
        self.comboMuxOrder = ttk.Combobox(self.root, width=8)
        self.comboMuxOrder.place(x=560, y=125)
        self.comboMuxOrder['values'] = ("None", "4 Bit", "5 Bit", "6 Bit", "7 Bit", "8 Bit", "9 Bit")
        self.comboMuxOrder.set("None")
        self.entExtClock = tk.Entry(self.root, width = 10, bd =0, relief=tk.FLAT)
        self.entExtClock.insert(0,"10000")
        self.entExtClock.place(x=560,y=35)
        self.entTable = tk.Entry(self.root, width = 65, bd =0, relief=tk.FLAT)
        self.entTable.place(x=50,y=225)
        self.btClear = ttk.Button(self.root, text ="Clear all events", command = None)
        self.btClear.place(x=240, y=5, width=150)
        self.TimeMode = False
        self.TM = tk.BooleanVar()
        self.TM.set(self.TimeMode)
        self.chkTM = tk.Checkbutton(self.root, text="Time mode, in mS", variable=self.TM, onvalue=True, offvalue=False,bg="gray95")
        self.chkTM.place(x=465, y=5)
        self.btEdit = ttk.Button(self.root, text="Generate", command=self.Generate)
        self.btEdit.place(x=460, y=155, width=190)
        self.btEdit = ttk.Button(self.root, text="Load", command=self.Load)
        self.btEdit.place(x=460, y=190, width=86)
        self.btEdit = ttk.Button(self.root, text="Save", command=self.Save)
        self.btEdit.place(x=564, y=190, width=86)
        # Event editor
        self.bg = 'gray89'
        self.frmEE = MIPSobjects.LabelFrame(self.root, "Event editor", 210,180)
        self.frmEE.place(x=10,y=35)
        self.frmEE.config(bg=self.bg)
        tk.Label(self.frmEE, text="Name", bg=self.bg).place(x=10, y=5)
        tk.Label(self.frmEE, text="Signal", bg=self.bg).place(x=10, y=30)
        tk.Label(self.frmEE, text="Start", bg=self.bg).place(x=10, y=55)
        tk.Label(self.frmEE, text="Width", bg=self.bg).place(x=10, y=80)
        tk.Label(self.frmEE, text="Value", bg=self.bg).place(x=10, y=105)
        tk.Label(self.frmEE, text="Value,off", bg=self.bg).place(x=10, y=130)
        self.entEvtName = tk.Entry(self.frmEE, width = 10, bd =0, relief=tk.FLAT)
        self.entEvtName.place(x=100,y=5)
        self.entEvtStart = tk.Entry(self.frmEE, width = 10, bd =0, relief=tk.FLAT)
        self.entEvtStart.place(x=100,y=55)
        self.entEvtStart.bind("<Return>", EntryChange)
        self.entEvtStart.bind("<FocusOut>", EntryChange)
        self.entEvtWidth = tk.Entry(self.frmEE, width = 10, bd =0, relief=tk.FLAT)
        self.entEvtWidth.place(x=100,y=80)
        self.entEvtWidth.bind("<Return>", EntryChange)
        self.entEvtWidth.bind("<FocusOut>", EntryChange)
        self.entEvtValue = tk.Entry(self.frmEE, width = 10, bd =0, relief=tk.FLAT)
        self.entEvtValue.place(x=100,y=105)
        self.entEvtValue.bind("<Return>", EntryChange)
        self.entEvtValue.bind("<FocusOut>", EntryChange)
        self.entEvtValueOff = tk.Entry(self.frmEE, width = 10, bd =0, relief=tk.FLAT)
        self.entEvtValueOff.place(x=100,y=130)
        self.entEvtValueOff.bind("<Return>", EntryChange)
        self.entEvtValueOff.bind("<FocusOut>", EntryChange)
        self.comboEvtSig = ttk.Combobox(self.frmEE, width=8)
        self.comboEvtSig.place(x=100, y=30)
        self.comboEvtSig.bind("<Return>", EntryChange)
        self.comboEvtSig.bind("<FocusOut>", EntryChange)
        # Frame paraameters
        self.frmFP = MIPSobjects.LabelFrame(self.root, "Frame parameters", 220,150)
        self.frmFP.place(x=230,y=65)
        self.frmFP.config(bg=self.bg)
        tk.Label(self.frmFP, text="Width", bg=self.bg).place(x=10, y=30)
        tk.Label(self.frmFP, text="Accumulations", bg=self.bg).place(x=10, y=70)
        self.entFrmWidth = tk.Entry(self.frmFP, width = 10, bd =0, relief=tk.FLAT)
        self.entFrmWidth.insert(0, "1000")
        self.entFrmWidth.place(x=110,y=30)
        self.entFrmAcc = tk.Entry(self.frmFP, width = 10, bd =0, relief=tk.FLAT)
        self.entFrmAcc.insert(0, "10")
        self.entFrmAcc.place(x=110,y=70)

