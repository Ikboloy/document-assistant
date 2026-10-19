# Document Assistant · English & Korean

A PDF question-answering portfolio project by **Sobirova Ikboloy**, Computer Engineering graduate of Keimyung University.

Upload a text-based PDF, find relevant passages, and optionally generate an English or Korean answer with page references. The first version deliberately uses an inspectable character n-gram TF-IDF retrieval baseline rather than claiming semantic understanding.

## Features

- English and Korean interface and answer language selection
- Page-preserving text extraction and overlapping chunks
- Local source search without an API key
- Optional OpenAI Responses API generation, with sources visible beside the answer
- Page-reference validation: missing or out-of-context references withhold the AI answer
- Download original source pages as PDF and answers with evidence as JSON
- Session-scoped results survive download reruns; replacing/removing a document clears results
- Docker packaging and automated core/UI workflow tests

## Run locally

Python 3.12 recommended. From this project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate with `.venv\Scripts\activate` instead. Open the local URL printed by Streamlit. Upload a PDF and ask a question using words from its text. For AI answers, enter your own API key in the sidebar and enable generation. The default model is `gpt-4.1-mini`; change it to a model available to your account. API use has separate billing.

```bash
python -m unittest discover -s tests -v
docker build -t document-assistant .
docker run --rm -p 8501:8501 document-assistant
```

## Example walkthrough

1. Upload an English handbook containing “Applications close on October 30.”
2. Ask “When do applications close?”
3. Review the returned source passage and original page number.
4. Enable AI generation to receive a natural-language answer; choosing Korean controls the answer language.
5. Download the source PDF pages to inspect the original layout, or save the answer and excerpts as JSON. Exported pages follow original order; their original numbers are listed in the filename.

For Korean PDFs, try a question such as `신청 마감일은 언제인가요?`. These are illustrative examples, not measured benchmark results.

## Architecture

PDF → page text → overlapping chunks → character TF-IDF ranking → top four passages → optional LLM answer.

`core.py` owns extraction, retrieval and generation; `app.py` owns the bilingual Streamlit UI. Tests cover page provenance, English/Korean ranking, unreadable PDFs and the API request contract. API calls are mocked in tests.

## Privacy and limits

Uploads are processed in memory by the application, with no app-level file persistence. Search stays local. If AI generation is enabled, the question and retrieved excerpts are sent to OpenAI with `store=False`; this does not promise zero provider retention. Never commit API keys or private documents. Shared deployments need authentication and rate limiting before accepting sensitive files.

- Maximum 20 MB and 100 pages; encrypted or image-only PDFs are unsupported.
- Layout extraction, tables and mixed reading order may be imperfect.
- Retrieval is lexical, not semantic; cross-language search is not supported in this version.
- Similarity scores are not confidence probabilities. Any nonzero match can appear.
- Citations in `[p. N]` format are checked against retrieved page numbers. This checks reference membership only, not factual correctness or support for every claim. Missing citations (including uncited abstentions) withhold the response; sources remain visible.
- No claim of measured accuracy, production readiness or a live deployment.

## Next steps

Add multilingual embeddings with an evaluated English/Korean query set, OCR, claim-level evidence validation, and retrieval metrics before introducing agents or MCP into the application itself. GitHub MCP is used to publish this project; it is not a runtime feature of the app.

## References

- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Streamlit](https://docs.streamlit.io/)
- [pypdf](https://pypdf.readthedocs.io/)
- [scikit-learn TF-IDF](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)

## Validation of this update

Run `python -m unittest discover -s tests -v` from the repository root. Ten tests cover retrieval, real generated PDF extraction and source-page export, missing/unknown references, no-evidence provider bypass, JSON export, and Streamlit session/download workflows. UI workflows use Streamlit AppTest with a mocked uploader; provider responses are mocked. A live paid model call, browser visual review, and Docker execution were not performed for this update.
