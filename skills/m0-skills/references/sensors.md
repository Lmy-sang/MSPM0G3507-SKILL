 # 传感器模块
 
 ## HC-05 蓝牙
 
 - 接口: UART1 (PB6=TX, PB7=RX), 3.3V TTL
 - 默认波特率: 9600 (可 AT 指令修改)
 - 模式: 从机, 配对后透明传输
 
 ### 蓝牙微信小程序控制 (轮趣例程)
 
 ```c
 // 蓝牙数���接收处理
 void BTBufferHandler(void) {
     // 从 UART1 接收数据, 解析控制指令
     // 例: "F"=前进, "B"=后退, "L"=左转, "R"=右转, "S"=停止
 }
 ```
 
 ## MPU6050 陀螺仪
 
 - 接口: I2C (PA0=SDA, PA1=SCL), 地址 0x68, INT=PA7
 - DMP 姿态解算: 200Hz 更新率, 可获得 Pitch/Roll/Yaw
 
 ### 初始化
 
 ```c
 // 硬件 I2C 初始化 (SysConfig 配置 I2C 实例)
 MPU6050_initialize();   // MPU6050 初始化
 DMP_Init();             // DMP 初始化
 NVIC_EnableIRQ(GPIO_MULTIPLE_GPIOA_INT_IRQN);  // MPU6050 INT 中断
 ```
 
 ### DMP 读取 (在 GROUP1_IRQHandler 中)
 
 ```c
 if (portE2_intp & MPU6050_INT_PIN_PIN) {
     Read_DMP();
     mpu6050.pitch = Roll;
     mpu6050.roll = Pitch;
     mpu6050.yaw = Yaw;
     mpu6050.gyro.x = gyro[0];
     mpu6050.gyro.y = gyro[1];
     mpu6050.gyro.z = gyro[2];
     DL_GPIO_clearInterruptStatus(Encoder2_PORT, MPU6050_INT_PIN_PIN);
 
     BalanceControlTask();  // 平衡车控制 (5ms 执行一次)
 }
 ```
 
 **MPU6050 DMP 中断和编码器中断共享 GROUP1。** 注意优先级设置, 避免 DMP 读取影响编码器计数。
 
 ## HC-SR04 超声波测距
 
 - 接口: GPIO (PA24=Trig, PA9=Echo)
 - 测量范围: 2cm-400cm
 
 ### 测量流程
 
 ```c
 // 1. 发送 10us 高脉冲到 Trig
 DL_GPIO_setPins(TRIG_PORT, TRIG_PIN);
 delay_us(10);
 DL_GPIO_clearPins(TRIG_PORT, TRIG_PIN);
 
 // 2. 等待 Echo 引脚变为高电平
 while (!DL_GPIO_readPins(ECHO_PORT, ECHO_PIN));
 
 // 3. 计时高电平持续时间 (us)
 uint32_t start = SysTick->VAL;
 while (DL_GPIO_readPins(ECHO_PORT, ECHO_PIN));
 uint32_t elapsed = start - SysTick->VAL;  // 注意 Systick 是向下计数
 
 // 4. 距离 = 时间 × 340m/s / 2
 float distance_cm = elapsed * 0.017f;  // 简化公式
 ```
 
 **互相斥约束**: 超声波不能和 CCD(共享 PA9) 或雷达(共享 PA24) 同时使用。
 
 ## HJ-DXJ8 八路灰度循线 (8 路独立输出)

- 模块: 8 路数字灰度传感器, 每路独立 OUT 线 (OUT1~OUT8)
- 接口: VCC / GND / OUT1 / OUT2 / ... / OUT8 (共 10 根线)
- 每路输出: 数字量 0/1
- 感应距离: 最佳 15-30mm
- 灵敏度: 每个通道有独立电位器调节

### 引脚配置

此模块需要 8 个独立 GPIO, 用户根据底板空闲引脚自行分配。

### 巡线算法

`c
int weights[8] = {-35, -25, -15, -5, 5, 15, 25, 35};
int err = 0, active = 0;
for (int i = 0; i < 8; i++) {
    if (results[i] == ACTIVE_VALUE) { err += weights[i]; active++; }
}
if (active > 0) err /= active;
Set_PWM(base + err*KP, base - err*KP);
`

**ACTIVE_VALUE**: 现场测试确定。
## CD4051 真值表
 
 | AD2 | AD1 | AD0 | 通道 | 传感器 X1-X8 对应 |
 |-----|-----|-----|------|-------------------|
 | 0 | 0 | 0 | CH1 | X1 (最左) |
 | 0 | 0 | 1 | CH2 | X2 |
 | 0 | 1 | 0 | CH3 | X3 |
 | 0 | 1 | 1 | CH4 | X4 |
 | 1 | 0 | 0 | CH5 | X5 |
 | 1 | 0 | 1 | CH6 | X6 |
 | 1 | 1 | 0 | CH7 | X7 |
 | 1 | 1 | 1 | CH8 | X8 (最右) |
 
 ### 读取实现
 
 ```c
 #define GRAY_AD0_PORT  GPIOA
 #define GRAY_AD0_PIN   DL_GPIO_PIN_12   // PA12 → X3
 #define GRAY_AD1_PIN   DL_GPIO_PIN_27   // PA27 → X2
 #define GRAY_AD2_PIN   DL_GPIO_PIN_16   // PB16 (GPIOB) → X1
 #define GRAY_OUT_PIN   DL_GPIO_PIN_17   // PB17 (GPIOB) → X4
 
 void ReadEightChannel(uint8_t results[8]) {
     for (int ch = 0; ch < 8; ch++) {
         // AD2=bit2, AD1=bit1, AD0=bit0
         uint8_t ad2 = (ch >> 2) & 1;
         uint8_t ad1 = (ch >> 1) & 1;
         uint8_t ad0 = ch & 1;
         // 设置地址线
         DL_GPIO_setPins(GRAY_AD0_PORT, GRAY_AD0_PIN | GRAY_AD1_PIN | GRAY_AD2_PIN); // 先全置高
         // 再按需置低 (简化: 用 setPins/clearPins 逐位)
         // ... 实际用 GRAYSCALE_PIN_WRITE 宏封装 ...
         delay_us(100);  // 等待 CD4051 稳定
         results[ch] = DL_GPIO_readPins(GPIOB, GRAY_OUT_PIN) ? 1 : 0;
     }
 }
 ```
 
 ### 巡线控制算法
 
 ```c
 // 加权位置计算偏差
 // 8 个传感器权重: {-35,-25,-15,-5,5,15,25,35}
 int weights[8] = {-35, -25, -15, -5, 5, 15, 25, 35};
 
 int err = 0, active = 0;
 for (int i = 0; i < 8; i++) {
     if (ir_data[i] == ACTIVE_VALUE) {  // 白底 0, 黑底 1
         err += weights[i];
         active++;
     }
 }
 if (active > 0) err /= active;
 
 // 差速转向: 左轮 +err, 右轮 -err
 int base_duty = 500;  // 基线速度
 int turn = err * KP_LINE;  // KP_LINE 默认 0.1
 Set_PWM(base_duty + turn, base_duty - turn);
 ```
 
 **互相斥约束**: 灰度巡线和 CCD 巡线不能共存 (共享 PA27)。
 
 **调参提示**: 白底赛道上 ACTIVE_VALUE=0, 黑底赛道上 ACTIVE_VALUE=1。PID 参数和基线速度需根据赛道材质在场地实调。
