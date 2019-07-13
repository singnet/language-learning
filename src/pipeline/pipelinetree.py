import logging
from typing import Dict, List, Any, Union, Callable, NewType, Optional
from time import time

import os
from ..common.cliutils import handle_path_string
from ..common.optconst import *
from ..common.tokencount import *
from ..common.absclient import AbstractPipelineComponent
from ..grammar_tester.gt_component import GrammarTesterComponent
from ..grammar_tester.parsevaluate import ParseEvaluatorComponent
from ..grammar_learner import GrammarLearnerComponent
from ..text_parser import TextParserComponent
from ..dash_board.textdashboard import TextFileDashboardComponent
from .varhelper import get_path_from_dict, subst_variables_in_str, subst_variables_in_dict, subst_variables_in_dict2
from .pipelinetreenode import PipelineTreeNode2
from .pipelineexceptions import *


__all__ = ['build_tree', 'run_tree', 'check_config']


logger = logging.getLogger(__name__)

PARAM_INPUT_PATH            = 'input_path'
PARAM_OUTPUT_PATH           = 'output_path'


class PathCreatorComponent(AbstractPipelineComponent):
    """
    Path Creator Component responsible for creating directory structures

    """
    def __init__(self):
        pass

    def validate_parameters(self, **kwargs):
        return True

    def run(self, **kwargs):
        return {}

    @staticmethod
    def create(**kwargs):
        path = kwargs.get("path", None)

        if path is not None and not os.path.isdir(path):
            os.makedirs(path)

        return {"path": path}


class TokenCounterComponent(AbstractPipelineComponent):
    """
    Token Counter Component is responsible for counting token appearances in the corpus.

    """
    def __init__(self, **kwargs):
        # check_kwargs(**kwargs)
        pass

    def validate_parameters(self, **kwargs):
        """ Validate configuration parameters """
        ret_val = True

        if kwargs.get(PARAM_INPUT_PATH, None) is None:
            print("Error: parameter '{}' is not specified.".format(PARAM_INPUT_PATH))
            ret_val = False

        if kwargs.get(PARAM_OUTPUT_PATH, None) is None:
            print("Error: parameter '{}' is not specified.".format(PARAM_OUTPUT_PATH))
            ret_val = False

        return ret_val

    def run(self, **kwargs):
        """ Execute component code """

        options = get_options(kwargs)

        input_path = kwargs.get(PARAM_INPUT_PATH, None)

        if input_path:
            input_path = handle_path_string(input_path)

        output_path = kwargs.get(PARAM_OUTPUT_PATH, None)

        if output_path:
            output_path = handle_path_string(output_path)

        # Run Token Counter
        dump_token_counts(input_path, output_path, options)

        return {}


# Pipeline component dictionary having tuples of component class and prefix, used when automaticaly creating
#   destination subdirectory.
PIPELINE_COMPONENTS = {
    "path-creator": (PathCreatorComponent, ""),
    "grammar-tester": (GrammarTesterComponent, "GT"),
    "grammar-learner": (GrammarLearnerComponent, "GL"),
    "text-parser": (TextParserComponent, "TP"),
    "dash-board": (TextFileDashboardComponent, ""),
    "token-counter": (TokenCounterComponent, "TC"),
    "parse-evaluator": (ParseEvaluatorComponent, "PE")
}


def get_component(name: str, params: dict) -> AbstractPipelineComponent:
    """
    Create an instance of the pipeline component

    :param name:    Pipeline component name.
    :return:        AbstractPipelineComponent instance pointer.
    """
    try:
        # Create an instance of specified pipeline component
        component = PIPELINE_COMPONENTS[name][0](**params)

        # Check the instance to be proper pipeline component
        if not isinstance(component, AbstractPipelineComponent):
            raise Exception(f"Error: {str(type(component))} is not an instance of AbstractPipelineComponent")

        return component

    except KeyError:
        raise Exception(f"Error: '{name}' is not a valid pipeline component name.")


