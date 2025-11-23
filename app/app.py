import os
import json
import uuid
import time
import threading
import streamlit as st
import requests

# -------- CONFIG ----------
BACKEND_URL = os.getenv("COURSETA_BACKEND", "http://127.0.0.1:8000")  # FastAPI base URL
DEMO_USER = os.getenv("COURSETA_USER", "educator")
DEMO_PASS = os.getenv("COURSETA_PASS", "password123")

# Endpoints
PREPROCESS = f"{BACKEND_URL}/Preprocess"
SUMMARIZE = f"{BACKEND_URL}/summarize/Summary"
QUESTION_GENERATE = f"{BACKEND_URL}/questions/generate_QA"
QUESTION_REFINE = f"{BACKEND_URL}/questions/refine"
QUESTION_APPROVE = f"{BACKEND_URL}/questions/approve"
QA_INGEST = f"{BACKEND_URL}/qa/ingest"
QA_ASK = f"{BACKEND_URL}/qa/ask"

# -------- HELPERS ----------
def api_post(url: str, json_data=None, files=None, params=None):
    try:
        if files:
            r = requests.post(url, files=files)
        else:
            r = requests.post(url, json=json_data, params=params)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API request failed: {e}")
        return None


# Session state init
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "texts" not in st.session_state:
    # store list of {id, source, text}
    st.session_state.texts = []
if "summaries" not in st.session_state:
    st.session_state.summaries = {}  # local map id->summary
if "questions" not in st.session_state:
    st.session_state.questions = {}  # id -> question dict
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -------- AUTH ----------
def show_login():
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Log in"):
        if username == DEMO_USER and password == DEMO_PASS:
            st.session_state.logged_in = True
            st.session_state.user = username
            st.sidebar.success("Logged in")
        else:
            st.sidebar.error("Invalid credentials (demo)")

def logout():
    st.session_state.logged_in = False
    st.session_state.user = None

# Main UI
st.title("J.A.R.V.I.S — Educational Assistant")

if not st.session_state.logged_in:
    show_login()
    st.stop()
else:
    st.sidebar.success(f"Signed in as {st.session_state.user}")
    if st.sidebar.button("Log out"):
        logout()

tabs = st.tabs(["Upload Materials", "Summaries / TOC", "Questions (Generate & Refine)", "Q&A Chat"])

# -------- Tab 1: Upload ----------
with tabs[0]:
    st.header("Upload Materials")
    st.write("Upload PDF, audio or video. The backend will preprocess (transcribe / extract) and return clean text.")

    uploaded = st.file_uploader("Upload file", type=["pdf","mp3","wav","m4a","mp4","avi","mov","mkv"])
    if uploaded:
        st.info(f"File uploaded: {uploaded.name} ({uploaded.type})")
        endpoint = PREPROCESS

        if not endpoint:
            st.error("Unsupported file type")
        else:
            if st.button("Send to preprocess"):
                files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}

                progress_bar = st.progress(0)
                status_placeholder = st.empty()

                # Shared container for response and a completion event
                resp_container = {"resp": None}
                done_event = threading.Event()

                def run_request():
                    try:
                        # perform the blocking API call in background
                        resp_container["resp"] = api_post(endpoint, files=files)
                    finally:
                        # signal that the request is done (success or error)
                        done_event.set()

                # start background thread
                worker = threading.Thread(target=run_request, daemon=True)
                worker.start()

                # animate progress until the worker completes
                pct = 0
                while not done_event.is_set():
                    progress_bar.progress(pct)
                    status_placeholder.text(f"Processing... {pct}%")
                    time.sleep(3)            # smooth animation interval
                    # increase pct but cap below 100 so it finishes only after real response
                    pct = pct + 2 if pct < 90 else 90

                # finalize
                progress_bar.progress(100)
                status_placeholder.text("Processing complete ✅")

                resp = resp_container["resp"]
                if resp:
                    sid = str(uuid.uuid4())
                    st.session_state.texts.insert(0, {
                        "id": sid,
                        "source": resp.get("source", uploaded.name),
                        "text": resp.get("text", "")
                    })
                    st.success("Preprocessing complete — text stored in session")
                    st.write("Preview (first 1000 chars):")
                    st.code(resp.get("text", "")[:1000])
                else:
                    st.error("Preprocessing failed (check backend logs).")
    if st.session_state.texts:
        st.markdown("**Previously uploaded / preprocessed texts (session)**")
        for t in st.session_state.texts[:5]:
            st.write(f"- {t['source']} (id: {t['id']})")

