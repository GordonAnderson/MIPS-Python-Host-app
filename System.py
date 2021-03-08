# system imports
from __future__ import absolute_import
import tkinter as tk
from tkinter import ttk

# this applications imports
import Comms

class System:
    def __init__(self, parent, mips):
        self.parent = parent
        self.mips = mips
        self.photo = tk.PhotoImage(file=mips.application_path + '/MIPS.png')
        self.mipsPIC = tk.Label(self.parent, image=self.photo, bg = "gray95")
        self.mipsPIC.image = self.photo
        self.mipsPIC.place(x=20, y=20)
        self.btConfigPort = ttk.Button(self.parent, text ="Configure port", command = self.mips.cp.settings)
        self.btConfigPort.place(x=70, y=200, width=200)
        tk.Label(self.parent, text="MIPS host name, for\nnetwork connected systems.", bg="gray92").place(x=70, y=230, width=190)
        self.comboNetwork = ttk.Combobox(self.parent, width=20)
        self.comboNetwork.place(x=70, y=280)
        self.btConnect = ttk.Button(self.parent, text ="Connect to MIPS", command = self.connect)
        self.btConnect.place(x=70, y=320, width=200)
        self.btFindandConnect = ttk.Button(self.parent, text ="Find MIPS and Connect", command = self.FindMIPSandConnect)
        self.btFindandConnect.place(x=70, y=360, width=200)
        self.btDisconnect = ttk.Button(self.parent, text ="Disconnect", command = self.disconnect)
        self.btDisconnect.place(x=70, y=400, width=200)
        tk.Label(self.parent, text="Multiple MIPS systems found\nand connected.\nSelect desired system.", bg="gray92").place(x=70, y=440, width=200)
        self.comboMIPSs = ttk.Combobox(self.parent, width=20)
        self.comboMIPSs.place(x=70, y=505)
        tk.Label(self.parent, text="MIPS Configuration:", bg="gray92").place(x=350, y=20)
        self.txtMIPSnotes = tk.Text( self.parent ,bg = "gray92", bd=0, highlightbackground="gray92")
        self.txtMIPSnotes.place(x=360, y=60, width = 370, height = 490)
        self.txtMIPSnotes.config(font=("", 14))
        self.DisconnectMessage()
    def connect(self):
        if self.mips.cp.isOpen: return
        self.mips.cp.open()
        if not self.mips.cp.isOpen: return
        self.mips.cp.statusbar = self.mips.statusbar
        self.mips.Systems.append(self.mips.cp)
        self.identifyMIPS(self.mips.cp)
    def disconnect(self):
        if len(self.mips.Systems) == 0:
            try:
                self.mips.cp.close()
            except:
                pass
        else:
            for cp in self.mips.Systems:
                cp.close()
        self.mips.Systems.clear()
        self.DisconnectMessage()
    def identifyMIPS(self,cp):
        self.txtMIPSnotes.config(state='normal')
        self.txtMIPSnotes.delete("1.0", 'end')
        while True:
            res = cp.SendMessage("ABOUT\n")
            if res.count('?') > 0: break
            self.txtMIPSnotes.insert("end", res)
            self.txtMIPSnotes.insert("end", '\n' + cp.getlines())
            res = cp.SendMessage("UUID\n")
            if res.count('?') > 0: break
            self.txtMIPSnotes.insert("end", '\n' + res)
            res = cp.SendMessage("UPTIME\n")
            if res.count('?') > 0: break
            self.txtMIPSnotes.insert("end", '\n\n' + res)
            res = cp.SendMessage("THREADS\n")
            if res.count('?') > 0: break
            self.txtMIPSnotes.insert("end", '\n\n' + res)
            self.txtMIPSnotes.insert("end", '\n' + cp.getlines())
            res = cp.SendMessage("CPUTEMP\n")
            if res.count('?') > 0: break
            self.txtMIPSnotes.insert("end", '\nCPU temp: ')
            self.txtMIPSnotes.insert("end", res)
            break
        self.txtMIPSnotes.config(state='disabled')
    def FindMIPSandConnect(self):
        if self.mips.cp == None or self.mips.cp.isOpen:
            return
        ports = self.mips.cp.findPorts()
        self.comboMIPSs.delete(0, tk.END)
        self.comboMIPSs['values'] = []
        self.mips.Systems.clear()
        for port in ports:
            self.mips.statusbarMessage('Trying port: ' + port)
            self.parent.update()
            cp = Comms.Comm(root)
            cp.port = port
            cp.open()
            if cp.isOpen:
                if cp.isMIPS():
                    self.mips.Systems.append(cp)
                    if len(self.comboMIPSs['values']) == 0:
                        self.comboMIPSs['values'] = (cp.MIPSname,)
                    else:
                        self.comboMIPSs['values'] += (cp.MIPSname,)
                if len(self.comboMIPSs['values']) > 0: self.comboMIPSs.current(0)
        self.mips.statusbarMessage('Number of MIPS system found: ' + str(len(self.comboMIPSs['values'])))
        cp = self.mips.findMIPScp(self.comboMIPSs.get())
        print(cp.MIPSname)
        if cp != None:
            self.identifyMIPS(cp)
            self.mips.cp = cp
        else:
            self.mips.cp = Comms.Comm(root)
        return
    def DisconnectMessage(self):
        self.txtMIPSnotes.config(state='normal')
        self.txtMIPSnotes.delete("1.0", 'end')
        self.txtMIPSnotes.insert("1.0" ,'\n\n\n')
        self.txtMIPSnotes.insert("4.0" ,'MIPS is currently not connected to this application.\n')
        self.txtMIPSnotes.insert("5.0" ,'Establish a connection using the following options:\n\n')
        self.txtMIPSnotes.insert("7.0" ,'1.) Manually select a MIPS system by selecting a serial\n')
        self.txtMIPSnotes.insert("8.0" ,'      port using the Configure port button to select port\n')
        self.txtMIPSnotes.insert("9.0" ,'      and parameters and then pressing the Connect to \n')
        self.txtMIPSnotes.insert("10.0",'      MIPS button. If a name is entered into the MIPS host\n')
        self.txtMIPSnotes.insert("11.0",'      name box then this displayed name will be used to\n')
        self.txtMIPSnotes.insert("12.0",'      make a network connection, leave this box blank to\n')
        self.txtMIPSnotes.insert("13.0",'      make a USB serial port connection.\n\n')
        self.txtMIPSnotes.insert("15.0",'2.) Press the Find MIPS and Connect button and this \n')
        self.txtMIPSnotes.insert("16.0",'      application will search for all connected MIPS\n')
        self.txtMIPSnotes.insert("17.0",'      systems and establish connections. If more that one\n')
        self.txtMIPSnotes.insert("18.0",'      system is found you will see a selection box that will\n')
        self.txtMIPSnotes.insert("19.0",'      allow you to toggle between MIPS systems.\n')
        self.txtMIPSnotes.insert("20.0",'      Additionally you can enter multiple network names\n')
        self.txtMIPSnotes.insert("21.0",'      for connected MIPS system and this application will\n')
        self.txtMIPSnotes.insert("22.0",'      connect to all the systems if found. Make sure the\n')
        self.txtMIPSnotes.insert("23.0",'      host name box is empty to use the USB serial ports.\n')
        self.txtMIPSnotes.config(state='disabled')
