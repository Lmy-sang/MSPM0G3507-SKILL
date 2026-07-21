# MSPM0G3507 电赛智能小车开发套件

> 基于 TI MSPM0G3507 (Cortex-M0+) + 嘉楠 K230 (RISC-V) 双芯架构的电赛控制类题目全栈开发方案。覆盖底盘运动控制、IMU 姿态解算、视觉追踪、蓝牙调参、步进云台等完整功能链，所有代码均基于轮趣 C07A 核心板 + S27F 底板实机验证。

[![MCU](https://img.shields.io/badge/MCU-MSPM0G3507-blue)](https://www.ti.com/product/MSPM0G3507)
[![SDK](https://img.shields.io/badge/SDK-mspm0__sdk__2__04__00__06-green)](https://www.ti.com/tool/MSPM0-SDK)
[![IDE](https://img.shields.io/badge/IDE-Keil%20MDK%20v5.42-orange)](https://www.keil.com/)
[![K230](https://img.shields.io/badge/CoPro-K230__YAHBOOM-purple)](https://developer.canaan-creative.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

> ---

## 系统架构图

```text
┌─────────────────── K230 视觉端 (MicroPython) ───────────────────┐
│                                                                  │
│  GC2093 摄像头 -> LAB 色块识别 -> UART (115200 8N1) -> MSPM0G   │
│  (CSI 2)           (找色块)       ASCII $...# 帧协议             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────── MSPM0G3507 主控端 (C) ───────────────────────┐
│                                                                  │
│  MPU6050(I2C) + 编码器(GPIO中断) + TB6612(TIMG6 PWM) + 步进电机(ZDT Modbus) │
│                                     │                             │
│              ┌──────────────────────┘                             │
│              ▼                                                    │
│  PID 级联控制器: 速度PI(内环) + 巡线/追踪PID(外环)                  │
│              │                                                    │
│              ▼                                                    │
│  SSD1306 OLED(I2C) + HC-05蓝牙(UART) + printf调试(UART0)          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 目录

- [先看你怎么用](#先看你怎么用)
- [硬件平台详解](#硬件平台详解)
- [引脚分配速查](#引脚分配速查)
- [工程目录详解](#工程目录详解)
- [开发环境搭建](#开发环境搭建)
- [烧录方法](#烧录方法)
- [调试技巧](#调试技巧)
- [常见问题排查](#常见问题排查)
- [电赛真题方案](#电赛真题方案)
- [依赖清单](#依赖清单)
- [License](#license)

---

## 工程架构规范: BSP / Module / App

所有 MSPM0G3507 Keil 工程必须遵循三层架构:

```
Project/
├── empty.c                   ← App: main() + 状态机 + 策略
├── empty.syscfg              ← SysConfig 引脚配置
├── ti_msp_dl_config.c/h      ← BSP: SysConfig 生成 (不可手改!)
├── board.c/h                 ← BSP: SysTick, delay, printf
├── Hardware/                 ← Module: 功能驱动
│   ├── motor.c/h             ← TB6612 PWM + PI 闭环
│   ├── encoder.c/h           ← 编码器中断 + RPM
│   ├── K210.c/h              ← K230 UART 协议解析
│   ├── key.c/h               ← BLS 按键
│   └── led.c/h               ← 用户 LED
├── ti/                       ← BSP: TI DriverLib (dl_*.c/h)
└── *.uvprojx                 ← Keil 工程文件
```

### 层间规则

- **App 只能调用 Module 接口**，不直接操作 BSP 寄存器
- **Module 调用 BSP** 的 DL_* DriverLib API
- **BSP 层**由 SysConfig 生成的 `ti_msp_dl_config.c/h` + 手写 `board.c/h` 组成，仅在更换硬件时修改
- **Module 层**极少改动，换题不需要改
- **App 层**集中了赛题状态机、模式切换、参数表——换题主要修改此层

### 编码规范

- 每个 `.c` 配 `.h`，`#ifndef` 防护
- 函数: `Set_PWM()`, `ReadEightIR()` 驼峰/下划线
- 全局变量: 首字母大写 (`Flag_Stop`, `MA_RPM`)
- 注释用中文简述函数功能和算法逻辑
- ISR 内不做耗时操作，只置标志位 + 关键数据读取

---

## 先看你怎么用

- **想用 AI 自动生成代码，不想记引脚和 API**：走 Skill 路线，用 Codex 加载 `skills/m0-skills/`
- **已经有电赛小车，想看现有代码怎么写**：直接看 `skills/m0-skills/references/` 下的各模块文档
- **想从零搭建电赛小车**：按硬件平台 → 基础外设 → 传感器 → 算法控制的顺序逐步构建
- **想基于 K230 做视觉追踪**：看 `references/k230-comm.md` + K230 例程代码

---

## 硬件平台详解

### MCU 对比

| 参数 | MSPM0G3507 | K230 嘉楠 |
|------|-----------|-------------|
| 架构 | Cortex-M0+ | RISC-V 双核 |
| 主频 | 32MHz(默认)/80MHz(PLL) | 1.6GHz(大核) |
| Flash | 128KB | -- |
| SRAM | 32KB | 512MB LPDDR4 |
| 开发语言 | C (TI Arm Clang) | MicroPython (CanMV) |
| 调试接口 | SWD (DAP) | USB 串口 REPL |
| OS | 裸机 (nortos) | RT-Smart |

### 外设清单

| 组件 | 型号 | 规格 | 接口 | 状态 |
|------|------|------|------|------|
| 核心板 | 轮趣 C07A V1.X | MSPM0G3507, CH9102 USB-UART | -- | 已验证 |
| 底板 | S27F | 与 S28A 内部走线相同 | -- | 已验证 |
| 电机驱动 | 轮趣 D153C | TB6612FNG 双路带稳压版, 12V, STBY 已接 3.3V | TIMG6 PWM | 已验证 |
| 编码电机 | 霍尔编码 | 13线, 2倍频=26, 30:1减速比 | GPIO 中断 | 已验证 |
| IMU | MPU6050 | 6轴, DMP 姿态解算 200Hz | I2C (PA0/PA1) | 已验证 |
| 显示 | SSD1306 | 0.96" 128x64 OLED | I2C (PA28/PA31) | 已验证 |
| 蓝牙 | HC-05 | BLE, 9600 baud | UART1 (PB6/PB7) | 已验证 |
| 超声波 | HC-SR04 | 2cm-400cm | GPIO (PA24/PA9) | 已验证 |
| 步进电机 | ZDT Emm42_V5.0 | Modbus RTU 闭环, FOC | UART | 已验证 |
| 灰度巡线 | HJ-DXJ8 | CD4051 8路数字输出 | GPIO (PA12/PA27/PB16/PB17) | 已验证 |
| 视觉 | 亚博 K230 | GC2093, CanMV v1.6+ | UART | 已验证 |
| 调试器 | DAP/CH9102 | SWD + 串口 | PA19/PA20 + PA10/PA11 | 已验证 |

---

## 引脚分配速查

> Skill 每次生成代码前会要求确认实际接线。

### 运动控制

| 功能 | 引脚 | 外设 | 备注 |
|------|------|------|------|
| 右轮 PWM | PB2 | TIMG6_C0 | TB6612 PWMA |
| 右轮方向 | PA13, PA14 | GPIO | AIN1/AIN2 |
| 左轮 PWM | PB3 | TIMG6_C1 | TB6612 PWMB |
| 左轮方向 | PA17, PA16 | GPIO | BIN1/BIN2 |
| 右编码器 | PA25, PA26 | GPIO 中断 | 2倍频 |
| 左编码器 | PB20, PB24 | GPIO 中断 | 2倍频 |
| 步进电机 (ZDT) | UART | Modbus RTU FOC | 云台 |

### 传感器与通信

| 功能 | 引脚 | 外设 | 备注 |
|------|------|------|------|
| MPU6050 | PA0, PA1 | I2C | 0x68, INT=PA7 |
| OLED | PA28, PA31, PB14, PB15 | GPIO | 0x3C |
| 蓝牙 | PB6, PB7 | UART1 | HC-05 |
| 超声波 | PA24, PA9 | GPIO | Trig/Echo |
| 灰度巡线 | PA12, PA27, PB16, PB17 | GPIO -> CD4051 | 8路 |
| 电池检测 | PA15 | ADC1 | 1/11 分压 |
| SWD | PA19, PA20 | -- | 保留 |

### 禁用引脚

| 引脚 | 原因 |
|------|------|
| PA2~PA6 | 时钟引脚 (ROSC/LFXIN/HFXIN) |
| PA19, PA20 | SWD 调试接口 |

---

## 工程目录详解

```
MSPM0G3507-SKILL/
├── README.md                          -> 项目总览（本文件）
├── LICENSE                            -> MIT 许可证
├── .agents/                           -> Codex 元数据
│
├── skills/                            -> Codex Skill 定义
│   └── m0-skills/
│       ├── SKILL.md                   -> Skill 入口 + 触发规则 + 模块速查表
│       ├── agents/openai.yaml         -> UI 元数据
│       ├── references/                -> 参考文档（按需加载）
│       │   ├── hardware.md            -> S27F 完整引脚映射 + 互斥约束
│       │   ├── driverlib.md           -> TI DriverLib API 速查
│       │   ├── motor-control.md       -> TB6612 + 编码器 + PI 速度闭环
│       │   ├── k230-comm.md           -> K230 ASCII 通信协议 ($...#)
│       │   ├── stepper-zdt.md         -> ZDT 步进 Modbus RTU 指令集
│       │   ├── sensors.md             -> HC-05 / MPU6050 / SR04 / CD4051 灰度
│       │   ├── architecture.md        -> BSP / Module / App 三层架构规范
│       │   └── competition-topics.md  -> 历年赛题 + 现场策略
│       ├── scripts/
│       │   └── pid_tune.py            -> PID 调参辅助工具
│       └── assets/                    -> 模板/资源文件
│
```

---

## 开发环境搭建

| 工具 | 下载地址 | 说明 |
|------|---------|------|
| Keil MDK | https://www.keil.com/ | v5.42 |
| MSPM0 SDK | https://www.ti.com/tool/MSPM0-SDK | mspm0_sdk_2_04_00_06 |
| SysConfig | TI 官方 | v1.23.1 |
| CanMV IDE | 亚博智能提供 | K230 开发 |

---

## 烧录方法

**使用 DAP/CH9102 串口烧录，禁用 STLINK（会锁芯片）！**

烧录步骤：
1. 按住 BSL 按键不松手
2. 按住 RST 按键约 1 秒后松开
3. 松开 BSL 按键，进入烧录模式
4. 10 秒内点击下载
5. 按 NRST 复位运行程序

---

## 调试技巧

- **OLED 多页显示**：关键变量直接打印在 OLED 上，比串口更快
- **printf 重定向**：UART0 -> 串口助手查看变量值
- **VOFA+ 波形**：编码器 RPM、PWM 输出等随时间变化的数据用 VOFA+ 显示
- **PID 调参工具**：`scripts/pid_tune.py` 接收 RPM CSV 数据并实时绘制阶跃响应曲线

---

## 常见问题排查

| 现象 | 原因 | 排查 |
|------|------|------|
| 电机不转 | PWM 未启动/方向错误/电池没电 | `DL_Timer_startCounter()`; 检查 TB6612 方向; 测电池电压 |
| 小车跑偏 | 左右速度差/机械不对称 | OLED 对比速度; 调 BALANCE_KP |
| OLED 不亮 | I2C 地址错/引脚错 | 确认 0x3C; 检查 PA28/PA31 |
| Yaw 漂移 | 电源噪声/DMP 未校准 | 静置 2 秒; 电池加电容滤波 |
| K230 无数据 | 未共地/波特率/帧格式 | 必须共地; 必须 115200 8N1 |
| 烧录失败 | SWD 松动/低功耗/RDP 锁 | 检查 PA19/PA20; 用 Mass Erase; **勿用 STLINK** |

---

## 电赛真题方案

| 年份 | 题号 | 题目 | 涉及知识点 |
|------|------|------|-----------|
| 2021 | F | 智能送药小车 | 巡线 + 码盘定位 + 近场通信 |
| 2022 | C | 小车跟随行驶 | 超声波/视觉测距 + PID 跟随 |
| 2024 | H | 自动行驶小车 | 巡线 + 色块/码识别 + 定点停靠 |
| 2024 | C | 无线传输信号模拟 | 信号处理 |
| 2025 | C | 单目视觉目标测量 | K230 单目测距 + A4 靶标 |
| 2025 | E | 简易自行瞄准 | 激光 + 伺服 + 图像识别 |

---

## 依赖清单

| 依赖 | 版本 | 必需 |
|------|------|------|
| MSPM0 SDK | mspm0_sdk_2_04_00_06 | 是 |
| TI Arm Clang | Keil 内置 | 是 |
| SysConfig | 1.23.1 | 是 |
| InvenSense eMPL | -- | 是 (MPU6050) |
| CanMV | canmv_k230 v1.6+ | 是 (K230) |
| DAP/CH9102 驱动 | -- | 是 (烧录) |

---








