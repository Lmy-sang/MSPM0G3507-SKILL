# 传感器模块

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
