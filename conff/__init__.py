from conff import ee
from conff import parser


__all__ = ['parse', 'load', 'encrypt', 'decrypt', 'generate_key', 'update', 'Parser']

parse = ee.parse
load = ee.load
encrypt = ee.encrypt
decrypt = ee.decrypt
generate_key = ee.generate_key
update = parser.update_recursive
Parser = parser.Parser
