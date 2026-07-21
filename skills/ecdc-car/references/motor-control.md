 # 电机控制: TB6612 + 编码器 + PI 速度闭环
 
 ## 硬件架构
 
 ```
 MSPM0G3507                    D153C (TB6612)             电机+编码器
 ─────────                     ─────────────              ──────────
 PA13 ──→ AIN1           ┌── VM (7-12V 电池)        电机A ── AO1/AO2
 PA14 ──→ AIN2           │                          编码器A ── E1A/E1B (PA25/PA26)
 PB2  ──→ PWMA (TIMG6)   │   STBY ── 3.3V (已接)
 PA17 ──→ BIN1           │
 PA16 ──→ BIN2           │                           电机B ── BO1/BO2
 PB3  ──→ PWMB (TIMG6)   │                           编码器B ── E2A/E2B (PB20/PB24)
 ```
 
 STBY 已经在 D153C 模块上接 3.3V, 不需要 MCU 控制。
 
 ## PWM 输出: Set_PWM()
 
 ```c
 void Set_PWM(int pwmA, int pwmB) {
     // 电机A 方向 + 占空比
     if (pwmA > 0) {
         DL_GPIO_setPins(AIN_PORT, AIN_AIN2_PIN);
         DL_GPIO_clearPins(AIN_PORT, AIN_AIN1_PIN);
         DL_Timer_setCaptureCompareValue(PWM_0_INST, ABS(pwmA), GPIO_PWM_0_C0_IDX);
     } else {
         DL_GPIO_setPins(AIN_PORT, AIN_AIN1_PIN);
         DL_GPIO_clearPins(AIN_PORT, AIN_AIN2_PIN);
         DL_Timer_setCaptureCompareValue(PWM_0_INST, ABS(pwmA), GPIO_PWM_0_C0_IDX);
     }
     // 电机B 方向 + 占空比 (同上, 替换 BIN/BIN2/PIN, GPIO_PWM_0_C1_IDX)
     if (pwmB > 0) { ... } else { ... }
 }
 ```
 
 **pwmA/pwmB > 0 为正转, < 0 为反转。占空比由 `DL_Timer_setCaptureCompareValue` 的绝对值控制。**
 
 ## 编码器读取: GROUP1_IRQHandler
 
 ```c
 void GROUP1_IRQHandler(void) {
     // 获取中断源
     uint32_t irq1 = DL_GPIO_getEnabledInterruptStatus(ENCODERA_PORT,
                         ENCODERA_E1A_PIN | ENCODERA_E1B_PIN);
     uint32_t irq2 = DL_GPIO_getEnabledInterruptStatus(ENCODERB_PORT,
                         ENCODERB_E2A_PIN | ENCODERB_E2B_PIN);
 
     // 电机A 编码器: 2倍频解码
     if (irq1 & ENCODERA_E1A_PIN) {
         Get_Encoder_countA += DL_GPIO_readPins(ENCODERA_PORT, ENCODERA_E1B_PIN) ? 1 : -1;
     } else if (irq1 & ENCODERA_E1B_PIN) {
         Get_Encoder_countA += DL_GPIO_readPins(ENCODERA_PORT, ENCODERA_E1A_PIN) ? -1 : 1;
     }
     // 电机B 同理
     // ...
     DL_GPIO_clearInterruptStatus(ENCODERA_PORT, ENCODERA_E1A_PIN | ENCODERA_E1B_PIN);
     DL_GPIO_clearInterruptStatus(ENCODERB_PORT, ENCODERB_E2A_PIN | ENCODERB_E2B_PIN);
 }
 ```
 
 **两个编码器的 GPIO 中断都在 GROUP1 里处理。通过读取另一相电平判断方向。**
 
 ## RPM 计算
 
 ```c
 float Calculate_Motor_RPM(int encoder_count, int sample_time_ms) {
     const int ENCODER_LINES = 13;    // 编码器线数
     const int MULTIPLY_FACTOR = 2;   // 2倍频
     const int GEAR_RATIO = 30;       // 减速比
     int pulses_per_revolution = ENCODER_LINES * MULTIPLY_FACTOR; // 26
     float motor_rpm = (float)encoder_count * 60000.0f /
                       (pulses_per_revolution * sample_time_ms);
     return motor_rpm / GEAR_RATIO;   // 输出轴转速
 }
 ```
 
 ## 增量式 PI 速度控制器
 
 ```c
 float Velcity_Kp = 2.6f, Velcity_Ki = 1.3f, Velcity_Kd = 0;  // 默认参数
 
 int Velocity_A(int TargetVelocity, int CurrentVelocity) {
     int Bias = TargetVelocity - CurrentVelocity;       // 速度偏差
     static int ControlVelocityA, Last_biasA;
 
     // 增量式 PI: control += Ki*(bias-last) + Kp*bias
     ControlVelocityA += Velcity_Ki * (Bias - Last_biasA) + Velcity_Kp * Bias;
     Last_biasA = Bias;
 
     // PWM 限幅
     if (ControlVelocityA > 7000)  ControlVelocityA = 7000;
     if (ControlVelocityA < -7000) ControlVelocityA = -7000;
     return ControlVelocityA;
 }
 ```
 
 **默认 Kp=2.6, Ki=1.3, PWM 限幅 ±7000。** 注意这是**增量式 PI**, 积分为 `ControlVelocity +=` 形式, 断电或静止时自动归零。
 
 ## 10ms 定时速度闭环 (典型模板)
 
 ```c
 void TIMER_0_INST_IRQHandler(void) {
     if (DL_TimerA_getPendingInterrupt(TIMER_0_INST) && DL_TIMER_IIDX_ZERO) {
         // 计算 RPM (10ms 采样)
         MA_RPM = Calculate_Motor_RPM(Get_Encoder_countA, 10);
         MB_RPM = Calculate_Motor_RPM(-Get_Encoder_countB, 10);
         Get_Encoder_countA = Get_Encoder_countB = 0;
 
         if (!Flag_Stop) {
             PWMA = -Velocity_A(TARGET_RPM, MA_RPM);
             PWMB = -Velocity_B(TARGET_RPM, MB_RPM);
             PWMA = limit_PWM(PWMA, -7999, 7999);
             PWMB = limit_PWM(PWMB, -7999, 7999);
             Set_PWM(PWMA, PWMB);
         } else {
             Set_PWM(0, 0);
         }
     }
 }
 ```
 
 ## PID 调参建议
 
 | 步骤 | 操作 | 效果 |
 |------|------|------|
 | 1 | Kp=2.6, Ki=0 | 先看响应速度 |
 | 2 | Kp 逐步增大 | 加快响应, 直到有轻微超调 |
 | 3 | Ki 逐步增大 | 消除稳态误差 |
 | 4 | 如果振荡 | 减小 Kp 和 Ki |
 
 **如果更换电机**: 修改 `encoder.c` 中的 `ENCODER_LINES`, `MULTIPLY_FACTOR`, `GEAR_RATIO`。
