import streamlit as st
import subprocess
import os
import uuid
import re
import requests

# Page Setup
st.set_page_config(page_title="SnapClip HD", page_icon="✂️", layout="centered")

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def clean_time(t_str):
    t_str = re.sub(r'\s+', '', str(t_str)).strip()
    parts = t_str.split(':')
    parts = [p.zfill(2) for p in parts]
    if len(parts) == 1:
        return f"00:00:{parts[0]}"
    elif len(parts) == 2:
        return f"00:{parts[0]}:{parts[1]}"
    elif len(parts) == 3:
        return f"{parts[0]}:{parts[1]}:{parts[2]}"
    return "00:00:00"

def clean_url(url):
    return url.split('?si=')[0].split('&')[0].strip()

def get_cobalt_stream(video_url):
    """Cobalt API کے ذریعے ویڈیو اسٹریم کا لنک حاصل کرنا"""
    instances = [
        "https://api.cobalt.tools/api/json",
        "https://cobalt.qtf.tw/api/json",
        "https://co.wuk.sh/api/json"
    ]
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": video_url,
        "videoQuality": "720"
    }
    
    for instance in instances:
        try:
            resp = requests.post(instance, json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "url" in data:
                    return data["url"]
                elif data.get("status") == "redirect":
                    return data["url"]
        except Exception:
            continue
            
    return None

st.title("✂️ SnapClip HD")
st.caption("یوٹیوب کی کسی بھی ویڈیو کا مخصوص حصہ کٹ کریں اور ڈاؤن لوڈ کریں!")

# Input fields
video_url_input = st.text_input("YouTube Video Link", placeholder="https://www.youtube.com/watch?v=...")

col1, col2 = st.columns(2)
with col1:
    start_time = st.text_input("Start Time (HH:MM:SS)", value="00:00:05")
with col2:
    end_time = st.text_input("End Time (HH:MM:SS)", value="00:00:15")

if st.button("🎬 Cut & Download Clip", type="primary", use_container_width=True):
    if not video_url_input:
        st.warning("براہ کرم پہلے ویڈیو کا لنک درج کریں!")
    else:
        with st.spinner("Cobalt API کے ذریعے ویڈیو اسٹریم حاصل کی جا رہی ہے..."):
            url = clean_url(video_url_input)
            start_t = clean_time(start_time)
            end_t = clean_time(end_time)
            
            # 1. API سے لنک لیں
            stream_url = get_cobalt_stream(url)
            
            if not stream_url:
                st.error("ویڈیو اسٹریم حاصل نہیں ہو سکی! لنک دوبارہ چیک کریں یا دوسری ویڈیو ٹرائی کریں۔")
            else:
                unique_id = uuid.uuid4().hex[:8]
                output_filename = f"clip_{unique_id}.mp4"
                output_path = os.path.join(DOWNLOAD_FOLDER, output_filename)
                
                # 2. FFmpeg کے ذریعے کلپ کاٹیں
                cmd = [
                    "ffmpeg",
                    "-ss", start_t,
                    "-to", end_t,
                    "-i", stream_url,
                    "-c", "copy",
                    "-y",
                    output_path
                ]
                
                try:
                    subprocess.run(cmd, capture_output=True, text=True, check=True)
                    
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        st.success("ویڈیو کامیابی سے کٹ ہو گئی ہے! 🎉")
                        st.video(output_path)
                        
                        with open(output_path, "rb") as file:
                            st.download_button(
                                label="⬇️ Download MP4",
                                data=file,
                                file_name=output_filename,
                                mime="video/mp4",
                                use_container_width=True
                            )
                    else:
                        st.error("فائل بنانے میں ناکامی ہوئی۔")
                except subprocess.CalledProcessError as e:
                    st.error(f"FFmpeg پروسیسنگ میں مسئلہ: {e.stderr if e.stderr else str(e)}")
                except Exception as e:
                    st.error(f"خرابی: {str(e)}")
                    
