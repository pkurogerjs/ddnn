import sys
sys.path.append('..')

import chainer

from elaas.elaas import Collection
from elaas.family.simple import SimpleHybridFamily
import deepopt.chooser
save_dir = '/mnt/data/'

mnist = Collection('simple_hybrid', nepochs=10)
mnist.set_model_family(SimpleHybridFamily(folder=save_dir))
train, test = chainer.datasets.get_mnist(ndim=3)

mnist.add_trainset(train)
mnist.add_testset(test)

# switch model family
# mnist.set_model_family()
mnist.set_searchspace(
    nfilters_embeded=[1,2],
    nlayers_embeded=[1,2],
    nfilters_cloud=[1,2],
    nlayers_cloud=[1,2],
    lr=[0.001],
    branchweight=[.1]
)

def constraintfn(**kwargs):
    #TODO: change to memory cost
    if kwargs['nfilters_embeded'] > 2:
        return False

    return True

mnist.set_constraints(constraintfn)
# switch chooser
mnist.set_chooser(deepopt.chooser.GridChooser())

# currently optimize based on the validation accuracy of the main model
traces = mnist.train()
visualize(traces)

# generate c
# mnist.generate_c((1,28,28))

# generate container
# mnist.generate_container()
