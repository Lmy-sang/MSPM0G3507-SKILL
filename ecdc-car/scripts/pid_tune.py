 #!/usr/bin/env python3
 """
 PID 参数整定辅助工具
 
 通过串口接收 MSPM0G3507 发送的编码器 RPM 数据 (CSV 格式),
 实时绘制速度阶跃响应曲线, 辅助判断 PID 参数是否合适。
 
 MCU 端需在 10ms 定时中断中通过 printf 输出:
   printf("RPM,%.2f,%.2f,%d,%d\\r\\n", MA_RPM, MB_RPM, PWMA, PWMB);
 
 用法:
   python pid_tune.py COM3 115200
 """
 
 import sys
 import time
 import argparse
 from collections import deque
 
 try:
     import serial
 except ImportError:
     print("需要 pyserial: pip install pyserial")
     sys.exit(1)
 
 try:
     import matplotlib.pyplot as plt
     import matplotlib.animation as animation
     HAS_MPL = True
 except ImportError:
     HAS_MPL = False
     print("警告: matplotlib 未安装, 仅记录 CSV 到文件, 不显示图表")
     print("安装: pip install matplotlib")
 
 
 class PIDTuner:
     def __init__(self, port, baud=115200, window=500):
         self.ser = serial.Serial(port, baud, timeout=0.1)
         self.window = window
         self.times = deque(maxlen=window)
         self.rpm_a = deque(maxlen=window)
         self.rpm_b = deque(maxlen=window)
         self.pwm_a = deque(maxlen=window)
         self.pwm_b = deque(maxlen=window)
         self.start_time = time.time()
         self.data = []  # CSV 存储
 
     def read_line(self):
         try:
             line = self.ser.readline().decode('ascii', errors='ignore').strip()
             return line
         except Exception:
             return None
 
     def parse_line(self, line):
         if not line.startswith("RPM,"):
             return None
         try:
             parts = line.split(",")
             if len(parts) >= 5:
                 return [float(parts[1]), float(parts[2]),
                         int(parts[3]), int(parts[4])]
         except ValueError:
             pass
         return None
 
     def update(self, frame):
         for _ in range(10):
             line = self.read_line()
             if line:
                 result = self.parse_line(line)
                 if result:
                     t = time.time() - self.start_time
                     self.times.append(t)
                     self.rpm_a.append(result[0])
                     self.rpm_b.append(result[1])
                     self.pwm_a.append(result[2])
                     self.pwm_b.append(result[3])
                     self.data.append(f"{t:.3f},{result[0]:.1f},{result[1]:.1f},"
                                      f"{result[2]},{result[3]}")
                     print(f"\rMA={result[0]:6.1f} MB={result[1]:6.1f} "
                           f"PWM_A={result[2]:+5d} PWM_B={result[3]:+5d}", end="")
 
        rd
         self.ax_rpm.plot(list(self.times), list(self.rpm_a), 'r-', label='MotorA', linewidth=0.8)
         self.ax_rpm.plot(list(self.times), list(self.rpm_b), 'b-', label='MotorB', linewidth=0.8)
         self.ax_rpm.set_ylabel("RPM")
         self.ax_rpm.legend(loc='upper right')
         self.ax_rpm.grid(True, alpha=0.3)
 
         self.ax_pwm.clear()
         self.ax_pwm.plot(list(self.times), list(self.pwm_a), 'r-', label='PWM_A', linewidth=0.8)
         self.ax_pwm.plot(list(self.times), list(self.pwm_b), 'b-', label='PWM_B', linewidth=0.8)
         self.ax_pwm.set_xlabel("Time (s)")
         self.ax_pwm.set_ylabel("PWM")
         self.ax_pwm.legend(loc='upper right')
         self.ax_pwm.grid(True, alpha=0.3)
 
     def run_gui(self):
         self.fig, (self.ax_rpm, self.ax_pwm) = plt.subplots(2, 1, figsize=(10, 6))
         self.fig.canvas.manager.set_window_title("PID Tuner - Motor Speed Response")
         ani = animation.FuncAnimation(self.fig, self.update, interval=50, cache_frame_data=False)
         plt.tight_layout()
         plt.show()
 
     def run_csv(self, duration=0):
         print(f"录制 CSV 数据到 pid_data.csv (按 Ctrl+C 停止)...")
         out_file = open("pid_data.csv", "w")
         out_file.write("time,MA_RPM,MB_RPM,PWMA,PWMB\n")
         try:
             t_end = time.time() + duration if duration > 0 else float('inf')
             while time.time() < t_end:
                 line = self.read_line()
                 if line:
                     result = self.parse_line(line)
                     if result:
                         t = time.time() - self.start_time
                         csv_line = f"{t:.3f},{result[0]:.1f},{result[1]:.1f},{result[2]},{result[3]}"
                         out_file.write(csv_line + "\n")
                         out_file.flush()
                         print(f"\r{t:.1f}s MA={result[0]:6.1f} MB={result[1]:6.1f}", end="")
         except KeyboardInterrupt:
             pass
         finally:
             out_file.close()
             print(f"\n数据已保存到 pid_data.csv ({len(open('pid_data.csv').readlines())-1} 行)")
 
     def close(self):
         self.ser.close()
 
 
 def main():
     parser = argparse.ArgumentParser(description="PID 参数整定辅助工具")
     parser.add_argument("port", help="串口号 (例: COM3)")
     parser.add_argument("baud", nargs="?", type=int, default=115200, help="波特率 (默认 115200)")
     parser.add_argument("--csv", action="store_true", help="仅录制 CSV, 不显示图表")
     parser.add_argument("--duration", type=int, default=0, help="CSV 录制时长 (秒, 0=无限)")
     parser.add_argument("--window", type=int, default=500, help="图表窗口大小 (点数, 默认 500)")
     args = parser.parse_args()
 
     tuner = PIDTuner(args.port, args.baud, args.window)
     try:
         if args.csv or not HAS_MPL:
             tuner.run_csv(args.duration)
         else:
             tuner.run_gui()
     finally:
         tuner.close()
 
 
 if __name__ == "__main__":
     main()
 
 """
 MCU 端代码模板 (加到 empty.c 的 while(1) 或 TIMER_ISR 中):
 
   // 在 10ms 定时中断中:
   printf("RPM,%.2f,%.2f,%d,%d\\r\\n", MA_RPM, MB_RPM, PWMA, PWMB);
 
 调参方法:
   1. 烧录 PID 程序到 MCU
   2. 运行: python pid_tune.py COM3
   3. 图表窗口打开后, 通过 BLS 按键启动电机
   4. 观察 RPM 阶跃响应曲线
   5. 判断: 上升时间 < 200ms, 超调量 < 10%, 稳态误差 < 5%
   6. 若不满足, 在 MCU 代码中修改 Velcity_Kp/Velcity_Ki, 重新烧录
 """
