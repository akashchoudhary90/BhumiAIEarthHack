import os
import dotenv
import streamlit as st
from openai import OpenAI
import pandas as pd
import json
import base64

# Load the OpenAI API key from environment variables or .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    dotenv.load_dotenv(".env")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def get_table_download_link(csv_data, filename, text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded"""
    # B64 encoding
    b64 = base64.b64encode(csv_data.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


def main():
    # Initialize session state variables if they don't exist
    if 'uploaded_button_clicked' not in st.session_state:
        st.session_state['uploaded_button_clicked'] = False

    if 'messages' not in st.session_state:
        st.session_state['messages'] = []

    if 'thread' not in st.session_state:
        st.session_state['thread'] = None

    if 'assistant' not in st.session_state:
        st.session_state['assistant'] = None

    client = OpenAI()

    uploaded_files = st.file_uploader("Please upload csv file containing sustainable ideas for evaluation.",
                                      type=["csv"],
                                      accept_multiple_files=True,
                                      label_visibility='visible')

    # Button to trigger the file upload process

    if len(uploaded_files) > 0:
        st.session_state['action'] = st.radio("Select an action", ("Create New Assistant (for training purpose)", "Connect to Existing Assistant (select this option to get ideas evaluated)"))
        if st.button('Proceed'):
            st.session_state['uploaded_button_clicked'] = True

    if st.session_state['uploaded_button_clicked']:
        if st.session_state['action'] == "Create New Assistant (for training purpose)":
            file_ids = []
            uploaded_logs = []
            st.session_state['proceed_button_clicked'] = True
            st.write("selected new assistant")
            with st.spinner('Uploading files'):
                for i, uploaded_file in enumerate(uploaded_files):
                    # Read the content of the uploaded file
                    # file_content = uploaded_file.getvalue()

                    # Detect encoding
                    # result = chardet.detect(file_content)
                    # encoding = result['encoding']

                    # Read the CSV file using the detected encoding
                    df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')

                    # Step 2: Convert the DataFrame to a JSON file
                    json_file_path = f'datat_{i}.json'
                    df.to_json(json_file_path, orient='records', lines=True)

                    # Upload the JSON file to OpenAI
                    with open(json_file_path, 'rb') as json_file:
                        oai_uploaded_file = client.files.create(
                            file=json_file,
                            purpose='assistants'
                        )
                    uploaded_log = {"file_name": uploaded_file.name, "file_id": oai_uploaded_file.id}
                    uploaded_logs.append(uploaded_log)
                    # st.write(uploaded_log)
                    file_ids.append(oai_uploaded_file.id)
                    # st.write(uploaded_logs)
            st.write(uploaded_logs)
            with st.spinner('Creating Assistant...'):
                # Add the file to the assistant
                # st.write("trying to create assistant")
                assistant = client.beta.assistants.create(
                    instructions=f"""
                    You are a helpful sustainability evaluator to question & answer over multiple files. Here\'s your file_id and file_name mapping:
                    As a sustainability evaluator, your have to assess innovative circular economy ideas. Your task involves rating each idea on a scale of 1 to 10, with the scores rounded to two decimal places, across various key criteria. These criteria include the stage of development (Maturity Stage), potential for market success (Market Potential), practicality of implementation (Feasibility), ability to expand or grow the idea (Scalability), level of technological innovation, adherence to circular economy principles, impact on communities (Community Impact), effectiveness in reducing carbon emissions (Carbon Footprint), waste reduction capabilities, and overall cost-efficiency (Cost-effectiveness).
                    After scoring each criterion, you are to calculate an overall score out of 100 for each idea. If an idea receives an overall score of below 60%, it should be considered for elimination from further consideration. Along with scoring, provide constructive feedback for each idea, pinpointing areas for improvement to enhance its sustainability and effectiveness. This feedback is crucial for guiding the refinement of ideas that have potential, ensuring they align closely with sustainable development goals.
                    """,  # instructions to the assistant to understand the context and purpose of the assistant
                    model="gpt-4-1106-preview",
                    tools=[{"type": "retrieval"}],  # augment with your own custom tools!
                    file_ids=file_ids
                )  # you need to pass the file_ids as a list when creating the assistant
                st.session_state['assistant'] = assistant

                st.write(st.session_state['assistant'])

                thread = client.beta.threads.create(
                    messages=st.session_state.messages
                )  # thread is a collection of messages between the user and the assistant

                st.write(thread)
                st.session_state['thread'] = thread
                # display chat history
            for message in st.session_state.messages:  # this is to show the chat history
                if message["role"] == "assistant":
                    st.chat_message("assistant").write(message["content"])
                else:
                    st.chat_message("user").write(message["content"])

            # chat input
            if st.session_state['assistant']:
                st.write("inside the assistant loop")
                if prompt := st.chat_input(placeholder="Enter your message here"):
                    st.write("prompt", prompt)

                    user_message = {
                        "role": "user",
                        "content": prompt
                    }

                    # Add the user's response to the chat - frontend
                    st.session_state.messages.append(user_message)
                    # Add the user's response to the thread - backend
                    st.write("messsage creation")
                    message = client.beta.threads.messages.create(
                        thread_id=st.session_state['thread'].id,
                        role="user",
                        content=prompt
                    )  # you can add the user's message to the thread using the thread_id

                    # display chat
                    st.chat_message("user").write(prompt)  # this is to show the user's input

                    with st.chat_message("assistant"):
                        with st.spinner():
                            # Run the assistant
                            run = client.beta.threads.runs.create(
                                thread_id=st.session_state['thread'].id,
                                assistant_id=st.session_state['assistant'].id
                            )  # after adding the user's message to the thread, you can run the assistant to get the assistant's response

                            while run.status != "completed":
                                run = client.beta.threads.runs.retrieve(
                                    thread_id=st.session_state['thread'].id,
                                    run_id=run.id
                                )  # you can retrieve the assistant's response when the status is "completed". This part is to make sure that the assistant has completed its response.

                            messages = client.beta.threads.messages.list(thread_id=st.session_state['thread'].id)
                            assistant_response = messages.data[0].content[
                                0].text.value  # get the most recent message

                            st.session_state.messages.append(
                                {
                                    "role": "assistant",
                                    "content": assistant_response
                                    # messages are stored in the "data" key with the latest message at the first index
                                })
                            st.write(assistant_response.replace("$", "\$"))  # display the assistant's response


        elif st.session_state['action'] == "Connect to Existing Assistant (select this option to get ideas evaluated)":
            file_ids = []
            uploaded_logs = []
            st.session_state['proceed_button_clicked'] = True
            st.write("selected existing assistant")
            st.session_state['uploaded_button_clicked'] = True
            json_array = []
            assistant_id = os.getenv("ASSISTANT_ID")
            existing_assistant = client.beta.assistants.retrieve(assistant_id)
            st.write(f"Connected to Assistant: {existing_assistant.id}")

            thread_id = os.getenv("THREAD_ID")
            thread = client.beta.threads.retrieve(thread_id)
            st.session_state['thread'] = thread
            st.session_state['assistant'] = existing_assistant
            with st.spinner('Evaluating ideas files'):
                for i, uploaded_file in enumerate(uploaded_files):
                    json_array = []
                    # Read the content of the uploaded file
                    # file_content = uploaded_file.getvalue()

                    # Detect encoding
                    # result = chardet.detect(file_content)
                    # encoding = result['encoding']

                    # Read the CSV file using the detected encoding
                    df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')

                    # Step 2: Convert the DataFrame to a JSON file
                    json_file_path = 'data.json'
                    data_json = df.to_json(json_file_path, orient='records', lines=True)

                    # Upload the JSON file to OpenAI
                    with open(json_file_path, 'rb') as json_file:
                        oai_uploaded_file = client.files.create(
                            file=json_file,
                            purpose='assistants'
                        )
                    uploaded_log = {"file_name": uploaded_file.name, "file_id": oai_uploaded_file.id}
                    uploaded_logs.append(uploaded_log)
                    # st.write(uploaded_log)
                    file_ids.append(oai_uploaded_file.id)

                    with open(json_file_path, 'r') as file:
                        for line in file:
                            json_object = json.loads(line)

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
                                json_array.append(assistant_response)


                                # Convert DataFrame to CSV
                    data = [json.loads(jstr) for jstr in json_array]
                    df = pd.DataFrame(data)
                    csv = df.to_csv( index=False)
                    # Display the download link in Streamlit
                    st.markdown(get_table_download_link(csv, "your_data.csv", "Download CSV file"),
                                unsafe_allow_html=True)

            # print("Response from the assistant:", response.choices[0].text.strip())

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
                    )  # you can add the user's message to the thread using the thread_id

                    # display chat
                    st.chat_message("user").write(prompt)  # this is to show the user's input

                    with st.chat_message("assistant"):
                        with st.spinner():
                            # Run the assistant
                            run = client.beta.threads.runs.create(
                                thread_id=st.session_state['thread'].id,
                                assistant_id=st.session_state['assistant'].id
                            )  # after adding the user's message to the thread, you can run the assistant to get the assistant's response

                            while run.status != "completed":
                                run = client.beta.threads.runs.retrieve(
                                    thread_id=st.session_state['thread'].id,
                                    run_id=run.id
                                )  # you can retrieve the assistant's response when the status is "completed". This part is to make sure that the assistant has completed its response.

                            messages = client.beta.threads.messages.list(thread_id=st.session_state['thread'].id)
                            assistant_response = messages.data[0].content[
                                0].text.value  # get the most recent message

                            st.session_state.messages.append(
                                {
                                    "role": "assistant",
                                    "content": assistant_response
                                    # messages are stored in the "data" key with the latest message at the first index
                                })
                            st.write(assistant_response.replace("$", "\$"))  # display the assistant's response
