import os
import re
import yt_dlp
from openai import OpenAI
from pydub import AudioSegment
import math

class YouTubeTranscriber:
    def __init__(self, model_size="base", use_openai_api=False, openai_api_key=None):
        """
        Initialize the transcriber with local Whisper model or OpenAI Whisper API
        :param model_size: Size of the local Whisper model (e.g., "base", "large")
        :param use_openai_api: Whether to use OpenAI Whisper API
        :param openai_api_key: OpenAI API key (required if use_openai_api=True)
        """
        self.use_openai_api = use_openai_api
        
        # Only set API-specific constraints if using OpenAI API
        if use_openai_api:
            if not openai_api_key:
                raise ValueError("OpenAI API key is required when using OpenAI Whisper API.")
            self.client = OpenAI(api_key=openai_api_key)
            self.MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB in bytes
            self.SEGMENT_LENGTH = 15 * 60 * 1000    # 10 minutes in milliseconds
            print("Using OpenAI Whisper API")
        else:
            import whisper
            print(f"Loading local Whisper model ({model_size})...")
            self.model = whisper.load_model(model_size)
            print("Local model loaded successfully")

    def sanitize_filename(self, filename):
        """Replace illegal characters in the filename with underscores."""
        return re.sub(r'[<>:"/\\|?*]', '_', filename)

    def download_audio(self, url, output_path="downloads"):
        """Download the audio part of a YouTube video using yt-dlp."""
        try:
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            info_extractor = yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True})
            info = info_extractor.extract_info(url, download=False)
            raw_title = info.get('title', 'unknown_title')
            safe_title = self.sanitize_filename(raw_title)

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(output_path, f'{safe_title}.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': False,
                'no_warnings': True,
            }

            print(f"Downloading video: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            downloaded_file = os.path.join(output_path, f"{safe_title}.mp3")
            if not os.path.exists(downloaded_file):
                raise FileNotFoundError(f"Downloaded file not found: {downloaded_file}")

            print(f"Audio downloaded to: {downloaded_file}")
            return downloaded_file

        except Exception as e:
            raise Exception(f"Error while downloading audio: {str(e)}")

    def split_audio_file(self, audio_file):
        """Split audio file into segments smaller than 25MB."""
        try:
            print(f"Loading audio file: {audio_file}")
            audio = AudioSegment.from_mp3(audio_file)
            duration = len(audio)
            
            # Calculate number of segments needed
            num_segments = math.ceil(duration / self.SEGMENT_LENGTH)
            segments = []
            
            print(f"Splitting audio into {num_segments} segments...")
            for i in range(num_segments):
                start = i * self.SEGMENT_LENGTH
                end = min((i + 1) * self.SEGMENT_LENGTH, duration)
                
                segment = audio[start:end]
                segment_path = f"{audio_file[:-4]}_segment_{i}.mp3"
                segment.export(segment_path, format="mp3")
                
                # Verify segment size
                if os.path.getsize(segment_path) > self.MAX_FILE_SIZE:
                    raise Exception(f"Segment {i} is still larger than 25MB after splitting")
                
                segments.append(segment_path)
                print(f"Created segment {i+1}/{num_segments}")
            
            return segments
            
        except Exception as e:
            raise Exception(f"Error while splitting audio file: {str(e)}")

    def transcribe_audio_local(self, audio_file, language=None):
        """Transcribe audio file using the local Whisper model."""
        try:
            import whisper
            print(f"Starting transcription for audio: {audio_file}")

            if language is None:
                print("Detecting audio language...")
                audio = whisper.load_audio(audio_file)
                audio = whisper.pad_or_trim(audio)
                mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
                _, probs = self.model.detect_language(mel)
                detected_language = max(probs, key=probs.get)
                print(f"Detected language: {detected_language}")
                language = detected_language

            print(f"Using language: {language}")
            result = self.model.transcribe(
                audio_file,
                language=language,
                task="transcribe"
            )

            return result["text"], language
            
        except Exception as e:
            raise Exception(f"Error while transcribing audio locally: {str(e)}")
    
    def get_iso639_1_code(self, language_name):
        """Map language name to ISO-639-1 code."""
        language_map = {
            "English": "en",
            "Chinese": "zh",
            "Spanish": "es",
            "French": "fr",
            "German": "de",
            "Japanese": "ja",
            "Korean": "ko",
            "Russian": "ru",
            "Portuguese": "pt",
            "Italian": "it",
            "Arabic": "ar"
        }
        return language_map.get(language_name, None)

    def transcribe_audio_openai(self, audio_file, language=None):
        """Transcribe audio file using OpenAI Whisper API."""
        try:
            iso_language = self.get_iso639_1_code(language) if language else None
            # Check if file size exceeds limit
            if os.path.getsize(audio_file) > self.MAX_FILE_SIZE:
                print("File size exceeds 25MB limit, splitting into segments...")
                segments = self.split_audio_file(audio_file)
                transcriptions = []
                
                for i, segment in enumerate(segments):
                    print(f"Transcribing segment {i+1}/{len(segments)}")
                    with open(segment, "rb") as f:
                        response = self.client.audio.transcriptions.create(
                            file=f, 
                            model="whisper-1", 
                            language=iso_language
                        )
                    transcriptions.append(response.text)
                    
                    # Clean up segment file
                    os.remove(segment)
                
                transcription = " ".join(transcriptions)
            else:
                print(f"Transcribing audio using OpenAI API: {audio_file}")
                with open(audio_file, "rb") as f:
                    response = self.client.audio.transcriptions.create(
                        file=f, 
                        model="whisper-1", 
                        language=iso_language
                    )
                transcription = response.text
            
            return transcription, language
        
        except Exception as e:
            # Clean up any remaining segment files in case of error
            if 'segments' in locals():
                for segment in segments:
                    if os.path.exists(segment):
                        try:
                            os.remove(segment)
                        except:
                            pass
            raise Exception(f"Error while transcribing audio with OpenAI API: {str(e)}")

    def transcribe_audio(self, audio_file, language=None):
        """Transcribe audio using the selected method (local or OpenAI API)."""
        if self.use_openai_api:
            transcription, detected_language = self.transcribe_audio_openai(audio_file, language)
        else:
            transcription, detected_language = self.transcribe_audio_local(audio_file, language)
            
        # Save transcription to file
        output_txt = audio_file.rsplit(".", 1)[0] + ".txt"
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(transcription)
        
        print(f"Transcription saved to: {output_txt}")
        return transcription, output_txt, detected_language

    def process_video(self, url, language=None, keep_audio=False):
        """
        Full process: download video audio and transcribe.
        If language is not specified, it will be detected automatically.
        """
        audio_file = None
        try:
            print(f"Processing video: {url}")

            audio_file = self.download_audio(url)

            transcription, output_txt, detected_language = self.transcribe_audio(audio_file, language)

            if not keep_audio and audio_file and os.path.exists(audio_file):
                os.remove(audio_file)
                print("Audio file deleted")
            
            return transcription, output_txt, detected_language
            
        except Exception as e:
            if audio_file and os.path.exists(audio_file) and not keep_audio:
                try:
                    os.remove(audio_file)
                except:
                    pass
            raise Exception(f"Error while processing video: {str(e)}")