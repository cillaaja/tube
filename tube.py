import sys
import subprocess
import threading
import os
import streamlit.components.v1 as components

# Pastikan streamlit terinstall
try:
    import streamlit as st
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
    import streamlit as st


# -------------------------------------------------
# 🎥 Jalankan FFmpeg langsung dari Google Drive URL
# -------------------------------------------------
def run_ffmpeg(drive_url, stream_key, is_shorts, log_callback):
    output_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"

    # Ambil file ID dari link Google Drive
    if "id=" in drive_url:
        file_id = drive_url.split("id=")[-1]
    elif "file/d/" in drive_url:
        file_id = drive_url.split("file/d/")[1].split("/")[0]
    else:
        log_callback("❌ URL Google Drive tidak valid.")
        return

    # Buat direct link download
    direct_url = f"https://drive.google.com/uc?id={file_id}&export=download"

    # Gunakan FFmpeg langsung dari URL tanpa download file
    scale_filter = "-vf scale=720:1280" if is_shorts else "-vf scale='min(1920,iw)':min(1080,ih)'"
    cmd = [
        "ffmpeg", "-re", "-i", direct_url,
        "-t", "3600",  # Maksimum 1 jam
        "-c:v", "libx264", "-preset", "veryfast",
        "-b:v", "6500k", "-maxrate", "6500k", "-bufsize", "13000k",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-g", "60", "-keyint_min", "60",
        "-f", "flv"
    ]
    cmd += scale_filter.split()
    cmd.append(output_url)

    log_callback(f"▶️ Menjalankan FFmpeg: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            log_callback(line.strip())
        process.wait()
    except Exception as e:
        log_callback(f"❌ Error: {e}")
    finally:
        log_callback("✅ Streaming selesai atau dihentikan.")


# -------------------------------------------------
# 🌐 Aplikasi Streamlit
# -------------------------------------------------
def main():
    st.set_page_config(page_title="YouTube Live 1080p", page_icon="🎥", layout="wide")

    st.title("🎬 Streaming Youtube")

    # Iklan opsional
    show_ads = st.checkbox("Tampilkan Iklan", value=True)
    if show_ads:
        st.subheader("Iklan Sponsor")
        components.html(
            """
            <div style="background:#f0f2f6;padding:20px;border-radius:10px;text-align:center">
                <script type='text/javascript' 
                        src='//pl26562103.profitableratecpm.com/28/f9/95/28f9954a1d5bbf4924abe123c76a68d2.js'>
                </script>
                <p style="color:#888">Iklan akan muncul di sini</p>
            </div>
            """,
            height=300
        )

    # Input link Google Drive
    st.subheader("🎞️ Masukkan Link Google Drive Video (publik)")
    drive_url = st.text_input(
        "🔗 Link Google Drive (contoh: https://drive.google.com/file/d/FILE_ID/view?usp=sharing)",
        placeholder="https://drive.google.com/file/d/...",
    )

    stream_key = st.text_input("🔑 YouTube Stream Key", type="password")
    is_shorts = st.checkbox("Mode Shorts (720x1280)", value=False)

    log_placeholder = st.empty()
    logs = []

    def log_callback(msg):
        logs.append(msg)
        log_placeholder.text("\n".join(logs[-25:]))

    if 'ffmpeg_thread' not in st.session_state:
        st.session_state['ffmpeg_thread'] = None

    if st.button("🚀 Jalankan Streaming"):
        if not drive_url or not stream_key:
            st.error("❗ Masukkan link Google Drive dan Stream Key!")
        else:
            st.session_state['ffmpeg_thread'] = threading.Thread(
                target=run_ffmpeg,
                args=(drive_url, stream_key, is_shorts, log_callback),
                daemon=True
            )
            st.session_state['ffmpeg_thread'].start()
            st.success("✅ Streaming dimulai! Tunggu hingga koneksi tersambung ke YouTube...")

    if st.button("🛑 Stop Streaming"):
        os.system("pkill ffmpeg")
        st.warning("⚠️ Streaming dihentikan!")

    log_placeholder.text("\n".join(logs[-25:]))


if __name__ == "__main__":
    main()