def single_proc_exec(node: PipelineTreeNode2) -> None:
    """
    Single process pipeline component execution routine

    :param node:        Execution tree node.
    :return:            None.
    """
    if node is None:
        return

    leaf = node._environment["LEAF"]
    create = node._environment.get("CREATE_LEAF", False)

    # Create path if it does not exist
    if create and not os.path.isdir(leaf):
        os.makedirs(leaf)

    parameters = node._parameters
    result = {}

    pre_exec = parameters.get("pre-exec-req", None)

    if pre_exec:
        for req in pre_exec:
            result = handle_request(node, req)

    start_time = time()

    # Create component instance
    component = get_component(node._component_name, parameters)

    # Execute component
    result = component.run(**{**parameters, **result})

    # Calculate execution time and format it in a string
    time_span_str = format_time_str(time() - start_time)

    # Make execution time available for post processing
    result.update(exec_time = time_span_str)

    post_exec = parameters.get("post-exec-req", None)

    if post_exec:
        for req in post_exec:
            handle_request(node, {**req, **result})

    # Just for debug purposes
    logger.debug(f"{node._component_name} execution time: {time_span_str}")


def handle_request(node: PipelineTreeNode2, req: dict) -> None:
    """
    Handle Post-execute Request

    :param node:        Pipiline tree node reference.
    :param req:         Request parameter dictionary.
    :return:            None
    """
    obj = req.pop("obj", None)

    if obj is None:
        raise Exception("Error: Required parameter 'obj' does not exist.")

    pos = str(obj).find(".")

    if pos < 0:
        raise Exception("Error: Object name and method should be separated by comma.")

    name = obj[:pos]
    meth = obj[pos+1:]

    inst = node.static_components.get(name, None)

    if inst is None:
        raise Exception("Error: static component '{}' does not exist.".format(name))

    return getattr(inst, meth)(**req)


def prepare_parameters(parent: Optional[PipelineTreeNode2], common: dict, specific: dict, environment: dict,
                       first_char="%", create_sub_dir: bool=True) -> (dict, dict):
    """
    Create built-in variables (such as PREV, RPREV, LEAF, RLEAF), substitute variables, starting with 'first_char'
        with their real values.

    :param parent:          Parent node of the execution tree.
    :param common:          Common parameters dictionary.
    :param specific:        Specific parameters dictionary.
    :param environment:     Environment dictionary.
    :param first_char:      Character that delimits variables ('%' is default).
    :param create_sub_dir   Boolean value forces the program to create subdirectory path based on specific dictionary.
    :return:                Tuple of two dictionaries: one for parameters, another for environment.
    """

    # Merge two dictionaries 'common-parameters' and 'specific-parameters'
    all_parameters = {**common, **specific} if common is not None else specific

    create_leaf = False

    # Check if 'LEAF' path should be created
    for v in all_parameters.values():
        if type(v) == str and v.find("LEAF") >= 0:
            create_leaf = True

    # Path parameters should not appear in other paths
    non_path = {k: v for k, v in zip(specific.keys(), specific.values())
                if (not (isinstance(v, list) or isinstance(v, dict) or isinstance(v, str)))
                or (isinstance(v, str) and v.find("/") < 0 and v.find("%") < 0)}

    # Get subdir path based on specific parameters if requested
    sep = "_"
    rleaf = common.get("CMP_PREFIX", "") + sep + get_path_from_dict(non_path, sep) if create_leaf else ""

    inherit_prev = all_parameters.get("inherit_prev_path", False)

    leaf = (environment["PREV"] + "/" + rleaf if parent is not None else rleaf) if inherit_prev and parent is not None \
        else environment["ROOT"] + "/" + rleaf

    # leaf = (environment["PREV"] + "/" + rleaf if parent is not None else rleaf) if inherit_prev \
    #     else environment["ROOT"] + "/" + rleaf

    new_environment = {**environment, **{"RLEAF": rleaf, "LEAF": leaf, "CREATE_LEAF": create_leaf}}

    scopes = {"THIS": {**new_environment, **all_parameters}, "PREV": {}} if parent is None else \
             {"THIS": {**new_environment, **all_parameters}, "PREV": {**parent._environment, **parent._parameters}}

    # Substitute derived path for LEAF, PREV and other variables
    all_parameters = subst_variables_in_dict2(all_parameters, scopes, True, first_char)

    return all_parameters, new_environment


