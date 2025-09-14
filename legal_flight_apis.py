#!/usr/bin/env python3
"""
Legal Flight Price API Integration Examples

Bruker offisielle API-er i stedet for scraping
"""

import requests
import json
from datetime import datetime
import os

class LegalFlightPriceAPI:
    """
    Eksempler på hvordan bruke lovlige API-er for flyprisdata
    """
    
    def __init__(self):
        # API nøkler (sett som miljøvariabler)
        self.amadeus_key = os.getenv('AMADEUS_API_KEY')
        self.skyscanner_key = os.getenv('SKYSCANNER_API_KEY')
    
    def amadeus_flight_search(self, origin, destination, departure_date, adults=1):
        """
        Amadeus API - offisiell flyprissøk
        https://developers.amadeus.com/
        """
        if not self.amadeus_key:
            return {'error': 'AMADEUS_API_KEY ikke satt'}
        
        # Først få access token
        auth_url = "https://api.amadeus.com/v1/security/oauth2/token"
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.amadeus_key,
            'client_secret': os.getenv('AMADEUS_SECRET')
        }
        
        try:
            auth_response = requests.post(auth_url, data=auth_data)
            token = auth_response.json()['access_token']
            
            # Søk etter flyreiser
            search_url = "https://api.amadeus.com/v2/shopping/flight-offers"
            headers = {'Authorization': f'Bearer {token}'}
            params = {
                'originLocationCode': origin,
                'destinationLocationCode': destination,
                'departureDate': departure_date,
                'adults': adults,
                'currencyCode': 'NOK'
            }
            
            response = requests.get(search_url, headers=headers, params=params)
            return response.json()
            
        except Exception as e:
            return {'error': str(e)}
    
    def skyscanner_search(self, origin, destination, departure_date):
        """
        Skyscanner API eksempel
        """
        if not self.skyscanner_key:
            return {'error': 'SKYSCANNER_API_KEY ikke satt'}
        
        # Implementer Skyscanner API kall
        return {'message': 'Skyscanner API implementasjon trengs'}
    
    def momondo_api_example(self):
        """
        Momondo har også API for partnere
        """
        return {'message': 'Momondo API krever partnerskap'}

def demo_legal_apis():
    """Demonstrer lovlige API-er"""
    api = LegalFlightPriceAPI()
    
    print("🔍 Lovlige flyprissøk alternativer:")
    print()
    
    print("1. Amadeus API (https://developers.amadeus.com/)")
    print("   - Omfattende flydata")
    print("   - Gratis tier tilgjengelig")
    print("   - Støtter booking")
    print()
    
    print("2. Skyscanner API (https://skyscanner.net/dataservice)")
    print("   - Populær sammenligningstjeneste")
    print("   - Partner program")
    print()
    
    print("3. Kayak API")
    print("   - Via deres partner program")
    print()
    
    print("4. Norwegian API")
    print("   - Direkte fra flyselskap")
    print()
    
    # Test Amadeus hvis API nøkkel er tilgjengelig
    result = api.amadeus_flight_search('OSL', 'BGO', '2025-09-20')
    print("Amadeus test resultat:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    demo_legal_apis()
