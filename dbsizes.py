#!/usr/bin/python3
# Display mysql database sizes with total
# Requirements: python 3.6 or later, python3-mysqlclient, mysql connection info in local file '.my.cnf'
# Author: John McNally, jmcnally@acm.org, 9/26/2023

import configparser
import MySQLdb
import os
import sys

DBSIZES_SQL = 'SELECT table_schema AS name, ROUND(SUM(data_length + index_length) / 1024 / 1024, 0) AS size FROM information_schema.tables GROUP BY table_schema'
total = 0

try:
    # Read MySQL connection info from file '.my.cnf'
    config_object = configparser.ConfigParser()
    with open(".my.cnf","r") as file_object:
        config_object.read_file(file_object)
        user = config_object.get("mysql","user")
        host = config_object.get("mysql","host")
        password = config_object.get("mysql","password")
        password = password.replace("'", "")

    # Connect to the database and execute the SQL query
    connection = MySQLdb.connect(host=host,user=user,password=password)
    cursor = connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(DBSIZES_SQL)
    dbsizes = cursor.fetchall()

    # Print the formatted output
    print("Size (MB) Name")
    for db in dbsizes:
        print(f"{db['size']:>8,}  {db['name']}")
        total += db['size']
    print("-----------------------------")
    print(f"{total:>8,}  TOTAL")
except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(f"ERROR: {e}, type: {exc_type}, file: {fname}, line: {exc_tb.tb_lineno}")
