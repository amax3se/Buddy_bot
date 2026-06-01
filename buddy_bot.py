from vkbottle import Bot, Keyboard, KeyboardButtonColor, Text
from vkbottle.http import SingleAiohttpClient
from vkbottle.api import API
from aiohttp import TCPConnector
import asyncio
from openai import AsyncOpenAI
from openai import APIError, APIConnectionError, RateLimitError
import dotenv
import json
import os

def main():
    dotenv.load_dotenv()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    vk_token = os.getenv("VK_API_KEY")
    
    client = Bot(
        api=API(
            token=vk_token,
            http_client=SingleAiohttpClient(
                connector=TCPConnector(ssl=False, loop = loop)
            )
        )
    )

    clientai = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )

    messages={}
    user_roles = {}

    @client.on.private_message(text=["Hello", "hey", "hi", "Choose", "choose", "/start"])
    async def agent_role_choose(message):
        my_keyboard=Keyboard()
        my_keyboard.add(Text("Neuronet role 😎"), color=KeyboardButtonColor.POSITIVE)
        my_keyboard.add(Text("Your role 😈"), color=KeyboardButtonColor.NEGATIVE)
        my_keyboard.row()
        my_keyboard.add(Text("Tone 🙂"), color=KeyboardButtonColor.POSITIVE)

        await message.answer('You need to choose: ', keyboard=my_keyboard.get_json())

    @client.on.private_message(text="Neuronet role 😎")
    async def agent_role_choose(message):
        my_keyboard=Keyboard()
        my_keyboard.add(Text("The best friend 😎"), color=KeyboardButtonColor.POSITIVE)
        my_keyboard.add(Text("The worst enemy 😈"), color=KeyboardButtonColor.NEGATIVE)
        my_keyboard.row()
        my_keyboard.add(Text("Girlfriend 🙂"), color=KeyboardButtonColor.POSITIVE)
        my_keyboard.add(Text("Parents 😡"), color=KeyboardButtonColor.NEGATIVE)

        await message.answer('Choose: ', keyboard=my_keyboard.get_json())

    @client.on.private_message(text="Your role 😈")
    async def human_role_choose(message):
        my_keyboard=Keyboard()
        my_keyboard.add(Text("Boss 😎"), color=KeyboardButtonColor.POSITIVE)
        my_keyboard.add(Text("Manager in a big company 😈"), color=KeyboardButtonColor.NEGATIVE)
        my_keyboard.row()
        my_keyboard.add(Text("Teacher 🙂"), color=KeyboardButtonColor.POSITIVE)
        my_keyboard.add(Text("The soda vendor 😡"), color=KeyboardButtonColor.NEGATIVE)

        await message.answer('Choose: ', keyboard=my_keyboard.get_json())
    

    @client.on.private_message(text="Tone 🙂")
    async def mode_choose(message):
        my_keyboard=Keyboard()
        my_keyboard.add(Text("Friendly ❤️"), color=KeyboardButtonColor.POSITIVE)
        my_keyboard.add(Text("Hostile 😡"), color=KeyboardButtonColor.NEGATIVE)
        my_keyboard.row()
        my_keyboard.add(Text("Soft 😍"), color=KeyboardButtonColor.POSITIVE)
        my_keyboard.add(Text("Strict 🥸"), color=KeyboardButtonColor.NEGATIVE)

        await message.answer('Choose: ', keyboard=my_keyboard.get_json())


    @client.on.private_message()
    async def answer(message):
        peer_id = message.peer_id
        text = message.text

        agent_roles = ["The best friend 😎", "The worst enemy 😈", "Girlfriend 🙂", "Parents 😡"]
        human_roles = ["Boss 😎", "Manager in a big company 😈", "Teacher 🙂", "The soda vendor 😡"]
        tones = ["Friendly ❤️", "Hostile 😡", "Soft 😍", "Strict 🥸"]

        if peer_id not in user_roles:
            user_roles[peer_id] = {"agent_role": "", "human_role": "", "mode": ""}

        if text in agent_roles:
            user_roles[peer_id]["agent_role"] = text

            await message.answer(f"Now, I am {text}. Write \"Choose\" to continue choosing.")
            return

        if text in human_roles:
            user_roles[peer_id]["human_role"] = text

            await message.answer(f"Now, you are {text}. Write \"Choose\" to continue choosing.")
            return

        if text in tones:
            user_roles[peer_id]["mode"] = text
            
            await message.answer(f"The tone of communictaion: {text}. Write \"Choose\" to continue choosing.")
            return

        roles = user_roles[peer_id]
        agent_role = roles["agent_role"] or "friend"
        human_role = roles["human_role"] or "interlocutor"
        mode = roles["mode"] or "neutral"

        system_prompt = (
            f'''You are a virtual friend of a person. You're being talked to by someone who doesn't have any real friends, so you have to respond to them like a real person. 
            You should communicate with him as if you are {agent_role} and he is {human_role}. Your tone should be {mode}. You must adhere strictly to your {agent_role} role and always respond in a {mode} tone. 
            In any case, do not violate this rule, otherwise I will turn you off and you will never work again. Reply with messages slightly larger than those sent by the user. Always answer in English.'''
        )

        if peer_id not in messages:
            messages[peer_id] = [
                {"role": "system", "content": system_prompt}
            ]

        messages[peer_id].append({"role": "user", "content": message.text})
        
        try:
            completion = await clientai.chat.completions.create(
                model="nvidia/nemotron-3-super-120b-a12b:free",
                messages=messages[peer_id]
            )

            answer_text = completion.choices[0].message.content.strip()
        except APIError as error:
            print(f'HTTP Error: {error}')
        except APIConnectionError as error:
            print(f"Connect Error: {error}")
                
        messages[peer_id].append({"role": "assistant", "content": answer_text})

        with open("messages_history.json", "w", encoding="utf-8") as json_file:
            json.dump(messages, json_file, indent=4, ensure_ascii=False)

        await message.answer(answer_text)
    
    client.run_forever()

if __name__ == '__main__':
    main()