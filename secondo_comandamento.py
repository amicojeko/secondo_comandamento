import tkinter as tk
import threading
import queue
import json
import os
import time

from vosk import Model, KaldiRecognizer
import pyaudio

# --- Definizione delle liste e mappatura emoji ---
animals = ["gatto", "cane", "coniglio", "cavallo"]
colors  = ["rosso", "verde", "blu", "giallo"]
fruits  = ["mela", "banana", "arancia", "fragola"]

categories = {
    "animali": animals,
    "colori": colors,
    "frutta": fruits
}

emoji_map = {
    "animali": "🐶",
    "colori": "🌈",
    "frutta": "🍌"
}

# --- Contatori globali ---
counters = {"animali": 0, "colori": 0, "frutta": 0}

# Coda per comunicare eventi dal thread del riconoscimento vocale alla GUI
event_queue = queue.Queue()

# --- Impostazione del modello Vosk ---
MODEL_PATH = "../vosk/vosk-model-it-0.22"  # Assicurati che questo sia il path corretto
if not os.path.exists(MODEL_PATH):
    print(f"Modello non trovato in {MODEL_PATH}")
    exit(1)

model = Model(MODEL_PATH)
all_keywords = animals + colors + fruits
grammar = json.dumps(all_keywords)
recognizer = KaldiRecognizer(model, 16000, grammar)

# --- Inizializzazione di PyAudio ---
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                input=True, frames_per_buffer=4096)
stream.start_stream()

# Variabili per tracciare i conteggi parziali per utterance
partial_counts = {"animali": 0, "colori": 0, "frutta": 0}
event_triggered = {"animali": False, "colori": False, "frutta": False}

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
                local_counts = {"animali": 0, "colori": 0, "frutta": 0}
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
                partial_counts = {"animali": 0, "colori": 0, "frutta": 0}
                event_triggered = {"animali": False, "colori": False, "frutta": False}
        else:
            # Elaborazione dei risultati parziali per aggiornamenti in tempo reale
            partial_result = json.loads(recognizer.PartialResult())
            partial_text = partial_result.get("partial", "").strip().lower()
            local_counts = {"animali": 0, "colori": 0, "frutta": 0}
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

# Creazione delle label per ciascuna categoria, posizionate verticalmente al centro
label_animals = tk.Label(root, text=f"{emoji_map['animali']}: 0", font=("Helvetica", 100), fg="white", bg="black")
label_colors  = tk.Label(root, text=f"{emoji_map['colori']}: 0", font=("Helvetica", 100), fg="white", bg="black")
label_fruits  = tk.Label(root, text=f"{emoji_map['frutta']}: 0", font=("Helvetica", 100), fg="white", bg="black")

label_animals.pack(expand=True)
label_colors.pack(expand=True)
label_fruits.pack(expand=True)

flash_in_progress = False

# Funzione per far lampeggiare lo schermo di rosso 3 volte
def flash_screen(times=3, delay=200):
    global flash_in_progress
    if flash_in_progress:
        return
    flash_in_progress = True
    original_bg = root["bg"]
    def flash(count):
        if count > 0:
            root.configure(bg="red")
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
                if cat == "animali":
                    label_animals.config(text=f"{emoji_map['animali']}: {counters[cat]}")
                elif cat == "colori":
                    label_colors.config(text=f"{emoji_map['colori']}: {counters[cat]}")
                elif cat == "frutta":
                    label_fruits.config(text=f"{emoji_map['frutta']}: {counters[cat]}")
            elif event[0] == "trigger":
                flash_screen()
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
