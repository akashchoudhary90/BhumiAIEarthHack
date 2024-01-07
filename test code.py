import os
import dotenv
import streamlit as st
from openai import OpenAI
import pandas as pd
import json

# Load the OpenAI API key from environment variables or .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    dotenv.load_dotenv(".env")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
assistant_id = 'asst_tBGByeRx2D4dMri4mhh9qPR3'
thread_id = 'thread_vS5RYQrqySCdQa4G0RxCNmmF'

client = OpenAI()


df = pd.read_csv(r"D:\downloads\[PARTICIPANTS] AI EarthHack Resources-20240106T141616Z-001\[PARTICIPANTS] AI EarthHack Resources\AI EarthHack Dataset - Copy.csv", encoding='ISO-8859-1')

json_file_path = r"D:\downloads\[PARTICIPANTS] AI EarthHack Resources-20240106T141616Z-001\[PARTICIPANTS] AI EarthHack Resources\data.json"
data_json = df.to_json(json_file_path, orient='records', lines=True)

existing_assistant = client.beta.assistants.retrieve(assistant_id)

thread = client.beta.threads.retrieve(thread_id)

with open(json_file_path, 'r') as file:
    for line in file:
        json_object = json.loads(line)
        print(json_object)
        print(
            "-------------------------------------------------------------------------------------------------------------")
        print (json_object['id'])

        if json_object['id']:
            message = client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content="Evaluate the problem and solution idea" + json.dumps(json_object)
            )
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )
            while run.status != "completed":
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )  # you can retrieve the assistant's response when the status is "completed". This part is to make sure that the assistant has completed its response.

            messages = client.beta.threads.messages.list(thread_id=thread_id)
            assistant_response = messages.data[0].content[0].text.value
            print(assistant_response)

'''
# display chat history
for message in st.session_state.messages:  # this is to show the chat history
    if message["role"] == "assistant":
        st.chat_message("assistant").write(message["content"])
    else:
        st.chat_message("user").write(message["content"])

# chat input
if st.session_state['assistant']:
    if prompt := st.chat_input(placeholder="Enter your message here"):
        # st.write("prompt", prompt)

        user_message = {
            "role": "user",
            "content": prompt
        }

        # Add the user's response to the chat - frontend
        st.session_state.messages.append(user_message)
        # Add the user's response to the thread - backend
        message = client.beta.threads.messages.create(
            thread_id=st.session_state['thread'].id,
            role="user",
            content=prompt
          ) # you can add the user's message to the thread using the thread_id

        # display chat
        st.chat_message("user").write(prompt)  # this is to show the user's input

        with st.chat_message("assistant"):
            with st.spinner():
                # Run the assistant
                run = client.beta.threads.runs.create(
                  thread_id=st.session_state['thread'].id,
                  assistant_id=st.session_state['assistant'].id
                ) # after adding the user's message to the thread, you can run the assistant to get the assistant's response

                while run.status != "completed":
                    run = client.beta.threads.runs.retrieve(
                        thread_id=st.session_state['thread'].id,
                        run_id=run.id
                    ) # you can retrieve the assistant's response when the status is "completed". This part is to make sure that the assistant has completed its response.

                messages = client.beta.threads.messages.list(thread_id=st.session_state['thread'].id)
                assistant_response = messages.data[0].content[0].text.value # get the most recent message

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_response # messages are stored in the "data" key with the latest message at the first index
                    })
                st.write(assistant_response.replace("$", "\$")) # display the assistant's response
'''