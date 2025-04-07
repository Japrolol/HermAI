"""
JARVIS AI Assistant
-------------------
A voice-activated AI assistant that uses OpenAI and Ollama models to process and respond to user queries.
Features:
- Wake word detection ("Hey Jarvis")
- Speech recognition using Vosk
- Text-to-speech responses
- Integration with OpenAI Assistants API
- Fallback to local Ollama models
- Web interface communication via WebSockets
- Conversation history tracking
- Background visualization with Three.js
- Voice interruption capability
- Automatic return to wake word listening after silence

This system mimics the JARVIS AI from Iron Man, responding to voice commands
and providing informative responses through speech and visual feedback.
"""

import json
import random
import ollama
import openai
from dotenv import load_dotenv
import pyttsx3
import queue
import sounddevice as sd
import vosk
import numpy as np
import asyncio
import aiohttp
import pygame
import time

load_dotenv()
model = "gpt-4o-mini"
audio_model = vosk.Model("vosk-model-small-en-us-0.15")
recognizer = vosk.KaldiRecognizer(audio_model, 16000)
wake_word = ["hey jarvis", "hi jarvis", "he jarvis", "h jarvis", "jarvis"]
q = queue.Queue()
threshold = 3000
silence_timeout = 5

listening_event = True
user_turn = True
speaking = False
assistant_manager = None
ollama_manager = None
last_user_input_time = 0

engine = pyttsx3.init()
engine.setProperty('rate', 170)
engine.setProperty('volume', 0.9)
engine.setProperty('voice', "com.apple.voice.premium.en-AU.Lee")


async def send_prompt_data(role, content):
    """Send prompt data to the web interface via HTTP POST request and save to conversation history."""
    url = "http://localhost:8000/prompt_response"
    data = {
        "role": role,
        "content": content
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                response_data = await response.json()
    except Exception as e:
        print(f"Error sending data to server: {e}")

    try:
        with open("conversation_history.json", 'r') as f:
            history = json.load(f)
            if not isinstance(history, list):
                history = []
    except (FileNotFoundError, json.JSONDecodeError):
        history = []

    history.append(data)
    with open("conversation_history.json", 'w') as f:
        json.dump(history, f, indent=4)


def play_wav_file(file):
    """Play an audio file using pygame mixer."""
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        print(f"Error playing audio file: {e}")


async def speak(text, is_prompt_response=False):
    """Convert text to speech and manage speaking state."""
    global speaking, user_turn, last_user_input_time

    speaking = True
    user_turn = False
    print(f"Speaking: {text}")

    async def run_speech():
        engine.say(text)
        engine.runAndWait()

    speech_task = asyncio.create_task(run_speech())
    await speech_task

    speaking = False
    user_turn = True

    last_user_input_time = time.time()


def audio_callback(indata, frames, timeinfo, status):
    """Common callback function for audio streams to detect speech."""
    global listening_event, user_turn, speaking, last_user_input_time

    if status:
        print(f"Audio status: {status}")

    amplitude = np.linalg.norm(indata)

    if listening_event and user_turn and not speaking:
        if amplitude > threshold:
            q.put(bytes(indata))
            last_user_input_time = time.time()


async def listen_for_audio(message_type="prompt", timeout=None):
    """Listen for audio input and process it accordingly."""
    global user_turn, speaking, q, recognizer, last_user_input_time

    print(f"Listening for {message_type}...")
    last_user_input_time = time.time()

    while not q.empty():
        try:
            q.get_nowait()
        except queue.Empty:
            break

    recognizer = vosk.KaldiRecognizer(audio_model, 16000)

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                          channels=1, callback=audio_callback) as stream:
        start_time = time.time()

        while True:
            current_time = time.time()
            if timeout and (current_time - last_user_input_time) > timeout:
                print(f"Silence timeout reached ({timeout}s), returning to wake word listening")
                stream.close()
                await listen_for_wake_word()
                return

            if speaking and message_type == "additional prompt":
                await asyncio.sleep(0.1)
                continue

            try:
                data = None
                try:
                    data = q.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.1)
                    continue

                if data and recognizer.AcceptWaveform(data):
                    result = recognizer.Result()
                    result_dict = json.loads(result)
                    text = result_dict.get('text', '')
                    if (text == ''):
                        await listen_for_wake_word()
                        return

                    if text:
                        stream.close()
                        await process_prompt(text)
                        return
            except Exception as e:
                print(f"Error processing audio: {e}")
                await asyncio.sleep(0.1)

            await asyncio.sleep(0.05)

        stream.close()
        await listen_for_wake_word()
        return


