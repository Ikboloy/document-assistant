import os
import streamlit as st
from core import answer, read_pdf, retrieve

st.set_page_config(page_title="Document Assistant", page_icon="📄", layout="wide")
language = st.sidebar.selectbox("Language / 언어", ["English", "한국어"])
ko = language == "한국어"
def t(en, kr):
    return kr if ko else en

st.title(t("📄 Document Assistant", "📄 문서 도우미"))
st.caption(t("Find answers in your PDF, with page references.", "PDF에서 답변을 찾고 출처 페이지를 확인하세요."))
st.sidebar.info(t("Search works without an API key. AI answers require your own OpenAI API key.", "검색은 API 키 없이 가능합니다. AI 답변에는 OpenAI API 키가 필요합니다."))
key = st.sidebar.text_input("OpenAI API key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
model = st.sidebar.text_input("Model", value=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
generate = st.sidebar.checkbox(t("Generate AI answer", "AI 답변 생성"), value=False)
if generate:
    st.warning(t("Retrieved PDF excerpts and your question will be sent to OpenAI when you submit. Do not upload confidential documents.", "제출 시 검색된 PDF 내용과 질문이 OpenAI로 전송됩니다. 기밀 문서를 업로드하지 마세요."))
uploaded = st.file_uploader(t("Upload a text-based PDF (20 MB / 100 pages max)", "텍스트 PDF 업로드 (최대 20 MB / 100페이지)"), type=["pdf"])
if uploaded:
    try:
        chunks = read_pdf(uploaded.getvalue())
    except Exception:
        st.error(t("Could not read this PDF. Use an unencrypted, text-based PDF within the size/page limits. Scanned PDFs require OCR.", "PDF를 읽을 수 없습니다. 용량/페이지 제한 이내의 암호화되지 않은 텍스트 PDF를 사용하세요. 스캔 PDF에는 OCR이 필요합니다."))
        st.stop()
    st.success(t(f"Ready: {len(chunks)} text chunks", f"준비 완료: 텍스트 조각 {len(chunks)}개"))
    with st.form("question"):
        question = st.text_input(t("Ask a question", "질문을 입력하세요"), max_chars=2000)
        submitted = st.form_submit_button(t("Find answer", "답변 찾기"))
    if submitted and question.strip():
        hits = retrieve(chunks, question)
        if not hits:
            st.info(t("No matching passages found. Try keywords from the PDF.", "일치하는 내용을 찾지 못했습니다. PDF에 있는 키워드로 검색해 보세요."))
        else:
            st.caption(t("Keyword baseline: use the same language as the document. Cross-language retrieval is not included yet.", "키워드 기반 검색: 문서와 같은 언어로 질문하세요. 언어 간 검색은 아직 지원하지 않습니다."))
            if generate:
                if not key:
                    st.error(t("Enter an API key to generate an answer.", "답변 생성을 위해 API 키를 입력하세요."))
                else:
                    try:
                        from openai import OpenAI
                        with st.spinner(t("Reading evidence…", "근거를 확인하고 있습니다…")):
                            st.write(answer(OpenAI(api_key=key, timeout=30, max_retries=1), model, question, hits, "Korean" if ko else "English"))
                    except Exception:
                        st.error(t("AI request failed. Check your key, model access, billing and connection. Sources are still available below.", "AI 요청에 실패했습니다. API 키, 모델 접근, 결제 및 연결 상태를 확인하세요. 출처는 아래에서 확인할 수 있습니다."))
            st.subheader(t("Source passages", "출처 내용"))
            for chunk, score in hits:
                with st.expander(t(f"Page {chunk.page} · similarity {score:.2f}", f"{chunk.page}페이지 · 유사도 {score:.2f}"), expanded=True):
                    st.write(chunk.text)
            st.caption(t("Similarity is not a confidence score. Verify AI answers against the passages.", "유사도는 답변 신뢰도 점수가 아닙니다. AI 답변을 출처와 비교하여 확인하세요."))
