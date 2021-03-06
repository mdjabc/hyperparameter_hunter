##################################################
# Import Own Assets
##################################################
from hyperparameter_hunter import Environment, CVExperiment
from hyperparameter_hunter.callbacks.recipes import dataset_recorder
from hyperparameter_hunter.feature_engineering import FeatureEngineer

##################################################
# Import Miscellaneous Assets
##################################################
from numpy.testing import assert_array_almost_equal
import pandas as pd
import pytest

##################################################
# Import Learning Assets
##################################################
from sklearn.linear_model import Ridge
from sklearn.preprocessing import QuantileTransformer

##################################################
# Dummy Objects for Testing
##################################################
boston_cols = [
    "CRIM",
    "ZN",
    "INDUS",
    "CHAS",
    "NOX",
    "RM",
    "AGE",
    "DIS",  # Target column
    "RAD",
    "TAX",
    "PTRATIO",
    "B",
    "LSTAT",
    "MEDV",
]
#                                                \/ DIS \/
boston_head_data = [
    [0.00632, 18.0, 2.31, 0.0, 0.538, 6.575, 65.2, 4.0900, 1.0, 296.0, 15.3, 396.90, 4.98, 24.0],
    [0.02731, 0.0, 7.07, 0.0, 0.469, 6.421, 78.9, 4.9671, 2.0, 242.0, 17.8, 396.90, 9.14, 21.6],
    [0.02729, 0.0, 7.07, 0.0, 0.469, 7.185, 61.1, 4.9671, 2.0, 242.0, 17.8, 392.83, 4.03, 34.7],
    [0.03237, 0.0, 2.18, 0.0, 0.458, 6.998, 45.8, 6.0622, 3.0, 222.0, 18.7, 394.63, 2.94, 33.4],
    # [0.06905, 0.0, 2.18, 0.0, 0.458, 7.147, 54.2, 6.0622, 3.0, 222.0, 18.7, 396.90, 5.33, 36.2],
]
boston_head = pd.DataFrame(data=boston_head_data, columns=boston_cols)
boston_head_inputs = boston_head.copy().drop(["DIS"], axis=1)
boston_head_targets = boston_head.copy().loc[:, ["DIS"]]

normal_train_inputs = [
    boston_head_inputs.iloc[[1, 2], :],
    boston_head_inputs.iloc[[0, 2], :],
    boston_head_inputs.iloc[[0, 1], :],
]
normal_train_targets = [
    boston_head_targets.iloc[[1, 2], :],
    boston_head_targets.iloc[[0, 2], :],
    boston_head_targets.iloc[[0, 1], :],
]
normal_validation_inputs = [
    boston_head_inputs.iloc[[0], :],
    boston_head_inputs.iloc[[1], :],
    boston_head_inputs.iloc[[2], :],
]
normal_validation_targets = [
    boston_head_targets.iloc[[0], :],
    boston_head_targets.iloc[[1], :],
    boston_head_targets.iloc[[2], :],
]
normal_holdout_inputs = [boston_head_inputs.iloc[[3], :]] * 3
normal_holdout_targets = [boston_head_targets.iloc[[3], :]] * 3

engineered_train_targets = [
    pd.DataFrame(dict(DIS=[0.0, 0.0])),
    pd.DataFrame(dict(DIS=[0.0, 0.999999])),
    pd.DataFrame(dict(DIS=[0.0, 0.999999])),
]
engineered_validation_targets = [
    pd.DataFrame(dict(DIS=[0.0])),
    pd.DataFrame(dict(DIS=[1.0])),
    pd.DataFrame(dict(DIS=[1.0])),
]
engineered_holdout_targets = [
    pd.DataFrame(dict(DIS=[1.0])),
    pd.DataFrame(dict(DIS=[1.0])),
    pd.DataFrame(dict(DIS=[1.0])),
]


# noinspection PyUnusedLocal
def holdout_last_row(train_dataset, target_column):
    return train_dataset.iloc[0:-1, :], train_dataset.iloc[[-1], :]


def my_quantile_transform(train_targets, non_train_targets):
    transformer = QuantileTransformer(output_distribution="uniform")
    train_targets[train_targets.columns] = transformer.fit_transform(train_targets.values)
    non_train_targets[train_targets.columns] = transformer.transform(non_train_targets.values)
    return train_targets, non_train_targets


@pytest.fixture
def boston_head_env_fixture():
    return Environment(
        train_dataset=boston_head,
        holdout_dataset=holdout_last_row,
        target_column="DIS",
        metrics=["r2_score", "median_absolute_error"],
        cv_type="KFold",
        cv_params=dict(n_splits=3, random_state=1),
        experiment_callbacks=[dataset_recorder(save_transformed=True)],
    )


@pytest.fixture
def intra_cv_experiment_fixture(request):
    feature_engineer = FeatureEngineer(steps=request.param)
    experiment = CVExperiment(
        model_initializer=Ridge, model_init_params=dict(), feature_engineer=feature_engineer
    )
    return experiment


@pytest.mark.parametrize(
    ["intra_cv_experiment_fixture", "end_data"],
    [
        [
            None,
            [
                normal_train_inputs,
                normal_train_targets,
                normal_validation_inputs,
                normal_validation_targets,
                normal_holdout_inputs,
                normal_holdout_targets,
            ],
        ],
        [
            [my_quantile_transform],
            [
                normal_train_inputs,
                engineered_train_targets,
                normal_validation_inputs,
                engineered_validation_targets,
                normal_holdout_inputs,
                engineered_holdout_targets,
            ],
        ],
    ],
    indirect=["intra_cv_experiment_fixture"],
)
def test_all_wrangled_targets(boston_head_env_fixture, intra_cv_experiment_fixture, end_data):
    agg_datasets = intra_cv_experiment_fixture.stat_aggregates["_datasets"]

    for f, datasets in enumerate(agg_datasets["on_fold_end"]):
        assert_array_almost_equal(datasets["fold_train_input"], end_data[0][f])
        assert_array_almost_equal(datasets["fold_train_target"], end_data[1][f])
        assert_array_almost_equal(datasets["fold_validation_input"], end_data[2][f])
        assert_array_almost_equal(datasets["fold_validation_target"], end_data[3][f])
        assert_array_almost_equal(datasets["fold_holdout_input"], end_data[4][f])
        assert_array_almost_equal(datasets["fold_holdout_target"], end_data[5][f])
