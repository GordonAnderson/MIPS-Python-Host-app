import tkinter as tk
from tkinter import ttk
import time
from time import sleep
from tkinter import simpledialog
import serial
import io
import os

class RingBuffer:
    def __init__(self, size):
        self.size = size
        self.head = 0
        self.tail = 0
        self.count = 0
        self.lines = 0
        self.buffer = [None] * size
    def getch(self):
        if self.count == 0: return 0
        c = self.buffer[self.tail]
        self.tail += 1
        if self.tail >= self.size: self.tail = 0
        self.count -= 1
        if c == '\n': self.lines -= 1
        return c
    def putch(self, c):
        if c == chr(0x06): return self.count
        if c == chr(0x15): return self.count
        if c == '\r': return self.count
        if c == '\n': self.lines += 1
        self.buffer[self.head] = c
        self.head += 1
        if self.head >= self.size: self.head = 0
        self.count += 1
        return self.count
    def clear(self):
        self.head = 0
        self.tail = 0
        self.count = 0
        self.lines = 0
    def numChars(self):
        return self.count
    def available(self):
        return self.size-self.count
    def numLines(self):
        return self.lines
    def getline(self):
        str = ""
        if self.lines <= 0: return str
        while True:
            c = self.getch()
            if c == '\n': break
            if self.count <= 0: break
            str += c
        return str

