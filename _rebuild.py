import os
base = r"D:\Downloads\diansai\代码\电赛skill\skills\ecdc-car"
for d in ["agents","references","scripts","assets/keil-empty/keil"]:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# Write SKILL.md
with open(os.path.join(base, "SKILL.md"), "w", encoding="utf-8", newline="\n") as f:
    f.write("""---
name: ecdc-car
description: 电子设计竞赛控制题小车开发技能。适用于 TI MSPM0G3507 + 轮趣 C07A 核心板 + S28A 底板 + TB6612 电机驱动 + 亚博 K230 视觉 + ZDT Modbus 步进 + MPU6050/HC-SR04/HC-05/HJ-DXJ8 八路灰度循线。基于 Keil MDK + SysConfig + TI DriverLib。当用户需要进行电赛小车底盘控制、电机 PID、K230 视觉通信、巡线控制、步进电机云台驱动、传感器读取、赛题方案设计时使用。
---

# ECDC-Car 电赛控制题小车技能

使用 MSPM0G3507 + 轮趣 C07A 核心板 + S28A 底板的差速二驱小车开发。

## 硬件平台

- MCU: TI MSPM0G3507 (Cortex-M0+, 80MHz, 128KB Flash, 32KB SRAM)
- 核心板: 轮趣 WHEELTEC C07A V1.0/V1.1
- 底板: S28A（与 S27F 内部走线相同，丝印不同）
- 底盘: 差速二驱, TB6612 D153C 双路驱动带稳压版
- IDE: Keil MDK v5.42
- SDK: mspm0_sdk_2_04_00_06, SysConfig 1.23.1
- 编程: TI DriverLib (DL_* API), 裸机 (nortos)

完整引脚映射见 [硬件参考](references/hardware.md)。

## 新建工程模板

assets/keil-empty/ 是预配好的 Keil 空工程模板(SDK 2.04.00.06, SysConfig 1.23.1)。初始化新工程时复制到目标目录, 编写代码后在 SysConfig 修改引脚。

## 软件架构: BSP / Module / App

- BSP: SysConfig生成的ti_msp_dl_config.c/h + board.c/h, 换硬件时修改
- Module: 电机PI、K230协议、PID、传感器驱动, 极少改动
- App: 赛题状态机、模式切换、策略, 换题主要修改此层

## 模块速查

| 需求 | 读取文件 | 内容 |
|------|---------|------|
| 引脚分配 | references/hardware.md | S28A 完整引脚表 + 互斥约束 |
| DriverLib API | references/driverlib.md | GPIO/Timer/UART/ADC/I2C/SysTick |
| 电机控制 | references/motor-control.md | TB6612 + 编码器 + 增量式 PI |
| K230 视觉 | references/k230-comm.md | ASCII $...# 协议 + 17种ID |
| ZDT 步进 | references/stepper-zdt.md | Modbus RTU + CRC16 |
| 传感器 | references/sensors.md | HC-05/MPU6050/SR04/CD4051灰度 |
| 软件架构 | references/architecture.md | BSP/Module/App + Keil结构 |
| 赛题策略 | references/competition-topics.md | 历年赛题 + 现场策略 |
| PID 调参 | scripts/pid_tune.py | 串口RPM + matplotlib实时曲线 |
""")
print("SKILL.md done")

# Write openai.yaml
with open(os.path.join(base, "agents/openai.yaml"), "w", encoding="utf-8", newline="\n") as f:
    f.write("""interface:
  display_name: "电赛小车控制"
  short_description: "电子设计竞赛 MSPM0G3507+C07A 差速小车控制"
  default_prompt: "帮我根据比赛题目搭建小车控制代码"
""")
print("openai.yaml done")

