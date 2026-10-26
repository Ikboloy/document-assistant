"""Optional catalog controls, kept separate from PDF retrieval."""
from uuid import uuid4
import streamlit as st
import catalog

def render_catalog(t, document=None, filename=None, language="en"):
    if not catalog.configured():
        return
    with st.expander(t("Saved document titles", "저장된 문서 제목")):
        st.caption(t(
            "Local single-user catalog. Save only the title and selected language; PDF contents, questions and answers are not stored. Up to 100 latest titles are shown.",
            "로컬 1인용 목록입니다. 제목과 선택한 언어만 저장하며 PDF 내용, 질문, 답변은 저장하지 않습니다. 최근 100개까지 표시합니다."))
        if document is not None:
            document.setdefault("catalog_id", str(uuid4()))
            with st.form("catalog_save"):
                title = st.text_input(t("Document title", "문서 제목"), value=filename or "", max_chars=200)
                consent = st.checkbox(t("Save this title to my local database", "이 제목을 로컬 데이터베이스에 저장"))
                save = st.form_submit_button(t("Save title", "제목 저장"))
            if save:
                if not consent:
                    st.warning(t("Select the checkbox to save.", "저장하려면 체크박스를 선택하세요."))
                else:
                    try:
                        catalog.save_title(title, language, document["catalog_id"])
                        st.success(t("Title saved.", "제목이 저장되었습니다."))
                    except catalog.CatalogError:
                        st.error(t("Could not save. Check the title and local database setup.", "저장하지 못했습니다. 제목과 로컬 데이터베이스 설정을 확인하세요."))
        try:
            rows = catalog.list_titles()
        except catalog.CatalogError:
            st.info(t("Catalog unavailable. Run local stack setup; PDF search still works.", "목록을 사용할 수 없습니다. 로컬 환경 설정을 실행하세요. PDF 검색은 계속 사용할 수 있습니다."))
            return
        if not rows:
            st.caption(t("No saved titles yet.", "저장된 제목이 없습니다."))
            return
        st.dataframe(rows, hide_index=True)
        labels = {r["id"]: f'{r["title"]} ({r["language"]}) · {r["id"][:8]}' for r in rows}
        with st.form("catalog_delete"):
            selected = st.selectbox(t("Title to delete", "삭제할 제목"), list(labels), format_func=labels.get)
            confirmed = st.checkbox(t("Permanently delete this catalog entry", "이 목록 항목을 영구 삭제"))
            delete = st.form_submit_button(t("Delete title", "제목 삭제"))
        if delete:
            if not confirmed:
                st.warning(t("Confirm deletion using the checkbox.", "체크박스로 삭제를 확인하세요."))
            else:
                try:
                    catalog.delete_title(selected)
                    st.rerun()
                except catalog.CatalogError:
                    st.error(t("Deletion failed. Please try again.", "삭제에 실패했습니다. 다시 시도하세요."))
