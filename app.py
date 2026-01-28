from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pathlib import Path
from remote import remote, E2B
from dotenv import load_dotenv
from io import StringIO
import traceback
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from typing import Literal
import random


load_dotenv(".env.local")

app = FastAPI(title="Remote Code Execution Demo")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


class CodeInput(BaseModel):
    code: str


class CodeOutput(BaseModel):
    output: str
    error: str | None = None


class Flight(BaseModel):
    """Model representing a flight with comprehensive metadata."""

    flight_number: str = Field(description="Flight number (e.g., 'AA123')")
    airline: str = Field(description="Airline name")

    # Origin and destination
    origin: str = Field(description="Departure city")
    destination: str = Field(description="Arrival city")
    origin_airport: str = Field(description="Origin airport code (e.g., 'JFK')")
    destination_airport: str = Field(description="Destination airport code (e.g., 'LAX')")

    # Timing
    departure_time: datetime = Field(description="Scheduled departure time")
    arrival_time: datetime = Field(description="Scheduled arrival time")
    duration_minutes: int = Field(description="Flight duration in minutes")

    # Pricing and availability
    price: float = Field(description="Ticket price in USD")
    available_seats: int = Field(description="Number of available seats", ge=0)
    cabin_class: Literal["economy", "premium_economy", "business", "first"] = Field(
        description="Cabin class"
    )

    # Aircraft and gate info
    aircraft_type: str = Field(description="Aircraft model (e.g., 'Boeing 737')")
    gate: str | None = Field(default=None, description="Departure gate (if assigned)")
    terminal: str | None = Field(default=None, description="Departure terminal")

    # Amenities
    has_wifi: bool = Field(default=False, description="WiFi available")
    has_meals: bool = Field(default=False, description="Meal service included")
    baggage_allowance: int = Field(description="Checked baggage allowance in kg")


@app.get("/")
async def index():
    """Serve the main HTML page."""
    return FileResponse("static/index.html")


async def get_flights() -> list[Flight]:
    """Generate 100 random flights across 5 cities over the next 7 days."""

    # Define cities with their airport codes
    cities = [
        ("New York", "JFK"),
        ("Los Angeles", "LAX"),
        ("Chicago", "ORD"),
        ("Miami", "MIA"),
        ("Seattle", "SEA"),
    ]

    # Airlines and their common aircraft
    airlines_aircraft = {
        "American Airlines": ["Boeing 737", "Boeing 777", "Airbus A321"],
        "Delta": ["Boeing 737", "Airbus A320", "Boeing 757"],
        "United": ["Boeing 737", "Boeing 787", "Airbus A319"],
        "Southwest": ["Boeing 737"],
        "JetBlue": ["Airbus A320", "Airbus A321"],
    }

    cabin_classes: list[Literal["economy", "premium_economy", "business", "first"]] = [
        "economy",
        "premium_economy",
        "business",
        "first",
    ]

    flights = []
    now = datetime.now()

    # Add a specific "needle in a haystack" flight for demonstration
    # LA to NYC, business class, between 10:30am and 2pm, with wifi
    needle_departure = now.replace(hour=11, minute=30, second=0, microsecond=0) + timedelta(days=3)
    needle_duration = 300  # 5 hours
    needle_arrival = needle_departure + timedelta(minutes=needle_duration)

    needle_flight = Flight(
        flight_number="AA1234",
        airline="American Airlines",
        origin="Los Angeles",
        destination="New York",
        origin_airport="LAX",
        destination_airport="JFK",
        departure_time=needle_departure,
        arrival_time=needle_arrival,
        duration_minutes=needle_duration,
        price=1250.00,
        available_seats=8,
        cabin_class="business",
        aircraft_type="Boeing 777",
        gate="B15",
        terminal="4",
        has_wifi=True,
        has_meals=True,
        baggage_allowance=32,
    )
    flights.append(needle_flight)

    for _ in range(100):
        # Random origin and destination (ensure they're different)
        origin, destination = random.sample(cities, 2)
        origin_city, origin_airport = origin
        dest_city, dest_airport = destination

        # Random airline and aircraft
        airline = random.choice(list(airlines_aircraft.keys()))
        aircraft = random.choice(airlines_aircraft[airline])

        # Random departure time in the next 7 days
        days_ahead = random.randint(0, 7)
        hour = random.randint(5, 23)  # Flights between 5 AM and 11 PM
        minute = random.choice([0, 15, 30, 45])
        departure = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(
            days=days_ahead
        )

        # Flight duration based on distance (rough estimate)
        duration = random.randint(120, 360)  # 2-6 hours
        arrival = departure + timedelta(minutes=duration)

        # Generate flight number
        airline_code = airline[:2].upper()
        flight_num = f"{airline_code}{random.randint(100, 9999)}"

        # Random pricing based on cabin class
        cabin = random.choice(cabin_classes)
        base_price = {
            "economy": random.uniform(150, 400),
            "premium_economy": random.uniform(400, 700),
            "business": random.uniform(800, 1500),
            "first": random.uniform(1500, 3000),
        }[cabin]

        # Random gate and terminal (sometimes not assigned yet)
        gate = (
            f"{random.choice('ABCDEFG')}{random.randint(1, 30)}" if random.random() > 0.3 else None
        )
        terminal = str(random.randint(1, 5)) if random.random() > 0.2 else None

        flight = Flight(
            flight_number=flight_num,
            airline=airline,
            origin=origin_city,
            destination=dest_city,
            origin_airport=origin_airport,
            destination_airport=dest_airport,
            departure_time=departure,
            arrival_time=arrival,
            duration_minutes=duration,
            price=round(base_price, 2),
            available_seats=random.randint(0, 50),
            cabin_class=cabin,
            aircraft_type=aircraft,
            gate=gate,
            terminal=terminal,
            has_wifi=random.random() > 0.3,  # 70% have WiFi
            has_meals=cabin in ["business", "first"]
            or duration > 180,  # Long flights or premium cabins
            baggage_allowance=23 if cabin in ["economy", "premium_economy"] else 32,
        )

        flights.append(flight)

    return flights


@remote(
    local_project_root=Path(__file__).parent,
    backend=E2B(template_prefix="test-remote-box1", template_version="0_1_7"),
    timeout_millis=10_000,  # 10 seconds
)
async def execute_remote_code(input: CodeInput) -> CodeOutput:
    """Execute user-provided code in a sandboxed environment."""
    output_buffer = StringIO(newline="")

    with redirect_stdout(output_buffer):
        try:
            # Create a namespace with explicitly allowed functions/variables
            namespace = {
                "get_flights": get_flights,
                # Add other safe functions/modules here as needed
                # "requests": requests,
                # "json": json,
            }

            # Wrap the user's code in an async function
            wrapped_code = "async def __async_exec():\n"
            for line in input.code.split("\n"):
                wrapped_code += f"    {line}\n"

            # Execute to define the async function in the namespace
            exec(wrapped_code, namespace)

            # Call the function and await the result
            await namespace["__async_exec"]()
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return CodeOutput(output=output_buffer.getvalue(), error=error_msg)

    return CodeOutput(output=output_buffer.getvalue(), error=None)


@app.post("/execute", response_model=CodeOutput)
async def execute_code(request: CodeInput):
    """Execute Python code in a remote sandboxed environment."""
    try:
        return await execute_remote_code(request)
    except Exception as e:
        return CodeOutput(output="", error=f"Execution failed: {type(e).__name__}: {str(e)}")
