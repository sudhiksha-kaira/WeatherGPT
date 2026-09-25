import os
from dotenv import load_dotenv
from groq import Groq
from rag.retriever import retrieve_information

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)


LANGUAGE_NAMES = {
    "en": "English",
    "te": "Telugu",
    "hi": "Hindi",
    "ta": "Tamil",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
    "ur": "Urdu",

    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "pl": "Polish",
    "uk": "Ukrainian",
    "el": "Greek",
    "ro": "Romanian",
    "cs": "Czech",
    "hu": "Hungarian",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "fi": "Finnish",

    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "th": "Thai",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "ms": "Malay",
    "fil": "Filipino",

    "ar": "Arabic",
    "fa": "Persian",
    "tr": "Turkish",
    "he": "Hebrew",
    "sw": "Swahili",
    "af": "Afrikaans"
}


def ask_weather_ai(
    question,
    weather,
    forecast=None,
    language_code="en",
    question_category="GENERAL_WEATHER",
    conversation_history=None
):

    language = LANGUAGE_NAMES.get(
        language_code,
        "English"
    )

    # --------------------------------------------------
    # CURRENT WEATHER
    # --------------------------------------------------

    weather_text = ""

    if weather:

        weather_text = f"""
Current weather:

Location: {weather.get("city", "")}
State: {weather.get("state", "")}
Country: {weather.get("country", "")}

Temperature: {weather.get("temperature", "")} °C
Feels Like: {weather.get("feels_like", "")} °C
Humidity: {weather.get("humidity", "")}%
Pressure: {weather.get("pressure", "")} hPa
Wind Speed: {weather.get("wind_speed", "")} m/s
Condition: {weather.get("condition", "")}

Latitude: {weather.get("latitude", "")}
Longitude: {weather.get("longitude", "")}
"""

    # --------------------------------------------------
    # FORECAST
    # --------------------------------------------------

    forecast_text = ""

    if forecast:

        forecast_text = "\nForecast information:\n"

        for item in forecast:

            forecast_text += (
                f"{item['datetime']} | "
                f"Temperature: {item['temperature']} °C | "
                f"Feels Like: {item['feels_like']} °C | "
                f"Humidity: {item['humidity']}% | "
                f"Wind: {item['wind_speed']} m/s | "
                f"Condition: {item['condition']} | "
                f"Rain probability: "
                f"{item['rain_probability'] * 100:.0f}%\n"
            )

    # --------------------------------------------------
    # RAG
    # --------------------------------------------------

    retrieved = retrieve_information(
        question,
        limit=3
    )

    knowledge_text = ""

    if retrieved:

        knowledge_text = (
            "\nRelevant weather and climate knowledge:\n"
        )

        for item in retrieved:

            knowledge_text += (
                item["text"] +
                "\n\n"
            )

    # --------------------------------------------------
    # CONVERSATION HISTORY
    # --------------------------------------------------

    history_text = ""

    if conversation_history:

        history_text = "\nPrevious conversation:\n"

        for message in conversation_history[-6:]:

            role = message.get(
                "role",
                "user"
            )

            content = message.get(
                "content",
                ""
            )

            history_text += (
                f"{role}: {content}\n"
            )

    # --------------------------------------------------
    # AI PROMPT
    # --------------------------------------------------

    prompt = f"""
You are WeatherGPT, a multilingual conversational
weather and climate assistant.

The user wants the response in:

{language}

Question category:

{question_category}

{weather_text}

{forecast_text}

{knowledge_text}

{history_text}

User's current question:

{question}

IMPORTANT RULES:

1. Always answer in {language}.

2. Use the current weather data when the question
   is about current conditions.

3. Use forecast data when the question is about
   future weather.

4. Use the knowledge retrieved from the RAG system
   for general weather and climate questions.

5. You may combine weather data and RAG knowledge
   when both are relevant.

6. Never invent weather information.

7. If weather data is unavailable, clearly say that
   current weather information is unavailable.

8. If the question is unrelated to weather or climate,
   politely explain that WeatherGPT mainly specializes
   in weather and climate information.

9. If the user asks about weather safety, provide
   practical safety advice based on the available
   weather information and retrieved knowledge.

10. Keep answers clear and easy to understand.

11. Use numbers and units when useful.

12. Consider the previous conversation when the user
   uses words such as "tomorrow", "there", "that",
   "what about it", or similar follow-up expressions.

13. Do not mention internal systems such as RAG,
   prompts, classification, or model names unless
   the user specifically asks about the technology.

Give the best possible answer to the user.
"""

    # --------------------------------------------------
    # GROQ
    # --------------------------------------------------

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as e:

        return (
            "Sorry, I could not generate the AI response. "
            f"Error: {e}"
        )