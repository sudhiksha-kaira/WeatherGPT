import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)


def classify_question(question):

    prompt = f"""
You are a question classification system for WeatherGPT.

Classify the user's question into exactly ONE of these categories:

1. CURRENT_WEATHER
   Questions about the weather right now.

2. FORECAST
   Questions about future weather, tomorrow, upcoming days,
   temperature prediction, rain prediction, etc.

3. WEATHER_ALERT
   Questions about dangerous weather conditions,
   warnings, storms, heavy rain, heatwaves, strong winds, etc.

4. CLIMATE_KNOWLEDGE
   General questions about climate, El Niño, La Niña,
   monsoon, climate change, drought, floods, etc.

5. WEATHER_SAFETY
   Questions asking what people should do during dangerous
   weather conditions.

6. GENERAL_WEATHER
   Other weather-related questions.

7. GENERAL
   Questions unrelated to weather or climate.

Examples:

"What is the temperature now?"
CURRENT_WEATHER

"Will it rain tomorrow?"
FORECAST

"Is there a storm warning?"
WEATHER_ALERT

"What is El Niño?"
CLIMATE_KNOWLEDGE

"What should I do during a thunderstorm?"
WEATHER_SAFETY

"How does humidity affect weather?"
GENERAL_WEATHER

"Who is the president of India?"
GENERAL

User question:
{question}

Return ONLY the category name.
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        category = response.choices[0].message.content.strip()

        valid_categories = [
            "CURRENT_WEATHER",
            "FORECAST",
            "WEATHER_ALERT",
            "CLIMATE_KNOWLEDGE",
            "WEATHER_SAFETY",
            "GENERAL_WEATHER",
            "GENERAL"
        ]

        if category in valid_categories:
            return category

        return "GENERAL_WEATHER"

    except Exception:
        return "GENERAL_WEATHER"