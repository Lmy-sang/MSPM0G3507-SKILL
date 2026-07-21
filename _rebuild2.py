import os
base = r"D:\Downloads\diansai\代码\电赛skill\skills\ecdc-car"

files = {}

files["references/driverlib.md"] = """# TI DriverLib API 参考
SDK: mspm0_sdk_2_04_00_06, SysConfig 1.23.1, Keil MDK v5.42

## 入口
main() { SYSCFG_DL_init(); ... while(1){} }
SYSCFG_DL_init() 由 SysConfig 根据 .syscfg 生成。

## GPIO
DL_GPIO_setPins(port,pin) / DL_GPIO_clearPins / DL_GPIO_readPins / DL_GPIO_togglePins
DL_GPIO_getEnabledInterruptStatus(port,pin) / DL_GPIO_clearInterruptStatus
引脚宏来自 ti_msp_dl_config.h

## Timer/PWM
DL_Timer_startCounter(PWM_0_INST) / DL_TimerA_startCounter(TIMER_0_INST)
DL_Timer_setCaptureCompareValue(INST, val, CH_IDX)
DL_TimerA_getPendingInterrupt / DL_TIMER_IIDX_ZERO
PWM 频率由 SysConfig 设置, 推荐 10kHz

## UART
DL_UART_Main_transmitData(UART_0_INST, ch) / DL_UART_isBusy
DL_UART_Main_receiveData(UART_1_INST) / DL_UART_getPendingInterrupt
DL_UART_IIDX_RX

## SysTick
DL_SYSTICK_config(CPUCLK_FREQ/1000); CPUCLK_FREQ=80000000
delay_ms(ms) / delay_us(us) 在 board.c 实现

## 中断
NVIC_EnableIRQ / NVIC_ClearPendingIRQ
GROUP1_IRQHandler 处理 GPIO 中断

## printf 重定向
int fputc(int ch, FILE *stream) {
    while(DL_UART_isBusy(UART_0_INST));
    DL_UART_Main_transmitData(UART_0_INST, ch);
    return ch;
}
"""

files["references/motor-control.md"] = """# 电机控制: TB6612 + 编码器 + PI 速度闭环

## 硬件
MotorA: PA13/PA14=Dir, PB2=PWMA(TIMG6_C0), Enc=PA25/PA26
MotorB: PA17/PA16=Dir, PB3=PWMB(TIMG6_C1), Enc=PB20/PB24
STBY 已在 D153C 模块接 3.3V, 无需 MCU 控制

## Set_PWM()
void Set_PWM(int pwmA, int pwmB) {
    // A: pwmA>0->正转(AIN2=1,AIN1=0), pwmA<0->反转
    if(pwmA>0){DL_GPIO_setPins(AIN_PORT,AIN_AIN2_PIN);DL_GPIO_clearPins(AIN_PORT,AIN_AIN1_PIN);}
    else     {DL_GPIO_setPins(AIN_PORT,AIN_AIN1_PIN);DL_GPIO_clearPins(AIN_PORT,AIN_AIN2_PIN);}
    DL_Timer_setCaptureCompareValue(PWM_0_INST,ABS(pwmA),GPIO_PWM_0_C0_IDX);
    // B 同理...
}

## 编码器 GROUP1_IRQHandler (2倍频)
if(irq1 & ENCODERA_E1A_PIN)
    Get_Encoder_countA += DL_GPIO_readPins(ENCODERA_PORT,ENCODERA_E1B)?1:-1;
else if(irq1 & ENCODERA_E1B_PIN)
    Get_Encoder_countA += DL_GPIO_readPins(ENCODERA_PORT,ENCODERA_E1A)?-1:1;
// 最后 DL_GPIO_clearInterruptStatus(...)

## RPM 计算
float Calculate_Motor_RPM(int count, int ms) {
    return (float)count * 60000.0f / (26 * ms) / 30;
}  // 13线*2倍频=26, 30:1减速比

## 增量式 PI (Kp=2.6, Ki=1.3, PWM限幅 +-7000)
int Velocity_A(int target, int current) {
    int bias = target - current;
    static int control, last;
    control += Ki*(bias-last) + Kp*bias;
    last = bias;
    if(control>7000) control=7000; if(control<-7000) control=-7000;
    return control;
}

## 10ms 定时闭环
void TIMER_0_INST_IRQHandler(void) {
    if(DL_TimerA_getPendingInterrupt(TIMER_0_INST) && DL_TIMER_IIDX_ZERO) {
        MA_RPM = Calculate_Motor_RPM(Get_Encoder_countA, 10);
        MB_RPM = Calculate_Motor_RPM(-Get_Encoder_countB, 10);
        Get_Encoder_countA = Get_Encoder_countB = 0;
        if(!Flag_Stop) {
            PWMA=-Velocity_A(TARGET,MA_RPM); PWMB=-Velocity_B(TARGET,MB_RPM);
            Set_PWM(limit_PWM(PWMA,-7999,7999), limit_PWM(PWMB,-7999,7999));
        } else Set_PWM(0,0);
    }
}
"""

