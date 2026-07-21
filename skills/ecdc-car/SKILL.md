---
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
