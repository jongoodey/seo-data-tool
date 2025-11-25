import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import requests
import base64
import json

# Page configuration
st.set_page_config(
    page_title="AI Keyword Analyser - DataForSEO",
    page_icon="🔍",
    layout="wide"
)

class DataForSEOClient:
    """Client for interacting with DataForSEO AI Optimisation API"""

    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.base_url = "https://api.dataforseo.com/v3"

    def _get_auth_header(self):
        """Generate basic auth header"""
        credentials = f"{self.login}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded}"}

    def get_keyword_search_volume(self, keywords, location, language):
        """Get AI keyword search volume data"""
        endpoint = f"{self.base_url}/ai_optimization/ai_keyword_data/keywords_search_volume/live"

        payload = [{
            "keywords": keywords,
            "location_name": location,
            "language_name": language
        }]

        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=self._get_auth_header()
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_llm_response(self, user_prompt, model_name, location, language,
                        force_web_search=False, system_message=None,
                        temperature=0.94, max_output_tokens=2048):
        """Get LLM response with AI search capabilities"""
        endpoint = f"{self.base_url}/ai_optimization/chat_gpt/llm_responses/live"

        payload = [{
            "user_prompt": user_prompt,
            "model_name": model_name,
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "web_search": True,
            "force_web_search": force_web_search,
            "web_search_country_iso_code": self._get_country_code(location)
        }]

        if system_message:
            payload[0]["system_message"] = system_message

        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=self._get_auth_header()
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_google_ai_overview(self, keyword, location, language, device="desktop",
                               os_type=None, calculate_rectangles=False):
        """Get Google AI Overview SERP data"""
        endpoint = f"{self.base_url}/serp/google/ai_mode/live/advanced"

        payload = [{
            "keyword": keyword,
            "location_name": location,
            "language_name": language,
            "device": device,
            "calculate_rectangles": calculate_rectangles
        }]

        if os_type:
            payload[0]["os"] = os_type

        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=self._get_auth_header()
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def _get_country_code(self, location_name):
        """Map location names to country ISO codes"""
        location_map = {
            "United States": "US",
            "United Kingdom": "GB",
            "Canada": "CA",
            "Australia": "AU",
            "Germany": "DE",
            "France": "FR",
            "Spain": "ES",
            "Italy": "IT",
            "Netherlands": "NL",
            "Belgium": "BE",
            "Switzerland": "CH",
            "Austria": "AT",
            "Sweden": "SE",
            "Norway": "NO",
            "Denmark": "DK",
            "Finland": "FI",
            "Poland": "PL",
            "Czech Republic": "CZ",
            "Ireland": "IE",
            "Portugal": "PT",
            "Greece": "GR",
            "Japan": "JP",
            "South Korea": "KR",
            "Singapore": "SG",
            "India": "IN",
            "Brazil": "BR",
            "Mexico": "MX",
            "Argentina": "AR",
            "Chile": "CL"
        }
        return location_map.get(location_name, "US")

    # ===================== BACKLINKS API METHODS =====================

    def get_backlinks(self, target, mode="as_is", limit=100, backlinks_status_type="live",
                      include_subdomains=True, order_by=None, filters=None):
        """Get backlinks for a domain/subdomain/page"""
        endpoint = f"{self.base_url}/backlinks/backlinks/live"

        payload = [{
            "target": target,
            "mode": mode,
            "limit": limit,
            "backlinks_status_type": backlinks_status_type,
            "include_subdomains": include_subdomains
        }]

        if order_by:
            payload[0]["order_by"] = order_by
        if filters:
            payload[0]["filters"] = filters

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_broken_backlinks(self, target, limit=100, include_subdomains=True):
        """Get broken backlinks for a domain/subdomain/page"""
        endpoint = f"{self.base_url}/backlinks/backlinks/live"

        payload = [{
            "target": target,
            "limit": limit,
            "include_subdomains": include_subdomains,
            "filters": [["is_lost", "=", True]]
        }]

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_backlink_anchors(self, target, limit=100, include_subdomains=True, order_by=None):
        """Get anchor text data for backlinks"""
        endpoint = f"{self.base_url}/backlinks/anchors/live"

        payload = [{
            "target": target,
            "limit": limit,
            "include_subdomains": include_subdomains
        }]

        if order_by:
            payload[0]["order_by"] = order_by

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_referring_domains(self, target, limit=100, include_subdomains=True, order_by=None):
        """Get referring domains for a target"""
        endpoint = f"{self.base_url}/backlinks/referring_domains/live"

        payload = [{
            "target": target,
            "limit": limit,
            "include_subdomains": include_subdomains
        }]

        if order_by:
            payload[0]["order_by"] = order_by

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_backlink_summary(self, target, include_subdomains=True):
        """Get backlink summary for a target"""
        endpoint = f"{self.base_url}/backlinks/summary/live"

        payload = [{
            "target": target,
            "include_subdomains": include_subdomains
        }]

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_bulk_backlinks(self, targets):
        """Get bulk backlink counts for multiple targets"""
        endpoint = f"{self.base_url}/backlinks/bulk_backlinks/live"

        payload = [{"targets": targets}]

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_bulk_referring_domains(self, targets):
        """Get bulk referring domain counts for multiple targets"""
        endpoint = f"{self.base_url}/backlinks/bulk_referring_domains/live"

        payload = [{"targets": targets}]

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_bulk_ranks(self, targets):
        """Get bulk rank scores for multiple targets"""
        endpoint = f"{self.base_url}/backlinks/bulk_ranks/live"

        payload = [{"targets": targets}]

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_bulk_spam_score(self, targets):
        """Get bulk spam scores for multiple targets"""
        endpoint = f"{self.base_url}/backlinks/bulk_spam_score/live"

        payload = [{"targets": targets}]

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_bulk_new_lost_backlinks(self, targets, date_from=None):
        """Get bulk new/lost backlink counts"""
        endpoint = f"{self.base_url}/backlinks/bulk_new_lost_backlinks/live"

        payload = [{"targets": targets}]
        if date_from:
            payload[0]["date_from"] = date_from

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_bulk_new_lost_referring_domains(self, targets, date_from=None):
        """Get bulk new/lost referring domain counts"""
        endpoint = f"{self.base_url}/backlinks/bulk_new_lost_referring_domains/live"

        payload = [{"targets": targets}]
        if date_from:
            payload[0]["date_from"] = date_from

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    # ===================== SERP API METHODS =====================

    def get_serp_organic(self, keyword, location, language, device="desktop", depth=100):
        """Get Google organic SERP results"""
        endpoint = f"{self.base_url}/serp/google/organic/live/advanced"

        payload = [{
            "keyword": keyword,
            "location_name": location,
            "language_name": language,
            "device": device,
            "depth": depth
        }]

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_bulk_serp(self, keywords, location, language, device="desktop"):
        """Get bulk SERP rankings for multiple keywords"""
        endpoint = f"{self.base_url}/serp/google/organic/live/advanced"

        # Create tasks for each keyword
        payload = []
        for keyword in keywords:
            payload.append({
                "keyword": keyword,
                "location_name": location,
                "language_name": language,
                "device": device,
                "depth": 100
            })

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    # ===================== DATAFORSEO LABS API METHODS =====================

    def get_domain_rank_overview(self, target, location, language):
        """Get domain rank overview"""
        endpoint = f"{self.base_url}/dataforseo_labs/google/domain_rank_overview/live"

        payload = [{
            "target": target,
            "location_name": location,
            "language_name": language
        }]

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_historical_rank_overview(self, target, location, language, date_from=None, date_to=None):
        """Get historical rank data for organic traffic estimation"""
        endpoint = f"{self.base_url}/dataforseo_labs/google/historical_rank_overview/live"

        payload = [{
            "target": target,
            "location_name": location,
            "language_name": language
        }]

        if date_from:
            payload[0]["date_from"] = date_from
        if date_to:
            payload[0]["date_to"] = date_to

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_ranked_keywords(self, target, location, language, limit=100, item_types=None):
        """Get ranked keywords for a domain"""
        endpoint = f"{self.base_url}/dataforseo_labs/google/ranked_keywords/live"

        payload = [{
            "target": target,
            "location_name": location,
            "language_name": language,
            "limit": limit
        }]

        if item_types:
            payload[0]["item_types"] = item_types

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_keyword_suggestions(self, keyword, location, language, limit=100, include_seed=False):
        """Get keyword suggestions based on seed keyword"""
        endpoint = f"{self.base_url}/dataforseo_labs/google/keyword_suggestions/live"

        payload = [{
            "keyword": keyword,
            "location_name": location,
            "language_name": language,
            "limit": limit,
            "include_seed_keyword": include_seed
        }]

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_keyword_ideas(self, keywords, location, language, limit=100):
        """Get similar/related keyword ideas"""
        endpoint = f"{self.base_url}/dataforseo_labs/google/keyword_ideas/live"

        payload = [{
            "keywords": keywords,
            "location_name": location,
            "language_name": language,
            "limit": limit
        }]

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_keywords_for_site(self, target, location, language, limit=100):
        """Get keyword suggestions for a website"""
        endpoint = f"{self.base_url}/dataforseo_labs/google/keywords_for_site/live"

        payload = [{
            "target": target,
            "location_name": location,
            "language_name": language,
            "limit": limit
        }]

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_keywords_for_categories(self, category_codes, location, language, limit=100):
        """Get keywords for product/service categories"""
        endpoint = f"{self.base_url}/dataforseo_labs/google/keywords_for_categories/live"

        payload = [{
            "category_codes": category_codes,
            "location_name": location,
            "language_name": language,
            "limit": limit
        }]

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_search_intent(self, keywords, language):
        """Get search intent classification for keywords"""
        endpoint = f"{self.base_url}/dataforseo_labs/google/search_intent/live"

        payload = [{
            "keywords": keywords,
            "language_name": language
        }]

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_bulk_keyword_difficulty(self, keywords, location, language):
        """Get keyword difficulty scores for multiple keywords"""
        endpoint = f"{self.base_url}/dataforseo_labs/google/bulk_keyword_difficulty/live"

        payload = [{
            "keywords": keywords,
            "location_name": location,
            "language_name": language
        }]

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    # ===================== KEYWORDS DATA API METHODS =====================

    def get_google_search_volume(self, keywords, location, language):
        """Get Google Ads search volume data"""
        endpoint = f"{self.base_url}/keywords_data/google_ads/search_volume/live"

        payload = [{
            "keywords": keywords,
            "location_name": location,
            "language_name": language
        }]

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    def get_bing_search_volume(self, keywords, location, language):
        """Get Bing search volume data"""
        endpoint = f"{self.base_url}/keywords_data/bing/search_volume/live"

        payload = [{
            "keywords": keywords,
            "location_name": location,
            "language_name": language
        }]

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

    # ===================== ON-PAGE API METHODS =====================

    def get_instant_pages(self, url, enable_javascript=True, enable_browser_rendering=True):
        """Get on-page analysis including load time and audit checks"""
        endpoint = f"{self.base_url}/on_page/instant_pages"

        payload = [{
            "url": url,
            "enable_javascript": enable_javascript,
            "enable_browser_rendering": enable_browser_rendering,
            "load_resources": True,
            "check_spell": True
        }]

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

def parse_keyword_data(response_data):
    """Parse keyword search volume response into DataFrame"""
    if not response_data or 'tasks' not in response_data:
        return None

    all_keywords = []

    for task in response_data['tasks']:
        if task['status_code'] == 20000 and task['result']:
            for result in task['result']:
                if 'items' in result:
                    for item in result['items']:
                        keyword_info = {
                            'Keyword': item.get('keyword', ''),
                            'Current Search Volume': item.get('ai_search_volume', 0),
                            'Location': result.get('location_code', ''),
                            'Language': result.get('language_code', '')
                        }

                        # Add historical data
                        if 'ai_monthly_searches' in item and item['ai_monthly_searches']:
                            monthly_data = item['ai_monthly_searches']
                            for i, month_data in enumerate(monthly_data[-12:]):  # Last 12 months
                                month_label = f"{month_data.get('year', '')}-{str(month_data.get('month', '')).zfill(2)}"
                                keyword_info[f'SV_{month_label}'] = month_data.get('ai_search_volume', 0)

                        all_keywords.append(keyword_info)

    return pd.DataFrame(all_keywords) if all_keywords else None

