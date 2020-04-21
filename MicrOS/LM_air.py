import math
from machine import ADC

#########################################
#  DHT22 temperature & humidity sensor  #
#########################################
DHT_OBJ = None


def __init_DHT22():
    global DHT_OBJ
    if DHT_OBJ is None:
        from dht import DHT22
        from machine import Pin
        from LogicalPins import getPlatformValByKey
        DHT_OBJ = DHT22(Pin(getPlatformValByKey('dht_pin')))
    return DHT_OBJ


def temp():
    __init_DHT22().measure()
    return "{} ºC".format(DHT_OBJ.temperature())


def hum():
    __init_DHT22().measure()
    return "{} %".format(DHT_OBJ.humidity())


def temp_hum():
    __init_DHT22().measure()
    return DHT_OBJ.temperature(), DHT_OBJ.humidity()

#########################################
#            MQ135 GAS SENSOR           #
#########################################


MQ123_CONST = {'RLOAD': 10.0,        # The load resistance on the board
               'RZERO': 76.63,       # Calibration resistance at atmospheric CO2 level
               'PARA': 116.6020682,  # Parameters for calculating ppm of CO2 from sensor resistance
               'PARB': 2.769034857,
               'CORA': 0.00035,      # Parameters to model temperature and humidity dependence
               'CORB': 0.02718,
               'CORC': 1.39538,
               'CORD': 0.0018,
               'CORE': -0.003333333,
               'CORF': -0.001923077,
               'CORG': 1.130128205,
               'ATMOCO2': 397.13}    # Atmospheric CO2 level for calibration purposes


def __get_correction_factor(temperature, humidity):
    """Calculates the correction factor for ambient air temperature and relative humidity
    Based on the linearization of the temperature dependency curve
    under and above 20 degrees Celsius, assuming a linear dependency on humidity,
    provided by Balk77 https://github.com/GeorgK/MQ135/pull/6/files
    """
    if temperature < 20:
        return MQ123_CONST['CORA'] * temperature * temperature - MQ123_CONST['CORB']\
               * temperature + MQ123_CONST['CORC'] - (humidity - 33.) * MQ123_CONST['CORD']
    return MQ123_CONST['CORE'] * temperature + MQ123_CONST['CORF'] * humidity + MQ123_CONST['CORG']


def __get_resistance():
    """Returns the resistance of the sensor in kOhms // -1 if not value got in pin"""
    adc = ADC(0)
    value = adc.read()
    if value == 0:
        return -1
    return (1023./value - 1.) * MQ123_CONST['RLOAD']


def __get_corrected_resistance(temperature, humidity):
    """Gets the resistance of the sensor corrected for temperature/humidity"""
    return __get_resistance()/ __get_correction_factor(temperature, humidity)


def get_corrected_ppm(temperature, humidity):
    """Returns the ppm of CO2 sensed (assuming only CO2 in the air)
    corrected for temperature/humidity"""
    return MQ123_CONST['PARA'] * math.pow((__get_corrected_resistance(temperature, humidity)\
                                           / MQ123_CONST['RZERO']), -MQ123_CONST['PARB'])


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
    _temperature, _humidity = temp_hum()
    temperature = _temperature  if temperature is None else temperature
    humidity = _humidity if humidity is None else humidity

    try:
        status = 'n/a'
        ppm = get_corrected_ppm(temperature, humidity)
        if ppm < 1000:
            status = 'PERFECT'
        elif ppm < 2000:
            status = 'POOR'
        elif ppm < 4000:
            status = "WARNING"
        elif ppm > 5000:
            status = "CRITICAL"
        return "{} PPM - {}".format(ppm, status)
    except Exception as e:
        return "getMQ135GasPPM ERROR: {}".format(e)


def help():
    return 'temp', 'hum', 'getMQ135GasPPM(temperature, humidity)'