# Write hardware.md
with open(os.path.join(base, "references/hardware.md"), "w", encoding="utf-8", newline="\n") as f:
    f.write("""# 硬件参考: MSPM0G3507 + C07A + S28A

## 平台总览

| 组件 | 型号 | 备注 |
|------|------|------|
| MCU | TI MSPM0G3507 | Cortex-M0+, 80MHz, 128KB/32KB |
| 核心板 | 轮趣 WHEELTEC C07A | V1.0 / V1.1 |
| 底板 | S28A（与 S27F 内部走线相同，丝印不同） | S28A 丝印不直接对应芯片引脚 |
| 底盘 | 差速二驱 | TB6612 D153C 双路驱动带稳压版 |
| 编码器 | 霍尔编码器 | 13线, 2倍频=26, 30:1减速比 |
| 电源 | RT9013-33GB | 5V->3.3V LDO |
| USB-UART | CH9102 | USART1, Type-C |

> **S28A 丝印注意事项**: S28A 底板丝印标签（PG1-4, PD1-8, PS, SW1/2 等）与 C07A 芯片引脚不直接对应。接线时必须对照 C07A搭配S28A底板引脚对应关系.pdf 找到实际 MSPM0G3507 引脚。S28A 与 S27F 内部走线完全相同，仅丝印不同。

## 引脚映射

### 系统
| 功能 | 引脚 | 外设 |
|------|------|------|
| LED | PB9 | GPIO |
| BLS 按键 | PA18 | GPIO |
| USB-UART | PA10,PA11 | USART1 |
| SWD | PA19,PA20 | SWD 不可复用 |
| OLED | PA28,PA31,PB14,PB15 | GPIO |

### 电机控制
| 功能 | 引脚 | 外设 |
|------|------|------|
| MotorA 编码器 A/B | PA25,PA26 | GPIO 中断 |
| MotorA 方向 IN1/IN2 | PA13,PA14 | GPIO |
| MotorA PWM | PB2 | TIMG6_C0 |
| MotorB 编码器 A/B | PB20,PB24 | GPIO 中断 |
| MotorB 方向 IN1/IN2 | PA17,PA16 | GPIO |
| MotorB PWM | PB3 | TIMG6_C1 |

### 传感器与通信
| 功能 | 型号 | 引脚 | 外设 |
|------|------|------|------|
| 陀螺仪 | MPU6050 | PA0,SDA PA1,SCL | I2C addr 0x68 |
| 陀螺仪 INT | MPU6050 | PA7 | GPIO DMP 200Hz |
| 蓝牙 | HC-05 | PB6,TX PB7,RX | UART1 |
| 超声波 | HC-SR04 | PA24,Trig PA9,Echo | GPIO |
| 电池检测 | - | PA15 | ADC1 1/11分压 |
| 步进电机 | ZDT Emm42_V5.0 | 独立UART | Modbus RTU |
| 八路灰度 | HJ-DXJ8 | PA12,AD0 PA27,AD1 PB16,AD2 PB17,OUT | GPIO->CD4051 |
| CCD巡线 | - | PA22,PA9,PA27 | ADC0 |

## 互斥约束

| 约束 | 冲突外设 | 共享引脚 |
|------|---------|---------|
| 超声波 vs 雷达 | HC-SR04 <-> 雷达 | PA24 |
| 超声波 vs CCD | HC-SR04 <-> CCD | PA9 |
| CCD vs 红外巡线 | CCD <-> 灰度模块 | PA27 |

## 禁用引脚

| 引脚 | 原因 |
|------|------|
| PA2~PA6 | 时钟引脚 (ROSC/LFXIN/HFXIN) |
| PA19,PA20 | SWD 调试接口 |

## 编码器参数

| 参数 | 值 |
|------|-----|
| 编码器线数 | 13 |
| 倍频系数 | 2 (上升沿) |
| 每转脉冲数 | 26 |
| 减速比 | 30:1 |
| RPM 公式 | count*60000/(26*sample_ms)/30 |

## TB6612 控制真值表

| PWM | IN1 | IN2 | 功能 |
|-----|-----|-----|------|
| 1 | 0 | 1 | 正转 |
| 1 | 1 | 0 | 反转 |
| 1 | 0 | 0 | 制动停止 |
| 1 | 1 | 1 | 制动停止 |
| 0 | X | X | 停止 |

PWM 推荐 10kHz。STBY 已在 D153C 模块上接 3.3V, 无需 MCU 控制。

## 电源系统

- 电机电源 VM: 7-12V
- 逻辑电源 VCC: 5V (模块稳压输出)
- MCU 电源: 3.3V (RT9013-33GB LDO)
- 电池检测: 1/11 分压, ADC1 读取 PA15
- 电池电压: V = ADC_val/4096 * 3.3V * 11
""")
print("hardware.md done")
print("All 3 core files written successfully")