def create_trend_chart(df, keyword):
    """Create a line chart showing keyword trend over time"""
    # Get historical columns
    hist_cols = [col for col in df.columns if col.startswith('SV_')]

    if not hist_cols:
        return None

    keyword_data = df[df['Keyword'] == keyword].iloc[0]

    months = [col.replace('SV_', '') for col in hist_cols]
    volumes = [keyword_data[col] for col in hist_cols]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months,
        y=volumes,
        mode='lines+markers',
        name=keyword,
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=8)
    ))

    fig.update_layout(
        title=f'Search Volume Trend: {keyword}',
        xaxis_title='Month',
        yaxis_title='AI Search Volume',
        hovermode='x unified',
        height=400
    )

    return fig

def create_comparison_chart(df):
    """Create a bar chart comparing current search volumes"""
    fig = px.bar(
        df.sort_values('Current Search Volume', ascending=False),
        x='Keyword',
        y='Current Search Volume',
        title='Keyword Search Volume Comparison',
        color='Current Search Volume',
        color_continuous_scale='Blues'
    )

    fig.update_layout(
        xaxis_title='Keyword',
        yaxis_title='AI Search Volume',
        height=400
    )

    return fig

def create_trend_comparison_chart(df):
    """Create multi-line chart comparing trends across keywords"""
    hist_cols = [col for col in df.columns if col.startswith('SV_')]

    if not hist_cols:
        return None

    fig = go.Figure()

    for _, row in df.iterrows():
        months = [col.replace('SV_', '') for col in hist_cols]
        volumes = [row[col] for col in hist_cols]

        fig.add_trace(go.Scatter(
            x=months,
            y=volumes,
            mode='lines+markers',
            name=row['Keyword'],
            line=dict(width=2),
            marker=dict(size=6)
        ))

    fig.update_layout(
        title='Keyword Trends Comparison',
        xaxis_title='Month',
        yaxis_title='AI Search Volume',
        hovermode='x unified',
        height=500,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="right",
            x=1.15
        )
    )

    return fig

