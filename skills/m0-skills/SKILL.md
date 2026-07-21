---
name: "m0-skills"
description: 电子设计竞赛控制题小车开发技能。适用于 TI MSPM0G3507 + 轮趣 C07A 核心板 + S27F 底板 + TB6612 电机驱动 + 亚博 K230 视觉 + ZDT Modbus 步进 + MPU6050/HC-SR04/HC-05/HJ-DXJ8 八路灰度循线。基于 Keil MDK + SysConfig + TI DriverLib。当用户需要进行电赛小车底盘控制、电机 PID、K230 视觉通信、巡线控制、步进电机云台驱动、传感器读取、赛题方案设计时使用。
---

# M0-Skills 电赛控制题小车技能

使用 MSPM0G3507 + 轮趣 C07A 核心板 + S27F 底板的差速二驱小车开发。

## 硬件平台

- MCU: TI MSPM0G3507 (Cortex-M0+, 80MHz, 128KB Flash, 32KB SRAM)
- 核心板: 轮趣 WHEELTEC C07A V1.0/V1.1
- 底板: S27F (S27F 与 S28A 内部走线相同，丝印不同)
- 底盘: 差速二驱, TB6612 D153C 双路驱动带稳压版
- IDE: Keil MDK v5.42
- SDK: mspm0_sdk_2_04_00_06, SysConfig 1.23.1
- 编程: TI DriverLib (DL_* API), 裸机 (nortos)

完整引脚映射和外设互斥约束见 [硬件参考](references/hardware.md)。


## 新建工程模板

`assets/keil-empty/` 是预配好的 Keil 空工程模板，已包含:
- empty.syscfg (MSPM0G3507, SDK 2.04.00.06, SysConfig 1.23.1)
- empty_LP_MSPM0G3507_nortos_keil.uvprojx (Keil 工程, 编译器和 SDK 路径已配好)
- ti_msp_dl_config.c/h (SysConfig 生成的初始化代码)
- mspm0g3507.sct (链接脚本) / startup_mspm0g350x_uvision.s (启动文件)

初始化新工程时:
1. 复制 assets/keil-empty/ 到目标目录
2. 根据实际需求编写 empty.c (main), board.c/h, Hardware/ 下驱动模块
3. 在 SysConfig 图形界面中修改 empty.syscfg 的引脚配置，重新生成 ti_msp_dl_config.c/h
4. **不可手改 ti_msp_dl_config.c/h**，只能通过 SysConfig 修改

## 软件架构: BSP / Module / App

代码按三层组织:

- **BSP 层**: 硬件抽象。由 SysConfig 生成的 ti_msp_dl_config.c/h 和手动编写的 board.c/h 组成。仅在更换硬件时修改。
- **Module 层**: 功能模块。电机闭环控制、K230 通信协议、PID 算法、传感器驱动。极少改动。
- **App 层**: 任务逻辑。赛题状态机、模式切换、参数表、策略。换题主要修改此层。

严格遵守此分层: App 只调用 Module 接口, Module 调用 BSP 的 DriverLib API。

## 核心规则

### 工程规则
1. SysConfig 生成的 ti_msp_dl_config.c/h 不可手改，用 SysConfig 图形界面修改后重新生成
2. 代码入口为 empty.c 的 main(), 调用 SYSCFG_DL_init()
3. 不使用微库时需实现 _sys_exit() 并重定义 fputc()
4. SDK 版本为 mspm0_sdk_2_04_00_06, 使用的 API 必须在该版本中存在
5. 烧录用 DAP/CH9102 串口, 禁用 STLINK (会锁芯片)

### 代码规则
1. 首先生成/检查 ti_msp_dl_config.h 中的宏名——所有外设实例名、引脚名、中断名以此文件为准
2. GPIO: DL_GPIO_setPins/clearPins/readPins, 中断: DL_GPIO_getEnabledInterruptStatus/clearInterruptStatus
3. PWM: DL_Timer_setCaptureCompareValue + DL_Timer_startCounter
4. 延迟: SysTick 80MHz 实现的 delay_ms/delay_us
5. printf 重定向到 UART0 用于调试
6. GPIO 中断共用 GROUP1_IRQHandler, ISR 内只做标志位和数据读取
7. 电机 PWM 推荐 10kHz, STBY 已在 D153C 模块上接 3.3V

## 模块速查

| 需求 | 读取文件 | 内容 |
|------|---------|------|
| 引脚分配、接线排查 | references/hardware.md | S27F 完整引脚表 + 互斥约束 |
| DriverLib API | references/driverlib.md | GPIO/Timer/UART/ADC/I2C/SysTick 速查 |
| 编码器、PID、差速控制 | references/motor-control.md | TB6612 + 编码器中断 + 增量式 PI |
| K230 视觉通信 | references/k230-comm.md | ASCII $...# 协议 + 17 种例程 ID |
| ZDT 步进电机 | references/stepper-zdt.md | Modbus RTU + CRC16 + 位置/速度模式 |
| 其他传感器 | references/sensors.md | HC-05/MPU6050/HC-SR04/HJ-DXJ8 CD4051 八路巡线 |
| 软件架构规范 | references/architecture.md | BSP/Module/App 三层 + Keil 工程结构 |
| 赛题策略 | references/competition-topics.md | 历年赛题分析 + 现场策略 |
| PID 调参 | scripts/pid_tune.py | 串口接收 RPM + 实时曲线 |

## 工作流程

1. 确认涉及哪些外设 → 查 references/hardware.md 确认引脚可用性
2. 确认需要哪些 Module → 读对应 reference 文件获取协议和代码模式
3. 确认 App 层逻辑 → 和用户讨论状态机和策略
4. 生成代码 → 遵循三层架构, App 只调用 Module 接口
5. 验证 → 确保所有 GPIO/外设名来自 ti_msp_dl_config.h 宏定义



