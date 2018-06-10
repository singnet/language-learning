
__all__ = ['ParseMetrics', 'ParseQuality']

class ParseMetrics():
    ''' Parse statistics data '''
    def __init__(self):
        self.completely_parsed_ratio = 0.0
        self.completely_unparsed_ratio = 0.0
        self.average_parsed_ratio = 0.0

    @staticmethod
    def text(stat) -> str:
        return  "Total sentences parsed in full:\t{0[0]:2.2f}%\n" \
                "Total sentences not parsed at all:\t{0[1]:2.2f}%\n" \
                "Average sentence parse:\t{0[2]:2.2f}%\n".format( (stat.completely_parsed_ratio * 100.0,
                                                                   stat.completely_unparsed_ratio * 100.0,
                                                                   stat.average_parsed_ratio * 100.0) )

    def __iadd__(self, other):
        self.completely_parsed_ratio += other.completely_parsed_ratio
        self.completely_unparsed_ratio += other.completely_unparsed_ratio
        self.average_parsed_ratio += other.average_parsed_ratio
        return self

    def __itruediv__(self, other:float):
        self.completely_parsed_ratio /= other
        self.completely_unparsed_ratio /= other
        self.average_parsed_ratio /= other
        return self


class ParseQuality():
    def __init__(self):
        self.total = 0.0
        self.missing = 0.0
        self.extra = 0.0
        self.ignored = 0.0
        self.quality = 0.0

    @staticmethod
    def text(stat) -> str:
        return  "Parse quality: {0:2.2f}%\n" \
                "Average total links: {1:2.2f}\n" \
                "Average ignored links: {2:2.2f}\n" \
                "Average missing links: {3:2.2f}\n" \
                "Average extra links:  {4:2.2f}".format(
                                                        stat.quality*100.0,
                                                        stat.total,
                                                        stat.ignored,
                                                        stat.missing,
                                                        stat.extra)

    def __iadd__(self, other):
        self.total += other.total
        self.missing += other.missing
        self.extra += other.extra
        self.ignored += other.ignored
        self.quality += other.quality
        return self

    def __itruediv__(self, other:float):
        self.total /= other
        self.missing /= other
        self.extra /= other
        self.ignored /= other
        self.quality /= other
        return self
