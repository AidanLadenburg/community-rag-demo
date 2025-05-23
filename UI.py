import streamlit as st
from RAG import CareerAdviceRAG
import streamlit.components.v1 as components
import urllib.parse
import re

st.set_page_config(
    page_title="Community RAG demo",
    page_icon="",
    layout="wide"
)

if 'rag_system' not in st.session_state:
    st.session_state.rag_system = CareerAdviceRAG(st.secrets["PINECONE_API_KEY"], st.secrets["GOOGLE_API_KEY"])
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'pending_user_message' not in st.session_state:
    st.session_state.pending_user_message = None
if 'soundcloud_source' not in st.session_state:
    st.session_state.soundcloud_source = ""
if 'message' not in st.session_state:
    st.session_state.message = ""

def extract_timestamp(message):
    match = re.search(r"(\d{1,2}):(\d{2})", message)
    if match:
        minutes = int(match.group(1))
        seconds = int(match.group(2))
        return (minutes * 60 + seconds) * 1000  # milliseconds
    return 0
def generate_soundcloud_embed(share_url, seek_ms=0):
    """
    Converts a SoundCloud share link into an HTML embed iframe with optional seek time.
    """
    import urllib.parse
    encoded_url = urllib.parse.quote(share_url, safe='')
    embed_code = f"""
    <iframe id="sc-player" width="50%" height="166" scrolling="no" frameborder="no" allow="autoplay"
    src="https://w.soundcloud.com/player/?url={encoded_url}&color=%23ff5500&inverse=false&auto_play=false&show_user=true">
    </iframe>
    <script src="https://w.soundcloud.com/player/api.js"></script>
    <script>
        var iframeElement = document.getElementById('sc-player');
        var widget = SC.Widget(iframeElement);

        widget.bind(SC.Widget.Events.READY, function() {{
            widget.seekTo({seek_ms});
        }});
    </script>
    """
    return embed_code.strip()

st.markdown("""
<style>
body {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: sans-serif;
}
            
.chat-container {
    margin-bottom: 100px;
    padding-bottom: 20px;
}
.chat-message {
    display: inline-block;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    border-radius: 12px;
    font-size: 1rem;
    line-height: 1.4;
    max-width: 60%;
    word-wrap: break-word;
}
.chat-message.assistant {
    background-color: #3a3a3a;
    color: #ffffff;
}
.chat-message.user {
    background-color: #4a90e2;
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)


st.sidebar.title("Community RAG")
st.sidebar.markdown("Desc here")

with st.sidebar.expander("Your Information (Optional)"):
    student_name = st.text_input("Name")
    student_year = st.selectbox("Year", ["First Year", "Second Year", "Third Year", "Fourth Year", "Graduate"])
    current_major = st.text_input("Current Major/Field of Study")

if st.sidebar.button("Start New Conversation"):
    st.session_state.rag_system.clear_conversation()
    st.session_state.chat_history = []
    st.session_state.pending_user_message = None

st.title("Community RAG demo")
st.markdown("Description")

with st.container():
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for i, message in enumerate(st.session_state.chat_history):
        if message["role"] == "user":
            st.markdown(
                f'<div style="display: flex; justify-content: flex-end;">'
                f'<div class="chat-message user">{message["content"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div style="display: flex; justify-content: flex-start;">'
                f'<div class="chat-message assistant">{message["content"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            if i == len(st.session_state.chat_history) - 1 and st.session_state.soundcloud_source:
                seek_ms = st.session_state.get("timestamp_ms", 0)
                components.html(generate_soundcloud_embed(st.session_state.soundcloud_source, seek_ms=seek_ms), height=200)

    st.markdown('</div>', unsafe_allow_html=True)

user_input = st.chat_input("Type your message here:")
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.session_state.pending_user_message = user_input
    st.rerun()

if st.session_state.pending_user_message:
    with st.spinner("Getting insights from professionals..."):
        response, source, message = st.session_state.rag_system.generate_response(st.session_state.pending_user_message)
    timestamp_ms = extract_timestamp(message)

    st.session_state.chat_history.append({"role": "assistant", "content": response})
    st.session_state.soundcloud_source = source
    st.session_state.timestamp_ms = timestamp_ms  # store seek time
    st.session_state.pending_user_message = None
    st.rerun()
