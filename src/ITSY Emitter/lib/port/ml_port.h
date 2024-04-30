/*
 * Author: Ben Westcott
 * Date created: 1/27/23
 */

#ifndef ML_PORT_H
#define ML_PORT_H

#include <Arduino.h>

#ifdef __cplusplus
extern "C"
{
#endif

typedef uint8_t ml_pin;

typedef enum
{
    PF_A, PF_B, PF_C, PF_D, PF_E, PF_F, PF_G, 
    PF_H, PF_I, PF_J, PF_K, PF_L, PF_M, PF_N
} ml_port_function;

typedef enum
{
    PP_ODD, PP_EVEN
} ml_port_parity;

typedef enum 
{ 
    DRIVE_OFF = 0x00, 
    DRIVE_ON = 0x01
} ml_port_drive_strength;

typedef enum 
{

    INPUT_STANDARD = 0x02,
    INPUT_PULL_DOWN = 0x06,
    INPUT_PULL_UP = 0x16,
    OUTPUT_TOTEMPOLE_INPUT_DISABLED = 0x01,
    OUTPUT_TOTEMPOLE_INPUT_ENABLED = 0x03,
    OUTPUT_PULL_DOWN = 0x04,
    OUTPUT_PULL_UP = 0x14,
    ANALOG = 0x00

} ml_port_config;

typedef enum
{
    PORT_GRP_A, 
    PORT_GRP_B, 
    PORT_GRP_C, 
    PORT_GRP_D
} ml_port_group;

typedef struct
{
    ml_port_group group;
    ml_pin pin;
    ml_port_function pf;
    ml_port_parity par;
    ml_port_config conf;
    ml_port_drive_strength drv;

} ml_pin_settings;

void port_pmux_disable(const ml_pin_settings *set);

void peripheral_port_init
(
    const ml_pin_settings *set
);

boolean logical_read
(
    const ml_pin_settings *set
);

void logical_set
(
    const ml_pin_settings *set
);

void logical_unset
(
    const ml_pin_settings *set
);

void logical_toggle
(
    const ml_pin_settings *set
);

/*
 * Works on ItsyBitsy M4 -- controls RGB LED 
 */
void dotstar_init(void);
void dotstar_set(uint8_t r, uint8_t g, uint8_t b, uint8_t brightness);

#define DOTSTAR_SET_BLUE() (dotstar_set(0x00, 0x00, 0xff, 31))
#define DOTSTAR_SET_RED() (dotstar_set(0xff, 0x00, 0x00, 31))
#define DOTSTAR_SET_GREEN() (dotstar_set(0x00, 0xff, 0x00, 31))
#define DOTSTAR_SET_YELLOW() (dotstar_set(0xff, 0xff, 0x00, 31))
#define DOTSTAR_SET_ORANGE() (dotstar_set(0xff, 0x80, 0x00, 31))
#define DOTSTAR_SET_PINK() (dotstar_set(0xff, 0x66, 0xb2, 31))
#define DOTSTAR_SET_LIGHT_BLUE() (dotstar_set(0x99, 0xcc, 0xff, 31))
#define DOTSTAR_SET_LIGHT_GREEN() (dotstar_set(0x99, 0xff, 0x99, 31))
#define DOTSTAR_SET_LIGHT_RED() (dotstar_set(0xff, 0x99, 0x99, 31))
#define DOTSTAR_SET_LIGHT_ORANGE() (dotstar_set(0xff, 0xcc, 0x99, 31))
#define DOTSTAR_SET_OFF() (dotstar_set(0x00, 0x00, 0x00, 0x00))


#ifdef __cplusplus
}
#endif

#endif // ML_PORT_H