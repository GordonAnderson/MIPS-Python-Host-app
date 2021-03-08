#
# MIPS host application
#
# This application must be built using Python version 3.7.6 and pyinstaller version 4.0. Later versions
# of these tools will not work due to a code signing set of bugs that are not yet resolved.
#
# Todo:
#   1.) Impliment programming functions
#   2.) Impliment help functions
#   3.) Finish comm class and add remaining menu options
#

# system imports
from __future__ import absolute_import
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import simpledialog
import os
import sys
import time

# this applications imports
import Comms
import Command
import Scripting
import MIPSobjects
import Program
import DCBias
import DIO
import RFdriver
import System
import PSG
import JTAG

global tabControl

class Properties:
    def __init__(self, parent):
        self.master = parent
        self.LoadControlPanel = ''
        self.LogFile = ''
        self.AutoConnect = False
        self.AutoRestore = False
        self.MinMIPS = 0
        self.UpdateSecs = 3
        self.MIPS_TCPIP = []
        self.MIPS_TCPIP.clear()
    def Show(self):
        self.properties = tk.Toplevel()
        self.properties.config(bg="gray98")
        self.properties.geometry('440x280')
        self.properties.title("MIPS properties")
        self.suo = tk.LabelFrame(self.properties, text="Startup options", width=420, height=150, bg="gray95", bd=0)
        self.suo.place(x=10, y=10)
        self.AC = tk.BooleanVar()
        self.AC.set(self.AutoConnect)
        self.chkAC = tk.Checkbutton(self.suo, text="Auto connect at startup", variable=self.AC, onvalue=True, offvalue=False,bg="gray95", command=self.EntryChange)
        self.chkAC.place(x=10, y=10)
        self.btLoadCP = tk.Button(self.suo, text=" Load Control Panel ", command=self.EntryChange)
        self.btLoadCP.place(x=10, y=35)
        self.entCP = tk.Entry(self.suo, width=25, bd=0, relief=tk.FLAT)
        self.entCP.place(x=175, y=35)
        self.entCP.delete(0, 'end')
        self.entCP.insert(0, self.LoadControlPanel)
        tk.Label(self.suo, text="Minimum number of MIPS systems", bg="gray95").place(x=10, y=65)
        self.entMIPSs = tk.Entry(self.suo, width=4, bd=0, relief=tk.FLAT)
        self.entMIPSs.place(x=250, y=65)
        self.entMIPSs.delete(0, 'end')
        self.entMIPSs.insert(0, str(self.MinMIPS))
        tk.Label(self.suo, text="MIPS TCP/IP list", bg="gray95").place(x=10, y=95)
        self.comboTCPIP = ttk.Combobox(self.suo, width=15)
        self.comboTCPIP.place(x=175, y=95)
        self.btClear = tk.Button(self.suo, text=" Clear ", command=self.EntryChange)
        self.btClear.place(x=350, y=95)
        self.ARC = tk.BooleanVar()
        self.ARC.set(self.AutoRestore)
        self.chkARC = tk.Checkbutton(self.properties, text="Automatically restore connections", variable=self.ARC, onvalue=True, offvalue=False,bg="gray98", command=self.EntryChange)
        self.chkARC.place(x=10, y=170)
        self.btLogFile = tk.Button(self.properties, text=" Log File ", command=self.EntryChange)
        self.btLogFile.place(x=10, y=195)
        self.entLogFile = tk.Entry(self.properties, width=35, bd=0, relief=tk.FLAT)
        self.entLogFile.place(x=100, y=195)
        self.entLogFile.delete(0, 'end')
        self.entLogFile.insert(0, self.LogFile)
        tk.Label(self.properties, text="Seconds between updates", bg="gray98").place(x=10, y=230)
        self.entUpdate = tk.Entry(self.properties, width=5, bd=0, relief=tk.FLAT)
        self.entUpdate.place(x=200, y=230)
        self.entUpdate.delete(0, 'end')
        self.entUpdate.insert(0, str(self.UpdateSecs))
        self.btAccept = tk.Button(self.properties, text=" Accept ", command=self.EntryChange)
        self.btAccept.place(x=350, y=250)
    def EntryChange(self):
        pass
    def Load(self,fileName):
        pass
    def Save(self,fileName):
        pass
    def Log(self,message):
        pass

