import re
import sys
import logging
from typing import Dict, List, Union, Set


__all__ = ['DictRule', 'LGDictionaryRuleSpace', 'read_dict_rules', 'save_dict_rules', 'rule_subset_dict',
           'count_germs_in_dict', 'count_max_rule_bytes_in_dict']


class DictRule:
    """
    Single LG dictionary rule class.

    """
    def __init__(self, cluster_id, germs, disjuncts):
        self.cluster_id: str = cluster_id
        self.germs: str = germs
        self.disjuncts: str = disjuncts

    def get_word_list(self) -> List[str]:
        """
        Split germ string into a list of words

        :return:            List of strings, where each string represents a single word.
        """
        return [ germ.strip()[1:-1] for germ in self.germs.split(" ")] if len(self.germs) else []

    def get_disjunct_list(self) -> List[str]:
        """
        Split disjunct string into a list of disjuncts

        :return:            List of strings, where each string represents a single disjunct.
        """
        if not len(self.disjuncts):
            return []

        return [ disjunct[1:-1] if disjunct[0] == "(" and disjunct[-1] == ")" else disjunct
                 for disjunct in re.split(re.compile(r"\s+or\s+", re.I), self.disjuncts) ]

    def __str__(self) -> str:
        """
        Format LG grammar rule to be stored in 4.0.dict file

        :return:        Formated rule string.
        """
        return f"% {self.cluster_id}\n{self.germs}:\n{self.disjuncts};\n"


class LGDictionaryRuleSpace:
    """
    LG dictionary rules class

    """
    def __init__(self, rules: List[DictRule]):

        # List of dictionary rules. The original dictionary rule order is left untouched.
        self._rule_list: List[DictRule] = rules

        # Dictionary rule counter
        self.rule_count: int = len(rules)

        # Dictionary with a list of LG dictionary rule indexes for each word
        self._word_rules: Dict[List[int]] = dict()

        # Fill the dictionary with words and rule indexes
        for index, rule in enumerate(self._rule_list):

            # Split into tokens and strip double quotes
            words = [germ[1:-1] for germ in rule.germs.split(" ")]

            for word in words:
                index_list = self._word_rules.get(word, None)

                # Add dictionary entry for the word if it's not exists
                if index_list is None:
                    index_list = list()
                    self._word_rules[word] = index_list

                # Append one more rule index
                index_list.append(index)

    def wordspace_intersection_rules(self, words: Set[str]) -> List[DictRule]:
        """
        Create dictionary rule list containing only germs produced by intersection of specified word set and
            set of old rule germs. Each rule contains only valid disjuncts having only connectors corresponding
            new rule/cluster set.

        :param words:       Set of words to be selected in rules.
        :return:            List of new rules.
        """
        # Create intersection of 'words' set and known words
        word_set = { key for key in self._word_rules.keys()} & words

        rule_set = set()

        # Create a set of rule indexes that correspond one or more word from 'words' set
        for key in word_set:
            rule_set |= set(self._word_rules[key])

        # Sorted list of selected rules
        selected_rules = [ self._rule_list[rule_index] for rule_index in sorted(list(rule_set)) ]

        # Valid cluster set
        connector_set = set([ rule1.cluster_id + rule2.cluster_id
                              for rule1 in selected_rules for rule2 in selected_rules
                              if rule1.cluster_id != rule2.cluster_id
                              ])

        # List of new dictionary rules
        new_rule_list: List[DictRule] = list()

        for rule in selected_rules:

            new_germs_str = " ".join([ f'"{word}"' for word in sorted(list(word_set & set(rule.get_word_list()))) ])

            old_disjuncts = rule.get_disjunct_list()

            new_disjuncts_str = ""

            index = 0

            for old_disjunct in old_disjuncts:

                old_connectors = re.findall(re.compile("(\w+)[-+]", re.I), old_disjunct)

                if len(set(old_connectors) & connector_set) != len(old_connectors):
                    continue

                new_disjuncts_str += f" or ({old_disjunct})" if index else f"({old_disjunct})"

                index += 1

            if len(new_germs_str) and len(new_disjuncts_str):
                new_rule_list.append(DictRule(rule.cluster_id, new_germs_str, new_disjuncts_str))

        return new_rule_list

    # def wordspace_intersection_rules(self, words: Set[str]) -> List[DictRule]:
    #     """
    #     Create dictionary rule list containing only germs produced by intersection of specified word set and
    #         set of old rule germs. Each rule contains only valid connectors in disjunct list corresponding
    #         selected rules (clusters).
    #
    #     :param words:       Set of words to be selected in rules.
    #     :return:            List of new rules.
    #     """
    #     # Create intersection of 'words' set and known words
    #     word_set = { key for key in self._word_rules.keys()} & words
    #
    #     rule_set = set()
    #
    #     # Create a set of rule indexes that correspond one or more word from 'words' set
    #     for key in word_set:
    #         rule_set |= set(self._word_rules[key])
    #
    #     # Sorted list of selected rules
    #     selected_rules = [ self._rule_list[rule_index] for rule_index in sorted(list(rule_set)) ]
    #
    #     # Valid cluster set
    #     connector_set = set([ rule1.cluster_id + rule2.cluster_id
    #                           for rule1 in selected_rules for rule2 in selected_rules
    #                           if rule1.cluster_id != rule2.cluster_id
    #                           ])
    #
    #     # List of new dictionary rules
    #     new_rule_list: List[DictRule] = list()
    #
    #     for rule in selected_rules:
    #
    #         new_germs_str = " ".join([ f'"{word}"' for word in sorted(list(word_set & set(rule.get_word_list()))) ])
    #
    #         old_disjuncts = rule.get_disjunct_list()
    #
    #         new_disjuncts_str = ""
    #
    #         index = 0
    #
    #         for old_disjunct in old_disjuncts:
    #
    #             old_connectors = re.findall(re.compile("(\w+)([-+])", re.I), old_disjunct)
    #
    #             new_connectors = [t[0] + t[1]
    #                               for t in list(filter(lambda e: len({e[0]} & connector_set), old_connectors))]
    #
    #             if not len(new_connectors):
    #                 continue
    #
    #             new_disjunct = " & ".join(new_connectors)
    #
    #             new_disjuncts_str += f" or ({new_disjunct})" if index else f"({new_disjunct})"
    #
    #             index += 1
    #
    #         if len(new_germs_str) and len(new_disjuncts_str):
    #             new_rule_list.append(DictRule(rule.cluster_id, new_germs_str, new_disjuncts_str))
    #
    #     return new_rule_list


