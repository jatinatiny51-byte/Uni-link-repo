from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import mysql.connector

app = FastAPI()

# MySQL Connection

connection = mysql.connector.connect(
    host='localhost',
    user='your_username',
    password='your_password',
    database='your_database',
    autocommit=True
)

@app.on_event("startup")
def startup_event():
    # Code to load data or perform initialization
    pass

@app.on_event("shutdown")
def shutdown_event():
    connection.close()

# Frontend loading
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return "<html><body><h1>Hello, FastAPI</h1></body></html>"

# Backend API example
@app.get("/api/data")
async def read_data():
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM your_table")
    results = cursor.fetchall()
    return results