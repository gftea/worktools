import ConfigParser



class EnodeBCfgD(object):
    node_type = None
    node_name = None
    node_ip = None
    node_cv = None
    uctool_ip = None
    uctool_username = None
    uctool_password = None
    uctool_name = None
    uctool_release = None
    uctool_revision = None


class LtesimCfgD(object):
    ip = None
    revision = None
    username = None
    password = None


class ClusterCfgD(object):
    enodeb_cfg_list = []
    ltesim_cfg = None


def parse_cfg(filename):
    """
    read config from file *filename* and return data in defined structure
    """
    config = ConfigParser.SafeConfigParser()
    config.read(filename)
    print config.items('CONFIG')

    cluster_cfg_data = ClusterCfgD()

    enbsection_list = config.get('CONFIG', 'EnodeBSectionList').split(',')
    for enb in enbsection_list:
        enb_cfg_data = EnodeBCfgD()
        enb_cfg_data.node_name = enb
        enb_cfg_data.node_type = config.get(enb, 'NodeType')
        enb_cfg_data.node_ip = config.get(enb, 'NodeIp')
        enb_cfg_data.uctool_ip = config.get(enb, 'UctoolIp')
        enb_cfg_data.uctool_name = config.get(enb, 'UctoolName')
        enb_cfg_data.uctool_username = config.get(enb, 'Username')
        enb_cfg_data.uctool_password = config.get(enb, 'Password')

        sw_ver_section = config.get(enb, 'SwVersionSection')
        enb_cfg_data.node_cv = config.get(sw_ver_section, 'NodeCv', raw=True)
        enb_cfg_data.uctool_release = config.get(sw_ver_section, 'UctoolRelease')
        enb_cfg_data.uctool_revision = config.get(sw_ver_section, 'UctoolRevision')

        cluster_cfg_data.enodeb_cfg_list.append(enb_cfg_data)
    
    ltesim_section = config.get('CONFIG', 'LtesimSection')
    ltesim_cfg_data = LtesimCfgD()
    ltesim_cfg_data.ip = config.get(ltesim_section, 'Ip')
    ltesim_cfg_data.revision = config.get(ltesim_section, 'Revision')
    ltesim_cfg_data.username = config.get(ltesim_section, 'Username')
    ltesim_cfg_data.password = config.get(ltesim_section, 'Password')

    cluster_cfg_data.ltesim_cfg = ltesim_cfg_data
    cluster_cfg_data.ltesim_cfg = ltesim_cfg_data

    return cluster_cfg_data



if __name__ == '__main__':
    
    cfg = parse_cfg(argv[1])
    
