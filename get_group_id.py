"""
A standalone script to get the chat ID of a Telegram group.

How to use:
1.  Add your bot to the Telegram group you want the ID for.
2.  Send any message to that group (e.g., "/start" or "hello").
3.  Replace 'YOUR_BOT_TOKEN_HERE' below with your actual bot token.
4.  Run this script from your terminal: python get_group_id.py
5.  The script will print the names and IDs of all chats the bot has seen.
    Look for your group's name and copy its ID (it will be a negative number).
"""

import requests
import json

# --- IMPORTANT: PASTE YOUR BOT TOKEN HERE ---
BOT_TOKEN = "7981227869:AAFqe9uj5wWMQWRPT0qk11WWh0G7pceeABk"


def get_chat_updates():
    """Fetches the latest updates for the bot to find chat IDs."""
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Error: Please replace 'YOUR_BOT_TOKEN_HERE' with your bot's API token.")
        return

    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    
    print("Fetching updates from Telegram...")

    try:
        response = requests.get(api_url, timeout=10)
        
        if response.status_code != 200:
            print(f"Error: Failed to connect to Telegram API. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
            
        data = response.json()

        if not data.get("ok"):
            print(f"Error: Telegram API returned an error: {data.get('description')}")
            return

        updates = data.get("result", [])
        
        if not updates:
            print("\nNo recent messages found for this bot.")
            print("Please make sure you have sent a message to the bot in the group.")
            return

        print("\n--- Found Recent Chats ---")
        found_chats = {}
        for update in updates:
            if "message" in update:
                chat_info = update["message"]["chat"]
                chat_id = chat_info["id"]
                chat_title = chat_info.get("title", "Direct Chat with User")
                
                if chat_id not in found_chats:
                    found_chats[chat_id] = chat_title
                    print(f"\nChat Name: {chat_title}")
                    print(f"  --> ID: {chat_id}")

        print("\n--- End of List ---")
        print("Group IDs are the negative numbers. Private chat IDs are positive.")

    except requests.exceptions.RequestException as e:
        print(f"A network error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    get_chat_updates()
