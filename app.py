import streamlit as st
from utils import (
    generate_initial_plot_blocking, # For initial plot
    generate_continuation_stream,   # For continuations
    generate_comic_image,
    format_story_history
)
import os
import time
from dotenv import load_dotenv

load_dotenv()

# Define theme descriptions
THEME_DESCRIPTIONS = {
    "Final Destination": "Death has a plan — and your character is in its path. Each move by the user brings danger, but the AI must twist fate and keep them alive. Expect close calls, clever saves, and suspense at every step.",
    "Survival": "Nature shows no mercy. Your character is being hunted — not by a person, but by the world itself. From collapsing caves to monster ambushes, the AI launches life-threatening events. The user must fight to keep the story (and character) alive.",
    "Superhero Tale": "Behind every mask is a secret. Dive into the double life of a hero blessed (or cursed) with powers, fighting not just crime but personal battles. Supervillains rise. Cities fall. And one hero stands in the middle.",
    "Fantasy Adventure": "Step into a world where dragons fly, spells crackle in the air, and ancient maps lead to hidden realms. Magic pulses through every tree and stone — and your character is about to set foot on a quest that will test their courage, wits, and heart.",
    "Mystery": "Whispers in the dark. Clues in plain sight. Someone is hiding the truth — and your character is on the trail. In a world filled with riddles and red herrings, only sharp minds and sharper instincts will survive.",
    "Slice of Life": "Sometimes, the quietest moments say the most. Follow your character through life’s small joys, awkward stumbles, and deep connections. From classrooms to coffee shops, this is a story about being human — honest, funny, and real.",
    "Sci-Fi Journey": "Rocket through galaxies, hack into alien tech, and face decisions that shape the fate of civilizations. From abandoned space stations to worlds ruled by AIs, your character must navigate the future — one jump at a time."
}

# Initialize session state variables
if 'current_round' not in st.session_state:
    st.session_state.current_round = 0
if 'story_history' not in st.session_state:
    # Story history will now be a list of dictionaries
    # e.g., {'type': 'plot', 'content': '...'}
    #       {'type': 'user', 'character_name': 'John', 'content': '...'}
    #       {'type': 'ai', 'content': '...'}
    st.session_state.story_history = []
if 'image_urls' not in st.session_state:
    st.session_state.image_urls = []
if 'character' not in st.session_state:
    st.session_state.character = ""
if 'theme' not in st.session_state:
    st.session_state.theme = ""
if 'email' not in st.session_state:
    st.session_state.email = ""
if 'generating_ai_response' not in st.session_state: # Flag to manage AI response generation
    st.session_state.generating_ai_response = False

# Page config
st.set_page_config(page_title="AI Comic Story Creator", layout="wide")

# Custom CSS (remains the same as your current version)
st.markdown("""
<style>
    /* Modern theme colors */
    body {
        background-color: #f5f5f5 !important;
        color: #333333 !important;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #2563eb !important;
        font-weight: 600 !important;
    }
    /* Form inputs */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        color: #333333 !important;
        padding: 14px !important;
        border-radius: 10px !important;
        font-size: 18px !important;
        transition: all 0.3s ease !important;
    }
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
    }
    .stTextInput > div > label,
    .stSelectbox > div > label {
        font-size: 20px !important;
        color: #2563eb !important;
        margin-bottom: 12px !important;
        font-weight: 500 !important;
    }
    .theme-description {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        color: #333333 !important;
        padding: 16px !important;
        border-radius: 10px !important;
        margin-top: 12px !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
    }
    .stButton > button {
        background-color: #2563eb !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px 32px !important;
        font-size: 20px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        margin-top: 24px !important;
        width: 100% !important;
        max-width: 320px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        display: block !important;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1) !important;
    }
    .stButton > button:hover {
        background-color: #1d4ed8 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
        scale: 1.02 !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
        scale: 1 !important;
    }
    .stProgress > div > div > div > div {
        background-color: #64b5f6 !important;
    }
    [data-testid="column"]:nth-of-type(1) { width: 40% !important; }
    [data-testid="column"]:nth-of-type(2) { width: 60% !important; }
    .story-entry { margin-bottom: 15px; padding: 10px; border-radius: 8px; }
    .plot-entry { background-color: #e3f2fd; border-left: 5px solid #2196f3; }
    .user-entry { background-color: #e8f5e9; border-left: 5px solid #4caf50; }
    .ai-entry { background-color: #f3e5f5; border-left: 5px solid #9c27b0; }
    .story-entry h4 { margin-top: 0; }
</style>
""", unsafe_allow_html=True)

