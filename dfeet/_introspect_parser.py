# Copyright (C) 2003, 2004, 2005, 2006 Red Hat Inc. <http://www.redhat.com/>
# Copyright (C) 2003 David Zeuthen
# Copyright (C) 2004 Rob Taylor
# Copyright (C) 2005, 2006 Collabora Ltd. <http://www.collabora.co.uk/>
#
# Licensed under the Academic Free License version 2.1
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from xml.parsers.expat import ExpatError, ParserCreate
from dbus.exceptions import IntrospectionParserException

class _Parser(object):
    __slots__ = ('map', 
                 'in_iface', 
                 'in_method', 
                 'in_signal',
                 'in_property',
                 'in_sig',
                 'out_sig', 
                 'node_level',
                 'in_signal')
    def __init__(self):
        self.map = {'child_nodes':[],'interfaces':{}}
        self.in_iface = ''
        self.in_method = ''
        self.in_signal = ''
        self.in_property = ''
        self.in_sig = ''
        self.out_sig = ''
        self.node_level = 0

    def parse(self, data):
        parser = ParserCreate('UTF-8', ' ')
        parser.buffer_text = True
        parser.StartElementHandler = self.StartElementHandler
        parser.EndElementHandler = self.EndElementHandler
        parser.Parse(data)
        return self.map

    def StartElementHandler(self, name, attributes):
        if name == 'node':
            self.node_level += 1
            if self.node_level == 2:
                self.map['child_nodes'].append(attributes['name'])
        elif not self.in_iface:
            if (not self.in_method and name == 'interface'):
                self.in_iface = attributes['name']
        else:
            if (not self.in_method and name == 'method'):
                self.in_method = attributes['name']
            elif (self.in_method and name == 'arg'):
                if attributes.get('direction', 'in') == 'in':
                    self.in_sig += attributes['type']
                if attributes.get('direction', 'out') == 'out':
                    self.out_sig += attributes['type']
            elif (not self.in_signal and name == 'signal'):
                self.in_signal = attributes['name']
            elif (self.in_signal and name == 'arg'):
                if attributes.get('direction', 'in') == 'in':
                    self.in_sig += attributes['type']
            elif (not self.in_property and name == 'property'):
                self.in_property = attributes['name']
                self.in_sig = attributes['type']
                self.out_sig = attributes['access']


    def EndElementHandler(self, name):
        if name == 'node':
            self.node_level -= 1
        elif self.in_iface:
            if (not self.in_method and name == 'interface'):
                self.in_iface = ''
            elif (self.in_method and name == 'method'):
                if not self.map['interfaces'].has_key(self.in_iface):
                    self.map['interfaces'][self.in_iface]={'methods':{}, 'signals':{}, 'properties':{}}

                if self.map['interfaces'][self.in_iface]['methods'].has_key(self.in_method):
                    print "ERROR: Some clever service is trying to be cute and has the same method name in the same interface"
                else:
                    self.map['interfaces'][self.in_iface]['methods'][self.in_method] = (self.in_sig, self.out_sig)

                self.in_method = ''
                self.in_sig = ''
                self.out_sig = ''
            elif (self.in_signal and name == 'signal'):
                if not self.map['interfaces'].has_key(self.in_iface):
                    self.map['interfaces'][self.in_iface]={'methods':{}, 'signals':{}, 'properties':{}}

                if self.map['interfaces'][self.in_iface]['signals'].has_key(self.in_signal):
                    print "ERROR: Some clever service is trying to be cute and has the same signal name in the same interface"
                else:
                    self.map['interfaces'][self.in_iface]['signals'][self.in_signal] = (self.in_sig, self.out_sig)

                self.in_signal = ''
                self.in_sig = ''
                self.out_sig = ''
            elif (self.in_property and name == 'property'):
                if not self.map['interfaces'].has_key(self.in_iface):
                    self.map['interfaces'][self.in_iface]={'methods':{}, 'signals':{}, 'properties':{}}

                if self.map['interfaces'][self.in_iface]['properties'].has_key(self.in_property):
                    print "ERROR: Some clever service is trying to be cute and has the same property name in the same interface"
                else:
                    self.map['interfaces'][self.in_iface]['properties'][self.in_property] = (self.in_sig, self.out_sig)

                self.in_property = ''
                self.in_sig = ''
                self.out_sig = ''


def process_introspection_data(data):
    """Return a dict mapping ``interface.method`` strings to a tupple of 
    concatenation of all their 'in' parameters and 'out' parameters, and mapping
    ``interface.signal`` strings to the concatenation of all their
    parameters.

    Example output::

        {
            'child_nodes': []
            'com.example.SignalEmitter.OneString': 's',
            'com.example.MethodImplementor.OneInt32Argument': 'i',
        }

    :Parameters:
        `data` : str
            The introspection XML. Must be an 8-bit string of UTF-8.
    """
    try:
        return _Parser().parse(data)
    except Exception, e:
        raise IntrospectionParserException('%s: %s' % (e.__class__, e))