# -------- Tab 2: Summaries ----------
with tabs[1]:
    st.header("Summarize Text / Generate TOC")
    st.write("Choose a preprocessed text or paste text, then create extractive + abstractive summary.")

    col1, col2 = st.columns([2,1])
    with col1:
        choice = st.selectbox("Select text", ["-- paste new text --"] + [f"{t['source']} ({t['id']})" for t in st.session_state.texts])
        pasted = st.text_area("Or paste text here (overrides selection)", height=200)
    with col2:
        toc_levels = st.number_input("TOC levels", min_value=1, max_value=4, value=2)
        n_sentences = st.number_input("Extractive sentences", min_value=1, max_value=20, value=8)
        abstractive_style = st.selectbox("Abstract style", ["concise","detailed","student_friendly"])
        FeedBack = st.text_area("FeedBack For the Summary (ex..'Make the summary shorter')", height=80, value="")

    if st.button("Generate summary"):
        if pasted.strip():
            txt = pasted
            source = "pasted_text"
        elif choice.startswith("--"):
            st.error("Please paste text or select a text")
            txt = None
        else:
            # find by id
            sel_id = choice.split("(")[-1].strip(")")
            t = next((x for x in st.session_state.texts if x["id"] == sel_id), None)
            if not t:
                st.error("Text not found in session")
                txt = None
            else:
                txt = t["text"]
                source = t["source"]

        if txt:
            payload = {
                "source": source,
                "text": txt,
                "toc_levels": int(toc_levels),
                "extractive_sentences": int(n_sentences),
                "abstractive_style": abstractive_style,
                "comments": FeedBack
            }

            progress_bar = st.progress(0)
            status_placeholder = st.empty()

            resp_container = {"resp": None}
            done_event = threading.Event()

            def run_request():
                try:
                    resp_container["resp"] = api_post(SUMMARIZE, json_data=payload)
                finally:
                    done_event.set()

            worker = threading.Thread(target=run_request, daemon=True)
            worker.start()

            pct = 0
            while not done_event.is_set():
                progress_bar.progress(pct)
                status_placeholder.text(f"Summarizing... {pct}%")
                time.sleep(3)
                pct = pct + 1 if pct < 95 else 95

            progress_bar.progress(100)
            status_placeholder.text("Summary complete ✅")

            resp = resp_container["resp"]
            if resp:
                sid = str(uuid.uuid4())
                st.session_state.summaries[sid] = {
                    "id": sid,
                    "source": source,
                    "toc": resp.get("toc", []),
                    "extractive": resp.get("extractive", []),
                    "abstract": resp.get("abstract_summary", ""),
                    "comments": resp.get("comments", "")
                }
                st.success("Summary generated (stored in session)")

                st.subheader("Table of Contents")
                for i, item in enumerate(resp.get("toc", []), 1):
                    st.write(f"{i}. {item.get('title')} — {item.get('hint','')}")

                st.subheader("Extractive Key Points")
                for b in resp.get("extractive", []):
                    st.write(f"- {b}")

                st.subheader("Additional Comments from the user")
                st.write(resp.get("comments", ""))

                st.subheader("Abstractive Summary")
                st.write(resp.get("abstract_summary", ""))
            else:
                st.error("Summary request failed (check backend logs).")
    if st.session_state.summaries:
        st.markdown("**Local summaries (session)**")
        for sid, s in list(st.session_state.summaries.items())[-5:]:
            with st.expander(f"{s['source']} — {sid}"):
                st.write("**Abstract**")
                st.write(s["abstract"][:1000])
                if st.button("Export summary as JSON", key=f"exp_{sid}"):
                    st.download_button(label="Download JSON", data=json.dumps(s, ensure_ascii=False, indent=2), file_name=f"summary_{sid}.json")

# -------- Tab 3: Questions ----------
with tabs[2]:
    st.header("Generate & Refine Questions")
    st.write("Choose a preprocessed text or paste text; the backend will return MCQ and True/False with IDs.")

    q_choice = st.selectbox("Select text for question generation", ["-- paste new text --"] + [f"{t['source']} ({t['id']})" for t in st.session_state.texts])
    q_pasted = st.text_area("Or paste text here", height=150)
    n_questions = st.number_input("Number of Questions", min_value=0, max_value=20, value=3)
    Q_type = st.selectbox("Question type", ["mcq", "tf"])
    difficulty = st.slider("Target difficulty (1-5)", 1, 5, 2)

    if st.button("Generate questions"):
        if q_pasted.strip():
            txt = q_pasted
            src = "pasted_text"
        elif q_choice.startswith("--"):
            st.error("Please paste or select a text")
            txt = None
        else:
            sel_id = q_choice.split("(")[-1].strip(")")
            t = next((x for x in st.session_state.texts if x["id"] == sel_id), None)
            if not t:
                st.error("Text not found")
                txt = None
            else:
                txt = t["text"]
                src = t["source"]

        if txt:
            payload = {"text": txt, "source": src, "n_questions": int(n_questions), "difficulty": int(difficulty), "Q_type": Q_type}

            # progress placeholders
            progress_bar = st.progress(0)
            status_placeholder = st.empty()
            done_event = threading.Event()

            result_holder = {"resp": None}  # ✅ mutable dict instead of nonlocal

            def run_request():
                try:
                    result_holder["resp"] = api_post(QUESTION_GENERATE, json_data=payload)
                finally:
                    done_event.set()

            threading.Thread(target=run_request).start()

            # update progress while waiting
            pct = 0
            while not done_event.is_set():
                progress_bar.progress(pct)
                status_placeholder.text(f"Generating questions... {pct}%")
                time.sleep(3)       # slower updates
                pct = pct + 1 if pct < 95 else 95

            done_event.wait()
            progress_bar.progress(100)
            status_placeholder.text("Done ✅")

            resp = result_holder["resp"]  # ✅ get it back safely
            if resp:
                for q in resp:
                    st.session_state.questions[q["id"]] = q
                st.success(f"Generated {len(resp)} questions and stored in session")

    # show existing questions
    if st.session_state.questions:
        st.subheader("Generated Questions")
        for qid, q in list(st.session_state.questions.items())[-10:]:
            with st.expander(f"[{q['type'].upper()}] {q['question']}"):
                st.write(f"Difficulty: {q.get('difficulty')}")
                if q.get("options"):
                    for opt in q["options"]:
                        st.write(f" - ({opt['id']}) {opt['option']}")
                st.write(f"Answer: {q.get('answer')}")
                st.write("Rationale:")
                st.write(q.get("rationale", ""))
