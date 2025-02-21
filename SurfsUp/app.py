# Import the dependencies
from flask import Flask, jsonify, request, abort
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy.ext.automap import automap_base
import os

#################################################
# Database Setup
#################################################

# Verify that the database file exists
db_path = "/Users/GURU/Desktop/sqlalchemy-challenge/SurfsUp/Resources/hawaii.sqlite"
if not os.path.exists(db_path):
    raise FileNotFoundError(f"Database file not found: {db_path}")

# Create engine to the correct SQLite file
engine = create_engine(f"sqlite:///{db_path}")  # Use three slashes for relative, four for absolute paths

# Reflect the existing database into a new model
Base = automap_base()
Base.prepare(autoload_with=engine)  # Updated per SQLAlchemy 2.0 changes

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def home():
    """List all available API routes."""
    return (
        "Welcome to the Climate API!<br/>"
        "Available Routes:<br/>"
        "<br/>"
        "/api/v1.0/precipitation - Last 12 months of precipitation data<br/>"
        "/api/v1.0/stations - List of weather stations<br/>"
        "/api/v1.0/tobs - Temperature observations of the most active station for the last year<br/>"
        "/api/v1.0/<start> - Min, Avg, and Max temperatures from the start date<br/>"
        "/api/v1.0/<start>/<end> - Min, Avg, and Max temperatures for a date range<br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return last 12 months of precipitation data as JSON."""
    session = Session(engine)
    try:
        # Get the last date and calculate one year back
        last_date = session.query(func.max(Measurement.date)).scalar()
        last_date = datetime.strptime(last_date, "%Y-%m-%d")
        year_ago = last_date - timedelta(days=365)

        # Query precipitation data for the last year
        results = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= year_ago).all()
        precipitation_data = {date: prcp for date, prcp in results}
    finally:
        session.close()

    return jsonify(precipitation_data)

@app.route("/api/v1.0/stations")
def stations():
    """Return a list of all weather stations."""
    session = Session(engine)
    try:
        results = session.query(Station.station).all()
        station_list = [station[0] for station in results]
    finally:
        session.close()

    return jsonify(station_list)

@app.route("/api/v1.0/tobs")
def tobs():
    """Return temperature observations of the most active station for the previous year."""
    session = Session(engine)
    try:
        # Find the most active station
        most_active_station = session.query(Measurement.station).group_by(Measurement.station).\
            order_by(func.count(Measurement.station).desc()).first()[0]

        # Get the last date and calculate one year back
        last_date = session.query(func.max(Measurement.date)).scalar()
        last_date = datetime.strptime(last_date, "%Y-%m-%d")
        year_ago = last_date - timedelta(days=365)

        # Query temperature observations
        results = session.query(Measurement.date, Measurement.tobs).\
            filter(Measurement.station == most_active_station).\
            filter(Measurement.date >= year_ago).all()

        temperature_data = [{"date": date, "temperature": tobs} for date, tobs in results]
    finally:
        session.close()

    return jsonify(temperature_data)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_range(start, end=None):
    """Return min, avg, and max temperature from a start date or within a date range."""
    session = Session(engine)
    try:
        # Convert string dates to proper format
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d")
        except ValueError:
            print(f"Invalid start date format: {start}")
            abort(400, description="Invalid start date format. Please use YYYY-MM-DD.")

        if end:
            try:
                end_date = datetime.strptime(end, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid end date format: {end}")
                abort(400, description="Invalid end date format. Please use YYYY-MM-DD.")
        else:
            end_date = datetime.utcnow()  # Set end_date to current date if not provided

        # Query temperature statistics
        query = session.query(
            func.min(Measurement.tobs),
            func.avg(Measurement.tobs),
            func.max(Measurement.tobs)
        ).filter(Measurement.date >= start_date).filter(Measurement.date <= end_date)

        results = query.all()
        
        temp_data = {
            "TMIN": results[0][0],
            "TAVG": results[0][1],
            "TMAX": results[0][2]
        }
    finally:
        session.close()

    return jsonify(temp_data)

if __name__ == "__main__":
    app.run(debug=True)
