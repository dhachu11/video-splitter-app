import streamlit as st
import os
import subprocess
import whisper
import zipfile

# ===== PAGE CONFIG =====
st.set_page_config(page_title="AI Video Splitter", page_icon="🎬", layout="centered")

# ===== CUSTOM CSS =====
st.markdown("""
<style>
body {
    background-color: #0f172a;
}
.main {
    background-color: #0f172a;
}
h1 {
    text-align: center;
    color: #ffffff;
}
.stButton>button {
    background-color: #6366f1;
    color: white;
    border-radius: 10px;
    height: 3em;
    width: 100%;
    font-size: 16px;
}
.stSelectbox label, .stFileUploader label {
    color: #e5e7eb;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ===== TITLE =====
st.title("🎬 AI Video Splitter")
st.caption("Split videos + generate captions automatically")

st.divider()

# ===== UPLOAD =====
uploaded_file = st.file_uploader("📤 Upload your video", type=["mp4", "mov", "avi"])

# ===== SETTINGS =====
interval = st.selectbox("⏱ Select clip duration", [15, 30, 45, 60])

# ===== PROCESS =====
if uploaded_file is not None:
    with open("input.mp4", "wb") as f:
        f.write(uploaded_file.read())

    st.success("✅ Video uploaded successfully")

    if st.button("🚀 Start Processing"):

        output_folder = "clips"

        # Clear old clips (important)
        if os.path.exists(output_folder):
            for file in os.listdir(output_folder):
                os.remove(os.path.join(output_folder, file))
        else:
            os.makedirs(output_folder)

        # ===== GET VIDEO DURATION =====
        def get_duration(video):
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries",
                 "format=duration", "-of",
                 "default=noprint_wrappers=1:nokey=1", video],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            return float(result.stdout)

        duration = get_duration("input.mp4")
        st.info(f"🎬 Total Duration: {duration:.2f} sec")

        # ===== LOAD AI MODEL =====
        with st.spinner("🤖 Loading AI model..."):
            model = whisper.load_model("tiny")  # use "base" if powerful PC

        start = 0
        clip_num = 1

        progress = st.progress(0)
        status = st.empty()

        # ===== PROCESS VIDEO =====
        while start < duration:
            output_clip = f"{output_folder}/clip_{clip_num}.mp4"

            status.write(f"✂️ Processing clip {clip_num}...")

            subprocess.run([
                "ffmpeg",
                "-i", "input.mp4",
                "-ss", str(start),
                "-t", str(interval),
                "-c", "copy",
                output_clip
            ])

            # Generate captions
            result = model.transcribe(output_clip)

            with open(f"{output_folder}/clip_{clip_num}.txt", "w", encoding="utf-8") as f:
                f.write(result["text"])

            start += interval
            clip_num += 1

            progress.progress(min(start/duration, 1.0))

        # ===== DONE =====
        st.success("🎉 Done! All clips created successfully")
        st.balloons()

        # ===== CREATE ZIP =====
        zip_path = "clips.zip"

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in os.listdir(output_folder):
                zipf.write(os.path.join(output_folder, file))

        # ===== DOWNLOAD BUTTON =====
        with open(zip_path, "rb") as f:
            st.download_button(
                label="📥 Download All Clips",
                data=f,
                file_name="clips.zip",
                mime="application/zip"
            )
