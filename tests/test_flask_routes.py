import os
import sys
import json
import pytest

# Ensure root workspace directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
import psalms_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    res = client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'ok'

def test_list_all_psalms_endpoint(client):
    res = client.get('/api/psalms')
    assert res.status_code == 200
    data = res.get_json()
    assert 'psalms' in data
    assert len(data['psalms']) >= 15, "Should list digitized psalms"

def test_psalm_detail_endpoint(client):
    res = client.get('/api/psalms/psalm_103_kind_chart')
    assert res.status_code == 200
    data = res.get_json()
    assert data['id'] == 'psalm_103_kind_chart'
    assert 'Ps 103' in data['title']
    assert data['key'] == 'Eb Major'
    assert len(data['response']['notes']) > 0

def test_psalm_exports(client):
    # MusicXML export
    res_xml = client.get('/api/psalms/psalm_103_kind_chart/export/musicxml')
    assert res_xml.status_code == 200
    assert b'score-partwise' in res_xml.data

    # MIDI export
    res_midi = client.get('/api/psalms/psalm_103_kind_chart/export/midi')
    assert res_midi.status_code == 200
    assert len(res_midi.data) > 0

    # JSON export
    res_json = client.get('/api/psalms/psalm_103_kind_chart/export/json')
    assert res_json.status_code == 200
    assert res_json.get_json()['id'] == 'psalm_103_kind_chart'

def test_batch_digitize_all_endpoint(client):
    res = client.post('/api/digitize-all')
    assert res.status_code == 200
    data = res.get_json()
    assert data['count'] >= 15
