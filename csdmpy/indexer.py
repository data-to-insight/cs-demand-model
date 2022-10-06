import pandas as pd

from csdmpy.constants import AgeBracket


class TransitionLevels:
    """
    Utility for creating all the common "transition" levels we have in the dataframe.

    This can go to two or three levels: two for populations, and three for transitions.

    Returns tuples of the form (AgeBracket, PlacementCategory, PlacementCategory) - if instead you want
    Pandas Indexes, use TransitionIndexes.
    """

    @staticmethod
    def transitions_all(exclude_self=False, levels=3):
        """
        Returns all the allowed transitions between placement categories, except NOT_IN_CARE.

        Optionally you can exclude the "self" transitions, such as Fostering -> Fostering by passing exclude_self=True.

        If levels=2, then the third element of the tuple is omitted.
        """
        for age_bin in AgeBracket:
            for pt1 in age_bin.placement_categories:
                if levels == 2:
                    yield age_bin, pt1
                else:
                    for pt2 in age_bin.placement_categories:
                        if not (exclude_self and pt1 == pt2):
                            yield age_bin, pt1, pt2

    @staticmethod
    def transitions_self():
        """
        Returns only the self-transitions, e.g. Fostering -> Fostering for all age brackets.
        """
        for age_bin in AgeBracket:
            for pt1 in age_bin.placement_categories:
                yield age_bin, pt1, pt1


class TransitionIndexes:
    """
    Utility for creating all the common "transition" levels we have in the dataframe.

    This can go to two or three levels: two for populations, and three for transitions.

    Returns MultiIndex of the form (AgeBracket, PlacementCategory, PlacementCategory) - if instead you want
    tuples, use TransitionLevels.
    """

    __levels = TransitionLevels()

    @staticmethod
    def transitions_all(exclude_self=False, levels=3):
        return TransitionIndexes.mix(TransitionIndexes.__levels.transitions_all(exclude_self, levels))

    @staticmethod
    def transitions_self():
        return TransitionIndexes.mix(TransitionIndexes.__levels.transitions_self())

    @staticmethod
    def mix(source):
        source = list(source)
        if len(source[0]) == 2:
            names = ['age_bin', 'placement_type']
        else:
            names = ['age_bin', 'placement_type', 'placement_type_after']
        return pd.MultiIndex.from_tuples(source, names=names)