async def listen_for_prompt():
    """Listen for the main prompt after wake word activation."""
    return await listen_for_audio("prompt")


async def listen_for_additional_prompt():
    """Listen for additional prompts after an initial response with a timeout."""
    return await listen_for_audio("additional prompt", timeout=silence_timeout)


async def detected_callback():
    """Handle wake word detection and prepare for user prompt."""
    global listening_event, user_turn, speaking

    print("Wake word detected!")
    listening_event = False
    user_turn = False

    await speak(random.choice([
        "Yes, how can I help you?",
        "Yes, what can I do for you?",
        "Yes, how can I assist you?",
        "I'm here."
    ]), is_prompt_response=False)

    while speaking:
        await asyncio.sleep(0.1)

    await asyncio.sleep(0.5)

    user_turn = True
    listening_event = True
    await listen_for_prompt()


async def listen_for_wake_word():
    """Listen continuously for wake word activation."""
    global user_turn, recognizer, q

    recognizer = vosk.KaldiRecognizer(audio_model, 16000)
    while not q.empty():
        try:
            q.get_nowait()
        except queue.Empty:
            break

    print("Listening for wake word...")

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                          channels=1, callback=audio_callback) as stream:
        while True:
            if user_turn:
                try:
                    data = None
                    try:
                        data = q.get_nowait()
                    except queue.Empty:
                        await asyncio.sleep(0.1)
                        continue

                    if data and recognizer.AcceptWaveform(data):
                        result = recognizer.Result()
                        result_dict = json.loads(result)
                        text = result_dict.get('text', '').lower()

                        if any(item in text for item in wake_word):
                            print(f"Detected wake word in: '{text}'")
                            stream.close()
                            await detected_callback()
                            break
                except Exception as e:
                    print(f"Error in wake word detection: {e}")
                    await asyncio.sleep(0.1)

            await asyncio.sleep(0.05)


async def process_prompt(prompt):
    """Process user prompt and get AI response."""
    global assistant_manager, ollama_manager, last_user_input_time

    last_user_input_time = time.time()
    print(f"User prompt: '{prompt}'")
    await send_prompt_data(role="user", content=prompt)
    await run_assistant(assistant_manager, ollama_manager, message=prompt)
    await listen_for_additional_prompt()


class OllamaManager:
    """Manage interactions with local Ollama models."""

    def __init__(self, model="jarvis", history_file="history.json"):
        self.model = model
        self.client = ollama.Client(host="http://localhost:11434")
        self.memory = []
        self.history_file = history_file
        self.load_history()

    async def generate_message(self, message):
        """Generate a response using the Ollama model."""
        self.memory.append({'role': 'user', 'content': message})
        try:
            response = await ollama.AsyncClient().chat(model=self.model, messages=self.memory)
            content = response['message']['content']

            self.memory.append({'role': 'assistant', 'content': content})
            self.append_history()
            await send_prompt_data(role="assistant", content=content)

            return content
        except Exception as e:
            print(f"Error generating Ollama response: {e}")
            return "I'm sorry, I encountered an error processing your request."

    def append_history(self):
        """Append conversation to history file."""
        try:
            with open(self.history_file, 'r') as f:
                history = json.load(f)
                if not isinstance(history, list):
                    history = []
        except (FileNotFoundError, json.JSONDecodeError):
            history = []

        history.extend(self.memory[-50:])

        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=4)

    def load_history(self):
        """Load conversation history from file."""
        try:
            with open(self.history_file, 'r') as f:
                self.memory = json.load(f)
                if not isinstance(self.memory, list):
                    self.memory = []
        except (FileNotFoundError, json.JSONDecodeError):
            self.memory = []


