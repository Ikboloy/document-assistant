import os
import hashlib
import streamlit as st
from core import CitationError, answer, read_pdf, retrieve, source_pdf, export_report

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
if not uploaded:
    st.session_state.pop("document", None)
    st.session_state.pop("result", None)
if uploaded:
    data = uploaded.getvalue()
    digest = hashlib.sha256(data).hexdigest()
    try:
        if st.session_state.get("document", {}).get("digest") != digest:
            st.session_state.pop("result", None)
            st.session_state["document"] = {"digest": digest, "chunks": read_pdf(data)}
        chunks = st.session_state["document"]["chunks"]
    except Exception:
        st.error(t("Could not read this PDF. Use an unencrypted, text-based PDF within the size/page limits. Scanned PDFs require OCR.", "PDF를 읽을 수 없습니다. 용량/페이지 제한 이내의 암호화되지 않은 텍스트 PDF를 사용하세요. 스캔 PDF에는 OCR이 필요합니다."))
        st.stop()
    st.success(t(f"Ready: {len(chunks)} text chunks", f"준비 완료: 텍스트 조각 {len(chunks)}개"))
    with st.form("question"):
        question = st.text_input(t("Ask a question", "질문을 입력하세요"), max_chars=2000)
        submitted = st.form_submit_button(t("Find answer", "답변 찾기"))
    if submitted:
        st.session_state.pop("result", None)
        if question.strip():
            hits = retrieve(chunks, question)
            result = {"hits": hits, "question": question, "answer": None, "error": None}
            if hits and generate:
                if not key:
                    result["error"] = "key"
                else:
                    try:
                        from openai import OpenAI
                        with st.spinner(t("Reading evidence…", "근거를 확인하고 있습니다…")):
                            result["answer"] = answer(OpenAI(api_key=key, timeout=30, max_retries=1), model, question, hits, "Korean" if ko else "English")
                    except CitationError:
                        result["error"] = "citation"
                    except Exception:
                        result["error"] = "api"
            st.session_state["result"] = result
    result = st.session_state.get("result")
    if result:
        hits = result["hits"]
        st.write(t("Question: ", "질문: ") + result["question"])
        if not hits:
            st.info(t("No matching passages found. Try keywords from the PDF.", "일치하는 내용을 찾지 못했습니다. PDF에 있는 키워드로 검색해 보세요."))
        else:
            if result["error"] == "key":
                st.error(t("Enter an API key and submit again.", "API 키를 입력하고 다시 제출하세요."))
            elif result["error"] == "citation":
                st.warning(t("The AI response had missing or unsupported page references and was withheld. Review the sources or try again.", "AI 답변의 페이지 출처가 누락되었거나 유효하지 않아 표시하지 않았습니다. 출처를 확인하거나 다시 시도하세요."))
            elif result["error"] == "api":
                st.error(t("AI request failed. Check your key, model access, billing and connection. Sources remain available.", "AI 요청에 실패했습니다. API 키, 모델 접근, 결제 및 연결 상태를 확인하세요. 출처는 아래에서 확인할 수 있습니다."))
            if result["answer"]:
                st.subheader(t("Answer", "답변"))
                st.write(result["answer"])
                st.caption(t("Page references match retrieved pages. This does not verify factual correctness.", "페이지 출처가 검색된 페이지와 일치합니다. 답변의 사실 여부를 검증한 것은 아닙니다."))
            st.subheader(t("Source passages", "출처 내용"))
            pages = sorted({chunk.page for chunk, _ in hits})
            for chunk, score in hits:
                with st.expander(t(f"Page {chunk.page} · similarity {score:.2f}", f"{chunk.page}페이지 · 유사도 {score:.2f}"), expanded=True):
                    st.write(chunk.text)
            st.caption(t("Page numbers count from the first PDF page, including covers. Search matches wording in the same language; similarity is not confidence.", "페이지 번호는 표지부터 계산합니다. 같은 언어의 표현으로 검색하며, 유사도는 신뢰도가 아닙니다."))
            st.download_button(t("Download answer and sources (JSON)", "답변 및 출처 다운로드 (JSON)"), export_report(uploaded.name, result["question"], result["answer"], hits), file_name="document-answer.json", mime="application/json")
            try:
                st.download_button(t("Download source pages (PDF)", "출처 페이지 다운로드 (PDF)"), source_pdf(data, pages), file_name="source-pages-" + "-".join(map(str, pages)) + ".pdf", mime="application/pdf")
            except Exception:
                st.warning(t("Source PDF export failed. The passages above are still available.", "출처 PDF 내보내기에 실패했습니다. 위의 내용을 확인하세요."))