class Comm:
    def __init__(self, parent):
        self.master = parent
        self.isOpen = False
        self.isError = False
        self.ErrorMessage = ""
        self.statusbar = None
        self.stopbits = 1
        self.bytesize = 8
        self.baudrate = 115200
        self.flowcontrol = "None"
        self.port = ""
        self.parity = 'N'
        self.rb = RingBuffer(10000)
        self.cp = None
        self.blkSize = 128
        self.MIPSname = 'MIPS'
    def update(self):
        # walks back to root or just fails to update!
        master = self.master
        while True:
            try:
                master.update()
                return
            except: pass
            try: master = master.master
            except: return
    def __statusbarMessage(self,message):
        if self.statusbar != None:
            self.statusbar.configure(text=message)
    def open(self):
        xonxoff = False
        rtscts = False
        if self.flowcontrol == "RTS/CTS": rtscts = True
        if self.flowcontrol == "XON/XOFF": xonxoff = True
        try:
            self.cp = serial.Serial(self.port,self.baudrate,self.bytesize,self.parity,self.stopbits,None,xonxoff,rtscts,None,False,None,None)
            self.isError = False
            self.isOpen = True
            # Get MIPS name
            res = self.SendMessage("GNAME\n")
            if res.count('?') == 0: self.MIPSname = res
            self.__statusbarMessage("Connected: " + self.port)
        except Exception as e:
            self.isError = True
            self.isOpen = False
            self.ErrorMessage = e
            if (self.statusbar != None): self.statusbar.configure(text=e)
    def close(self):
        if self.cp == None:
            self.__statusbarMessage('Nothing to disconnect!')
            return
        if self.cp.isOpen():
            self.cp.close()
        else:
            self.__statusbarMessage(self.port + ' all ready disconnected!')
            return
        while self.cp.isOpen():
            self.master().update()
        self.isOpen = False
        self.__statusbarMessage('Disconnected: ' + self.port)
    def findPorts(self):
        from serial.tools.list_ports import comports
        ports = []
        for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
            ports.append(port)
        return ports
    def ProcessSerial(self):
        if(self.isOpen == False): return
        while True:
            if self.cp.inWaiting() > 0:
                c = self.cp.read(1)
                self.rb.putch(chr(int.from_bytes(c,byteorder='big')))
            else:
                break
    def SendString(self, message):
        if(self.isOpen == False): return
        try:
            self.cp.flush()
            self.cp.write(message.encode('utf-8'))
            self.isError = False
        except Exception as e:
            self.isError = True
            self.ErrorMessage = e
            if (self.statusbar != None): self.statusbar.configure(text=e)
            self.__statusbarMessage('Error sending string!')
    def waitforline(self,timeout):
        if(self.isOpen == False): return True
        if timeout == 0:
            while True:
                self.ProcessSerial()
                if self.rb.lines > 0: break
            return True
        startT = time.monotonic()
        while (startT + timeout) > time.monotonic():
            self.ProcessSerial()
            if self.rb.lines > 0: return True
        return False
    def getlines(self):
        res = ""
        while self.waitforline(0.5):
            res += self.rb.getline() + "\n"
        return res
    def SendMessage(self,message):
        if (self.isOpen == False): return
        for i in range(0,1):
            self.SendString(message)
            if len(message) > 100: self.waitforline(3)
            else: self.waitforline(1)
            if self.rb.numLines() >= 1:
                return self.rb.getline()
        self.__statusbarMessage(message.replace('\n' , ' ') + ' :Timeout')
        return '?\n'
    def SendCommand(self, message):
        if (self.isOpen == False): return
        for i in range(0,1):
            self.SendString(message)
            if len(message) > 100: self.waitforline(3)
            else: self.waitforline(1)
            if self.rb.numLines() >= 1:
                res = self.rb.getline()
                if res == "": return True
                if res == "?":
                    return False
        self.__statusbarMessage(message.replace('\n', ' ') + ' :Timeout')
        return False
    def isMIPS(self):
        if not self.isOpen: return False
        res = self.SendMessage("GVER\n")
        if res.count("Version") > 0: return True
        return False
    def CalculateCRC(self, binarydata):
        generator = 0x1D
        crc = 0x00
        for b in binarydata:
            crc ^= int(b)
            for i in range(0,8):
                if (crc & 0x80) != 0: crc = (((crc << 1) & 0xFF) ^ int(generator))
                else:
                    crc <<= 1
                    crc &= 0xFF
        return crc
    def GetMIPSfile(self,MIPSfile, LocalFile):
        self.__statusbarMessage("Reading file from MIPS...")
        self.update()
        if self.SendCommand("GET," + MIPSfile + "\n"):
            self.waitforline(0.5)
            FileSize = self.rb.getline()
            FileData = ""
            for i in range(0,int(FileSize),1024):
                length = 1024
                self.waitforline(0.5)
                if int(FileSize) < 1024: length = int(FileSize)
                for j in range(0, length*2):
                    c = self.rb.getch()
                    if c == "\n": break;
                    FileData += c
                if (int(FileSize) - i) > 1024: self.SendString("Next\n")
            if len(FileData) != (2 * int(FileSize)):
                self.__statusbarMessage("File size read error!")
                return
            self.waitforline(0.5)
            FileCRC = self.rb.getline()
            if FileCRC == "":               #not sure why??
                self.waitforline(0.5)
                FileCRC = self.rb.getline().strip('\n')
            FileDataBinary = bytes.fromhex(FileData)
            if self.CalculateCRC(FileDataBinary) != int(FileCRC):
                self.__statusbarMessage("CRC error!")
                return
            # here with a valid file in FileDataBinary, save it to a file on this machine
            newFile = open(LocalFile, "wb")
            newFile.write(FileDataBinary)
            newFile.close()
            self.__statusbarMessage(LocalFile + " downloaded from MIPS")
            return
        self.__statusbarMessage("MIPS did not accept command!")
    def PutMIPSfile(self, MIPSfile, LocalFile):
        newFile = open(LocalFile, "rb")
        FileDataBinary = newFile.read()
        FileData = FileDataBinary.hex()
        newFile.close()
        self.__statusbarMessage("Sending file to MIPS...")
        self.update()
        self.SendCommand("PUT," + MIPSfile + "," + str(len(FileDataBinary)) + "\n")
        sleep(0.1)
        for i in range(0, len(FileData), 1024):
            flen = 1024
            if (len(FileData)-i) < 1024: flen = len(FileData)-i
            # Send data block in chunks
            for k in range(0,flen,self.blkSize):
                if flen >= (k+self.blkSize): self.SendString(FileData[i+k:i+k+self.blkSize])
                else: self.SendString(FileData[i+k:i+k+flen])
                sleep(0.05)
            if (flen == 1024) and ((len(FileData)-i) != 1024):
                if not self.waitforline(1.0):
                    print("timeout")
                    self.__statusbarMessage("Timeout, waiting for signal from MIPS!")
                else: self.rb.getline()
        sleep(0.1)
        self.SendString("\n")
        self.SendString(str(self.CalculateCRC(FileDataBinary)) + "\n")
        self.__statusbarMessage(LocalFile + " uploaded to MIPS")
    def GetEEPROM(self, fileName, board, addr):
        self.update()
        # Send the command to MIPS to get the EEPROM
        if self.SendCommand("GETEEPROM," + board + "," + '{:x}'.format(addr) + '\n'):
            # Now process the data in the ring buffer
            # First read the length
            self.waitforline(0.5)
            fileSize = self.rb.getline()
            # Read the hex data stream
            self.waitforline(1.0)
            fileData = self.rb.getline()
            if len(fileData) != 2 * int(fileSize):
                # Here if file data block is not the proper size
                self.__statusbarMessage("Data block size not correct!")
                return
            # Read the CRC
            self.waitforline(0.5)
            fileCRC = self.rb.getline()
            # Convert data to byte array and calculate CRC
            FileDataBinary = bytes.fromhex(fileData)
            if self.CalculateCRC(FileDataBinary) == int(fileCRC):
                # Now save the data to the user selected file
                newFile = open(fileName, "wb")
                newFile.write(FileDataBinary)
                newFile.close()
                self.__statusbarMessage("EEPROM from MIPS read and saved successfully!")
            else:
                self.__statusbarMessage("CRC error!")
    def PutEEPROM(self, fileName, board, addr):
        self.update()
        # Send the command to MIPS to send EEPROM data
        if self.SendCommand("PUTEEPROM," + board + "," + '{:x}'.format(addr) + '\n'):
            # open the local file to send and read the data
            newFile = open(fileName, "rb")
            FileDataBinary = newFile.read()
            FileData = FileDataBinary.hex()
            newFile.close()
            # Send file size
            self.SendString(str(len(FileDataBinary)) + '\n')
            # send hex data
            flen = len(FileData)
            for k in range(0,flen,self.blkSize):
                if flen >= (k+self.blkSize): self.SendString(FileData[k:k+self.blkSize])
                else: self.SendString(FileData[k:k+flen])
                sleep(0.05)
            self.SendString('\n')
            # Send CRC
            self.SendString(str(self.CalculateCRC(FileDataBinary)) + '\n')
            self.__statusbarMessage("MIPS module's EEPROM Written!")
    def GetFLASH(self, fileName):
        self.update()
        if self.SendCommand("GETFLASH\n"):
            # Now process the data in the ring buffer
            # First read the length
            self.waitforline(0.5)
            fileSize = self.rb.getline()
            # Read the hex data stream
            self.waitforline(1.0)
            fileData = self.rb.getline()
            if len(fileData) != 2 * int(fileSize):
                # Here if file data block is not the proper size
                self.__statusbarMessage("Data block size not correct!")
                return
            # Read the CRC
            self.waitforline(0.5)
            fileCRC = self.rb.getline()
            # Convert data to byte array and calculate CRC
            FileDataBinary = bytes.fromhex(fileData)
            if self.CalculateCRC(FileDataBinary) == int(fileCRC):
                # Now save the data to the user selected file
                newFile = open(fileName, "wb")
                newFile.write(FileDataBinary)
                newFile.close()
                self.__statusbarMessage("FLASH from module read and saved successfully!")
            else:
                self.__statusbarMessage("CRC error!")
    def PutFLASH(self, fileName):
        self.update()
        if self.SendCommand("PUTFLASH\n"):
            # open the local file to send and read the data
            newFile = open(fileName, "rb")
            FileDataBinary = newFile.read()
            FileData = FileDataBinary.hex()
            newFile.close()
            # Send file size
            flen = len(FileData)
            for k in range(0,flen,self.blkSize):
                if flen >= (k+self.blkSize): self.SendString(FileData[k:k+self.blkSize])
                else: self.SendString(FileData[k:k+flen])
                sleep(0.05)
            self.SendString('\n')
            # send hex data
            self.SendString(FileData + '\n')
            # Send CRC
            self.SendString(str(self.CalculateCRC(FileDataBinary)) + '\n')
            self.__statusbarMessage("Module FLASH Written!")
    def FLASHupload(self, faddress, fileName, cmd = 'ARBPGM'):
        # open the local file to send and read the data
        newFile = open(fileName, "rb")
        FileDataBinary = newFile.read()
        FileData = FileDataBinary.hex()
        newFile.close()
        self.update()
        # Send the data to MIPS module
        if self.SendCommand(cmd + "," + format(faddress, 'x') + "," + str(len(FileDataBinary)) + "\n"):
            for i in range(0, len(FileData), 512):
                length = 512
                if (len(FileData) - i) < 512: length = len(FileData) - i
                # Send this in chunks in case the sender is a lot faster than MIPS
                for k in range(0, length, 128):
                    if length > (k + 128): self.SendString(FileData[i+k : i+k+128])
                    else: self.SendString(FileData[i+k : i+length])
                    sleep(0.010)
                if length == 512:
                    self.waitforline(0.5)
                    if self.rb.getline() == "":
                        # Here if we timed out, display error and exit
                        self.__statusbarMessage("Timedout waiting for data from module!")
                        return
            self.SendString('\n')
            self.SendString(str(self.CalculateCRC(FileDataBinary)) + '\n')
            self.__statusbarMessage("File uploaded to Module FLASH!")
    def settings(self):
        def applyCallBack():
            self.baudrate = int(BaudRate.get())
            self.stopbits = int(StopBits.get())
            self.bytesize = int(DataBits.get())
            self.parity = Parity.get()[0]
            self.flowcontrol = FlowControl.get()
            self.port=portsel.get()
            settings.destroy()
            settings.quit()
        def portselCallback(event):
            from serial.tools.list_ports import comports
            for p in comports():
                if p.device == portsel.get():
                    self.desc.configure(text="")
                    self.manf.configure(text="")
                    self.sn.configure(text="")
                    self.loc.configure(text="")
                    self.vid.configure(text="")
                    self.pid.configure(text="")
                    self.desc.configure(text=p.description)
                    self.manf.configure(text=p.manufacturer)
                    self.sn.configure(text=p.serial_number)
                    self.loc.configure(text=p.location)
                    self.vid.configure(text=p.vid)
                    self.pid.configure(text=p.pid)
                    break
        settings = tk.Toplevel()
        settings.config(bg="gray98")
        settings.geometry('670x350')
        settings.title("Settings")
        ssp = tk.LabelFrame(settings, text="Select Serial Port", width=400, height=180, bg="gray95", bd=0)
        ssp.place(x=10, y=10)
        portsel = ttk.Combobox(ssp, width=40, textvariable=12)
        portsel['values'] = self.findPorts()
        #portsel['values'] += ('12',)
        portsel.bind("<<ComboboxSelected>>", portselCallback)
        portsel.set(self.port)
        portsel.place(x=10, y=5)
        portsel.current()
        tk.Label(ssp, text="Description:", bg="gray95").place(x=10, y=30)
        self.desc = tk.Label(ssp, text="", bg="gray95")
        self.desc.place(x=130, y=30)
        tk.Label(ssp, text="Manufacture:", bg="gray95").place(x=10, y=50)
        self.manf = tk.Label(ssp, text="", bg="gray95")
        self.manf.place(x=130, y=50)
        tk.Label(ssp, text="Serial number:", bg="gray95").place(x=10, y=70)
        self.sn = tk.Label(ssp, text="", bg="gray95")
        self.sn.place(x=130, y=70)
        tk.Label(ssp, text="Location:", bg="gray95").place(x=10, y=90)
        self.loc = tk.Label(ssp, text="", bg="gray95")
        self.loc.place(x=130, y=90)
        tk.Label(ssp, text="Vendor identifier:", bg="gray95").place(x=10, y=110)
        self.vid = tk.Label(ssp, text="", bg="gray95")
        self.vid.place(x=130, y=110)
        tk.Label(ssp, text="Product identifier:", bg="gray95").place(x=10, y=130)
        self.pid = tk.Label(ssp, text="", bg="gray95")
        self.pid.place(x=130, y=130)

        sp = tk.LabelFrame(settings, text="Select Parameters", width=220, height=180, bg="gray95", bd=0)
        sp.place(x=430, y=10)
        tk.Label(sp, text="BaudRate:", bg="gray95").place(x=10, y=10)
        tk.Label(sp, text="Data bits:", bg="gray95").place(x=10, y=40)
        tk.Label(sp, text="Parity:", bg="gray95").place(x=10, y=70)
        tk.Label(sp, text="Stop bits:", bg="gray95").place(x=10, y=100)
        tk.Label(sp, text="Flow control:", bg="gray95").place(x=10, y=130)
        BaudRate = ttk.Combobox(sp, width=10)
        BaudRate.place(x=100, y=10)
        BaudRate['values'] = (9600, 19200, 38400, 115200)
        BaudRate.set(self.baudrate)
        DataBits = ttk.Combobox(sp, width=10)
        DataBits.place(x=100, y=40)
        DataBits['values'] = (5, 6, 7, 8)
        DataBits.set(self.bytesize)
        Parity = ttk.Combobox(sp, width=10)
        Parity.place(x=100, y=70)
        Parity['values'] = ("None", "Even", "Odd", "Mark", "Space")
        Parity.set(self.parity)
        if self.parity == 'E': Parity.set("Even")
        if self.parity == 'O': Parity.set("Odd")
        if self.parity == 'M': Parity.set("Mark")
        if self.parity == 'S': Parity.set("Space")
        StopBits = ttk.Combobox(sp, width=10)
        StopBits.place(x=100, y=100)
        StopBits['values'] = (1, 2)
        StopBits.set(self.stopbits)
        FlowControl = ttk.Combobox(sp, width=10)
        FlowControl.place(x=100, y=130)
        FlowControl['values'] = ("None", "RTS/CTS", "XON/XOFF")
        FlowControl.set(self.flowcontrol)
        apply = tk.Button(settings, text=" Apply ", command=applyCallBack)
        apply.place(x=600, y=250)
        portselCallback(None)
        settings.mainloop()

