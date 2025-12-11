import pathlib, sys
BASE = pathlib.Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))
from fastapi.testclient import TestClient
from app.main import app

def test_practice_list_roundtrip():
    c = TestClient(app)
    r = c.get('/api/practice/list', params={'student_id': 1})
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    r = c.post('/api/practice/list', json={'student_id': 1, 'ids': [2,3,3]})
    assert r.status_code == 200
    r = c.get('/api/practice/list', params={'student_id': 1})
    assert r.json() == [2,3]

def test_practice_record_save():
    c = TestClient(app)
    r = c.post('/api/practice/record', json={'student_id':1, 'question_id':2, 'answer':'A'})
    assert r.status_code == 200
    assert r.json().get('ok')
