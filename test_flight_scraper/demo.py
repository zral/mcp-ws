"""
Demo script that shows how the Google Flights scraper would work
without actually hitting Google's servers
"""

import json
from datetime import datetime
from google_flights_scraper import SearchParameters, FlightData


def create_demo_flight_data():
    """Create demo flight data to simulate scraper results"""
    demo_flights = [
        FlightData(
            airline="SAS",
            departure_time="08:30",
            arrival_time="09:45",
            duration="1h 15m",
            stops="Nonstop",
            price="kr 1,245",
            co2_emissions="45 kg CO₂",
            emissions_variation="-12% emissions"
        ),
        FlightData(
            airline="Norwegian",
            departure_time="10:15",
            arrival_time="11:30", 
            duration="1h 15m",
            stops="Nonstop",
            price="kr 985",
            co2_emissions="42 kg CO₂",
            emissions_variation="-18% emissions"
        ),
        FlightData(
            airline="Lufthansa",
            departure_time="14:20",
            arrival_time="17:40",
            duration="3h 20m",
            stops="1 stop",
            price="kr 1,580",
            co2_emissions="78 kg CO₂",
            emissions_variation="+15% emissions"
        ),
        FlightData(
            airline="KLM",
            departure_time="16:45",
            arrival_time="20:10",
            duration="3h 25m", 
            stops="1 stop",
            price="kr 1,420",
            co2_emissions="81 kg CO₂",
            emissions_variation="+22% emissions"
        ),
        FlightData(
            airline="SAS",
            departure_time="19:30",
            arrival_time="20:45",
            duration="1h 15m",
            stops="Nonstop",
            price="kr 1,890",
            co2_emissions="45 kg CO₂",
            emissions_variation="-12% emissions"
        )
    ]
    return demo_flights


def demo_scraper_output():
    """Demonstrate what the scraper output would look like"""
    print("=" * 80)
    print("GOOGLE FLIGHTS SCRAPER DEMO")
    print("=" * 80)
    print()
    
    # Demo search parameters
    params = SearchParameters(
        departure="OSL",
        destination="CPH", 
        departure_date="2025-01-15",
        ticket_type="One way"
    )
    
    print(f"Search Parameters:")
    print(f"  From: {params.departure}")
    print(f"  To: {params.destination}")
    print(f"  Date: {params.departure_date}")
    print(f"  Type: {params.ticket_type}")
    print()
    
    # Generate demo flight data
    flights = create_demo_flight_data()
    
    print(f"Found {len(flights)} flights:")
    print("=" * 60)
    
    for i, flight in enumerate(flights, 1):
        print(f"\nFlight {i}:")
        print(f"  ✈️  Airline: {flight.airline}")
        print(f"  🛫 Departure: {flight.departure_time}")
        print(f"  🛬 Arrival: {flight.arrival_time}")
        print(f"  ⏱️  Duration: {flight.duration}")
        print(f"  🔄 Stops: {flight.stops}")
        print(f"  💰 Price: {flight.price}")
        print(f"  🌍 CO₂: {flight.co2_emissions}")
        print(f"  📊 Emissions: {flight.emissions_variation}")
    
    # Demo saving to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"demo_flight_results_{params.departure}_{params.destination}_{timestamp}.json"
    
    output_data = {
        "search_parameters": {
            "departure": params.departure,
            "destination": params.destination,
            "departure_date": params.departure_date,
            "return_date": params.return_date,
            "ticket_type": params.ticket_type
        },
        "timestamp": timestamp,
        "flights": [
            {
                "airline": flight.airline,
                "departure_time": flight.departure_time,
                "arrival_time": flight.arrival_time,
                "duration": flight.duration,
                "stops": flight.stops,
                "price": flight.price,
                "co2_emissions": flight.co2_emissions,
                "emissions_variation": flight.emissions_variation
            }
            for flight in flights
        ]
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Demo results saved to: {filename}")
    print()
    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print()
    print("This demonstrates what the actual scraper would return.")
    print("To run the real scraper (against Google Flights):")
    print("  python google_flights_scraper.py")
    print()
    print("⚠️  Remember: Use responsibly and respect Terms of Service!")


if __name__ == "__main__":
    demo_scraper_output()