import mysql.connector
from database import get_connection

def get_make_id(make_name):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT make_id FROM vehiclemake WHERE make = %s", (make_name,))
    make_id = cursor.fetchone()
    conn.close()
    return make_id


def get_model_id(model_name):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT model_id FROM vehiclemodellist WHERE model = %s", (model_name,))
    model_id = cursor.fetchone()
    conn.close()
    return model_id


def get_model_name(make_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT model FROM vehiclemodellist WHERE make_id = %s", (make_id,))
    model_id = cursor.fetchone()
    conn.close()
    return model_id


def get_cities_by_state(state_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT city_name, city_id FROM cities WHERE state_id = %s", (state_id,))
    city = cursor.fetchone()
    conn.close()
    return city


def get_area_id(area_name):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT id FROM area WHERE area = %s", (area_name,))
    area_id = cursor.fetchone()
    conn.close()
    return area_id