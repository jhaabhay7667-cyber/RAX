
import pyttsx3

engine = pyttsx3.init("sapi5")

engine.setProperty("rate", 175)
engine.setProperty("volume", 1.0)

voices = engine.getProperty("voices")

print("Available voices:")
for i, voice in enumerate(voices):
    print(i, voice.name)

if voices:
    engine.setProperty("voice", voices[0].id)

engine.say("Hello Abhay. This is RAX speaking. If you can hear me, text to speech is working.")
engine.runAndWait()

print("Finished speaking.")