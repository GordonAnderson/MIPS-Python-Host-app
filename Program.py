import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import os
import time

import Comms
import Command


# This function is called when the program MIPS menu option is called. The following steps are
# performed:
#   1.) Make sure MIPS is connected, if not exit
#   2.) Ask user for the input file name, this is the .bin file to program
#   3.) Tell the user what we are going to do and confirm
#   4.) Tell user to remove RF heads etc
#   5.) Start the bootloader by connecting at 1200 baud
#   6.) Start the download program
def Download(parent, mips):
    MsgBox = tk.messagebox.askquestion('Update MIPS firmware',  'This will erase the MIPS firmware and attemp to load a new version. ' + \
                                                                'Make sure you have a new MIPS binary file to load, it should have a .bin extension. ' + \
                                                                'The MIPS firmware will be erased so if your bin file is invalid or fails to program, ' + \
                                                                'MIPS will be rendered useless!, Continue?'
                                                                ,icon='warning')
    if MsgBox == 'no': return
    if mips.isPC: programmer = 'bossac.exe'
    else: programmer = 'bossac'
    programmer_path = os.path.join(mips.application_path, programmer)
    filename = filedialog.askopenfilename(initialdir=mips.application_path, title="Select file to program",
                                               filetypes=(("bin files", "*.bin"), ("all files", "*.*")))
    if(filename == ""): return
    tk.messagebox.showwarning('Update MIPS firmware', 'Unplug any RF drive heads from MIPS before you proceed. This includes unplugging the FAIMS RF deck as well. ' + \
                                                   'It is assumed that you have already established communications with the MIPS system. ' + \
                                                   'If the connection is not establised this function will exit with no action.'
                                                   ,icon='warning')
    # Make sure MIPS is connected
    if not mips.cp.isOpen:
        tk.messagebox.showerror('Update MIPS firmware',
                               'This application must be connected to a MIPS box to program its FLASH!'
                                ,icon='warning')
        return
    # Init the bootloader, connect at 1200 baud, send a char and then disconnect
    mips.cp.close()
    mips.parent.update()
    time.sleep(1)
    savebaudrate = mips.cp.baudrate
    mips.cp.baudrate = 1200
    mips.parent.update()
    time.sleep(2)
    mips.cp.open()
    mips.parent.update()
    mips.cp.SendString("\n")
    mips.parent.update()
    time.sleep(1)
    mips.cp.close()
    parent.insert(tk.END, "MIPS bootloader enabled!\n")
    mips.parent.update()
    time.sleep(2)
    mips.parent.update()
    # Program the flash
    cd = Command.Command(parent,[programmer_path, '-e', '-w', '-v', '-b', filename, '-R'])
    cd.process()
    while cd.running: mips.parent.update()
    mips.cp.baudrate = savebaudrate
    time.sleep(2)
    mips.parent.update()
    mips.cp.open()

def saveMIPSfirmware(parent, mips):
    MsgBox = tk.messagebox.askquestion('Save MIPS firmware',  'This will read the current MIPS firmware and save to a file. ' + \
                                                                'You should save to a file with the .bin extension and indicate the current version. ' + \
                                                                'Are you sure you want to contine?'
                                                                ,icon='warning')
    if MsgBox == 'no': return
    if mips.isPC: programmer = 'bossac.exe'
    else: programmer = 'bossac'
    programmer_path = os.path.join(mips.application_path, programmer)
    filename = filedialog.asksaveasfilename(initialdir=mips.application_path, title="Select file to save program",
                                               filetypes=(("bin files", "*.bin"), ("all files", "*.*")))
    if(filename == ""): return
    tk.messagebox.showwarning('Save MIPS firmware', 'Unplug any RF drive heads from MIPS before you proceed. This includes unplugging the FAIMS RF deck as well. ' + \
                                                   'It is assumed that you have already established communications with the MIPS system. ' + \
                                                   'If the connection is not establised this function will exit with no action.'
                                                   ,icon='warning')
    # Make sure MIPS is connected
    if not mips.cp.isOpen:
        tk.messagebox.showerror('Save MIPS firmware',
                               'This application must be connected to a MIPS box to program its FLASH!'
                                ,icon='warning')
        return
    mips.cp.close()
    mips.parent.update()
    time.sleep(1)
    cd = Command.Command(parent,[programmer_path, '-r', '-b', filename, '-R'])
    cd.process()
    while cd.running: mips.parent.update()
    time.sleep(2)
    mips.parent.update()
    mips.cp.open()


def setBootloaderBootFlag(parent, mips):
    MsgBox = tk.messagebox.askquestion('Set MIPS boot flag',  'This function will attemp to set the bootloader boot flag in the MIPS system. ' + \
                                                                'This function is provided as part of an error recovery process and should not normally be necessary. ' + \
                                                                'If the boot flag is set on an erased DUE the results are unpredictable, Continue?'
                                                                ,icon='warning')
    if MsgBox == 'no': return
    if mips.isPC: programmer = 'bossac.exe'
    else: programmer = 'bossac'
    programmer_path = os.path.join(mips.application_path, programmer)
    tk.messagebox.showwarning('Set MIPS boot flag', 'Unplug any RF drive heads from MIPS before you proceed. This includes unplugging the FAIMS RF deck as well. ' + \
                                                   'It is assumed that you have already established communications with the MIPS system. ' + \
                                                   'If the connection is not establised this function will exit with no action.'
                                                   ,icon='warning')
    # Make sure MIPS is connected
    if not mips.cp.isOpen:
        tk.messagebox.showerror('Set MIPS boot flag',
                               'This application must be connected to a MIPS box to set boot flag in FLASH!'
                                ,icon='warning')
        return
    mips.cp.close()
    mips.parent.update()
    time.sleep(1)
    cd = Command.Command(parent,[programmer_path, '-b' '-R'])
    cd.process()
    while cd.running: mips.parent.update()
    time.sleep(2)
    mips.parent.update()
    mips.cp.open()
