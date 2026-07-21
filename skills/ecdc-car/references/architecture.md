# 软件架构: BSP / Module / App

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
