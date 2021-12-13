import unittest
import os
from sdap.data_access import CollectionLoader

class CollectionLoaderTestCase(unittest.TestCase):

    def test_collectionLoad(self):

        collection_config_file = 'collection-config.yaml'
        collection_config_dir = os.path.dirname(__file__)

        collectionLoader = CollectionLoader(os.path.join(collection_config_dir, collection_config_file))

        collectionLoader.get_driver('hls').get()

if __name__ == '__main__':
    unittest.main()
