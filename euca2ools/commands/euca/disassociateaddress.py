# Copyright 2009-2013 Eucalyptus Systems, Inc.
#
# Redistribution and use of this software in source and binary forms,
# with or without modification, are permitted provided that the following
# conditions are met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from euca2ools.commands.euca import EucalyptusRequest
from requestbuilder import Arg
from requestbuilder.exceptions import ArgumentError


class DisassociateAddress(EucalyptusRequest):
    DESCRIPTION = 'Disassociate an elastic IP address from an instance'
    ARGS = [Arg('PublicIp', metavar='ADDRESS', nargs='?', help='''[Non-VPC
                only] elastic IP address to disassociate (required)'''),
            Arg('-a', '--association-id', dest='AssociationId',
                metavar='ASSOC',
                help="[VPC only] address's association ID (required)")]

    def configure(self):
        EucalyptusRequest.configure(self)
        if self.args.get('PublicIp'):
            if self.args.get('AssociationId'):
                raise ArgumentError('argument -a/--association-id: not '
                                    'allowed with an IP address')
            elif self.args['PublicIp'].startswith('eipassoc'):
                raise ArgumentError('VPC elastic IP association IDs must be '
                                    'be specified with -a/--association-id')
        elif not self.args.get('AssociationId'):
            raise ArgumentError(
                'argument -a/--association-id or an IP address is required')

    def print_result(self, result):
        target = self.args.get('PublicIp') or self.args.get('AssociationId')
        print self.tabify(('ADDRESS', target))
