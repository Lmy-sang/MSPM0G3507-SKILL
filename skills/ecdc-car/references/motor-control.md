# 电机控制: TB6612 + 编码器 + PI 速度闭环

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
