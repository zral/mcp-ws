#!/usr/bin/env python3
"""
Flight Price Scraper

ADVARSEL: Dette skriptet er kun for utdanningsformål.
Sjekk alltid nettsidenes robots.txt og Terms of Service før bruk.
"""

import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime, timedelta
import json
from urllib.parse import urlencode
import logging

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlightScraper:
    def __init__(self):
        # Simuler en ekte nettleser
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def search_google_flights(self, origin, destination, departure_date, return_date=None):
        """
        Forsøk på å hente flypris-data fra Google Flights
        
        NB: Google bruker JavaScript og avansert anti-bot beskyttelse,
        så dette vil sannsynligvis ikke fungere i praksis.
        """
        try:
            # Bygg URL for Google Flights søk
            params = {
                'hl': 'en',
                'curr': 'NOK',
                'tfs': f'CBwQAhooEgoyMDI1LTA5LTE0agcIARIDT1NMcgcIARIDQkdPGhIKCjIwMjUtMDktMTRyBwgBEgNPU0w'
            }
            
            url = f"https://www.google.com/travel/flights?" + urlencode(params)
            
            logger.info(f"Forsøker å hente data fra: {url}")
            
            # Legg til tilfeldig forsinkelse
            time.sleep(random.uniform(2, 5))
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Google Flights bruker kompleks JavaScript, så HTML parsing er begrenset
                price_elements = soup.find_all(text=lambda text: text and 'kr' in text.lower())
                
                prices = []
                for price_text in price_elements:
                    # Prøv å ekstrahere priser
                    if any(char.isdigit() for char in price_text):
                        prices.append(price_text.strip())
                
                return {
                    'origin': origin,
                    'destination': destination,
                    'departure_date': departure_date,
                    'return_date': return_date,
                    'prices_found': prices[:10],  # Første 10 funn
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error(f"HTTP {response.status_code}: {response.reason}")
                return {'status': 'error', 'message': f'HTTP {response.status_code}'}
                
        except Exception as e:
            logger.error(f"Feil ved scraping: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def search_alternative_sites(self, origin, destination, departure_date):
        """
        Alternativ tilnærming - søk på andre flyprissider
        """
        sites_to_try = [
            {
                'name': 'Norwegian',
                'url': 'https://www.norwegian.com',
                'method': self._scrape_norwegian
            },
            {
                'name': 'SAS',
                'url': 'https://www.sas.no',
                'method': self._scrape_sas
            }
        ]
        
        results = []
        for site in sites_to_try:
            try:
                logger.info(f"Prøver {site['name']}...")
                result = site['method'](origin, destination, departure_date)
                results.append(result)
                
                # Vær høflig - vent mellom forespørsler
                time.sleep(random.uniform(3, 7))
                
            except Exception as e:
                logger.error(f"Feil med {site['name']}: {e}")
                results.append({
                    'site': site['name'],
                    'status': 'error',
                    'message': str(e)
                })
        
        return results
    
    def _scrape_norwegian(self, origin, destination, departure_date):
        """Eksempel for Norwegian.com"""
        # Dette er kun et eksempel - faktisk implementasjon krever
        # detaljert analyse av nettsiden
        url = "https://www.norwegian.com/no/"
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return {
                    'site': 'Norwegian',
                    'status': 'success',
                    'message': 'Nettsiden lastet, men krever JavaScript for booking'
                }
        except:
            pass
        
        return {'site': 'Norwegian', 'status': 'error', 'message': 'Kunne ikke nå nettsiden'}
    
    def _scrape_sas(self, origin, destination, departure_date):
        """Eksempel for SAS.no"""
        return {'site': 'SAS', 'status': 'error', 'message': 'Implementasjon ikke komplett'}

def main():
    """Hovedfunksjon for testing"""
    scraper = FlightScraper()
    
    # Test parametere
    origin = "OSL"
    destination = "BGO"
    departure_date = "2025-09-20"
    
    print(f"Søker flypriser fra {origin} til {destination} den {departure_date}")
    print("=" * 60)
    
    # Prøv Google Flights (vil sannsynligvis feile)
    google_results = scraper.search_google_flights(origin, destination, departure_date)
    print("Google Flights resultater:")
    print(json.dumps(google_results, indent=2, ensure_ascii=False))
    print()
    
    # Prøv alternative nettsider
    alt_results = scraper.search_alternative_sites(origin, destination, departure_date)
    print("Alternative nettsider:")
    print(json.dumps(alt_results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    print("🚨 ADVARSEL: Dette skriptet er kun for utdanningsformål!")
    print("Sjekk alltid robots.txt og Terms of Service før bruk.")
    print("Moderne flyprissider bruker JavaScript og anti-bot beskyttelse.")
    print()
    
    response = input("Fortsett likevel? (j/n): ")
    if response.lower() in ['j', 'ja', 'y', 'yes']:
        main()
    else:
        print("Avbryter...")
