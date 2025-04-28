import streamlit as st
import subprocess
import os
import uuid
import tempfile
import soundfile as sf
import numpy as np
import pyaudio
import wave
from datetime import datetime

# Set page title
st.title("TalkSHOW Video Generator")

# Initialize session state
if 'audio_path' not in st.session_state:
    st.session_state.audio_path = None

tab1, tab2 = st.tabs(["Upload Audio", "Record Audio"])

with tab1:
    audio_file = st.file_uploader("Upload an audio file (.wav)", type=["wav"])
    
    if audio_file is not None:
        os.makedirs("demo_audio", exist_ok=True)
        unique_filename = f"{audio_file.name}"
        audio_path = os.path.join("./demo_audio", unique_filename)

        with open(audio_path, "wb") as f:
            f.write(audio_file.getbuffer())

        st.audio(audio_file)
        st.success(f"Audio file saved as {unique_filename}")

        st.session_state.audio_path = audio_path

with tab2:
    st.write("Record your audio:")
    
    def record_audio():
        chunk = 1024
        format = pyaudio.paInt16
        channels = 1
        rate = 16000
        record_seconds = 5
        output_filename = "output.wav"

        # Ensure the demo_audio folder exists
        os.makedirs("./demo_audio", exist_ok=True)
        
        # Save the file inside the demo_audio folder (no double "demo_audio")
        output_path = os.path.join("./demo_audio", output_filename)

        p = pyaudio.PyAudio()
        stream = p.open(format=format, channels=channels,
                        rate=rate, input=True,
                        frames_per_buffer=chunk)

        st.write("Recording...")
        frames = []

        for i in range(0, int(rate / chunk * record_seconds)):
            data = stream.read(chunk)
            frames.append(data)

        st.write("Recording finished")

        stream.stop_stream()
        stream.close()
        p.terminate()

        # Save the recording to the demo_audio folder
        wf = wave.open(output_path, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(format))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))
        wf.close()

        return output_path

    if st.button("Record Audio"):
        recorded_filename = record_audio()
        recorded_path = os.path.join(recorded_filename)
        st.success(f"Recording saved as {recorded_filename}")
        st.session_state.audio_path = recorded_path   # <-- Save it globally

# Common controls section
st.sidebar.header("Generation Settings")
demo_type = st.sidebar.selectbox("Select demo type", ["Whole Body", "Only Face", "Diversity (Multiple Samples)"])
speaker_id = st.sidebar.number_input("Speaker ID", min_value=0, step=1, value=0)


# Button to trigger generation
if st.button("Generate Video"):
    if st.session_state.audio_path is None:
        st.warning("Please upload or record a .wav file.")
    else:
        audio_path = st.session_state.audio_path  # ✅ Use the saved audio path

        if demo_type == "Whole Body":
            cmd = f"python scripts/demo.py --config_file ./config/LS3DCG.json --infer --audio_file {audio_path} --body_model_name s2g_LS3DCG --body_model_path experiments/2022-10-19-smplx_S2G-LS3DCG/ckpt-99.pth --id 0"
            base_name = os.path.splitext(os.path.basename(audio_path))[0]
            video_dir = os.path.join("visualise", "video", "LS3DCG", f"{base_name}.wav")
            video_path = os.path.join(video_dir, f"{base_name}.mp4")
        elif demo_type == "Only Face":
            cmd = f"python scripts/demo.py --config_file ./config/body_pixel.json --infer --audio_file {audio_path} --id 0 --only_face"
            base_name = os.path.splitext(os.path.basename(audio_path))[0]
            video_dir = os.path.join("visualise", "video", "body-pixel2", f"{base_name}.wav")
            video_path = os.path.join(video_dir, f"{base_name}.mp4")
        elif demo_type == "Diversity (Multiple Samples)":
            cmd = f"python scripts/demo.py --config_file ./config/body_pixel.json --infer --audio_file {audio_path} --id 0 --num_sample 12"
            base_name = os.path.splitext(os.path.basename(audio_path))[0]
            video_dir = os.path.join("visualise", "video", "body-pixel2", f"{base_name}.wav")
            video_path = os.path.join(video_dir, f"{base_name}.mp4")

        print(audio_path)

        st.info("Running the generation script...")
        log_placeholder = st.empty()
        log_text = ""

        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        for line in iter(process.stdout.readline, ''):
            log_text += line
            log_placeholder.text(log_text)

        process.stdout.close()
        process.wait()

        print(video_path)

        if os.path.exists(video_path):
            st.success("Video generated successfully!")
            st.video(video_path)
        else:
            st.error("Video not found. Please check the logs for errors.")
