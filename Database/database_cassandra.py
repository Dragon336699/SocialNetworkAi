from cassandra.cluster import Cluster

_cluster = None
_session = None

def get_cassandra_session():
    global _cluster, _session

    if _session is None:
        _cluster = Cluster(["cassandra"])
        _session = _cluster.connect("fricon")

    return _session