files["references/k230-comm.md"] = """# K230 视觉通信: ASCII 文本协议
与轮趣 K210 二进制协议(0xCC/0xDD)完全不同。

## 物理层
UART 115200 8N1, K230 和 MSPM0G 必须共地

## 协议格式
$[长度],[例程ID],[数据1],...,[数据N],#
$: 帧头 #: 帧尾 后附换行符

## 接收解析
void UART_1_INST_IRQHandler(void) {
    if(DL_UART_getPendingInterrupt(UART_1_INST)==DL_UART_IIDX_RX) {
        uint8_t ch=DL_UART_Main_receiveData(UART_1_INST);
        if(ch=='${dollar}') k230_idx=0;
        k230_buf[k230_idx++]=ch;
        if(ch=='#') k230_frame_ready=1;
    }
}

## 常用例程 ID
01:颜色(x,y,w,h) 03:二维码(x,y,w,h,msg) 13:OCR(msg) 14:YOLO(x,y,w,h,msg) 15:目标跟踪(x,y,w,h)

## K230 侧开发
固件: CanMV_K230 v1.6+ IDE: CanMV IDE 4.0.7
LAB 校准必须在现场灯光下重新做
陷阱: Timer(-1), PWM(2,50), pin.value(1/0), f-string不支持
""".replace('${dollar}', '$')

files["references/stepper-zdt.md"] = """# ZDT 张大头步进: Modbus RTU 闭环
Emm_V5.0 总线型智能闭环步进, 内置 FOC+PID

## 接线
UART TTL 直连 MCU, 115200 8N1, 独立 12-24V 供电
S28A 底板舵机口 PA8 是 TIMG0 PWM, 步进走 UART 需另选引脚

## Modbus RTU 帧
[Addr(01H)] [Func] [Data] [CRC16_Lo] [CRC16_Hi]

## 关键指令
Enable:   01 10 00 F3 00 02 04 AB 01 00 00 CRC16
速度模式: 01 10 00 F6 00 03 06 [dir] [acc] [rpm] [sync] 00 CRC16
位置(相对): 01 10 00 FD 00 05 0A [dir] [acc] [rpm] [pulse] 00 [sync] CRC16
停止:     01 10 00 FE 00 01 02 [sync] CRC16
读转速:   01 04 00 35 00 02 CRC16
读位置:   01 04 00 36 00 03 CRC16
清零:     01 06 00 0A 00 01 CRC16
校准:     01 06 00 06 00 01 CRC16

## 字段
dir:0=CW 1=CCW acc:0-255 rpm:0-3000 pulse:16细分3200=1圈
角度=位置*360/65536

## CRC16
uint16_t crc=0xFFFF;
for(i=0;i<len;i++){crc^=data[i]; for(j=0;j<8;j++) crc=(crc&1)?(crc>>1)^0xA001:(crc>>1);}
先发低字节后高字节

## 流程
上电等2s->使能->确认->速度/位置指令->循环读状态
"""

