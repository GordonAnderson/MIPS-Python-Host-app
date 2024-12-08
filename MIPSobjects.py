import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import Util

#
# Todo:
#   1.) Finish the DCBchannel and test, done
#   2.) Impliment DCBenable, done
#   3.) Impliment DCBoffset, done
#   4.) Impliment DCBiasGroung
#   5.) Build DCbias tab
#   6.) Impliment DIOchannel, done
#   7.) Implement Ccontrol, done
#   8.) Build DIO tab
#   8.) Implement RFcontrol, done

def entryBoxUpdate(object, cmd, cp):
    if not object == object.focus_get():
        res = cp.SendMessage(cmd)
        if res=="" or res==None: return False
        if object.config().get('state')[-1] == 'disabled':
            object.config(state='normal')
            object.delete(0,'end')
            object.insert(0,res)
            object.config(state='disabled')
        else:
            object.delete(0,'end')
            object.insert(0,res)
        return True
#
# Control panel objects
#

# Creates a window to hold the control panel
class Window(tk.Toplevel):
    def __init__(self, name, width, height, *args, **kwargs):
        self.name = name
        tk.Toplevel.__init__(self, *args, **kwargs)
        self.config(bg="gray92")
        self.geometry(str(width) + 'x' + str(height))
        self.title(name)
    def GetObjectName(self):
        return self.name
    def SetObjectName(self, name):
        self.name = name

class LabelFrame(tk.LabelFrame):
    def __init__(self, master, name, width, height):
        tk.LabelFrame.__init__(self, master, text = name, width = width, height = height, bg = "gray95", bd = 0)
        self.name = name
    def GetObjectName(self):
        return self.name
    def SetObjectName(self, name):
        self.name = name
        self.configure(text = name)

class TextFileWindow:
    def __init__(self, title, filename):
        self.title = title
        self.filename = filename
        self.window = None
    def closingCallBack(self):
        self.window.destroy()
        self.window = None
    def save(self, filename):
        try:
            with open(filename, 'w') as file:
                file.write(self.mipsHelp.get("1.0", "end"))
                file.close()
        except: pass
    def load(self, filename):
        try:
            with open(filename, 'r') as file:
                data = file.read()
                file.close()
                self.mipsHelp.delete("1.0", "end")
                self.mipsHelp.insert(tk.END, data)
        except:
            self.mipsHelp.delete("1.0", "end")
            self.mipsHelp.insert(tk.END, "Can't open " + self.filename)
    def keyDetect(self, event):
        if self.filename == '': return
        MsgBox = tk.messagebox.askquestion('Save to file',
                                           'Save data to file: ' + self.filename + ', Continue?'
                                           , icon='warning')
        if MsgBox == 'no': return
        self.save(self.filename)
    def show(self):
        if self.window != None: return
        # create window
        self.window = tk.Toplevel()
        self.window.protocol("WM_DELETE_WINDOW", self.closingCallBack)
        self.window.geometry('600x400')
        self.window.title(self.title)
        # Horizontal (x) Scroll bar
        xscrollbar = tk.Scrollbar(self.window, orient=tk.HORIZONTAL)
        xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        # Vertical (y) Scroll Bar
        yscrollbar = tk.Scrollbar(self.window)
        yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.mipsHelp = tk.Text(self.window, wrap="none", bg="gray95")
        self.mipsHelp.pack(fill="both", expand=True)
        self.mipsHelp.bind("<Control-s>", self.keyDetect)
        # Configure the scrollbars
        xscrollbar.config(command=self.mipsHelp.xview)
        yscrollbar.config(command=self.mipsHelp.yview)
        self.mipsHelp['yscrollcommand'] = yscrollbar.set
        self.mipsHelp['xscrollcommand'] = xscrollbar.set
        # Load file text to window
        if self.filename != "": self.load(self.filename)

