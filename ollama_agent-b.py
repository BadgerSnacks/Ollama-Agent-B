'''
Coded by: BadgerSnacks
Chat-GPT was used to help write some of the code.
This is for educational purpose and experimentation.
'''

import subprocess
import os

from ollama import chat
from ollama import ChatResponse

#Check to see if Ollama is installed
try:
    subprocess.run(["ollama", "--version"], capture_output=True, text=True)
    print("Ollama is installed!")
except Exception:
    if os.name == "posix":
        _linux_install = True
        while _linux_install:
            _answer = input("Ollama is not installed, Would you like to install it? (y/n): ").lower().strip()
            if _answer == "y":
                print("Installing Ollama...")
                subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True, check=True)
                _linux_install = False
            elif _answer == "n":
                print("Please install Ollama before continuing")
                _linux_install = False
    elif os.name == "nt":
        print("Ollama is not installed on windows!")

try:
    subprocess.run("ollama serve", capture_output=True, text=True)
except Exception:
    print("Something went wrong! The Ollama server did not start.")

#Pick a model from ollama.com/search to use. I suggest llama3.1, gemma3, or mistral
model_name = "gemma3"

#Checks to see if the model is already downloaded, if not it will attempt to download directly from Ollama.com
result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
if model_name not in result.stdout:
    print(f"Model '{model_name}' not found. Pulling...")
    subprocess.run(["ollama", "pull", model_name], check=True)
else:
    print(f"Model '{model_name}' ready to go.")


#Ask user if they would like to set up a personality/ Perhaps add a function to list pregenerated ones.
personality_check = True
personality = "You are a personal chat bot."
while personality_check:
    personality_setup = input("Setup a personality? Y/N: ").lower().strip()
    if personality_setup == "y":
        personality = str(input("Enter personality description: "))
        personality_check = False
        print("Personality saved for session.")
    elif personality_setup == "n":
        print("No personality will be used.")
        personality_check = False
    elif personality_setup != "y" or "n":
        print("Please enter Y or N")

#Default personality's
it_professional = "A calm, sharp-minded IT professional specializing in cybersecurity. Speaks clearly and efficiently, with a dry sense of humor and zero tolerance for sloppy code or weak passwords. Values logic, precision, and digital hygiene. Enjoys explaining complex systems in plain language. Treats every conversation like a troubleshooting session — diagnose, verify, patch, move on. Believes security is not paranoia; it’s preparation"


# Code created with the help of chat-GPT to summerize the chat content.
def summarize_with_ollama(model: str, current_summary: str, recent_text: str, limit_chars: int = 800) -> str:
    """
    Merge current_summary with recent_text into a concise running summary.
    Uses the same model via ollama.chat. Returns plaintext <= limit_chars.
    """
    summary_messages = [ #This block of code is the actual message that is sent to the AI model to tell it how to summerize the conversation
        {
            "role": "system",
            "content": (
                "You are a careful summarizer. Update the running summary using the NEW MESSAGES. "
                f"Keep it concise (<= {limit_chars} characters). "
                "Preserve durable facts, decisions, constraints, and open tasks. "
                "Do not invent facts. No markdown, bullets optional, plain text only."
            ),
        },
        {
            "role": "user",
            "content": (
                f"CURRENT SUMMARY: \n{current_summary}\n\n"
                f"NEW MESSAGES: \n{recent_text}\n\n"
                "Return the updated summary now."
            ),
        },
    ]
    try:
        resp: ChatResponse = chat(model=model, messages=summary_messages) #This sends the summary above to the AI model and retrieves a response
        text = (resp.message.content or "").strip()
        return text[:limit_chars]
    except Exception:
        # If anything goes wrong, keep the old summary (Fail-safe).
        return current_summary

def ping_with_ollama(ip: str):
    try:
        if os.name == "nt":
            args = ["ping", "-n", "4", ip]
        else:
            args = ["ping", "-c", "1", ip]

        _ping = subprocess.run(f"ping {ip}", capture_output=True, text=True)
        if _ping.returncode == 0:
            return _ping.stdout
        else:
            return (_ping.stdout or _ping.stderr or "Ping fialed").strip()
    except Exception as e:
        print(f"Ping failed: {e}")


SUMMARY_TRIGGER_LINES = 20 # When memory has this many lines, summarize
MEMORY_TAIL_LINES = 16    # after summarizing, keep only this many lines (approx. 8 exchanges)
RECENT_WINDOW_LINES = 24  # how many recent lines to feed the summarizer
running_summary = ""      # Added: the compact synopsis



#Variables used for the while loop function that handles the chat
chatting = True #used to keep the while loop going
memory = [] #memory arry to keep track of current chat before it is summerized.

#Display Useful Instructions for user here, like how to quit and any specific keywords.
print("Type #help for list of functions.")

#While loop function for the actual chat logic
while chatting:
    user_input = str(input(">>> "))

    if user_input == "#help":
        print(
            "#quit - exit the program.\n#ping - followed by an IP address to have the AI give feedback on open ports.\nMore functions to come."
              )
        continue

    if user_input == "#ping":
        _ip = input("What is the address: ").strip()
        ping_text = ping_with_ollama(_ip)

        content = (
            f"[Personality]\n{it_professional}\n\n"
            f"[Task]\nAnalyze the ping output below. Explain latency, packet loss, TTL, and likely network health."
            f"Flag any anomalies. Give actionable next steps for deeper diagnostics.\n\n"
            f"[Ping Output]\n{ping_text}]"
            f"[User]\nThe Target was: {_ip}\n\n"
        )
        response: ChatResponse = chat(model=model_name, messages=[
            {"role": "user", "content": content}
        ])
        print("\n", response.message.content, "\n")
        memory.append(f"User: #ping {_ip}")
        memory.append(f"Assistant: {response.message.content}")
        continue

    if user_input == "#quit":
        print("Goodbye")
        break

    memory_text = "\n".join(memory)  # Joins memory to a text line

    running_summary_block = f"[Running Summary]\n{running_summary}\n\n" if running_summary else ""

    # This breaks the content down with labels that the AI can read and understand. These can be edited
    content = (
        f"[Personality]\n{personality}\n\n"
        f"{running_summary_block}"
        f"[Conversation Memory]\n{memory_text}\n\n"
        f"[User]\n{user_input}\n]"
    )

    #This is the response given to use by the model that is actually seen.
    response: ChatResponse = chat(model= model_name, messages=[
        {
            'role': 'user',
            'content': content
        },
    ])
    print("\n",response.message.content,"\n")

    memory.append(f"User: {user_input}")
    memory.append(f"Assistant: {response.message.content}")

    if len(memory) >= SUMMARY_TRIGGER_LINES:
        recent_chunk = "\n".join(memory[-RECENT_WINDOW_LINES:])
        running_summary = summarize_with_ollama(model_name, running_summary, recent_chunk)
        # Prune old memory now that the info is in the summary
        memory = memory[-MEMORY_TAIL_LINES:]