st.title("🎨 AI Comic Story Creator")
st.markdown("Create your own comic story with AI! Choose your character, theme, and guide the story!")

with st.sidebar:
    st.header("Story Setup")
    if st.session_state.character:
        st.markdown(f"**Character:** {st.session_state.character}")
    if st.session_state.theme:
        st.markdown(f"**Theme:** {st.session_state.theme}")
        st.markdown(f"**Description:** {THEME_DESCRIPTIONS[st.session_state.theme]}")
    if st.session_state.character and st.session_state.theme:
        st.markdown("---")
    
    st.subheader("Progress")
    progress_value = st.session_state.current_round / 10
    st.progress(progress_value)
    st.write(f"Round {st.session_state.current_round}/10")
    if st.session_state.current_round >= 10:
        st.balloons()




# --- Initial Story Setup (Round 0) ---
if st.session_state.current_round == 0:
    st.subheader("Start Your Story")
    col1_form, col2_form = st.columns(2)
    with col1_form:
        email = st.text_input("📧 Your Email:", key="email_input", placeholder="Enter your email address", value=st.session_state.email)
        character = st.text_input("👤 Character Name:", key="character_input", placeholder="E.g., Captain Astra, Detective Rex", value=st.session_state.character)
        theme = st.selectbox("🎨 Select Theme:", options=list(THEME_DESCRIPTIONS.keys()), key="theme_input", index=list(THEME_DESCRIPTIONS.keys()).index(st.session_state.theme) if st.session_state.theme else 0)

    with col2_form:
        if theme:
            st.markdown(f"""
            <div class="theme-description">
                <h4>{theme}</h4>
                <p><small>{THEME_DESCRIPTIONS[theme]}</small></p>
            </div>
            """, unsafe_allow_html=True)

    if st.button("✨ Create Story", help="Click to start your interactive story!"):
        if email and character and theme:
            st.session_state.email = email
            st.session_state.character = character
            st.session_state.theme = theme
            st.session_state.description = THEME_DESCRIPTIONS[theme]
            
            st.session_state.story_history = [] # Clear any previous history
            st.session_state.image_urls = []

            with st.spinner("⏳ Creating the story plot for you..."):
                initial_plot_content = generate_initial_plot_blocking(
                    st.session_state.character, 
                    st.session_state.theme,
                    st.session_state.description
                )
            
            if initial_plot_content:
                st.session_state.story_history.append({'type': 'plot', 'content': initial_plot_content})
            else:
                st.error("💥 Apologies! The AI couldn't generate the initial plot. Please try again.")
                # Optionally, prevent moving to next round if plot fails
                st.stop() # Stop further execution in this script run


            with st.spinner("🎨 Generating first comic panel..."):
                image_url = generate_comic_image(initial_plot_content)
                if image_url == "error_nsfw":
                    st.warning("🎨 The story opening was a bit too graphic for the image generator. No comic panel this time, but the story continues!")
                elif isinstance(image_url, str) and image_url.startswith("error_"):
                    st.error("😢 Oops! Couldn't generate the first comic panel due to a model error.")
                elif image_url: # Check if it's a valid URL (truthy string)
                    st.session_state.image_urls.append(image_url)
                else: # None or empty output from model
                    st.error("😢 Oops! Couldn't generate the first comic panel. The model returned no image.")
            
            st.session_state.current_round = 1
            st.experimental_rerun()
        else:
            st.error("❗ Please fill in all fields: Email, Character Name, and Theme.")