# MIPS application main data object
class MIPS:
    def __init__(self, parent):
        self.Version = "MIPS, Version 0.1, July 17, 2020"
        self.master = parent
        self.master.geometry('800x650')
        self.master.resizable(0, 0)
        self.master.title(self.Version)
        self.Systems = []
        self.cp = Comms.Comm(self.master)
        # determine if application is a script file or frozen exe
        if getattr(sys, 'frozen', False):
            self.application_path = os.path.dirname(sys.executable)
        elif __file__:
            self.application_path = os.path.dirname(__file__)
        self.last_path = self.application_path
        if os.name == "posix": self.isPC = False
        else: self.isPC = True
        self.statusbar = tk.Label(self.master, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.statusbarMessage(" MIPS app initalizing...", 2000)
        self.properties = Properties(parent)
    def findMIPScp(self,MIPSname):
        for cp in self.Systems:
            if cp.MIPSname == MIPSname: return (cp)
        return None
    def statusbarMessage(self,message, ctime = 0):
        self.statusbar.configure(text=message)
        if ctime > 0: self.statusbar.after(ctime,self.clearStatusbar)
    def clearStatusbar(self):
        self.statusbar.configure(text="")

def main():

    def tabChangeCallBack(e):
        curTab = tabControl.tab(tabControl.select(), "text")
        if curTab == 'Terminal':
            menubar.entryconfig("Terminal", state="normal")
            # Terminal tab selected. If comm port is open start processing characters
            if mips.cp.isOpen:
                terminal.stopRequest = False
                root.after(100, terminal.commLoop)
        else:
            menubar.entryconfig("Terminal", state="disable")
            terminal.stopRequest = True
            terminal.RepeatCmd = ""
        if curTab == 'DCBias': dcbias.open()
        else: dcbias.close()
        if curTab == 'RF driver': rfdriver.open()
        else: rfdriver.close()
        if curTab == 'Digital IO': dio.open()
        else: dio.close()
        if curTab == 'Pulse Seq Generator': psg.open()
        else: psg.close()

    def selectTabName(tabcontrol, name):
        for i in tabcontrol.tabs():
            if tabcontrol.tab(i, "text") == name:
                tabcontrol.select(i)
                return

    # MIPS menus and menu callback function

    def DownloadCallBack():
        selectTabName(tabControl, 'Terminal')
        mips.master.update()
        Program.Download(terminal.mipsTerm, mips)

    def readfirmwareCallBack():
        selectTabName(tabControl, 'Terminal')
        mips.master.update()
        Program.saveMIPSfirmware(terminal.mipsTerm, mips)

    def bootflagCallBack():
        selectTabName(tabControl, 'Terminal')
        mips.master.update()
        Program.setBootloaderBootFlag(terminal.mipsTerm, mips)

    def donothing():
        gh = MIPSobjects.TextFileWindow("MIPS commands", mips.application_path + "/MIPScommands.txt")
        gh.show()

    def scriptingMenuSelect():
        scp = Scripting.Script(root, globals())
        scp.show()

    def sendMIPSfile():
        MsgBox = tk.messagebox.askquestion('Send MIPS file',  'This function will send the file you select on the local system ' + \
                                                              'to MIPS and save it on the SD card on the MIPS controller. ' + \
                                                              'You will need to define the MIPS filename and select the local file., Continue?'
                                                              ,icon='warning')
        if MsgBox == 'no': return
        localFile = filedialog.askopenfilename(parent = root, initialdir=mips.application_path, title="Select file to send to MIPS")
        if localFile == '': return
        fileName = simpledialog.askstring(title="MIPS file name", prompt="Enter the MIPS file name you wish to create:")
        if fileName == '': return
        mips.cp.PutMIPSfile(fileName,localFile)

    def getMIPSfile():
        MsgBox = tk.messagebox.askquestion('Read MIPS file',  'This function will read the file you select on thee MIPS SD card ' + \
                                                              'and save it on the local system. ' + \
                                                              'You will need to define the MIPS filename and select a local file, Continue?'
                                                              ,icon='warning')
        if MsgBox == 'no': return
        fileName = simpledialog.askstring(title="MIPS file name", prompt="Enter the MIPS file name you wish to retrieve:")
        if fileName == '': return
        localFile = filedialog.asksaveasfilename(parent = root, initialdir=mips.application_path, title="Select file for MIPS retrieved file")
        if localFile == '': return
        mips.cp.GetMIPSfile(fileName,localFile)

    def readEEPROM():
        MsgBox = tk.messagebox.askquestion('Read module EEPROM','This function will read the configuration EEPROM data on a MIPS ' + \
                                                                'module and save it to a file on the local system. You will need to define ' + \
                                                                'the MIPS filename and the MIPS module address information, Continue?'
                                                                ,icon='warning')
        if MsgBox == 'no': return
        addr = simpledialog.askstring(title="Module address", prompt="Enter the MIPS module board address in HEX:")
        if addr == '': return
        board = simpledialog.askstring(title="Module address", prompt="Enter the MIPS module board select, A or B:")
        if board == '' or ((board.upper() != 'A') and (board.upper() != 'B')): return
        localFile = filedialog.asksaveasfilename(parent = root,initialdir=mips.application_path, title="Select file for MIPS module retrieved EEPROM data",filetypes = (("Binary file","*.bin"),("all files","*.*")))
        if localFile == '': return
        mips.cp.GetEEPROM(localFile,board,int(addr,16))

    def writeEEPROM():
        MsgBox = tk.messagebox.askquestion('Write module EEPROM','This function will write the configuration EEPROM data on a MIPS ' + \
                                                                 'module using data from file on the local system. You will need to define ' + \
                                                                 'the MIPS filename and the MIPS module address information. ' + \
                                                                 'Sending invalid data could render the module inoperative, Continue?'
                                                                 ,icon='warning')
        if MsgBox == 'no': return
        addr = simpledialog.askstring(title="Module address", prompt="Enter the MIPS module board address in HEX:")
        if addr == '': return
        board = simpledialog.askstring(title="Module address", prompt="Enter the MIPS module board select, A or B:")
        if board == '' or ((board.upper() != 'A') and (board.upper() != 'B')): return
        localFile = filedialog.askopenfilename(parent = root,initialdir=mips.application_path, title="Select file for MIPS module EEPROM data to send",filetypes = (("Binary file","*.bin"),("all files","*.*")))
        if localFile == '': return
        mips.cp.PutEEPROM(localFile,board,int(addr,16))

    def readFLASH():
        MsgBox = tk.messagebox.askquestion('Read module FLASH',  'This function will read the configuration FLASH data on a MIPS ' + \
                                                                 'module and save the data to a file on the local system. ' + \
                                                                 'The modules processor must be connected to this app or communicating ' + \
                                                                 'through MIPS using the TWITALK capability, Continue?'
                                                                 ,icon='warning')
        if MsgBox == 'no': return
        localFile = filedialog.asksaveasfilename(initialdir=mips.application_path, title="Select file for MIPS module retrieved FLASH data",filetypes = (("Binary file","*.bin"),("all files","*.*")))
        if localFile == '': return
        mips.cp.GetFLASH(localFile)

    def writeFLASH():
        MsgBox = tk.messagebox.askquestion('Write module FLASH',  'This function will write the configuration FLASH data on a MIPS ' + \
                                                                  'module from a selected data file on the local system. ' + \
                                                                  'The modules processor must be connected to this app or communicating ' + \
                                                                  'through MIPS using the TWITALK capability. ' + \
                                                                  'Sending invalid data could render the module inoperative, Continue?'
                                                                  ,icon='warning')
        if MsgBox == 'no': return
        localFile = filedialog.askopenfilename(initialdir=mips.application_path, title="Select file to write to MIPS module FLASH",filetypes = (("Binary file","*.bin"),("all files","*.*")))
        if localFile == '': return
        mips.cp.PutFLASH(localFile)

    def uploadFW():
        addr = simpledialog.askstring(title='Upload module FW',  prompt = 'Module FLASH FW write function. This function will allow\n' + \
                                                                          'you to upload a file and place it in FLASH at the address\n' + \
                                                                          'you select. Proceed with caution, you can render your\n' + \
                                                                          'system inoperable by entering invalid information.\n' + \
                                                                          'ARB upload, enter FLASH address in hex or cancel:\n' + \
                                                                          '  mover.bin at c0000\n' + \
                                                                          '  arb.bin at d0000')
        if addr == None: return
        if addr == '': return
        localFile = filedialog.askopenfilename(initialdir=mips.application_path, title="Select FW file to write to MIPS module",filetypes = (("Binary file","*.bin"),("all files","*.*")))
        if localFile == None: return
        if localFile == '': return
        mips.cp.FLASHupload(int(addr,16), localFile)

    def jtag():
        MsgBox = tk.messagebox.askquestion('JTAG uploader',  'This function uploads a xsvf file to the Arduino JTAG interface. ' + \
                                                             'It is assumed this application is connected to a Arduino with ' + \
                                                             'JTAG interface. Continue?'
                                                             ,icon='warning')
        if MsgBox == 'no': return
        localFile = filedialog.askopenfilename(initialdir=mips.application_path, title="Select xsvf file to upload to JTAG interface",filetypes = (("xsvf file","*.xsvf"),("all files","*.*")))
        if localFile == None: return
        if localFile == '': return
        jtag = JTAG.Uploader(terminal, mips.cp, 2)
        jtag.upload_one_file(localFile)

    # Create the main dialog and the main mips data object
    root = tk.Tk()
    mips = MIPS(root)

    tabControl = ttk.Notebook(root)
    frmSystem = ttk.Frame(tabControl)
    frmTerminal = ttk.Frame(tabControl)
    frmDCbias = ttk.Frame(tabControl)
    frmDIO = ttk.Frame(tabControl)
    frmRFdriver = ttk.Frame(tabControl)
    frmPSG = ttk.Frame(tabControl)

    tabControl.add(frmSystem, text='System')
    tabControl.add(frmTerminal, text='Terminal')
    tabControl.add(frmDIO, text='Digital IO')
    tabControl.add(frmRFdriver, text='RF driver')
    tabControl.add(frmDCbias, text='DCBias')
    tabControl.add(frmPSG, text='Pulse Seq Generator')
    tabControl.pack(expand=1, fill="both")

    tabControl.bind("<<NotebookTabChanged>>", tabChangeCallBack)

    # Each tab has an object that controls the tab behavior.
    # Below we create all the tab objects.
    system = System.System(frmSystem, mips)
    terminal = Comms.Terminal(frmTerminal, mips.cp)
    dio = DIO.DIO(frmDIO, mips.cp.MIPSname, mips.cp)
    rfdriver = RFdriver.RFdriver(frmRFdriver, 2, mips.cp.MIPSname, mips.cp)
    dcbias = DCBias.DCBias(frmDCbias, 8, mips.cp.MIPSname, mips.cp)
    psg = PSG.PSG(frmPSG, mips)

    menubar = tk.Menu(root)
    filemenu = tk.Menu(menubar, tearoff=0)
    filemenu.add_command(label="Load", command=donothing)
    filemenu.add_command(label="Save", command=donothing)
    menubar.add_cascade(label="File", menu=filemenu)

    terminalmenu = tk.Menu(menubar, tearoff=0)
    terminalmenu.add_command(label="Clear", command=terminal.clear)
    terminalmenu.add_command(label="Message repeat", command=terminal.messageRepeat)
    terminalmenu.add_separator()
    terminalmenu.add_command(label="Get file from MIPS", command=getMIPSfile)
    terminalmenu.add_command(label="Send file to MIPS", command=sendMIPSfile)
    terminalmenu.add_separator()
    terminalmenu.add_command(label="Read EEPROM", command=readEEPROM)
    terminalmenu.add_command(label="Write EEPROM", command=writeEEPROM)
    terminalmenu.add_separator()
    terminalmenu.add_command(label="Read FLASH", command=readFLASH)
    terminalmenu.add_command(label="Write FLASH", command=writeFLASH)
    terminalmenu.add_command(label="FLASH FW upload", command=uploadFW)
    terminalmenu.add_separator()
    terminalmenu.add_command(label="JTAG", command=jtag)
    menubar.add_cascade(label="Terminal", menu=terminalmenu)
    menubar.entryconfig("Terminal", state = "disable")

    toolsmenu = tk.Menu(menubar, tearoff=0)
    toolsmenu.add_command(label="Program MIPS", command=DownloadCallBack)
    toolsmenu.add_command(label="Save current MIPS firmware", command=readfirmwareCallBack)
    toolsmenu.add_command(label="Set bootloaded boot flag", command=bootflagCallBack)
    toolsmenu.add_separator()
    toolsmenu.add_command(label="Load configuration", command=donothing)
    toolsmenu.add_separator()
    toolsmenu.add_command(label="Scripting", command=scriptingMenuSelect)
    menubar.add_cascade(label="Tools", menu=toolsmenu)

    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label="About MIPS", command=donothing)
    helpmenu.add_command(label="Properties", command=mips.properties.Show)
    helpmenu.add_command(label="Genral Help", command=donothing)
    helpmenu.add_command(label="MIPS commands", command=donothing)
    menubar.add_cascade(label="Help", menu=helpmenu)

    root.config(menu=menubar)

    # Startup the system!
    root.mainloop()

if __name__ == "__main__":
    main()