def read_dict_rules(file_path: str) -> []:
    """
    Extract dictionary rule list out of LG dictionary file

    :param dict_path:       Path to a .dict file
    :return:                List of DictRule
    """
    re_dict_rule = re.compile(r'^% ([A-Z]{2,12})(?:(?:\n|\r\n?)+(.+):){1}(?:(?:\n|\r\n?)+(.+)){1}', re.M)

    # reDictRule = re.compile(r'^% ([A-Z]{3})(?:(?:\n|\r\n?)+(.+)\:){1}(?:(?:\n|\r\n?)+(.+)){1}', re.M)

    # Read the whole file at once
    with open(file_path, "r") as dict:
        file_data = dict.read()

    return [DictRule(parse[0], parse[1], parse[2][:-1]) for parse in re.findall(re_dict_rule, file_data)]


def save_dict_rules(dst_dict_path: str, rules: List[DictRule]) -> None:
    """
    Save dictionary rules into proper LG dictionary file

    :param dst_dict_path:   Destination dictionary file path.
    :param rules:           List of dictionary rules.
    :return:                None.
    """
    logger = logging.getLogger(__name__ + ".save_dict_rules")

    if not len(rules):
        logger.warning("No rules to save!")
        return

    with open(dst_dict_path, "w") as dest:

        print("<dictionary-version-number>: V0v0v5+;", file=dest)
        print("<dictionary-locale>: EN4us+;\n", file=dest)

        for rule in rules:
            print(str(rule), file=dest)

        # The last and very important rule
        print("<UNKNOWN-WORD>: XXX+;", file=dest)


def rule_subset_dict(sent: Union[str, List[str]], src_dict_path: str, dst_dict_path: str) -> None:
    """
    Filter out all LG dictionary rules not applicable to specified sentence(s) and clean up selected rules
        to have only valid connectors in disjuncts.

    :param sent:            Sentence or list of sentences.
    :param src_dict_path:   Source LG dictionary file path.
    :param dst_dict_path:   Destination LG dictionary path.
    :return:                None
    """
    logger = logging.getLogger(__name__ + ".rule_subset_dict")

    word_set = set()

    if isinstance(sent, str):
        word_set |= { word.strip() for word in sent.split(" ") }

    elif isinstance(sent, list):
        for sentence in sent:
            word_set |= { word.strip() for word in sentence.split(" ") }

    else:
        raise ValueError("Parameter 'sent' must be either string or list of strings.")

    dict_space: LGDictionaryRuleSpace = LGDictionaryRuleSpace(read_dict_rules(src_dict_path))

    save_dict_rules(dst_dict_path, dict_space.wordspace_intersection_rules(word_set))

    logger.warning(f"New dictionary file is saved at: {dst_dict_path}")


def count_germs_in_dict(dict_path: str) -> (int, int):
    """
    Count all germs in all rules

    :param dict_path:       Path to dictionary file.
    :return:                Number of germs in all rules and number of rules.
    """
    logger = logging.getLogger(__name__ + ".count_germs_in_dict")

    logger.debug(dict_path)

    re_dict_rule = re.compile(r'^([^<%\n].+?):(.+?);(?:\s*)$', re.M | re.S)

    # Read the whole file at once
    with open(dict_path, "r") as dict:
        file_data = dict.read()

    rules = [parse[0] for parse in re.findall(re_dict_rule, file_data)]

    word_count = 0

    for rule in rules:
        word_count += len(rule.split())

    return word_count, len(rules)


def count_max_rule_bytes_in_dict(dict_path: str) -> int:
    """
    Count all germs in all rules

    :param dict_path:       Path to dictionary file.
    :return:                Length in bytes of the longest rule in the dictionary.
    """
    logger = logging.getLogger(__name__ + ".count_max_rule_bytes_in_dict")

    logger.debug(dict_path)

    re_dict_rule = re.compile(r'^([^<%\n].+?:.+?;\s*)$', re.M | re.S)

    # Read the whole file at once
    with open(dict_path, "r") as dict:
        file_data = dict.read()

    max_rule_bytes = -1

    for rule in re.findall(re_dict_rule, file_data):
        max_rule_bytes = max(len(rule.encode("utf-8")), max_rule_bytes)

    return max_rule_bytes
