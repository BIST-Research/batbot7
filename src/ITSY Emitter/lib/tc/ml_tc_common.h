/*
 * Author: Jayson De La Vega, Ben Westcott
 * Date created: 8/2/23
 */

#ifndef ML_TC_H
#define ML_TC_H

#include <Arduino.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C"
{
#endif

#define ML_TC_N_CHANNELS                    0x02

typedef enum _ml_tc_cc_t
{
    CC0, CC1
} ml_tc_cc_t;

#define ML_TC_COUNT_MODE_COUNT16            0x00
#define ML_TC_COUNT_MODE_COUNT8             0x01
#define ML_TC_COUNT_MODE_COUNT32            0x02

typedef enum _ml_tc_count_mode_t
{
    MODE_COUNT16 = ML_TC_COUNT_MODE_COUNT16,
    MODE_COUNT8 = ML_TC_COUNT_MODE_COUNT8,
    MODE_COUNT32 = ML_TC_COUNT_MODE_COUNT32
} ml_tc_count_mode_t;

#define ML_TC_PRESCSYNC_GCLK                0x00
#define ML_TC_PRESCSYNC_PRESC               0x01
#define ML_TC_PRESCSYNC_RESYNC              0x02

typedef enum _ml_tc_prescsync_t
{
    PRESCSYNC_GCLK = ML_TC_PRESCSYNC_GCLK,
    PRESCSYNC_PRESC = ML_TC_PRESCSYNC_PRESC,
    PRESCSYNC_RESYNC = ML_TC_PRESCSYNC_RESYNC
} ml_tc_prescsync_t;

typedef enum _ml_tc_prescaler_t
{
    PRESCALER_DIV1, PRESCALER_DIV2, PRESCLER_DIV4,
    PRESCALER_DIV8, PRESCALER_DIV16,PRESCALER_DIV64, 
    PRESCALER_DIV256, PRESCALER_DIV1024
} ml_tc_prescaler_t;


#define ML_TC_CAPTMODE_DEFAULT              0x00
#define ML_TC_CAPTMODE_CAPTMIN              0x01
#define ML_TC_CAPTMODE_CAPTMAX              0x02

typedef enum _ml_tc_captmode_t
{
    CAPTMODE_DEFAULT = ML_TC_CAPTMODE_DEFAULT,
    CAPTMODE_CAPTMIN = ML_TC_CAPTMODE_CAPTMIN,
    CAPTMODE_CAPTMAX = ML_TC_CAPTMODE_CAPTMAX
} ml_tc_captmode_t;

#define ML_TC_CMD_NONE                      0x00
#define ML_TC_CMD_RETRIGGER                 0x01
#define ML_TC_CMD_STOP                      0x02
#define ML_TC_CMD_UPDATE                    0x03
#define ML_TC_CMD_READSYNC                  0x04

typedef enum _ml_tc_cmd_t
{
    CMD_NONE = ML_TC_CMD_NONE,
    CMD_RETRIGGER = ML_TC_CMD_RETRIGGER,
    CMD_STOP = ML_TC_CMD_STOP,
    CMD_UPDATE = ML_TC_CMD_UPDATE,
    CMD_READSYNC = ML_TC_CMD_READSYNC
} ml_tc_cmd_t;

#define ML_TC_COUNT_DIR_UP                  0x00
#define ML_TC_COUNT_DIR_DOWN                0x01

typedef enum _ml_tc_count_dir_t
{
    COUNT_DIR_UP = ML_TC_COUNT_DIR_UP,
    COUNT_DIR_DOWN = ML_TC_COUNT_DIR_DOWN
} ml_tc_count_dir_t;

#define ML_TC_EVACT_OFF                     0x00
#define ML_TC_EVACT_RETRIGGER               0x01
#define ML_TC_EVACT_COUNT                   0x02
#define ML_TC_EVACT_START                   0x03
#define ML_TC_EVACT_STAMP                   0x04
#define ML_TC_EVACT_PPW                     0x05
#define ML_TC_EVACT_PWP                     0x06
#define ML_TC_EVACT_PW                      0x07

typedef enum _ml_tc_evact_t
{
    EVACT_OFF = ML_TC_EVACT_OFF,
    EVACT_RETRIGGER = ML_TC_EVACT_RETRIGGER,
    EVACT_COUNT = ML_TC_EVACT_COUNT,
    EVACT_START = ML_TC_EVACT_START,
    EVACT_STAMP = ML_TC_EVACT_STAMP,
    EVACT_PPW = ML_TC_EVACT_PPW,
    EVACT_PWP = ML_TC_EVACT_PWP,
    EVACT_PW = ML_TC_EVACT_PW
} ml_tc_evact_t;

#define ML_TC_WAVEGEN_NFRQ                  0x00
#define ML_TC_WAVEGEN_MFRQ                  0x01
#define ML_TC_WAVEGEN_NPWM                  0x02
#define ML_TC_WAVEGEN_MPWM                  0x03

typedef enum _ml_tc_wavegen_t
{
    WAVEGEN_NFRQ = ML_TC_WAVEGEN_NFRQ,
    WAVEGEN_MFRQ = ML_TC_WAVEGEN_MFRQ,
    WAVEGEN_NPWM = ML_TC_WAVEGEN_NPWM,
    WAVEGEN_MPWM = ML_TC_WAVEGEN_MPWM
} ml_tc_wavegen_t;

void TC_sync(Tc *instance);

void TC_enable(Tc *instance);

void TC_disable(Tc *instance);

void TC_swrst(Tc *instance);

void TC_channel_capture_compare_set
(
    Tc *instance, 
    const ml_tc_cc_t channel, 
    const uint8_t ccval
);

void TC_set_oneshot(Tc *instance);
void TC_force_stop(Tc *instance);
void TC_force_retrigger(Tc *instance);

#define ML_TC_OVF_INTSET(instance)           (instance->COUNT16.INTENSET.bit.OVF = 0x01)
#define ML_TC_ERR_INTSET(instance)           (instance->COUNT16.INTENSET.bit.ERR = 0x01)
#define ML_TC_MC0_INTSET(instance)           (instance->COUNT16.INTENSET.bit.MC0 = 0x01)
#define ML_TC_MC1_INTSET(instance)           (instance->COUNT16.INTENSET.bit.MC1 = 0x01)

#define ML_TC_OVF_INTCLR(instance)           (instance->COUNT16.INTENCLR.bit.OVF = 0x01)
#define ML_TC_ERR_INTCLR(instance)           (instance->COUNT16.INTENCLR.bit.ERR = 0x01)
#define ML_TC_MC0_INTCLR(instance)           (instance->COUNT16.INTENCLR.bit.MC0 = 0x01)
#define ML_TC_MC1_INTCLR(instance)           (instance->COUNT16.INTENCLR.bit.MC1 = 0x01)

#define ML_TC_OVF_CLR_INTFLAG(instance)      (instance->COUNT16.INTFLAG.bit.OVF = 0x01)
#define ML_TC_ERR_CLR_INTFLAG(instance)      (instance->COUNT16.INTFLAG.bit.ERR = 0x01)
#define ML_TC_MC0_CLR_INTFLAG(instance)      (instance->COUNT16.INTFLAG.bit.MC0 = 0x01)
#define ML_TC_MC1_CLR_INTFLAG(instance)      (instance->COUNT16.INTFLAG.bit.MC1 = 0x01)

#define ML_TC_CLR_INTFLAGS(instance)         (instance->COUNT16.INTFLAG.reg = TC_INTFLAG_MASK)

#define ML_TC_OVF_INTFLAG(instance)          (instance->COUNT16.INTFLAG.bit.OVF == 0x01)
#define ML_TC_ERR_INTFLAG(instance)          (instance->COUNT16.INTFLAG.bit.ERR == 0x01)
#define ML_TC_MC0_INTFLAG(instance)          (instance->COUNT16.INTFLAG.bit.MC0 == 0x01)
#define ML_TC_MC1_INTFLAG(instance)          (instance->COUNT16.INTFLAG.bit.MC1 == 0x01)


#ifdef __cplusplus
}
#endif

#endif // ML_TC_H