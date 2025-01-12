import os
import base64
import streamlit as st
from transcriber import YouTubeTranscriber
from summarizer import TextSummarizer
from chatbot import ChatGPT

def get_audio_player_html(audio_path):
    """Generate HTML for a custom audio player with progress bar"""
    try:
        # Read audio file as bytes and encode to base64
        with open(audio_path, 'rb') as audio_file:
            audio_bytes = audio_file.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
        
        # HTML template for custom audio player
        audio_html = f'''
            <audio style="width: 100%; margin-top: 10px;" controls>
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                Your browser does not support the audio element.
            </audio>
        '''
        return audio_html
    except Exception as e:
        return None


# Streamlit application title
st.title("YouTube Video GPT")

# Create tabs for different stages
tab1, tab2, tab3 = st.tabs(["Transcription", "Summary", "Chat"])

# Initialize session state
if "transcription" not in st.session_state:
    st.session_state.transcription = None
if "detected_language" not in st.session_state:
    st.session_state.detected_language = None
if "summary" not in st.session_state:
    st.session_state.summary = None
if "transcript_api_key" not in st.session_state:
    st.session_state.transcript_api_key = ""
if "summary_api_key" not in st.session_state:
    st.session_state.summary_api_key = ""
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None
if "output_txt" not in st.session_state:
    st.session_state.output_txt = None
if "endpoint" not in st.session_state:
    st.session_state.endpoint = ""
if "deployment_id" not in st.session_state:
    st.session_state.deployment_id = ""
if "use_azure" not in st.session_state:
    st.session_state.use_azure = False
if "use_openai_whisper" not in st.session_state:
    st.session_state.use_openai_whisper = False
if "last_video_url" not in st.session_state:
    st.session_state.last_video_url = ""
if "chatgpt" not in st.session_state:
    st.session_state.chatgpt = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "system", "content": "You are a helpful AI assistant."}
    ]

# Sidebar configuration
st.sidebar.header("Configuration")

# API Key for Transcript
st.sidebar.text_input(
    "Enter your OpenAI API Key for Transcript:",
    type="password",
    key="transcript_api_key",
    help="This API Key is used for OpenAI Whisper API (Transcript)."
)

# API Key for Summary
st.sidebar.text_input(
    "Enter your OpenAI API Key for Summary:",
    type="password",
    key="summary_api_key",
    help="This API Key is used for summarization."
)

# Option to use Azure OpenAI
st.sidebar.checkbox("Use Azure OpenAI", key="use_azure")

if st.session_state.use_azure:
    st.sidebar.text_input("Enter Azure OpenAI Endpoint:", key="endpoint", help="The Azure OpenAI endpoint URL.")
    st.sidebar.text_input("Enter Azure Deployment ID:", key="deployment_id", help="The Azure OpenAI deployment ID.")
else:
    # Model selection only for non-Azure OpenAI
    model_options = ["gpt-3.5-turbo", "gpt-4", "gpt-4-0125-preview"]
    selected_model = st.sidebar.selectbox("Select GPT Model:", model_options, index=0, key="selected_model")

# Tab 1: Transcription
with tab1:
    st.header("Step 1: Generate Transcription")

    # Input field for YouTube video URL
    video_url = st.text_input("Enter YouTube video URL", key="video_url")

    # Option to use OpenAI Whisper
    st.checkbox("Use OpenAI Whisper for Transcription", value=False, key="use_openai_whisper")

    # Whisper model selection (only for local Whisper)
    model_size = st.selectbox(
        "Select Whisper model size (for local transcription only)",
        ["tiny", "base", "small", "medium", "large"],
        index=1,
        key="model_size",
        disabled=st.session_state.use_openai_whisper
    )

    # Language selection
    language_options = [
        "None (Auto-detect)", "English", "Chinese", "Spanish", "French", "German",
        "Japanese", "Korean", "Russian", "Portuguese", "Italian", "Arabic"
    ]
    selected_language = st.selectbox(
        "Select Language for Transcription", language_options, index=0, key="language"
    )

    # Option to keep downloaded audio file
    keep_audio = st.checkbox("Keep downloaded audio file", value=True, key="keep_audio")

    # Generate transcription button
    if st.button("Generate Transcription", key="generate_transcription"):
        if video_url.strip() == "":
            st.error("Please enter a valid YouTube video URL")
        else:
            try:
                # Save current video URL
                st.session_state.last_video_url = video_url

                # Initialize the transcriber
                if st.session_state.use_openai_whisper:
                    if st.session_state.transcript_api_key.strip() == "":
                        st.error("Please enter your OpenAI API Key for Transcript in the sidebar.")
                        raise ValueError("OpenAI API Key for Transcript is required for OpenAI Whisper.")
                    
                    transcriber = YouTubeTranscriber(
                        use_openai_api=True,
                        openai_api_key=st.session_state.transcript_api_key
                    )
                else:
                    transcriber = YouTubeTranscriber(model_size=model_size)

                st.info("Processing the video, please wait...")

                # Set the language to None if the user selects auto-detection
                language = None if selected_language == "None (Auto-detect)" else selected_language

                # Process the video to generate transcription
                transcription, output_txt, detected_language = transcriber.process_video(
                    url=video_url,
                    language=language,
                    keep_audio=keep_audio
                )

                # Save results to session state
                st.session_state.transcription = transcription
                st.session_state.detected_language = detected_language
                st.session_state.audio_file = output_txt.rsplit(".", 1)[0] + ".mp3"
                st.session_state.output_txt = output_txt

                st.success(f"Transcription completed! Detected language: {detected_language}")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # Display transcription and audio player if available
    if st.session_state.transcription:
        st.text_area("Transcription Text", st.session_state.transcription, height=300, key="transcription_area_1")
        
        if st.session_state.output_txt and os.path.exists(st.session_state.output_txt):
            st.download_button(
                label="Download Transcription",
                data=open(st.session_state.output_txt, 'rb').read(),
                file_name="transcription.txt",
                mime="text/plain"
            )
        
        if st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
            st.subheader("Audio Player")
            audio_html = get_audio_player_html(st.session_state.audio_file)
            if audio_html:
                st.markdown(audio_html, unsafe_allow_html=True)
                st.download_button(
                    label="Download Audio",
                    data=open(st.session_state.audio_file, 'rb').read(),
                    file_name="audio.mp3",
                    mime="audio/mp3"
                )

