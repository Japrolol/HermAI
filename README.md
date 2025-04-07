# HermAI

A voice-activated AI assistant inspired by Iron Man's JARVIS. This Python project uses OpenAI and Ollama models with Vosk speech recognition to create a responsive interface that listens for "Hey Jarvis" wake words. Features include natural text-to-speech, web visualization, and conversation memory. Works with both cloud and local AI capabilities.

## Features

- **Wake Word Detection**: Listens for the "Hey Jarvis" wake word.
- **Speech Recognition**: Uses Vosk for speech recognition.
- **AI Models**: Integrates with OpenAI and Ollama models for AI capabilities.
- **Text-to-Speech**: Provides natural text-to-speech responses.
- **Web Visualization**: Offers a web-based interface for visualizing interactions.
- **Conversation Memory**: Remembers past interactions to provide contextually relevant responses.
- **Cloud and Local AI**: Supports both cloud-based and local AI processing.

## Installation

### Python Dependencies

1. Clone the repository:
    ```bash
    git clone https://github.com/Japrolol/HermAI.git
    cd HermAI
    ```

2. Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows, use `venv\Scripts\activate`
    ```

3. Install the Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up environment variables for your OpenAI and Ollama API keys.

### Node.js and npm Dependencies

1. Ensure you have [Node.js](https://nodejs.org/) and [npm](https://www.npmjs.com/) installed.

2. Install the Node.js dependencies:
    ```bash
    npm install
    ```

## Usage

1. Activate the Python virtual environment:
    ```bash
    source venv/bin/activate # On Windows, use `venv\Scripts\activate`
    ```

2. Run the main script:
    ```bash
    python main.py
    ```

3. Interact with HermAI using the wake word "Hey Jarvis".

## Contributing

Contributions are welcome! Please fork the repository and open a pull request with your changes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Acknowledgments

- Inspired by Iron Man's JARVIS.
- Uses OpenAI and Ollama models.
- Speech recognition powered by Vosk.
