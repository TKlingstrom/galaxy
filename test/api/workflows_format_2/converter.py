import os
import sys

import yaml
import json
import uuid

try:
    from collections import OrderedDict
except ImportError:
    from galaxy.util.odict import odict as OrderedDict


STEP_TYPES = [
    "data_input",
    "data_collection_input",
    "tool",
    "pause",
]

STEP_TYPE_ALIASES = {
    'input': 'data_input',
    'input_collection': 'data_collection_input',
}

RUN_ACTIONS_TO_STEPS = {
}


def yaml_to_workflow(has_yaml, galaxy_interface, workflow_directory):
    as_python = yaml.load(has_yaml)
    return python_to_workflow(as_python, galaxy_interface, workflow_directory)


def python_to_workflow(as_python, galaxy_interface, workflow_directory):
    if workflow_directory is None:
        workflow_directory = os.path.abspath(".")

    conversion_context = ConversionContext(
        galaxy_interface,
        workflow_directory,
    )
    return _python_to_workflow(as_python, conversion_context)


def _python_to_workflow(as_python, conversion_context):

    if not isinstance(as_python, dict):
        raise Exception("This is not a not a valid Galaxy workflow definition.")

    if "class" not in as_python:
        raise Exception("This is not a not a valid Galaxy workflow definition, must define a class.")

    if as_python["class"] != "GalaxyWorkflow":
        raise Exception("This is not a not a valid Galaxy workflow definition, 'class' must be 'GalaxyWorkflow'.")

    __ensure_defaults(as_python, {
        "a_galaxy_workflow": "true",
        "format-version": "0.1",
        "annotation": "",
        "name": "Workflow",
        "uuid": str(uuid.uuid4()),
    })

    steps = as_python["steps"]

    # If an inputs section is defined, build steps for each
    # and add to steps array.
    if "inputs" in as_python:
        inputs = as_python["inputs"]
        convert_inputs_to_steps(inputs, steps)

    if isinstance(steps, list):
        steps_as_dict = OrderedDict()
        for i, step in enumerate(steps):
            steps_as_dict[ str(i) ] = step
            if "id" not in step:
                step["id"] = i

            if "label" in step:
                label = step["label"]
                conversion_context.labels[label] = i

            if "position" not in step:
                # TODO: this really should be optional in Galaxy API.
                step["position"] = {
                    "left": 10 * i,
                    "top": 10 * i
                }

        as_python["steps"] = steps_as_dict
        steps = steps_as_dict

    for step in steps.itervalues():
        step_type = step.get("type", None)
        if "run" in step:
            if step_type is not None:
                raise Exception("Steps specified as run actions cannot specify a type.")
            run_action = step.get("run")
            if "@import" in run_action:
                if len(run_action) > 1:
                    raise Exception("@import must be only key if present.")

                run_action_path = run_action["@import"]
                runnable_path = os.path.join(conversion_context.workflow_directory, run_action_path)
                with open(runnable_path, "r") as f:
                    runnable_description = yaml.load(f)
                    run_action = runnable_description

            run_class = run_action["class"]
            run_to_step_function = eval(RUN_ACTIONS_TO_STEPS[run_class])

            run_to_step_function(conversion_context, step, run_action)
            del step["run"]

    for step in steps.itervalues():
        step_type = step.get("type", "tool")
        step_type = STEP_TYPE_ALIASES.get(step_type, step_type)
        if step_type not in STEP_TYPES:
            raise Exception("Unknown step type encountered %s" % step_type)
        step["type"] = step_type
        eval("transform_%s" % step_type)(conversion_context, step)

    for output in as_python.get("outputs", []):
        assert isinstance(output, dict), "Output definition must be dictionary"
        assert "source" in output, "Output definition must specify source"

        source = output["source"]
        id, output_name = conversion_context.step_output(source)
        step = steps[str(id)]
        if "workflow_output" not in step:
            step["workflow_outputs"] = []

        step["workflow_outputs"].append({
            "output_name": output_name,
        })

    return as_python


def convert_inputs_to_steps(inputs, steps):
    new_steps = []
    for input_def_raw in inputs:
        input_def = input_def_raw.copy()

        if "label" in input_def and "id" in input_def:
            raise Exception("label and id are aliases for inputs, may only define one")
        if "label" not in input_def and "id" not in input_def:
            raise Exception("Input must define a label.")

        raw_label = input_def.pop("label", None)
        raw_id = input_def.pop("id", None)
        label = raw_label or raw_id

        if not label:
            raise Exception("Input label must not be empty.")

        input_type = input_def.pop("type", "data")
        if input_type in ["File", "data", "data_input"]:
            step_type = "data_input"
        elif input_type in ["collection", "data_collection", "data_collection_input"]:
            step_type = "data_collection_input"
        else:
            raise Exception("Input type must be a data file or collection.")

        step_def = input_def
        step_def.update({
            "type": step_type,
            "label": label,
        })
        new_steps.append(step_def)

    for i, new_step in enumerate(new_steps):
        steps.insert(i, new_step)


def transform_data_input(context, step):
    transform_input(context, step, default_name="Input dataset")


def transform_data_collection_input(context, step):
    transform_input(context, step, default_name="Input dataset collection")


def transform_input(context, step, default_name):
    default_name = step.get("label", default_name)
    __ensure_defaults( step, {
        "annotation": "",
    })

    __ensure_inputs_connections(step)

    if "inputs" not in step:
        step["inputs"] = [{}]

    step_inputs = step["inputs"][0]
    if "name" in step_inputs:
        name = step_inputs["name"]
    else:
        name = default_name

    __ensure_defaults( step_inputs, {
        "name": name,
        "description": "",
    })
    tool_state = {
        "name": name
    }
    if "collection_type" in step:
        tool_state["collection_type"] = step["collection_type"]

    __populate_tool_state(step, tool_state)


