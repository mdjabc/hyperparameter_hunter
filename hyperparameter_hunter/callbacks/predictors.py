##################################################
# Import Own Assets
##################################################
from hyperparameter_hunter.callbacks.bases import BasePredictorCallback

##################################################
# Import Miscellaneous Assets
##################################################
import numpy as np
import pandas as pd


class PredictorOOF(BasePredictorCallback):
    final_oof_predictions: pd.DataFrame
    repetition_oof_predictions: pd.DataFrame
    run_validation_predictions: pd.DataFrame
    validation_index: list
    experiment_params = dict

    def on_experiment_start(self):
        self.final_oof_predictions = self.__zeros_df()
        super().on_experiment_start()

    def on_repetition_start(self):
        self.repetition_oof_predictions = self.__zeros_df()
        super().on_repetition_start()

    def on_run_end(self):
        self.run_validation_predictions = self.model.predict(self.fold_validation_input)
        self.run_validation_predictions = _format_predictions(
            self.run_validation_predictions, self.target_column, index=self.validation_index
        )

        self.repetition_oof_predictions.iloc[
            self.validation_index
        ] += self.run_validation_predictions

        super().on_run_end()

    def on_fold_end(self):
        self.repetition_oof_predictions.iloc[self.validation_index] /= self.experiment_params[
            "runs"
        ]
        super().on_fold_end()

    def on_repetition_end(self):
        self.final_oof_predictions += self.repetition_oof_predictions
        super().on_repetition_end()

    def on_experiment_end(self):
        self.final_oof_predictions /= self.cv_params.get("n_repeats", 1)
        super().on_experiment_end()

    def __zeros_df(self):
        return pd.DataFrame(0, index=np.arange(len(self.train_dataset)), columns=self.target_column)


class PredictorHoldout(BasePredictorCallback):
    final_holdout_predictions: pd.DataFrame
    repetition_holdout_predictions: pd.DataFrame
    fold_holdout_predictions: pd.DataFrame
    run_holdout_predictions: pd.DataFrame
    experiment_params: dict

    def on_experiment_start(self):
        self.final_holdout_predictions = 0
        super().on_experiment_start()

    def on_repetition_start(self):
        self.repetition_holdout_predictions = 0
        super().on_repetition_start()

    def on_fold_start(self):
        self.fold_holdout_predictions = 0
        super().on_fold_start()

    def on_run_end(self):
        self.run_holdout_predictions = self.model.predict(self.fold_holdout_input)
        self.run_holdout_predictions = _format_predictions(
            self.run_holdout_predictions, self.target_column
        )

        self.fold_holdout_predictions += self.run_holdout_predictions
        super().on_run_end()

    def on_fold_end(self):
        self.fold_holdout_predictions /= self.experiment_params["runs"]
        self.repetition_holdout_predictions += self.fold_holdout_predictions
        super().on_fold_end()

    def on_repetition_end(self):
        self.repetition_holdout_predictions /= self.cv_params["n_splits"]
        self.final_holdout_predictions += self.repetition_holdout_predictions
        super().on_repetition_end()

    def on_experiment_end(self):
        self.final_holdout_predictions /= self.cv_params.get("n_repeats", 1)
        super().on_experiment_end()


class PredictorTest(BasePredictorCallback):
    final_test_predictions: pd.DataFrame
    repetition_test_predictions: pd.DataFrame
    fold_test_predictions: pd.DataFrame
    run_test_predictions: pd.DataFrame
    experiment_params: dict

    def on_experiment_start(self):
        self.final_test_predictions = 0
        super().on_experiment_start()

    def on_repetition_start(self):
        self.repetition_test_predictions = 0
        super().on_repetition_start()

    def on_fold_start(self):
        self.fold_test_predictions = 0
        super().on_fold_start()

    def on_run_end(self):
        self.run_test_predictions = self.model.predict(self.fold_test_input)
        self.run_test_predictions = _format_predictions(
            self.run_test_predictions, self.target_column
        )

        self.fold_test_predictions += self.run_test_predictions
        super().on_run_end()

    def on_fold_end(self):
        self.fold_test_predictions /= self.experiment_params["runs"]
        self.repetition_test_predictions += self.fold_test_predictions
        super().on_fold_end()

    def on_repetition_end(self):
        self.repetition_test_predictions /= self.cv_params["n_splits"]
        self.final_test_predictions += self.repetition_test_predictions
        super().on_repetition_end()

    def on_experiment_end(self):
        self.final_test_predictions /= self.cv_params.get("n_repeats", 1)
        super().on_experiment_end()


def _format_predictions(predictions, target_column, index=None, dtype=np.float64):
    """Organize predictions into a standard format, and one-hot encode predictions as necessary

    Parameters
    ----------
    predictions: Array-like
        A model's predictions for a set of input data
    target_column: List
        A list of one or more strings corresponding to the name(s) of target output column(s)
    index: Array-like, or None, default=None
        Index to use for the resulting DataFrame. Defaults to `numpy.arange(len(predictions))`
    dtype: Dtype, or None, default=`numpy.float64`
        Datatype to force on `predictions`. If None, datatype will be inferred

    Returns
    -------
    predictions: `pandas.DataFrame`
        Formatted DataFrame containing `predictions` that has been one-hot encoded if necessary

    Examples
    --------
    >>> _format_predictions(np.array([3.2, 14.5, 6.8]), ["y"])
          y
    0   3.2
    1  14.5
    2   6.8
    >>> _format_predictions(np.array([1, 0, 1]), ["y"])
         y
    0  1.0
    1  0.0
    2  1.0
    >>> _format_predictions(np.array([2, 1, 0]), ["y_0", "y_1", "y_2"], dtype=np.int8)
       y_0  y_1  y_2
    0    0    0    1
    1    0    1    0
    2    1    0    0"""
    # `target_column` indicates multidimensional output, but predictions are one-dimensional
    if (len(target_column) > 1) and ((len(predictions.shape) == 1) or (predictions.shape[1] == 1)):
        predictions = pd.get_dummies(predictions).values

    predictions = pd.DataFrame(data=predictions, index=index, columns=target_column, dtype=dtype)
    return predictions


if __name__ == "__main__":
    pass
