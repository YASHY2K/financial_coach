import streamlit as st
import logging
import sys
from langchain_core.messages import HumanMessage

# --- Setup Logging ---
# Configure logging to print to the console (stdout)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("streamlit_app")

try:
    from src.agents.graph import graph

    logger.info("Successfully imported graph from src.agents")
except ImportError:
    from agents.graph import graph

    logger.info("Successfully imported graph from agents (fallback)")

st.set_page_config(page_title="Smart Financial Coach", layout="wide")
st.title("💸 Smart Financial Coach")
st.markdown("Ask me about your spending, subscriptions, or financial goals!")

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Main Chat Loop ---
if prompt := st.chat_input("How much did I spend on Coffee?"):
    # Log user input
    logger.info(f"User Input: {prompt}")

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")

        try:
            config = {"configurable": {"thread_id": "demo_session_1"}}
            inputs = {"messages": [HumanMessage(content=prompt)]}

            logger.info("Invoking AI Agent...")

            # --- Stream the response (Optional but better for logging) ---
            # Using invoke() is fine, but we log the result immediately after
            result = graph.invoke(inputs, config=config)

            # Log the raw result structure for debugging
            logger.debug(f"Graph Result: {result}")

            final_response = result["messages"][-1].content
            logger.info(f"AI Response generated (Length: {len(final_response)} chars)")

            message_placeholder.markdown(final_response)
            st.session_state.messages.append(
                {"role": "assistant", "content": final_response}
            )

        except Exception as e:
            # Log the full error traceback
            logger.error("Error during AI execution", exc_info=True)
            message_placeholder.error(f"An error occurred: {e}")
