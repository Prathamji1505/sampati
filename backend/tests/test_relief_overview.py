from .test_accounts import signup
from .test_deliveries import action, create, dispatch, issued_stock


def test_overview_counts_pending_work_without_treating_issues_as_arrivals(client):
    auth = signup(client)
    _, _, _, request, issue = issued_stock(client, auth)
    shipment = create(client, auth, issue)
    before = client.get('/api/overview/relief').json()
    assert before['needs_total'] == 1 and before['needs'][0]['remaining'] == '40'
    assert before['attention']['shipments'] == 1 and before['attention']['stock_positions'] == 1
    shipment = dispatch(client, auth, shipment)
    result = action(client, auth, shipment, 'delivery', quantity='12.125')
    assert result.status_code == 201
    after = client.get('/api/overview/relief').json()
    assert after['needs'][0]['remaining'] == '27.875' and after['needs'][0]['unit'] == 'packs'
    assert after['needs'][0]['id'] == request['id']
    signup(client, username='separate-owner')
    assert client.get('/api/overview/relief').json()['needs_total'] == 0
    assert all(value == 0 for value in client.get('/api/overview/relief').json()['attention'].values())


def test_overview_requires_membership_and_demo_is_read_only(client):
    assert client.get('/api/overview/relief').status_code == 401
    demo = client.get('/api/demo/overview/relief')
    assert demo.status_code == 200 and demo.json()['needs'] == []
