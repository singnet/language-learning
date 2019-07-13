import re
import logging
import traceback
from typing import Dict, List, Any, Union, Callable, Optional
from .pipelineexceptions import PipelineComponentException, FatalPipelineException

__all__ = ['PipelineTreeNode2']


class PipelineTreeNode2:
    """
    Pipeline execution tree node

    """
    roots = list()
    static_components = dict()
    logger = logging.getLogger("PipelineTreeNode2")

    def __init__(self,
                 seq_no: int,
                 name: str,
                 parameters: Dict[str, Any],
                 environment: Union[Dict[str, Any], None]=None,
                 parent=None):
        """
        :param seq_no:          Hierarchy level number;
        :param name:            Component name;
        :param parameters:      Configuration parameters
        :param environment:     Environment variables dictionary;
        :param parent:          Parent node reference.
        """
        if parent is None:
            self.roots.append(self)

        self.seq_no: int = seq_no
        self._component_name: str = name
        self._parameters: Dict[str, Any] = {} if parameters is None else parameters
        self._environment: Dict[str, Any] = {} if environment is None else environment
        self._siblings: List[PipelineTreeNode2] = []
        self._parent: Union[None, PipelineTreeNode2] = parent

        if self._parent is not None:
            self._parent.add_sibling(self)

    @staticmethod
    def free_static_components():
        for o in PipelineTreeNode2.static_components.values():
            if o is not None:
                del o

        PipelineTreeNode2.static_components = dict()

    @staticmethod
    def _get_exception_name(exception_obj: Optional[Exception]) -> str:
        """
        Get exception class name string

        :param exception_obj:   Exception derived class object
        :return:                Exception class name or empty string if 'exception_obj' is None
        """
        if exception_obj is None:
            return ""

        name_pattern = re.compile("<class '(\w+)'>", re.S)
        result_list = re.findall(name_pattern, str(exception_obj.__class__))
        return result_list[0] if len(result_list) > 0 else ""

    @staticmethod
    def log_error(message: str, node, exception_obj: Exception, traceback_str: str=""):
        """
        Log exception information

        :param message:         Error message.
        :param node:            Execution tree node the exception is rased at.
        :param exception_obj:   Exception object.
        :param traceback_str:   Traceback converted to string.
        :return:                None.
        """
        node.logger.critical(f"{node._component_name}(cfg={node.seq_no+1}, "
                             f"run={node._environment.get('RUN_COUNT', 0)}):\n"
                             f"{node._get_exception_name(exception_obj)}: {message}\n")

        node.logger.debug(   f"{traceback_str}\n"
                             f"Environment:\n{node._environment}\n"
                             f"Parameters:\n{node._parameters}")

    @staticmethod
    def traverse(job: Callable, node=None) -> None:
        """
        Traverse pipeline tree executing the job

        :param job:         Function/method to execute for each node.
        :param node:        Node to start from
        :return:            None
        """
        if node is None or node._parameters.get("skip_configuration", False):
            return None

        if job is not None:
            try:
                job(node)

            # Stop the pipeline only if Ctrl+C is triggered
            except KeyboardInterrupt:
                raise

            # Discontinue execution of the current branch otherwise
            except KeyError as err:
                node.log_error(f"Argument {str(err)} is missing in kwargs.", node, err)
                # raise PipelineComponentException(f"Fatal error: argument {str(err)} is missing in kwargs.", node, err)
                return None

            except FileNotFoundError as err:
                node.log_error(str(err), node, err)
                # raise PipelineComponentException(str(err), node, err)
                return None

            except PermissionError as err:
                node.log_error(str(err))
                return None

            except Exception as err:
                node.log_error(str(err), node, err, traceback.format_exc())
                # raise PipelineComponentException(str(err), node, err, traceback.format_exc())
                return None

        for sibling in node._siblings:
                PipelineTreeNode2.traverse(job, sibling)

    @staticmethod
    def traverse_all(job: Callable) -> None:
        """
        Traverse all execution paths of pipeline tree

        :param job:         Function/method to execute for each node.
        :return:            None
        """
        for i, root in enumerate(PipelineTreeNode2.roots, 0):
            PipelineTreeNode2.logger.info("Execution path: " + str(i))
            PipelineTreeNode2.traverse(job, root)

    @staticmethod
    def print_node(parameters: dict, environment: dict):
        """
        Print parameters for debug purposes

        :param parameters:  Input parameters.
        :param environment: Environment variables.
        :return:
        """
        print(parameters)

    def add_sibling(self, node) -> None:
        """
        Add sibling to pipeline tree

        :param node:    Sibling node to add.
        :return:        None
        """
        self._siblings.append(node)
