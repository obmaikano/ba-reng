"""Tests for the Read API endpoints (Stage 2.0-2.1)."""

from backend.api.metrics.participation_index import compute


def test_status_returns_counts(api_client):
    """Status endpoint reports record counts and last crawl outcome."""
    resp = api_client.client.get('/api/v1/status')
    assert resp.status_code == 200
    body = resp.json()
    assert body['status'] == 'ok'
    assert body['mp_count'] == 2
    assert body['contribution_count'] == 3
    assert body['last_crawl']['status'] == 'SUCCESS'


def test_list_mps_includes_participation_index(api_client):
    """MP list includes contribution counts and a weighted participation index."""
    resp = api_client.client.get('/api/v1/mps')
    assert resp.status_code == 200
    mps = {mp['name']: mp for mp in resp.json()}
    jane = mps['Jane Motswana']
    assert jane['contribution_count'] == 2
    assert jane['participation_index']['is_proxy'] is True
    assert jane['participation_index']['caveat'] == (
        'Based on recorded contributions only. Not attendance data.'
    )


def test_get_mp_by_id_returns_breakdown(api_client):
    """A single MP profile includes breakdown by contribution type."""
    jane_id = api_client.mp_ids['Jane Motswana']
    resp = api_client.client.get(f'/api/v1/mps/{jane_id}')
    assert resp.status_code == 200
    body = resp.json()
    assert body['name'] == 'Jane Motswana'
    types = {row['contribution_type'] for row in body['breakdown_by_type']}
    assert types == {'question', 'motion'}


def test_get_mp_not_found(api_client):
    """Requesting an unknown MP id returns 404."""
    unknown_id = max(api_client.mp_ids.values()) + 1
    resp = api_client.client.get(f'/api/v1/mps/{unknown_id}')
    assert resp.status_code == 404


def test_get_mp_contributions(api_client):
    """MP contributions endpoint returns that MP's contributions with source_url."""
    jane_id = api_client.mp_ids['Jane Motswana']
    resp = api_client.client.get(f'/api/v1/mps/{jane_id}/contributions')
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 2
    assert all(row['source_url'] for row in rows)


def test_list_contributions_filters_by_type(api_client):
    """Contributions can be filtered by type."""
    resp = api_client.client.get('/api/v1/contributions', params={'type': 'motion'})
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]['contribution_type'] == 'motion'


def test_list_contributions_filters_by_constituency(api_client):
    """Contributions can be filtered by MP constituency."""
    resp = api_client.client.get(
        '/api/v1/contributions', params={'constituency': 'Francistown East'},
    )
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]['mp_name'] == 'John Kgosi'


def test_get_contribution_by_id(api_client):
    """A single contribution can be fetched by id."""
    contribution_id = api_client.contribution_ids[0]
    resp = api_client.client.get(f'/api/v1/contributions/{contribution_id}')
    assert resp.status_code == 200
    assert resp.json()['mp_name'] == 'Jane Motswana'


def test_get_contribution_not_found(api_client):
    """Requesting an unknown contribution id returns 404."""
    unknown_id = max(api_client.contribution_ids) + 1
    resp = api_client.client.get(f'/api/v1/contributions/{unknown_id}')
    assert resp.status_code == 404


def test_list_constituencies(api_client):
    """Constituency list includes every MP's constituency and contribution count."""
    resp = api_client.client.get('/api/v1/constituencies')
    assert resp.status_code == 200
    names = {row['constituency'] for row in resp.json()}
    assert names == {'Gaborone Central', 'Francistown East'}


def test_get_constituency_case_insensitive(api_client):
    """Constituency lookup is case-insensitive."""
    resp = api_client.client.get('/api/v1/constituencies/gaborone central')
    assert resp.status_code == 200
    assert resp.json()['mp_name'] == 'Jane Motswana'


def test_get_constituency_unknown_returns_empty_shape(api_client):
    """An unknown constituency returns a zeroed placeholder, not a 404."""
    resp = api_client.client.get('/api/v1/constituencies/nowhere')
    assert resp.status_code == 200
    body = resp.json()
    assert body['contribution_count'] == 0
    assert body['mp_name'] is None


def test_search_matches_subject_text(api_client):
    """Search matches on contribution subject text."""
    resp = api_client.client.get('/api/v1/search', params={'q': 'Mohembo'})
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]['mp_name'] == 'Jane Motswana'


def test_search_matches_mp_name(api_client):
    """Search matches on MP name."""
    resp = api_client.client.get('/api/v1/search', params={'q': 'Kgosi'})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_search_requires_query_param(api_client):
    """Search without a query string is rejected."""
    resp = api_client.client.get('/api/v1/search')
    assert resp.status_code == 422


def test_participation_index_weighting() -> None:
    """Motions are weighted 1.5x, questions 1.0x, matching the PLAN spec."""
    result = compute([
        {'contribution_type': 'motion', 'cnt': 2},
        {'contribution_type': 'question', 'cnt': 3},
    ])
    assert result['participation_index'] == 2 * 1.5 + 3 * 1.0
    assert result['is_proxy'] is True
    assert result['caveat'] == 'Based on recorded contributions only. Not attendance data.'


def test_participation_index_unknown_type_defaults_to_weight_one() -> None:
    """An unrecognized contribution type falls back to a 1.0x weight."""
    result = compute([{'contribution_type': 'tabling', 'cnt': 4}])
    assert result['participation_index'] == 4.0
