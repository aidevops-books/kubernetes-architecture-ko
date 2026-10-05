"""Local HTTP business-contract tests. These do not certify PostgreSQL/Kubernetes."""
import concurrent.futures
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


class ContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        os.environ['SQLITE_PATH'] = str(Path(cls.temp.name)/'test.sqlite')
        os.environ.pop('REDIS_HOST', None)
        os.environ['EXTERNAL_URL'] = 'http://127.0.0.1:1'
        spec=importlib.util.spec_from_file_location('cloudshop_test_app',ROOT/'api/app.py')
        cls.app=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.app)
        cls.app.initialize()
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),cls.app.Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def call(self,path,data=None,key=None):
        headers={'Content-Type':'application/json','X-Request-ID':'contract-test'}
        if key: headers['Idempotency-Key']=key
        req=Request(self.base+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
        try:
            response=urlopen(req,timeout=5)
        except HTTPError as exc:
            response=exc
        with response:
            return response.status,json.loads(response.read())

    def test_health_and_products(self):
        self.assertEqual(self.call('/healthz')[0],200)
        self.assertEqual(self.call('/readyz')[0],200)
        status,data=self.call('/api/products')
        self.assertEqual(status,200)
        self.assertEqual(len(data['products']),3)
        self.assertEqual(data['source'],'database')

    def test_idempotency_conflict_and_read(self):
        data={'product_id':1,'quantity':2}
        status,result=self.call('/api/orders',data,'same-order')
        self.assertEqual(status,201)
        order_id=result['order']['id']
        self.assertEqual(self.call('/api/orders',data,'same-order')[1]['order']['id'],order_id)
        self.assertEqual(self.call('/api/orders',{'product_id':1,'quantity':3},'same-order')[0],409)
        self.assertEqual(self.call('/api/orders/'+order_id)[1]['order']['quantity'],2)

    def test_concurrent_retry_creates_one_order(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            results=list(pool.map(lambda _: self.call('/api/orders',{'product_id':2,'quantity':1},'concurrent-key'),range(6)))
        self.assertEqual(sum(status==201 for status,_ in results),1)
        self.assertEqual(len({data['order']['id'] for _,data in results}),1)

    def test_input_validation(self):
        for body,key in [({'product_id':1,'quantity':0},'invalid'),({'product_id':1,'quantity':True},'bool'),({'product_id':1,'quantity':1},None),([], 'array')]:
            self.assertEqual(self.call('/api/orders',body,key)[0],400)
        self.assertEqual(self.call('/api/orders',{'product_id':999,'quantity':1},'missing')[0],404)

    def test_optional_external_failure_is_degraded(self):
        status,data=self.call('/api/description')
        self.assertEqual(status,200)
        self.assertTrue(data['degraded'])
        self.assertEqual(self.call('/api/products')[0],200)

    def test_shutdown_changes_readiness(self):
        self.app.STOPPING.set()
        try:
            self.assertEqual(self.call('/readyz')[0],503)
            self.assertEqual(self.call('/healthz')[0],200)
        finally:
            self.app.STOPPING.clear()


if __name__=='__main__':
    unittest.main(verbosity=2)
