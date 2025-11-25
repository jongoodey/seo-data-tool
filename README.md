# AI Keyword Analyser - DataForSEO

A comprehensive Streamlit application for analysing keywords and querying AI models using the DataForSEO AI Optimisation API.

## Features

### 1. AI Keyword Search Volume Analysis
- Analyse up to 1000 keywords at once
- View current AI search volumes
- Historical trend data (12 months)
- Interactive charts and visualizations:
  - Search volume comparison bar charts
  - Multi-keyword trend comparisons
  - Individual keyword trend analysis
- Export data in CSV and JSON formats

### 2. LLM Scraper
- Query multiple AI models (ChatGPT, Claude, Gemini, Perplexity)
- Web-enhanced responses
- Customisable parameters:
  - Temperature control
  - Max output tokens
  - System messages
  - Force web search
- View response metadata (tokens, cost, model info)

### 3. Google AI Overview
- Retrieve actual Google AI-generated overviews from search results
- View markdown-formatted AI content
- Access reference sources used in the overview
- See additional content (videos, tables, expanded elements)
- Device and OS selection (desktop/mobile, Windows/macOS/Android/iOS)
- Optional pixel positioning data for visual analysis
- Export complete SERP data

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit app:
```bash
streamlit run app.py
```

2. Enter your DataForSEO API credentials in the sidebar:
   - Login (email)
   - Password

3. Configure analysis settings:
   - Select location (country)
   - Select language
   - Choose function type

4. For Keyword Analysis:
   - Enter keywords (one per line or comma-separated)
   - Click "Analyse Keywords"
   - View results in different tabs:
     - Overview: Metrics and comparison charts
     - Trends: Historical trend analysis
     - Data Table: Complete data view
     - Export: Download as CSV or JSON

5. For LLM Scraper:
   - Select AI model (ChatGPT, Claude, etc.)
   - Enter your prompt (max 500 characters)
   - Configure advanced settings (optional)
   - Click "Request"
   - View AI response and metadata

6. For Google AI Overview:
   - Enter a search keyword (up to 700 characters)
   - Select device type (desktop or mobile)
   - Choose operating system
   - Configure advanced settings if needed
   - Click "Get AI Overview"
   - View the AI-generated overview, references, and additional content

## Configuration

### Supported Locations
- United States, United Kingdom, Canada, Australia
- Germany, France, Spain, Italy, Netherlands
- Belgium, Switzerland, Austria, Sweden, Norway
- Denmark, Finland, Poland, Czech Republic
- Ireland, Portugal, Greece, Japan, South Korea
- Singapore, India, Brazil, Mexico, Argentina, Chile

### Supported Languages
- English, Spanish, French, German, Italian
- Portuguese, Dutch, Polish, Swedish, Norwegian
- Danish, Finnish, Czech, Greek, Japanese
- Korean, Chinese

## API Information

This application uses the DataForSEO APIs:
- AI Keyword Data: Search volume and historical trends
- LLM Responses: Query AI models with web search capabilities
- Google AI Overview SERP: Retrieve actual Google AI overviews from search results

API Documentation:
- https://docs.dataforseo.com/v3/ai_optimization/overview/
- https://docs.dataforseo.com/v3/serp/google/ai_mode/live/advanced/

## Requirements

- Python 3.8+
- DataForSEO API account
- Internet connection

## Cost

API usage is charged by DataForSEO according to their pricing:
- AI Keyword Search Volume: Per keyword
- LLM Responses: Per request + token usage
- Google AI Overview: Per search (double cost if calculate_rectangles is enabled)

Check current pricing at: https://dataforseo.com/pricing

## Security

Your API credentials are:
- Never stored in the application
- Only used for API authentication during your session
- Entered fresh each time you use the app
- Recommended to use environment variables for automated deployments

## Troubleshooting

### No data returned
- Verify API credentials are correct
- Check that keywords are properly formatted
- Ensure location and language are supported

### API errors
- Check your API account has sufficient credits
- Verify rate limits aren't exceeded (2000 calls/minute)
- Confirm keywords don't exceed 1000 per request

### LLM Scraper timeout
- Processing can take up to 120 seconds
- Wait for the full response
- Try reducing max_output_tokens if timeout persists

### No AI Overview found
- Google doesn't show AI Overviews for all keywords
- AI Overviews are not available in all locations
- Currently only English language is supported for AI Overviews
- Try different keywords or locations

## Support

For API-related issues, contact DataForSEO support:
- Website: https://dataforseo.com
- Documentation: https://docs.dataforseo.com

## Licence

This application is provided as-is for use with DataForSEO API services.
