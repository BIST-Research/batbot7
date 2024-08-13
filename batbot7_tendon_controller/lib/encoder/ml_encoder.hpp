/*
 * Author: Ben Westcott
 * Date created: 7/31/23
 */

#include <Arduino.h>
#include <ml_motor.hpp>

/*
 * M0:
 *      enca: D40 --> PC13 --> EXTINT[13]
 *      encb: D41 --> PC12 --> EXTINT[12]
 * M1:
 *      enca: D42 --> PC15 --> EXTINT[15]
 *      encb: D43 --> PC14 --> EXTINT[14]
 * M2:
 *      enca: D44 --> PC11 --> EXTINT[11]
 *      encb: D45 --> PC10 --> EXTINT[10]
 * M3:
 *      enca: D46 --> PC06 --> EXTINT[6]
 *      encb: D47 --> PC07 --> EXTINT[9]
 * M4:
 *      enca: D48 --> PC04 --> EXTINT[4]
 *      encb: D49 --> PC05 --> EXTINT[5]
 * M5:
 *      enca: D30 --> PA23 --> EXTINT[7]
 *      encb: D51 --> PD08 --> EXTINT[3]
 */

void encoder_extint_init(void);
void encoder_tick(ml_motor *set);