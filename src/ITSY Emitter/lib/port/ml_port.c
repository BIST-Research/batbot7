/*
 * Author: Ben Westcott
 * Date created: 3/12/23
 */

#include <ml_port.h>

#define CONFIG_PULLEN(config)       (((config & 0x4) >> 2))
#define CONFIG_INEN(config)         (((config & 0x2) >> 1))
#define CONFIG_DIRSET(config)       (((config & 0x1) >> 0))
#define CONFIG_OUT(config)          (((config & 0x10) >> 4))

void peripheral_port_init(const ml_pin_settings *set)
{

    const ml_port_group group = set->group;
    const ml_pin pin = set->pin;
    const ml_port_parity parity = set->par;
    const ml_port_config config = set->conf;
    const ml_port_drive_strength drive = set->drv;
    const ml_port_function func = set->pf;


    uint8_t pmux_mask = parity ? PORT_PMUX_PMUXE((uint8_t)func) : PORT_PMUX_PMUXO((uint8_t)func);

    PORT->Group[group].PINCFG[pin].reg |= PORT_PINCFG_PMUXEN;

    PORT->Group[group].PINCFG[pin].reg |= (CONFIG_PULLEN(config) ? PORT_PINCFG_PULLEN : 0x0);

    PORT->Group[group].PINCFG[pin].reg |= (CONFIG_INEN(config) ? PORT_PINCFG_INEN : 0x0);

    PORT->Group[group].PINCFG[pin].reg |= (drive ? PORT_PINCFG_DRVSTR : 0x0);

    PORT->Group[group].PMUX[pin >> 1].reg |= pmux_mask;

    PORT->Group[group].DIR.reg |= (CONFIG_DIRSET(config) ? PORT_DIRSET_DIRSET(pin) : 0x0);

    PORT->Group[group].OUT.reg |= (CONFIG_OUT(config) ? PORT_OUT_OUT(pin) : 0x0);

}

void port_pmux_disable(const ml_pin_settings *set)
{
    PORT->Group[set->group].PINCFG[set->pin].bit.PMUXEN = 0x00;
}

boolean logical_read(const ml_pin_settings *set)
{
    return ((PORT->Group[set->group].IN.reg & (1 << PORT_IN_IN(set->pin))) >> PORT_IN_IN(set->pin));
}

void logical_set(const ml_pin_settings *set)
{
    PORT->Group[set->group].OUTSET.reg = (1 << PORT_OUTSET_OUTSET(set->pin));
}

void logical_unset(const ml_pin_settings *set)
{
    PORT->Group[set->group].OUTCLR.reg = (1 << PORT_OUTCLR_OUTCLR(set->pin));
}

void logical_toggle(const ml_pin_settings *set)
{
    PORT->Group[set->group].OUTTGL.reg = (1 << PORT_OUTTGL_OUTTGL(set->pin));
}

const ml_pin_settings dotstar_clk_pin = 
{
    PORT_GRP_B, 2, PF_D, PP_EVEN, OUTPUT_PULL_DOWN, DRIVE_OFF
};

const ml_pin_settings dotstar_data_pin = 
{
    PORT_GRP_B, 3, PF_D, PP_ODD, OUTPUT_PULL_DOWN, DRIVE_OFF
};

void dotstar_init(void)
{
    peripheral_port_init(&dotstar_clk_pin);
    peripheral_port_init(&dotstar_data_pin);

    port_pmux_disable(&dotstar_data_pin);
    port_pmux_disable(&dotstar_clk_pin);
}

void dotstar_write(uint8_t x)
{
    for(uint8_t i = 0x80; i != 0; i >>= 1)
    {
        if(x & i)
        {
            logical_set(&dotstar_data_pin);
        }
        else 
        {
            logical_unset(&dotstar_data_pin);
        }

        logical_set(&dotstar_clk_pin);
        logical_unset(&dotstar_clk_pin);
    }
}

void dotstar_set(uint8_t r, uint8_t g, uint8_t b, uint8_t brightness)
{
    dotstar_write(0x00);
    dotstar_write(0x00);
    dotstar_write(0x00);
    dotstar_write(0x00);

    dotstar_write(0b11100000 | brightness);
    dotstar_write(b);
    dotstar_write(g);
    dotstar_write(r);
}
