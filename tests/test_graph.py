from src.graph import build_graph
from src.schemas import GroundedAnswer
from src.config import URLS
class Store:
    def __init__(self, passages): self.passages=passages
    def search(self,*args): return self.passages
class Embed:
    def embed_query(self,q): return [1.0]
class Model:
    def __init__(self, ids, supported=True): self.ids=ids; self.supported=supported
    def invoke(self,*args): return GroundedAnswer(supported=self.supported,answer='CS 225 is Data Structures.',evidence_ids=self.ids)
PASSAGE={'id':'a','content':'CS 225 Data Structures','source_url':URLS[0],'heading':'CS 225','course_code':'CS 225'}
def run(passages, ids, supported=True):
    return build_graph(Store(passages),Embed(),Model(ids,supported)).invoke({'question':'What is CS 225?'})
def test_supported():
    r=run([PASSAGE],['a']); assert r['status']=='answered'; assert r['citations'][0]['url']==URLS[0]
def test_empty(): assert run([],[])['status']=='insufficient_evidence'
def test_invented_citation_rejected(): assert run([PASSAGE],['fake'])['status']=='insufficient_evidence'
def test_irrelevant_rejected(): assert run([PASSAGE],[],False)['status']=='insufficient_evidence'
def test_untrusted_source_rejected(): assert run([{**PASSAGE,'source_url':'https://evil.example'}],['a'])['status']=='insufficient_evidence'
def test_bare_course_number_requests_subject_without_retrieval():
    class NoEmbed:
        def embed_query(self, question):
            raise AssertionError('Ambiguous questions should not call embeddings')
    result=build_graph(Store([PASSAGE]),NoEmbed(),Model(['a'])).invoke({'question':'What are the prerequisites for 225?'})
    assert result['status']=='insufficient_evidence'
    assert 'Which subject' in result['answer']
    assert result['citations']==[]
def test_topic_only_in_prerequisite_is_not_retrieved_as_course_coverage():
    main={**PASSAGE,'content':'MATH 415 Applied Linear Algebra. Linear algebra techniques.'}
    misleading={**PASSAGE,'id':'b','content':'MATH 522 Lie Groups. Prerequisite: undergraduate linear algebra.'}
    r=build_graph(Store([main,misleading]),Embed(),Model(['a'])).invoke({'question':'Which mathematics courses cover linear algebra?'})
    assert [p['id'] for p in r['passages']]==['a']
