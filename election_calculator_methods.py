from qgis.core import NULL

import numpy as np

def method_dhondt(layer, fields: list[str], seats_count_field):

    result = {}

    for feature in layer.getFeatures():
        votes_counts = []

        for field in fields:
            votes_counts.append(feature[field])

        seats = feature[seats_count_field]

        quotients = []
        for i in range(1, seats+1):
            quotient = []

            for j in votes_counts:
                if isinstance(j, int):
                    quotient.append(j / i)
                else:
                    quotient.append(-1)

            quotients.append(quotient)

        quotient_array = np.array(quotients)
        ix, jx = np.unravel_index(quotient_array.argsort(axis=None), quotient_array.shape)

        quotient_indexes = list(zip(ix, jx))
        quotient_indexes.reverse()
        seats_quotient_indexes = quotient_indexes[0:seats]

        feature_result = {}
        for _, y in seats_quotient_indexes:
            feature_result[y] = feature_result.get(y, 0) + 1

        result[feature.id()] = feature_result

    return result

def method_sainte_lague(layer, fields: list[str], seats_count_field):

    result = {}

    for feature in layer.getFeatures():
        votes_counts = []

        for field in fields:
            votes_counts.append(feature[field])

        seats = feature[seats_count_field]

        quotients = []
        for i in range(1, seats + 1, 2):
            quotient = []

            for j in votes_counts:
                if isinstance(j, int):
                    quotient.append(j / i)
                else:
                    quotient.append(-1)

            quotients.append(quotient)

        quotient_array = np.array(quotients)
        ix, jx = np.unravel_index(quotient_array.argsort(axis=None), quotient_array.shape)

        quotient_indexes = list(zip(ix, jx))
        quotient_indexes.reverse()
        seats_quotient_indexes = quotient_indexes[0:seats]

        feature_result = {}
        for _, y in seats_quotient_indexes:
            feature_result[y] = feature_result.get(y, 0) + 1

        result[feature.id()] = feature_result

    return result

def method_hare_niemeyer(layer, fields: list[str], seats_count_field):

    result = {}

    for feature in layer.getFeatures():
        votes_counts = []

        for field in fields:
            votes_counts.append(feature[field])

        seats = feature[seats_count_field]

        feature_result = {}

        seats_assigned = 0
        seats_rests = []

        votes_ = [v for v in votes_counts if v != NULL]
        for idx, votes in enumerate(votes_counts):
            if not isinstance(votes, int):
                votes = 0

            seats_ = ((votes * seats) / sum(votes_) )
            seats_assigned += int(seats_)

            feature_result[idx] = int(seats_)
            seats_rests.append(seats_ - int(seats_))

        while seats_assigned < seats:
            idx = seats_rests.index(max(seats_rests))
            feature_result[idx] += 1
            seats_rests.pop(idx)
            seats_assigned += 1

        result[feature.id()] = feature_result

    return result