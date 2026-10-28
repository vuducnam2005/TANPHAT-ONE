"""Validate OpenAPI and optionally check the running development API against it."""
# CLI output and literal OpenAPI path placeholders are intentional.
# ruff: noqa: T201, RUF027
import argparse
import json
from pathlib import Path

import requests
import yaml
from openapi_schema_validator import OAS30Validator
from openapi_spec_validator import validate
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT4

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    document = yaml.safe_load((ROOT / 'contracts/openapi/tanphat-v1.yaml').read_text(encoding='utf-8'))
    validate(document)
    registry = Registry().with_resource('urn:tanphat:openapi', Resource(document, DRAFT4))
    print('PASS: OpenAPI specification.')
    if not args.live:
        return

    def check(response, path, expected_status):
        assert response.status_code == expected_status, f'{path}: unexpected HTTP status {response.status_code}'
        schema = document['paths'][path]['get']['responses'][str(expected_status)]
        if '$ref' in schema:
            schema = document['components']['responses'][schema['$ref'].rsplit('/', 1)[-1]]
        schema = schema['content']['application/json']['schema']
        OAS30Validator(schema, registry=registry, _resolver=registry.resolver('urn:tanphat:openapi')).validate(response.json())

    base_url = 'http://127.0.0.1:18069'
    check(requests.get(base_url + '/api/v1/me', timeout=15), '/api/v1/me', 401)
    credentials = json.loads((ROOT / '.local/dev-secrets.json').read_text(encoding='utf-8'))

    def login(session, user, password):
        response = session.post(base_url + '/web/session/authenticate', json={
            'jsonrpc': '2.0', 'method': 'call', 'id': 1,
            'params': {'db': 'tp_tanphat_dev', 'login': user, 'password': password},
        }, timeout=30)
        assert response.json().get('result', {}).get('uid'), f'Development login failed for {user}.'

    def check_contracts(session):
        """Validate list, every visible detail and revision; returns the detail payloads."""
        contracts = session.get(base_url + '/api/v1/contracts', timeout=15)
        check(contracts, '/api/v1/contracts', 200)
        details = []
        for row in contracts.json()['data']:
            for as_of in ('2026-10-31', '2026-11-01'):
                detail = session.get(base_url + f"/api/v1/contracts/{row['id']}?as_of={as_of}", timeout=15)
                check(detail, '/api/v1/contracts/{contract_id}', 200)
            details.append(detail.json()['data'])
            for revision in detail.json()['data']['revisions']:
                check(session.get(base_url + f"/api/v1/contracts/{row['id']}/revisions/{revision['id']}", timeout=15),
                      '/api/v1/contracts/{contract_id}/revisions/{revision_id}', 200)
        return details

    with requests.Session() as session:
        login(session, 'admin', credentials['admin'])
        details = check_contracts(session)
        assert any(detail['permissions']['financial_read'] for detail in details), 'No financial contract shape checked.'
    with requests.Session() as session:
        login(session, 'planner.dev', credentials['planner'])
        details = check_contracts(session)
        assert details and not any(detail['permissions']['financial_read'] for detail in details)
        contract_id = details[0]['id']
        check(session.get(base_url + '/api/v1/contracts/2147483647', timeout=15), '/api/v1/contracts/{contract_id}', 404)
        check(session.get(base_url + f'/api/v1/contracts/{contract_id}?as_of=31-10-2026', timeout=15),
              '/api/v1/contracts/{contract_id}', 400)
        check(session.get(base_url + f'/api/v1/contracts/{contract_id}/documents/2147483647/content', timeout=15),
              '/api/v1/contracts/{contract_id}/documents/{document_id}/content', 404)
        check(session.get(base_url + '/api/v1/me', timeout=15), '/api/v1/me', 200)
        projects = session.get(base_url + '/api/v1/projects', timeout=15)
        check(projects, '/api/v1/projects', 200)
        project_id = projects.json()['data'][0]['id']
        check(session.get(base_url + f'/api/v1/projects/{project_id}', timeout=15), '/api/v1/projects/{project_id}', 200)
        check(session.get(base_url + '/api/v1/projects?limit=101', timeout=15), '/api/v1/projects', 400)
        check(session.get(base_url + '/api/v1/projects/2147483647', timeout=15), '/api/v1/projects/{project_id}', 404)
    print('PASS: live bootstrap, project and contract list/detail/revision, money shapes and error response schemas.')


if __name__ == '__main__':
    main()
