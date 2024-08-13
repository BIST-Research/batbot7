/*
 * Author: Ben Westcott
 * Date created: 7/29/23
 */

#include <ml_motor.hpp>

void motor_set_speed(ml_motor *motor, uint16_t speed)
{
    motor->pwm_inst->CCBUF[motor->pwm_cc_num].reg = TCC_CCBUF_CCBUF(speed);
    TCC_sync(motor->pwm_inst);
}

// void motor_set_direction(ml_motor *motor, ml_motor_dir dir)
// {
//     if(dir == OFF)
//     {
//         motor->pwm_inst->CCBUF[motor->pwm_cc_num].reg = TCC_CCBUF_CCBUF(0x00);
//         TCC_sync(motor->pwm_inst);
//     } 
//     else if(dir == CW)
//     {
//         logical_set(&motor->phase);
//     } 
//     else
//     {
//         logical_unset(&motor->phase);
//     }
// }