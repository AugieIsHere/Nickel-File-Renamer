# Nickel File Renamer

A powerful file renaming tool that uses AI to suggest better names for your files and folders. Built with Python, Cline, and OpenRouter AI.

## Features

- Directory tree browser for easy navigation and selection
- Select multiple files and folders for renaming
- Choose to rename folders individually or their contents separately
- AI-powered name suggestions using OpenRouter AI
- Multiple AI model options with support for custom model IDs
- Customizable renaming instructions with savable presets
- Preview of original and suggested names with in-line editing
- Batch rename operations
- User-friendly GUI interface
- Session persistence (remembers last used model and instruction preset)

## Prerequisites

- Python 3.8 or higher
- OpenRouter API key (get one at https://openrouter.ai/)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/AugieIsHere/Nickel-File-Renamer/.git
cd Nickel-File-Renamer
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Set up your OpenRouter API key:
   - Get an API key from https://openrouter.ai/
   - Create a `.env` file in the project root
   - Add your API key: `OPENROUTER_API_KEY=your_api_key_here`

## Usage

1. Run the application:
```bash
python nickel_file_renamer.py
```

2. Select a root directory to start browsing when prompted

3. Use the directory tree in the left panel to navigate your file system:
   - Double-click folders to expand/collapse them
   - Right-click items for context menu options:
     - "Select Item" - Add the item to your selection
     - "Select Contents" - Add all items in a folder to your selection
     - "Expand/Collapse" - Expand or collapse a folder

4. View and manage your selected items in the right panel:
   - Right-click to remove items from your selection
   - Use "Clear Selection" to remove all selected items

5. Choose an AI model from the dropdown menu or type a custom model ID
   - Click the "?" button next to the model dropdown for format help
   - You can use any model supported by OpenRouter

6. Enter custom instructions for the AI (optional)

7. Save and manage instruction presets:
   - Click "Save Current" to save the current instruction as a preset
   - Choose from existing presets in the dropdown
   - Click "Load" to load a selected preset
   - Click "Delete" to remove a preset

8. Click "Get AI Suggestions" to receive AI-powered name suggestions

9. Review the suggestions in the results table:
   - Double-click on any suggested name to edit it directly
   - Use "Select All" or "Deselect All" to manage selections
   - Click "Reject Selected" to move items back to the selection list
   - The Type column indicates whether each item is a File or Folder

10. Click "Apply Selected Renames" to perform the rename operations

## Customization

You can customize the AI's behavior by modifying the instructions in the input field. Examples:
- "Make all names lowercase and replace spaces with underscores"
- "Add date prefix to all files"
- "Make names more descriptive based on content"
- "Standardize naming across all files"

## AI Models

The application supports all AI models available through OpenRouter. Pre-configured models include:

### Anthropic Models
- Claude 3 Opus/Sonnet/Haiku

### OpenAI Models
- GPT-4o
- GPT-4 Turbo
- GPT-3.5 Turbo

### Google Models
- Gemini 1.5 Pro/Flash

### Mistral Models
- Mistral Large/Medium/Small

### Meta Models
- Llama 3 (70B and 8B)

### Cohere Models
- Command R Plus/R

### DeepSeek Models
- DeepSeek Chat v3
- DeepSeek R1 (including free versions)

You can also enter any custom model ID supported by OpenRouter in the format `provider/model-name`. Visit the [OpenRouter models page](https://openrouter.ai/models) for a current list of all available models.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