class Terminal:
    def __init__(self, parent, cp):
        self.parent = parent
        self.cp = cp
        self.RepeatCmd = ""
        self.stopRequest = False
        self.scrollmips = tk.Scrollbar(self.parent)
        self.scrollmips.pack(side=tk.RIGHT, fill=tk.Y)
        self.mipsTerm = tk.Text(self.parent, bg="gray95")
        self.mipsTerm.pack(fill="both", expand=True)
        self.mipsTerm.bind("<Key>", self.key_pressed)
        self.mipsTerm.bind("<<Paste>>", self.key_paste)
        self.mipsTerm.bind("<Command-c>", self.key_copy)
        self.scrollmips.config(command=self.mipsTerm.yview)
        self.mipsTerm['yscrollcommand'] = self.scrollmips.set
    def print(self, *args, **kwargs):
        output = io.StringIO()
        print(*args, file=output, **kwargs)
        contents = output.getvalue()
        output.close()
        self.mipsTerm.insert(tk.END, contents)
    def key_pressed(self,event):
        if(event.char == ""): return
        self.cp.SendString(event.char)
    def key_paste(self,event):
        lines = self.mipsTerm.clipboard_get()
        for c in lines:
            self.cp.SendString(c)
    def key_copy(self,event):
        pass
    def clear(self):
        self.mipsTerm.delete("1.0", "end")
    def repeatLoop(self):
        if self.RepeatCmd == "": return
        if self.RepeatCmd == None: return
        if not self.cp.isOpen: return
        #if tabControl.tab(tabControl.select(), "text") != 'Terminal': return
        self.cp.SendString(self.RepeatCmd + "\n")
        self.parent.after(1000, self.repeatLoop)
    def messageRepeat(self):
        self.RepeatCmd=""
        self.repeatLoop()
        self.RepeatCmd = simpledialog.askstring(title="Repeat command", prompt="Enter the command to repeat:")
        self.parent.after(1000, self.repeatLoop)
    def commLoop(self):
        if self.stopRequest:
            self.stopRequest = False
            return
        self.cp.ProcessSerial()
        if self.cp.rb.numChars() > 0:
            while self.cp.rb.numChars() > 0:
                c=self.cp.rb.getch()
                self.mipsTerm.insert(tk.END,c)
            self.mipsTerm.see('end')
        if self.cp.isOpen:
            self.parent.after(100, self.commLoop)