def build_tree(config: List, globals: dict, first_char="%") -> List[PipelineTreeNode2]:
    """
    Build execution tree

    :param config:          Dictionary with configuration parameters (taken from JSON configuration file).
    :param globals:         Global variable dictionary.
    :param first_char:      Starting character to distinguish variables from other literals.
    :return:                Root node list to start execution from.
    """
    parents = list()

    for level, component_config in enumerate(config):

        name = component_config.get("component", None)
        type = component_config.get("type", "dynamic")
        comm = component_config.get("common-parameters", {})
        spec = component_config.get("specific-parameters", None)

        if name is None:
            raise Exception("No 'component' parameter found in configuration.")

        if type == "dynamic" and spec is None:
            raise Exception("No 'specific-parameters' section found in configuration.")

        if type == "static":
            params = subst_variables_in_dict(component_config.get("parameters", {}), globals, first_char)

            inst_name = component_config.get("instance-name", None)

            if inst_name is not None:
                PipelineTreeNode2.static_components[inst_name] = get_component(name, params)

            continue

        children = list()

        # Add component prefix to 'common-parameters'
        comm = {**comm, **{"CMP_PREFIX": PIPELINE_COMPONENTS[name][1]}}

        if len(parents):
            for parent in parents:

                # Only if the previous component path should be followed
                if parent._parameters.get("follow_exec_path", True):

                    for count, specific in enumerate(spec):

                        # Create parameter and environment dictionaries
                        parameters, environment = prepare_parameters(
                            parent, comm, specific,
                            {**globals, **{"RPREV": parent._environment["RLEAF"], "PREV": parent._environment["LEAF"]},
                             **{"RUN_COUNT": count + 1}}, first_char, len(spec) > 1)

                        children.append(PipelineTreeNode2(level, name, parameters, environment, parent))

        else:
            for count, specific in enumerate(spec):

                # Create parameter and environment dictionaries
                parameters, environment = prepare_parameters(None, comm, specific,
                                                             {**globals, **{"RUN_COUNT": count + 1}},
                                                             first_char, len(spec) > 1)

                children.append(PipelineTreeNode2(level, name, parameters, environment, None))

        parents = None
        parents = children
        children = None

    return PipelineTreeNode2.roots


def check_config(config: List) -> None:
    """
    Check/validate configuration structure.

    :param config:      List with each component configuration dictionary. At least it should be that.
    :return:            None
    """
    ret = True

    if not isinstance(config, list):
        raise FatalPipelineException("Top level element of the pipeline configuration should be a list of pipeline "
                                     "component configurations.")

    for comp_no, comp_cfg in enumerate(config):
        if not isinstance(comp_cfg, dict):
            logger.error("Each pipeline component configuration must be specified by a dictionary.")
            ret = False
            continue

        component = comp_cfg.get("component", None)

        if component is None:
            logger.error(f"Required parameter 'component' is missing in component #{comp_no} configuration.")
            ret = False
            continue

        type = comp_cfg.get("type", None)

        if type is None or type != "static":

            spec_params = comp_cfg.get("specific-parameters", None)

            if spec_params is None:
                logger.error(f"Required parameter 'specific-parameters' is missing in {component}'s configuration "
                             f"(component #{comp_no}).")
                ret = False
                continue

            if not isinstance(spec_params, list):
                logger.error(f"'{component}' component (#{comp_no}) configuration's 'specific-parameters' "
                             f"must be a list.")
                ret = False
                continue

            for no, param in enumerate(spec_params):
                if not isinstance(param, dict):
                    logger.error(f"{component}'s 'specific-parameters' element {no} must be a dictionary.")
                    ret = False
                    continue

    if not ret:
        raise FatalPipelineException("Configuration error(s) found.")


def format_time_str(parse_time) -> str:
    """
    Format execution time to be printed out

    :param parse_time:      Timespan.
    :return:                Formated string.
    """
    hours = int(parse_time / 3600)
    minutes = int((parse_time - hours * 3600) / 60)
    seconds = int(parse_time % 60)
    millis  = int((parse_time % 60 - seconds) * 1000)
    return "{}h {}m {}s {}ms".format(hours, minutes, seconds, millis)


def run_tree() -> None:
    """
    Run pipeline components traversing the execution tree

    :return:
    """
    start_time = time()

    PipelineTreeNode2.traverse_all(single_proc_exec)

    logger.warning("Overal pipeline execution time: " + format_time_str(time() - start_time))