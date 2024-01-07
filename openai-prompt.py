import threading
import time
import subprocess
import random
import argparse
from pathlib import Path
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown
from rich.rule import Rule

def loading_animation():
    console = Console()
    spinner = "|/-\\"
    idx = 0
    while not stop_loading:
        console.print(spinner[idx % len(spinner)], end="\r")
        idx += 1
        time.sleep(0.1)

def chat_with_model(model, messages):
    client = OpenAI()

    #custom_instructions = "\nBreak down complex concepts into understandable explanations. Where applicable, use analogies or examples to clarify your points.\n"
    custom_instructions = "\nBe informal.\n"
    messages.append({"role": "system", "content": custom_instructions})

    completion = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1500,
            temperature=0
            )

    response_content = completion.choices[0].message.content
    messages.append({"role": "assistant", "content": response_content})
    return response_content

def copy_to_clipboard(text):
    command = 'copyq add -'
    subprocess.run(command, input=text, text=True, shell=True)

def main(topic=None):
    global stop_loading
    stop_loading = False

    # Define a list of possible topics
    possible_topics = ["devops", "machine learning", "web development", "data science", "game development"]

    # If topic is not provided, choose a random one from the list
    if not topic:
        topic = random.choice(possible_topics)

    # Define the file path for storing the conversation history
    config_path = Path.home() / ".config" / "openaiprompt"
    config_path.mkdir(parents=True, exist_ok=True)
    history_file_path = config_path / f"{topic}.txt"

    console = Console(width=100)
    console.print(f"Starting interactive chat with GPT-5 on topic '{topic}'. Type ':exit' to exit.", style="bold blue")

    # Load and display previous conversation history if it exists
    conversation_history = []
    if history_file_path.exists():
        with open(history_file_path, 'r') as file:
            lines = file.readlines()
            conversation_history = [{"role": "user", "content": line.strip()} for line in lines]
            previous_conversation = ''.join(lines)
            if previous_conversation.strip():
                console.print("\n[bold cyan]Previous conversation:[/bold cyan]")
                console.print(Markdown(previous_conversation))


    while True:
        console.print("\n[bold cyan]Enter your message (end with ':go' and press Enter to send):[/bold cyan]")
        input_lines = []
        while True:
            line = console.input()
            if line.strip() == ":exit":
                with open(history_file_path, 'w') as file:
                    for message in conversation_history:
                        file.write(message["content"] + "\n")
                return
            if line.strip() == ":go":
                break
            input_lines.append(line)
        user_message = "\n".join(input_lines)

        if not user_message.strip() or user_message.strip() == ":go":
            continue

        conversation_history.append({"role": "user", "content": user_message})

        console.print(Rule(style="bright_black"))

        stop_loading = False
        thread = threading.Thread(target=loading_animation)
        thread.start()

        response = chat_with_model("gpt-4-1106-preview", conversation_history)

        stop_loading = True
        thread.join()

        markdown_response = Markdown(response)
        console.print(markdown_response)

        copy_to_clipboard(response)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Interact with OpenAI GPT model on a specific topic.')
    parser.add_argument('--topic', help='The topic for the conversation (optional)', default=None)
    args = parser.parse_args()
    main(args.topic)
