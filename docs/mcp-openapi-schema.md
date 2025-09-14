# MCP Server OpenAPI Schema

## OpenAPI 3.0 Specification

```yaml
openapi: 3.0.3
info:
  title: Travel Weather MCP Server API
  description: Model Context Protocol server for travel planning with weather data
  version: 1.0.0
  contact:
    name: Travel Weather API Support
    email: support@example.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: http://localhost:8000
    description: Local development server
  - url: http://travel-weather-mcp-server:8000
    description: Docker container

paths:
  /tools/call:
    post:
      summary: Execute MCP tool
      description: Call any of the available MCP tools
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ToolCallRequest'
            examples:
              weather_forecast:
                summary: Get weather forecast
                value:
                  name: get_weather_forecast
                  arguments:
                    location: "Oslo"
                    days: 5
              travel_route:
                summary: Get travel route
                value:
                  name: get_travel_routes
                  arguments:
                    origin: "Oslo"
                    destination: "Bergen"
                    mode: "driving"
              trip_plan:
                summary: Plan complete trip
                value:
                  name: plan_trip
                  arguments:
                    origin: "Oslo"
                    destination: "Stavanger"
                    travel_date: "2025-09-20"
                    mode: "driving"
                    days: 3
      responses:
        '200':
          description: Successful tool execution
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ToolCallResponse'
        '400':
          description: Invalid request or missing parameters
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /tools/list:
    get:
      summary: List available tools
      description: Get information about all available MCP tools
      responses:
        '200':
          description: List of available tools
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ToolsListResponse'

  /health:
    get:
      summary: Health check
      description: Check if the server is running
      responses:
        '200':
          description: Server is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "healthy"
                  timestamp:
                    type: string
                    format: date-time

components:
  schemas:
    ToolCallRequest:
      type: object
      required:
        - name
        - arguments
      properties:
        name:
          type: string
          enum: [get_weather_forecast, get_travel_routes, plan_trip]
          description: Name of the tool to execute
        arguments:
          type: object
          description: Tool-specific arguments

    ToolCallResponse:
      type: object
      properties:
        success:
          type: boolean
        result:
          type: object
          description: Tool execution result
        error:
          type: string
          description: Error message if execution failed

    WeatherForecastArgs:
      type: object
      required:
        - location
      properties:
        location:
          type: string
          description: City or location name
          example: "Oslo"
        days:
          type: integer
          minimum: 1
          maximum: 5
          default: 5
          description: Number of days to forecast

    TravelRoutesArgs:
      type: object
      required:
        - origin
        - destination
      properties:
        origin:
          type: string
          description: Starting location
          example: "Oslo"
        destination:
          type: string
          description: Destination location
          example: "Bergen"
        mode:
          type: string
          enum: [driving, walking, cycling]
          default: driving
          description: Transportation mode

    PlanTripArgs:
      type: object
      required:
        - origin
        - destination
      properties:
        origin:
          type: string
          description: Starting location
          example: "Oslo"
        destination:
          type: string
          description: Destination location
          example: "Stavanger"
        travel_date:
          type: string
          format: date
          description: Travel date in YYYY-MM-DD format
          example: "2025-09-20"
        mode:
          type: string
          enum: [driving, walking, cycling]
          default: driving
          description: Transportation mode
        days:
          type: integer
          minimum: 1
          maximum: 5
          default: 5
          description: Number of days for weather forecast

    WeatherForecastResponse:
      type: object
      properties:
        location:
          type: string
          example: "Oslo"
        country:
          type: string
          example: "Norway"
        coordinates:
          $ref: '#/components/schemas/Coordinates'
        forecast:
          type: array
          items:
            $ref: '#/components/schemas/WeatherDay'
        summary:
          type: string
          example: "Partly cloudy with temperatures 8-15°C"

    TravelRoutesResponse:
      type: object
      properties:
        origin:
          $ref: '#/components/schemas/Location'
        destination:
          $ref: '#/components/schemas/Location'
        route:
          $ref: '#/components/schemas/Route'
        travel_advice:
          $ref: '#/components/schemas/TravelAdvice'

    PlanTripResponse:
      type: object
      properties:
        trip_plan:
          type: object
          properties:
            route:
              $ref: '#/components/schemas/Route'
            weather:
              type: object
              properties:
                origin_weather:
                  $ref: '#/components/schemas/WeatherSummary'
                destination_weather:
                  $ref: '#/components/schemas/WeatherSummary'
            recommendations:
              type: array
              items:
                type: string

    Coordinates:
      type: object
      properties:
        lat:
          type: number
          format: float
          example: 59.9133301
        lon:
          type: number
          format: float
          example: 10.7389701

    Location:
      type: object
      properties:
        name:
          type: string
          example: "Oslo"
        coordinates:
          type: array
          items:
            type: number
          minItems: 2
          maxItems: 2
          example: [10.7389701, 59.9133301]

    WeatherDay:
      type: object
      properties:
        date:
          type: string
          format: date
          example: "2025-09-14"
        day_name:
          type: string
          example: "Saturday"
        temperature:
          type: object
          properties:
            min:
              type: number
              format: float
            max:
              type: number
              format: float
            feels_like:
              type: number
              format: float
        weather:
          type: object
          properties:
            main:
              type: string
              example: "Clouds"
            description:
              type: string
              example: "broken clouds"
        humidity:
          type: integer
          example: 67
        wind_speed:
          type: number
          format: float
          example: 3.2
        precipitation:
          type: number
          format: float
          example: 0

    Route:
      type: object
      properties:
        distance_km:
          type: number
          format: float
          example: 456.0
        duration_hours:
          type: number
          format: float
          example: 8.3
        mode:
          type: string
          example: "driving"
        source:
          type: string
          enum: [openroute, fallback]
          example: "openroute"

    TravelAdvice:
      type: object
      properties:
        category:
          type: string
          enum: [short_distance, medium_distance, long_distance]
          example: "medium_distance"
        recommendations:
          type: array
          items:
            type: string

    WeatherSummary:
      type: object
      properties:
        location:
          type: string
        date:
          type: string
          format: date
        temperature:
          type: object
          properties:
            min:
              type: number
            max:
              type: number
        description:
          type: string

    ToolsListResponse:
      type: object
      properties:
        tools:
          type: array
          items:
            type: object
            properties:
              name:
                type: string
              description:
                type: string
              parameters:
                type: object

    ErrorResponse:
      type: object
      properties:
        error:
          type: string
          description: Error message
        code:
          type: integer
          description: Error code
        details:
          type: object
          description: Additional error details
```