def transform_pause(context, step, default_name="Pause for dataset review"):
    default_name = step.get("label", default_name)
    __ensure_defaults( step, {
        "annotation": "",
    })

    __ensure_inputs_connections(step)

    if "inputs" not in step:
        step["inputs"] = [{}]

    step_inputs = step["inputs"][0]
    if "name" in step_inputs:
        name = step_inputs["name"]
    else:
        name = default_name

    __ensure_defaults( step_inputs, {
        "name": name,
    })
    tool_state = {
        "name": name
    }

    connect = __init_connect_dict(step)
    __populate_input_connections(context, step, connect)
    __populate_tool_state(step, tool_state)


def transform_tool(context, step):
    if "tool_id" not in step:
        raise Exception("Tool steps must define a tool_id.")

    __ensure_defaults( step, {
        "annotation": "",
        "name": step['tool_id'],
        "post_job_actions": {},
        "tool_version": None,
    } )
    post_job_actions = step["post_job_actions"]

    tool_state = {
        # TODO: Galaxy should not require tool state actually specify a __page__.
        "__page__": 0,
    }

    connect = __init_connect_dict(step)

    def append_link(key, value):
        if key not in connect:
            connect[key] = []
        connect[key].append(value["$link"])

    def replace_links(value, key=""):
        if __is_link(value):
            append_link(key, value)
            return None
        if isinstance(value, dict):
            new_values = {}
            for k, v in value.iteritems():
                new_key = __join_prefix(key, k)
                new_values[k] = replace_links(v, new_key)
            return new_values
        elif isinstance(value, list):
            new_values = []
            for i, v in enumerate(value):
                # If we are a repeat we need to modify the key
                # but not if values are actually $links.
                if __is_link(v):
                    append_link(key, v)
                    new_values.append(None)
                else:
                    new_key = "%s_%d" % ( key, i )
                    new_values.append(replace_links(v, new_key))
            return new_values
        else:
            return value

    if "state" in step:
        step_state = step["state"]
        step_state = replace_links(step_state)

        for key, value in step_state.iteritems():
            tool_state[key] = json.dumps(value)
        del step["state"]

    # Fill in input connections
    __populate_input_connections(context, step, connect)

    __populate_tool_state(step, tool_state)

    # Handle outputs.
    if "outputs" in step:
        for name, output in step.get("outputs", {}).items():
            if output.get("hide", False):
                action_name = "HideDatasetAction%s" % name
                action = __action(
                    "HideDatasetAction",
                    name,
                )
                post_job_actions[action_name] = action

            if output.get("rename", None):
                new_name = output.get("rename")
                action_name = "RenameDatasetAction%s" % name
                arguments = dict(newname=new_name)
                action = __action(
                    "RenameDatasetAction",
                    name,
                    arguments,
                )
                post_job_actions[action_name] = action

        del step["outputs"]


def run_tool_to_step(conversion_context, step, run_action):
    tool_description = conversion_context.galaxy_interface.import_tool(
        run_action
    )
    step["type"] = "tool"
    step["tool_id"] = tool_description["tool_id"]
    step["tool_version"] = tool_description["tool_version"]
    step["tool_hash"] = tool_description["tool_hash"]


class ConversionContext(object):

    def __init__(self, galaxy_interface, workflow_directory):
        self.labels = {}
        self.galaxy_interface = galaxy_interface
        self.workflow_directory = workflow_directory

    def step_id(self, label_or_id):
        if label_or_id in self.labels:
            id = self.labels[label_or_id]
        else:
            id = label_or_id
        return int(id)

    def step_output(self, value):
        value_parts = str(value).split("#")
        if len(value_parts) == 1:
            value_parts.append("output")
        id = self.step_id(value_parts[0])
        return id, value_parts[1]


def __action(type, name, arguments={}):
    return {
        "action_arguments": arguments,
        "action_type": type,
        "output_name": name,
    }


def __is_link(value):
    return isinstance(value, dict) and "$link" in value


def __join_prefix(prefix, key):
    if prefix:
        new_key = "%s|%s" % (prefix, key)
    else:
        new_key = key
    return new_key


def __init_connect_dict(step):
    if "connect" not in step:
        step["connect"] = {}

    connect = step["connect"]
    del step["connect"]
    return connect


def __populate_input_connections(context, step, connect):
    __ensure_inputs_connections(step)
    input_connections = step["input_connections"]

    for key, values in connect.iteritems():
        input_connection_value = []
        if not isinstance(values, list):
            values = [ values ]
        for value in values:
            if not isinstance(value, dict):
                if key == "$step":
                    value += "#__NO_INPUT_OUTPUT_NAME__"
                id, output_name = context.step_output(value)
                value = {"id": id, "output_name": output_name}
            input_connection_value.append(value)
        if key == "$step":
            key = "__NO_INPUT_OUTPUT_NAME__"
        input_connections[key] = input_connection_value


def __ensure_inputs_connections(step):
    if "input_connections" not in step:
        step["input_connections"] = {}


def __ensure_defaults(in_dict, defaults):
    for key, value in defaults.items():
        if key not in in_dict:
            in_dict[ key ] = value


def __populate_tool_state(step, tool_state):
    step["tool_state"] = json.dumps(tool_state)


def main(argv):
    print json.dumps(yaml_to_workflow(argv[0]))


if __name__ == "__main__":
    main(sys.argv)