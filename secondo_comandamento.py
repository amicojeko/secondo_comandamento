import tkinter as tk
import threading
import queue
import json
import os
import time
import yaml

from vosk import Model, KaldiRecognizer
import pyaudio

# --- Caricamento della configurazione da YAML ---
def load_config(config_file="config.yaml"):
    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Errore nel caricamento della configurazione: {e}")
        exit(1)

# Carica la configurazione
config = load_config()

# Inizializza categorie, parole ed emoji dalla configurazione
categories = {}
emoji_map = {}
color_map = {}
all_keywords = []

# Processa la configurazione
for category, cat_config in config.items():
    words = cat_config.get('words', [])
    categories[category] = words
    emoji_map[category] = cat_config.get('emoji', '')
    color_map[category] = cat_config.get('color', 'red')
    all_keywords.extend(words)

# --- Contatori globali ---
counters = {cat: 0 for cat in categories.keys()}

# Coda per comunicare eventi dal thread del riconoscimento vocale alla GUI
event_queue = queue.Queue()

# --- Impostazione del modello Vosk ---
MODEL_PATH = "../vosk/vosk-model-it-0.22"  # Assicurati che questo sia il path corretto
if not os.path.exists(MODEL_PATH):
    print(f"Modello non trovato in {MODEL_PATH}")
    exit(1)

model = Model(MODEL_PATH)
grammar = json.dumps(all_keywords)
recognizer = KaldiRecognizer(model, 16000, grammar)

# --- Inizializzazione di PyAudio ---
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                input=True, frames_per_buffer=4096)
stream.start_stream()

# Variabili per tracciare i conteggi parziali per utterance
partial_counts = {cat: 0 for cat in categories.keys()}
event_triggered = {cat: False for cat in categories.keys()}

# Funzione del thread di speech recognition
def speech_recognition_loop():
    global partial_counts, event_triggered
    while True:
        data = stream.read(4096, exception_on_overflow=False)
        # Se il recognizer considera l'utterance "finale"
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            final_text = result.get("text", "").strip().lower()
            if final_text:
                local_counts = {cat: 0 for cat in categories.keys()}
                words = final_text.split()
                for word in words:
                    for cat, word_list in categories.items():
                        if word in word_list:
                            local_counts[cat] += 1
                # Per ogni categoria, calcola il delta rispetto ai conteggi parziali
                for cat in counters.keys():
                    delta = local_counts[cat] - partial_counts[cat]
                    if delta > 0:
                        event_queue.put(("update", cat, delta))
                        # Triggera l'evento solo una volta per categoria per utterance
                        if not event_triggered[cat] and local_counts[cat] > 0:
                            event_queue.put(("trigger", cat, words[0]))
                            event_triggered[cat] = True
                # Reset per la prossima utterance
                partial_counts = {cat: 0 for cat in categories.keys()}
                event_triggered = {cat: False for cat in categories.keys()}
        else:
            # Elaborazione dei risultati parziali per aggiornamenti in tempo reale
            partial_result = json.loads(recognizer.PartialResult())
            partial_text = partial_result.get("partial", "").strip().lower()
            local_counts = {cat: 0 for cat in categories.keys()}
            words = partial_text.split()
            for word in words:
                for cat, word_list in categories.items():
                    if word in word_list:
                        local_counts[cat] += 1
            for cat in counters.keys():
                delta = local_counts[cat] - partial_counts[cat]
                if delta > 0:
                    event_queue.put(("update", cat, delta))
                    if not event_triggered[cat] and local_counts[cat] > 0:
                        event_queue.put(("trigger", cat, words[0]))
                        event_triggered[cat] = True
            partial_counts = local_counts.copy()
        time.sleep(0.01)

# --- Interfaccia Grafica con Tkinter ---
root = tk.Tk()
root.configure(bg="black")
root.attributes("-fullscreen", True)

# Funzione per chiudere l'app
def quit_app(event=None):
    root.destroy()
root.bind("<Command-q>", quit_app)
root.bind("<Alt-F4>", quit_app)

# Creazione dinamica delle label per ciascuna categoria
label_map = {}
for category in categories.keys():
    label_map[category] = tk.Label(
        root,
        text=f"{emoji_map[category]}: 0",
        font=("Helvetica", 100),
        fg="white",
        bg="black"
    )
    label_map[category].pack(expand=True)

flash_in_progress = False

# Funzione per far lampeggiare lo schermo con colore specifico della categoria
def flash_screen(category=None, times=3, delay=200):
    global flash_in_progress
    if flash_in_progress:
        return
    flash_in_progress = True
    original_bg = root["bg"]
    # Usa il colore specifico della categoria se fornito, altrimenti usa rosso
    flash_color = color_map.get(category, "red") if category else "red"

    def flash(count):
        if count > 0:
            root.configure(bg=flash_color)
            root.after(delay, lambda: restore(count))
        else:
            root.configure(bg=original_bg)
            global flash_in_progress
            flash_in_progress = False

    def restore(count):
        root.configure(bg=original_bg)
        root.after(delay, lambda: flash(count - 1))

    flash(times)

# Funzione per elaborare gli eventi dalla coda e aggiornare l'interfaccia
def process_queue():
    try:
        while True:
            event = event_queue.get_nowait()
            if event[0] == "update":
                cat = event[1]
                delta = event[2]
                counters[cat] += delta
                label_map[cat].config(text=f"{emoji_map[cat]}: {counters[cat]}")
            elif event[0] == "trigger":
                cat = event[1]
                flash_screen(category=cat)
            event_queue.task_done()
    except queue.Empty:
        pass
    root.after(50, process_queue)

# Avvio del thread per il riconoscimento vocale
threading.Thread(target=speech_recognition_loop, daemon=True).start()

# Avvio della funzione di polling della coda
root.after(50, process_queue)

root.mainloop()

# Pulizia finale all'uscita
stream.stop_stream()
stream.close()
p.terminate()
