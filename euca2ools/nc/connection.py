# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2011, Eucalyptus Systems, Inc.
# All rights reserved.
#
# Redistribution and use of this software in source and binary forms, with or
# without modification, are permitted provided that the following conditions
# are met:
#
#   Redistributions of source code must retain the above
#   copyright notice, this list of conditions and the
#   following disclaimer.
#
#   Redistributions in binary form must reproduce the above
#   copyright notice, this list of conditions and the
#   following disclaimer in the documentation and/or other
#   materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Author: Mitch Garnaat mgarnaat@eucalyptus.com

import urllib, base64
import time
from boto.connection import AWSAuthConnection
from boto import handler
from boto.resultset import ResultSet
from boto.exception import BotoClientError
from boto.exception import S3ResponseError
from boto.exception import S3CreateError
from boto.s3.bucket import Bucket

class EucaConnection(AWSAuthConnection):

    DefaultHost = 'localhost'
    DefaultPort = 8773

    def __init__(self, private_key_path, cert_path,
                 aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=False, port=DefaultPort, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None,
                 host=DefaultHost, debug=0, https_connection_factory=None,
                 path='/'):
        self.private_key_path = private_key_path
        self.cert_path = cert_path
        AWSAuthConnection.__init__(self, host, aws_access_key_id,
                                   aws_secret_access_key,
                                   is_secure, port, proxy, proxy_port,
                                   proxy_user, proxy_pass,
                                   debug=debug,
                                   https_connection_factory=https_connection_factory,
                                   path=path)

    def _required_auth_capability(self):
        return ['euca-nc']

    def make_request(self, verb='GET', bucket='', key='', headers=None,
                     data='', query_args=None, sender=None, action=None,
                     effective_user_id = None, params=None):
        http_request = self.build_base_http_request(verb, path, None,
                                                    params, {}, '',
                                                    self.server_name())
        if action:
            http_request.headers['EucaOperation'] = action
        if not effective_user_id:
            effective_user_id = self.aws_access_key_id
        http_request = self.fill_in_auth(http_request,
                                         cert_path=self.cert_path,
                                         euid=effective_user_id,
                                         bucket=bucket)
        return AWSAuthConnection.make_request(self, verb, path=qs,
                                              data=data,
                                              headers=headers,
                                              sender=sender,
                                              add_auth_header=False)

    def get_bucket(self, bucket_name, validate=True, headers=None):
        bucket = Bucket(self, bucket_name)
        if validate:
            bucket.get_all_keys(headers, maxkeys=0)
        return bucket

    def create_bucket(self, bucket_name, headers=None,
                      location='', policy=None):
        """
        Creates a new located bucket. By default it's in the USA. You can pass
        Location.EU to create an European bucket.

        :type bucket_name: string
        :param bucket_name: The name of the new bucket
        
        :type headers: dict
        :param headers: Additional headers to pass along with
                        the request to AWS.

        :type location: :class:`boto.s3.connection.Location`
        :param location: The location of the new bucket
        
        :type policy: :class:`boto.s3.acl.CannedACLStrings`
        :param policy: A canned ACL policy that will be applied
                       to the new key in S3.
             
        """
        if not bucket_name.islower():
            raise BotoClientError("Bucket names must be lower case.")

        if policy:
            if headers:
                headers['x-amz-acl'] = policy
            else:
                headers = {'x-amz-acl' : policy}
        if location == '':
            data = ''
        else:
            data = '<CreateBucketConstraint><LocationConstraint>' + \
                    location + '</LocationConstraint></CreateBucketConstraint>'
        response = self.make_request('PUT', bucket_name, headers=headers,
                data=data)
        body = response.read()
        if response.status == 409:
            raise S3CreateError(response.status, response.reason, body)
        if response.status == 200:
            return Bucket(self, bucket_name)
        else:
            raise S3ResponseError(response.status, response.reason, body)

    # generics

    def get_list(self, action, params, markers, path='/', parent=None, verb='GET'):
        if not parent:
            parent = self
        response = self.make_request(action, params, path, verb)
        body = response.read()
        boto.log.debug(body)
        if response.status == 200:
            rs = ResultSet(markers)
            h = handler.XmlHandler(rs, parent)
            xml.sax.parseString(body, h)
            return rs
        else:
            boto.log.error('%s %s' % (response.status, response.reason))
            boto.log.error('%s' % body)
            raise self.ResponseError(response.status, response.reason, body)

    def get_object(self, action, params, cls, path='/', parent=None, verb='GET'):
        if not parent:
            parent = self
        response = self.make_request(action, params, path, verb)
        body = response.read()
        boto.log.debug(body)
        if response.status == 200:
            obj = cls(parent)
            h = handler.XmlHandler(obj, parent)
            xml.sax.parseString(body, h)
            return obj
        else:
            boto.log.error('%s %s' % (response.status, response.reason))
            boto.log.error('%s' % body)
            raise self.ResponseError(response.status, response.reason, body)

    def get_status(self, action, params, path='/', parent=None, verb='GET'):
        if not parent:
            parent = self
        response = self.make_request(action, params, path, verb)
        body = response.read()
        boto.log.debug(body)
        if response.status == 200:
            rs = ResultSet()
            h = handler.XmlHandler(rs, parent)
            xml.sax.parseString(body, h)
            return rs.status
        else:
            boto.log.error('%s %s' % (response.status, response.reason))
            boto.log.error('%s' % body)
            raise self.ResponseError(response.status, response.reason, body)
