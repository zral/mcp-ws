# Gratis API-alternativer for Travel Weather Agent

## Oversikt

Travel Weather Agent bruker nå gratis API-alternativer istedet for Google Maps API for å redusere kostnader og avhengigheter:

### Før (Google Maps):
- ❌ Google Geocoding API - Koster penger etter gratis kvote
- ❌ Google Directions API - Koster penger etter gratis kvote
- ❌ Krever registrering og kredittkort

### Nå (Gratis alternativer):
- ✅ **Nominatim** (OpenStreetMap) - Helt gratis geocoding
- ✅ **OpenRouteService** - Gratis tier med 2000 forespørsler/dag
- ✅ **Fallback beregninger** - Luftlinje når API ikke er tilgjengelig

## API-er som brukes

### 1. Nominatim (OpenStreetMap Geocoding)

**Hva:** Konverterer stedsnavn til koordinater
**Kostnad:** Helt gratis
**Begrensninger:** Maks 1 forespørsel per sekund
**Dokumentasjon:** https://nominatim.org/

**Eksempel:**
```http
GET https://nominatim.openstreetmap.org/search?q=Oslo,Norway&format=json
```

**Fordeler:**
- Ingen API nøkkel nødvendig
- Basert på crowdsourced OpenStreetMap data
- Høy kvalitet data for de fleste steder

**Ulemper:**
- Strengere rate limiting enn Google
- Kan være mindre nøyaktig for obskure steder

### 2. OpenRouteService

**Hva:** Beregner ruter mellom punkter
**Kostnad:** Gratis tier med 2000 forespørsler/dag
**Registrering:** Valgfri (øker grensen til 2000/dag)
**Dokumentasjon:** https://openrouteservice.org/

**Eksempel:**
```http
POST https://api.openrouteservice.org/v2/directions/driving-car
{
  "coordinates": [[8.681495,49.41461],[8.687872,49.420318]]
}
```

**Fordeler:**
- Profesjonell rute-beregning
- Støtter bil, sykkel, gåing
- Detaljerte instruksjoner
- Kan brukes uten API nøkkel (begrenset)

**Ulemper:**
- Daglig grense på 2000 forespørsler
- Mindre trafikk-data enn Google

### 3. Fallback beregninger

Når API-ene ikke er tilgjengelige, brukes:
- **Haversine formula** for luftlinje avstand
- **Estimerte reisetider** basert på transportmåte
- **Grunnleggende koordinat-informasjon**

## Implementasjon

### Geocoding med Nominatim

```python
async def geocode_location(location: str) -> tuple[float, float] | None:
    async with httpx.AsyncClient() as client:
        url = f"{NOMINATIM_API_BASE}/search"
        params = {
            "q": location,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }
        headers = {
            "User-Agent": "TravelWeatherAgent/1.0"  # Kreves av Nominatim
        }
        
        response = await client.get(url, params=params, headers=headers)
        data = response.json()
        
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
        return None
```

### Ruting med OpenRouteService

```python
async def get_route_openroute(origin_coords, destination_coords, profile="driving-car"):
    async with httpx.AsyncClient() as client:
        url = f"{OPENROUTE_API_BASE}/directions/{profile}"
        
        data = {
            "coordinates": [
                [origin_coords[1], origin_coords[0]],      # [lon, lat]
                [destination_coords[1], destination_coords[0]]
            ],
            "format": "json",
            "instructions": True,
            "language": "no"
        }
        
        headers = {"Content-Type": "application/json"}
        
        # Legg til API nøkkel hvis tilgjengelig
        if OPENROUTE_API_KEY:
            headers["Authorization"] = OPENROUTE_API_KEY
        
        response = await client.post(url, json=data, headers=headers)
        return response.json()
```

### Fallback beregninger

```python
async def get_route_fallback(origin: str, destination: str) -> str:
    origin_coords = await geocode_location(origin)
    dest_coords = await geocode_location(destination)
    
    # Beregn luftlinje avstand med Haversine formula
    distance_km = haversine(origin_coords, dest_coords)
    
    # Estimerte reisetider
    driving_time = distance_km / 80  # 80 km/t
    walking_time = distance_km / 5   # 5 km/t
    
    return f"Luftlinje avstand: {distance_km:.1f} km\\nEstimert kjøretid: {driving_time:.1f} timer"
```

## Konfigurasjon

### Miljøvariabler

```bash
# Nødvendig
OPENWEATHER_API_KEY=your-key-here

# Valgfri (øker OpenRouteService grenser)
OPENROUTE_API_KEY=your-key-here

# Ikke lenger nødvendig
# GOOGLE_API_KEY=...
```

### Docker Compose

```yaml
environment:
  - OPENWEATHER_API_KEY=${OPENWEATHER_API_KEY}
  - OPENROUTE_API_KEY=${OPENROUTE_API_KEY}  # Valgfri
```

## Ytelse og begrensninger

### Rate Limiting

| API | Gratis grense | Med API nøkkel |
|-----|---------------|----------------|
| Nominatim | 1 req/sek | Samme |
| OpenRouteService | 40 req/dag | 2000 req/dag |
| Fallback | Ubegrenset | Ubegrenset |

### Fallback strategi

1. **Prøv OpenRouteService** - For nøyaktige ruter
2. **Hvis det feiler** → Bruk fallback beregninger
3. **Alltid** → Bruk Nominatim for geocoding

### Kvalitet sammenlignet med Google

| Funksjon | Google Maps | Våre alternativer | Kvalitet |
|----------|------------|-------------------|----------|
| Geocoding | Høy | Høy (Nominatim) | 95% |
| Ruting | Høy | Middels-Høy (OpenRoute) | 85% |
| Trafikk data | Excellent | Ingen | 0% |
| Kostnader | Høy | Gratis | ∞% bedre |

## Fordeler med endringen

✅ **Ingen kostnader** - Alle API-er er gratis
✅ **Ingen kredittkort** - Ikke behov for betalingsmetode
✅ **Open source** - Basert på åpne data og tjenester
✅ **Robust fallback** - Fungerer selv når API-er er nede
✅ **Enklere oppsett** - Færre API nøkler å konfigurere

## Ulemper

⚠️ **Rate limiting** - Strengere grenser enn Google
⚠️ **Mindre trafikk-data** - Ingen sanntids trafikk informasjon  
⚠️ **Potensielt lavere kvalitet** - For obskure destinasjoner

## Migrering

For å bytte fra Google Maps til de nye API-ene:

1. **Fjern gammel konfigurasjon:**
   ```bash
   # Ikke lenger nødvendig
   unset GOOGLE_API_KEY
   ```

2. **Legg til ny konfigurasjon (valgfri):**
   ```bash
   export OPENROUTE_API_KEY="your-key-here"
   ```

3. **Rebuild Docker containers:**
   ```bash
   docker-compose build
   docker-compose up
   ```

Systemet vil automatisk fungere uten OpenRouteService API nøkkel, men med fallback beregninger.
