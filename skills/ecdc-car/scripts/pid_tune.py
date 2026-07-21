#!/usr/bin/env python3
"""PID Tuning Tool - reads RPM CSV from MCU serial, plots real-time response."""
import sys, time, argparse, serial
from collections import deque
try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

class PIDTuner:
    def __init__(self, port, baud=115200, window=500):
        self.ser = serial.Serial(port, baud, timeout=0.1)
        self.window = window
        self.times = deque(maxlen=window)
        self.rpm_a = deque(maxlen=window); self.rpm_b = deque(maxlen=window)
        self.pwm_a = deque(maxlen=window); self.pwm_b = deque(maxlen=window)
        self.start_time = time.time()

    def read_line(self):
        try: return self.ser.readline().decode().strip()
        except: return None

    def parse(self, line):
        if not line or not line.startswith("RPM,"): return None
        try:
            p = line.split(",")
            if len(p) >= 5: return [float(p[1]),float(p[2]),int(p[3]),int(p[4])]
        except: pass
        return None

    def update(self, frame):
        for _ in range(10):
            r = self.parse(self.read_line() or "")
            if r:
                t = time.time() - self.start_time
                self.times.append(t); self.rpm_a.append(r[0]); self.rpm_b.append(r[1])
                self.pwm_a.append(r[2]); self.pwm_b.append(r[3])
        self.ax_rpm.clear(); self.ax_pwm.clear()
        self.ax_rpm.plot(list(self.times),list(self.rpm_a),"r-",lw=0.8,label="MA")
        self.ax_rpm.plot(list(self.times),list(self.rpm_b),"b-",lw=0.8,label="MB")
        self.ax_rpm.legend(); self.ax_rpm.grid(True,alpha=0.3)
        self.ax_pwm.plot(list(self.times),list(self.pwm_a),"r-",lw=0.8)
        self.ax_pwm.plot(list(self.times),list(self.pwm_b),"b-",lw=0.8)

    def run_gui(self):
        self.fig,(self.ax_rpm,self.ax_pwm)=plt.subplots(2,1,figsize=(10,6))
        self.fig.canvas.manager.set_window_title("PID Tuner")
        ani = animation.FuncAnimation(self.fig,self.update,interval=50,cache_frame_data=False)
        plt.tight_layout(); plt.show()

    def run_csv(self, duration=0):
        print("Recording to pid_data.csv (Ctrl+C to stop)...")
        with open("pid_data.csv","w") as f:
            f.write("time,MA_RPM,MB_RPM,PWMA,PWMB\n")
            try:
                t_end = time.time() + (duration if duration > 0 else 1e9)
                while time.time() < t_end:
                    r = self.parse(self.read_line() or "")
                    if r: f.write(f"{time.time()-self.start_time:.3f},{r[0]:.1f},{r[1]:.1f},{r[2]},{r[3]}\n"); f.flush()
            except KeyboardInterrupt: pass

    def close(self): self.ser.close()

def main():
    p = argparse.ArgumentParser(description="PID Tuning Tool")
    p.add_argument("port", help="COM port")
    p.add_argument("baud", nargs="?", type=int, default=115200)
    p.add_argument("--csv", action="store_true")
    p.add_argument("--duration", type=int, default=0)
    p.add_argument("--window", type=int, default=500)
    args = p.parse_args()
    tuner = PIDTuner(args.port, args.baud, args.window)
    try:
        if args.csv or not HAS_MPL: tuner.run_csv(args.duration)
        else: tuner.run_gui()
    finally: tuner.close()

if __name__ == "__main__": main()
