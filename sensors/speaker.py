import os
import uuid
import asyncio
from gtts import gTTS

class Speaker:
    def __init__(self, language="en"):
        self.language = language
        self.lock = asyncio.Lock()
        self.audio_dir = "./audio"
    
    async def say(self, message):
        async with self.lock:
            filename = f"message_{uuid.uuid4()}.mp3"
            try:
                tts = gTTS(text=message, lang=self.language)
                tts.save(filename)
                await self._play_mp3(filename)
            except Exception as e:
                print(f"Error generating or playing speech: {e}")
            finally:
                if os.path.exists(filename):
                    os.remove(filename)
    
    async def play_audio(self, file_name):
        async with self.lock:
            file_path = os.path.join(self.audio_dir, f"{file_name}.mp3")
            if not os.path.exists(file_path):
                print(f"Error: File '{file_path}' does not exist.")
                return
            await self._play_mp3(file_path)
    
    async def _play_mp3(self, file_path):
        try:
            process = await asyncio.create_subprocess_exec(
                "mpg123", file_path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await process.communicate()
        except Exception as e:
            print(f"Error playing audio file '{file_path}': {e}")
