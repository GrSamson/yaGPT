import os
import json
import time
import requests
import logging
import sqlite3
import time

TOKEN_PATH = "tokens/token.json"
DB_NAME = 'prompts_database.db'
TABLE_NAME = 'user_data'

def create_db(database_name=DB_NAME):
    connection = sqlite3.connect(database_name)
    connection.close()


def execute_query(sql_query, data=None, db_path=DB_NAME):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        if data:
            cursor.execute(sql_query, data)
        else:
            cursor.execute(sql_query)
        connection.commit()


def execute_selection_query(sql_query, data=None, db_path=DB_NAME):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    if data:
        cursor.execute(sql_query, data)
    else:
        cursor.execute(sql_query)
    rows = cursor.fetchall()
    connection.close()
    return rows


def create_table(table_name):
    sql_query = f'CREATE TABLE IF NOT EXISTS {table_name} (user_id INTEGER PRIMARY KEY, genre TEXT, character TEXT, setting TEXT, response TEXT, is_ended INTEGER, last_interaction INTEGER)'
    execute_query(sql_query)


def insert_row(table_name, values, columns=''):
    if columns != '':
        columns = '(' + ', '.join(columns) + ')'
    sql_query = f"INSERT INTO {table_name} {columns} VALUES ({', '.join(['?'] * len(values))})"
    execute_query(sql_query, values)


def prepare_db():
    create_db()
    create_table(TABLE_NAME)


def get_last_interaction(user_id):
    sql_query = f'SELECT last_interaction FROM {TABLE_NAME} WHERE user_id = ?'
    result = execute_selection_query(sql_query, (user_id,))
    if result:
        return result[0][0]
    return None


def is_users_limit(USERS_LIMIT=3):
    sql_query = f'SELECT COUNT(DISTINCT user_id) FROM {TABLE_NAME}'
    result = execute_selection_query(sql_query)
    if result:
        unique_users = result[0][0]
        return unique_users >= USERS_LIMIT
    return False


def get_all_tokens():
    sql_query = f'SELECT DISTINCT user_id, last_interaction FROM {TABLE_NAME}'
    all_tokens = 0
    result = execute_selection_query(sql_query)
    if result:
        for row in result:
            user_id, last_interaction = row
            session_size = get_session_size(user_id, last_interaction)
            all_tokens += session_size
    return all_tokens

def get_session_size(user_id, last_interaction):
    if last_interaction is not None:
        current_time = int(time.time())
        session_size = current_time - last_interaction
        return session_size
    else:
        return 0


def save_user_data(user_id, genre=None, character=None, setting=None, response=None, is_ended=0):
    sql_check_user = "SELECT * FROM user_data WHERE user_id=?"
    user_exists = execute_selection_query(sql_check_user, (user_id,))

    if user_exists:
        sql_update_user = "UPDATE user_data SET genre=?, character=?, setting=?, response=?, is_ended=? WHERE user_id=?"
        execute_query(sql_update_user, (genre, character, setting, response, is_ended, user_id))
    else:
        sql_insert_user = "INSERT INTO user_data (user_id, genre, character, setting, response, is_ended) VALUES (?, ?, ?, ?, ?, ?)"
        execute_query(sql_insert_user, (user_id, genre, character, setting, response, is_ended))

def get_user_data(user_id):
    sql_query = "SELECT * FROM user_data WHERE user_id = ?"
    user_data = execute_selection_query(sql_query, (user_id,))
    return user_data



if __name__ == '__main__':
    prepare_db()
