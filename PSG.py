# system imports
from __future__ import absolute_import
import tkinter as tk
from tkinter import ttk

# this applications imports
import Comms
import MIPSobjects
import Util

class psgPoint:
    def __init__(self):
        self.Name = None
        self.TimePoint = None
        self.Commands = []
        self.Loop = False
        self.LoopName = None
        self.LoopCount = 0

class PSE:
    def __init__(self, parent):
        self.master = parent
        self.psgPoints = []
        self.CurrentIndex = 0
    def createTP(self):
         # If the sequence list is empty create a time point
        if len(self.psgPoints) <= 0:
            tp = psgPoint()
            tp.Name = "TP_1"
            tp.TimePoint = 0
            tp.Commands.append("A=0")
            self.psgPoints.append(tp)
            self.CurrentIndex = 0
            return
        # If here insert new time ppoint at the current index.
        # First build a unique time point name
        name = self.psgPoints[self.CurrentIndex].Name
        np = name.split('_')
        if np[-1].isnumeric():
            name = ""
            for i in range(len(np)-1):
                if name == "": name += np[i]
                else: name += "_" + np[i]
            name += "_" + str(int(np[-1]) + 1)
        else: name += "_1"
        # If name is not unique then add _1 to the end of name until it is!
        while True:
            for x in self.psgPoints:
                if name == x.Name:
                    name += "_1"
                    break
            else:
                # Here with a unique name, insert the time point and advance current index to this point
                ntp = psgPoint()
                ntp.Name = name
                ntp.TimePoint = int(self.psgPoints[self.CurrentIndex].TimePoint) + 100
                ntp.Commands.append("A=0")
                self.CurrentIndex += 1
                if len(self.psgPoints) <= self.CurrentIndex: self.psgPoints.append(ntp)
                else: self.psgPoints.insert(self.CurrentIndex,ntp)
                return
    def updateTP(self):
        self.psgPoints[self.CurrentIndex].Name = self.TPname.Get()
        self.psgPoints[self.CurrentIndex].TimePoint = self.NumClk.Get()
        self.psgPoints[self.CurrentIndex].LoopCount = self.NumCycles.Get()
        if self.Loop.Get() == 'On': self.psgPoints[self.CurrentIndex].Loop = True
        else: self.psgPoints[self.CurrentIndex].Loop = False
        self.psgPoints[self.CurrentIndex].Commands = self.txtTPcommands.get('1.0', tk.END).splitlines()
        self.psgPoints[self.CurrentIndex].LoopName = self.LoopPoint.Get()
    def displayTP(self):
        name = 'Current time point {} of {}'
        self.frameCTP.SetObjectName(name.format(self.CurrentIndex+1, len(self.psgPoints)))
        self.TPname.Set(self.psgPoints[self.CurrentIndex].Name)
        self.NumClk.Set(self.psgPoints[self.CurrentIndex].TimePoint)
        self.NumCycles.Set(self.psgPoints[self.CurrentIndex].LoopCount)
        self.txtTPcommands.config(state='normal')
        self.txtTPcommands.delete("1.0", 'end')
        for x in self.psgPoints[self.CurrentIndex].Commands:
            self.txtTPcommands.insert(tk.END, x + '\n')
        if self.psgPoints[self.CurrentIndex].Loop: self.Loop.Set('On')
        else: self.Loop.Set('Off')
        # Fill loop selection combo box with valid name options
        self.LoopPoint.comboBox.select_clear()
        lst = []
        for i in range(self.CurrentIndex):
            lst.append(self.psgPoints[i].Name)
        self.LoopPoint.SetList(lst)
        self.LoopPoint.Set(self.psgPoints[self.CurrentIndex].LoopName)
    def open(self):
        self.createTP()
        # Create the pulse sequence editor
        self.pse = tk.Toplevel()
        self.pse.config(bg="gray98")
        self.pse.geometry('450x600')
        self.pse.title("Pulse Sequence Editor")
        self.frameCTP = MIPSobjects.LabelFrame(self.pse, 'Current time point 1 of 1', 430, 140)
        self.frameCTP.place(x=10, y=10)
        self.frameCTP.config(bg='gray89')
        self.TPname = MIPSobjects.Ccontrol(self.frameCTP, 'Name', '', 'LineEdit', 'Name', 'Name', '', '', None, 20, 20, 300)
        self.NumClk = MIPSobjects.Ccontrol(self.frameCTP, 'Number of clocks from start of sequence', '', 'LineEdit', 'NumClk', 'NumClk', '', '', None, 20, 50,300)
        self.NumTime = MIPSobjects.Ccontrol(self.frameCTP, 'Time from start of sequence', '', 'LineEdit', 'NumTime', 'NumTime', '', '', None, 20, 80,300)
        self.Editor()
        self.displayTP()
    def Editor(self):
        self.btNext = ttk.Button(self.pse, text="Next", command=self.Next)
        self.btNext.place(x=10, y=160, width=80)
        self.btInsert = ttk.Button(self.pse, text="Insert", command=self.Insert)
        self.btInsert.place(x=98, y=160, width=80)
        self.btPulse = ttk.Button(self.pse, text="Pulse", command=self.PulseEditor)
        self.btPulse.place(x=186, y=160, width=80)
        self.btPrevious = ttk.Button(self.pse, text="Prev", command=self.Prev)
        self.btPrevious.place(x=274, y=160, width=80)
        self.btDelete = ttk.Button(self.pse, text="Delete", command=self.Delete)
        self.btDelete.place(x=360, y=160, width=80)
        self.LoopPoint = MIPSobjects.Ccontrol(self.pse, '', '', 'ComboBox', 'LoopPoint', 'LoopPoint', '', '', None, 20,
                                              200)
        self.Loop = MIPSobjects.Ccontrol(self.pse, 'Loop to', '', 'CheckBox', 'Off', 'On', '', '', None, 10, 200, 100)
        self.NumCycles = MIPSobjects.Ccontrol(self.pse, 'Num cycles', '', 'LineEdit', 'NumCycles', 'NumCycles', '', '',
                                              None, 240, 200)
        tk.Label(self.pse, text="Time point settings:", bg="gray89", anchor="w").place(x=10, y=240, width=150)
        self.txtTPcommands = tk.Text(self.pse, bg="gray92", bd=0, highlightbackground="gray92")
        self.txtTPcommands.place(x=10, y=270, width=430, height=320)
        self.txtTPcommands.config(font=("", 14))
    def PulseEditorDismiss(self):
        self.framePulse.place_forget()
        self.Editor()
        self.displayTP()
    def PulseEditor(self):
        self.framePulse = MIPSobjects.LabelFrame(self.pse, 'Insert pulse parameters', 430, 430)
        self.framePulse.place(x=10, y=160)
        self.framePulse.config(bg='gray89')
        self.btCancel = ttk.Button(self.framePulse, text="Cancel", command=self.PulseEditorDismiss)
        self.btCancel.place(x=200, y=380, width=100)
        self.btGenerate = ttk.Button(self.framePulse, text="Generate", command=None)
        self.btGenerate.place(x=320, y=380, width=100)
        mess = "This function will generate the time points needed to make a\n" \
               "voltage pulse on the DC bias channel number selected. If you\n" \
               "are inserting this between existing time points in a sequence\n" \
               "then there must be adequate space or an error will be reported."
        tk.Label(self.framePulse, text=mess, bg="gray89", justify=tk.LEFT).place(x=10, y=10, width=410)
        self.RPchan = MIPSobjects.Ccontrol(self.framePulse, 'DC bias channel', '', 'LineEdit', 'RPchan', 'RPchan', '',
                                           '', None, 30, 100, 200)
        mess = "Pulse voltage, note the\ncurrent time point\nvalue will define the\nresting voltage"
        self.RPPV = MIPSobjects.Ccontrol(self.framePulse, mess, '', 'LineEdit', 'PV', 'PV', '', 'Volts', None, 30, 130,
                                         200, 75)
        self.PulseWidth = MIPSobjects.Ccontrol(self.framePulse, 'Pulse width', '', 'LineEdit', 'PulseWidth',
                                               'PulseWidth', '', 'cycles', None, 30, 210, 200)
        self.RampUp = MIPSobjects.Ccontrol(self.framePulse, 'Ramp up number\nof steps', '', 'LineEdit', 'RampUp',
                                           'RampUp', '', '', None, 30, 240, 200, 50)
        self.RampDown = MIPSobjects.Ccontrol(self.framePulse, 'Ramp down number\nof steps', '', 'LineEdit', 'RampDown',
                                             'RampDown', '', '', None, 30, 280, 200, 50)
        self.RampStepSize = MIPSobjects.Ccontrol(self.framePulse, 'Ramp step size', '', 'LineEdit', 'RampStepSize',
                                                 'RampStepSize', '', 'cycles', None, 30, 330, 200)
        self.RPchan.Set('1')
        self.RPPV.Set('100')
        self.PulseWidth.Set('1000')
        self.RampUp.Set('10')
        self.RampDown.Set('10')
        self.RampStepSize.Set('10')
    def Insert(self):
        #self.updateTP()
        self.createTP()
        self.displayTP()
    def Prev(self):
        self.updateTP()
        if self.CurrentIndex > 0:
            self.CurrentIndex = self.CurrentIndex - 1
            self.displayTP()
    def Next(self):
        self.updateTP()
        if (self.CurrentIndex + 1) < len(self.psgPoints):
            self.CurrentIndex = self.CurrentIndex + 1
            self.displayTP()
    def Delete(self):
        if len(self.psgPoints) > 1:
            self.psgPoints.pop(self.CurrentIndex)
            if self.CurrentIndex >= len(self.psgPoints): self.CurrentIndex = len(self.psgPoints)-1
            self.displayTP()

