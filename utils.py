import os
import replicate
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.callbacks.base import BaseCallbackHandler
from dotenv import load_dotenv
import threading
from queue import Queue, Empty
from typing import Any

# Custom Callback Handler to capture streamed tokens
class TokenStreamCallbackHandler(BaseCallbackHandler):
    def __init__(self, queue: Queue):
        super().__init__()
        self._queue = queue

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        self._queue.put(token)

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        self._queue.put(None)  # Signal end of stream

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        self._queue.put(None)  # Signal end of stream on error

# Wrapper to run LLMChain in a thread and yield tokens from the callback queue
def _create_chain_stream_generator(chain: LLMChain, inputs: dict, token_queue: Queue):
    def llm_thread_target():
        try:
            chain.run(inputs)
        except Exception:
            token_queue.put(None) # Ensure queue gets None on error in thread
            # Optionally re-raise or log error from thread
            # print(f"Error in LLM thread: {e}") 

    thread = threading.Thread(target=llm_thread_target)
    thread.start()

    while True:
        try:
            token = token_queue.get(timeout=0.1) # Small timeout to prevent blocking UI
            if token is None: # End of stream signal
                break
            yield token
        except Empty:
            # If queue is empty, check if thread is still alive
            if not thread.is_alive() and token_queue.empty():
                break # Thread finished and queue is empty
            continue # Continue polling if thread is alive or queue might still get items
    thread.join() # Ensure thread is cleaned up


load_dotenv()

def generate_initial_plot_stream(character, theme):
    """Generates the initial story plot as a stream of tokens using callbacks."""
    token_queue = Queue()
    llm = ChatOpenAI(
        temperature=0.7,
        streaming=True,
        callbacks=[TokenStreamCallbackHandler(token_queue)]
    )
    
    template = """You are a creative storyteller. Craft an intriguing opening for a comic story.
    The story features a character named {character} and revolves around the theme of {theme}.
    Introduce the setting and {character}, and hint at an impending event or challenge related to the {theme}.
    Keep the plot engaging and around 100-150 words.

    Story Opening:"""
    
    prompt = PromptTemplate(
        input_variables=["character", "theme"],
        template=template
    )
    story_chain = LLMChain(llm=llm, prompt=prompt)
    inputs = {"character": character, "theme": theme}
    
    return _create_chain_stream_generator(story_chain, inputs, token_queue)

def generate_continuation_stream(history_for_prompt, latest_user_input, character, theme):
    """Generates story continuation as a stream of tokens using callbacks."""
    token_queue = Queue()
    llm = ChatOpenAI(
        temperature=0.7,
        streaming=True,
        callbacks=[TokenStreamCallbackHandler(token_queue)]
    )
    
    template = """You are a creative storyteller. Continue the story based on the history and the main character's latest action.
    
    Story Background:
    - Main Character: {character}
    - Theme: {theme}
    
    Story So Far:
    {history_for_prompt}
    
    {character}'s Latest Action: {latest_user_input}
    
    Your Continuation (respond directly to {character}'s action, be creative, engaging, and keep it around 100-150 words):
    """
    
    prompt = PromptTemplate(
        input_variables=["character", "theme", "history_for_prompt", "latest_user_input"],
        template=template
    )
    story_chain = LLMChain(llm=llm, prompt=prompt)
    inputs = {
        "character": character,
        "theme": theme,
        "history_for_prompt": history_for_prompt,
        "latest_user_input": latest_user_input
    }
    
    return _create_chain_stream_generator(story_chain, inputs, token_queue)

def generate_comic_image(prompt):
    model = "iwasrobbed/sdxl-suspense:2717cb6a3d2505d13e1e05ba16cbfe188f86609b9060b785220d3c30cefe6242"
    
    # The new model might have different input parameters.
    # Based on your example, it primarily uses "prompt".
    # You might need to adjust this further based on the model's specific schema on Replicate.
    input_params = {
        "prompt": f"A comic panel in the style of TOK, depicting: {prompt}"
    }
    
    output = replicate.run(
        model,
        input=input_params
    )
    
    return output[0] if output else None

def format_story_history(history_list):
    """Formats the story history list into a single string for AI context."""
    # history_list contains [initial_plot, user_1_input, ai_1_response, user_2_input, ai_2_response, ...]
    # We want to join them into a coherent narrative flow.
    return "\n\n".join(history_list)
