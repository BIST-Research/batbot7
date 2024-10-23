#ifndef TENDONMOTOR_H
#define TENDONMOTOR_H

#include <port/ml_port.h>
#include <tcc/ml_tcc_common.h>
#include <ml_pid.hpp>

#define ML_HPCB_LV_75P1 (75.81)
#define ML_HPCB_LV_100P1 (100.37)
#define ML_HPCB_LV_150P1 (150.58)
#define ML_HPCB_LV_210P1 (210.59)

#define ML_ENC_CPR (12)

#define ENC_DEG_TO_TICKS(deg) (deg * ML_ENC_CPR * ML_HPCB_LV_75P1) / 360.0
#define ENC_TICK_TO_DEG(ticks) ((360.0*(float)ticks)/((float)ML_ENC_CPR*ML_HPCB_LV_75P1))


// direction motor should turn
typedef enum
{
    CW,
    CCW,
    OFF
} Tendon_Direction;

class TendonController
{
public:
    // create motor and encoder object
    // TendonController(uint8_t ccChan, ml_pin phasePin, ml_pin pwmPi, ml_pin encA, ml_pin encB, String name);
    TendonController(String name);

    void Attach_Drive_Pin(ml_port_group portGroup, ml_pin pin, ml_port_function, uint8_t cc_chan);

    void Attach_Direction_Pin(ml_port_group portGroup, ml_pin pin, ml_port_function);
    void Attach_EncA_Pin(ml_port_group portGroup, ml_pin pin, ml_port_function);
    void Attach_EncB_Pin(ml_port_group portGroup, ml_pin pin, ml_port_function);

    // current angle of motor
    float Get_Angle();

    // number of encoder ticks
    int32_t Get_Ticks();

    // return name assigned
    String Get_Name();

    // set motor duty cycle
    void Set_Duty_Cyle(uint16_t dutyCycle);

    void set_PWM_Freq(uint16_t pwmValue);

    // set the direction motor turns
    void Set_Direction(Tendon_Direction dir);

    void Toggle_Direction();

    // move tendon to angle
    void Set_Angle(float destAngle, float MAX_PWM = 6000);

    // angles of tendon
    void Set_Start_Angle_Limit(float angle);
    void Set_Stop_Angle_Limit(float angle);

    void Calibrate_Min_PWM();

    // init tcc clock
    void _init_tcc();

    // attach interrupt for encoder
    void encoder_ISR();

    void init_peripheral();

    void Reset_Encoder_Zero();

    void CalibrateLimits();

    void Move_To_End(bool cw);

    void Set_EncA_Flag();

    void Set_EncB_Flag();

    void Set_PID_Param(float p, float i, float d);

    uint32_t m_encA_ticks = 0;
    uint32_t m_encB_ticks = 0;

    int32_t m_currentTicks = 0;
    float m_gear_ratio = ML_HPCB_LV_75P1;

private:
    // pin settings
    ml_pin_settings m_encoder_a;
    ml_pin_settings m_encoder_b;
    ml_pin_settings m_phase;
    ml_pin_settings m_drive;

    // pwm stuff
    Tcc *m_pwm_channel;
    uint8_t m_pwm_CC = 0;

    // encoder values
    int32_t m_lastTicks = 0;
    float m_angle = 0;
    int32_t m_target_ticks = 0;
    bool m_settled = false;

    // pid stuff
    float m_kp, m_kd, m_ki, m_umax;
    float m_error_prev, m_error_integral;
    float m_prevPIDTime = 0;
    uint32_t m_chillBand = 0;

    // current pwm speed
    uint16_t m_cur_pwm = 0;
    Tendon_Direction m_direction = OFF;


    // min PWM values for each motor
    uint16_t m_min_CW_PWM = 0;
    uint16_t m_min_CCW_PWM = 0;
    bool m_calibrated = false;


    // limits
    float m_start_angle = -180;
    float m_end_angle = 180;

    // motor and encoder default settings
    uint32_t m_cycles_per_rev = ML_ENC_CPR;

    // name of the current tendon controller
    String m_name = "";

    // frequency of tcc channel
    uint32_t m_tcc_freq = 6000;
};

#endif