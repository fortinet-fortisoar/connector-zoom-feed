"""
Copyright start
MIT License
Copyright (c) 2023 Fortinet Inc Copyright end
"""

import requests, datetime
from connectors.core.connector import get_logger, ConnectorError

logger = get_logger('zoom-feed')

SERVICE_ENDPOINT_MAPPING = {
    "Zoom": "/Zoom.txt",
    "Zoom Meetings - IPv4": "/ZoomMeetings.txt",
    "Zoom Meetings - IPv6": "/ZoomMeetings-IPv6.txt",
    "Zoom Cloud Room Connector": "/ZoomCRC.txt",
    "Zoom Phone - IPv4": "/ZoomPhone.txt",
    "Zoom Phone - IPv6": "/ZoomPhone-IPv6.txt",
    "Zoom Contact Center - IPv4": "/ZoomCC.txt",
    "Zoom Contact Center - IPv6": "/ZoomCC.txt",
    "Zoom CDN - IPv4": "/ZoomCDN.txt",
    "Zoom CDN - IPv6": "/ZoomCDN-IPv6.txt",
    "Zoom Apps": "/ZoomApps.txt",
    "Zoom Apps - IPv6": "/ZoomApps-IPv6.txt"
}


class ZoomFeed:
    def __init__(self, config):
        server_url = config.get('server_url').strip('/')
        if server_url.startswith('https') or server_url.startswith('http'):
            self.server_url = server_url
        else:
            self.server_url = "https://{0}".format(server_url)
        self.verify_ssl = config.get('verify_ssl', True)

    def make_rest_call(self, endpoint='', method='GET', get_modified_date=False, **kwargs):
        try:
            server_url = self.server_url + endpoint
            response = requests.request(url=server_url, method=method, verify=self.verify_ssl, **kwargs)
            if response.ok:
                if 'json' in str(response.headers):
                    return response.json()
                else:
                    logger.debug('Response not in json format')
                    if get_modified_date:
                        modified_date = response.headers.get('last-modified')
                        return response.text, modified_date
                    return response.text
            else:
                raise ConnectorError(
                    '{0} . Error status: {1}'.format(response.text, response.status_code))
        except requests.exceptions.SSLError:
            logger.error('An SSL error occurred.')
            raise ConnectorError('An SSL error occurred.')
        except requests.exceptions.ConnectionError:
            logger.error('A connection error occurred.')
            raise ConnectorError('A connection error occurred.')
        except Exception as Err:
            logger.exception(Err)
            raise ConnectorError(Err)


def check_health(config):
    try:
        zoom = ZoomFeed(config)
        zoom.make_rest_call(endpoint='/Zoom.txt')
        return True
    except Exception as Err:
        logger.exception(Err)
        raise ConnectorError(Err)


def compare_last_and_current_time(last_pull_time, modified_date):
    try:
        try:
            last_pull_ts = int(datetime.datetime.strptime(str(last_pull_time), "%Y-%m-%dT%H:%M:%S.%fZ").timestamp())
            modified_time_ts = int(datetime.datetime.strptime(modified_date, "%a, %d %b %Y %H:%M:%S %Z").timestamp())
        except Exception as err:
            logger.debug('Err = {0}'.format(err))
            logger.debug('Now checking format {}'.format('%Y-%m-%dT%H:%M:%S.%fZ'))
            raise
        if last_pull_ts < modified_time_ts:
            return True
        return False
    except Exception as Err:
        logger.exception(Err)
        raise ConnectorError(Err)


def filter_resp(resp):
    try:
        resp = resp.split()
        return resp
    except Exception as Err:
        logger.exception(Err)
        raise ConnectorError(Err)


def get_indicators(config, params):
    try:
        zoom = ZoomFeed(config)
        response = {}
        for service in params.get('services', ['Zoom']):
            resp, modified_date = zoom.make_rest_call(SERVICE_ENDPOINT_MAPPING.get(service), get_modified_date=True)
            last_pull_time = params.get("last_pull_time")
            flag = compare_last_and_current_time(last_pull_time, modified_date) if last_pull_time else True
            resp = filter_resp(resp) if flag else []
            response[service] = resp
        return response
    except Exception as Err:
        logger.exception(Err)
        raise ConnectorError(Err)


operations = {
    'get_indicators': get_indicators
}
