from math import pow

#########################################
#  DHT22 temperature & humidity sensor  #
#########################################
__DHT_OBJ = None


def __init_DHT22():
    global __DHT_OBJ
    if __DHT_OBJ is None:
        from dht import DHT22
        from machine import Pin
        from LogicalPins import get_pin_on_platform_by_key
        __DHT_OBJ = DHT22(Pin(get_pin_on_platform_by_key('simple_1')))
    return __DHT_OBJ


def __temp_hum():
    __init_DHT22().measure()
    return __DHT_OBJ.temperature(), __DHT_OBJ.humidity()


def dht_measure():
    temp_, hum_ = __temp_hum()
    return "\n{} ºC\n{} %".format(temp_, hum_)


#########################################
#            MQ135 GAS SENSOR           #
#########################################
__ADC = None


def __get_correction_factor(temperature, humidity):
    """Calculates the correction factor for ambient air temperature and relative humidity
    Based on the linearization of the temperature dependency curve
    under and above 20 degrees Celsius, assuming a linear dependency on humidity,
    provided by Balk77 https://github.com/GeorgK/MQ135/pull/6/files
    0.00035  - 'CORA' Parameters to model temperature and humidity dependence
    0.02718  - 'CORB'
    1.39538  - 'CORC'
    0.0018   - 'CORD'
    -0.003333333  - 'CORE'
    -0.001923077  - 'CORF'
    1.130128205   - 'CORG'
    """
    if temperature < 20:
        return 0.00035 * temperature * temperature - 0.02718\
               * temperature + 1.39538 - (humidity - 33.) * 0.0018
    return -0.003333333 * temperature + -0.001923077 * humidity + 1.130128205


def __get_resistance():
    """
    Returns the resistance of the sensor in kOhms // -1 if not value got in pin
    10.0 - 'RLOAD' The load resistance on the board
    """
    global __ADC
    if __ADC is None:
        from machine import ADC
        from LogicalPins import get_pin_on_platform_by_key
        __ADC = ADC(get_pin_on_platform_by_key('adc_0'))
    value = __ADC.read()
    if value == 0:
        return -1
    return (1023./value - 1.) * 10.0


def __get_corrected_resistance(temperature, humidity):
    """Gets the resistance of the sensor corrected for temperature/humidity"""
    return __get_resistance()/__get_correction_factor(temperature, humidity)


def __get_corrected_ppm(temperature, humidity):
    """
    Returns the ppm of CO2 sensed (assuming only CO2 in the air)
    corrected for temperature/humidity
    76.63       - 'RZERO' Calibration resistance at atmospheric CO2 level
    116.6020682 - 'PARA' parameters for calculating ppm of CO2 from sensor resistance
    2.769034857 - 'PARB'
    """
    return 116.6020682 * pow((__get_corrected_resistance(temperature, humidity)\
                                           / 76.63), -2.769034857)


def getMQ135GasPPM(temperature=None, humidity=None):
    """
    CO2 Gas Concentration - Parts-per-million - PPM
    -> 1ppm = 0.0001% gas.
    Concentration evaluation:
        250-400ppm      Normal background concentration in outdoor ambient air
        400-1,000ppm    Concentrations typical of occupied indoor spaces with good air exchange
        1,000-2,000ppm  Complaints of drowsiness and poor air.
        2,000-5,000 ppm Headaches, sleepiness and stagnant, stale, stuffy air. Poor concentration, loss of attention, increased heart rate and slight nausea may also be present.
        5,000ppm        Workplace exposure limit (as 8-hour TWA) in most jurisdictions.
        >40,000 ppm     Exposure may lead to serious oxygen deprivation resulting in permanent brain damage, coma, even death.
    """
    if temperature is None or humidity is None:
        temperature, humidity = __temp_hum()

    try:
        status = 'n/a'
        ppm = __get_corrected_ppm(temperature, humidity)
        if ppm <= 1000:
            status = 'PERFECT'
        elif ppm <= 2000:
            status = 'POOR'
        elif ppm <= 4000:
            status = "WARNING"
        elif ppm > 4000:
            status = "CRITICAL"
        return "\n{} PPM - {}".format(ppm, status)
    except Exception as e:
        return "\ngetMQ135GasPPM ERROR: {}".format(e)


def measure():
    _temp, _hum = __temp_hum()
    return "\n{} ºC\n{} %{}".format(_temp, _hum, getMQ135GasPPM(_temp, _hum))


def help():
    return 'measure', 'dht_measure', 'getMQ135GasPPM(temp, hum)'

