import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import os
import string
import sys
import time
import serial

class Uploader:
    def __init__(self, parent, cp, debug):
        self.p = parent
        self.cp = cp
        self.debug = debug
        # Close MIPS serial port and open for jtag
        cp.master.update()
        time.sleep(1)
        # Create a translation array of printable characters
        global _printable_chars
        _printable_chars = string.digits + string.ascii_letters + string.punctuation + ' '
        self._translate_str = ''.join([(chr(x) in _printable_chars) and chr(x) or '.' for x in range(256)])
        # Help printing new lines
        self._need_lf = False
        #
        self._file_size = 0
        # Hashes
        self._sum = 0
        # To compute the elapsed time
        self._start_time = 0
        # Error code
        self._error_code = 0
    def error_code(self):
        return self._error_code
    def error_code(self, value):
        self._error_code = value
    def reset_arduino(self):
        """Resets the arduino and clear any garbage on the serial port."""
        #self._serial.setDTR(False)
        #time.sleep(1)
        self.cp.cp.flushInput()
        self.cp.cp.flushOutput()
        #self._serial.setDTR(True)
        self._start_time = 0
    def print_lf(self):
        if self._need_lf:
            self._need_lf = False
            self.p.print
    def initialize_hashes(self):
        self._sum = 0
    def update_hashes(self, s):
        for c in s:
            self._sum += c
    def print_hashes(self):
        cksum = (-self._sum) & 0xFF
        if self.debug > 1:
            self.p.print('  Expected checksum:  0x%02X/%lu.' % (cksum, self._file_size))
            self.p.print('  Expected sum: 0x%08lX/%lu.' % (self._sum, self._file_size))
        if self._start_time > 0:
            self.p.print('Elapsed time: %.02f seconds.' % \
                  (time.time() - self._start_time))
    def upload_one_file(self, filename):
        self.reset_arduino()
        self.p.print(filename)
        fd = open(filename, "rb")
        self._file_size = os.fstat(fd.fileno()).st_size
        bytes_written = 0
        self.cp.cp.write(bytearray("JTAG\n".encode()))
        self.cp.cp.timeout = 2.0
        self.cp.cp.write_timeout = 2.0
        while True:
            line = self.cp.cp.readline().strip()
            if not line:
                continue
            command = line[0]
            argument = line[1:]
            if chr(command) == 'S':
                num_bytes = int(argument)
                xsvf_data = fd.read(num_bytes)
                bytes_written += len(xsvf_data)
                self.update_hashes(xsvf_data)
                try:
                    self.cp.cp.write(xsvf_data)
                    self.cp.cp.write(0xff * (num_bytes - len(xsvf_data)))
                except:
                    continue
                    #return self.error_code == 0
                if self.debug > 1:
                    self.p.print('\rSent: %8d bytes, %8d remaining' % \
                          (bytes_written, self._file_size - bytes_written),
                    sys.stdout.flush())
                    self._need_lf = True
            elif chr(command) == 'R':
                self.initialize_hashes()
                if self.debug > 1:
                    self.p.print('File: %s' % os.path.realpath(fd.name))
                    self.p.print('Ready to send %d bytes.' % self._file_size)
                self._start_time = time.time()
            elif chr(command) == 'Q':
                self.print_lf()
                # Split the argument. The first field is the error code,
                # the next field is the error message.
                args = argument.decode('utf-8').split(',')
                self.error_code = int(args[0])
                if self.debug > 1:
                    self.p.print('Quit: {1:s} ({0:d}).'.format(
                        self.error_code, args[1]))
                self.print_hashes()
                return self.error_code == 0
            elif chr(command) == 'D':
                if self.debug > 0:
                    self.print_lf()
                    self.p.print('Device:', argument.decode('utf-8'))
            elif chr(command) == '!':
                if self.debug > 0:
                    self.print_lf()
                    self.p.print('IMPORTANT:', argument.decode('utf-8'))
            else:
                self.print_lf()
                self.p.print('Unrecognized line:',\
                    line.translate(self._translate_str.encode()))
    def upload_all_files(self, fd_list):
        ok = True
        for fd in fd_list:
            with fd:
                ok = self.upload_one_file(fd)
                if not ok:
                    break
        return ok
