import json
import math
import numpy as np

from deeppavlov import build_model
from pathlib import Path

class ContextSearchModel:
    _CONFIG_FILE_NAME = 'model_config_squad_bert.json'

    def __init__(self):
        self.model_config_path = Path(__file__).absolute().parent / self._CONFIG_FILE_NAME
        with open(self.model_config_path, 'r') as file:
            model_config = json.load(file)
            self._model = build_model(model_config, download=True)
    
    def predict(self, *values):
        '''
        Predicts the answer to a question given a context.

        :param values:
            A list of two-dimensional tuples containing two strings: the context and question.

        :returns:
            A list of tuples containing the predicated answer, predicated start index of answer, probability of answer, logits for answer
        '''

        contexts = []
        questions = []

        for query in values:
            contexts.append(query[0])
            questions.append(query[1])
   
        predictions_answers, predictions_start_indices, predictions_logits = self._model(contexts, questions)
        predictions = []
        for i in range(len(predictions_answers)):
            answer, start_index, logit = predictions_answers[i], predictions_start_indices[i], predictions_logits[i] 
            odds = np.exp(logit)

            # If the logit is TOO BIG for numpy to compute, we say that it has a 100% probability.
            # In reality, it doesn't...but, it certainly is very close.
            probability = odds / (1 + odds) if not np.isposinf(odds) else 1
            predictions.append((answer, start_index, probability, logit))

        return predictions
