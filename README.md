# Fun with sensors  
### Video Demo:  <URL HERE>
### Description:
**Fun with Sensors** is a web application that collects readings from an Enviro+ air quality sensor connected to a Raspberry Pi Zero single-board computer, which measures the air quality in a room. The Raspberry Pi transmits data to a MySQL database on PythonAnywhere using a Python script to read the sensor data, access the database and write the values into a table. This web application, made with Flask and Python, then accesses the MySQL database and renders a few graphs to better illustrate the readings.

### File list:
#### application.py
The code for the main web application, based on CS50's finance web application. This file imports scripts from MySQLdb, Flask, werkzeug, helpers. It generates the flask frontend, connects to the MySQL database and reads out data from the tables in the Readings and Charts menus. To avoid connection errors, application.py connects to the database using the function mydb.disconnectSafeConnect (see mydb.py), reading user authentication details from a separate mysql config file for added safety. The cursor class returns values as a dictionary.

The latest readings in the Charts section are rendered using chart.js. Application.py further allows the user to register a username and password (for increased security), log into sessions, change the password and show a summary figure of the workflow. Login is required for all sections of the website.

#### helpers.py
Based on CS50's finance web application this script provides two additional functions apology and login_required.

#### mydb.py
A script to ensure that the MySQL database does not disconnect with an error between connections and re-establishes the connection automatically after a timeout.

#### /static/
This folder contains the css style file, which is losely based on the CS50 stylesheet with some additions. Mainly bootstrap was used to design the frontend. The static folder further contains the Chart.min.js script that renders the Graphs, which was taken from and modified according to the chart.js documentation. A favicon and the setup figure have also been included.

#### /templates/
Contains the html files to generate the website, also losely based on what I have learned during CS50's week 7-9. Readings.html and chart.html contain the code to display sensor data from the database in a table and the containers for chart.js.

### Working model:
A working model that is still connected to an active sensor can be found [on my PythonAnywhere site](https://xysmalobia.pythonanywhere.com/).