class AssistantManager:
    """Manage interactions with OpenAI Assistant API."""

    thread_id = "thread_dIhNIp3uEFkoqT1mFWNCu2U4"
    assistant_id = "asst_XEIk1VCTAepIKUkoRTqdD7LR"

    def __init__(self, model: str = model):
        self.client = openai.OpenAI()
        self.model = model
        self.assistant = None
        self.thread = None
        self.run = None
        self.summary = None

        if AssistantManager.assistant_id:
            self.assistant = self.client.beta.assistants.retrieve(
                assistant_id=AssistantManager.assistant_id
            )
        if AssistantManager.thread_id:
            self.thread = self.client.beta.threads.retrieve(
                thread_id=AssistantManager.thread_id
            )

    def create_assistant(self, name: str, instructions: str, tools):
        """Create a new assistant if one doesn't exist."""
        if not self.assistant:
            assistant_obj = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                model=self.model,
                tools=tools
            )
            AssistantManager.assistant_id = assistant_obj.id
            self.assistant = assistant_obj

    def create_thread(self):
        """Create a new thread if one doesn't exist."""
        if not self.thread:
            thread_obj = self.client.beta.threads.create()
            AssistantManager.thread_id = thread_obj.id
            self.thread = thread_obj

    def add_message_to_thread(self, role, content):
        """Add a message to the current thread."""
        if self.thread:
            self.client.beta.threads.messages.create(
                thread_id=AssistantManager.thread_id,
                role=role,
                content=content
            )

    def run_assistant(self, instructions=None):
        """Run the assistant with the current thread."""
        if not instructions:
            instructions = """
            You are called JARVIS (Just A Rather Very Intelligent System).
            You are an AI Assistant in the Herma household, specifically for Jakub (Japro).
            Give short and concise answers. You specialize in technology.
            You are made in Python and Three.js. You are a voice assistant so don't use weird characters. Don't try to format the message, just sound good. Don't make too long messages because I cannot interrupt you if you say the wrong thing
            """

        if self.thread and self.assistant:
            self.run = self.client.beta.threads.runs.create(
                assistant_id=self.assistant.id,
                thread_id=self.thread.id,
                instructions=instructions
            )

    async def process_message(self):
        """Process the latest message from the assistant."""
        if self.thread:
            messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
            summary = []

            last_message = messages.data[0]
            response = last_message.content[0].text.value
            summary.append(response)

            self.summary = "\n".join(summary)
            print(f"Jarvis: {response}")
            await send_prompt_data(role="assistant", content=response)
            await speak(response, is_prompt_response=True)

    def call_required_functions(self, required_actions):
        """Handle function calls required by the assistant."""
        if not self.run:
            return

        tools_outputs = []

        for action in required_actions["tool_calls"]:
            func_name = action["function"]["name"]
            arguments = json.loads(action["function"]["arguments"])

        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread.id,
            run_id=self.run.id,
            tool_outputs=tools_outputs
        )

    def get_summary(self):
        """Get a summary of the conversation."""
        return self.summary

    async def wait_for_completed(self):
        """Wait for the assistant run to complete."""
        if self.thread and self.run:
            while True:
                await asyncio.sleep(1)
                try:
                    run_status = self.client.beta.threads.runs.retrieve(
                        thread_id=self.thread.id,
                        run_id=self.run.id
                    )

                    if run_status.status == "completed":
                        await self.process_message()
                        break
                    elif run_status.status == "requires_action":
                        self.call_required_functions(
                            required_actions=run_status.required_action.submit_tool_outputs.model_dump()
                        )
                except Exception as e:
                    print(f"Error checking assistant run status: {e}")
                    break

    def run_steps(self):
        """List the steps of the current run."""
        if self.thread and self.run:
            run_steps = self.client.beta.threads.runs.steps.list(
                thread_id=self.thread.id,
                run_id=self.run.id
            )
            print(f"Run Steps: {run_steps}")


async def run_assistant(assistant_manager=None, ollama_manager=None, message="Hello"):
    """Run either the OpenAI assistant or Ollama model based on availability."""
    try:
        if assistant_manager:
            assistant_manager.add_message_to_thread(role="user", content=message)
            assistant_manager.run_assistant()
            await assistant_manager.wait_for_completed()
        elif ollama_manager:
            response = await ollama_manager.generate_message(message)
            print(f"Jarvis: {response}")
            await speak(response, is_prompt_response=True)
        else:
            print("No AI model available")
            await speak("I'm sorry, but I don't have an AI model available right now.", is_prompt_response=False)
    except Exception as e:
        print(f"Error in run_assistant: {e}")
        await speak("I encountered an error processing your request.", is_prompt_response=False)


async def main():
    """Initialize the JARVIS system and start listening for commands."""
    global assistant_manager, ollama_manager

    print("Initializing JARVIS...")

    try:
        assistant_manager = AssistantManager()
        print("OpenAI Assistant initialized")
    except Exception as e:
        print(f"Failed to initialize OpenAI Assistant: {e}")
        try:
            ollama_manager = OllamaManager()
            print("Ollama model initialized")
        except Exception as e:
            print(f"Failed to initialize Ollama model: {e}")
            print("Warning: No AI model available, JARVIS will have limited functionality")

    print("JARVIS is now online")

    await listen_for_wake_word()


if __name__ == "__main__":
    asyncio.run(main())