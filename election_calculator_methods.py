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
            if not isinstance(feature_seats, int) or feature_seats <= 0:
                return None

            feature_result = method(feature_seats, votes_by_party)

            result[feature.id()] = feature_result

        return result

    def dhondt(self, seats: int, votes: list):
        return self._calculate_seats_by_quotients(seats, votes)

    def sainte_lague(self, seats: int, votes: list):
        return self._calculate_seats_by_quotients(seats, votes, 2)

    def sainte_lague_scandinavian(self, seats: int, votes: list):
        return self._calculate_seats_by_quotients(seats, votes, 2, 0.4)

    def hare_niemeyer(self, seats: int, votes: list):
        return self._calculate_seats_by_remainders(seats, votes)

    def _calculate_seats_by_quotients(self, seats: int, votes: list, step: int = 1, first_quotient_modifier: float = 0.0):
        votes_idx = [i for i in range(0, len(votes))]

        results = {party: 0 for party in votes_idx}
        divisors = {party: 1 + first_quotient_modifier for party in votes_idx}

        for _ in range(seats):
            best_party = max(votes_idx, key=lambda p: votes[p] / divisors[p] if isinstance(votes[p], int) else -1 / divisors[p])
            results[best_party] += 1
            if divisors[best_party] == 1 + first_quotient_modifier:
                divisors[best_party] += (1 + step) - (1 + first_quotient_modifier)
            else:
                divisors[best_party] += step

        return results

    def _calculate_seats_by_remainders(self, seats: int, votes: list):
        votes_without_nulls = [v for v in votes if v != NULL]
        total_votes = sum(votes_without_nulls)

        quotas = {party: (votes_without_nulls[party] / total_votes) * seats for party in votes}
        results = {party: int(quotas[party]) for party in votes}
        remaining_seats = seats - sum(results.values())

        fractional_parts = sorted(((party, quotas[party] - results[party]) for party in votes), key=lambda x: x[1],
                                  reverse=True)

        for i in range(remaining_seats):
            results[fractional_parts[i][0]] += 1

        return results
