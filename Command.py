import subprocess
import threading

class Command:
    def __init__(self, parent, cmd):
        self.parent = parent
        self.cmd = cmd
        self.dspstr = ""
        self.indx = "1.0"
        self.running = False
    def process(self):
        try:
            self.parent.insert("end", "starting: " + ' '.join(self.cmd) + "\n")
            self.indx = str(self.parent.index('end-1c linestart'))
            self.ph = subprocess.Popen(self.cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            self.running = True
        except Exception as e:
            self.parent.insert("end", "Failed to start: " + str(e) + "\n")
            return
        # Start threads to process stdout and stderr streams
        self.thstdout = threading.Thread(target=self.stdoutThread, args=("stdout",))
        self.thstdout.start()
        self.thstderr = threading.Thread(target=self.stderrThread, args=("stderr",))
        self.thstderr.start()
    def stdoutThread(self,name):
        self.ProcessChars_stdout(self.ph.stdout)
        if not self.thstderr.is_alive(): self.running = False
    def stderrThread(self,name):
        self.ProcessChars_stdout(self.ph.stderr)
        if not self.thstdout.is_alive(): self.running = False
    def ProcessChars_stdout(self,pipe):
        while True:
            b = pipe.read(1)
            if b.decode() == "\r":
                b += pipe.read(1)
            if len(b) > 0:
                if (b.decode() == "\n") or (b.decode() == "\r\n"):
                    self.parent.delete(self.indx, "end")
                    self.parent.insert("end", "\n")
                    self.parent.insert("end", self.dspstr + "\n")
                    self.indx = str(self.parent.index('end-1c linestart'))
                    self.dspstr = ""
                else:
                    if b.decode()[0] == "\r":
                        self.parent.delete(self.indx, "end-1c")
                        self.parent.insert('end-1c linestart', self.dspstr)
                        if len(b)>1: self.dspstr=b.decode()[1:]
                        else: self.dspstr = ""
                    else:
                        self.dspstr += b.decode()
            else: break


