try:
    import speech_recognition as sr
    VOICE_AVAILABLE = True
except ImportError:
    sr = None
    VOICE_AVAILABLE = False

class VoiceHandler:
    def __init__(self):
        if VOICE_AVAILABLE:
            self.recognizer = sr.Recognizer()
        else:
            self.recognizer = None

    def listen(self):
        """
        Listens to the microphone and returns the transcribed text.
        Raises RequestError or UnknownValueError on failure.
        """
        if not VOICE_AVAILABLE:
            raise Exception("Voice recognition is not available on this platform.")

        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen
                print("Listening...")
                audio = self.recognizer.listen(source, timeout=30, phrase_time_limit=120)
                
                # Transcribe (Google Web Speech API - Free)
                # Setting language to German by default, but it often auto-detects or we can make it configurable
                text = self.recognizer.recognize_google(audio, language="de-DE")
                print(f"Recognized: {text}")
                return text
                
        except sr.WaitTimeoutError:
            raise Exception("No speech detected (Timeout).")
        except sr.UnknownValueError:
            raise Exception("Could not understand audio.")
        except sr.RequestError as e:
            raise Exception(f"Service error: {e}")
        except Exception as e:
            raise Exception(f"Microphone error: {e}")
