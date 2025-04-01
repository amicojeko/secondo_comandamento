import json
from vosk import Model, KaldiRecognizer
import pyaudio
import os

# --- Definizione delle liste di parole ---
animals = ["gatto", "cane", "coniglio", "cavallo"]
colors  = ["rosso", "verde", "blu", "giallo"]
fruits  = ["mela", "banana", "arancia", "fragola"]

# --- Contatori globali ---
counters = {"animali": 0, "colori": 0, "frutta": 0}

# Per gestire la conta parziale nell'utterance corrente
partial_counts = {"animali": 0, "colori": 0, "frutta": 0}
# Per triggerare l'evento solo una volta per categoria per utterance
event_triggered = {"animali": False, "colori": False, "frutta": False}

def event_trigger(category, word):
    # Evento fittizio: in futuro qui andrai a inviare il comando all'ESP
    print(f"Evento triggered per {category.upper()} con parola: '{word}'")

def print_counters():
    print(f"Contatori -> Animali: {counters['animali']} | Colori: {counters['colori']} | Frutta: {counters['frutta']}")

# --- Impostazione del modello ---
MODEL_PATH = "../vosk/vosk-model-it-0.22"  # Assicurati che questo sia il path corretto
if not os.path.exists(MODEL_PATH):
    print(f"Modello non trovato in {MODEL_PATH}")
    exit(1)

model = Model(MODEL_PATH)

# Crea la grammar limitata alle parole di interesse
all_keywords = animals + colors + fruits
grammar = json.dumps(all_keywords)
recognizer = KaldiRecognizer(model, 16000, grammar)

# --- Configurazione del microfono con PyAudio ---
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                input=True, frames_per_buffer=4096)
stream.start_stream()

print("In ascolto... parla ora (CTRL+C per uscire)")

try:
    while True:
        data = stream.read(4096, exception_on_overflow=False)
        # Se viene segnalato il termine dell'utterance
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            final_text = result.get("text", "").strip().lower()
            if final_text:
                # Conta le occorrenze per categoria nell'utterance finale
                local_counts = {"animali": 0, "colori": 0, "frutta": 0}
                for word in final_text.split():
                    if word in animals:
                        local_counts["animali"] += 1
                    elif word in colors:
                        local_counts["colori"] += 1
                    elif word in fruits:
                        local_counts["frutta"] += 1
                # Per ogni categoria, calcola il delta rispetto alla conta parziale già registrata
                for cat in counters:
                    delta = local_counts[cat] - partial_counts[cat]
                    if delta > 0:
                        counters[cat] += delta
                        # Triggera l'evento solo se non ancora fatto per questa categoria nell'utterance
                        if not event_triggered[cat] and local_counts[cat] > 0:
                            # Usa la prima parola riconosciuta di quella categoria per il trigger
                            for word in final_text.split():
                                if (cat == "animali" and word in animals) or \
                                   (cat == "colori" and word in colors) or \
                                   (cat == "frutta" and word in fruits):
                                    event_trigger(cat, word)
                                    break
                            event_triggered[cat] = True
                print_counters()
            # Reset per la nuova utterance
            partial_counts = {"animali": 0, "colori": 0, "frutta": 0}
            event_triggered = {"animali": False, "colori": False, "frutta": False}
        else:
            # Risultato parziale per aggiornamenti in tempo reale
            partial_result = json.loads(recognizer.PartialResult())
            partial_text = partial_result.get("partial", "").strip().lower()
            local_counts = {"animali": 0, "colori": 0, "frutta": 0}
            for word in partial_text.split():
                if word in animals:
                    local_counts["animali"] += 1
                elif word in colors:
                    local_counts["colori"] += 1
                elif word in fruits:
                    local_counts["frutta"] += 1
            # Aggiorna i counter globali con la differenza rispetto all'ultima conta parziale
            for cat in counters:
                delta = local_counts[cat] - partial_counts[cat]
                if delta > 0:
                    counters[cat] += delta
                    if not event_triggered[cat] and local_counts[cat] > 0:
                        # Triggera l'evento una volta per categoria
                        for word in partial_text.split():
                            if (cat == "animali" and word in animals) or \
                               (cat == "colori" and word in colors) or \
                               (cat == "frutta" and word in fruits):
                                event_trigger(cat, word)
                                break
                        event_triggered[cat] = True
            # Aggiorna la conta parziale corrente
            partial_counts = local_counts.copy()
            print_counters()

except KeyboardInterrupt:
    print("\nChiusura in corso...")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
