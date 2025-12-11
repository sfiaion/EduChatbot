import pathlib, sys
BASE = pathlib.Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))
from fastapi.testclient import TestClient
from app.main import app

def test_recommendation_high_slot():
    c = TestClient(app)
    r = c.post('/api/problems/2/recommendation', json={'question_id':2,'student_id':1,'slot':'high','expect_num':5})
    assert r.status_code == 200
    data = r.json()
    assert data['found'] >= 1
    assert isinstance(data['items'], list)
