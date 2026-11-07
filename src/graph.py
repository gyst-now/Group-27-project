import json
import logging
import re
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import Settings, URLS
from src.external import build_external_answer
from src.schemas import GroundedAnswer
from src.prompts import SYSTEM
from src.vectorstore import VectorStore

NO_EVIDENCE = 'The selected UIUC 2026–27 catalog sources cannot establish that answer. Please clarify the course subject and number, or consult an official academic advisor for information outside this catalog.'

class State(TypedDict, total=False):
    question: str
    passages: list[dict]
    supported: bool
    answer: str
    citations: list[dict]
    status: str
    selected: list[str]
    clarification: str


def build_graph(store, embedder, model, external_answer=None):
    def retrieve(state):
        question = state['question']
        if (re.search(r'\b\d{3}\b', question)
                and re.search(r'\b(?:prerequisites?|course|class)\b', question, re.I)
                and not re.search(r'\b(?:CS|MATH)\b', question, re.I)):
            return {'passages': [], 'clarification': 'Which subject do you mean—for example, CS 225 or MATH 225? Please include the subject and course number.'}
        passages = store.search(embedder.embed_query(state['question']), state['question'])
        topic_match = re.search(r'\b(?:cover|covers|discuss|teach|teaches)\s+(.+?)[?.]?$', question, re.I)
        if topic_match:
            topic = topic_match[1].strip(' ?.').lower()
            def prerequisite_only(passage):
                description, separator, prerequisites = passage['content'].partition('Prerequisite:')
                return bool(separator and topic in prerequisites.lower() and topic not in description.lower())
            passages = [p for p in passages if not prerequisite_only(p)]
        return {'passages': [p for p in passages if p.get('source_url') in URLS]}

    def assess(state):
        if not state['passages']:
            return {'supported': False}
        evidence = [{k: p.get(k) for k in ('id', 'content', 'heading', 'course_code')} for p in state['passages']]
        decision = model.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=json.dumps({'question': state['question'], 'evidence': evidence}))])
        selected = list(dict.fromkeys(decision.evidence_ids))
        valid = {p['id'] for p in state['passages']}
        supported = decision.supported and bool(selected) and set(selected) <= valid and bool(decision.answer.strip())
        return {'supported': supported, 'answer': decision.answer, 'selected': selected}

    def answer(state):
        by_id = {p['id']: p for p in state['passages']}
        citations = []
        for index, key in enumerate(state['selected'], 1):
            p = by_id[key]
            citations.append(dict(label=f'[{index}]', title=p.get('heading') or 'UIUC catalog',
                url=p['source_url'], course_code=p.get('course_code'), excerpt=p['content']))
        return {'status': 'answered', 'citations': citations}

    def insufficient(state):
        if external_answer and not state.get('clarification'):
            try:
                result = external_answer(state['question'])
                if result['answer'] and result['citations']:
                    return result
                return {'status': 'insufficient_evidence',
                        'answer': 'I could not verify an answer from external sources. Try specifying the occupation, region, or time period.',
                        'citations': []}
            except Exception as exc:
                logging.getLogger(__name__).warning('External research failed: %s', type(exc).__name__)
                return {'status': 'insufficient_evidence',
                        'answer': 'The catalog does not cover this question, and external research is temporarily unavailable.',
                        'citations': []}
        return {'status': 'insufficient_evidence', 'answer': state.get('clarification', NO_EVIDENCE), 'citations': []}

    graph = StateGraph(State)
    graph.add_node('retrieve_catalog', retrieve)
    graph.add_node('assess_evidence', assess)
    graph.add_node('generate_grounded_answer', answer)
    graph.add_node('insufficient_evidence', insufficient)
    graph.add_edge(START, 'retrieve_catalog')
    graph.add_edge('retrieve_catalog', 'assess_evidence')
    graph.add_conditional_edges('assess_evidence', lambda s: 'generate_grounded_answer' if s['supported'] else 'insufficient_evidence')
    graph.add_edge('generate_grounded_answer', END)
    graph.add_edge('insufficient_evidence', END)
    return graph.compile()


def production_graph():
    s = Settings.load()
    embedder = OpenAIEmbeddings(model='text-embedding-3-small', dimensions=1536, api_key=s.openai_key, request_timeout=15, max_retries=1)
    model = ChatOpenAI(model=s.model, api_key=s.openai_key, timeout=20, max_retries=1, temperature=0, max_tokens=1000).with_structured_output(GroundedAnswer)
    return build_graph(VectorStore(s), embedder, model, build_external_answer(s))