## JSON Schema Examples

### Weather Forecast Request
```json
{
  "name": "get_weather_forecast",
  "arguments": {
    "location": "Oslo",
    "days": 3
  }
}
```

### Weather Forecast Response
```json
{
  "success": true,
  "result": {
    "location": "Oslo",
    "country": "Norway",
    "coordinates": {
      "lat": 59.9133301,
      "lon": 10.7389701
    },
    "forecast": [
      {
        "date": "2025-09-14",
        "day_name": "Saturday",
        "temperature": {
          "min": 8.2,
          "max": 15.4,
          "feels_like": 14.8
        },
        "weather": {
          "main": "Clouds",
          "description": "broken clouds"
        },
        "humidity": 67,
        "wind_speed": 3.2,
        "precipitation": 0
      }
    ],
    "summary": "Delvis skyet vær med temperaturer mellom 8-15°C"
  }
}
```

### Travel Routes Request
```json
{
  "name": "get_travel_routes",
  "arguments": {
    "origin": "Oslo", 
    "destination": "Bergen",
    "mode": "driving"
  }
}
```

### Travel Routes Response
```json
{
  "success": true,
  "result": {
    "origin": {
      "name": "Oslo",
      "coordinates": [10.7389701, 59.9133301]
    },
    "destination": {
      "name": "Bergen", 
      "coordinates": [5.3259192, 60.3943055]
    },
    "route": {
      "distance_km": 456.0,
      "duration_hours": 8.3,
      "mode": "driving",
      "source": "openroute"
    },
    "travel_advice": {
      "category": "medium_distance",
      "recommendations": [
        "Planlegg for 8-9 timer kjøring",
        "Ta pauser underveis", 
        "Sjekk værforhold før avreise"
      ]
    }
  }
}
```
