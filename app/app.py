import sys
import os
import re
import streamlit as st

PROJETO_RAIZ = r"D:\Python\youtube_transcriber"
sys.path.append(PROJETO_RAIZ)

from youtube_whisper_pipeline import baixar_audio, transcrever_audio, resumir_texto

st.set_page_config(page_title="YouTube Whisper App", page_icon="🎧", layout="centered")

st.title("YouTube Whisper App")
st.markdown("Extraia **áudio**, gere **transcrições** e **resumos automáticos** de vídeos do YouTube.")

url = st.text_input("Cole aqui a URL do vídeo do YouTube:")

if st.button("Iniciar processo"):
    if not url:
        st.warning("Por favor, insira uma URL válida.")
    else:
        with st.spinner("Baixando áudio..."):
            audio_path = baixar_audio(url)
        st.success("Áudio baixado!")

        with st.spinner("Transcrevendo áudio... (pode levar alguns minutos)"):
            transcricao, _ = transcrever_audio(audio_path)
        st.success("Transcrição concluída!")

        st.subheader("Transcrição")
        st.text_area("Texto completo:", transcricao, height=200)

        with st.spinner("Gerando resumo..."):
            resumo = resumir_texto(transcricao)
        st.success("Resumo gerado!")

        st.subheader("Resumo")
        st.write(resumo)

        # --- Criando botões de download ---
        st.download_button(
            label="Baixar Transcrição",
            data=transcricao,
            file_name="transcricao.txt",
            mime="text/plain"
        )

        st.download_button(
            label="Baixar Resumo",
            data=resumo,
            file_name="resumo.txt",
            mime="text/plain"
        )

        # --- Insights automáticos ---
        st.subheader("Insights automáticos:")

        def gerar_insights(texto):
            frases = re.split(r'(?<=[.!?]) +', texto)
            insights = []

            for frase in frases:
                frase_lower = frase.lower()
                if "importante" in frase_lower or "principal" in frase_lower:
                    insights.append("🔹 " + frase.strip())
                elif "problema" in frase_lower or "desafio" in frase_lower:
                    insights.append("⚠️ " + frase.strip())
                elif "resultado" in frase_lower or "melhoria" in frase_lower:
                    insights.append("✅ " + frase.strip())

            if not insights:
                insights.append("Nenhum insight específico encontrado automaticamente.")
            return insights

        insights = gerar_insights(resumo)
        for i in insights:
            st.write(i)

        # --- Salvar resultados localmente ---
        os.makedirs("resultados", exist_ok=True)
        with open("resultados/transcricao.txt", "w", encoding="utf-8") as f:
            f.write(transcricao)
        with open("resultados/resumo.txt", "w", encoding="utf-8") as f:
            f.write(resumo)

        st.success("Processo finalizado com sucesso!")

        from datetime import datetime

        # --- Log automático ---
        with open("resultados/log_execucoes.txt", "a", encoding="utf-8") as log:
            log.write(f"{datetime.now()} - Vídeo: {url}\n")


        