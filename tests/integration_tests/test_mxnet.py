import numpy as np

import pytest

try:
    import mxnet as mx
    _available = True
except ImportError:
    _available = False

import optuna
from optuna.integration import MxnetPruningCallback
from optuna.testing.integration import DeterministicPruner


def test_mxnet_pruning_callback():
    # type: () -> None

    if not _available:
        pytest.skip('This test requires mxnet '
                    'but this version can not install mxnet with pip.')

    def objective(trial):
        # type: (optuna.trial.Trial) -> float

        # Symbol
        data = mx.symbol.Variable('data')
        data = mx.symbol.FullyConnected(data=data, num_hidden=1)
        data = mx.symbol.Activation(data=data, act_type="sigmoid")
        mlp = mx.symbol.SoftmaxOutput(data=data, name="softmax")

        # Optimizer
        optimizer = mx.optimizer.RMSProp()

        # Dataset
        train = mx.io.NDArrayIter(data=np.zeros((16, 20), np.float32),
                                  label=np.zeros((16,), np.int32),
                                  batch_size=1,
                                  shuffle=True)

        model = mx.mod.Module(symbol=mlp)
        model.fit(train_data=train,
                  optimizer=optimizer,
                  num_epoch=1,
                  batch_end_callback=MxnetPruningCallback(trial, 'accuracy'))
        return 1.0

    study = optuna.create_study(pruner=DeterministicPruner(True))
    study.optimize(objective, n_trials=1)
    assert study.trials[0].state == optuna.structs.TrialState.PRUNED

    study = optuna.create_study(pruner=DeterministicPruner(False))
    study.optimize(objective, n_trials=1)
    assert study.trials[0].state == optuna.structs.TrialState.COMPLETE
    assert study.trials[0].value == 1.0
