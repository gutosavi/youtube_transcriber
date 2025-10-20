import os
import re
import whisper
import yt_dlp
from nltk.tokenize import sent_tokenize
from transformers import pipeline
from datetime import datetime
from langdetect import detect
from deep_translator import GoogleTranslator
import nltk

nltk.download("punkt_tab")
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

# Log automático
def registrar_log(mensagem):
    os.makedirs("resultados", exist_ok=True)
    with open("resultados/log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {mensagem}\n")

FFMPEG_PATH = r"D:\Python\ffmpeg\bin"
DOWNLOADS_DIR = r"D:\Python\youtube_transcriber\notebooks\downloads"

def normalizar_nome(nome):
    nome = nome.lower()
    nome = re.sub(r'[^a-z0-9]+', '_', nome)
    nome = nome.strip('_')
    return f"_{nome}"

# Download de áudio:
def baixar_audio(url):
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    registrar_log(f"Iniciando download do vídeo: {url}")

    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        titulo = info.get("title", "audio_youtube")

    nome_limpo = normalizar_nome(titulo)
    caminho_mp3 = os.path.join(DOWNLOADS_DIR, f"{nome_limpo}.mp3")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOADS_DIR, f"{nome_limpo}.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "ffmpeg_location": FFMPEG_PATH,
        "quiet": False
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    registrar_log(f"Áudio salvo em: {caminho_mp3}")
    print(f"Áudio salvo em: {caminho_mp3}")
    return caminho_mp3

# Transcrição:
def transcrever_audio(caminho_audio, modelo="base"):
    registrar_log(f"Iniciando transcrição do áudio: {caminho_audio}")
    print("Transcrevendo áudio com Whisper...")
    model = whisper.load_model(modelo)
    resultado = model.transcribe(caminho_audio)
    texto = resultado["text"]

    caminho_txt = caminho_audio.replace(".mp3", ".txt")
    with open(caminho_txt, "w", encoding="utf-8") as f:
        f.write(texto)

    registrar_log(f"Transcrição salva em: {caminho_txt}")
    return texto, caminho_txt

def limpar_ingles_estranho(texto):
    padroes = [
        r"\bthat\b", r"\bof\b", r"\bby\b", r"\band\b",
        r"\bthe\b", r"\ba\b", r"\ban\b", r"\bfor\b",
        r"\bas\b", r"\bwith\b", r"\bto\b", r"\bon\b"
    ]
    texto = re.sub("|".join(padroes), "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def traduzir_para_portugues_se_necessario(texto):
    try:
        idioma = detect(texto)
        if idioma != "pt":
            print(f"Texto detectado em {idioma}. Traduzindo para português...")
            registrar_log(f"Traduzindo texto de {idioma} para português")
            texto_traduzido = GoogleTranslator(source='auto', target='pt').translate(texto)
        else:
            print("Texto já está em português, sem tradução necessária.")
    except Exception as e:
        print(f"Erro ao detectar idioma: {e}")
        registrar_log(f"Erro na detecção de idioma: {e}")
    return texto

# Resumo:
def resumir_texto(texto, modelo="facebook/bart-large-cnn"):
    registrar_log(f"Iniciando resumo com modelo {modelo}")
    summarizer = pipeline("summarization", model=modelo)

    frases = sent_tokenize(texto)
    blocos = []
    bloco_atual = ""

    for frase in frases:
        if len(bloco_atual) + len(frase) < 1500:
            bloco_atual += " " + frase
        else:
            blocos.append(bloco_atual)
            bloco_atual = frase
    blocos.append(bloco_atual)

    resumos = []
    for i, bloco in enumerate(blocos):
        resumo = summarizer(bloco, max_length=150, min_length=50, do_sample=False)
        resumos.append(resumo[0]["summary_text"])
    
    registrar_log("Resumo final gerado com sucesso")
    return " ".join(resumos)

# Execução do pipeline:
if __name__ == "__main__":
    url = input("Cole o link do YouTube: ")

    audio_path = baixar_audio(url)
    texto_transcrito, caminho_txt = transcrever_audio(audio_path)

    texto_limpo = limpar_ingles_estranho(texto_transcrito)
    texto_final = traduzir_para_portugues_se_necessario(texto_limpo)

    resumo = resumir_texto(texto_final)

    caminho_resumo = caminho_txt.replace(".txt", "_resumo.txt")
    with open(caminho_resumo, "w", encoding="utf-8") as f:
        f.write(resumo)

    print(f"\nResumo salvo em: {caminho_resumo}")
    registrar_log(f"Resumo salvo em: {caminho_resumo}")
