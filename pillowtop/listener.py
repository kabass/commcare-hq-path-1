import logging
import restkit
from restkit.resource import Resource
import hashlib
import simplejson
from gevent import socket
import rawes
import gevent
from django.conf import settings
import logging
from dimagi.utils.decorators.memoized import memoized
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.ERROR)

import couchdbkit
if couchdbkit.version_info < (0,6,0):
    USE_NEW_CHANGES=False
else:
    from couchdbkit.changes import ChangesStream
    USE_NEW_CHANGES=True

CHECKPOINT_FREQUENCY = 100
WAIT_HEARTBEAT = 10000

def old_changes(pillow):
    from couchdbkit import Server, Consumer
    c = Consumer(pillow.couch_db, backend='gevent')
    while True:
        try:
            c.wait(pillow.parsing_processor, since=pillow.since, filter=pillow.couch_filter,
                heartbeat=WAIT_HEARTBEAT, feed='continuous', timeout=30000)
        except Exception, ex:
            logging.exception("Exception in form listener: %s, sleeping and restarting" % ex)
            gevent.sleep(5)

def new_changes(pillow):
     with ChangesStream(pillow.couch_db, feed='continuous', heartbeat=True, since=pillow.since,
         filter=pillow.couch_filter) as st:
        for c in st:
            pillow.processor(c)

class BasicPillow(object):
    couch_filter = None # string for filter if needed
    couch_db = None #couchdbkit Database Object
    changes_seen = 0

    def run(self, since=0):
        """
        Couch changes stream creation
        """
        logging.info("Starting pillow %s" % self.__class__)
        if USE_NEW_CHANGES:
            new_changes(self)
        else:
            old_changes(self)

    def get_name(self):
        return "%s.%s" % (self.__module__, self.__class__.__name__)

    def get_checkpoint_doc_name(self):
        return "pillowtop_%s" % self.get_name()

    def get_checkpoint(self):
        doc_name = self.get_checkpoint_doc_name()

        if self.couch_db.doc_exist(doc_name):
            checkpoint_doc = self.couch_db.open_doc(doc_name)
        else:
            checkpoint_doc = {
                "_id": doc_name,
                "seq": 0
                #todo: bigcouch changes seq are [num, string] arrs, num is meaningless,string is meaningful
            }
            self.couch_db.save_doc(checkpoint_doc)
        return checkpoint_doc

    def reset_checkpoint(self):
        checkpoint_doc = self.get_checkpoint()
        checkpoint_doc['old_seq'] = checkpoint_doc['seq']
        checkpoint_doc['seq'] = 0
        self.couch_db.save_doc(checkpoint_doc)


    @property
    def since(self):
        checkpoint = self.get_checkpoint()
        return checkpoint['seq']

    def set_checkpoint(self, change):
        checkpoint = self.get_checkpoint()
        checkpoint['seq'] = change['seq']
        self.couch_db.save_doc(checkpoint)

    def parsing_processor(self, change):
        """
        Processor that also parses the change to json - only for pre 0.6.0 couchdbkit,
        as the change is passed as a string
        """
        self.processor(simplejson.loads(change))

    def processor(self, change, do_set_checkpoint=True):
        """
        Parent processsor for a pillow class - this should not be overridden.
        This workflow is made for the situation where 1 change yields 1 transport/transaction
        """
        self.changes_seen+=1
        if self.changes_seen % CHECKPOINT_FREQUENCY == 0 and do_set_checkpoint:
            logging.info("(%s) setting checkpoint: %d" % (self.get_checkpoint_doc_name(),
                                                      change['seq']))
            self.set_checkpoint(change)


        t = self.change_trigger(change)
        if t is not None:
            tr = self.change_transform(t)
            if tr is not None:
                self.change_transport(tr)


    def change_trigger(self, changes_dict):
        """
        Step one of pillowtop process
        For a given _changes indicator, the changes dict (the id, _rev) is sent here.

        Note, a couch _changes line is: {'changes': [], 'id': 'guid',  'seq': <int>}
        a 'deleted': True might be there too

        whereas a doc_dict is _id
        Should return a doc_dict
        """
        if changes_dict.get('deleted', False):
            #override deleted behavior on consumers that care/deal with deletions
            return None
        return self.couch_db.open_doc(changes_dict['id'])

    def change_transform(self, doc_dict):
        """
        Step two of the pillowtop processor:
        Process/transform doc_dict if needed - by default, return the doc_dict passed.
        """
        return doc_dict
    def change_transport(self, doc_dict):
        """
        Step three of the pillowtop processor:
        Finish transport of doc if needed. Your subclass should implement this
        """
        raise NotImplementedError("Error, this pillowtop subclass has not been configured to do anything!")