# -------- Tab 4: Q&A ----------
with tabs[3]:
    st.header("Q&A Chat")

    st.write("Chose from preprocessed texts or paste new text, you MUST press Ingest chunk then you can ask questions grounded in the course materials.")

    ingest_choice = st.selectbox("Ingest source", ["-- paste new chunk --"] + [f"{t['source']} ({t['id']})" for t in st.session_state.texts])
    chunk_text = st.text_area("Chunk text to ingest (overrides selection)", height=150)
    
    if st.button("Ingest chunk"):
        if chunk_text.strip():
            docs = [{"id": str(uuid.uuid4()), "text": chunk_text, "source": "pasted_chunk"}]
        elif ingest_choice.startswith("--"):
            st.error("Select or paste a chunk")
            docs = []
        else:
            sel_id = ingest_choice.split("(")[-1].strip(")")
            t = next((x for x in st.session_state.texts if x["id"] == sel_id), None)
            docs = [{"id": str(uuid.uuid4()), "text": t["text"], "source": t["source"]}] if t else []
        
        if docs:
            payload = {"docs": docs}

            # progress placeholders
            progress_bar = st.progress(0)
            status_placeholder = st.empty()
            done_event = threading.Event()
            result_holder = {"resp": None}

            def run_request():
                try:
                    result_holder["resp"] = api_post(QA_INGEST, json_data=payload)
                finally:
                    done_event.set()

            threading.Thread(target=run_request).start()

            pct = 0
            while not done_event.is_set():
                progress_bar.progress(pct)
                status_placeholder.text(f"Ingesting docs... {pct}%")
                time.sleep(2)
                pct = pct + 2 if pct < 95 else 95

            done_event.wait()
            progress_bar.progress(100)
            status_placeholder.text("Done ✅")

            res = result_holder["resp"]
            if res:
                st.success(f"Ingested docs: {res.get('added')} (index size: {res.get('index_size')})")

    st.subheader("Ask a question")
    q_input = st.text_input("Your question")
    if st.button("Ask"):
        if not q_input.strip():
            st.error("Enter a question")
        else:
            payload = {"query": q_input, "chat_history": st.session_state.chat_history, "k": 5}

            # progress placeholders
            progress_bar = st.progress(0)
            status_placeholder = st.empty()
            done_event = threading.Event()
            result_holder = {"resp": None}

            def run_request():
                try:
                    result_holder["resp"] = api_post(QA_ASK, json_data=payload)
                finally:
                    done_event.set()

            threading.Thread(target=run_request).start()

            pct = 0
            while not done_event.is_set():
                progress_bar.progress(pct)
                status_placeholder.text(f"Asking... {pct}%")
                time.sleep(3)
                pct = pct + 2 if pct < 95 else 95

            done_event.wait()
            progress_bar.progress(100)
            status_placeholder.text("Done ✅")

            res = result_holder["resp"]
            if res:
                if not res.get("on_topic"):
                    st.warning(res.get("redirect"))
                else:
                    st.markdown("**Answer:**")
                    st.write(res.get("answer"))
                    st.markdown("**Sources:**")
                    for s in res.get("sources", []):
                        st.write(f"- {s}")
                    st.session_state.chat_history.append({"role":"user","content": q_input})
                    st.session_state.chat_history.append({"role":"assistant","content": res.get("answer", "")})

st.sidebar.markdown("---")
st.sidebar.write("J.A.R.V.I.S — Educational Assistant")
