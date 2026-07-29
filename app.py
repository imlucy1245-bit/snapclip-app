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

def normalize_youtube_url(url):
    """ہر قسم کے یوٹیوب لنک (youtu.be یا youtube.com) کو سٹینڈرڈ لنک میں بدلنا"""
    url = url.strip()
    # If it's a short link (youtu.be)
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0].split("&")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    # If it's a regular link with parameters
    elif "watch?v=" in url:
        video_id = url.split("watch?v=")[1].split("&")[0].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

def get_cobalt_stream(video_url):
    """Cobalt API کے مختلف سرورز سے سٹریمنگ لنک حاصل کرنا"""
    instances = [
        "https://api.cobalt.tools",
        "https://cobalt.qtf.tw",
        "https://co.wuk.sh",
        "https://api.wuk.sh"
    ]
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    payload = {
        "url": video_url,
        "videoQuality": "720",
        "youtubeVideoCodec": "h264"
    }
    
    for instance in instances:
        try:
            resp = requests.post(f"{instance}/api/json", json=payload, headers=headers, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                if "url" in data:
                    return data["url"]
                elif data.get("status") == "redirect":
                    return data["url"]
                elif data.get("status") == "tunnel":
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
        with st.spinner("ویڈیو لنک پروسیس ہو رہا ہے..."):
            clean_url = normalize_youtube_url(video_url_input)
            start_t = clean_time(start_time)
            end_t = clean_time(end_time)
            
            # 1. API سے سٹریمنگ لنک حاصل کریں
            stream_url = get_cobalt_stream(clean_url)
            
            if not stream_url:
                st.error("ویڈیو اسٹریم حاصل نہیں ہو سکی! ویڈیو لنک کو ایک بار براؤزر سے کاپی کر کے دوبارہ کوشش کریں۔")
            else:
                unique_id = uuid.uuid4().hex[:8]
                output_filename = f"clip_{unique_id}.mp4"
                output_path = os.path.join(DOWNLOAD_FOLDER, output_filename)
                
                # 2. FFmpeg سے ویڈیو کلپ کٹ کریں
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
                    