class ElasticPillow(BasicPillow):
    """
    Elasticsearch handler
    """
    es_host = ""
    es_port = ""
    es_index = ""
    es_type = ""
    es_meta = {}

    # Note - we allow for for existence because we do not care - we want the ES
    # index to always have the latest version of the case based upon ALL changes done to it.
    allow_updates=True

    def __init__(self):
        es = self.get_es()
        if not es.head(self.es_index):
            es.put(self.es_index, data=self.es_meta)

    def get_doc_path(self, doc_id):
        return "%s/%s/%s" % (self.es_index, self.es_type, doc_id)

    def get_index_mapping(self):
        es = self.get_es()
        return es.get('%s/_mapping' % self.es_index)[self.es_index]

    @memoized
    def get_es(self):
        return rawes.Elastic('%s:%s' % (self.es_host, self.es_port))

    def delete_index(self):
        """
        Coarse way of deleting an index - a todo is to set aliases where need be
        """
        es = self.get_es()
        if es.head(self.es_index):
            es.delete(self.es_index)

    def create_index(self):
        """
        Rebuild an index after a delete
        """
        es = self.get_es()
        es.put(self.es_index, data=self.es_meta)

    def change_trigger(self, changes_dict):
        if changes_dict.get('deleted', False):
            try:
                self.get_es().delete(path=self.get_doc_path(changes_dict['id']))
            except Exception, ex:
                logging.error("ElasticPillow: error deleting route %s - ignoring: %s" % \
                              (self.get_doc_path(changes_dict['id']), ex))
            return None
        return self.couch_db.open_doc(changes_dict['id'])


    def doc_exists(self, doc_id):
        """
        Using the HEAD 404/200 result API for document existence
        Returns True if 200(exists)
        """
        es = self.get_es()
        doc_path = self.get_doc_path(doc_id)
        head_result = es.head(doc_path)
        return head_result

    def change_transport(self, doc_dict):
        """
        Default elastic pillow for a given doc to a type.
        """
        try:
            es = self.get_es()
            doc_path = self.get_doc_path(doc_dict['_id'])

            if self.allow_updates:
                can_put = True
            else:
                can_put = not self.doc_exists(doc_dict['_id'])

            if can_put:
                res = es.put(doc_path,  data = doc_dict)
                if res.get('status', 0) == 400:
                    logging.error("Pillowtop Error [%s]:\n%s\n\tDoc id: %s\n\t%s" % (self.get_name(),
                                     res.get('error', "No error message"),
                                     doc_dict['_id'], doc_dict.keys()))
        except Exception, ex:
            logging.error("PillowTop [%s]: transporting change data to elasticsearch error: %s",
                (self.get_name(), ex))
            return None


class AliasedElasticPillow(ElasticPillow):
    es_alias = ''
    es_index_prefix = ''
    seen_types = {}

    def __init__(self, **kwargs):
        super(AliasedElasticPillow, self).__init__(**kwargs)
        self.seen_types = self.get_index_mapping()


    def calc_meta(self):
        raise NotImplementedError("Need to implement your own meta calculator")


    def type_exists(self, doc_dict):
        es = self.get_es()
        type_string = self.get_type_string(doc_dict)

        ##################
        #ES 0.20 has the index HEAD API.  While we're on 0.19, we will need to poll the index
        # metadata
        #type_path = "%(index)s/%(type_string)s" % ( { 'index': self.es_index, 'type_string': type_string, })

        #if we don't want to server confirm it for both .19 or .20, then this hash is enough
        #if self.seen_types.has_key(type_string):
        #return True
        #else:
        #self.seen_types[type_string] = True
        #head_result = es.head(type_path)
        #return head_result
        ##################

        #####
        #0.19 method, get the mapping from the index
        return self.seen_types.has_key(type_string)

    def get_type_string(self, doc_dict):
        raise NotImplementedError("Please implement acustom type string resolver")

    def get_doc_path_typed(self, doc_dict):
        return "%(index)s/%(type_string)s/%(id)s" % (
            {
                'index': self.es_index,
                'type_string': self.get_type_string(doc_dict),
                'id': doc_dict['_id']
            })

    def doc_exists(self, doc_dict):
        """
        Overrided based upon the doc type
        """
        es = self.get_es()
        doc_path = "%(index)s/%(type_string)s/%(id)s" % (
            {
                'index': self.es_index,
                'type_string': self.get_type_string(doc_dict),
                'id': doc_dict['_id']
            })
        head_result = es.head(doc_path)
        return head_result

    def get_name(self):
        return "%s.%s.%s" % (self.__module__, self.__class__.__name__, self.calc_meta())

    def calc_meta(self):
        if not hasattr(self, '_calc_meta'):
            self._calc_meta = hashlib.md5(simplejson.dumps(self.es_meta)).hexdigest()
        return self._calc_meta

    @property
    def es_index(self):
        return "%s_%s" % (self.es_index_prefix, self.calc_meta())




class NetworkPillow(BasicPillow):
    """
    Basic network endpoint handler.
    This is useful for the logstash/Splunk use cases.
    """
    endpoint_host = ""
    endpoint_port = 0
    transport_type = 'tcp'

    def change_transport(self, doc_dict):
        try:
            address = (self.endpoint_host, self.endpoint_port)
            if self.transport_type == 'tcp':
               stype = socket.SOCK_STREAM
            elif self.transport_type == 'udp':
                stype = socket.SOCK_DGRAM
            sock = socket.socket(type=stype)
            sock.connect(address)
            sock.send(simplejson.dumps(doc_dict), timeout=1)
            return 1
        except Exception, ex:
            logging.error("PillowTop [%s]: transport to network socket error: %s" % (self .get_name(), ex))
            return None

class LogstashMonitoringPillow(NetworkPillow):
    """
    This is a logstash endpoint (but really just TCP) for our production monitoring/aggregation
    of log information.
    """
    def __init__(self):
        if settings.DEBUG:
            #In a dev environment don't care about these
            logging.info("[%s] Settings are DEBUG, suppressing the processing of these feeds" % self.get_name())
    def processor(self, change):
        if settings.DEBUG:
            return {}
        else:
            return super(NetworkPillow, self).processor(change)

