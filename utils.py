from genericpath import exists
from sklearn import metrics as skmetr
from datetime import datetime
import numpy as np
import copy
import glob
import os
import torch

class Option(object):
      
    def __init__(self, my_dict):
        self.dict = my_dict
        for key in my_dict:
            setattr(self, key, my_dict[key])

    def copy(self):
        return Option(copy.deepcopy(self.dict))


def metricSummer(metricss, type):
    meanMetrics_seeds = []
    meanMetric_all = {}
    stdMetrics_seeds = []
    stdMetric_all = {}

    for metrics in metricss:  # this is over different seeds
        meanMetric = {}
        stdMetric = {}

        for metric in metrics:  # this is over different folds
            metric = metric[type]  # get results from the specified type

            for key in metric.keys():
                if key not in meanMetric:
                    meanMetric[key] = []

                meanMetric[key].append(metric[key])

        for key in meanMetric:
            stdMetric[key] = np.std(meanMetric[key])
            meanMetric[key] = np.mean(meanMetric[key])

        meanMetrics_seeds.append(meanMetric)
        stdMetrics_seeds.append(stdMetric)

    for key in meanMetrics_seeds[0].keys():
        meanMetric_all[key] = np.mean([metric[key] for metric in meanMetrics_seeds])
        stdMetric_all[key] = np.mean([metric[key] for metric in stdMetrics_seeds])

    return meanMetrics_seeds, stdMetrics_seeds, meanMetric_all, stdMetric_all


def calculateMetric(result):
    labels = result["labels"]
    predictions = result["predictions"]

    isMultiClass = np.max(labels) > 1
    hasProbs = "probs" in result

    if hasProbs:
        probs = result["probs"]

    try:
        accuracy = skmetr.accuracy_score(labels, predictions)
    except Exception as e:
        accuracy = np.nan

    if isMultiClass:
        try:
            precision = skmetr.precision_score(labels, predictions, average="micro")
        except Exception as e:
            precision = np.nan

        try:
            recall = skmetr.recall_score(labels, predictions, average="micro")
        except Exception as e:
            recall = np.nan

        if hasProbs:
            try:
                roc = skmetr.roc_auc_score(labels, probs, average="macro", multi_class="ovr")
            except Exception as e:
                roc = np.nan
        else:
            roc = np.nan
    else:
        try:
            precision = skmetr.precision_score(labels, predictions, average="binary")
        except Exception as e:
            precision = np.nan

        try:
            recall = skmetr.recall_score(labels, predictions, average="binary")
        except Exception as e:
            recall = np.nan

        if hasProbs:
            try:
                roc = skmetr.roc_auc_score(labels, probs[:, 1])
            except Exception as e:
                roc = np.nan
        else:
            roc = np.nan

    return {"accuracy": accuracy, "precision": precision, "recall": recall, "roc": roc}


