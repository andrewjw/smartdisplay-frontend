#
# Taken from https://github.com/devbis/micropython-aiosentry
# and adapted to work with modern Sentry.io and without asyncio.
#
#
# MIT License
#
# Copyright (c) 2019 Ivan Belokobylskiy
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import machine
import binascii
import os
import sys
import io
import json
import urequests


def get_exception_str(exception: Exception) -> str:
    exception_io = io.StringIO()
    sys.print_exception(exception, exception_io)
    exception_io.seek(0)
    result = exception_io.read()
    exception_io.close()
    return result


def http_request(domain, url, data, headers=()) -> str:
    method = urequests.get
    if data:
        method = urequests.post

    r = method(domain + url, data=data, headers=headers)
    return r.text


class SentryClient:
    def __init__(self, ingest_domain: str, project_id: str, key: str) -> None:
        self.ingest_domain = ingest_domain
        self.project_id = project_id
        self.key = key

    def send_exception(self, exception: Exception) -> str:
        domain = 'https://' + self.ingest_domain
        url_tpl = '/api/{}/store/'
        url = url_tpl.format(self.project_id)
        json_data = (
            '{'
            '"event_id": "%(event_id)s",'
            '"exception": {"values":[{"type": "%(type)s","value": '
            '%(value)s,"module": "%(module)s"}]},'
            '"tags": {'
            '"machine_id": "%(machine_id)s", '
            '"platform": "%(platform)s",'
            '"os.name": "%(os_name)s",'
            '"os.version": "%(os_version)s"},'
            '"extra": {"stacktrace": %(stacktrace)s}'
            '}' %
            {
                'event_id': binascii.hexlify(os.urandom(16)).decode(),
                'type': exception.__class__.__name__,
                'value': json.dumps(
                    exception.args[0] if exception.args else '',
                ),
                'module': exception,
                'stacktrace': json.dumps(get_exception_str(exception)),
                'machine_id': binascii.hexlify(machine.unique_id()).decode(),
                'platform': sys.platform,
                'os_name': sys.implementation.name,
                'os_version': ".".join(
                    str(x) for x in sys.implementation.version
                ),
            }
        )

        return http_request(
            domain,
            url,
            json_data,
            {
                "Content-Type": "application/json",
                "X-Sentry-Auth": "Sentry sentry_version=7, sentry_key={}, "
                "sentry_client=sentry-micropython/0.1".format(self.key)
            },
        )