# Tab 2: Summary
with tab2:
    st.header("Step 2: Generate Summary")

    # Check if transcription is available
    if st.session_state.transcription:
        # Display transcription text
        st.text_area("Transcription Text", st.session_state.transcription, height=300, disabled=True, key="transcription_area_2")

        # Input field for custom prompt
        custom_prompt = st.text_input(
            "Enter a custom prompt for summarization (optional):",
            value=None,
            key="custom_prompt"
        )

        # Generate summary button
        if st.button("Generate Summary", key="generate_summary"):
            if st.session_state.summary_api_key.strip() == "":
                st.error("Please enter your OpenAI API Key for Summary in the sidebar.")
            elif st.session_state.use_azure and (not st.session_state.endpoint or not st.session_state.deployment_id):
                st.error("Please provide both Azure OpenAI Endpoint and Deployment ID in the sidebar.")
            else:
                try:
                    # Initialize the summarizer
                    if st.session_state.use_azure:
                        summarizer = TextSummarizer(
                            api_key=st.session_state.summary_api_key,
                            model=None,
                            azure=True,
                            endpoint=st.session_state.endpoint,
                            deployment_id=st.session_state.deployment_id
                        )
                    else:
                        summarizer = TextSummarizer(
                            api_key=st.session_state.summary_api_key,
                            model=selected_model
                        )

                    summary = summarizer.summarize(
                        st.session_state.transcription,
                        user_prompt=custom_prompt,
                        detected_language=st.session_state.detected_language,
                    )

                    # Save the summary to session state
                    st.session_state.summary = summary

                    # Display the summary in markdown
                    st.success("Summary generated successfully!")

                except Exception as e:
                    st.error(f"An error occurred while generating the summary: {str(e)}")

        # Display the summary if available
        if st.session_state.summary:
            st.markdown("### Summary (Markdown Format)")
            st.markdown(st.session_state.summary, unsafe_allow_html=True)

            # Add download button for summary
            st.download_button(
                label="Download Summary",
                data=st.session_state.summary,
                file_name="summary.md",
                mime="text/markdown"
            )
    else:
        st.warning("Please generate the transcription first in the 'Transcription' tab.")

# Tab 3: Chat
with tab3:
    st.header("Step 3: Chat with GPT")

    # Initialize/Reset ChatGPT
    if st.button("Initialize/Reset ChatGPT"):
        try:
            # Reinitialize ChatGPT
            chatgpt = ChatGPT(
                api_key=st.session_state.summary_api_key,
                model=selected_model if not st.session_state.use_azure else "gpt-3.5-turbo",
                azure=st.session_state.use_azure,
                endpoint=st.session_state.endpoint if st.session_state.use_azure else None,
                deployment_id=st.session_state.deployment_id if st.session_state.use_azure else None
            )
            st.session_state.chatgpt = chatgpt
            
            # Reset chat history while keeping the system message
            st.session_state.chat_history = [
                {"role": "system", "content": "You are a helpful AI assistant."}
            ]
            
            # Add context from transcript and summary if available
            if st.session_state.transcription:
                context_message = f"Context - Transcription: {st.session_state.transcription}"
                st.session_state.chat_history.append({"role": "system", "content": context_message})
            
            if st.session_state.summary:
                context_message = f"Context - Summary: {st.session_state.summary}"
                st.session_state.chat_history.append({"role": "system", "content": context_message})
            
            st.success("ChatGPT reset successfully!")
        except Exception as e:
            st.error(f"Reset failed: {str(e)}")

    # Chat interface
    if st.session_state.chatgpt:
        # Create a container with fixed height for chat messages
        chat_container = st.container(height=600)

        # Display chat history
        for message in st.session_state.chat_history[-20:]:
            role = message["role"]
            # Only display non-system messages
            if role != "system":
                with chat_container.chat_message(role):
                    st.write(message["content"])

        # Chat input at the bottom
        chat_input = st.chat_input("Type your message here")
        if chat_input:
            st.session_state.chat_history.append({"role": "user", "content": chat_input})
            try:
                response = st.session_state.chatgpt.chat(
                    st.session_state.chat_history,
                    transcription=st.session_state.transcription,
                    summary=st.session_state.summary
                )
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()  # Rerun to update the chat history
            except Exception as e:
                st.error(f"Error during chat: {str(e)}")