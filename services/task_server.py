# encoding: utf-8

import tornado.web
import tornado.ioloop
import tornado.gen

import json
import time

from distributed import Executor


PORT = 63000
PORT_SCHEDULER = 63500


def report_result(result):
    print("<Post result to db etc. on success here>")
    print("Result is: {}".format(result))
    print("---")


def my_task(n):
    print("My task: running")
    time.sleep(n)
    print("My task done")
    return n


class TaskHandler(tornado.web.RequestHandler):
    def get(self, task_id):
        self.write('Querying task id {}'.format(task_id))

    @tornado.gen.coroutine
    def post(self):
        data = json.loads(self.request.body.decode('utf-8'))
        print('Request received:')
        print(data)
        print('---')

        loop = tornado.ioloop.IOLoop.current()

        ex = Executor('127.0.0.1:{}'.format(PORT_SCHEDULER), loop=loop,
                      start=False)
        yield ex._start()

        print('Submitting task')
        try:
            task = ex.submit(my_task, 2, pure=False)
        except Exception as e:
            print(e)
            self.write({'status': 'error',
                        'message': 'Failed to submit task: {}'.format(e)})
        else:
            self.write({
                'status': 'success',
                'data': {'task_id': task.key}
                })

        loop.add_future(task, report_result)


def make_app():
    return tornado.web.Application([
        (r"/task/([0-9a-z]+)?", TaskHandler),
        (r"/task", TaskHandler),
        ])


if __name__ == "__main__":
    loop = tornado.ioloop.IOLoop.current()

    from distributed import Scheduler
    s = Scheduler(loop=loop)
    s.start(PORT_SCHEDULER)
    print('Task scheduler listening on port {}'.format(PORT_SCHEDULER))

    from distributed import Worker
    w = Worker('127.0.0.1', PORT_SCHEDULER, loop=loop)
    w.start(0)
    print('Single worker activated')

    app = make_app()
    app.listen(PORT)
    print('Task server listening on port {}'.format(PORT))

    loop.start()
