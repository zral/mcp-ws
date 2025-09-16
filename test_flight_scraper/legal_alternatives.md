# Legale alternativer til flight scraping

Før du bruker webscraping, vurder disse offisielle API-ene:

## Offisielle Flight API-er

### 1. Google Travel Partner API
- **Offisiell API fra Google**
- Krever partnerskap med Google
- Tilgang til samme data som Google Flights
- Link: https://developers.google.com/travel/

### 2. Amadeus for Developers
- **Gratis tier tilgjengelig**
- Omfattende flydata og booking
- RESTful API
- Link: https://developers.amadeus.com/

### 3. Skyscanner API
- **Partner API**
- Populær flight comparison service
- Link: https://partners.skyscanner.net/

### 4. Travelport Universal API
- **Profesjonell travel API**
- Tilgang til GDS-systemer
- Link: https://developer.travelport.com/

### 5. Sabre APIs
- **GDS-leverandør**
- Omfattende travel data
- Link: https://developer.sabre.com/

## Hvorfor bruke offisielle API-er?

### Fordeler
- ✅ Lovlig og i henhold til bruksvilkår
- ✅ Stabil og pålitelig data
- ✅ Støtte og dokumentasjon
- ✅ Rate limiting og SLA
- ✅ Strukturerte data

### Ulemper med scraping
- ❌ Kan bryte bruksvilkår
- ❌ IP-blokkering
- ❌ Ustabile CSS-selektorer
- ❌ CAPTCHA-utfordringer
- ❌ Etiske bekymringer

## Eksempel: Amadeus API

```python
import requests

# Autentisering
auth_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
auth_data = {
    "grant_type": "client_credentials",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
}

# Få access token
token_response = requests.post(auth_url, data=auth_data)
access_token = token_response.json()["access_token"]

# Søk etter flyvninger
flights_url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
headers = {"Authorization": f"Bearer {access_token}"}

params = {
    "originLocationCode": "OSL",
    "destinationLocationCode": "CPH",
    "departureDate": "2025-01-15",
    "adults": 1
}

response = requests.get(flights_url, headers=headers, params=params)
flights = response.json()
```

## Konklusjon

For produksjonsbruk, bruk alltid offisielle API-er når de er tilgjengelige. 
Webscraping bør kun brukes for:
- Utdanning og læring
- Testing og prototyping
- Når ingen offisielle API-er finnes
- Med respekt for nettsiders bruksvilkår