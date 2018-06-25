from decimal import *

__all__ = ["ParseMetrics", "ParseQuality"]

class ParseMetrics():
    """ Parse statistics data """
    def __init__(self, other=None):

        if other is None:
            self.completely_parsed_ratio = Decimal('0.0')
            self.completely_unparsed_ratio = Decimal('0.0')
            self.average_parsed_ratio = Decimal('0.0')
            self.sentences = int(0)
        else:
            self.completely_parsed_ratio = other.completely_parsed_ratio
            self.completely_unparsed_ratio = other.completely_unparsed_ratio
            self.average_parsed_ratio = other.average_parsed_ratio
            self.sentences = other.sentences

    @staticmethod
    def completely_parsed(stat) -> Decimal:
        if not stat.sentences:
            return Decimal("0")

        return stat.completely_parsed_ratio / stat.sentences * Decimal("100")

    @staticmethod
    def completely_unparsed(stat) -> Decimal:
        if not stat.sentences:
            return Decimal("0")

        return stat.completely_unparsed_ratio / stat.sentences * Decimal("100")

    @staticmethod
    def parseability(stat) -> Decimal:
        if not stat.sentences:
            return Decimal("0")

        return stat.average_parsed_ratio / stat.sentences * Decimal("100")

    @staticmethod
    def parseability_str(stat) -> str:
        return "{0:06.2f}%".format(stat.parseability(stat))

    @staticmethod
    def text(stat) -> str:
        return  "Total sentences parsed in full:\t{0[0]:2.2f}%\n" \
                "Total sentences not parsed at all:\t{0[1]:2.2f}%\n" \
                "Average sentence parse:\t{0[2]:2.2f}%\n" \
                "Total sentences:\t{0[3]:2.2f}\n".format( (stat.completely_parsed(stat),
                                                                   stat.completely_unparsed(stat),
                                                                   stat.parseability(stat),
                                                                   stat.sentences
                                                                   ) )

    def __eq__(self, other):
        return  self.average_parsed_ratio == other.average_parsed_ratio and \
                self.completely_parsed_ratio == other.completely_parsed_ratio and \
                self.completely_unparsed_ratio == other.completely_unparsed_ratio

    def __iadd__(self, other):
        self.completely_parsed_ratio += other.completely_parsed_ratio
        self.completely_unparsed_ratio += other.completely_unparsed_ratio
        self.average_parsed_ratio += other.average_parsed_ratio
        self.sentences += other.sentences
        return self

    # def __itruediv__(self, other:Decimal):
    #     self.completely_parsed_ratio /= other
    #     self.completely_unparsed_ratio /= other
    #     # self.average_parsed_ratio /= other
    #     return self


class ParseQuality():
    def __init__(self):
        self.total = Decimal('0.00')
        self.missing = Decimal('0.00')
        self.extra = Decimal('0.00')
        self.ignored = Decimal('0.00')
        self.quality = Decimal('0.00')
        self.sentences = Decimal('0.00')

    @staticmethod
    def avg_total_links(stat) -> Decimal:
        if not stat.sentences:
            return Decimal('0.00')

        return stat.total / stat.sentences

    @staticmethod
    def avg_ignored_links(stat) -> Decimal:
        if not stat.sentences:
            return Decimal('0.00')

        return stat.ignored / stat.sentences

    @staticmethod
    def avg_missing_links(stat) -> Decimal:
        if not stat.sentences:
            return Decimal('0.00')

        return stat.missing / stat.sentences

    @staticmethod
    def avg_extra_links(stat) -> Decimal:
        if not stat.sentences:
            return Decimal('0.00')

        return stat.extra / stat.sentences

    @staticmethod
    def parse_quality(stat) -> Decimal:
        if not stat.sentences:
            return Decimal('0.00')

        return stat.quality / stat.sentences * Decimal('100.0')

    @staticmethod
    def parse_quality_str(stat) -> str:
        return "{0:06.2f}%".format(stat.parse_quality(stat))

    @staticmethod
    def text(stat) -> str:
        return  "Parse quality: {0:2.2f}%\n" \
                "Average total links: {1:2.2f}\n" \
                "Average ignored links: {2:2.2f}\n" \
                "Average missing links: {3:2.2f}\n" \
                "Average extra links:  {4:2.2f}\n" \
                "Tolal sentences: {5:2.2f}\n".format(
                                                        stat.parse_quality(stat),
                                                        stat.avg_total_links(stat),
                                                        stat.avg_ignored_links(stat),
                                                        stat.avg_missing_links(stat),
                                                        stat.avg_extra_links(stat),
                                                        stat.sentences)

    def __eq__(self, other):
        return  self.quality == other.quality and \
                self.total == other.total and \
                self.ignored == other.ignored and \
                self.missing == other.missing and \
                self.extra == other.extra

    def __iadd__(self, other):
        self.total += other.total
        self.missing += other.missing
        self.extra += other.extra
        self.ignored += other.ignored
        self.quality += other.quality
        self.sentences += other.sentences
        return self

    # def __itruediv__(self, other:Decimal):
    #     self.total /= other
    #     self.missing /= other
    #     self.extra /= other
    #     self.ignored /= other
    #     self.quality /= other
    #     return self
