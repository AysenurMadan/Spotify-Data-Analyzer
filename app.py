import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import plotly.express as px

# 1. Sayfa Ayarları
st.set_page_config(page_title="Spotify Data Pro", layout="wide")

# Tasarım - Koyu Tema ve Spotify Yeşili
st.markdown("""
    <style>
    .main { background-color: #121212; color: #1DB954; }
    .stMetric { border: 2px solid #1DB954; border-radius: 15px; padding: 10px; background-color: #1e1e1e; }
    </style>
    """, unsafe_allow_html=True)

# Yardımcı Fonksiyon: dk:sn formatı
def format_duration(ms):
    total_seconds = int(ms / 1000)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"

# API Bilgileri
CLIENT_ID = '74daab88fce5488e869356c452ce4d2c'
CLIENT_SECRET = 'd04912a15359488d876132fe420057e9'
REDIRECT_URI = 'http://127.0.0.1:8501'

# Yetki Kapsamı
scope = "user-top-read user-library-read"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=scope
))

st.title("🚀 Spotify Müzik Veri Analizörü")

with st.sidebar:
    st.image("https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_RGB_Green.png", width=150)
    st.info("Bu proje, kütüphanenizi zaman ve süre metrikleriyle analiz eder.")
    data_source = st.radio("Veri Kaynağı Seçin:", ["En Çok Dinlenenler", "Kütüphanemdeki Şarkılar"])
    st.write("---")
    st.caption("Geliştirici: AYŞENUR MADAN")

if st.button('Analizi Başlat'):
    with st.spinner('Verileriniz işleniyor...'):
        try:
            if data_source == "En Çok Dinlenenler":
                results = sp.current_user_top_tracks(limit=50, time_range='long_term')
                tracks = results['items']
            else:
                results = sp.current_user_saved_tracks(limit=50)
                tracks = [item['track'] for item in results['items']]

            if tracks:
                data = []
                for track in tracks:
                    # Albüm yılı bilgisi (Her zaman erişilebilirdir, 403 vermez)
                    release_date = track.get('album', {}).get('release_date', '2000')
                    year = int(release_date[:4])
                    decade = f"{(year // 10) * 10}s" # Örn: 2014 -> 2010s

                    data.append({
                        "Şarkı": track.get('name', 'Bilinmiyor'),
                        "Sanatçı": track.get('artists', [{}])[0].get('name', 'Bilinmiyor'),
                        "Süre_MS": track.get('duration_ms', 0),
                        "Süre (dk:sn)": format_duration(track.get('duration_ms', 0)),
                        "Yıl": year,
                        "On Yıl": decade,
                        "Albüm": track.get('album', {}).get('name', 'Bilinmiyor')
                    })

                df = pd.DataFrame(data)

                # --- Metrikler ---
                m1, m2, m3 = st.columns(3)
                m1.metric("Toplam Şarkı", len(df))
                m2.metric("En Eski Şarkı Yılı", df['Yıl'].min())
                m3.metric("Favori Dönem", df['On Yıl'].mode()[0])

                st.divider()

                # --- Grafikler ---
                g1, g2 = st.columns(2)

                with g1:
                    st.subheader("⏱️ En Favori 15 Şarkının Süre Dağılımı")
                    top_15 = df.head(15).copy()
                    top_15['Saniye'] = top_15['Süre_MS'] / 1000
                    fig_dur = px.bar(top_15, x='Saniye', y='Şarkı', orientation='h', 
                                     color='Saniye', color_continuous_scale='Greens',
                                     text='Süre (dk:sn)')
                    fig_dur.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_dur, use_container_width=True)

                with g2:
                    st.subheader("📅 Zaman Yolculuğu: Yıllara Göre Dağılım")
                    decade_df = df['On Yıl'].value_counts().reset_index()
                    decade_df.columns = ['On Yıl', 'Adet']
                    fig_pie = px.pie(decade_df, values='Adet', names='On Yıl', hole=0.4,
                                     color_discrete_sequence=px.colors.sequential.Greens_r)
                    st.plotly_chart(fig_pie, use_container_width=True)

                st.subheader("📜 Veri Seti Detayları")
                st.dataframe(df[["Şarkı", "Sanatçı", "Süre (dk:sn)", "Yıl", "Albüm"]], use_container_width=True)
                st.success("Analiz başarıyla tamamlandı!")

            else:
                st.error("Veri bulunamadı.")
        except Exception as e:
            st.error(f"Sistemsel bir hata oluştu: {e}")