files["references/sensors.md"] = """# 传感器模块

## HC-05 蓝牙
UART1 (PB6=TX, PB7=RX), 3.3V, 9600, 配对后透明传输

## MPU6050 陀螺仪
I2C (PA0=SDA, PA1=SCL), addr 0x68, INT=PA7 DMP 200Hz
MPU6050_initialize(); DMP_Init();
NVIC_EnableIRQ(GPIO_MULTIPLE_GPIOA_INT_IRQN);
DMP 读取在 GROUP1_IRQHandler 中, 与编码器中断共享

## HC-SR04 超声波
PA24=Trig, PA9=Echo
1. Trig 10us高脉冲 2. 等Echo变高计时 3. distance=time_us*0.017
互斥: 不能与CCD(PA9)或雷达(PA24)同时使用

## HJ-DXJ8 八路灰度 (CD4051)
4 GPIO: PA12=AD0(X3), PA27=AD1(X2), PB16=AD2(X1), PB17=OUT(X4)
CD4051: AD2,AD1,AD0=000->CH1(X1)...111->CH8(X8)
读取: for(ch=0;ch<8;ch++){ setAD0/1/2; delay_us(100); results[ch]=readOUT; }
巡线: weights[]={-35,-25,-15,-5,5,15,25,35}; err=sum(weights[i]*active[i])/count
Set_PWM(base+err*KP, base-err*KP) // KP=0.1
白底ACTIVE=0 黑底ACTIVE=1 最佳高度18mm 互斥:不能与CCD(PA27)同时用
"""

files["references/architecture.md"] = """# 软件架构: BSP / Module / App

## 三层
App(任务逻辑): 赛题状态机/模式切换/策略, 换题改此层
Module(功能模块): 电机PI/K230协议/PID/传感器驱动, 极少改动
BSP(硬件抽象): GPIO/PWM/ADC/UART/I2C SysConfig生成, 换硬件时改

## Keil 工程结构
empty.c(main) + empty.syscfg(SysConfig) + ti_msp_dl_config.c/h(生成,不手改)
board.c/h(BSP:SysTick,delay,printf) + Hardware/(Module:motor/encoder/K210...)
ti/(DriverLib) + *.uvprojx(Keil工程)

## main() 模板
SYSCFG_DL_init(); DL_Timer_startCounter(PWM_0_INST);
NVIC_EnableIRQ(ENCODERA_INT_IRQN); // ...
while(1){ switch(g_mode){ case MODE_LINE: LineTask(); } }

## 编码规范
函数: Set_PWM/ReadEightIR 全局: Flag_Stop/MA_RPM 局部: bias/i
每.c配.h #ifndef防护 宏大写 ISR不耗时只置标志+数据
"""

files["references/competition-topics.md"] = """# 电赛赛题分析

## 历年赛题
2021F:智能送药小车(巡线+码盘+NFC)
2022C:小车跟随(PID+超声波/视觉)
2024H:自动行驶小车(巡线+色块/码+定点)
2025C:单目视觉测量(K230+A4靶标)
2025E:简易瞄准(激光+伺服+视觉)

## 高频考点
巡线:灰度+CCD+PID 色块/码:K230+UART 定点:编码器+位置闭环
超声波:脉冲测距 双车:蓝牙通信

## 赛前检查
所有传感器跑通 编码器方向确认 备用电池 K230固件+LAB校准
每模块独立备份 3套PID预设(快速/均衡/稳定) 带串口助手/USB-TTL/万用表

## 选题策略
选硬件匹配度最高的题 优先有成熟代码的(巡线/色块/测距) 避开需新采购的模块

## 现场节奏
1h:选题+引脚 2-4h:基础框架 5-12h:算法调优 13-20h:完整流程 最后4h:固化+电池+展示

## 常见问题
电机不转:PWM+方向+电池 巡线跑偏:PID+高度+光线 K230无数据:共地+波特率
编码器不准:中断优先级+噪声 小车抖:PID增益过大+机械松动
"""

files["scripts/pid_tune.py"] = '''#!/usr/bin/env python3
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
            f.write("time,MA_RPM,MB_RPM,PWMA,PWMB\\n")
            try:
                t_end = time.time() + (duration if duration > 0 else 1e9)
                while time.time() < t_end:
                    r = self.parse(self.read_line() or "")
                    if r: f.write(f"{time.time()-self.start_time:.3f},{r[0]:.1f},{r[1]:.1f},{r[2]},{r[3]}\\n"); f.flush()
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
'''

for path, content in files.items():
    full_path = os.path.join(base, path)
    with open(full_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"Wrote {path}")

print(f"\nAll {len(files)} reference/script files written")