class Tab:
    def __init__(self, parent, name, width, height, x, y):
        self.tabs = []
        self.frms = []
        self.names = []
        self.master = parent
        self.name = name
        try: bg = self.master.cget('bg')
        except: bg ="gray92"
        self.frame = tk.Frame(self.master, bg=bg)
        self.frame.place(x=x,y=y,width=width,height=height)
        self.tabControl = ttk.Notebook(self.frame,padding=0)
        #self.tabControl.configure(borderwidth=0)
    def addTab(self, name):
        self.frms.append(ttk.Frame(self.tabControl))
        self.names.append(name)
        self.tabControl.add(self.frms[-1], text=name)
        self.tabControl.pack(expand=1, fill="both")
    def selectTab(self, name, tname):
        if(name != self.name): return None
        for i in range(0,len(self.names)):
            if(tname == ''.join(self.names[i])):
                return self.frms[i]
        return None


#
# Custom control object
#
#  Implements a generic control with the following features:
#      - TYPE, defines the control type
#              - LineEdit, CheckBox, Button, ComboBox
#      - Set command
#              to set the MIPS value from LineEdit box
#              checked state command for the CheckBox
#              pressed command for Button
#      - Get command
#              to read the MIPS value to update the LineEdit box
#              unchecked state command for the CheckBox
#              not used for Button
#      - Readback command
#              if set add a readback box and this command will read the value for LineEdit
#              CheckBox read command
#              not used for Button
#  Syntax example:
#      Ccontrol,name,mips name,type,get command,set command,readback command,units,X,Y
#
class Ccontrol:
    def __init__(self, parent, name, MIPSname, type, getcmd, setcmd, rbcmd, units, comm, x, y, w = -1, h = 25):
        self.master = parent
        self.name = name
        self.units = units
        self.MIPSname = MIPSname
        self.kind = 'Ccontrol'
        self.cp = comm
        self.x=x
        self.y=y
        self.w=w
        self.h=h
        self.isShutdown = False
        self.ShutDownValue = None
        self.ActiveValue = 0.0
        self.setcmd = setcmd.replace('_',',')
        self.getcmd = getcmd.replace('_',',')
        self.rbcmd = rbcmd.replace('_',',')
        self.type = type
        self.entVal = None
        self.entRB = None
        self.comboBox = None
        self.chkBox = None
        # get background color from parent if avalible
        try: bg = self.master.cget('bg')
        except: bg ="gray92"
        # build full name
        self.fullname = self.name
        while parent != None:
            try:
                if parent.GetObjectName() != "":
                    self.fullname = parent.GetObjectName() + '.' + self.fullname
            except:
                pass
            parent = parent.master
        if self.type == 'LineEdit':
            # If Read back command or set command are empty then its only one lineEdit
            # box, else two.
            if self.w == -1: w = 80
            if self.setcmd == '' or self.rbcmd == '':
                # Only 1 entry box
                self.frame = tk.Frame(self.master, bg=bg)
                self.frame.place(x=x, y=y, width=w + 150, height=h)
                self.lblName = tk.Label(self.frame, text=self.name, bg=bg, justify=tk.LEFT)
                self.lblName.place(x=0, y=0)
                if self.units != '':
                    self.lblUnits = tk.Label(self.frame, text=self.units, bg=bg)
                    self.lblUnits.place(x=w + 70, y=(h-25)/2)
                if self.setcmd != '':
                    self.entVal = tk.Entry(self.frame, width=7, bd=0, relief=tk.FLAT)
                    self.entVal.place(x=w, y=(h-25)/2)
                    self.entVal.bind("<Return>", self.EntryChange)
                    self.entVal.bind("<FocusOut>", self.EntryChange)
                elif self.rbcmd != '':
                    self.entRB = tk.Entry(self.frame, width=7, bd=0, disabledforeground='black', relief=tk.FLAT)
                    self.entRB.place(x=80, y=(h-25)/2)
                    self.entRB.config(state='disabled')
            else:
                self.frame = tk.Frame(self.master, bg=bg)
                self.frame.place(x=x, y=y, width=350, height=25)
                self.lblName = tk.Label(self.frame, text=self.name, bg=bg)
                self.lblName.place(x=0, y=0)
                self.entVal = tk.Entry(self.frame, width=7, bd=0, relief=tk.FLAT)
                self.entVal.place(x=80, y=0)
                self.entVal.bind("<Return>", self.EntryChange)
                self.entVal.bind("<FocusOut>", self.EntryChange)
                self.entRB = tk.Entry(self.frame, width=7, bd=0, disabledforeground='black', relief=tk.FLAT)
                self.entRB.place(x=155, y=0)
                self.entRB.config(state='disabled')
                self.lblUnits = tk.Label(self.frame, text=self.units, bg=bg)
                self.lblUnits.place(x=225, y=0)
            pass
        elif self.type == 'CheckBox':
            if self.w == -1: w = 150
            self.frame = tk.Frame(self.master, bg=bg)
            self.frame.place(x=x, y=y, width=w, height=25)
            self.state = tk.StringVar()
            self.state.set(self.getcmd.split(',')[-1])
            self.chkBox = tk.Checkbutton(self.frame, text=self.name, variable=self.state, onvalue=self.setcmd.split(',')[-1], offvalue=self.getcmd.split(',')[-1],bg=bg, command=lambda: self.EntryChange(None))
            self.chkBox.config(disabledforeground='black')
            self.chkBox.place(x=0, y=0)
        elif self.type == 'Button':
            self.frame = tk.Frame(self.master, bg=bg)
            self.frame.place(x=x, y=y, width=150, height=25)
            self.button = ttk.Button(self.frame, text=self.name, command=lambda: self.EntryChange(None))
            self.button.place(x=0, y=0, width=150)
        elif self.type == 'ComboBox':
            self.frame = tk.Frame(self.master, bg=bg)
            self.frame.place(x=x, y=y, width=250, height=25)
            self.lblName = tk.Label(self.frame, text=self.name, bg=bg)
            self.lblName.place(x=0, y=0)
            if self.units != '':
                self.lblUnits = tk.Label(self.frame, text=self.units, bg=bg)
                self.lblUnits.place(x=200, y=0)
            self.comboBox = ttk.Combobox(self.frame, width=10)
            self.comboBox.place(x=100, y=0)
            self.comboBox.bind('<<ComboboxSelected>>', self.EntryChange)
    def EntryChange(self, event):
        if self.cp == None: return
        if self.type == 'LineEdit':
            self.cp.SendCommand(self.setcmd + self.entVal.get() + '\n')
        elif self.type == 'CheckBox':
            if self.state.get() == self.setcmd.split(',')[-1]: self.cp.SendCommand(self.setcmd + '\n')
            else: self.cp.SendCommand(self.getcmd + '\n')
        elif self.type == 'Button':
            self.cp.SendCommand(self.setcmd + '\n')
        elif self.type == 'ComboBox':
            if self.comboBox.get() == '': return
            if self.comboBox.get() == None: return
            self.cp.SendCommand(self.setcmd + self.comboBox.get() + '\n')
    def Update(self):
        if self.cp == None: return
        if self.type == 'LineEdit':
            if self.entVal != None: entryBoxUpdate(self.entVal, self.getcmd + '\n', self.cp)
            if self.entRB != None: entryBoxUpdate(self.entRB, self.rbcmd + '\n', self.cp)
        elif self.type == 'CheckBox':
            res = self.cp.SendMessage(self.rbcmd + '\n')
            if res == self.setcmd.split(',')[-1]: self.chkBox.select()
            if res == self.getcmd.split(',')[-1]: self.chkBox.deselect()
        elif self.type == 'ComboBox':
            res = self.cp.SendMessage(self.getcmd + '\n')
            self.comboBox.set(res)
    def Get(self):
        if self.type == 'LineEdit':
            return(self.entVal.get())
        elif self.type == 'CheckBox':
            return(self.state.get())
        elif self.type == 'ComboBox':
            return(self.comboBox.get())
    def Report(self):
        if self.type == 'LineEdit':
            res = ''
            if self.entVal != None: res = ',' + self.entVal.get()
            if self.entRB != None: res = ',' + self.entRB.get()
            if res == '': return('')
            if self.isShutdown: res = ',' + str(self.ActiveValue)
            return(self.fullname + res)
        elif self.type == 'CheckBox':
            return(self.fullname + ',' + self.state.get())
        elif self.type == 'ComboBox':
            return(self.fullname + ',' + self.comboBox.get())
    def Set(self, strVals):
        if self.type == 'LineEdit':
            self.entVal.delete(0, 'end')
            self.entVal.insert(0, strVals)
            self.entVal.event_generate('<FocusOut>')
            return True
        elif self.type == 'CheckBox':
            tokens = strVals.split(',')
            #if len(tokens) < 2: return False
            if tokens[-1] == self.setcmd.split(',')[-1]: self.chkBox.select()
            elif tokens[-1] == self.getcmd.split(',')[-1]: self.chkBox.deselect()
            else:
                return False
            return True
        elif self.type == 'ComboBox':
            if strVals == None: strVals = " "
            tokens = strVals.split(',')
            self.comboBox.set(tokens[-1])
    def SetValues(self,strVals):
        if not strVals.startswith(self.fullname): return False
        if self.type == 'LineEdit':
            if self.entVal == None: return(False)
            tokens = strVals.split(',')
            if len(tokens) < 2: return False
            if self.isShutdown: self.ActiveValue = float(tokens[2])
            else:
                self.entVal.delete(0, 'end')
                self.entVal.insert(0, tokens[len(tokens)-1])
                self.entVal.event_generate('<FocusOut>')
            return True
        elif self.type == 'CheckBox':
            tokens = strVals.split(',')
            if len(tokens) < 2: return False
            if tokens[1] == self.setcmd.split(',')[-1]: self.chkBox.select()
            elif tokens[1] == self.getcmd.split(',')[-1]: self.chkBox.deselect()
            else: return False
            return True
        elif self.type == 'ComboBox':
            tokens = strVals.split(',')
            if len(tokens) < 2: return False
            try:
                i = self.comboBox['values'].index(tokens[1].strip())
                self.comboBox.current(i)
                return True
            except:
                return False
        return False
    def ProcessCommand(self, cmd):
        if not cmd.startswith(self.fullname): return '?'
        if self.type == 'LineEdit':
            if cmd.strip() == self.fullname:
                if self.entVal != None:
                    return self.entVal.get()
                if self.entRB != None:
                    return self.entRB.get()
                return '?'
            if cmd.strip() == self.fullname + '.readback':
                if self.entVal != None and self.entRB != None:
                    return self.entRB.get()
                return '?'
            tokens = cmd.split('=')
            if len(tokens) < 2: return('?')
            if self.entVal == None: return('?')
            if tokens[0].strip() == self.fullname:
                self.entVal.delete(0, 'end')
                self.entVal.insert(0, tokens[1].strip())
                self.EntryChange(None)
                return ''
            return '?'
        elif self.type == 'CheckBox':
            if cmd.strip() == self.fullname:
                return self.state.get()
            tokens = cmd.split('=')
            if len(tokens) < 2: return('?')
            if tokens[0].strip() == self.fullname:
                if tokens[1].strip() == self.setcmd.split(',')[-1]: self.chkBox.select()
                elif tokens[1].strip() == self.getcmd.split(',')[-1]: self.chkBox.deselect()
                else: return '?'
                self.EntryChange(None)
                return ""
        elif self.type == 'Button':
            if cmd.strip() == self.fullname:
                self.EntryChange(None)
                return ''
        elif self.type == 'ComboBox':
            if cmd.strip() == self.fullname:
                return self.comboBox.get()
            tokens = cmd.split('=')
            if len(tokens) < 2: return False
            try:
                i = self.comboBox['values'].index(tokens[1].strip())
                self.comboBox.current(i)
                self.EntryChange(None)
                return ''
            except:
                return '?'
    def SetList(self, comboBoxList):
        if self.comboBox == None: return
        self.comboBox['values'] = comboBoxList
    def Shutdown(self):
        if self.type == 'LineEdit':
            if self.ShutDownValue == None: return
            if self.isShutdown: return
            self.isShutdown = True
            self.activeVoltage = float(self.entVal.get())
            self.entVal.delete(0, 'end')
            self.entVal.insert(0, str(self.ShutDownValue))
            self.EntryChange(None)
    def Restore(self):
        if self.type == 'LineEdit':
            if not self.isShutdown: return
            self.isShutdown = False
            self.entVal.delete(0, 'end')
            self.entVal.insert(0, '{:.2f}'.format(self.activeVoltage))
            self.EntryChange(None)
    def AutoUpdate(self, interval):
        self.interval = interval
        if self.interval == 0: return
        self.master.after(self.interval, lambda: self.AutoUpdate(self.interval))
        self.Update()
