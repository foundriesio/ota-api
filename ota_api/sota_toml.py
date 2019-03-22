# Copyright (C) 2019 Foundries.io
# Author: Marti Bolivar <marti@foundries.io>
from collections import namedtuple, OrderedDict

from ota_api.settings import GATEWAY_SERVER

SotaConfigCommon = namedtuple('SotaConfigCommon', 'gateway_server')

# TOML values (but not keys) can use {common.gateway_server} or other
# attributes of the named tuple in format strings access common
# values.
SOTA_CONFIG_COMMON = SotaConfigCommon(GATEWAY_SERVER)


def _mk_config():
    # Default SOTA configuration. This is not a complete aktualizr
    # configuration file
    return OrderedDict([
        ("tls",
         OrderedDict([("server", '"{common.gateway_server}"'),
                      ("ca_source", '"file"'),
                      ("pkey_source", '"file"'),
                      ("cert_source", '"file"')])),

        ("provision",
         OrderedDict([("server", '"{common.gateway_server}"'),
                      ("p12_password", '""'),
                      ("expiry_days", '"36000"'),
                      ("provision_path", '""'),
                      ("primary_ecu_hardware_id", None)])),

        ("uptane",
         OrderedDict([("polling", 'true'),
                      ("director_server",
                       '"{common.gateway_server}/director"'),
                      ("repo_server", '"{common.gateway_server}/repo"'),
                      ("key_source", '"file"')])),

        ("pacman",
         OrderedDict([("type", '"ostree"'),
                      ("ostree_server", '"{common.gateway_server}/treehub"'),
                      ("packages_file", '"/usr/package.manifest"')])),

        ("storage",
         OrderedDict([("type", '"sqlite"'),
                      ("path", '"/var/sota/"')])),

        ("import",
         OrderedDict([("tls_cacert_path", '"/var/sota/root.crt"'),
                      ("tls_pkey_path", '"/var/sota/pkey.pem"'),
                      ("tls_clientcert_path", '"/var/sota/client.pem"')])),
    ])


def sota_toml_fmt(common=SOTA_CONFIG_COMMON, overrides=None):
    d = _mk_config()
    if overrides:
        for section in overrides:
            if section not in d:
                d[section] = OrderedDict()
            for k, v in overrides[section].items():
                d[section][k] = v

    ret = []
    for section in d:
        ret.append('[{}]'.format(section))
        for k, v in d[section].items():
            if v is None or v == "":
                # None or an empty string means unset. (For a literal
                # empty string, use 2 double quote characters, i.e. '""'.)
                ret.append('# {} is not set'.format(k))
            else:
                ret.append('{} = {}'.format(k, v.format(common=common)))
        ret.append('')
    return '\n'.join(ret).rstrip() + '\n'