ClockOptions = ["Ext","ExtN","ExtS","42000000","10500000","2625000","656250"]
TriggerOptions = ["Software","Edge","Pos","Neg"]

class PSG:
    def __init__(self, parent, mips):
        self.master = parent
        self.mips = mips
        self.pse = PSE(self)
    def open(self):
        # get background color from parent if avalible
        try: bg = self.master.cget('bg')
        except: bg ="gray92"
        self.framePS = MIPSobjects.LabelFrame(self.master,'Pulse Sequence', 700, 70)
        self.framePS.place(x=20,y=20)
        self.framePS.config(bg='gray89')
        self.btLoad = ttk.Button(self.framePS, text ="Load from file", command = None)
        self.btLoad.place(x=20, y=10, width=150)
        self.btEdit = ttk.Button(self.framePS, text ="Edit current", command = None)
        self.btEdit.place(x=190, y=10, width=150)
        self.btCreate = ttk.Button(self.framePS, text ="Create new", command = self.CreateNew)
        self.btCreate.place(x=360, y=10, width=150)
        self.btSave = ttk.Button(self.framePS, text ="Save to file", command = None)
        self.btSave.place(x=530, y=10, width=150)

        self.frameSGC = MIPSobjects.LabelFrame(self.master, 'Sequence Generator Control', 700, 100)
        self.frameSGC.place(x=20, y=120)
        self.frameSGC.config(bg='gray89')
        self.clock = MIPSobjects.Ccontrol(self.frameSGC, 'Clock', '', 'ComboBox', 'Clock', 'Clock', '', '', None, 20, 10)
        self.clock.SetList(ClockOptions)
        self.clock.comboBox.current(0)
        self.trigger = MIPSobjects.Ccontrol(self.frameSGC, 'Trigger', '', 'ComboBox', 'Trigger', 'Trigger', '', '', None, 20, 40)
        self.trigger.SetList(TriggerOptions)
        self.trigger.comboBox.current(0)
        self.ExtClockFreq = MIPSobjects.Ccontrol(self.frameSGC, 'Ext clock freq', '', 'LineEdit', 'ExtClock', 'ExtClock', '', '', None, 480, 20)
        self.ExtClockFreq.Set('6250')

        self.frameETP = MIPSobjects.LabelFrame(self.master, 'Edit loaded pulse sequence time point', 400, 140)
        self.frameETP.place(x=320, y=250)
        self.frameETP.config(bg='gray89')
        self.TimePoint = MIPSobjects.Ccontrol(self.frameETP, 'Time point', '', 'LineEdit', 'TimePoint','TimePoint', '', '', None, 20, 20)
        self.Channel = MIPSobjects.Ccontrol(self.frameETP, 'Channel', '', 'LineEdit', 'Channel','Channel', '', '', None, 20, 50)
        self.Value = MIPSobjects.Ccontrol(self.frameETP, 'Value', '', 'LineEdit', 'Value','Value', '', '', None, 20, 80)
        self.btRead = ttk.Button(self.frameETP, text ="Read", command = None)
        self.btRead.place(x=270, y=30, width=100)
        self.btWrite = ttk.Button(self.frameETP, text ="Write", command = None)
        self.btWrite.place(x=270, y=60, width=100)

        self.SeqNum = MIPSobjects.Ccontrol(self.master, 'Sequence Nr', '', 'LineEdit', 'SeqNum','SeqNum', '', '', None, 40, 270)
        self.AdvNum = MIPSobjects.Ccontrol(self.master, 'Advance Seq Nr', '', 'CheckBox', 'On','Off', '', '', None, 40, 330)
        self.btDownload = ttk.Button(self.master, text ="Download", command = None)
        self.btDownload.place(x=35, y=420, width=120)
        self.btViewTable = ttk.Button(self.master, text ="View table", command = None)
        self.btViewTable.place(x=165, y=420, width=120)
        self.btVisualize = ttk.Button(self.master, text ="Visualize", command = None)
        self.btVisualize.place(x=295, y=420, width=120)
        self.btTrigger = ttk.Button(self.master, text ="Trigger", command = None)
        self.btTrigger.place(x=425, y=420, width=120)
        self.btTrigger = ttk.Button(self.master, text ="Exit table mode", command = None)
        self.btTrigger.place(x=555, y=420, width=140)
    def CreateNew(self):
        self.pse.psgPoints.clear()
        self.pse.open()
    def close(self):
        pass

