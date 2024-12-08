import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image
from PIL import ImageTk
import time
import threading
import os

import MIPSobjects
import Util
import DCBias
import RFdriver
import DIO
import MIPS
import MIPSobjects
import Scripting
import Comms
import Timing

#
# Add:
#  1.) SENDCOMMAND (done)
#  2.) TCPSERVER
#  3.) SCRIPTBUTTON (done)
#       - add option for run once and run on update, CALLONSTART, CALLONUPDATE
#  4.) CPANEL, loads an additional control panel
#  5.) ARBCHANNEL
#  6.) COMPRESSOR
#  7.) CPBUTTON, reloads the current control panel
#  8.) TIMING
#  9.) Status bar (done)
#  10.) Properties, intergrate into control panel
#  11.) Logging
#  12.) Help
#  13.) Add Kind to all mips objects (done)
#  14.) When shutting down do not shutdown DC bias channels if there is an enable
#  15.) Add find file function (done)
#  16.) Serial watch dog??
#  17.) Device
#  18.) ESI
#  19.) Status light
#  20.) RFamp
#  21.) Plotting
#  22.) control panel functions
#       - Command (done)
#       - Add include capability

class ControlPanel:
    def __init__(self, parent, filename, mips):
        def on_closing():
            if self.Shutdown:
                MsgBox = tk.messagebox.askquestion('MIPS warning!',
                                'The system is currently shutdown, this means all voltages are disabled and ' + \
                                'all RF drive levels are set to 0. Make sure you have saved all your settings ' + \
                                'because when the control panel is restarted you will lose the shutdown recover data.' + \
                                ' Continue?'
                                , icon='warning')
                if MsgBox == 'no': return
            self.mips.master.deiconify()
            self.containers[0].destroy()
        self.master = parent
        self.filename = filename
        self.width = 670
        self.height = 350
        self.mips = mips
        self.mips.cpanel = self
        self.cpobjs = []
        self.cp = None
        self.scrpt = None
        self.interval = 1000
        self.lock = threading.Lock()
        self.Shutdown = False
        self.GroupBoxes = []
        self.containers = []
        if(self.master == None): self.containers.append(tk.Toplevel())
        else: self.containers.append(self.master)
        self.containers[-1].config(bg="gray95")
        self.containers[-1].geometry('670x350')
        self.containers[-1].title(filename)
        # Open file and load the controls. Read the file line by line and process
        cpfile = open(filename,'r')
        if not cpfile: return
        while True:
            line = cpfile.readline()
            if not line: break
            if len(line) <= 0: break
            line = line.strip()
            if len(line) == 0: continue
            # file line starts with # its a comment
            if(line[0] == "#"): continue
            res = line.split(",")
            if(len(res) == 3) and (res[0].strip().upper() == "SIZE"):
                self.containers[-1].geometry(res[1].strip() + "x" + res[2].strip())
                self.width = int(res[1].strip())
                self.height = int(res[2].strip())
            if(len(res) == 2) and (res[0].strip().upper() == "IMAGE"):
                try:
                    bg = self.containers[-1].cget('bg')
                except:
                    bg = "gray92"
                try:
                    self.photo = Image.open(self.mips.findFile(res[1].strip(),self.filename))
                    self.photo = self.photo.resize((self.width-10, self.height-10), Image.ANTIALIAS)
                    self.photoImg = ImageTk.PhotoImage(self.photo)
                    self.background = tk.Label(self.containers[-1], image=self.photoImg, bg=bg)
                    self.background.place(x=0, y=0)
                except:
                    pass
            if(len(res) == 3) and (res[0].strip().upper() == "MIPSCOMMS"):
                self.mipsCommasButton = ttk.Button(self.containers[-1], text="MIPS comms", command=self.commsPressed)
                self.mipsCommasButton.place(x=res[1].strip(), y=res[2].strip(), width=150)
            if(len(res) == 5) and (res[0].strip().upper() == "TEXTLABEL"):
                try:
                    bg = self.containers[-1].cget('bg')
                except:
                    bg = "gray92"
                tk.Label(self.containers[-1], text=res[1].strip(),bg=bg,font=("", res[2].strip())).place(x=res[3].strip(), y=res[4].strip())
            if (len(res) == 4) and (res[0].strip().upper() == "SHUTDOWN"):
                self.shutdownName = res[1].strip()
                self.enableName = "System enable"
                self.SaveButtonName = tk.StringVar()
                self.SaveButtonName.set(res[1].strip())
                self.SaveButton = ttk.Button(self.containers[-1], textvariable = self.SaveButtonName, command=self.shutdownPressed)
                self.SaveButton.place(x=res[2].strip(), y=res[3].strip(), width=150)
            if (len(res) == 5) and (res[0].strip().upper() == "SAVELOAD"):
                self.SaveButton = ttk.Button(self.containers[-1], text=res[1].strip(), command=self.savePressed)
                self.SaveButton.place(x=res[3].strip(), y=res[4].strip(), width=150)
                self.LoadButton = ttk.Button(self.containers[-1], text=res[2].strip(), command=self.loadPressed)
                self.LoadButton.place(x=res[3].strip(), y=int(res[4].strip()) + 40, width=150)
            if (len(res) == 3) and (res[0].strip().upper() == "SCRIPT"):
                self.ScriptButton = ttk.Button(self.containers[-1], text="Script", command=self.scriptPressed)
                self.ScriptButton.place(x=res[1].strip(), y=res[2].strip(), width=150)
            if (len(res) == 5) and (res[0].strip().upper() == "SCRIPTBUTTON"):
                self.cpobjs.append(Scripting.ScriptButton(self.containers[-1],res[1].strip(),self.mips.findFile(res[2].strip(),self.filename),res[3].strip(),res[4].strip()))
                self.cpobjs[-1].locals = mips.locals
                self.cpobjs[-1].statusbarMessage = self.statusbarMessage
            if (len(res) == 2) and (res[0].strip().upper() == "CALLONSTART"):
                if(res[1].strip() == 'TRUE'):
                    self.cpobjs[-1].runOnce = True
            if (len(res) == 2) and (res[0].strip().upper() == "CALLONUPDATE"):
                if(res[1].strip() == 'TRUE'):
                    self.cpobjs[-1].onUpdate = True
            if (len(res) == 6) and (res[0].strip().upper() == "DCBCHANNEL"):
                cp = self.mips.findMIPScp(res[2].strip())
                self.cpobjs.append(DCBias.DCBchannel(self.containers[-1], res[1].strip(), res[2].strip(), res[3].strip(), cp, "V", res[4].strip(), res[5].strip()))
            if (len(res) == 6) and (res[0].strip().upper() == "DCBOFFSET"):
                cp = self.mips.findMIPScp(res[2].strip())
                self.cpobjs.append(DCBias.DCBoffset(self.containers[-1], res[1].strip(), res[2].strip(), res[3].strip(), cp, "V", res[4].strip(), res[5].strip()))
            if (len(res) == 5) and (res[0].strip().upper() == "DCBENABLE"):
                cp = self.mips.findMIPScp(res[2].strip())
                self.cpobjs.append(DCBias.DCBenable(self.containers[-1], res[1].strip(), res[2].strip(), cp, res[3].strip(), res[4].strip()))
            if (len(res) == 6) and (res[0].strip().upper() == "RFCCHANNEL"):
                cp = self.mips.findMIPScp(res[2].strip())
                self.cpobjs.append(RFdriver.RFchannel(self.containers[-1], res[1].strip(), res[2].strip(), res[3].strip(), cp, res[4].strip(), res[5].strip()))
            if (len(res) == 6) and (res[0].strip().upper() == "RFCHANNEL"):
                cp = self.mips.findMIPScp(res[2].strip())
                self.cpobjs.append(RFdriver.RFchannel(self.containers[-1], res[1].strip(), res[2].strip(), res[3].strip(), cp, res[4].strip(), res[5].strip()))
            if (len(res) == 6) and (res[0].strip().upper() == "DIOCHANNEL"):
                cp = self.mips.findMIPScp(res[2].strip())
                self.cpobjs.append(DIO.DIOchannel(self.containers[-1], res[1].strip(), res[2].strip(), res[3].strip(), cp, res[4].strip(), res[5].strip()))
            if (len(res) >= 10) and (res[0].strip().upper() == "CCONTROL"):
                cp = self.mips.findMIPScp(res[2].strip())
                self.cpobjs.append(MIPSobjects.Ccontrol(self.containers[-1],res[1].strip(),res[2].strip(),res[3].strip(),res[4].strip(),res[5].strip(),res[6].strip(),res[7].strip(),cp,res[8].strip(),res[9].strip()))
            if (len(res) == 6) and (res[0].strip().upper() == "GROUPBOX"):
                self.GroupBoxes.append(MIPSobjects.LabelFrame(self.containers[-1],res[1].strip(),res[2].strip(),res[3].strip()))
                self.GroupBoxes[-1].place(x=res[4].strip(), y=res[5].strip())
                self.GroupBoxes[-1].config(bg='gray89')
                self.containers.append(self.GroupBoxes[-1])
            if (len(res) == 1) and (res[0].strip().upper() == "GROUPBOXEND"):
                self.containers.pop()
            if (len(res) >= 7) and (res[0].strip().upper() == "TAB"):
                self.cpobjs.append(MIPSobjects.Tab(self.containers[-1],res[1].strip(),res[2].strip(),res[3].strip(),res[4].strip(),res[5].strip()))
                for i in range(6, len(res)):
                    self.cpobjs[-1].addTab(res[i].split())
                    print(res[i].split())
            if (len(res) == 3) and (res[0].strip().upper() == "TABSELECT"):
                for i in range (0, len(self.cpobjs)):
                    try:
                        frm = self.cpobjs[i].selectTab(res[1].strip(),res[2].strip())
                        if frm != None: self.containers.append(frm)
                    except:
                        pass
            if (len(res) == 1) and (res[0].strip().upper() == "TABSELECTEND"):
                self.containers.pop()
            if (len(res) > 2) and (res[0].strip().upper() == "SENDCOMMAND"):
                if(line.strip().upper().startswith(res[0].strip().upper())):
                    self.mips.SendCommand(res[1], ((line.strip()[line.find(res[1])+len(res[1])+1:]).strip()) + '\n')
            if (len(res) == 5) and (res[0].strip().upper() == "TIMING"):
                cp = self.mips.findMIPScp(res[2].strip())
                self.cpobjs.append(Timing.TimingControl(self.containers[-1], res[1].strip(), res[2].strip(), cp, res[3].strip(), res[4].strip()))
        cpfile.close()
        self.statusbar = tk.Label(self.containers[0], text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.statusbarMessage(" Control panel initalizing...", 2000)
        self.containers[0].protocol("WM_DELETE_WINDOW", on_closing)
        #self.containers[0].mainloop()
        for obj in self.cpobjs:
            try:
                if(obj.kind == "Timing"):
                    obj.TG.addSignal("Trig out", "t")
                    obj.TG.addSignal("Delta t", "d")
                    for obj1 in self.cpobjs:
                        try:
                            if(obj1.kind == "DCBchannel") or (obj1.kind == "DIOchannel"):
                                if(obj1.MIPSname == obj.MIPSname): obj.TG.addSignal(obj1.name, obj1.channel)
                        except:
                            pass
            except:
                pass
    def statusbarMessage(self,message, ctime = 0):
        self.statusbar.configure(text=message)
        if ctime > 0: self.statusbar.after(ctime,self.clearStatusbar)
    def clearStatusbar(self):
        self.statusbar.configure(text="")
    def Command(self,cmd):
        # Add SHUTDOWN, RESTORE, SAVE, LOAD, SENDMESSAGE, SENDCOMMAND
        for obj in self.cpobjs:
            try:
                res = obj.ProcessCommand(cmd)
                if res != '?': return(res + '\n')
            except:
                pass
        return('?\n')
    def scriptPressed(self):
        if self.scrpt == None:
            self.scrpt = Scripting.Script(self.containers[0], self.mips.locals)
            self.scrpt.show()
        self.scrpt.hide(False)
    def savePressed(self):
        # This function saves the current control panel settings as well as the following meta-data
        # - Control panel name
        # - Time and date
        # - MIPS versions (if connected)
        # - MIPS uptime (if connected)
        localFile = filedialog.asksaveasfilename(parent = self.containers[0],initialdir=self.mips.application_path, title="Select file to save method data",filetypes = (("Method file","*.settings"),("all files","*.*")))
        if localFile == '': return
        fp = open(localFile,"w")
        fp.write('# Control panel settings, ' + time.asctime(time.localtime(time.time())) + '\n')
        fp.write('# MIPS, ' + self.mips.Version + '\n')
        fp.write('# Control panel file,' + self.filename + '\n')
        for s in self.mips.Systems:
            fp.write('# ' + s.MIPSname + ': ' + s.MIPSver + '\n')
            res = s.SendMessage('UPTIME\n')
            fp.write('# ' + s.MIPSname + ': ' + res + '\n')
        for obj in self.cpobjs:
            try:
                fp.write(obj.Report() + '\n')
            except:
                pass
        fp.close()
    def loadPressed(self):
        localFile = filedialog.askopenfilename(initialdir=self.mips.application_path, title="Select file to load method data",filetypes = (("settings file","*.settings"),("all files","*.*")))
        if localFile == '': return
        fp = open(localFile,'r')
        if not fp: return
        while True:
            line = fp.readline()
            if not line: break
            if len(line) <= 0: break
            line = line.strip()
            if len(line) == 0: continue
            # file line starts with # its a comment
            if(line[0] == "#"): continue
            for obj in self.cpobjs:
                try:
                    if(obj.SetValues(line)): continue
                except:
                    pass
        fp.close()
    def shutdownPressed(self):
        # This function will shut the MIPS systems down by setting the
        # outputs to zero.
        # Update this function. Need to first look for and shutdown all
        # DCBenables and make a list of MIPS names that are disabled.
        # Then do not shutdown any DCBias channels or offsets that are
        # in this MIPS name list
        if(self.SaveButtonName.get() == self.shutdownName):
            self.SaveButtonName.set(self.enableName)
            self.Shutdown = True
            for obj in self.cpobjs:
                try:
                    obj.Shutdown()
                except:
                    pass
        else:
            self.SaveButtonName.set(self.shutdownName)
            self.Shutdown = False
            for obj in self.cpobjs:
                try:
                    obj.Shutdown()
                except:
                    pass
    def commsPressed(self):
        def mipsSelectCallback(event):
            cp = self.mips.findMIPScp(comboMIPSs.get())
            Term.cp = cp
            self.close()
            Term.open()
        def on_closing():
            Term.close()
            self.open()
            mipsComms.destroy()
        cp = None
        mipsComms = tk.Toplevel()
        mipsComms.protocol("WM_DELETE_WINDOW", on_closing)
        mipsComms.geometry('600x390')
        mipsComms.title("MIPS communications")
        tk.Label(mipsComms, text="Select MIPS system").place(x=15, y=5)
        comboMIPSs = ttk.Combobox(mipsComms, width=13)
        comboMIPSs['state'] = 'readonly'
        comboMIPSs.place(x=10, y=25)
        # Fill the MIPS selection comboBox
        strList = []
        for s in self.mips.Systems:
            strList.append(s.MIPSname)
        comboMIPSs['values'] = strList
        comboMIPSs.bind("<<ComboboxSelected>>", mipsSelectCallback)
        try:
            comboMIPSs.current(0)
        except:
            pass
        commsFrame = ttk.Frame(mipsComms)
        commsFrame.place(x=5, y=60)
        Term = Comms.Terminal(commsFrame, cp)
        mipsSelectCallback(None)
        mipsComms.grab_set()
        mipsComms.mainloop()
    def AutoUpdate(self, interval):
        self.interval = interval
        if self.interval == 0: return
        for c in self.cpobjs:
            try:
                self.lock.acquire(1)
                c.Update()
                self.lock.release()
            except:
                self.lock.release()
        self.containers[0].after(self.interval, lambda: self.AutoUpdate(self.interval))
    def open(self):
        self.AutoUpdate(2000)
    def close(self):
        self.AutoUpdate(0)
