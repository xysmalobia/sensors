#!/usr/bin/python3

import mysql.connector
import sshtunnel
import ltr559
import time
import mydb
import MySQLdb
import MySQLdb.cursors
import configparser

from datetime import datetime
from enviroplus import gas
from pms5003 import PMS5003, ReadTimeoutError
from smbus import SMBus
from bme280 import BME280
from subprocess import PIPE, Popen, check_output
from mysql.connector import Error 
from mysql.connector import errorcode

try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559
    ltr559 = LTR559()
except ImportError:
    import ltr559

print("""This script reads temperature, pressure, humidity, PM1, PM2.5, 
and PM10 particle data from Enviro plus and sends them to a MySQL database
at PythonAnywhere.

Press Ctrl+C to exit!

""")

# set interval between readings
period = 500

# get mysql config details for authentification
cfg = configparser.ConfigParser()
cfg.read('.my.cnf') 

user = cfg["mysql"]["user"]
password = cfg["mysql"]["password"]
ssh_username = cfg['mysql']['ssh_username']
ssh_password = cfg['mysql']['ssh_password']
host = cfg['mysql']['host']
database = cfg['mysql']['database']

# connecting to the different sensors
pms5003 = PMS5003()
bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)

# get CPU temperature to use for compensation
def get_cpu_temperature():
    process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE, universal_newlines=True)
    output, _error = process.communicate()
    return float(output[output.index('=') + 1:output.rindex("'")])

def main():
    while True:

        # read out current time and format
        now = datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")

        # connecting to the remote mysql database via sshtunnel
        sshtunnel.SSH_TIMEOUT = 15.0
        sshtunnel.TUNNEL_TIMEOUT = 15.0

        with sshtunnel.SSHTunnelForwarder(
            ('ssh.pythonanywhere.com'), ssh_username=ssh_username, ssh_password=ssh_password,
            remote_bind_address=(host, 3306)
        ) as tunnel:
            connection = mydb.disconnectSafeConnect(
                user=user, password=password,
                host='127.0.0.1', port=tunnel.local_bind_port,
                database=database,
            )
            print("Connection established...\n")

            try:
                # collecting data from the particle sensor
                pms5003 = PMS5003()
                readings = pms5003.read()
                pm1 = readings.pm_ug_per_m3(1.0)
                pm2 = readings.pm_ug_per_m3(2.5)
                pm10 = readings.pm_ug_per_m3(10)

                # collecting data from the gas sensor
                greadings = gas.read_all()
                gasr = greadings.reducing
                gaso = greadings.oxidising
                gasn = greadings.nh3

                # collecting data from the bme280 sensor
                humidity = round(bme280.get_humidity())
                pressure = round(bme280.get_pressure())
                
                # collecting data from lumenosity sensor
                lumenosity = ltr559.get_lux()
                
                # calculate temperature using compensation factor
                comp_factor = 2.25
                cpu_temp = get_cpu_temperature()
                raw_temp = bme280.get_temperature()
                temperature = float(raw_temp - ((cpu_temp - raw_temp) / comp_factor))

                if temperature is not None and humidity is not None:
                    if humidity < 75:
                        try:
                            # enter value into mysql database
                            cursor = connection.cursor()
                            cursor.execute("CREATE TABLE IF NOT EXISTS sensor (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, temperature FLOAT, humidity INT, pressure INT, pm1 INT, pm2 INT, pm10 INT, lumenosity INT, gasr FLOAT, gaso FLOAT, gasn FLOAT, date DATETIME)")

                            insert_stmt = ("INSERT INTO sensor(temperature, humidity, pressure, pm1, pm2, pm10, lumenosity, gasr, gaso, gasn, date) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
                            data = (temperature, humidity, pressure, pm1, pm2, pm10, lumenosity, gasr, gaso, gasn, dt_string)

                            cursor.execute(insert_stmt, data)
                            connection.commit()
                            print("Record inserted.")                                

                        except mysql.connector.Error as error:
                            print("Database Update Failed!: {}".format(error)) 
                            connection.rollback()

                    else:
                        print("Outlier... try again")
                        continue

                else:
                    print("Failed to get readings. Try again.")
                    continue

                time.sleep(period)

            except ReadTimeoutError:
                pms5003 = PMS5003()
                continue


main()

