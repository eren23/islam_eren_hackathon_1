# Route Planner

A smart route planner that creates cycling routes with interesting stops based on natural language requests. The application uses AI to understand route requirements and can work with either OpenStreetMap (free) or Google Maps (requires API key).

## Features

- Natural language route planning
- Support for both OpenStreetMap and Google Maps
- Automatic route generation with customizable stops (bars, cafes, etc.)
- Interactive map interface
- Current location detection
- Manual location selection
- Responsive web interface

## Prerequisites

- Python 3.8+
- OpenRouter API key (for natural language processing)
- Google Maps API key (optional, only if using Google Maps mode)

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Copy `sample.env` to `.env` and configure your API keys:
```bash
cp sample.env .env
```
4. Edit `.env` and add your API keys:
```
OPENROUTER_API_KEY=your_openrouter_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key  # Optional
MAP_MODE=osm  # or 'google' for Google Maps
```

## Usage

1. Start the Flask server:
```bash
python app.py
```
2. Open your browser and navigate to `http://localhost:5000`
3. Allow location access or manually select a starting point
4. Enter your route requirements in natural language (e.g., "I want to ride my bike for 10km with a beer break at 5km")
5. Click "Plan Route" to generate your customized route

## Map Modes

### OpenStreetMap (Default)
- Free to use
- No API key required
- Uses actual cycling-friendly roads
- May have limited POI (Points of Interest) data in some areas

### Google Maps
- Requires API key
- Better POI data
- More accurate routing
- Usage costs apply

## API Keys

### OpenRouter API Key
Required for natural language processing. Get one at [OpenRouter](https://openrouter.ai/).

### Google Maps API Key (Optional)
Only required if using Google Maps mode. Get one at [Google Cloud Console](https://console.cloud.google.com/).

## License

MIT License

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. 