# --- Story Continuation (Rounds 1-10) ---
else:
    col1_story, col2_panels = st.columns([4,3]) # Adjusted column ratio

    with col1_story:
        st.subheader("📜 Story Progress")
        
        # Display story history from the structured list
        for i, entry in enumerate(st.session_state.story_history):
            if entry['type'] == 'plot':
                st.markdown(f"<div class='story-entry plot-entry'><h4>✨ Story Introduction ✨</h4><p>{entry['content']}</p></div>", unsafe_allow_html=True)
            elif entry['type'] == 'user':
                st.markdown(f"<div class='story-entry user-entry'><h4>👤 {entry['character_name']} Says:</h4><p>{entry['content']}</p></div>", unsafe_allow_html=True)
            elif entry['type'] == 'ai':
                st.markdown(f"<div class='story-entry ai-entry'><h4>🤖 AI Continues:</h4><p>{entry['content']}</p></div>", unsafe_allow_html=True)
            st.markdown("---") # Separator

        # User input area for next part of the story
        if st.session_state.current_round <= 10:
            if not st.session_state.generating_ai_response: # Only show input if not waiting for AI
                user_input = st.text_area(f"Round {st.session_state.current_round}/10: What does {st.session_state.character} do next?", key=f"user_input_round_{st.session_state.current_round}")
                
                if st.button("➡️ Continue Story", key=f"continue_btn_{st.session_state.current_round}"):
                    if user_input:
                        # Add user input to history
                        st.session_state.story_history.append({
                            'type': 'user',
                            'character_name': st.session_state.character,
                            'content': user_input
                        })
                        st.session_state.generating_ai_response = True # Set flag
                        st.experimental_rerun() # Rerun to show user input, then generate AI response
                    else:
                        st.warning("❗ Please tell us what happens next!")
            
            # AI Response and Image Generation (triggered after user input is added and rerun)
            if st.session_state.generating_ai_response and st.session_state.story_history[-1]['type'] == 'user':
                latest_user_input = st.session_state.story_history[-1]['content']
                history_for_prompt = format_story_history([item['content'] for item in st.session_state.story_history])
                ai_response_content = "" # Initialize

                try:
                    # --- AI Text Generation (in col1_story) ---
                    with col1_story:
                        st.markdown("**AI's Turn:**")
                        ai_response_placeholder = st.empty()
                        with st.spinner(f"✍️ AI is crafting the story's continuation (Round {st.session_state.current_round})..."):
                            ai_stream_gen = generate_continuation_stream(
                                history_for_prompt,
                                latest_user_input,
                                st.session_state.character,
                                st.session_state.theme,
                                st.session_state.description
                            )
                            full_response_chunks = []
                            for chunk in ai_stream_gen:
                                full_response_chunks.append(chunk)
                                ai_response_placeholder.markdown("".join(full_response_chunks) + "▌")
                            ai_response_content = "".join(full_response_chunks)
                            ai_response_placeholder.markdown(ai_response_content)
                        
                        if ai_response_content: # Check if AI generated something
                            st.session_state.story_history.append({'type': 'ai', 'content': ai_response_content})
                        else:
                            st.error("The AI didn't return a response this round. Please try continuing again.")
                            # Don't proceed to image generation or increment round if AI fails
                            st.session_state.generating_ai_response = False
                            st.experimental_rerun()
                            st.stop() # Stop further execution for this run
                        
                        # --- Image Generation (spinner in col1_story, image displayed in col2_panels) ---
                        if ai_response_content: # Only generate image if AI response was successful
                            with st.spinner(f"🎨 Visualizing your action for Round {st.session_state.current_round}... (Image will appear on the right)"):
                                image_url = generate_comic_image(latest_user_input)
                                if image_url == "error_nsfw":
                                    st.warning(f"🎨 Your action for Round {st.session_state.current_round} was a bit too graphic for the image generator. No panel, but the story goes on!")
                                elif isinstance(image_url, str) and image_url.startswith("error_"):
                                    st.error(f"😢 Oops! Couldn't generate the comic panel for Round {st.session_state.current_round} due to a model error.")
                                elif image_url:
                                    st.session_state.image_urls.append(image_url)
                                else:
                                    st.error(f"😢 Oops! Couldn't generate the comic panel for Round {st.session_state.current_round}. The model returned no image.")
                
                finally:
                    if ai_response_content: # Only increment round if AI was successful
                        st.session_state.current_round += 1
                    st.session_state.generating_ai_response = False # Reset flag
                    st.experimental_rerun() # Rerun to reflect all changes (text, image, round number)

        elif st.session_state.current_round > 10:
            st.success("🎉 Congratulations! Your 10-round comic story is complete!")
            st.markdown("You can review your story and comic panels.")
            # Placeholder for PDF generation and email
            if st.button("📜 Download Story as PDF (Coming Soon!)"):
                st.info("PDF generation feature is under development.")
            if st.button("🔄 Start a New Story"):
                # Clear all session state to reset the app
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.experimental_rerun()

    with col2_panels:
        st.subheader("🖼️ Comic Panels")
        if not st.session_state.image_urls:
            st.info("Your comic panels will appear here as the story unfolds!")
        
        for idx, img_url in enumerate(st.session_state.image_urls):
            if img_url:
                st.image(img_url, caption=f"Panel {idx + 1}", use_column_width=True)
            else:
                st.warning(f"😢 Panel {idx + 1} could not be generated.")
            st.markdown("---")
