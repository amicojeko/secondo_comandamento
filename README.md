# 🎤 Riconoscimento Vocale Reattivo con Python, Vosk e Tkinter

Questo progetto è una demo interattiva per riconoscimento vocale **in tempo reale**, basato su:

- **Python 3.12.4** installato in modo isolato e sicuro con `pyenv`
- **Vosk** per il riconoscimento vocale offline e in italiano
- **Tkinter** per un'interfaccia grafica fullscreen che mostra contatori ed effetti visivi
- Eventuali trigger futuri verso **ESP/Arduino** via Wi-Fi

L'app mostra tre grandi emoji al centro dello schermo e aggiorna contatori ogni volta che rileva parole specifiche (frutti, animali o colori). Quando viene riconosciuta una parola nuova, lo schermo lampeggia di rosso per 3 volte. È pensata per essere utilizzata in ambienti interattivi o progetti embedded.

---

# Setup Python 3.12.4 su macOS con pyenv, Tkinter e dipendenze per Vosk

Questa guida ti aiuta a installare una versione pulita di Python 3.12.4 su macOS usando `pyenv`, configurando correttamente **Tkinter** (tramite Tcl/Tk 8) e installando le dipendenze necessarie per progetti basati su riconoscimento vocale con **Vosk** e **PyAudio**.

---

## ✅ Requisiti

- macOS 13 o successivo (testato su macOS 15.4)
- [Homebrew](https://brew.sh/) installato
- Shell: `zsh` (default su macOS) o `bash`
- `pyenv` per la gestione delle versioni di Python

---

## 📦 1. Installa Tcl/Tk 8 (compatibile con Tkinter)

```bash
brew install tcl-tk@8
```

Poi **aggiungi il percorso di Tcl/Tk al tuo ambiente**:

```bash
echo 'export PATH="/opt/homebrew/opt/tcl-tk@8/bin:$PATH"' >> ~/.zshrc
```

Imposta le variabili per compilare Python con Tkinter:

```bash
export LDFLAGS="-L/opt/homebrew/opt/tcl-tk@8/lib"
export CPPFLAGS="-I/opt/homebrew/opt/tcl-tk@8/include"
export PKG_CONFIG_PATH="/opt/homebrew/opt/tcl-tk@8/lib/pkgconfig"
```

---

## 🐍 2. Installa `pyenv` e `pyenv-virtualenv` (opzionale ma consigliato)

```bash
brew install pyenv
brew install pyenv-virtualenv
```

Aggiungi a `~/.zshrc`:

```bash
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

Poi ricarica la configurazione:

```bash
source ~/.zshrc
```

---

## 📥 3. Installa Python 3.12.4

Assicurati che le variabili d'ambiente di Tcl/Tk siano attive nel terminale, poi:

```bash
pyenv install 3.12.4
```

Imposta Python come versione globale o locale:

```bash
pyenv global 3.12.4   # oppure pyenv local 3.12.4 dentro un progetto
```

---

## 🧪 4. Verifica che Tkinter funzioni

```bash
python -m tkinter
```

✅ Se si apre una piccola finestra, tutto funziona correttamente.

---

## 📚 5. Installa le dipendenze per Vosk e audio

```bash
pip install vosk pyaudio
```

Se `pyaudio` dà errore, installa `portaudio`:

```bash
brew install portaudio
pip install pyaudio
```

---

## 🎉 Fine!

Ora hai:
- Una versione pulita e isolata di Python 3.12.4
- Tkinter funzionante per interfacce grafiche
- Dipendenze installate per progetti basati su riconoscimento vocale

Puoi avviare il tuo progetto con fiducia!

---

**Nota:**
Ogni volta che vuoi reinstallare Python con Tkinter tramite `pyenv`, ricordati di **esportare le variabili LDFLAGS / CPPFLAGS / PKG_CONFIG_PATH** per puntare a Tcl-Tk 8.

## 🛠️ 6. Esegui il tuo progetto

```bash
python secondo_comandamento.py
```
