import sys
import os
import html

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp {
        background:
            radial-gradient(circle at 78% 13%, rgba(255,218,104,.34), transparent 13%),
            radial-gradient(circle at 18% 28%, rgba(73,169,255,.30), transparent 22%),
            linear-gradient(180deg, #62c9f5 0%, #2388ca 36%, #164d91 68%, #101c4a 100%);
        background-size: 130% 130%;
        animation: skyShift 18s ease-in-out infinite alternate;
        color: white;
        min-height: 100vh;
        overflow-x: hidden;
    }

    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        background:
            radial-gradient(circle at 50% 18%, rgba(255,255,255,.14), transparent 18%),
            linear-gradient(180deg, rgba(255,255,255,.05), rgba(2,16,48,.25));
        animation: skyGlow 8s ease-in-out infinite alternate;
    }

    @keyframes skyShift {
        0% { background-position: 0% 40%; }
        100% { background-position: 100% 60%; }
    }

    @keyframes skyGlow {
        0% { opacity: .65; }
        100% { opacity: 1; }
    }

    .weather-scene {
        position: fixed;
        inset: 0;
        overflow: hidden;
        pointer-events: none;
        z-index: 1;
    }

    .sun {
        position: absolute;
        width: 145px;
        height: 145px;
        top: 7%;
        right: 11%;
        border-radius: 50%;
        background: radial-gradient(circle, #fffbd6 0%, #ffe27a 28%, rgba(255,199,67,.42) 55%, transparent 72%);
        animation: sunMove 7s ease-in-out infinite, sunGlow 4s ease-in-out infinite;
    }

    @keyframes sunMove {
        0%,100% { transform: translateY(0) scale(1); }
        50% { transform: translateY(13px) scale(1.06); }
    }

    @keyframes sunGlow {
        0%,100% { filter: brightness(.9); }
        50% { filter: brightness(1.2); }
    }

    .cloud {
        position: absolute;
        width: 220px;
        height: 64px;
        border-radius: 70px;
        background: rgba(255,255,255,.30);
        filter: blur(1.5px);
        box-shadow:
            35px -20px 0 7px rgba(255,255,255,.27),
            90px -11px 0 12px rgba(255,255,255,.24),
            138px 2px 0 3px rgba(255,255,255,.20);
    }

    .cloud-one {
        top: 15%;
        left: -300px;
        animation: cloudOne 38s linear infinite;
    }

    .cloud-two {
        top: 30%;
        left: -350px;
        transform: scale(.68);
        opacity: .62;
        animation: cloudTwo 50s linear infinite;
        animation-delay: -19s;
    }

    .cloud-three {
        top: 8%;
        left: -330px;
        transform: scale(.48);
        opacity: .40;
        animation: cloudThree 58s linear infinite;
        animation-delay: -11s;
    }

    @keyframes cloudOne {
        from { left: -320px; }
        to { left: 110%; }
    }

    @keyframes cloudTwo {
        from { left: -380px; }
        to { left: 115%; }
    }

    @keyframes cloudThree {
        from { left: -350px; }
        to { left: 120%; }
    }

    .spark {
        position: absolute;
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: rgba(255,255,255,.85);
        box-shadow: 0 0 12px rgba(255,255,255,.75);
        animation: sparkle 3.5s ease-in-out infinite;
    }

    .sp1 { left: 11%; top: 18%; animation-delay: .2s; }
    .sp2 { left: 27%; top: 11%; animation-delay: 1.1s; }
    .sp3 { left: 48%; top: 24%; animation-delay: 2s; }
    .sp4 { left: 70%; top: 20%; animation-delay: .8s; }
    .sp5 { left: 84%; top: 34%; animation-delay: 1.7s; }

    @keyframes sparkle {
        0%,100% { opacity: .15; transform: scale(.65); }
        50% { opacity: .9; transform: scale(1.5); }
    }

    .particle {
        position: absolute;
        bottom: -20px;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: rgba(210,244,255,.42);
        animation: floatParticle 12s linear infinite;
    }

    .p1 { left: 8%; animation-delay: -2s; }
    .p2 { left: 23%; animation-delay: -7s; }
    .p3 { left: 41%; animation-delay: -4s; }
    .p4 { left: 59%; animation-delay: -9s; }
    .p5 { left: 76%; animation-delay: -1s; }
    .p6 { left: 91%; animation-delay: -6s; }

    @keyframes floatParticle {
        0% { transform: translateY(0) scale(.5); opacity: 0; }
        15% { opacity: .65; }
        80% { opacity: .25; }
        100% { transform: translateY(-105vh) scale(1.3); opacity: 0; }
    }

    .main .block-container {
        max-width: 1480px;
        padding: 20px 34px 60px;
        position: relative;
        z-index: 2;
    }

    header[data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"] { visibility: hidden; }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stToolbar"] {
        visibility: hidden;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stToolbar"] {
        visibility: hidden;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(5,17,46,.97), rgba(22,20,61,.96));
        border-right: 1px solid rgba(255,255,255,.13);
        backdrop-filter: blur(20px);
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 16px;
        margin: 8px 0 22px;
    }

    .brand-logo {
        font-size: 58px;
        filter: drop-shadow(0 8px 20px rgba(0,0,0,.28));
        animation: logoFloat 4s ease-in-out infinite;
    }

    @keyframes logoFloat {
        0%, 100% { transform: translateY(0) rotate(-2deg); }
        50% { transform: translateY(-7px) rotate(2deg); }
    }

    .brand-name {
        font-size: clamp(40px, 4.5vw, 64px);
        line-height: .95;
        font-weight: 900;
        letter-spacing: -3px;
        color: white;
        text-shadow: 0 8px 28px rgba(0,0,0,.25);
    }

    .brand-name span {
        color: #26d9ff;
    }

    .brand-subtitle {
        margin-top: 9px;
        font-size: 15px;
        color: rgba(255,255,255,.75);
    }

    .time-pill {
        display: inline-block;
        float: right;
        margin-top: -72px;
        margin-bottom: 25px;
        padding: 11px 17px;
        border-radius: 999px;
        background: rgba(8,25,62,.55);
        border: 1px solid rgba(255,255,255,.18);
        backdrop-filter: blur(15px);
        font-size: 12px;
    }

    .search-panel {
        clear: both;
        padding: 20px;
        border-radius: 26px;
        background: linear-gradient(135deg, rgba(8,30,70,.88), rgba(30,52,92,.84));
        border: 1px solid rgba(255,255,255,.28);
        box-shadow: 0 20px 55px rgba(0,0,0,.30);
        backdrop-filter: blur(22px);
        margin-bottom: 18px;
    }

    .search-label {
        font-size: 15px;
        font-weight: 800;
        color: rgba(255,255,255,.88);
        margin-bottom: 10px;
    }


    .ai-panel {
        padding: 17px 20px;
        border-radius: 18px;
        background: linear-gradient(135deg, rgba(5,27,68,.94), rgba(21,72,140,.92));
        border: 1px solid rgba(255,255,255,.28);
        color: #ffffff !important;
        box-shadow: 0 12px 30px rgba(0,0,0,.24);
        margin-bottom: 10px;
    }

    .voice-title {
        margin: 16px 0 8px;
        padding: 9px 13px;
        border-radius: 12px;
        display: inline-block;
        background: rgba(4,24,58,.82);
        border: 1px solid rgba(255,255,255,.24);
        color: #ffffff !important;
        font-size: 14px;
        font-weight: 850;
        box-shadow: 0 8px 20px rgba(0,0,0,.18);
    }

    [data-testid="stAudioInput"] {
        border-radius: 16px !important;
        border: 1px solid rgba(255,255,255,.35) !important;
        background: rgba(248,251,255,.98) !important;
        padding: 7px !important;
    }

    [data-testid="stAudioInput"] * {
        color: #17345d !important;
    }

    [data-testid="stPopover"] > button {
         width: 100% !important;
         min-height: 50px !important;
         border-radius: 15px !important;
         background: linear-gradient(135deg, #172554, #312e81) !important;
         color: #ffffff !important;
         border: 2px solid rgba(255,255,255,.70) !important;
         box-shadow: 0 10px 28px rgba(7,20,55,.42) !important;
         font-size: 15px !important;
         font-weight: 900 !important;
         opacity: 1 !important;
         text-shadow: 0 1px 2px rgba(0,0,0,.25) !important;
     }

    [data-testid="stPopover"] > button p,
    [data-testid="stPopover"] > button span,
    [data-testid="stPopover"] > button div {
        color: #ffffff !important;
        opacity: 1 !important;
    }

    [data-testid="stPopover"] > button:hover {
         background: linear-gradient(135deg, #1e3a8a, #4338ca) !important;
         transform: translateY(-1px);
         box-shadow: 0 13px 32px rgba(7,20,55,.50) !important;
     }

    .history-empty {
        padding: 16px;
        border-radius: 14px;
        background: #eef6ff;
        color: #17345d;
        text-align: center;
        font-weight: 700;
    }

    .popular {
        display: flex;
        gap: 8px;
        align-items: center;
        flex-wrap: wrap;
        margin-top: 12px;
        color: rgba(255,255,255,.72);
        font-size: 12px;
    }

    .pill {
        padding: 7px 12px;
        border-radius: 999px;
        background: rgba(255,255,255,.09);
        border: 1px solid rgba(255,255,255,.14);
        color: white;
    }

    .hero {
        padding: 25px 28px;
        min-height: 260px;
        border-radius: 28px;
        background:
            linear-gradient(135deg, rgba(19,102,204,.90), rgba(17,65,112,.88)),
            rgba(7,24,54,.90);
        border: 1px solid rgba(255,255,255,.32);
        box-shadow: 0 22px 60px rgba(0,0,0,.38);
        backdrop-filter: blur(22px);
        overflow: hidden;
        position: relative;
    }

    .hero::after {
        content: "✦";
        position: absolute;
        right: 7%;
        top: 9%;
        font-size: 105px;
        color: rgba(83,218,255,.20);
        animation: starPulse 4s ease-in-out infinite;
    }

    @keyframes starPulse {
        0%, 100% { transform: scale(.88) rotate(0deg); opacity: .35; }
        50% { transform: scale(1.08) rotate(18deg); opacity: .85; }
    }

    .place {
        font-size: 23px;
        font-weight: 850;
    }

    .muted {
        color: rgba(255,255,255,.66);
        font-size: 12px;
    }

    .weather-row {
        display: flex;
        align-items: center;
        gap: 20px;
        margin-top: 25px;
    }

    .big-icon {
        font-size: 82px;
        animation: weatherFloat 4s ease-in-out infinite;
        filter: drop-shadow(0 12px 22px rgba(0,0,0,.25));
    }

    @keyframes weatherFloat {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-9px); }
    }

    .big-temp {
        font-size: 82px;
        line-height: .9;
        font-weight: 900;
        letter-spacing: -5px;
    }

    .condition {
        font-size: 17px;
        font-weight: 750;
        margin-top: 8px;
    }

    .panel {
        padding: 19px;
        border-radius: 23px;
        background: linear-gradient(135deg, rgba(9,28,57,.88), rgba(32,48,70,.84));
        border: 1px solid rgba(255,255,255,.25);
        box-shadow: 0 17px 45px rgba(0,0,0,.32);
        backdrop-filter: blur(20px);
        margin-bottom: 17px;
    }

    .panel-title {
        font-size: 19px;
        font-weight: 850;
        color: white;
        margin-bottom: 13px;
    }

    .metric {
        text-align: center;
        min-height: 108px;
    }

    .metric-icon {
        font-size: 27px;
    }

    .metric-label {
        font-size: 11px;
        color: rgba(255,255,255,.58);
        margin-top: 5px;
    }

    .metric-value {
        font-size: 21px;
        font-weight: 900;
        margin-top: 3px;
    }

    .forecast-card {
        min-height: 155px;
        padding: 13px 8px;
        border-radius: 18px;
        text-align: center;
        background: linear-gradient(180deg, rgba(242,248,255,.96), rgba(216,232,250,.94));
        color: #10284f !important;
        border: 1px solid rgba(255,255,255,.90);
        box-shadow: 0 10px 28px rgba(0,0,0,.28);
        transition: transform .25s ease, box-shadow .25s ease;
    }

    .forecast-card:hover {
        transform: translateY(-5px);
    }

    .forecast-day {
        font-size: 12px;
        font-weight: 850;
        color: #10284f !important;
    }

    .forecast-icon {
        font-size: 36px;
        margin: 9px 0 4px;
    }

    .forecast-temp {
        font-size: 19px;
        font-weight: 900;
        color: #071e49 !important;
    }

    .forecast-desc {
        font-size: 10px;
        color: #28466f !important;
        opacity: 1;
        margin-top: 5px;
        font-weight: 650;
    }

    .alert-card {
        padding: 14px;
        border-radius: 17px;
        background: linear-gradient(135deg, rgba(255,70,98,.72), rgba(255,164,62,.32));
        border: 1px solid rgba(255,255,255,.20);
        margin-bottom: 9px;
    }

    .alert-title {
        font-weight: 850;
        font-size: 13px;
    }

    .alert-text {
        font-size: 11px;
        color: rgba(255,255,255,.82);
        margin-top: 4px;
    }

    .ai-panel {
        padding: 19px;
        border-radius: 23px;
        background: linear-gradient(135deg, rgba(12,48,104,.90), rgba(58,31,112,.88));
        border: 1px solid rgba(255,255,255,.24);
        box-shadow: 0 18px 50px rgba(0,0,0,.32);
        backdrop-filter: blur(20px);
    }

    .chat-user {
        margin: 9px 0 7px auto;
        max-width: 88%;
        padding: 12px 15px;
        border-radius: 18px 18px 4px 18px;
        background: linear-gradient(135deg, #168cff, #6555ee);
    }

    .chat-ai {
        margin: 7px auto 10px 0;
        max-width: 92%;
        padding: 12px 15px;
        border-radius: 18px 18px 18px 4px;
        background: rgba(255,255,255,.08);
        border: 1px solid rgba(255,255,255,.14);
    }

    .chat-label {
        font-size: 10px;
        font-weight: 800;
        opacity: .62;
        margin-bottom: 4px;
    }

    [data-testid="stTextInput"] input {
        background: rgba(255,255,255,.97) !important;
        color: #18325e !important;
        border-radius: 17px !important;
        border: 2px solid rgba(112,185,255,.42) !important;
        min-height: 48px;
    }

    [data-testid="stTextInput"] label {
        display: none;
    }

    div.stButton > button {
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,.18);
        background: linear-gradient(135deg, #168cff, #5a4de8);
        color: white;
        font-weight: 800;
        min-height: 44px;
        box-shadow: 0 8px 25px rgba(20,103,230,.24);
        transition: transform .2s ease, box-shadow .2s ease;
    }

    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 30px rgba(54,120,255,.35);
        color: white;
    }

    .footer {
        text-align: center;
        padding: 28px;
        color: rgba(255,255,255,.50);
        font-size: 11px;
    }
    header[data-testid="stHeader"] { background:transparent; }
    [data-testid="stToolbar"] { visibility:hidden; }

    [data-testid="stSidebar"] {
        background:linear-gradient(180deg,rgba(7,25,72,.97),rgba(31,39,91,.93));
        border-right:1px solid rgba(255,255,255,.15);
        backdrop-filter:blur(20px);
    }

    [data-testid="stSidebar"] * { color:white !important; }

    .brand {
        display:flex;
        align-items:center;
        gap:16px;
        margin:8px 0 22px;
    }

    .brand-logo {
        font-size:58px;
        filter:drop-shadow(0 8px 18px rgba(0,0,0,.25));
    }

    .brand-name {
        font-size:clamp(40px,4.5vw,64px);
        line-height:.95;
        font-weight:900;
        letter-spacing:-3px;
        color:white;
        text-shadow:0 7px 28px rgba(0,0,0,.25);
    }

    .brand-name span { color:#20d9ff; }

    .brand-subtitle {
        margin-top:9px;
        font-size:16px;
        color:rgba(255,255,255,.82);
    }

    .time-pill {
        display:inline-block;
        float:right;
        margin-top:-72px;
        margin-bottom:25px;
        padding:11px 17px;
        border-radius:999px;
        background:rgba(7,28,71,.48);
        border:1px solid rgba(255,255,255,.24);
        backdrop-filter:blur(14px);
        font-size:12px;
    }

    .search-panel {
        clear:both;
        padding:17px 20px 15px;
        border-radius:28px;
        background:rgba(255,255,255,.17);
        border:1px solid rgba(255,255,255,.30);
        box-shadow:0 20px 60px rgba(0,0,0,.18);
        backdrop-filter:blur(20px);
    }

    .search-label {
        font-size:15px;
        font-weight:800;
        color:rgba(255,255,255,.88);
        margin-bottom:10px;
    }

    .popular {
        display:flex;
        gap:8px;
        align-items:center;
        flex-wrap:wrap;
        margin-top:11px;
        color:rgba(255,255,255,.75);
        font-size:12px;
    }

    .pill {
        padding:6px 12px;
        border-radius:999px;
        background:rgba(255,255,255,.17);
        border:1px solid rgba(255,255,255,.23);
        color:white;
    }

    .hero {
        padding:25px 28px;
        min-height:260px;
        border-radius:28px;
        background:linear-gradient(135deg,rgba(20,105,210,.78),rgba(36,174,230,.30));
        border:1px solid rgba(255,255,255,.28);
        box-shadow:0 22px 60px rgba(0,0,0,.23);
        backdrop-filter:blur(18px);
        overflow:hidden;
        position:relative;
    }

    .hero::after {
        content:"☁️";
        position:absolute;
        right:5%;
        top:8%;
        font-size:100px;
        opacity:.12;
        animation:cloudFloat 6s ease-in-out infinite;
    }

    @keyframes cloudFloat {
        0%,100% { transform:translate(0,0); }
        50% { transform:translate(-20px,10px); }
    }

    .place {
        font-size:23px;
        font-weight:850;
    }

    .muted {
        color:rgba(255,255,255,.68);
        font-size:12px;
    }

    .weather-row {
        display:flex;
        align-items:center;
        gap:20px;
        margin-top:25px;
    }

    .big-icon {
        font-size:82px;
        animation:float 4s ease-in-out infinite;
    }

    @keyframes float {
        0%,100% { transform:translateY(0); }
        50% { transform:translateY(-9px); }
    }

    .big-temp {
        font-size:82px;
        line-height:.9;
        font-weight:900;
        letter-spacing:-5px;
    }

    .condition {
        font-size:17px;
        font-weight:750;
        margin-top:8px;
    }

    .panel {
        padding:19px;
        border-radius:24px;
        background:rgba(255,255,255,.14);
        border:1px solid rgba(255,255,255,.23);
        box-shadow:0 17px 45px rgba(0,0,0,.17);
        backdrop-filter:blur(17px);
        margin-bottom:17px;
    }

    .panel-title {
        font-size:19px;
        font-weight:850;
        color:white;
        margin-bottom:13px;
    }

    .metric {
        text-align:center;
        min-height:108px;
    }

    .metric-icon { font-size:27px; }
    .metric-label { font-size:11px;color:rgba(255,255,255,.60);margin-top:5px; }
    .metric-value { font-size:21px;font-weight:900;margin-top:3px; }

    .forecast-card {
        min-height:155px;
        padding:13px 8px;
        border-radius:18px;
        text-align:center;
        background:rgba(226,242,255,.72);
        color:#122d59;
        border:1px solid rgba(255,255,255,.70);
        box-shadow:0 8px 22px rgba(0,0,0,.10);
    }

    .forecast-day { font-size:12px;font-weight:850; }
    .forecast-icon { font-size:36px;margin:9px 0 4px; }
    .forecast-temp { font-size:19px;font-weight:900; }
    .forecast-desc { font-size:10px;opacity:.70;margin-top:5px; }

    .alert-card {
        padding:14px;
        border-radius:17px;
        background:linear-gradient(135deg,rgba(255,74,99,.72),rgba(255,165,66,.36));
        border:1px solid rgba(255,255,255,.23);
        margin-bottom:9px;
    }

    .alert-title { font-weight:850;font-size:13px; }
    .alert-text { font-size:11px;color:rgba(255,255,255,.82);margin-top:4px; }

    .ai-panel {
        padding:19px;
        border-radius:24px;
        background:linear-gradient(135deg,rgba(15,71,157,.66),rgba(81,37,153,.48));
        border:1px solid rgba(255,255,255,.24);
        box-shadow:0 18px 50px rgba(0,0,0,.20);
        backdrop-filter:blur(18px);
    }

    .chat-user {
        margin:9px 0 7px auto;
        max-width:88%;
        padding:12px 15px;
        border-radius:18px 18px 4px 18px;
        background:linear-gradient(135deg,#258cff,#5d57ff);
    }

    .chat-ai {
        margin:7px auto 10px 0;
        max-width:92%;
        padding:12px 15px;
        border-radius:18px 18px 18px 4px;
        background:rgba(255,255,255,.13);
        border:1px solid rgba(255,255,255,.20);
    }

    .chat-label {
        font-size:10px;
        font-weight:800;
        opacity:.65;
        margin-bottom:4px;
    }

    [data-testid="stTextInput"] input {
        background:rgba(255,255,255,.96) !important;
        color:#18325e !important;
        border-radius:17px !important;
        border:2px solid rgba(255,255,255,.70) !important;
        min-height:48px;
    }

    [data-testid="stTextInput"] label { display:none; }

    div.stButton > button {
        border-radius:15px;
        border:1px solid rgba(255,255,255,.22);
        background:linear-gradient(135deg,#168cff,#3457e8);
        color:white;
        font-weight:800;
        min-height:44px;
        box-shadow:0 8px 25px rgba(20,103,230,.25);
    }

    div.stButton > button:hover {
        transform:translateY(-2px);
        background:linear-gradient(135deg,#2ca4ff,#6259ff);
        color:white;
    }

    .footer {
        text-align:center;
        padding:28px;
        color:rgba(255,255,255,.55);
        font-size:11px;
    }
    header[data-testid="stHeader"] { background:transparent; }
    .weather-title { font-size:clamp(42px,5vw,68px); font-weight:800; letter-spacing:-2px; color:white; text-shadow:0 5px 22px rgba(0,0,0,.28); }
    .weather-subtitle { font-size:17px; color:rgba(255,255,255,.84); margin-bottom:25px; }
    .brand-card { padding:20px 24px; border-radius:28px; background:linear-gradient(135deg,rgba(255,255,255,.25),rgba(255,255,255,.08)); border:1px solid rgba(255,255,255,.30); box-shadow:0 18px 55px rgba(0,0,0,.20); backdrop-filter:blur(18px); }
    .section-title { font-size:27px; font-weight:800; color:white; margin-top:25px; margin-bottom:14px; text-shadow:0 3px 14px rgba(0,0,0,.20); }
    .weather-card { padding:20px; border-radius:22px; background:rgba(255,255,255,.15); border:1px solid rgba(255,255,255,.23); text-align:center; min-height:130px; box-shadow:0 12px 35px rgba(0,0,0,.14); backdrop-filter:blur(14px); }
    .weather-card-title { font-size:13px; color:rgba(255,255,255,.68); margin-bottom:8px; }
    .weather-card-value { font-size:27px; font-weight:800; color:white; }
    .forecast-card { padding:18px 14px; border-radius:20px; background:rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.22); margin-bottom:10px; box-shadow:0 10px 30px rgba(0,0,0,.12); backdrop-filter:blur(14px); }
    .alert-card { padding:17px 20px; border-radius:20px; margin-bottom:12px; background:linear-gradient(135deg,rgba(255,91,91,.25),rgba(255,177,79,.10)); border:1px solid rgba(255,175,110,.32); backdrop-filter:blur(14px); }
    .ai-card { padding:20px; border-radius:22px; background:rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.22); margin-top:10px; box-shadow:0 12px 35px rgba(0,0,0,.14); backdrop-filter:blur(14px); color:white; }
    .hero-weather { padding:28px; border-radius:30px; background:linear-gradient(135deg,rgba(255,255,255,.28),rgba(255,255,255,.09)); border:1px solid rgba(255,255,255,.32); box-shadow:0 20px 60px rgba(0,0,0,.22); backdrop-filter:blur(18px); }
    .hero-temp { font-size:clamp(64px,7vw,100px); line-height:.95; font-weight:800; letter-spacing:-4px; color:white; text-shadow:0 8px 30px rgba(0,0,0,.22); }
    .hero-location { font-size:28px; font-weight:800; color:white; }
    .hero-condition { font-size:19px; font-weight:600; color:rgba(255,255,255,.92); margin-top:8px; }
    .hero-muted { color:rgba(255,255,255,.68); }
    .chat-user { padding:14px 18px; margin:10px 0 8px auto; max-width:82%; border-radius:20px 20px 5px 20px; background:rgba(42,145,255,.72); color:white; }
    .chat-ai { padding:15px 18px; margin:8px auto 12px 0; max-width:88%; border-radius:20px 20px 20px 5px; background:rgba(255,255,255,.15); border:1px solid rgba(255,255,255,.20); color:white; }
    .chat-label { font-size:11px; font-weight:700; opacity:.72; margin-bottom:5px; }
    div.stButton > button { border-radius:14px; border:1px solid rgba(255,255,255,.25); background:linear-gradient(135deg,#1488ff,#075bd4); color:white; font-weight:700; box-shadow:0 8px 24px rgba(0,95,220,.30); }
    div.stButton > button:hover { background:linear-gradient(135deg,#2b9aff,#0a68e5); color:white; }
    [data-testid="stTextInput"] input { background:rgba(255,255,255,.94)!important; color:#10243d!important; border-radius:15px!important; border:1px solid rgba(255,255,255,.8)!important; }
    [data-testid="stTextInput"] label, [data-testid="stRadio"] label { color:rgba(255,255,255,.90)!important; }
    [data-testid="stRadio"] div[role="radiogroup"] { gap:10px; }
    [data-testid="stRadio"] div[role="radiogroup"] label { background:rgba(255,255,255,.13); padding:8px 14px; border-radius:14px; border:1px solid rgba(255,255,255,.18); }
    [data-testid="stAlert"] { border-radius:16px; backdrop-filter:blur(10px); }
    .footer { text-align:center; color:rgba(255,255,255,.55); padding:35px 0 10px; font-size:12px; }
    
    .section-heading {
        font-size: 21px;
        font-weight: 900;
        color: #ffffff;
        margin: 20px 0 12px;
        text-shadow: 0 3px 12px rgba(0,0,0,.28);
    }

    .hero {
        padding: 24px 26px !important;
        border-radius: 24px !important;
        background: #f8fbff !important;
        border: 2px solid rgba(255,255,255,.95) !important;
        box-shadow: 0 14px 35px rgba(0,0,0,.25) !important;
        color: #10284f !important;
    }

    .hero .place {
        color: #0b2c5c !important;
        font-size: 20px !important;
        font-weight: 900 !important;
    }

    .hero .muted {
        color: #526b88 !important;
        font-weight: 650 !important;
    }

    .hero .big-temp {
        color: #071e49 !important;
        text-shadow: none !important;
    }

    .hero .condition {
        color: #173e70 !important;
        font-weight: 850 !important;
    }

    .metric.panel {
        background: #f8fbff !important;
        border: 2px solid rgba(255,255,255,.95) !important;
        box-shadow: 0 12px 28px rgba(0,0,0,.22) !important;
        color: #10284f !important;
    }

    .metric-label {
        color: #55708f !important;
        font-size: 12px !important;
        font-weight: 750 !important;
    }

    .metric-value {
        color: #071e49 !important;
        font-size: 23px !important;
    }

    .forecast-card {
        min-height: 185px !important;
        padding: 17px 10px !important;
        border-radius: 20px !important;
        background: #f8fbff !important;
        color: #10284f !important;
        border: 2px solid rgba(255,255,255,.98) !important;
        box-shadow: 0 14px 30px rgba(0,0,0,.24) !important;
    }

    .forecast-day {
        color: #173e70 !important;
        font-size: 12px !important;
        font-weight: 900 !important;
        line-height: 1.3 !important;
    }

    .forecast-temp {
        color: #071e49 !important;
        font-size: 24px !important;
        font-weight: 950 !important;
        margin-top: 4px !important;
    }

    .forecast-desc {
        color: #315477 !important;
        opacity: 1 !important;
        font-size: 11px !important;
        font-weight: 750 !important;
        line-height: 1.35 !important;
    }

    .forecast-desc:last-child {
        display: inline-block;
        margin-top: 9px !important;
        padding: 5px 8px;
        border-radius: 999px;
        background: #e5f1ff;
        color: #1262b3 !important;
    }

    .alert-card {
        padding: 17px 18px !important;
        border-radius: 18px !important;
        background: #fff7f3 !important;
        border: 2px solid #ffb18f !important;
        box-shadow: 0 10px 24px rgba(0,0,0,.18) !important;
    }

    .alert-title {
        color: #9f2f16 !important;
        font-size: 14px !important;
        font-weight: 950 !important;
    }

    .alert-text {
        color: #55352d !important;
        font-size: 12px !important;
        line-height: 1.5 !important;
        font-weight: 650 !important;
    }

    .search-panel {
        background: rgba(7,30,73,.78) !important;
        border: 1px solid rgba(255,255,255,.28) !important;
        box-shadow: 0 15px 35px rgba(0,0,0,.22) !important;
    }

    .popular, .pill { display: none !important; }

    .hero { margin-bottom: 34px !important; }
    .metric.panel { margin-top: 0 !important; min-height: 125px !important; }
    .section-heading { margin-top: 30px !important; margin-bottom: 18px !important; }
    .forecast-card { margin-bottom: 8px !important; }
    .alerts-panel {
        margin-top: 34px !important;
        padding: 22px !important;
        border-radius: 22px !important;
        background: rgba(7,30,73,.90) !important;
        border: 2px solid rgba(255,205,160,.55) !important;
        box-shadow: 0 16px 38px rgba(0,0,0,.28) !important;
    }
    .alerts-heading {
        color: #ffffff !important;
        font-size: 22px !important;
        font-weight: 950 !important;
        margin-bottom: 16px !important;
    }
    .alerts-empty {
        padding: 15px 18px !important;
        border-radius: 14px !important;
        background: rgba(48,185,115,.18) !important;
        border: 1px solid rgba(117,255,177,.38) !important;
        color: #eafff1 !important;
        font-weight: 750 !important;
    }
    .history-popover {
        margin-top: 14px !important;
    }
    @media (max-width: 900px) {
        .forecast-card { min-height: 165px !important; }
        .forecast-temp { font-size: 20px !important; }
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



st.markdown(
    """
    <div class="nature-animation">
        <div class="sun-glow"></div>
        <div class="moving-cloud cloud-a"></div>
        <div class="moving-cloud cloud-b"></div>
        <div class="moving-cloud cloud-c"></div>
        <div class="leaf l1"></div>
        <div class="leaf l2"></div>
        <div class="leaf l3"></div>
        <div class="leaf l4"></div>
        <div class="leaf l5"></div>
        <div class="rain-drop r1"></div>
        <div class="rain-drop r2"></div>
        <div class="rain-drop r3"></div>
        <div class="rain-drop r4"></div>
        <div class="rain-drop r5"></div>
        <div class="rain-drop r6"></div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="weather-scene">
        <div class="sun"></div>
        <div class="cloud cloud-one"></div>
        <div class="cloud cloud-two"></div>
        <div class="cloud cloud-three"></div>
        <div class="spark sp1"></div>
        <div class="spark sp2"></div>
        <div class="spark sp3"></div>
        <div class="spark sp4"></div>
        <div class="spark sp5"></div>
        <div class="particle p1"></div>
        <div class="particle p2"></div>
        <div class="particle p3"></div>
        <div class="particle p4"></div>
        <div class="particle p5"></div>
        <div class="particle p6"></div>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown(
    """
    <div style="text-align:center;padding:12px 0 22px;">
        <div style="font-size:52px;">🌦️</div>
        <div style="font-size:23px;font-weight:900;">WeatherGPT</div>
        <div style="font-size:10px;opacity:.60;margin-top:5px;">GLOBAL WEATHER INTELLIGENCE</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.radio(
    "Navigation",
    ["🏠 Home", "📅 Forecast", "🚨 Weather Alerts", "🤖 AI Assistant", "🌍 Climate Info"],
    label_visibility="collapsed"
)

st.sidebar.markdown(
    """
    <div style="margin-top:25px;padding:14px;border-radius:17px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.12);">
        <div style="font-size:11px;opacity:.58;">POWERED BY</div>
        <div style="font-size:13px;font-weight:800;margin-top:4px;">WeatherGPT AI</div>
        <div style="font-size:10px;opacity:.55;margin-top:4px;">Weather • Forecast • Alerts • Climate</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="brand">
        <div class="brand-logo">🌦️</div>
        <div>
            <div class="brand-name">Weather<span>GPT</span></div>
            <div class="brand-subtitle">Conversational AI for Weather Forecasting, Alerts, and Climate Information.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

from datetime import datetime
now = datetime.now().strftime("%a, %d %b %Y  |  %I:%M %p")
st.markdown(f'<div class="time-pill">📅 {now} &nbsp; | &nbsp; 🌐 Global</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="search-panel"><div class="search-label">🔎 Search any city, village, town, or place worldwide</div>',
    unsafe_allow_html=True
)

location_mode = st.radio(
    "Location method",
    ["✏️ Search Location", "📍 Use My Location"],
    horizontal=True,
    label_visibility="collapsed"
)

if location_mode == "✏️ Search Location":
    search_col, button_col = st.columns([6, 1.35])

    with search_col:
        location = st.text_input(
            "Global search",
            placeholder="Search any city, village, town, or place worldwide...",
            label_visibility="collapsed"
        )

    with button_col:
        search_weather = st.button("🌦️ Get Weather", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    state = ""
    country = ""

    if search_weather:
        if not location:
            st.warning("Please enter a location.")
        else:
            with st.spinner("🌍 Finding location and live weather..."):
                weather, error = get_weather(location, state, country)

            if weather:
                st.session_state.weather = weather
                st.session_state.error = None
                forecast, forecast_error = get_forecast(weather["latitude"], weather["longitude"])
                st.session_state.forecast = forecast or []
                st.session_state.alerts = generate_weather_alerts(forecast) if forecast else []
                if forecast_error:
                    st.warning(f"Forecast warning: {forecast_error}")
            else:
                st.session_state.weather = None
                st.session_state.forecast = None
                st.session_state.alerts = []
                st.session_state.error = error

else:
    st.markdown(
        '<div class="panel"><div class="panel-title">📍 Current Location</div>'
        '<div style="font-size:12px;color:rgba(255,255,255,.65);">Allow browser location access to get live weather for your current position.</div></div>',
        unsafe_allow_html=True
    )

    current_location = streamlit_geolocation()

    if current_location and current_location.get("latitude") is not None and current_location.get("longitude") is not None:
        latitude = float(current_location["latitude"])
        longitude = float(current_location["longitude"])

        if st.button("🌦️ Get Weather Here"):
            with st.spinner("📍 Getting live weather..."):
                weather, error = get_weather_by_coordinates(latitude, longitude)

            if weather:
                st.session_state.weather = weather
                st.session_state.error = None
                forecast, forecast_error = get_forecast(latitude, longitude)
                st.session_state.forecast = forecast or []
                st.session_state.alerts = generate_weather_alerts(forecast) if forecast else []
                if forecast_error:
                    st.warning(f"Forecast warning: {forecast_error}")
            else:
                st.session_state.weather = None
                st.session_state.forecast = None
                st.session_state.alerts = []
                st.session_state.error = error
    else:
        st.info("📍 Allow browser location access to use your current location.")

if st.session_state.weather:
    weather = st.session_state.weather
    forecast = st.session_state.forecast or []
    alerts = st.session_state.alerts

    location_text = ", ".join(
        part for part in [weather.get("city",""), weather.get("state",""), weather.get("country","")]
        if part
    )

    icon = get_weather_icon(weather["condition"])

    st.markdown('<div class="section-heading">🌤️ Current Weather Details</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="hero">
            <div class="place">📍 {html.escape(location_text)}</div>
            <div class="muted">Live weather information</div>
            <div class="weather-row">
                <div class="big-icon">{icon}</div>
                <div>
                    <div class="big-temp">{weather["temperature"]:.0f}°C</div>
                    <div class="condition">{html.escape(weather["condition"].title())}</div>
                    <div class="muted">Feels like {weather["feels_like"]:.0f}°C</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    metric_data = [
        ("💧", "Humidity", f'{weather["humidity"]}%'),
        ("💨", "Wind Speed", f'{weather["wind_speed"]} m/s'),
        ("📊", "Pressure", f'{weather["pressure"]} hPa'),
        ("🌡️", "Feels Like", f'{weather["feels_like"]:.1f}°C')
    ]

    metric_cols = st.columns(4)
    for col, (mi, label, value) in zip(metric_cols, metric_data):
        with col:
            st.markdown(
                f'<div class="panel metric">'
                f'<div class="metric-icon">{mi}</div>'
                f'<div class="metric-label">{label}</div>'
                f'<div class="metric-value">{value}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown('<div class="section-heading">📅 5-Day Forecast</div>', unsafe_allow_html=True)

    forecast_items = forecast[:5]

    if forecast_items:
        cols = st.columns(len(forecast_items))
        for i, item in enumerate(forecast_items):
            with cols[i]:
                st.markdown(
                    f"""
                    <div class="forecast-card">
                        <div class="forecast-day">{datetime.fromisoformat(str(item["datetime"])).strftime("%a, %d %b • %I:%M %p") if "T" in str(item["datetime"]) else str(item["datetime"])}</div>
                        <div class="forecast-icon">{get_weather_icon(item["condition"])}</div>
                        <div class="forecast-temp">{item["temperature"]:.0f}°C</div>
                        <div class="forecast-desc">{html.escape(item["condition"].title())}</div>
                        <div class="forecast-desc">🌧️ {item["rain_probability"]*100:.0f}% rain</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    st.markdown('<div class="panel-title" style="margin-top:34px;">📈 Forecast Trends</div>', unsafe_allow_html=True)
    if forecast_items:
        st.line_chart({
            "Temperature (°C)": [x["temperature"] for x in forecast_items],
            "Rain Probability (%)": [x["rain_probability"] * 100 for x in forecast_items]
        })

    st.markdown(
        '<div class="alerts-panel"><div class="alerts-heading">🚨 Weather Alerts</div>',
        unsafe_allow_html=True
    )
    if alerts:
        for alert in alerts[:6]:
            st.markdown(
                f'<div class="alert-card"><div class="alert-title">{html.escape(alert["type"])}</div>'
                f'<div class="alert-text">{html.escape(alert["message"])}</div></div>',
                unsafe_allow_html=True
            )
    else:
        st.markdown('<div class="alerts-empty">✅ No significant weather alerts detected.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel-title" style="margin-top:25px;">🤖 Ask WeatherGPT</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="ai-panel"><div style="font-size:13px;color:rgba(255,255,255,.70);">'
        'Ask about weather, forecasts, climate, rainfall, or weather safety.</div></div>',
        unsafe_allow_html=True
    )

    question = st.text_input(
        "AI question",
        placeholder="Ask anything about this weather...",
        label_visibility="collapsed"
    )

    st.markdown('<div class="voice-title">🎙️ Voice Question</div>', unsafe_allow_html=True)

    audio_input = st.audio_input(
        "Voice question",
        label_visibility="collapsed"
    )

    if audio_input:
        with st.spinner("🎙️ Understanding your voice..."):
            voice_text, voice_error = transcribe_audio(audio_input)

        if voice_error:
            st.error(f"Voice recognition error: {voice_error}")
        elif voice_text:
            question = voice_text
            st.info(f"🎙️ You said: {voice_text}")

    if st.button("✨ Ask WeatherGPT", use_container_width=True) and question:
        with st.spinner("🤖 WeatherGPT is thinking..."):
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

        st.session_state.conversation_history.append({"role":"user","content":question})
        st.session_state.conversation_history.append({"role":"assistant","content":answer})

        st.markdown(
            f'<div class="chat-user"><div class="chat-label">YOU</div>{html.escape(question)}</div>'
            f'<div class="chat-ai"><div class="chat-label">🤖 WEATHERGPT · {detected_language}</div>'
            f'{html.escape(answer).replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True
        )

        try:
            tts = gTTS(text=answer, lang=detected_language_code, slow=False)
            audio_file = "weather_response.mp3"
            tts.save(audio_file)
            st.audio(audio_file, format="audio/mp3")
        except Exception:
            pass

    with st.popover("🕘 History", use_container_width=True):
        if st.session_state.conversation_history:
            st.markdown("### 🕘 Conversation History")
            for message in st.session_state.conversation_history:
                if message["role"] == "user":
                    st.markdown(
                        f'<div class="chat-user"><div class="chat-label">YOU</div>{html.escape(message["content"])}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div class="chat-ai"><div class="chat-label">🤖 WEATHERGPT</div>{html.escape(message["content"]).replace(chr(10), "<br>")}</div>',
                        unsafe_allow_html=True
                    )
            if st.button("🗑️ Clear Conversation", use_container_width=True):
                st.session_state.conversation_history = []
                st.rerun()
        else:
            st.markdown(
                '<div class="history-empty">🕘 No conversation history yet.</div>',
                unsafe_allow_html=True
            )

    st.markdown('<div class="footer">🌦️ WeatherGPT · Global Weather Intelligence · Powered by AI</div>', unsafe_allow_html=True)


elif st.session_state.error:

    st.error(
        f"❌ Weather API error: "
        f"{st.session_state.error}"
    )