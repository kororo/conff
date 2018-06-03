from conff import ee
from conff import parser


__all__ = ['parse', 'load']

parse = ee.parse
load = ee.load
encrypt = ee.fn_encrypt_names
decrypt = ee.fn_decrypt_names
generate_key = ee.fn_crypt_generate_key_names
update = ee.update_recursive
Parser = parser.Parser
