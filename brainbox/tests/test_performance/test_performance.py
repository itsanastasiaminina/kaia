import uuid
from unittest import TestCase

import pandas as pd

from datetime import datetime
from brainbox.framework import BrainBoxTask,  IDecider, BrainBoxApi, SimplePlanner, AlwaysOnPlanner

class Test(IDecider):
    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass

    def __call__(self, arg):
        return f'OK-{arg}'




class BrainBoxWebServerEmptyTestCase(TestCase):
    def make_test(self, tasks, planer):
        with BrainBoxApi.Test([Test()]) as api:
            results = []
            for task in tasks:
                sent_time = datetime.now()
                _ = api.execute(task)
                arrived_time = datetime.now()
                job = api.job(task.id)
                row = job.__dict__
                row['sent_timestamp'] = sent_time
                row['result_timestamp'] = arrived_time
                del row['_sa_instance_state']
                results.append(row)

            pd.options.display.width = None
            df = pd.DataFrame(results)
            print(df)
            print(df.dtypes)
            df['sending_delta'] = (df['received_timestamp'] - df['sent_timestamp']).dt.total_seconds()
            df['queue_delta'] = (df['assigned_timestamp'] - df['received_timestamp']).dt.total_seconds()
            df['transition_delta'] = (df['accepted_timestamp'] - df['assigned_timestamp']).dt.total_seconds()
            df['processing_delta'] = (df['finished_timestamp'] - df['accepted_timestamp']).dt.total_seconds()
            df['receiving_delta'] = (df['result_timestamp'] - df['finished_timestamp']).dt.total_seconds()
            df['total_delta'] = (df['result_timestamp'] - df['sent_timestamp']).dt.total_seconds()

            delta_columns = [c for c in df.columns if '_delta' in c]
            #print(df[delta_columns])
            print(df[delta_columns].iloc[1:].mean(axis=0))

            return df

    def test_one_decider(self):
        tasks = [BrainBoxTask.call(Test)(arg=i).to_task(id=str(i)) for i in range(20)]
        self.make_test(tasks, SimplePlanner())
        #self.make_test(tasks, AlwaysOnPlanner())










