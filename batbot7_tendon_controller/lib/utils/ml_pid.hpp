#include <Arduino.h>

/**
 * Author Mason Lopez
 *
 *
 * simple pid from curio res
 */

class ml_pid
{
public:
    // simple constructor
    ml_pid() : m_kp(1), m_kd(0), m_ki(0), m_umax(255), m_error_prev(0), m_error_integral(0) {}

    // set paramaets
    void Set_Params(float kp, float kd, float ki, float umaxIn)
    {
        m_kp = kp;
        m_kd = kd;
        m_ki = ki;

        m_umax = umaxIn;
    }

    int16_t Compute_Signal(int curTicks, int targetTicks)
    {
        unsigned long curTime = micros();
        unsigned long deltaTime = curTime - m_prevTime;
        
        // calculate the error
        int16_t error = targetTicks - curTicks;

        // derivative
        float dedt = (error-m_error_prev)/deltaTime;

        // integral
        m_error_integral += error*deltaTime;

        // calc control signal
        float sig = m_kp*error + m_kd*dedt + m_ki*m_error_integral;

        sig = fabs(sig);


        // store previous
        m_prevTime = curTime;

        return sig;
    }

private:
    float m_kp, m_kd, m_ki, m_umax;

    float m_error_prev, m_error_integral;

    unsigned long m_prevTime = 0;
};
