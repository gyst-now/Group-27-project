"""Local-only alternative: uv pip install streamlit; streamlit run app.py."""
import os
import httpx
import streamlit as st
st.title('University Catalog Advisor')
st.caption('UIUC 2026–2027 · Independent educational prototype, not an official advisor.')
question = st.chat_input('Ask about CS, MATH, or CS BS requirements')
if question:
    st.chat_message('user').write(question)
    try:
        with st.spinner('Searching catalog evidence…'):
            r = httpx.post(os.getenv('API_BASE_URL','http://localhost:8000')+'/api/chat', json={'question': question}, timeout=55)
            r.raise_for_status()
            result = r.json()
        st.chat_message('assistant').write(result['answer'])
        for citation in result['citations']:
            st.link_button(citation['title'], citation['url'])
            with st.expander('Evidence'):
                st.write(citation['excerpt'])
    except Exception:
        st.error('Catalog service unavailable. Check the backend configuration.')