def main():
    st.title("🔍 AI Keyword Analyser")
    st.markdown("Analyse keywords using DataForSEO's AI Optimisation API")

    # Sidebar for API credentials and settings
    with st.sidebar:
        st.header("⚙️ Configuration")

        st.subheader("API Credentials")
        api_login = st.text_input("DataForSEO Login", type="default")
        api_password = st.text_input("DataForSEO Password", type="password")

        st.markdown("---")

        st.subheader("Analysis Settings")

        # Function category selection
        function_category = st.selectbox(
            "Category",
            ["AI Optimisation", "Backlinks", "SERP & Rankings", "Keywords"],
            help="Choose the tool category"
        )

        # Function selection based on category
        if function_category == "AI Optimisation":
            function_type = st.selectbox(
                "Function",
                ["AI Keyword Search Volume", "LLM Scraper", "Google AI Overview"],
                help="Choose the type of analysis to perform"
            )
        elif function_category == "Backlinks":
            function_type = st.selectbox(
                "Function",
                ["Backlink List", "Broken Backlink List", "Backlink Anchor List",
                 "Referring Domains", "Backlink Summary",
                 "Bulk Backlinks Overview", "Bulk Referring Domains Overview",
                 "Bulk Backlink Rank Checker", "Bulk Backlink Spam Score",
                 "Bulk New&Lost Backlinks Overview", "Bulk New&Lost Referring Domains Overview"],
                help="Choose the backlink analysis tool"
            )
        elif function_category == "SERP & Rankings":
            function_type = st.selectbox(
                "Function",
                ["SERP Parser", "Bulk Rank Tracking (Google)",
                 "Organic Domain Rank Overview", "Organic Traffic Estimation",
                 "Ranked Keywords", "Page Load Time", "Page Audit Checks"],
                help="Choose the SERP/ranking tool"
            )
        else:  # Keywords
            function_type = st.selectbox(
                "Function",
                ["Keyword Search Intent", "Keywords Difficulty",
                 "Google Search Volume", "Bing Search Volume",
                 "Keyword Suggestions", "Similar Keywords",
                 "Website Keyword Suggestions", "Keyword Suggestions for Categories"],
                help="Choose the keyword research tool"
            )

        # Location selection
        location = st.selectbox(
            "Location",
            ["United States", "United Kingdom", "Canada", "Australia",
             "Germany", "France", "Spain", "Italy", "Netherlands",
             "Belgium", "Switzerland", "Austria", "Sweden", "Norway",
             "Denmark", "Finland", "Poland", "Czech Republic", "Ireland",
             "Portugal", "Greece", "Japan", "South Korea", "Singapore",
             "India", "Brazil", "Mexico", "Argentina", "Chile"]
        )

        # Language selection
        language = st.selectbox(
            "Language",
            ["English", "Spanish", "French", "German", "Italian",
             "Portuguese", "Dutch", "Polish", "Swedish", "Norwegian",
             "Danish", "Finnish", "Czech", "Greek", "Japanese",
             "Korean", "Chinese"]
        )

    # Main content area
    if not api_login or not api_password:
        st.warning("⚠️ Please enter your DataForSEO API credentials in the sidebar to begin.")
        st.info("""
        ### How to use this tool:
        1. Enter your DataForSEO API login and password in the sidebar
        2. Select your preferred location and language
        3. Choose the analysis function
        4. Enter keywords or prompts below
        5. Click 'Analyse' to get insights

        Don't have an account? Visit [DataForSEO](https://dataforseo.com) to sign up.
        """)
        return

    # Initialize client
    client = DataForSEOClient(api_login, api_password)

    # Content based on function type
    if function_type == "AI Keyword Search Volume":
        st.header("📊 AI Keyword Search Volume Analysis")

        # Keyword input
        keyword_input = st.text_area(
            "Keywords",
            placeholder="Enter keywords (one per line or comma-separated)\n\nExample:\nseo\ndigital marketing\ncontent optimisation",
            height=150,
            help="Enter up to 1000 keywords to analyse"
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_button = st.button("🔍 Analyse Keywords", type="primary", use_container_width=True)

        if analyse_button:
            if not keyword_input.strip():
                st.error("Please enter at least one keyword.")
                return

            # Parse keywords
            keywords = []
            for line in keyword_input.split('\n'):
                keywords.extend([k.strip() for k in line.split(',') if k.strip()])

            keywords = list(set(keywords))[:1000]  # Limit to 1000 unique keywords

            st.info(f"Analysing {len(keywords)} keyword(s)...")

            with st.spinner("Fetching data from DataForSEO..."):
                response = client.get_keyword_search_volume(keywords, location, language)

            if response:
                df = parse_keyword_data(response)

                if df is not None and not df.empty:
                    st.success(f"✅ Analysis complete! Found data for {len(df)} keyword(s).")

                    # Display metrics
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Total Keywords", len(df))

                    with col2:
                        total_volume = df['Current Search Volume'].sum()
                        st.metric("Total Search Volume", f"{total_volume:,}")

                    with col3:
                        avg_volume = df['Current Search Volume'].mean()
                        st.metric("Average Volume", f"{avg_volume:,.0f}")

                    with col4:
                        max_volume = df['Current Search Volume'].max()
                        st.metric("Highest Volume", f"{max_volume:,}")

                    # Tabs for different views
                    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "📊 Trends", "📋 Data Table", "💾 Export"])

                    with tab1:
                        st.subheader("Search Volume Comparison")
                        comparison_chart = create_comparison_chart(df)
                        st.plotly_chart(comparison_chart, use_container_width=True)

                        # Top performing keywords
                        st.subheader("Top 10 Keywords by Search Volume")
                        top_keywords = df.nlargest(10, 'Current Search Volume')[['Keyword', 'Current Search Volume']]
                        st.dataframe(top_keywords, hide_index=True, use_container_width=True)

                    with tab2:
                        st.subheader("Historical Trend Analysis")

                        # Multi-keyword trend comparison
                        trend_comparison = create_trend_comparison_chart(df)
                        if trend_comparison:
                            st.plotly_chart(trend_comparison, use_container_width=True)

                        # Individual keyword trends
                        st.subheader("Individual Keyword Trends")
                        selected_keyword = st.selectbox("Select a keyword to view detailed trend", df['Keyword'].tolist())

                        if selected_keyword:
                            trend_chart = create_trend_chart(df, selected_keyword)
                            if trend_chart:
                                st.plotly_chart(trend_chart, use_container_width=True)
                            else:
                                st.info("No historical data available for this keyword.")

                    with tab3:
                        st.subheader("Complete Data")
                        st.dataframe(df, use_container_width=True, hide_index=True)

                    with tab4:
                        st.subheader("Export Data")

                        # CSV download
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"keyword_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )

                        # JSON download
                        json_str = df.to_json(orient='records', indent=2)
                        st.download_button(
                            label="📥 Download JSON",
                            data=json_str,
                            file_name=f"keyword_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                else:
                    st.error("No data returned. Please check your keywords and try again.")

    elif function_type == "LLM Scraper":
        st.header("🤖 LLM Scraper")

        col1, col2 = st.columns(2)

        with col1:
            se_type = st.selectbox(
                "Search Engine (SE)",
                ["ChatGPT", "Claude", "Gemini", "Perplexity"],
                help="Select the LLM to query"
            )

        with col2:
            force_web_search = st.selectbox(
                "Force Web Search",
                ["Disable", "Enable"],
                help="Force the LLM to use web search"
            )

        # Keyword/Prompt input
        user_prompt = st.text_area(
            "Keyword / Prompt",
            placeholder="Enter your question or prompt for the AI model\n\nExample: What are the best SEO practices for 2024?",
            height=150,
            help="Max 500 characters"
        )

        with st.expander("⚙️ Advanced Settings"):
            col1, col2 = st.columns(2)

            with col1:
                temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=2.0,
                    value=0.94,
                    step=0.01,
                    help="Controls randomness in responses. Higher = more creative, lower = more focused"
                )

            with col2:
                max_tokens = st.number_input(
                    "Max Output Tokens",
                    min_value=16,
                    max_value=4096,
                    value=2048,
                    step=100,
                    help="Maximum length of the response"
                )

            system_message = st.text_area(
                "System Message (Optional)",
                placeholder="Provide instructions for how the AI should behave\n\nExample: You are an SEO expert providing actionable advice.",
                height=100,
                help="Max 500 characters"
            )

        col1, col2 = st.columns([1, 4])
        with col1:
            request_button = st.button("🚀 Request", type="primary", use_container_width=True)

        if request_button:
            if not user_prompt.strip():
                st.error("Please enter a prompt.")
                return

            if len(user_prompt) > 500:
                st.error("Prompt must be 500 characters or less.")
                return

            # Map SE type to model name
            model_map = {
                "ChatGPT": "gpt-4o",
                "Claude": "claude-3-5-sonnet-20241022",
                "Gemini": "gemini-1.5-pro",
                "Perplexity": "sonar-reasoning"
            }

            model_name = model_map.get(se_type, "gpt-4o")
            force_ws = force_web_search == "Enable"
            sys_msg = system_message.strip() if system_message.strip() else None

            st.info(f"Querying {se_type}... (This may take up to 120 seconds)")

            with st.spinner("Processing your request..."):
                response = client.get_llm_response(
                    user_prompt=user_prompt,
                    model_name=model_name,
                    location=location,
                    language=language,
                    force_web_search=force_ws,
                    system_message=sys_msg,
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )

            if response:
                st.success("✅ Response received!")

                # Parse and display response
                if 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]

                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]

                        # Display response content
                        st.subheader("🤖 AI Response")

                        response_displayed = False

                        if 'items' in result and result['items']:
                            item = result['items'][0]

                            # Try different response formats
                            # Format 1: Direct sections array (most common for ChatGPT/Claude responses)
                            if 'sections' in item and isinstance(item['sections'], list):
                                for section in item['sections']:
                                    if 'text' in section:
                                        st.markdown(section['text'])
                                        response_displayed = True
                                    elif 'content' in section:
                                        st.markdown(section['content'])
                                        response_displayed = True

                            # Format 2: content.sections structure
                            elif 'content' in item and isinstance(item['content'], dict) and 'sections' in item['content']:
                                for section in item['content']['sections']:
                                    if 'text' in section:
                                        st.markdown(section['text'])
                                        response_displayed = True

                            # Format 3: Direct text field
                            elif 'text' in item:
                                st.markdown(item['text'])
                                response_displayed = True

                            # Format 4: Message or response field
                            elif 'message' in item:
                                st.markdown(item['message'])
                                response_displayed = True
                            elif 'response' in item:
                                st.markdown(item['response'])
                                response_displayed = True

                            # Format 5: Content as string
                            elif 'content' in item and isinstance(item['content'], str):
                                st.markdown(item['content'])
                                response_displayed = True

                            # If no standard format found, show the raw item content
                            if not response_displayed:
                                st.warning("Response received but in an unexpected format. Showing raw content:")
                                with st.expander("📄 View Raw Response", expanded=True):
                                    st.json(item)
                                response_displayed = True

                            # Show metadata
                            with st.expander("📊 Response Metadata"):
                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    if 'model_name' in item:
                                        st.metric("Model", item['model_name'])
                                    elif 'model' in item:
                                        st.metric("Model", item['model'])

                                with col2:
                                    if 'input_tokens' in item:
                                        st.metric("Input Tokens", item['input_tokens'])
                                    elif 'tokens_input' in item:
                                        st.metric("Input Tokens", item['tokens_input'])

                                with col3:
                                    if 'output_tokens' in item:
                                        st.metric("Output Tokens", item['output_tokens'])
                                    elif 'tokens_output' in item:
                                        st.metric("Output Tokens", item['tokens_output'])

                                if 'cost' in result:
                                    st.metric("Cost (USD)", f"${result['cost']:.4f}")

                                # Show full metadata in expandable section
                                st.markdown("**All Metadata:**")
                                metadata = {k: v for k, v in item.items() if k not in ['content', 'sections', 'text', 'message', 'response']}
                                st.json(metadata)

                            # Show sources if available
                            if 'web_search_applied' in item and item['web_search_applied']:
                                st.markdown("---")
                                st.subheader("🔗 Web Sources Used")
                                st.info("This response utilized web search to provide current information.")

                                # Check for citations or sources
                                if 'citations' in item and item['citations']:
                                    for idx, citation in enumerate(item['citations'], 1):
                                        with st.expander(f"Source {idx}"):
                                            st.json(citation)
                        else:
                            st.warning("No items found in response. Showing raw result:")
                            st.json(result)

                        # Download response
                        st.markdown("---")
                        st.subheader("💾 Export Response")

                        response_json = json.dumps(response, indent=2)
                        st.download_button(
                            label="📥 Download Full Response (JSON)",
                            data=response_json,
                            file_name=f"llm_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")
                        # Show the full error response for debugging
                        with st.expander("🔍 View Error Details"):
                            st.json(task)
                else:
                    st.error("No response data received.")
                    # Show what was received for debugging
                    with st.expander("🔍 View Raw Response"):
                        st.json(response)

    elif function_type == "Google AI Overview":
        st.header("🔎 Google AI Overview SERP")
        st.markdown("Retrieve Google's AI-generated overview that appears in search results")

        # Keyword input
        search_keyword = st.text_input(
            "Search Keyword",
            placeholder="Enter a search query (up to 700 characters)\n\nExample: best SEO tools for small business",
            help="The keyword to search for in Google"
        )

        col1, col2 = st.columns(2)

        with col1:
            device = st.selectbox(
                "Device",
                ["desktop", "mobile"],
                help="Choose device type for search results"
            )

        with col2:
            if device == "desktop":
                os_options = ["Windows", "macOS"]
            else:
                os_options = ["Android", "iOS"]

            os_type = st.selectbox(
                "Operating System",
                os_options,
                help="Select the operating system"
            )

        with st.expander("⚙️ Advanced Settings"):
            calculate_rectangles = st.checkbox(
                "Calculate Rectangles",
                value=False,
                help="Include pixel positioning data (costs double)"
            )

            if calculate_rectangles:
                col1, col2, col3 = st.columns(3)

                with col1:
                    screen_width = st.number_input(
                        "Screen Width",
                        min_value=320,
                        max_value=7680,
                        value=1920,
                        help="Browser screen width in pixels"
                    )

                with col2:
                    screen_height = st.number_input(
                        "Screen Height",
                        min_value=240,
                        max_value=4320,
                        value=1080,
                        help="Browser screen height in pixels"
                    )

                with col3:
                    resolution_ratio = st.number_input(
                        "Resolution Ratio",
                        min_value=0.5,
                        max_value=3.0,
                        value=1.0,
                        step=0.1,
                        help="Device resolution multiplier"
                    )
            else:
                screen_width = None
                screen_height = None
                resolution_ratio = None

        col1, col2 = st.columns([1, 4])
        with col1:
            search_button = st.button("🔍 Get AI Overview", type="primary", use_container_width=True)

        if search_button:
            if not search_keyword.strip():
                st.error("Please enter a search keyword.")
                return

            if len(search_keyword) > 700:
                st.error("Keyword must be 700 characters or less.")
                return

            st.info("Fetching Google AI Overview...")

            with st.spinner("Retrieving search results..."):
                response = client.get_google_ai_overview(
                    keyword=search_keyword,
                    location=location,
                    language=language,
                    device=device,
                    os_type=os_type,
                    calculate_rectangles=calculate_rectangles
                )

            if response:
                if 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]

                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]

                        st.success("✅ AI Overview retrieved successfully!")

                        # Display search info
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("Keyword", search_keyword)

                        with col2:
                            st.metric("Location", location)

                        with col3:
                            if 'cost' in result:
                                st.metric("Cost (USD)", f"${result['cost']:.6f}")

                        st.markdown("---")

                        # Check if AI Overview exists
                        if 'items' in result and result['items']:
                            ai_overview_found = False

                            for item in result['items']:
                                if item.get('type') == 'ai_overview':
                                    ai_overview_found = True

                                    st.subheader("🤖 Google AI Overview")

                                    # Display markdown content
                                    if 'markdown' in item:
                                        st.markdown(item['markdown'])

                                    # Display references
                                    if 'references' in item and item['references']:
                                        st.markdown("---")
                                        st.subheader("📚 References")

                                        for idx, ref in enumerate(item['references'], 1):
                                            with st.expander(f"Reference {idx}: {ref.get('title', 'N/A')}"):
                                                col1, col2 = st.columns([3, 1])

                                                with col1:
                                                    if 'url' in ref:
                                                        st.markdown(f"**URL:** [{ref['url']}]({ref['url']})")
                                                    if 'domain' in ref:
                                                        st.markdown(f"**Domain:** {ref['domain']}")
                                                    if 'breadcrumb' in ref:
                                                        st.markdown(f"**Breadcrumb:** {ref['breadcrumb']}")

                                                with col2:
                                                    if 'xpath' in ref:
                                                        st.caption(f"Position: {ref['xpath']}")

                                    # Display items (videos, tables, expanded content)
                                    if 'items' in item and item['items']:
                                        st.markdown("---")
                                        st.subheader("📊 Additional Content")

                                        for sub_item in item['items']:
                                            item_type = sub_item.get('type', 'unknown')

                                            if item_type == 'ai_overview_video_element':
                                                with st.expander(f"🎥 Video: {sub_item.get('title', 'N/A')}"):
                                                    if 'url' in sub_item:
                                                        st.markdown(f"**URL:** [{sub_item['url']}]({sub_item['url']})")
                                                    if 'source' in sub_item:
                                                        st.markdown(f"**Source:** {sub_item['source']}")
                                                    if 'timestamp' in sub_item:
                                                        st.markdown(f"**Timestamp:** {sub_item['timestamp']}")
                                                    if 'thumbnail' in sub_item:
                                                        st.image(sub_item['thumbnail'], width=300)

                                            elif item_type == 'ai_overview_table_element':
                                                st.markdown("**📋 Table:**")
                                                if 'table' in sub_item:
                                                    table_data = sub_item['table']
                                                    if 'table_header' in table_data and 'table_content' in table_data:
                                                        df_table = pd.DataFrame(
                                                            table_data['table_content'],
                                                            columns=table_data['table_header']
                                                        )
                                                        st.dataframe(df_table, use_container_width=True)

                                            elif item_type == 'ai_overview_expanded_element':
                                                with st.expander("📖 Expanded Content"):
                                                    if 'expanded_element' in sub_item:
                                                        for exp_item in sub_item['expanded_element']:
                                                            if 'title' in exp_item:
                                                                st.markdown(f"**{exp_item['title']}**")
                                                            if 'description' in exp_item:
                                                                st.markdown(exp_item['description'])
                                                            if 'url' in exp_item:
                                                                st.markdown(f"[Learn more]({exp_item['url']})")
                                                            st.markdown("---")

                                    # Pixel positioning data
                                    if calculate_rectangles and 'rectangle' in item:
                                        with st.expander("📐 Pixel Positioning Data"):
                                            rect = item['rectangle']
                                            col1, col2, col3, col4 = st.columns(4)

                                            with col1:
                                                st.metric("X Position", rect.get('x', 'N/A'))
                                            with col2:
                                                st.metric("Y Position", rect.get('y', 'N/A'))
                                            with col3:
                                                st.metric("Width", rect.get('width', 'N/A'))
                                            with col4:
                                                st.metric("Height", rect.get('height', 'N/A'))

                                    break

                            if not ai_overview_found:
                                st.warning("⚠️ No AI Overview found for this search query. Google may not be showing an AI Overview for this particular keyword.")
                                st.info("Try a different keyword or check if AI Overviews are available in your selected location.")

                        else:
                            st.warning("No search results returned.")

                        # Export functionality
                        st.markdown("---")
                        st.subheader("💾 Export Data")

                        response_json = json.dumps(response, indent=2)
                        st.download_button(
                            label="📥 Download Full Response (JSON)",
                            data=response_json,
                            file_name=f"google_ai_overview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )

                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")
                else:
                    st.error("No response data received.")

    # ===================== BACKLINKS TOOLS =====================

    elif function_type == "Backlink List":
        st.header("🔗 Backlink List")
        st.markdown("Get detailed backlink data for a domain, subdomain, or page")

        target_input = st.text_input(
            "Target",
            placeholder="Enter domain (e.g., example.com) or full URL",
            help="Domain without https:// or www, or full URL for page-level analysis"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            mode = st.selectbox(
                "Mode",
                ["as_is", "one_per_domain", "one_per_anchor"],
                help="How to group backlinks"
            )

        with col2:
            limit = st.number_input(
                "Limit",
                min_value=1,
                max_value=1000,
                value=100,
                help="Maximum backlinks to return"
            )

        with col3:
            backlinks_status = st.selectbox(
                "Status",
                ["live", "lost", "all"],
                help="Filter by backlink status"
            )

        include_subdomains = st.checkbox("Include Subdomains", value=True)

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Get Backlinks", type="primary", use_container_width=True)

        if analyse_btn:
            if not target_input.strip():
                st.error("Please enter a target domain or URL.")
            else:
                with st.spinner("Fetching backlink data..."):
                    response = client.get_backlinks(
                        target=target_input.strip(),
                        mode=mode,
                        limit=limit,
                        backlinks_status_type=backlinks_status,
                        include_subdomains=include_subdomains
                    )

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success(f"✅ Found {result.get('total_count', 0):,} backlinks!")

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Backlinks", f"{result.get('total_count', 0):,}")
                        with col2:
                            st.metric("Returned", f"{result.get('items_count', 0):,}")
                        with col3:
                            st.metric("Target", target_input.strip())
                        with col4:
                            if 'cost' in task:
                                st.metric("Cost (USD)", f"${task['cost']:.4f}")

                        if 'items' in result and result['items']:
                            # Create DataFrame
                            backlinks_data = []
                            for item in result['items']:
                                backlinks_data.append({
                                    'Domain From': item.get('domain_from', ''),
                                    'URL From': item.get('url_from', ''),
                                    'URL To': item.get('url_to', ''),
                                    'Anchor': item.get('anchor', ''),
                                    'Dofollow': item.get('dofollow', False),
                                    'Page Rank': item.get('page_from_rank', 0),
                                    'Domain Rank': item.get('domain_from_rank', 0),
                                    'First Seen': item.get('first_seen', ''),
                                    'Last Seen': item.get('last_seen', ''),
                                    'Type': item.get('item_type', ''),
                                    'Spam Score': item.get('backlink_spam_score', 0)
                                })

                            df = pd.DataFrame(backlinks_data)

                            tab1, tab2, tab3 = st.tabs(["📋 Data Table", "📊 Charts", "💾 Export"])

                            with tab1:
                                st.dataframe(df, use_container_width=True, hide_index=True)

                            with tab2:
                                # Dofollow vs Nofollow chart
                                dofollow_counts = df['Dofollow'].value_counts()
                                fig1 = px.pie(
                                    values=dofollow_counts.values,
                                    names=['Dofollow' if x else 'Nofollow' for x in dofollow_counts.index],
                                    title="Dofollow vs Nofollow"
                                )
                                st.plotly_chart(fig1, use_container_width=True)

                                # Top referring domains
                                top_domains = df['Domain From'].value_counts().head(20)
                                fig2 = px.bar(
                                    x=top_domains.values,
                                    y=top_domains.index,
                                    orientation='h',
                                    title="Top 20 Referring Domains",
                                    labels={'x': 'Backlinks', 'y': 'Domain'}
                                )
                                fig2.update_layout(yaxis={'categoryorder': 'total ascending'})
                                st.plotly_chart(fig2, use_container_width=True)

                            with tab3:
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    "📥 Download CSV",
                                    csv,
                                    f"backlinks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    "text/csv"
                                )
                                st.download_button(
                                    "📥 Download JSON",
                                    json.dumps(response, indent=2),
                                    f"backlinks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                    "application/json"
                                )
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Broken Backlink List":
        st.header("🔗 Broken Backlink List")
        st.markdown("Find lost/broken backlinks for a domain or page")

        target_input = st.text_input(
            "Target",
            placeholder="Enter domain (e.g., example.com) or full URL",
            help="Domain without https:// or www, or full URL for page-level analysis"
        )

        col1, col2 = st.columns(2)
        with col1:
            limit = st.number_input("Limit", min_value=1, max_value=1000, value=100)
        with col2:
            include_subdomains = st.checkbox("Include Subdomains", value=True)

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Find Broken Backlinks", type="primary", use_container_width=True)

        if analyse_btn:
            if not target_input.strip():
                st.error("Please enter a target domain or URL.")
            else:
                with st.spinner("Searching for broken backlinks..."):
                    response = client.get_broken_backlinks(
                        target=target_input.strip(),
                        limit=limit,
                        include_subdomains=include_subdomains
                    )

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success(f"✅ Found {result.get('total_count', 0):,} broken backlinks!")

                        if 'items' in result and result['items']:
                            broken_data = []
                            for item in result['items']:
                                broken_data.append({
                                    'Domain From': item.get('domain_from', ''),
                                    'URL From': item.get('url_from', ''),
                                    'URL To': item.get('url_to', ''),
                                    'Anchor': item.get('anchor', ''),
                                    'Domain Rank': item.get('domain_from_rank', 0),
                                    'First Seen': item.get('first_seen', ''),
                                    'Lost Date': item.get('last_seen', '')
                                })

                            df = pd.DataFrame(broken_data)
                            st.dataframe(df, use_container_width=True, hide_index=True)

                            csv = df.to_csv(index=False)
                            st.download_button(
                                "📥 Download CSV",
                                csv,
                                f"broken_backlinks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                "text/csv"
                            )
                        else:
                            st.info("No broken backlinks found!")
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Backlink Anchor List":
        st.header("⚓ Backlink Anchor List")
        st.markdown("Analyse anchor text distribution for backlinks")

        target_input = st.text_input(
            "Target",
            placeholder="Enter domain (e.g., example.com) or full URL"
        )

        col1, col2 = st.columns(2)
        with col1:
            limit = st.number_input("Limit", min_value=1, max_value=1000, value=100)
        with col2:
            include_subdomains = st.checkbox("Include Subdomains", value=True)

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Get Anchors", type="primary", use_container_width=True)

        if analyse_btn:
            if not target_input.strip():
                st.error("Please enter a target domain or URL.")
            else:
                with st.spinner("Fetching anchor data..."):
                    response = client.get_backlink_anchors(
                        target=target_input.strip(),
                        limit=limit,
                        include_subdomains=include_subdomains
                    )

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success(f"✅ Found {result.get('total_count', 0):,} unique anchors!")

                        if 'items' in result and result['items']:
                            anchor_data = []
                            for item in result['items']:
                                anchor_data.append({
                                    'Anchor': item.get('anchor', ''),
                                    'Backlinks': item.get('backlinks', 0),
                                    'Referring Domains': item.get('referring_domains', 0),
                                    'Rank': item.get('rank', 0),
                                    'First Seen': item.get('first_seen', ''),
                                    'Spam Score': item.get('backlinks_spam_score', 0)
                                })

                            df = pd.DataFrame(anchor_data)

                            tab1, tab2, tab3 = st.tabs(["📋 Data Table", "📊 Charts", "💾 Export"])

                            with tab1:
                                st.dataframe(df, use_container_width=True, hide_index=True)

                            with tab2:
                                # Top anchors by backlinks
                                fig = px.bar(
                                    df.head(20),
                                    x='Backlinks',
                                    y='Anchor',
                                    orientation='h',
                                    title="Top 20 Anchors by Backlinks"
                                )
                                fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                                st.plotly_chart(fig, use_container_width=True)

                                # Word cloud-like visualization
                                fig2 = px.treemap(
                                    df.head(50),
                                    path=['Anchor'],
                                    values='Backlinks',
                                    title="Anchor Text Distribution"
                                )
                                st.plotly_chart(fig2, use_container_width=True)

                            with tab3:
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    "📥 Download CSV",
                                    csv,
                                    f"anchors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    "text/csv"
                                )
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Referring Domains":
        st.header("🌐 Referring Domains")
        st.markdown("Analyse domains linking to your target")

        target_input = st.text_input(
            "Target",
            placeholder="Enter domain (e.g., example.com) or full URL"
        )

        col1, col2 = st.columns(2)
        with col1:
            limit = st.number_input("Limit", min_value=1, max_value=1000, value=100)
        with col2:
            include_subdomains = st.checkbox("Include Subdomains", value=True)

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Get Referring Domains", type="primary", use_container_width=True)

        if analyse_btn:
            if not target_input.strip():
                st.error("Please enter a target domain or URL.")
            else:
                with st.spinner("Fetching referring domains..."):
                    response = client.get_referring_domains(
                        target=target_input.strip(),
                        limit=limit,
                        include_subdomains=include_subdomains
                    )

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success(f"✅ Found {result.get('total_count', 0):,} referring domains!")

                        if 'items' in result and result['items']:
                            domains_data = []
                            for item in result['items']:
                                domains_data.append({
                                    'Domain': item.get('domain', ''),
                                    'Backlinks': item.get('backlinks', 0),
                                    'Rank': item.get('rank', 0),
                                    'First Seen': item.get('first_seen', ''),
                                    'Spam Score': item.get('backlinks_spam_score', 0),
                                    'Broken Backlinks': item.get('broken_backlinks', 0)
                                })

                            df = pd.DataFrame(domains_data)

                            tab1, tab2, tab3 = st.tabs(["📋 Data Table", "📊 Charts", "💾 Export"])

                            with tab1:
                                st.dataframe(df, use_container_width=True, hide_index=True)

                            with tab2:
                                # Top domains by backlinks
                                fig = px.bar(
                                    df.head(20),
                                    x='Backlinks',
                                    y='Domain',
                                    orientation='h',
                                    title="Top 20 Referring Domains by Backlinks"
                                )
                                fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                                st.plotly_chart(fig, use_container_width=True)

                                # Domain rank distribution
                                fig2 = px.histogram(
                                    df,
                                    x='Rank',
                                    nbins=20,
                                    title="Domain Rank Distribution"
                                )
                                st.plotly_chart(fig2, use_container_width=True)

                            with tab3:
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    "📥 Download CSV",
                                    csv,
                                    f"referring_domains_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    "text/csv"
                                )
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Backlink Summary":
        st.header("📊 Backlink Summary")
        st.markdown("Get a comprehensive overview of backlink metrics for a domain")

        target_input = st.text_input(
            "Target",
            placeholder="Enter domain (e.g., example.com) or full URL"
        )

        include_subdomains = st.checkbox("Include Subdomains", value=True)

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Get Summary", type="primary", use_container_width=True)

        if analyse_btn:
            if not target_input.strip():
                st.error("Please enter a target domain or URL.")
            else:
                with st.spinner("Fetching backlink summary..."):
                    response = client.get_backlink_summary(
                        target=target_input.strip(),
                        include_subdomains=include_subdomains
                    )

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success("✅ Summary retrieved!")

                        # Key metrics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Backlinks", f"{result.get('backlinks', 0):,}")
                        with col2:
                            st.metric("Referring Domains", f"{result.get('referring_domains', 0):,}")
                        with col3:
                            st.metric("Referring IPs", f"{result.get('referring_ips', 0):,}")
                        with col4:
                            st.metric("Rank", f"{result.get('rank', 0):,}")

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Crawled Pages", f"{result.get('crawled_pages', 0):,}")
                        with col2:
                            st.metric("External Links", f"{result.get('external_links_count', 0):,}")
                        with col3:
                            st.metric("Internal Links", f"{result.get('internal_links_count', 0):,}")
                        with col4:
                            st.metric("Spam Score", f"{result.get('backlinks_spam_score', 0)}")

                        st.markdown("---")

                        # Link types breakdown
                        col1, col2 = st.columns(2)

                        with col1:
                            st.subheader("Link Types")
                            if 'referring_links_types' in result and result['referring_links_types']:
                                types_df = pd.DataFrame([
                                    {'Type': k, 'Count': v}
                                    for k, v in result['referring_links_types'].items()
                                ])
                                fig = px.pie(types_df, values='Count', names='Type', title="Link Types Distribution")
                                st.plotly_chart(fig, use_container_width=True)

                        with col2:
                            st.subheader("Link Attributes")
                            if 'referring_links_attributes' in result and result['referring_links_attributes']:
                                attrs_df = pd.DataFrame([
                                    {'Attribute': k, 'Count': v}
                                    for k, v in result['referring_links_attributes'].items()
                                ])
                                fig = px.bar(attrs_df, x='Attribute', y='Count', title="Link Attributes")
                                st.plotly_chart(fig, use_container_width=True)

                        # TLD Distribution
                        if 'referring_links_tld' in result and result['referring_links_tld']:
                            st.subheader("TLD Distribution")
                            tld_data = result['referring_links_tld']
                            tld_df = pd.DataFrame([
                                {'TLD': k, 'Count': v}
                                for k, v in sorted(tld_data.items(), key=lambda x: x[1], reverse=True)[:20]
                            ])
                            fig = px.bar(tld_df, x='TLD', y='Count', title="Top 20 TLDs")
                            st.plotly_chart(fig, use_container_width=True)

                        # Export
                        st.download_button(
                            "📥 Download Full Report (JSON)",
                            json.dumps(response, indent=2),
                            f"backlink_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            "application/json"
                        )
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Bulk Backlinks Overview":
        st.header("📊 Bulk Backlinks Overview")
        st.markdown("Get backlink counts for multiple domains at once (up to 1000)")

        targets_input = st.text_area(
            "Targets",
            placeholder="Enter domains or URLs (one per line)\n\nexample.com\nanothersite.com\nthirdsite.org",
            height=150
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Analyse", type="primary", use_container_width=True)

        if analyse_btn:
            targets = [t.strip() for t in targets_input.strip().split('\n') if t.strip()]
            if not targets:
                st.error("Please enter at least one target.")
            elif len(targets) > 1000:
                st.error("Maximum 1000 targets allowed.")
            else:
                with st.spinner(f"Analyzing {len(targets)} targets..."):
                    response = client.get_bulk_backlinks(targets)

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success("✅ Analysis complete!")

                        if 'items' in result:
                            df = pd.DataFrame([
                                {'Target': item.get('target', ''), 'Backlinks': item.get('backlinks', 0)}
                                for item in result['items']
                            ])
                            df = df.sort_values('Backlinks', ascending=False)

                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Total Targets", len(df))
                            with col2:
                                st.metric("Total Backlinks", f"{df['Backlinks'].sum():,}")

                            st.dataframe(df, use_container_width=True, hide_index=True)

                            fig = px.bar(df.head(20), x='Target', y='Backlinks', title="Backlinks Comparison")
                            st.plotly_chart(fig, use_container_width=True)

                            csv = df.to_csv(index=False)
                            st.download_button("📥 Download CSV", csv, "bulk_backlinks.csv", "text/csv")
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Bulk Referring Domains Overview":
        st.header("🌐 Bulk Referring Domains Overview")
        st.markdown("Get referring domain counts for multiple domains at once")

        targets_input = st.text_area(
            "Targets",
            placeholder="Enter domains or URLs (one per line)",
            height=150
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Analyse", type="primary", use_container_width=True)

        if analyse_btn:
            targets = [t.strip() for t in targets_input.strip().split('\n') if t.strip()]
            if not targets:
                st.error("Please enter at least one target.")
            elif len(targets) > 1000:
                st.error("Maximum 1000 targets allowed.")
            else:
                with st.spinner(f"Analyzing {len(targets)} targets..."):
                    response = client.get_bulk_referring_domains(targets)

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success("✅ Analysis complete!")

                        if 'items' in result:
                            df = pd.DataFrame([
                                {
                                    'Target': item.get('target', ''),
                                    'Referring Domains': item.get('referring_domains', 0),
                                    'Referring Main Domains': item.get('referring_main_domains', 0),
                                    'Nofollow Domains': item.get('referring_domains_nofollow', 0)
                                }
                                for item in result['items']
                            ])
                            df = df.sort_values('Referring Domains', ascending=False)

                            st.dataframe(df, use_container_width=True, hide_index=True)

                            fig = px.bar(df.head(20), x='Target', y='Referring Domains', title="Referring Domains Comparison")
                            st.plotly_chart(fig, use_container_width=True)

                            csv = df.to_csv(index=False)
                            st.download_button("📥 Download CSV", csv, "bulk_referring_domains.csv", "text/csv")
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Bulk Backlink Rank Checker":
        st.header("📈 Bulk Backlink Rank Checker")
        st.markdown("Get rank scores for multiple domains at once")

        targets_input = st.text_area(
            "Targets",
            placeholder="Enter domains or URLs (one per line)",
            height=150
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Check Ranks", type="primary", use_container_width=True)

        if analyse_btn:
            targets = [t.strip() for t in targets_input.strip().split('\n') if t.strip()]
            if not targets:
                st.error("Please enter at least one target.")
            elif len(targets) > 1000:
                st.error("Maximum 1000 targets allowed.")
            else:
                with st.spinner(f"Checking ranks for {len(targets)} targets..."):
                    response = client.get_bulk_ranks(targets)

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success("✅ Analysis complete!")

                        if 'items' in result:
                            df = pd.DataFrame([
                                {'Target': item.get('target', ''), 'Rank': item.get('rank', 0)}
                                for item in result['items']
                            ])
                            df = df.sort_values('Rank', ascending=False)

                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Total Targets", len(df))
                            with col2:
                                st.metric("Average Rank", f"{df['Rank'].mean():.0f}")

                            st.dataframe(df, use_container_width=True, hide_index=True)

                            fig = px.bar(df.head(20), x='Target', y='Rank', title="Domain Rank Comparison")
                            st.plotly_chart(fig, use_container_width=True)

                            csv = df.to_csv(index=False)
                            st.download_button("📥 Download CSV", csv, "bulk_ranks.csv", "text/csv")
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Bulk Backlink Spam Score":
        st.header("🚫 Bulk Backlink Spam Score")
        st.markdown("Get spam scores for multiple domains at once (0-100 scale)")

        targets_input = st.text_area(
            "Targets",
            placeholder="Enter domains or URLs (one per line)",
            height=150
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Check Spam Scores", type="primary", use_container_width=True)

        if analyse_btn:
            targets = [t.strip() for t in targets_input.strip().split('\n') if t.strip()]
            if not targets:
                st.error("Please enter at least one target.")
            elif len(targets) > 1000:
                st.error("Maximum 1000 targets allowed.")
            else:
                with st.spinner(f"Checking spam scores for {len(targets)} targets..."):
                    response = client.get_bulk_spam_score(targets)

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success("✅ Analysis complete!")

                        if 'items' in result:
                            df = pd.DataFrame([
                                {'Target': item.get('target', ''), 'Spam Score': item.get('spam_score', 0)}
                                for item in result['items']
                            ])
                            df = df.sort_values('Spam Score', ascending=False)

                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Total Targets", len(df))
                            with col2:
                                st.metric("Average Spam Score", f"{df['Spam Score'].mean():.1f}")

                            # Color code by spam level
                            st.dataframe(df, use_container_width=True, hide_index=True)

                            fig = px.bar(
                                df.head(20),
                                x='Target',
                                y='Spam Score',
                                title="Spam Score Comparison",
                                color='Spam Score',
                                color_continuous_scale='RdYlGn_r'
                            )
                            st.plotly_chart(fig, use_container_width=True)

                            csv = df.to_csv(index=False)
                            st.download_button("📥 Download CSV", csv, "bulk_spam_scores.csv", "text/csv")
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Bulk New&Lost Backlinks Overview":
        st.header("📈📉 Bulk New & Lost Backlinks")
        st.markdown("Track new and lost backlinks for multiple domains")

        targets_input = st.text_area(
            "Targets",
            placeholder="Enter domains or URLs (one per line)",
            height=150
        )

        date_from = st.date_input(
            "Date From",
            value=datetime.now().replace(day=1),
            help="Compare from this date (default: 1 month ago)"
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Analyse", type="primary", use_container_width=True)

        if analyse_btn:
            targets = [t.strip() for t in targets_input.strip().split('\n') if t.strip()]
            if not targets:
                st.error("Please enter at least one target.")
            elif len(targets) > 1000:
                st.error("Maximum 1000 targets allowed.")
            else:
                with st.spinner(f"Analyzing {len(targets)} targets..."):
                    response = client.get_bulk_new_lost_backlinks(
                        targets,
                        date_from=date_from.strftime('%Y-%m-%d')
                    )

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success("✅ Analysis complete!")

                        if 'items' in result:
                            df = pd.DataFrame([
                                {
                                    'Target': item.get('target', ''),
                                    'New Backlinks': item.get('new_backlinks', 0),
                                    'Lost Backlinks': item.get('lost_backlinks', 0),
                                    'Net Change': item.get('new_backlinks', 0) - item.get('lost_backlinks', 0)
                                }
                                for item in result['items']
                            ])

                            st.dataframe(df, use_container_width=True, hide_index=True)

                            fig = px.bar(
                                df.head(20),
                                x='Target',
                                y=['New Backlinks', 'Lost Backlinks'],
                                title="New vs Lost Backlinks",
                                barmode='group'
                            )
                            st.plotly_chart(fig, use_container_width=True)

                            csv = df.to_csv(index=False)
                            st.download_button("📥 Download CSV", csv, "new_lost_backlinks.csv", "text/csv")
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Bulk New&Lost Referring Domains Overview":
        st.header("📈📉 Bulk New & Lost Referring Domains")
        st.markdown("Track new and lost referring domains for multiple targets")

        targets_input = st.text_area(
            "Targets",
            placeholder="Enter domains or URLs (one per line)",
            height=150
        )

        date_from = st.date_input(
            "Date From",
            value=datetime.now().replace(day=1),
            help="Compare from this date"
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Analyse", type="primary", use_container_width=True)

        if analyse_btn:
            targets = [t.strip() for t in targets_input.strip().split('\n') if t.strip()]
            if not targets:
                st.error("Please enter at least one target.")
            elif len(targets) > 1000:
                st.error("Maximum 1000 targets allowed.")
            else:
                with st.spinner(f"Analyzing {len(targets)} targets..."):
                    response = client.get_bulk_new_lost_referring_domains(
                        targets,
                        date_from=date_from.strftime('%Y-%m-%d')
                    )

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success("✅ Analysis complete!")

                        if 'items' in result:
                            df = pd.DataFrame([
                                {
                                    'Target': item.get('target', ''),
                                    'New Domains': item.get('new_referring_domains', 0),
                                    'Lost Domains': item.get('lost_referring_domains', 0),
                                    'Net Change': item.get('new_referring_domains', 0) - item.get('lost_referring_domains', 0)
                                }
                                for item in result['items']
                            ])

                            st.dataframe(df, use_container_width=True, hide_index=True)

                            fig = px.bar(
                                df.head(20),
                                x='Target',
                                y=['New Domains', 'Lost Domains'],
                                title="New vs Lost Referring Domains",
                                barmode='group'
                            )
                            st.plotly_chart(fig, use_container_width=True)

                            csv = df.to_csv(index=False)
                            st.download_button("📥 Download CSV", csv, "new_lost_referring_domains.csv", "text/csv")
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    # ===================== SERP & RANKINGS TOOLS =====================

    elif function_type == "SERP Parser":
        st.header("🔍 SERP Parser")
        st.markdown("Get Google organic search results for a keyword")

        keyword_input = st.text_input(
            "Keyword",
            placeholder="Enter search keyword",
            help="The keyword to search for"
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            device = st.selectbox("Device", ["desktop", "mobile"])
        with col2:
            depth = st.number_input("Depth", min_value=10, max_value=200, value=100, step=10)
        with col3:
            pass  # Reserved for future options

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Parse SERP", type="primary", use_container_width=True)

        if analyse_btn:
            if not keyword_input.strip():
                st.error("Please enter a keyword.")
            else:
                with st.spinner("Fetching SERP data..."):
                    response = client.get_serp_organic(
                        keyword=keyword_input.strip(),
                        location=location,
                        language=language,
                        device=device,
                        depth=depth
                    )

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success("✅ SERP data retrieved!")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Results", f"{result.get('se_results_count', 0):,}")
                        with col2:
                            st.metric("Items Returned", result.get('items_count', 0))
                        with col3:
                            if 'cost' in task:
                                st.metric("Cost (USD)", f"${task['cost']:.4f}")

                        if 'items' in result and result['items']:
                            organic_results = []
                            for item in result['items']:
                                if item.get('type') == 'organic':
                                    organic_results.append({
                                        'Position': item.get('rank_absolute', 0),
                                        'Title': item.get('title', ''),
                                        'URL': item.get('url', ''),
                                        'Domain': item.get('domain', ''),
                                        'Description': item.get('description', '')[:100] + '...' if item.get('description') else ''
                                    })

                            if organic_results:
                                df = pd.DataFrame(organic_results)
                                st.dataframe(df, use_container_width=True, hide_index=True)

                                csv = df.to_csv(index=False)
                                st.download_button("📥 Download CSV", csv, "serp_results.csv", "text/csv")

                        st.download_button(
                            "📥 Download Full Response (JSON)",
                            json.dumps(response, indent=2),
                            "serp_full.json",
                            "application/json"
                        )
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Bulk Rank Tracking (Google)":
        st.header("📊 Bulk Rank Tracking")
        st.markdown("Track rankings for multiple keywords at once")

        keywords_input = st.text_area(
            "Keywords",
            placeholder="Enter keywords (one per line)",
            height=150
        )

        target_domain = st.text_input(
            "Target Domain (Optional)",
            placeholder="Enter domain to highlight (e.g., example.com)",
            help="If provided, will highlight where this domain ranks"
        )

        col1, col2 = st.columns(2)
        with col1:
            device = st.selectbox("Device", ["desktop", "mobile"])
        with col2:
            pass

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Track Rankings", type="primary", use_container_width=True)

        if analyse_btn:
            keywords = [k.strip() for k in keywords_input.strip().split('\n') if k.strip()]
            if not keywords:
                st.error("Please enter at least one keyword.")
            elif len(keywords) > 100:
                st.error("Maximum 100 keywords allowed per request.")
            else:
                with st.spinner(f"Tracking {len(keywords)} keywords..."):
                    response = client.get_bulk_serp(
                        keywords=keywords,
                        location=location,
                        language=language,
                        device=device
                    )

                if response and 'tasks' in response:
                    results_data = []
                    for task in response['tasks']:
                        if task['status_code'] == 20000 and task.get('result'):
                            result = task['result'][0]
                            keyword = result.get('keyword', '')

                            target_position = None
                            top_3 = []

                            if 'items' in result:
                                for item in result['items']:
                                    if item.get('type') == 'organic':
                                        pos = item.get('rank_absolute', 0)
                                        domain = item.get('domain', '')

                                        if pos <= 3:
                                            top_3.append(domain)

                                        if target_domain and target_domain.lower() in domain.lower():
                                            target_position = pos

                            results_data.append({
                                'Keyword': keyword,
                                'Target Position': target_position if target_position else 'Not in Top 100',
                                'Top 1': top_3[0] if len(top_3) > 0 else '',
                                'Top 2': top_3[1] if len(top_3) > 1 else '',
                                'Top 3': top_3[2] if len(top_3) > 2 else ''
                            })

                    if results_data:
                        st.success(f"✅ Tracked {len(results_data)} keywords!")
                        df = pd.DataFrame(results_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)

                        csv = df.to_csv(index=False)
                        st.download_button("📥 Download CSV", csv, "rank_tracking.csv", "text/csv")

    elif function_type == "Organic Domain Rank Overview":
        st.header("📈 Organic Domain Rank Overview")
        st.markdown("Get ranking distribution and traffic metrics for a domain")

        target_input = st.text_input(
            "Target Domain",
            placeholder="Enter domain (e.g., example.com)",
            help="Domain without https:// or www"
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Get Overview", type="primary", use_container_width=True)

        if analyse_btn:
            if not target_input.strip():
                st.error("Please enter a target domain.")
            else:
                with st.spinner("Fetching domain rank overview..."):
                    response = client.get_domain_rank_overview(
                        target=target_input.strip(),
                        location=location,
                        language=language
                    )

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        
                        # Check if we have actual data - metrics are inside items array
                        items_count = result.get('items_count', 0)
                        items = result.get('items')
                        
                        if items_count == 0 or not items:
                            # No data found for this domain
                            st.warning(f"⚠️ No ranking data found for **{target_input.strip()}** in {location}.")
                            st.info("""
**Possible reasons:**
- The domain may be new or have very low search visibility
- The domain may not rank for any keywords in the selected location/language
- The domain name may be misspelled

**Try:**
- Check the domain spelling
- Try a different location or language
- Use a more established domain to verify the tool is working
                            """)
                        else:
                            st.success(f"✅ Domain overview for **{target_input.strip()}**")
                            
                            # Get metrics from items[0]
                            item_data = items[0]
                            metrics = item_data.get('metrics', {})
                            
                            # Create tabs for Organic and Paid
                            tab_organic, tab_paid, tab_export = st.tabs(["🌿 Organic Search", "💰 Paid Search", "💾 Export"])
                            
                            with tab_organic:
                                if 'organic' in metrics:
                                    organic = metrics['organic']
                                    
                                    # Key metrics row
                                    st.markdown("### 📊 Key Metrics")
                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        etv = organic.get('etv', 0) or 0
                                        st.metric("🚀 Est. Monthly Traffic", f"{etv:,.0f}")
                                    with col2:
                                        count = organic.get('count', 0) or 0
                                        st.metric("🔑 Keywords Ranking", f"{count:,}")
                                    with col3:
                                        cost = organic.get('estimated_paid_traffic_cost', 0) or 0
                                        st.metric("💵 Traffic Value", f"${cost:,.0f}")
                                    with col4:
                                        pos1 = organic.get('pos_1', 0) or 0
                                        st.metric("🥇 #1 Rankings", f"{pos1:,}")
                                    
                                    st.divider()
                                    
                                    # Movement metrics
                                    st.markdown("### 📈 Keyword Movement")
                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        is_new = organic.get('is_new', 0) or 0
                                        st.metric("🆕 New Keywords", f"{is_new:,}", delta="new", delta_color="normal")
                                    with col2:
                                        is_up = organic.get('is_up', 0) or 0
                                        st.metric("⬆️ Moved Up", f"{is_up:,}", delta=f"+{is_up:,}" if is_up else None, delta_color="normal")
                                    with col3:
                                        is_down = organic.get('is_down', 0) or 0
                                        st.metric("⬇️ Moved Down", f"{is_down:,}", delta=f"-{is_down:,}" if is_down else None, delta_color="inverse")
                                    with col4:
                                        is_lost = organic.get('is_lost', 0) or 0
                                        st.metric("❌ Lost Keywords", f"{is_lost:,}", delta=f"-{is_lost:,}" if is_lost else None, delta_color="inverse")
                                    
                                    st.divider()
                                    
                                    # Position distribution chart
                                    st.markdown("### 📊 Ranking Position Distribution")
                                    
                                    # Build position data with proper ordering
                                    position_order = ['1', '2_3', '4_10', '11_20', '21_30', '31_40', '41_50', '51_60', '61_70', '71_80', '81_90', '91_100']
                                    pos_labels = ['#1', '#2-3', '#4-10', '#11-20', '#21-30', '#31-40', '#41-50', '#51-60', '#61-70', '#71-80', '#81-90', '#91-100']
                                    
                                    pos_data = []
                                    for pos_key, label in zip(position_order, pos_labels):
                                        value = organic.get(f'pos_{pos_key}', 0) or 0
                                        pos_data.append({'Position': label, 'Keywords': value, 'order': position_order.index(pos_key)})
                                    
                                    if pos_data:
                                        pos_df = pd.DataFrame(pos_data)
                                        pos_df = pos_df.sort_values('order')
                                        
                                        # Create bar chart with color gradient
                                        fig = px.bar(
                                            pos_df, 
                                            x='Position', 
                                            y='Keywords',
                                            color='Keywords',
                                            color_continuous_scale='Greens',
                                            text='Keywords'
                                        )
                                        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                                        fig.update_layout(
                                            xaxis_title="SERP Position",
                                            yaxis_title="Number of Keywords",
                                            showlegend=False,
                                            coloraxis_showscale=False,
                                            height=400
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                                    
                                    # Show data table
                                    with st.expander("📋 View Raw Data"):
                                        display_df = pos_df[['Position', 'Keywords']].copy()
                                        display_df['Keywords'] = display_df['Keywords'].apply(lambda x: f"{x:,}")
                                        st.dataframe(display_df, use_container_width=True, hide_index=True)
                                else:
                                    st.info("No organic search data available for this domain.")
                            
                            with tab_paid:
                                if 'paid' in metrics:
                                    paid = metrics['paid']
                                    
                                    # Check if there's any paid data
                                    paid_count = paid.get('count', 0) or 0
                                    
                                    if paid_count == 0:
                                        st.info("🔍 No paid search data found for this domain. This domain may not be running Google Ads campaigns in this location.")
                                    else:
                                        # Key metrics row
                                        st.markdown("### 💰 Paid Search Metrics")
                                        col1, col2, col3, col4 = st.columns(4)
                                        with col1:
                                            etv = paid.get('etv', 0) or 0
                                            st.metric("🚀 Est. Monthly Traffic", f"{etv:,.0f}")
                                        with col2:
                                            st.metric("🔑 Keywords", f"{paid_count:,}")
                                        with col3:
                                            cost = paid.get('estimated_paid_traffic_cost', 0) or 0
                                            st.metric("💵 Ad Spend Est.", f"${cost:,.0f}")
                                        with col4:
                                            pos1 = paid.get('pos_1', 0) or 0
                                            st.metric("🥇 #1 Ad Position", f"{pos1:,}")
                                        
                                        # Position distribution for paid
                                        st.divider()
                                        st.markdown("### 📊 Ad Position Distribution")
                                        
                                        pos_data = []
                                        for pos_key, label in zip(position_order, pos_labels):
                                            value = paid.get(f'pos_{pos_key}', 0) or 0
                                            pos_data.append({'Position': label, 'Keywords': value, 'order': position_order.index(pos_key)})
                                        
                                        if any(p['Keywords'] > 0 for p in pos_data):
                                            pos_df = pd.DataFrame(pos_data)
                                            pos_df = pos_df.sort_values('order')
                                            
                                            fig = px.bar(
                                                pos_df, 
                                                x='Position', 
                                                y='Keywords',
                                                color='Keywords',
                                                color_continuous_scale='Blues',
                                                text='Keywords'
                                            )
                                            fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                                            fig.update_layout(
                                                xaxis_title="Ad Position",
                                                yaxis_title="Number of Keywords",
                                                showlegend=False,
                                                coloraxis_showscale=False,
                                                height=400
                                            )
                                            st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.info("No paid search data available for this domain.")
                            
                            with tab_export:
                                st.markdown("### 💾 Export Options")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.download_button(
                                        "📥 Download Full Report (JSON)",
                                        json.dumps(response, indent=2),
                                        f"domain_rank_overview_{target_input.strip().replace('.', '_')}.json",
                                        "application/json",
                                        use_container_width=True
                                    )
                                
                                with col2:
                                    # Create CSV export of key metrics
                                    if 'organic' in metrics:
                                        organic = metrics['organic']
                                        export_data = {
                                            'Metric': ['Est. Monthly Traffic', 'Keywords Ranking', 'Traffic Value ($)', '#1 Rankings', 
                                                      'New Keywords', 'Keywords Up', 'Keywords Down', 'Lost Keywords'],
                                            'Value': [
                                                organic.get('etv', 0) or 0,
                                                organic.get('count', 0) or 0,
                                                organic.get('estimated_paid_traffic_cost', 0) or 0,
                                                organic.get('pos_1', 0) or 0,
                                                organic.get('is_new', 0) or 0,
                                                organic.get('is_up', 0) or 0,
                                                organic.get('is_down', 0) or 0,
                                                organic.get('is_lost', 0) or 0
                                            ]
                                        }
                                        export_df = pd.DataFrame(export_data)
                                        csv_data = export_df.to_csv(index=False)
                                        st.download_button(
                                            "📥 Download Summary (CSV)",
                                            csv_data,
                                            f"domain_metrics_{target_input.strip().replace('.', '_')}.csv",
                                            "text/csv",
                                            use_container_width=True
                                        )
                                
                                # Show raw JSON preview
                                with st.expander("🔍 Preview Raw API Response"):
                                    st.json(response)
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Organic Traffic Estimation":
        st.header("📈 Organic Traffic Estimation")
        st.markdown("Get historical traffic data for a domain")

        target_input = st.text_input(
            "Target Domain",
            placeholder="Enter domain (e.g., example.com)"
        )

        col1, col2 = st.columns(2)
        with col1:
            date_from = st.date_input(
                "Date From",
                value=datetime.now().replace(month=datetime.now().month - 6 if datetime.now().month > 6 else datetime.now().month + 6, year=datetime.now().year if datetime.now().month > 6 else datetime.now().year - 1)
            )
        with col2:
            date_to = st.date_input("Date To", value=datetime.now())

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Get Traffic Data", type="primary", use_container_width=True)

        if analyse_btn:
            if not target_input.strip():
                st.error("Please enter a target domain.")
            else:
                with st.spinner("Fetching historical traffic data..."):
                    response = client.get_historical_rank_overview(
                        target=target_input.strip(),
                        location=location,
                        language=language,
                        date_from=date_from.strftime('%Y-%m-%d'),
                        date_to=date_to.strftime('%Y-%m-%d')
                    )

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success("✅ Data retrieved!")

                        if 'items' in result and result['items']:
                            traffic_data = []
                            for item in result['items']:
                                if 'metrics' in item and 'organic' in item['metrics']:
                                    organic = item['metrics']['organic']
                                    traffic_data.append({
                                        'Date': item.get('date', ''),
                                        'Estimated Traffic': organic.get('etv', 0),
                                        'Keywords': organic.get('count', 0),
                                        'Traffic Cost': organic.get('estimated_paid_traffic_cost', 0)
                                    })

                            if traffic_data:
                                df = pd.DataFrame(traffic_data)
                                df['Date'] = pd.to_datetime(df['Date'])
                                df = df.sort_values('Date')

                                fig = px.line(
                                    df,
                                    x='Date',
                                    y='Estimated Traffic',
                                    title="Organic Traffic Over Time"
                                )
                                st.plotly_chart(fig, use_container_width=True)

                                fig2 = px.line(
                                    df,
                                    x='Date',
                                    y='Keywords',
                                    title="Ranking Keywords Over Time"
                                )
                                st.plotly_chart(fig2, use_container_width=True)

                                st.dataframe(df, use_container_width=True, hide_index=True)

                                csv = df.to_csv(index=False)
                                st.download_button("📥 Download CSV", csv, "traffic_history.csv", "text/csv")
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Ranked Keywords":
        st.header("🎯 Ranked Keywords")
        st.markdown("Get keywords a domain is ranking for in Google")

        target_input = st.text_input(
            "Target",
            placeholder="Enter domain (e.g., example.com) or full URL"
        )

        col1, col2 = st.columns(2)
        with col1:
            limit = st.number_input("Limit", min_value=1, max_value=1000, value=100)
        with col2:
            item_types = st.multiselect(
                "Result Types",
                ["organic", "paid", "featured_snippet", "local_pack"],
                default=["organic"]
            )

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Get Keywords", type="primary", use_container_width=True)

        if analyse_btn:
            if not target_input.strip():
                st.error("Please enter a target domain or URL.")
            else:
                with st.spinner("Fetching ranked keywords..."):
                    response = client.get_ranked_keywords(
                        target=target_input.strip(),
                        location=location,
                        language=language,
                        limit=limit,
                        item_types=item_types if item_types else None
                    )

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success(f"✅ Found {result.get('total_count', 0):,} ranking keywords!")

                        if 'items' in result and result['items']:
                            keywords_data = []
                            for item in result['items']:
                                kw_info = item.get('keyword_data', {}).get('keyword_info', {})
                                keywords_data.append({
                                    'Keyword': item.get('keyword_data', {}).get('keyword', ''),
                                    'Position': item.get('rank_absolute', 0),
                                    'Search Volume': kw_info.get('search_volume', 0),
                                    'CPC': kw_info.get('cpc', 0),
                                    'Competition': kw_info.get('competition_level', ''),
                                    'URL': item.get('url', ''),
                                    'Type': item.get('type', '')
                                })

                            df = pd.DataFrame(keywords_data)

                            tab1, tab2, tab3 = st.tabs(["📋 Data", "📊 Charts", "💾 Export"])

                            with tab1:
                                st.dataframe(df, use_container_width=True, hide_index=True)

                            with tab2:
                                # Position distribution
                                fig = px.histogram(df, x='Position', nbins=20, title="Position Distribution")
                                st.plotly_chart(fig, use_container_width=True)

                                # Search volume distribution
                                fig2 = px.scatter(
                                    df.head(100),
                                    x='Position',
                                    y='Search Volume',
                                    text='Keyword',
                                    title="Position vs Search Volume"
                                )
                                st.plotly_chart(fig2, use_container_width=True)

                            with tab3:
                                csv = df.to_csv(index=False)
                                st.download_button("📥 Download CSV", csv, "ranked_keywords.csv", "text/csv")
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Page Load Time":
        st.header("⏱️ Page Load Time")
        st.markdown("Analyse page load performance and Core Web Vitals")

        url_input = st.text_input(
            "URL",
            placeholder="Enter full URL (e.g., https://example.com/page)",
            help="Include https://"
        )

        col1, col2 = st.columns(2)
        with col1:
            enable_js = st.checkbox("Enable JavaScript", value=True)
        with col2:
            enable_rendering = st.checkbox("Enable Browser Rendering", value=True)

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Analyse", type="primary", use_container_width=True)

        if analyse_btn:
            if not url_input.strip():
                st.error("Please enter a URL.")
            elif not url_input.startswith('http'):
                st.error("URL must start with http:// or https://")
            else:
                with st.spinner("Analyzing page performance..."):
                    response = client.get_instant_pages(
                        url=url_input.strip(),
                        enable_javascript=enable_js,
                        enable_browser_rendering=enable_rendering
                    )

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success("✅ Analysis complete!")

                        if 'items' in result and result['items']:
                            item = result['items'][0]

                            # Core Web Vitals
                            st.subheader("🎯 Core Web Vitals")

                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                page_timing = item.get('page_timing', {})
                                st.metric("Time to Interactive", f"{page_timing.get('time_to_interactive', 0):.2f}s")
                            with col2:
                                st.metric("DOM Complete", f"{page_timing.get('dom_complete', 0):.2f}s")
                            with col3:
                                st.metric("Connection Time", f"{page_timing.get('connection_time', 0):.3f}s")
                            with col4:
                                st.metric("Download Time", f"{page_timing.get('download_time', 0):.3f}s")

                            # OnPage Score
                            st.subheader("📊 Page Metrics")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("OnPage Score", f"{item.get('onpage_score', 0):.1f}/100")
                            with col2:
                                st.metric("Page Size", f"{item.get('size', 0) / 1024:.1f} KB")
                            with col3:
                                st.metric("Status Code", item.get('status_code', ''))
                            with col4:
                                st.metric("Encoding", item.get('content_encoding', 'none'))

                        st.download_button(
                            "📥 Download Full Report (JSON)",
                            json.dumps(response, indent=2),
                            "page_performance.json",
                            "application/json"
                        )
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Page Audit Checks":
        st.header("🔍 Page Audit Checks")
        st.markdown("Get comprehensive SEO audit for a page")

        url_input = st.text_input(
            "URL",
            placeholder="Enter full URL (e.g., https://example.com/page)"
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Audit Page", type="primary", use_container_width=True)

        if analyse_btn:
            if not url_input.strip():
                st.error("Please enter a URL.")
            elif not url_input.startswith('http'):
                st.error("URL must start with http:// or https://")
            else:
                with st.spinner("Running page audit..."):
                    response = client.get_instant_pages(
                        url=url_input.strip(),
                        enable_javascript=True,
                        enable_browser_rendering=True
                    )

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success("✅ Audit complete!")

                        if 'items' in result and result['items']:
                            item = result['items'][0]

                            col1, col2 = st.columns(2)

                            with col1:
                                st.subheader("📝 Meta Information")
                                meta = item.get('meta', {})
                                st.markdown(f"**Title:** {meta.get('title', 'N/A')}")
                                st.markdown(f"**Description:** {meta.get('description', 'N/A')}")
                                st.markdown(f"**Canonical:** {meta.get('canonical', 'N/A')}")
                                st.markdown(f"**Robots:** {', '.join(meta.get('robots', []))}")

                            with col2:
                                st.subheader("📊 Page Stats")
                                st.metric("OnPage Score", f"{item.get('onpage_score', 0):.1f}/100")
                                st.metric("Total DOM Elements", item.get('total_dom_size', 0))
                                st.metric("Words on Page", item.get('content', {}).get('plain_text_word_count', 0))

                            # Checks
                            if 'checks' in item:
                                st.subheader("✅ Audit Checks")
                                checks = item['checks']
                                passed = sum(1 for v in checks.values() if v is True)
                                failed = sum(1 for v in checks.values() if v is False)

                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Passed", passed, delta_color="normal")
                                with col2:
                                    st.metric("Failed", failed, delta_color="inverse")

                                # List failed checks
                                failed_checks = [k for k, v in checks.items() if v is False]
                                if failed_checks:
                                    st.warning("**Issues Found:**")
                                    for check in failed_checks:
                                        st.markdown(f"- {check.replace('_', ' ').title()}")

                        st.download_button(
                            "📥 Download Full Report (JSON)",
                            json.dumps(response, indent=2),
                            "page_audit.json",
                            "application/json"
                        )
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    # ===================== KEYWORDS TOOLS =====================

    elif function_type == "Keyword Search Intent":
        st.header("🎯 Keyword Search Intent")
        st.markdown("Classify keywords by search intent (informational, navigational, commercial, transactional)")

        keywords_input = st.text_area(
            "Keywords",
            placeholder="Enter keywords (one per line, up to 1000)",
            height=150
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Analyse Intent", type="primary", use_container_width=True)

        if analyse_btn:
            keywords = [k.strip() for k in keywords_input.strip().split('\n') if k.strip()]
            if not keywords:
                st.error("Please enter at least one keyword.")
            elif len(keywords) > 1000:
                st.error("Maximum 1000 keywords allowed.")
            else:
                with st.spinner(f"Analyzing intent for {len(keywords)} keywords..."):
                    response = client.get_search_intent(keywords, language)

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success("✅ Analysis complete!")

                        if 'items' in result and result['items']:
                            intent_data = []
                            for item in result['items']:
                                intent_info = item.get('keyword_intent', {})
                                intent_data.append({
                                    'Keyword': item.get('keyword', ''),
                                    'Intent': intent_info.get('label', ''),
                                    'Probability': f"{intent_info.get('probability', 0):.2%}"
                                })

                            df = pd.DataFrame(intent_data)

                            tab1, tab2, tab3 = st.tabs(["📋 Data", "📊 Charts", "💾 Export"])

                            with tab1:
                                st.dataframe(df, use_container_width=True, hide_index=True)

                            with tab2:
                                intent_counts = df['Intent'].value_counts()
                                fig = px.pie(
                                    values=intent_counts.values,
                                    names=intent_counts.index,
                                    title="Search Intent Distribution"
                                )
                                st.plotly_chart(fig, use_container_width=True)

                            with tab3:
                                csv = df.to_csv(index=False)
                                st.download_button("📥 Download CSV", csv, "search_intent.csv", "text/csv")
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Keywords Difficulty":
        st.header("📊 Keywords Difficulty")
        st.markdown("Get keyword difficulty scores (0-100 scale)")

        keywords_input = st.text_area(
            "Keywords",
            placeholder="Enter keywords (one per line, up to 1000)",
            height=150
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Check Difficulty", type="primary", use_container_width=True)

        if analyse_btn:
            keywords = [k.strip() for k in keywords_input.strip().split('\n') if k.strip()]
            if not keywords:
                st.error("Please enter at least one keyword.")
            elif len(keywords) > 1000:
                st.error("Maximum 1000 keywords allowed.")
            else:
                with st.spinner(f"Checking difficulty for {len(keywords)} keywords..."):
                    response = client.get_bulk_keyword_difficulty(keywords, location, language)

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success("✅ Analysis complete!")

                        if 'items' in result and result['items']:
                            diff_data = []
                            for item in result['items']:
                                diff_data.append({
                                    'Keyword': item.get('keyword', ''),
                                    'Difficulty': item.get('keyword_difficulty', 0)
                                })

                            df = pd.DataFrame(diff_data)
                            df = df.sort_values('Difficulty', ascending=False)

                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Keywords Analysed", len(df))
                            with col2:
                                st.metric("Average Difficulty", f"{df['Difficulty'].mean():.1f}")

                            st.dataframe(df, use_container_width=True, hide_index=True)

                            fig = px.histogram(df, x='Difficulty', nbins=20, title="Keyword Difficulty Distribution")
                            st.plotly_chart(fig, use_container_width=True)

                            csv = df.to_csv(index=False)
                            st.download_button("📥 Download CSV", csv, "keyword_difficulty.csv", "text/csv")
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Google Search Volume":
        st.header("📊 Google Search Volume")
        st.markdown("Get search volume data from Google Ads")

        keywords_input = st.text_area(
            "Keywords",
            placeholder="Enter keywords (one per line, up to 1000)",
            height=150
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Get Volume", type="primary", use_container_width=True)

        if analyse_btn:
            keywords = [k.strip() for k in keywords_input.strip().split('\n') if k.strip()]
            if not keywords:
                st.error("Please enter at least one keyword.")
            elif len(keywords) > 1000:
                st.error("Maximum 1000 keywords allowed.")
            else:
                with st.spinner(f"Fetching volume for {len(keywords)} keywords..."):
                    response = client.get_google_search_volume(keywords, location, language)

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success("✅ Data retrieved!")

                        if 'items' in result:
                            volume_data = []
                            for item in result['items']:
                                volume_data.append({
                                    'Keyword': item.get('keyword', ''),
                                    'Search Volume': item.get('search_volume', 0),
                                    'CPC': item.get('cpc', 0),
                                    'Competition': item.get('competition', ''),
                                    'Competition Index': item.get('competition_index', 0),
                                    'Low Bid': item.get('low_top_of_page_bid', 0),
                                    'High Bid': item.get('high_top_of_page_bid', 0)
                                })

                            df = pd.DataFrame(volume_data)
                            df = df.sort_values('Search Volume', ascending=False)

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Keywords", len(df))
                            with col2:
                                st.metric("Total Volume", f"{df['Search Volume'].sum():,}")
                            with col3:
                                st.metric("Avg CPC", f"${df['CPC'].mean():.2f}")

                            tab1, tab2, tab3 = st.tabs(["📋 Data", "📊 Charts", "💾 Export"])

                            with tab1:
                                st.dataframe(df, use_container_width=True, hide_index=True)

                            with tab2:
                                fig = px.bar(
                                    df.head(20),
                                    x='Keyword',
                                    y='Search Volume',
                                    title="Top 20 Keywords by Search Volume"
                                )
                                st.plotly_chart(fig, use_container_width=True)

                                fig2 = px.scatter(
                                    df,
                                    x='Search Volume',
                                    y='CPC',
                                    text='Keyword',
                                    title="Search Volume vs CPC"
                                )
                                st.plotly_chart(fig2, use_container_width=True)

                            with tab3:
                                csv = df.to_csv(index=False)
                                st.download_button("📥 Download CSV", csv, "google_search_volume.csv", "text/csv")
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Bing Search Volume":
        st.header("📊 Bing Search Volume")
        st.markdown("Get search volume data from Bing")

        keywords_input = st.text_area(
            "Keywords",
            placeholder="Enter keywords (one per line, up to 1000)",
            height=150
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Get Volume", type="primary", use_container_width=True)

        if analyse_btn:
            keywords = [k.strip() for k in keywords_input.strip().split('\n') if k.strip()]
            if not keywords:
                st.error("Please enter at least one keyword.")
            elif len(keywords) > 1000:
                st.error("Maximum 1000 keywords allowed.")
            else:
                with st.spinner(f"Fetching volume for {len(keywords)} keywords..."):
                    response = client.get_bing_search_volume(keywords, location, language)

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success("✅ Data retrieved!")

                        if 'items' in result:
                            volume_data = []
                            for item in result['items']:
                                volume_data.append({
                                    'Keyword': item.get('keyword', ''),
                                    'Search Volume': item.get('search_volume', 0),
                                    'CPC': item.get('cpc', 0),
                                    'Competition': item.get('competition', 0)
                                })

                            df = pd.DataFrame(volume_data)
                            df = df.sort_values('Search Volume', ascending=False)

                            st.dataframe(df, use_container_width=True, hide_index=True)

                            fig = px.bar(
                                df.head(20),
                                x='Keyword',
                                y='Search Volume',
                                title="Top 20 Keywords by Bing Search Volume"
                            )
                            st.plotly_chart(fig, use_container_width=True)

                            csv = df.to_csv(index=False)
                            st.download_button("📥 Download CSV", csv, "bing_search_volume.csv", "text/csv")
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Keyword Suggestions":
        st.header("💡 Keyword Suggestions")
        st.markdown("Get keyword suggestions based on a seed keyword")

        seed_keyword = st.text_input(
            "Seed Keyword",
            placeholder="Enter your seed keyword"
        )

        col1, col2 = st.columns(2)
        with col1:
            limit = st.number_input("Limit", min_value=1, max_value=1000, value=100)
        with col2:
            include_seed = st.checkbox("Include Seed Keyword", value=False)

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Get Suggestions", type="primary", use_container_width=True)

        if analyse_btn:
            if not seed_keyword.strip():
                st.error("Please enter a seed keyword.")
            else:
                with st.spinner("Fetching keyword suggestions..."):
                    response = client.get_keyword_suggestions(
                        keyword=seed_keyword.strip(),
                        location=location,
                        language=language,
                        limit=limit,
                        include_seed=include_seed
                    )

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success(f"✅ Found {result.get('total_count', 0):,} suggestions!")

                        if 'items' in result and result['items']:
                            suggestions_data = []
                            for item in result['items']:
                                kw_info = item.get('keyword_info', {})
                                kw_props = item.get('keyword_properties', {})
                                intent_info = item.get('search_intent_info', {})
                                suggestions_data.append({
                                    'Keyword': item.get('keyword', ''),
                                    'Search Volume': kw_info.get('search_volume', 0),
                                    'CPC': kw_info.get('cpc', 0),
                                    'Competition': kw_info.get('competition_level', ''),
                                    'Difficulty': kw_props.get('keyword_difficulty', 0),
                                    'Intent': intent_info.get('main_intent', '')
                                })

                            df = pd.DataFrame(suggestions_data)
                            df = df.sort_values('Search Volume', ascending=False)

                            tab1, tab2, tab3 = st.tabs(["📋 Data", "📊 Charts", "💾 Export"])

                            with tab1:
                                st.dataframe(df, use_container_width=True, hide_index=True)

                            with tab2:
                                fig = px.bar(
                                    df.head(20),
                                    x='Keyword',
                                    y='Search Volume',
                                    title="Top 20 Keyword Suggestions"
                                )
                                st.plotly_chart(fig, use_container_width=True)

                                if df['Intent'].any():
                                    intent_counts = df['Intent'].value_counts()
                                    fig2 = px.pie(values=intent_counts.values, names=intent_counts.index, title="Intent Distribution")
                                    st.plotly_chart(fig2, use_container_width=True)

                            with tab3:
                                csv = df.to_csv(index=False)
                                st.download_button("📥 Download CSV", csv, "keyword_suggestions.csv", "text/csv")
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Similar Keywords":
        st.header("🔄 Similar Keywords")
        st.markdown("Find related keyword ideas based on seed keywords")

        keywords_input = st.text_area(
            "Seed Keywords",
            placeholder="Enter seed keywords (one per line, up to 200)",
            height=100
        )

        limit = st.number_input("Limit", min_value=1, max_value=1000, value=100)

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Find Similar", type="primary", use_container_width=True)

        if analyse_btn:
            keywords = [k.strip() for k in keywords_input.strip().split('\n') if k.strip()]
            if not keywords:
                st.error("Please enter at least one seed keyword.")
            elif len(keywords) > 200:
                st.error("Maximum 200 seed keywords allowed.")
            else:
                with st.spinner("Finding similar keywords..."):
                    response = client.get_keyword_ideas(keywords, location, language, limit)

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success(f"✅ Found {result.get('total_count', 0):,} related keywords!")

                        if 'items' in result and result['items']:
                            ideas_data = []
                            for item in result['items']:
                                kw_info = item.get('keyword_info', {})
                                kw_props = item.get('keyword_properties', {})
                                ideas_data.append({
                                    'Keyword': item.get('keyword', ''),
                                    'Search Volume': kw_info.get('search_volume', 0),
                                    'CPC': kw_info.get('cpc', 0),
                                    'Competition': kw_info.get('competition_level', ''),
                                    'Difficulty': kw_props.get('keyword_difficulty', 0)
                                })

                            df = pd.DataFrame(ideas_data)
                            df = df.sort_values('Search Volume', ascending=False)

                            st.dataframe(df, use_container_width=True, hide_index=True)

                            csv = df.to_csv(index=False)
                            st.download_button("📥 Download CSV", csv, "similar_keywords.csv", "text/csv")
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Website Keyword Suggestions":
        st.header("🌐 Website Keyword Suggestions")
        st.markdown("Get keyword suggestions relevant to a website")

        target_input = st.text_input(
            "Target Domain",
            placeholder="Enter domain (e.g., example.com)"
        )

        limit = st.number_input("Limit", min_value=1, max_value=1000, value=100)

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Get Keywords", type="primary", use_container_width=True)

        if analyse_btn:
            if not target_input.strip():
                st.error("Please enter a target domain.")
            else:
                with st.spinner("Fetching keyword suggestions..."):
                    response = client.get_keywords_for_site(
                        target=target_input.strip(),
                        location=location,
                        language=language,
                        limit=limit
                    )

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success(f"✅ Found {result.get('total_count', 0):,} keywords!")

                        if 'items' in result and result['items']:
                            keywords_data = []
                            for item in result['items']:
                                kw_info = item.get('keyword_info', {})
                                kw_props = item.get('keyword_properties', {})
                                keywords_data.append({
                                    'Keyword': item.get('keyword', ''),
                                    'Search Volume': kw_info.get('search_volume', 0),
                                    'CPC': kw_info.get('cpc', 0),
                                    'Competition': kw_info.get('competition_level', ''),
                                    'Difficulty': kw_props.get('keyword_difficulty', 0)
                                })

                            df = pd.DataFrame(keywords_data)
                            df = df.sort_values('Search Volume', ascending=False)

                            tab1, tab2, tab3 = st.tabs(["📋 Data", "📊 Charts", "💾 Export"])

                            with tab1:
                                st.dataframe(df, use_container_width=True, hide_index=True)

                            with tab2:
                                fig = px.bar(
                                    df.head(20),
                                    x='Keyword',
                                    y='Search Volume',
                                    title="Top Keywords for Website"
                                )
                                st.plotly_chart(fig, use_container_width=True)

                            with tab3:
                                csv = df.to_csv(index=False)
                                st.download_button("📥 Download CSV", csv, "website_keywords.csv", "text/csv")
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    elif function_type == "Keyword Suggestions for Categories":
        st.header("📂 Keywords for Categories")
        st.markdown("Get keywords for specific product/service categories")

        # Common category codes from DataForSEO
        category_options = {
            "Apparel": 10166,
            "Arts & Entertainment": 10003,
            "Autos & Vehicles": 10047,
            "Beauty & Fitness": 10044,
            "Books & Literature": 10022,
            "Business & Industrial": 10012,
            "Computers & Electronics": 10063,
            "Finance": 10007,
            "Food & Drink": 10071,
            "Games": 10017,
            "Health": 10045,
            "Hobbies & Leisure": 10065,
            "Home & Garden": 10069,
            "Internet & Telecom": 10013,
            "Jobs & Education": 10023,
            "Law & Government": 10019,
            "News": 10016,
            "Online Communities": 10299,
            "People & Society": 10014,
            "Pets & Animals": 10066,
            "Real Estate": 10029,
            "Reference": 10020,
            "Science": 10174,
            "Shopping": 10018,
            "Sports": 10020,
            "Travel": 10067
        }

        selected_categories = st.multiselect(
            "Select Categories",
            options=list(category_options.keys()),
            help="Select up to 20 categories"
        )

        limit = st.number_input("Limit", min_value=1, max_value=1000, value=100)

        col1, col2 = st.columns([1, 4])
        with col1:
            analyse_btn = st.button("🔍 Get Keywords", type="primary", use_container_width=True)

        if analyse_btn:
            if not selected_categories:
                st.error("Please select at least one category.")
            elif len(selected_categories) > 20:
                st.error("Maximum 20 categories allowed.")
            else:
                category_codes = [category_options[cat] for cat in selected_categories]

                with st.spinner("Fetching keywords for categories..."):
                    response = client.get_keywords_for_categories(
                        category_codes=category_codes,
                        location=location,
                        language=language,
                        limit=limit
                    )

                if response and 'tasks' in response and response['tasks']:
                    task = response['tasks'][0]
                    if task['status_code'] == 20000 and task.get('result'):
                        result = task['result'][0]
                        st.success(f"✅ Found {result.get('total_count', 0):,} keywords!")

                        if 'items' in result and result['items']:
                            keywords_data = []
                            for item in result['items']:
                                kw_info = item.get('keyword_info', {})
                                kw_props = item.get('keyword_properties', {})
                                keywords_data.append({
                                    'Keyword': item.get('keyword', ''),
                                    'Search Volume': kw_info.get('search_volume', 0),
                                    'CPC': kw_info.get('cpc', 0),
                                    'Competition': kw_info.get('competition_level', ''),
                                    'Difficulty': kw_props.get('keyword_difficulty', 0)
                                })

                            df = pd.DataFrame(keywords_data)
                            df = df.sort_values('Search Volume', ascending=False)

                            st.dataframe(df, use_container_width=True, hide_index=True)

                            fig = px.bar(
                                df.head(20),
                                x='Keyword',
                                y='Search Volume',
                                title="Top Keywords by Category"
                            )
                            st.plotly_chart(fig, use_container_width=True)

                            csv = df.to_csv(index=False)
                            st.download_button("📥 Download CSV", csv, "category_keywords.csv", "text/csv")
                    else:
                        st.error(f"Error: {task.get('status_message', 'Unknown error')}")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Powered by <a href='https://dataforseo.com' target='_blank'>DataForSEO</a> API |
        Built with Streamlit |
        Built by <a href='https://indexify.co.uk' target='_blank'>Indexify</a></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
