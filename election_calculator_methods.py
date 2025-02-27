from qgis.core import QgsMapLayer, NULL

import numpy as np

class ElectionCalculatorSeatsDistributor:
    def __init__(self, layer: QgsMapLayer, fields: list[str], seats_count_field: str):
        self.layer = layer
        self.fields = fields
        self.seats_count_field = seats_count_field

    def calculate(self, method):
        result = {}

        for feature in self.layer.getFeatures():
            votes_by_party = []

            for field in self.fields:
                votes_by_party.append(feature[field])

            feature_seats = feature[self.seats_count_field]
            feature_result = method(feature_seats, votes_by_party)

            result[feature.id()] = feature_result

        return result

    def dhondt(self, seats: int, votes: list):
        return self._calculate_seats_by_quotients(seats, votes)

    def sainte_lague(self, seats: int, votes: list):
        return self._calculate_seats_by_quotients(seats, votes, 2)

    def hare_niemeyer(self, seats: int, votes: list):
        return self._calculate_seats_by_remainders(seats, votes)

    def _calculate_seats_by_quotients(self, seats: int, votes: list, step: int = 1):
        quotients = []
        for i in range(1, seats+1, step):
            quotient = []

            for j in votes:
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

        result = {}
        for _, y in seats_quotient_indexes:
            result[y] = result.get(y, 0) + 1

        return result

    def _calculate_seats_by_remainders(self, seats: int, votes: list):
        result = {}

        seats_assigned = 0
        seats_remainders = []

        votes_without_nulls = [v for v in votes if v != NULL]
        for idx, votes in enumerate(votes):
            if not isinstance(votes, int):
                votes = 0

            seats_ = ((votes * seats) / sum(votes_without_nulls))
            seats_assigned += int(seats_)

            result[idx] = int(seats_)
            seats_remainders.append(seats_ - int(seats_))

        while seats_assigned < seats:
            idx = seats_remainders.index(max(seats_remainders))
            result[idx] += 1
            seats_remainders.pop(idx)
            seats_assigned += 1

        return result

# def method_dhondt(layer, fields: list[str], seats_count_field):
#
#     result = {}
#
#     for feature in layer.getFeatures():
#         votes_counts = []
#
#         for field in fields:
#             votes_counts.append(feature[field])
#
#         seats = feature[seats_count_field]
#         feature_result = {}
#
#         quotients = []
#         for i in range(1, seats+1):
#             quotient = []
#
#             for j in votes_counts:
#                 if isinstance(j, int):
#                     quotient.append(j / i)
#                 else:
#                     quotient.append(-1)
#
#             quotients.append(quotient)
#
#         quotient_array = np.array(quotients)
#         ix, jx = np.unravel_index(quotient_array.argsort(axis=None), quotient_array.shape)
#
#         quotient_indexes = list(zip(ix, jx))
#         quotient_indexes.reverse()
#         seats_quotient_indexes = quotient_indexes[0:seats]
#
#         for _, y in seats_quotient_indexes:
#             feature_result[y] = feature_result.get(y, 0) + 1
#
#         result[feature.id()] = feature_result
#
#     return result
#
# def method_sainte_lague(layer, fields: list[str], seats_count_field):
#
#     result = {}
#
#     for feature in layer.getFeatures():
#         votes_counts = []
#
#         for field in fields:
#             votes_counts.append(feature[field])
#
#         seats = feature[seats_count_field]
#         feature_result = {}
#
#         quotients = []
#         for i in range(1, seats + 1, 2):
#             quotient = []
#
#             for j in votes_counts:
#                 if isinstance(j, int):
#                     quotient.append(j / i)
#                 else:
#                     quotient.append(-1)
#
#             quotients.append(quotient)
#
#         quotient_array = np.array(quotients)
#         ix, jx = np.unravel_index(quotient_array.argsort(axis=None), quotient_array.shape)
#
#         quotient_indexes = list(zip(ix, jx))
#         quotient_indexes.reverse()
#         seats_quotient_indexes = quotient_indexes[0:seats]
#
#         for _, y in seats_quotient_indexes:
#             feature_result[y] = feature_result.get(y, 0) + 1
#
#         result[feature.id()] = feature_result
#
#     return result
#
# def method_hare_niemeyer(layer, fields: list[str], seats_count_field):
#
#     result = {}
#
#     for feature in layer.getFeatures():
#         votes_counts = []
#
#         for field in fields:
#             votes_counts.append(feature[field])
#
#         seats = feature[seats_count_field]
#         feature_result = {}
#
#         seats_assigned = 0
#         seats_rests = []
#
#         votes_ = [v for v in votes_counts if v != NULL]
#         for idx, votes in enumerate(votes_counts):
#             if not isinstance(votes, int):
#                 votes = 0
#
#             seats_ = ((votes * seats) / sum(votes_) )
#             seats_assigned += int(seats_)
#
#             feature_result[idx] = int(seats_)
#             seats_rests.append(seats_ - int(seats_))
#
#         while seats_assigned < seats:
#             idx = seats_rests.index(max(seats_rests))
#             feature_result[idx] += 1
#             seats_rests.pop(idx)
#             seats_assigned += 1
#
#         result[feature.id()] = feature_result
#
#     return result
