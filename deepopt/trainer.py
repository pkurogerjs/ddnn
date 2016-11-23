from chainer import training
from chainer.training import extensions
import chainer.serializers as S
import chainer
import os
import json

class Trainer(object):
    def __init__(self, folder, chain, train, test, batchsize=1024, resume=True, gpu=0, nepoch=1):
        self.nepoch = nepoch
        self.folder = folder

        if gpu >= 0:
            chainer.cuda.get_device(gpu).use()
            chain.to_gpu(gpu)
        eval_chain = chain.copy()
        eval_chain.test = True

        if not os.path.exists(folder):
            os.makedirs(folder)

        train_iter = chainer.iterators.SerialIterator(train, batchsize)
        test_iter = chainer.iterators.SerialIterator(test, batchsize,
                                                     repeat=False, shuffle=False)

        updater = training.StandardUpdater(train_iter, chain.optimizer, device=gpu)
        trainer = training.Trainer(updater, (nepoch, 'epoch'), out=folder)
        # trainer.extend(TrainingModeSwitch(chain))
        trainer.extend(extensions.Evaluator(test_iter, eval_chain, device=gpu))
        trainer.extend(extensions.snapshot_object(
            chain, 'chain_snapshot_epoch_{.updater.epoch:06}'), trigger=(1,'epoch'))
        trainer.extend(extensions.snapshot(
            filename='snapshot_epoch_{.updater.epoch:06}'), trigger=(1,'epoch'))
        trainer.extend(extensions.LogReport(trigger=(1,'epoch')))
        # trainer.extend(extensions.PrintReport(
        #     ['epoch', 'main/loss', 'validation/main/loss',
        #      'main/accuracy', 'validation/main/accuracy']))

        if resume:
            i = 1
            trainerFile = os.path.join(folder,'snapshot_epoch_{:06}'.format(i))
            while i <= nepoch and os.path.isfile(trainerFile):
                i = i + 1
                trainerFile = os.path.join(folder,'snapshot_epoch_{:06}'.format(i))
            i = i - 1
            trainerFile = os.path.join(folder,'snapshot_epoch_{:06}'.format(i))
            if i >= 0 and os.path.isfile(trainerFile):
                S.load_npz(trainerFile, trainer)

        self.trainer = trainer

    def run(self):
        self.trainer.run()
        ext = self.trainer.get_extension('validation')()
        test_accuracy = ext['validation/main/accuracy']
        test_loss = ext['validation/main/loss']
        acc = test_accuracy.tolist()
        loss = test_loss.tolist()
        return acc,loss

    def get_result(self, key):
        ext = self.trainer.get_extension('validation')()
        return ext['{}'.format(key)].tolist()

    def get_log_result(self, key):
        folder = self.folder
        nepoch = self.nepoch
        with open(os.path.join(folder,'log'),'r') as f:
            log = json.load(f)
        return [v[key] for v in log][:nepoch]
