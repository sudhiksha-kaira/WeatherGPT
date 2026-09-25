import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

import streamlit as st

from gtts import gTTS
from streamlit_geolocation import streamlit_geolocation
from groq import Groq
from dotenv import load_dotenv

from utils.weather_api import (
    get_weather,
    get_weather_by_coordinates,
    get_forecast
)

from utils.ai_response import (
    ask_weather_ai
)

from utils.weather_alerts import (
    generate_weather_alerts
)

from utils.voice_input import (
    transcribe_audio
)
from utils.question_classifier import classify_question

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

groq_client = Groq(
    api_key=GROQ_API_KEY
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="WeatherGPT",
    page_icon="🌦️",
    layout="wide"
)

# ============================================================
# PROFESSIONAL DASHBOARD STYLE
# ============================================================

st.markdown(
    """
    <style>

    /* Main page */
    .main {
        padding-top: 1rem;
    }

    /* WeatherGPT title */
    .weather-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .weather-subtitle {
        font-size: 18px;
        opacity: 0.75;
        margin-bottom: 25px;
    }

    /* Weather cards */
    .weather-card {
        padding: 20px;
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.25);
        text-align: center;
        min-height: 130px;
    }

    .weather-card-title {
        font-size: 15px;
        opacity: 0.7;
        margin-bottom: 8px;
    }

    .weather-card-value {
        font-size: 30px;
        font-weight: 700;
    }

    /* Section headings */
    .section-title {
        font-size: 25px;
        font-weight: 650;
        margin-top: 20px;
        margin-bottom: 15px;
    }

    /* Alert cards */
    .alert-card {
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
        border: 1px solid rgba(255, 100, 100, 0.35);
    }

    /* Forecast cards */
    .forecast-card {
        padding: 15px;
        border-radius: 14px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        margin-bottom: 10px;
    }

    /* AI response */
    .ai-card {
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(100, 150, 255, 0.25);
        margin-top: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)
def get_weather_icon(condition):
    condition = condition.lower()

    if "thunderstorm" in condition:
        return "⛈️"
    elif "rain" in condition or "drizzle" in condition:
        return "🌧️"
    elif "snow" in condition:
        return "❄️"
    elif "clear" in condition:
        return "☀️"
    elif "cloud" in condition:
        return "☁️"
    elif "mist" in condition or "fog" in condition or "haze" in condition:
        return "🌫️"
    else:
        return "🌤️"

# ============================================================
# LANGUAGE LIST
# ============================================================

LANGUAGE_CODES = {

    "English": "en",

    # Indian languages
    "Telugu": "te",
    "Hindi": "hi",
    "Tamil": "ta",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Marathi": "mr",
    "Bengali": "bn",
    "Gujarati": "gu",
    "Punjabi": "pa",
    "Odia": "or",
    "Assamese": "as",
    "Urdu": "ur",

    # European languages
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Dutch": "nl",
    "Polish": "pl",
    "Ukrainian": "uk",
    "Greek": "el",
    "Romanian": "ro",
    "Czech": "cs",
    "Hungarian": "hu",
    "Swedish": "sv",
    "Danish": "da",
    "Norwegian": "no",
    "Finnish": "fi",

    # Asian languages
    "Chinese": "zh",
    "Japanese": "ja",
    "Korean": "ko",
    "Thai": "th",
    "Vietnamese": "vi",
    "Indonesian": "id",
    "Malay": "ms",
    "Filipino": "fil",

    # Middle Eastern languages
    "Arabic": "ar",
    "Persian": "fa",
    "Turkish": "tr",
    "Hebrew": "he",

    # Other
    "Swahili": "sw",
    "Afrikaans": "af"
}


# ============================================================
# AI LANGUAGE DETECTION
# ============================================================

def detect_response_language(question):

    language_list = ", ".join(
        [
            f"{name} ({code})"
            for name, code in LANGUAGE_CODES.items()
        ]
    )

    prompt = f"""
You are a language detection assistant.

Determine the language in which the user wants
WeatherGPT to answer.

IMPORTANT:

The user may write a language using English
letters instead of its native script.

Examples:

"Naku Telugu lo answer cheppu"
means the user wants Telugu.

"mujhe Hindi mein jawab do"
means the user wants Hindi.

"answer in Tamil"
means the user wants Tamil.

"please answer in English"
means the user wants English.

Do NOT decide only from the alphabet/script.

Understand the meaning and the user's requested
response language.

Available languages and codes:

{language_list}

User message:

{question}

Return ONLY the two-letter language code.

Examples:

Telugu -> te
Hindi -> hi
English -> en
Spanish -> es

Do not return anything else.
"""

    try:

        response = groq_client.chat.completions.create(

            model="openai/gpt-oss-20b",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0
        )

        detected_code = (
            response
            .choices[0]
            .message
            .content
            .strip()
            .lower()
        )

        # Clean possible extra text
        detected_code = (
            detected_code
            .replace("`", "")
            .replace(".", "")
            .strip()
        )

        if detected_code in LANGUAGE_CODES.values():

            return detected_code

    except Exception:

        pass

    return "en"


# ============================================================
# GET LANGUAGE NAME
# ============================================================

def get_language_name(language_code):

    for name, code in LANGUAGE_CODES.items():

        if code == language_code:
            return name

    return "English"


# ============================================================
# SESSION STATE
# ============================================================

if "weather" not in st.session_state:
    st.session_state.weather = None

if "forecast" not in st.session_state:
    st.session_state.forecast = None

if "alerts" not in st.session_state:
    st.session_state.alerts = []

if "error" not in st.session_state:
    st.session_state.error = None

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="weather-title">🌦️ WeatherGPT</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="weather-subtitle">'
    'Conversational AI for Weather Forecasting, '
    'Alerts, and Climate Information.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# LOCATION SELECTOR
# ============================================================

st.markdown(
    '<div class="section-title">📍 Choose Location</div>',
    unsafe_allow_html=True
)

st.caption(
    "Use your current location or search for a city or village."
)

location_mode = st.radio(
    "Location method",
    [
        "📍 Use Current Location",
        "✏️ Enter Location Manually"
    ],
    horizontal=True,
    label_visibility="collapsed"
)


# ============================================================
# CURRENT LOCATION
# ============================================================

if location_mode == "📍 Use Current Location":

    st.write(
        "Click the button below and allow your browser "
        "to access your location."
    )

    current_location = streamlit_geolocation()

    if (
        current_location
        and current_location.get("latitude") is not None
        and current_location.get("longitude") is not None
    ):

        latitude = float(
            current_location["latitude"]
        )

        longitude = float(
            current_location["longitude"]
        )

        st.success(
            "📍 Current location detected."
        )

        st.write(
            f"Latitude: {latitude:.6f}"
        )

        st.write(
            f"Longitude: {longitude:.6f}"
        )

        if st.button(
            "🌦️ Get Weather for Current Location",
            key="current_location_get_weather"
        ):

            weather, error = (
                get_weather_by_coordinates(
                    latitude,
                    longitude
                )
            )

            if weather:

                st.session_state.weather = weather
                st.session_state.error = None

                forecast, forecast_error = (
                    get_forecast(
                        latitude,
                        longitude
                    )
                )

                if forecast:

                    st.session_state.forecast = forecast

                    st.session_state.alerts = (
                        generate_weather_alerts(
                            forecast
                        )
                    )

                else:

                    st.session_state.forecast = None
                    st.session_state.alerts = []

                if forecast_error:

                    st.warning(
                        f"Forecast warning: "
                        f"{forecast_error}"
                    )

            else:

                st.session_state.weather = None
                st.session_state.forecast = None
                st.session_state.alerts = []

                st.session_state.error = error


    else:

        st.info(
            "📍 Press the location button above "
            "to detect your current location."
        )


# ============================================================
# MANUAL LOCATION
# ============================================================

else:

    location = st.text_input(
        "Location",
        placeholder="Example: Hyderabad or Bahakal"
    )

    col1, col2 = st.columns(2)

    with col1:

        state = st.text_input(
            "State / Region",
            placeholder="Example: Telangana"
        )

    with col2:

        country = st.text_input(
            "Country",
            placeholder="Example: India"
        )


    if st.button("🔍 Get Weather",
                 key="manual_get_weather"):

        if not location:

            st.warning(
                "Please enter a location."
            )

        else:

            weather, error = get_weather(
                location,
                state,
                country
            )

            if weather:

                st.session_state.weather = weather
                st.session_state.error = None

                forecast, forecast_error = (
                    get_forecast(
                        weather["latitude"],
                        weather["longitude"]
                    )
                )

                if forecast:

                    st.session_state.forecast = forecast

                    st.session_state.alerts = (
                        generate_weather_alerts(
                            forecast
                        )
                    )

                else:

                    st.session_state.forecast = None
                    st.session_state.alerts = []

                if forecast_error:

                    st.warning(
                        f"Forecast warning: "
                        f"{forecast_error}"
                    )

            else:

                st.session_state.weather = None
                st.session_state.forecast = None
                st.session_state.alerts = []

                st.session_state.error = error


# ============================================================
# GET WEATHER
# ============================================================

if st.button("🔍 Get Weather"):

    if not location:

        st.warning(
            "Please enter a location."
        )

    else:

        weather, error = get_weather(
            location,
            state,
            country
        )

        if weather:

            st.session_state.weather = weather
            st.session_state.error = None

            forecast, forecast_error = get_forecast(
                weather["latitude"],
                weather["longitude"]
            )

            if forecast:

                st.session_state.forecast = forecast

                st.session_state.alerts = (
                    generate_weather_alerts(
                        forecast
                    )
                )

            else:

                st.session_state.forecast = None
                st.session_state.alerts = []

            if forecast_error:

                st.warning(
                    f"Forecast warning: "
                    f"{forecast_error}"
                )

        else:

            st.session_state.weather = None
            st.session_state.forecast = None
            st.session_state.alerts = []

            st.session_state.error = error


# ============================================================
# DISPLAY WEATHER
# ============================================================

if st.session_state.weather:

    weather = st.session_state.weather
    forecast = st.session_state.forecast
    alerts = st.session_state.alerts


    # ========================================================
    # LOCATION RESULT
    # ========================================================

    st.success(
        f"Weather information for "
        f"{weather['city']}, "
        f"{weather['state']}, "
        f"{weather['country']}"
    )

    # ========================================================
    # WEATHER SUMMARY
    # ========================================================

    st.markdown(
      f"""
      <div style="
        padding: 25px;
        border-radius: 18px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-top: 20px;
        margin-bottom: 20px;
     ">

        <div style="
            font-size: 16px;
            opacity: 0.7;
            margin-bottom: 8px;
        ">
            📍 Weather for
        </div>

        <div style="
            font-size: 30px;
            font-weight: 700;
            margin-bottom: 8px;
        ">
            {weather['city']}
        </div>

        <div style="
            font-size: 17px;
            opacity: 0.75;
            margin-bottom: 18px;
        ">
            {weather['state']}, {weather['country']}
        </div>

        <div style="font-size:38px;font-weight:700;">
            {get_weather_icon(weather['condition'])} {weather['temperature']} °C
        </div>
        <div style="font-size:18px;margin-top:5px;">
            {get_weather_icon(weather['condition'])} {weather['condition'].title()}
        </div>

        <div style="
            font-size: 15px;
            opacity: 0.7;
            margin-top: 8px;
        ">
            Feels like {weather['feels_like']} °C
        </div>

      </div>
      """,
      unsafe_allow_html=True
    )


    # ========================================================
    # CURRENT WEATHER DASHBOARD
    # ========================================================

    st.divider()

    st.markdown(
    '<div class="section-title">🌤️ Current Weather</div>',
    unsafe_allow_html=True
    )


    # --------------------------------------------------------
    # WEATHER CARDS
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

     st.markdown(
        f"""
        <div class="weather-card">
            <div class="weather-card-title">
                🌡️ Temperature
            </div>
            <div class="weather-card-value">
                {weather['temperature']} °C
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


    with col2:

     st.markdown(
        f"""
        <div class="weather-card">
            <div class="weather-card-title">
                🤗 Feels Like
            </div>
            <div class="weather-card-value">
                {weather['feels_like']} °C
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


    with col3:

     st.markdown(
        f"""
        <div class="weather-card">
            <div class="weather-card-title">
                💧 Humidity
            </div>
            <div class="weather-card-value">
                {weather['humidity']}%
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


    st.write("")


    col4, col5, col6 = st.columns(3)

    with col4:

     st.markdown(
        f"""
        <div class="weather-card">
            <div class="weather-card-title">
                💨 Wind Speed
            </div>
            <div class="weather-card-value">
                {weather['wind_speed']} m/s
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


    with col5:

     st.markdown(
        f"""
        <div class="weather-card">
            <div class="weather-card-title">
                📊 Pressure
            </div>
            <div class="weather-card-value">
                {weather['pressure']} hPa
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


    with col6:

     st.markdown(
        f"""
        <div class="weather-card">
            <div class="weather-card-title">
                ☁️ Condition
            </div>
            <div class="weather-card-value">
               {get_weather_icon(weather['condition'])}
               {weather['condition'].title()}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # LOCATION DETAILS
    # ========================================================

    st.divider()

    st.subheader("📍 Location Details")

    st.write(
        f"**Latitude:** "
        f"{weather['latitude']}"
    )

    st.write(
        f"**Longitude:** "
        f"{weather['longitude']}"
    )


    # ========================================================
    # WEATHER ALERTS
    # ========================================================

    st.divider()

    st.markdown(
    '<div class="section-title">🚨 Weather Alerts</div>',
    unsafe_allow_html=True
    )

    if alerts:

     st.warning(
        f"⚠️ {len(alerts)} weather alert(s) detected."
     )

     for alert in alerts:

        alert_html = (
            '<div class="alert-card">'
            f'<h4>{alert["type"]}</h4>'
            f'<p>🕒 <b>{alert["datetime"]}</b></p>'
            f'<p>{alert["message"]}</p>'
            '</div>'
        )

        st.markdown(
            alert_html,
            unsafe_allow_html=True
        )

    else:

     st.success(
        "✅ No significant weather alerts "
        "detected in the available forecast."
    )

    # ========================================================
    # FORECAST CARDS
    # ========================================================

    st.divider()

    st.markdown(
    '<div class="section-title">📅 Upcoming Weather Forecast</div>',
    unsafe_allow_html=True
    )

    st.caption(
    "Forecast conditions for the upcoming hours."
    )

    for item in forecast[:8]:

     forecast_html = (
        '<div class="forecast-card">'

        f'<h4> {get_weather_icon(item["condition"])} 🕒 {item["datetime"]} </h4>'

        '<div style="display:flex; '
        'flex-wrap:wrap; gap:25px; '
        'margin-top:15px;">'

        f'<div>'
        f'<b>🌡️ Temperature</b><br>'
        f'{item["temperature"]} °C'
        f'</div>'

        f'<div>'
        f'<b>💧 Humidity</b><br>'
        f'{item["humidity"]}%'
        f'</div>'

        f'<div>'
        f'<b>💨 Wind</b><br>'
        f'{item["wind_speed"]} m/s'
        f'</div>'

        f'<div>'
        f'<b>🌧️ Rain Probability</b><br>'
        f'{item["rain_probability"] * 100:.0f}%'
        f'</div>'

        f'<div><b>{get_weather_icon(item["condition"])} Condition</b><br>{item["condition"].title()}</div>'

        '</div>'

        '</div>'
    )

    st.markdown(
        forecast_html,
        unsafe_allow_html=True
    )


    # ========================================================
    # WEATHERGPT AI ASSISTANT
    # ========================================================

    st.divider()

    st.markdown(
    '<div class="section-title">💬 WeatherGPT AI Assistant</div>',
    unsafe_allow_html=True
    )

    st.caption(
    "Ask about weather, forecasts, climate, rainfall, "
    "temperature, or weather safety."
    )


    # ========================================================
    # TEXT QUESTION
    # ========================================================

    typed_question = st.text_input(
       "💬 Your Question",
       placeholder="Example: Will it rain tomorrow?",
       key="weather_question"
    )


    # ========================================================
    # VOICE QUESTION
    # ========================================================

    st.write("🎙️ Or ask using your voice")

    audio_input = st.audio_input(
    "Speak your question"
    )


    # ========================================================
    # QUESTION PROCESSING
    # ========================================================

    question = typed_question.strip()


    if audio_input:

       with st.spinner(
        "🎙️ Understanding your speech..."
       ):

        voice_text, voice_error = (
            transcribe_audio(
                audio_input
            )
        )

       if voice_error:

        st.error(
            f"Voice recognition error: "
            f"{voice_error}"
        )

       elif voice_text:

        question = voice_text

        st.info(
            f"🎙️ You said: {voice_text}"
        )


    # ========================================================
    # AI RESPONSE
    # ========================================================

    if st.button(
    "🤖 Ask WeatherGPT",
    key="ask_weather_gpt"
    ):

      if not question:

        st.warning(
            "Please enter a question or use your voice."
        )

    else:

       with st.spinner(
        "🤖 WeatherGPT is thinking..."
       ):

        detected_language_code = detect_response_language(question)
        detected_language = get_language_name(detected_language_code)

        question_category = classify_question(question)

        answer = ask_weather_ai(
           question,
           weather,
           forecast,
           detected_language_code,
           question_category,
           st.session_state.conversation_history
        )

        st.session_state.conversation_history.append(
            {
                "role": "user",
                "content": question
            }
        )

        st.session_state.conversation_history.append(
            {
                "role": "assistant",
                "content": answer
            }
        )


       # ====================================================
       # DETECTED LANGUAGE
       # ====================================================

       st.markdown(
          f"""
          <div class="ai-card">
            <b>🌐 Response Language</b><br>
            {detected_language}
           </div>
           """,
           unsafe_allow_html=True
        )


        # ====================================================
        # USER QUESTION
        # ====================================================

       st.markdown(
           f"""
           <div class="ai-card">
             <b>👤 Your Question</b>
             <p>{question}</p>
          </div>
          """,
          unsafe_allow_html=True
        )


        # ====================================================
        # AI ANSWER
        # ====================================================

       st.markdown(
          f"""
          <div class="ai-card">
            <h3>🤖 WeatherGPT</h3>
            <p>{answer}</p>
          </div>
          """,
          unsafe_allow_html=True
        )


        # ====================================================
        # TEXT TO SPEECH
        # ====================================================

       try:

         tts = gTTS(
            text=answer,
            lang=detected_language_code,
            slow=False
         )

         audio_file = "weather_response.mp3"

         tts.save(
            audio_file
         )

         st.write(
            "🔊 Listen to WeatherGPT"
         )

         st.audio(
            audio_file,
            format="audio/mp3"
         )

       except Exception as e:

         st.warning(
            f"Text-to-Speech error: {e}"

         )

    # ============================================================
    # CONVERSATION HISTORY
    # ============================================================

    if st.session_state.conversation_history:

     st.divider()

     st.markdown(
        '<div class="section-title">💬 Conversation History</div>',
        unsafe_allow_html=True
     )

     history = st.session_state.conversation_history

     for message in history:

        if message["role"] == "user":

            st.markdown(
                f"""
                <div class="ai-card">
                    <b>👤 You</b>
                    <p>{message["content"]}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        elif message["role"] == "assistant":

            st.markdown(
                f"""
                <div class="ai-card">
                    <b>🤖 WeatherGPT</b>
                    <p>{message["content"]}</p>
                </div>
                """,
                unsafe_allow_html=True
            )


    # ============================================================
    # CLEAR CONVERSATION
    #  ============================================================

    if st.session_state.conversation_history:

     if st.button(
        "🗑️ Clear Conversation",
        key="clear_conversation"
     ):

        st.session_state.conversation_history = []

        st.rerun()
# ============================================================
# DISPLAY ERROR
# ============================================================

elif st.session_state.error:

    st.error(
        f"❌ Weather API error: "
        f"{st.session_state.error}"
    )