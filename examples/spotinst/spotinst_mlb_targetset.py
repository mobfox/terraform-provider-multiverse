# Original Author: David Spitzer <david.sp@mobfox.com>
# Maintainer :  Ben Ishak <wahb.bi@mobfox.com>

from __future__ import print_function
import os, sys
import json
import logging
import urllib.request
import urllib.response
import http.client
from urllib.request import Request

spotinst_token = 'SPOTINST_TOKEN'
spotinst_account_id = 'SPOTINST_ACCOUNT_ID'

root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

def initialize():
    if os.getenv('method') is None:
        os.environ["method"] = "query"
        print("Running the function in Query Mode")
    if os.getenv('method') == 'insert':
        print("Running the function in Insert Mode")


def handler(event, context):
    logging.debug('Starting from event: %s', event)
    data = json.loads(context)
    if event == 'create':
        try:
            resources = create_resources(data)
            resources["id"] = str(json.dumps(resources["resources"]))
            with open('spotinst.json', 'w') as outfile:
                json.dump(resources, outfile)
            return resources
        except Exception as e:
            raise e
    elif event == 'update':
        raise Exception("Updates are not supported")
    elif event == 'read':
        with open('spotinst.json', 'r') as f:
            resources = json.load(f)
        return resources
    elif event == 'delete':
        try:
            resources_created: list = data
            with open('spotinst.log', 'a') as outfile:
                json.dump(data, outfile)
            delete_resources(resources_created)
            return {"Status": "SUCCESS"}
        except Exception as e:
            raise e
    else:
        raise Exception("Unknown Action {}".format(event))


def delete_resources(resources_to_delete: list):
    logging.info('Deleting %d resources', len(resources_to_delete))
    for resource in resources_to_delete:
        try:
            logging.info('Sending DELETE %s', resource)
            send_spotinst_request('DELETE', resource)
        except Exception as e:
            logging.error("Error rolling back: %s", e)


def create_resources(data: dict) -> dict:
    resources_created: list = []
    try:
        test_target_set_id = \
            create_target_set(data,
                              '{}-test'.format(data['name']),
                              '/health.check.haproxy.php',
                              80)['items'][0]['id']
        resources_created.append('/loadBalancer/targetSet/{}?accountId={}'.format(test_target_set_id, spotinst_account_id))
        control_target_set_id = \
            create_target_set(data,
                              '{}-control'.format(data['name']),
                              '/health',
                              8081)['items'][0]['id']
        resources_created.append(
            '/loadBalancer/targetSet/{}?accountId={}'.format(control_target_set_id, spotinst_account_id))

        routing_rules: list = create_routing_rules(data, test_target_set_id, control_target_set_id)
        resources_created += routing_rules

        return {
            "resources": resources_created,
            "testTargetSet": test_target_set_id,
            "controlTargetSet": control_target_set_id
        }
    except Exception as e:
        logging.error('Error creating resources')
        logging.exception(e)
        delete_resources(resources_created)
        raise e


def create_routing_rules(data: dict, test_target_set_id: str, control_target_set_id: str) -> list:
    resources_created = []
    for listener_id in data['mlb_listener_ids']:
        try:
            resources_created.append('/loadBalancer/routingRule/{}?accountId={}'.format(create_routing_rule(
                data['mlb_id'],
                data['test_group_callback_fqdn'],
                test_target_set_id,
                listener_id), spotinst_account_id))
            resources_created.append('/loadBalancer/routingRule/{}?accountId={}'.format(create_routing_rule(
                data['mlb_id'],
                data['test_group_callback_fqdn'],
                test_target_set_id,
                listener_id,
                80), spotinst_account_id))
            resources_created.append('/loadBalancer/routingRule/{}?accountId={}'.format(create_routing_rule(
                data['mlb_id'],
                data['test_group_callback_fqdn'],
                test_target_set_id,
                listener_id,
                443), spotinst_account_id))
            resources_created.append('/loadBalancer/routingRule/{}?accountId={}'.format(create_routing_rule(
                data['mlb_id'],
                data['control_group_callback_fqdn'],
                control_target_set_id,
                listener_id), spotinst_account_id))
            resources_created.append('/loadBalancer/routingRule/{}?accountId={}'.format(create_routing_rule(
                data['mlb_id'],
                data['control_group_callback_fqdn'],
                control_target_set_id,
                listener_id,
                80), spotinst_account_id))
            resources_created.append('/loadBalancer/routingRule/{}?accountId={}'.format(create_routing_rule(
                data['mlb_id'],
                data['control_group_callback_fqdn'],
                control_target_set_id,
                listener_id,
                443), spotinst_account_id))
        except Exception as e:
            logging.error('Error creating routing rules')
            logging.exception(e)
            delete_resources(resources_created)
            raise e
    return resources_created


def create_routing_rule(load_balancer_id: str, callback_fqdn: str, targetset_id: str, listener_id: str,
                        port: int = None) -> str:
    create_routing_rule_req = {
        'routingRule': {
            'balancerId': load_balancer_id,
            'route': 'Host(`{}`)'.format(
                (callback_fqdn if port is None else '{}:{}'.format(callback_fqdn, port))),
            'targetSetIds': [targetset_id],
            'middlewareIds': [],
            'listenerId': listener_id,
            'tags': [],
            'priority': 10
        }
    }
    routing_rule_id: str = \
        send_spotinst_request('POST', '/loadBalancer/routingRule?accountId={}'.format(spotinst_account_id),
                              create_routing_rule_req)['response']['items'][0]['id']
    return routing_rule_id


def create_target_set(data, name, healthcheck, port) -> dict:
    create_target_set_request = {
        'targetSet': {
            'name': name,
            'balancerId': data['mlb_id'],
            'deploymentId': data['mlb_deployment_id'],
            'protocol': 'HTTP',
            'weight': 1,
            'healthCheck': {
                'interval': 10,
                'path': healthcheck,
                'port': port,
                'protocol': 'HTTP',
                'timeout': 5,
                'healthyThresholdCount': 2,
                'unhealthyThresholdCount': 3
            },
            'tags': []
        }
    }
    return send_spotinst_request('POST', '/loadBalancer/targetSet?accountId={}'.format(spotinst_account_id),
                                 create_target_set_request)['response']


def send_spotinst_request(method, path, body=None) -> dict:
    request = urllib.request.Request('https://api.spotinst.io' + path)
    json_body: str = None
    if body is not None:
        request.add_header('Content-Type', 'application/json')
        json_body = json.dumps(body)
        request.data = json_body.encode('utf-8')
    request.add_header('Authorization', 'Bearer ' + spotinst_token)
    request.method = method
    logging.debug("Sending %s to %s: %s", method, request.get_full_url(), json_body if json_body is not None else '<empty>')
    response_object: http.client.HTTPResponse = urllib.request.urlopen(request)
    response_json = json.loads(response_object.read())
    logging.debug("Response: %s", response_json)
    return response_json

if __name__ == '__main__':
    print(json.dumps(handler(sys.argv[1], sys.argv[2])))