def calculateMetrics(resultss):
    metricss = []

    for results in resultss:
        metrics = []

        for result in results:
            train_results = result["train"]
            test_results = result["test"]

            train_labels = train_results["labels"]
            train_predictions = train_results["predictions"]
            train_probs = train_results["probs"] if "probs" in train_results else None
            train_loss = train_results["loss"]

            test_labels = test_results["labels"]
            test_predictions = test_results["predictions"]
            test_probs = test_results["probs"] if "probs" in test_results else None
            test_loss = test_results["loss"]

            isMultiClass = np.max(test_labels) > 1
            hasProbs = "probs" in train_results

            # metrics
            try:
                train_accuracy = skmetr.accuracy_score(train_labels, train_predictions)
            except Exception as e:
                train_accuracy = np.nan

            try:
                test_accuracy = skmetr.accuracy_score(test_labels, test_predictions)
            except Exception as e:
                test_accuracy = np.nan

            if isMultiClass:
                try:
                    train_precision = skmetr.precision_score(train_labels, train_predictions, average="micro")
                except Exception as e:
                    train_precision = np.nan

                try:
                    test_precision = skmetr.precision_score(test_labels, test_predictions, average="micro")
                except Exception as e:
                    test_precision = np.nan

                try:
                    train_recall = skmetr.recall_score(train_labels, train_predictions, average="micro")
                except Exception as e:
                    train_recall = np.nan

                try:
                    test_recall = skmetr.recall_score(test_labels, test_predictions, average="micro")
                except Exception as e:
                    test_recall = np.nan

                if hasProbs:
                    try:
                        train_roc = skmetr.roc_auc_score(train_labels, train_probs, average="macro", multi_class="ovr")
                    except Exception as e:
                        train_roc = np.nan

                    try:
                        test_roc = skmetr.roc_auc_score(test_labels, test_probs, average="macro", multi_class="ovr")
                    except Exception as e:
                        test_roc = np.nan
                else:
                    train_roc = np.nan
                    test_roc = np.nan
            else:
                try:
                    train_precision = skmetr.precision_score(train_labels, train_predictions, average="binary")
                except Exception as e:
                    train_precision = np.nan

                try:
                    test_precision = skmetr.precision_score(test_labels, test_predictions, average="binary")
                except Exception as e:
                    test_precision = np.nan

                try:
                    train_recall = skmetr.recall_score(train_labels, train_predictions, average="binary")
                except Exception as e:
                    train_recall = np.nan

                try:
                    test_recall = skmetr.recall_score(test_labels, test_predictions, average="binary")
                except Exception as e:
                    test_recall = np.nan

                if hasProbs:
                    try:
                        train_roc = skmetr.roc_auc_score(train_labels, train_probs[:, 1])
                    except Exception as e:
                        train_roc = np.nan

                    try:
                        test_roc = skmetr.roc_auc_score(test_labels, test_probs[:, 1])
                    except Exception as e:
                        test_roc = np.nan
                else:
                    train_roc = np.nan
                    test_roc = np.nan

            metric = {"train": {"accuracy": train_accuracy, "precision": train_precision, "recall": train_recall, "roc": train_roc, "loss": train_loss},
                      "test": {"accuracy": test_accuracy, "precision": test_precision, "recall": test_recall, "roc": test_roc, "loss": test_loss}}

            metrics.append(metric)

        metricss.append(metrics)

    return metricss


def dumpTestResults(testName, hyperParams, modelName, datasetName, metricss):
    datasetNameToResultFolder = {
        "abide1": "./Results/ABIDE_I",
        "hcpRest": "./Results/HCP_REST",
        "hcpTask": "./Results/HCP_TASK",
        "cobre": "./Results/COBRE",
        "hcpWM": "./Results/HCP_WM"
    }

    dumpPrepend = "{}_{}_{}".format(testName, modelName, datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))

    meanMetrics_seeds, stdMetrics_seeds, meanMetric_all, stdMetric_all = metricSummer(metricss, "test")

    targetFolder = datasetNameToResultFolder[datasetName] + "/" + modelName + "/" + testName
    os.makedirs(targetFolder, exist_ok=True)

    # text save, for human readable format
    metricFile = open(targetFolder + "/" + "metricss.txt", "w")
    metricFile.write("\n \n \n \n")
    for metrics in metricss:
        metricFile.write("\n \n")
        for metric in metrics:
            metricFile.write("\n{}".format(metric))
    metricFile.close()

    # text save of summary metrics, interprettable format
    summaryMetricFile = open(targetFolder + "/" + "summaryMetrics.txt", "w")
    # write mean metrics
    summaryMetricFile.write("\n MEAN METRICS \n \n")
    summaryMetricFile.write("{}".format(meanMetric_all))
    # write std metrics
    summaryMetricFile.write("\n \n \n STD METRICS \n \n")
    summaryMetricFile.write("{}".format(stdMetric_all))
    summaryMetricFile.close()

    # save hyper params
    hyperParamFile = open(targetFolder + "/" + "hyperParams.txt", "w")
    for key in vars(hyperParams):
        hyperParamFile.write("\n{} : {}".format(key, vars(hyperParams)[key]))
    hyperParamFile.close()

    # torch save, for visualizer
    torch.save(metricss, targetFolder + "/" + "metrics.save")
