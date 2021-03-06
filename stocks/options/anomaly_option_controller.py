import csv

from stocks.options import option_controller as o
from stocks import stock_controller as s
from bot import cal as cal

strike_value_SPY = {}  # Maintains SPY strike value (Strike : Cost [volume * premium])
anomalies_csv = "Discord_Stonks/doc/anomalies.csv"
call_strikes_SPY = []
put_strikes_SPY = []

monthly_expir = cal.third_friday(cal.getYear(), cal.getMonth(), cal.getMonthlyDay()).strftime("%Y-%m-%d")
nextmonth_expir = cal.third_friday(cal.getYear(), cal.getMonth() + 1, cal.getMonthlyDay()).strftime("%Y-%m-%d")


def loadStrikes_SPY():
    """Loads strikes into call_strikes & put_strikes for SPY

    :return:
    """
    price = s.tickerPrice('SPY')
    callprice = o.roundPrice(price, 1, 'call')
    putprice = o.roundPrice(price, 1, 'put')

    for i in range(0, 15):  # Now that we have the iterator and rounded price, collect actual strikes
        call_strikes_SPY.append(o.grabStrike(callprice, 1, 'call', i))
        put_strikes_SPY.append(o.grabStrike(putprice, 1, 'put', i))


def prepare_Anomalies():
    """Gets strikes loaded and anomalies pre-generated to examine against.

    :return:
    """
    loadStrikes_SPY()
    print('Loaded anomaly strikes')
    anomaly = generate_SPY()


def checkDiff(anomaly, value, optionSpecs, strike, type, expir):
    """Checks difference in the last recorded price and reports if the difference is greater than highestDiff for
    DTE

    :param anomaly:
    :param value:
    :param strike:
    :param type:
    :param DTE:
    :return: anomaly (empty or populated)
    """
    DTE = cal.DTE(expir)
    if DTE > 30:
        highestDiff = 800000
    elif DTE > 15:
        highestDiff = 700000
    else:
        highestDiff = 600000

    prev_value = strike_value_SPY.get(expir + ' ' + str(strike) + type)['value']
    diff = int(value - prev_value)
    if diff > highestDiff:
        prev_volume = strike_value_SPY.get(expir + ' ' + str(strike) + type)['volume']
        anomaly.setdefault(expir + ' ' + str(strike) + type, {})['diff'] = diff
        anomaly.setdefault(expir + ' ' + str(strike) + type, {})['curr'] = optionSpecs[0]
        anomaly.setdefault(expir + ' ' + str(strike) + type, {})['volume'] = optionSpecs[1] - prev_volume
        anomaly.setdefault(expir + ' ' + str(strike) + type, {})['gamma'] = optionSpecs[2]
        anomaly.setdefault(expir + ' ' + str(strike) + type, {})['dte'] = str(DTE) + 'DTE'
        return anomaly


def generateValue_SPY(strike, type, expir, anomaly):
    """Generates value from strike (premium) * volume. Stores everything in strike_value_SPY, returns anomaly.

    :param strike:
    :param type:
    :param expir:
    :param anomaly:
    :return: anomaly (empty or populated)
    """
    typeAbv = type[0].upper()
    value, optionSpecs = o.pcOptionMin('SPY', strike, type, expir)
    if strike_value_SPY.get(expir + ' ' + str(strike) + typeAbv):
        anomaly = checkDiff(anomaly, value, optionSpecs, strike, typeAbv, expir)

    strike_value_SPY.setdefault(expir + ' ' + str(strike) + typeAbv, {})['value'] = int(value)
    strike_value_SPY.setdefault(expir + ' ' + str(strike) + typeAbv, {})['volume'] = optionSpecs[1]
    return anomaly


def generate_SPY():
    """calls generateValue_SPY for every strike and expiration and seeks anomalies. Returns anomaly

    :return: extraneous cash flows
    """
    anomaly = {}

    for strike in call_strikes_SPY:
        anomaly = generateValue_SPY(strike, 'call', cal.find_friday(), anomaly)
        anomaly = generateValue_SPY(strike, 'call', monthly_expir, anomaly)
        anomaly = generateValue_SPY(strike, 'call', nextmonth_expir, anomaly)
    for strike in put_strikes_SPY:
        anomaly = generateValue_SPY(strike, 'put', cal.find_friday(), anomaly)
        anomaly = generateValue_SPY(strike, 'put', monthly_expir, anomaly)
        anomaly = generateValue_SPY(strike, 'put', nextmonth_expir, anomaly)
    return anomaly


def checkAnomalies(timestamp, daystamp):
    """Called every 3m to check records against current option values. Reports any anomalies found.

    :param timestamp:
    :return:
    """
    anomaly = generate_SPY()

    if anomaly:
        price = s.tickerPrice('SPY')
        res = "Found large cash movement in past 3 min:\nCurrent SPY price @ " + str(price) + "\n"
        w = csv.writer(open(anomalies_csv, "w"))

        for val in anomaly:
            cost = formatIntForHumans(anomaly.get(val)['diff'])
            curr = str(int(anomaly.get(val)['curr']))
            volume = str(anomaly.get(val)['volume'])
            gamma = str(anomaly.get(val)['gamma'])
            dte = str(anomaly.get(val)['dte'])
            w.write([val, dte, cost, curr, volume, gamma, daystamp, timestamp[2:]])
            res += dte + val[10:] + ': +$' + cost + "   Price: $" + curr + "   Vol: " + volume + "   Gamma: " + gamma + "\n"
        return res
