from string import Template

from IPython.display import display
from ipywidgets import Button, Dropdown, HBox, Label, Layout, Output, Textarea, VBox


def comma_join_list(list, conj="or"):  # todo: move to util
    return "{} {} {}".format(", ".join(list[:-1]), conj, list[-1])


def color(str):
    # return '\x1b[31m{}\x1b[0m'.format(str)
    return "\x1b[48;5;159m{}\x1b[0m".format(str)


class PromptTemplate:
    """
    The PromptTemplate class represents a prompt template for LLM annotation.
    """

    def __init__(self, label_schema, label_names=[], template="", **kwargs):
        """
        Init function

        Parameters
        ----------
        label_schema : list
            List of label objects
        label_names : list, optional
            List of label names to be used for annotation, by default []
        template : str, optional
            Stringified template with input slot, by default ''
        """
        self.set_schema(label_schema, label_names)
        self.template = template

        self.task_inst = kwargs.get(
            "task_inst", "Label the {name} of the following text as {options}."
        )
        self.is_json_template = kwargs.get("is_json_template", False)
        format_inst = (
            "Your answer should be in a valid JSON format and ensure you include both opening and closing braces and quotations for the property fields in all cases as {format_sample}."
            if self.is_json_template
            else "Your answer should be in the following format '{format_sample}'."
        )
        self.format_inst = kwargs.get("format_inst", format_inst)

    def set_schema(self, label_schema, label_names):
        """
        A helper function to set schema to be used in prompt template.

        Parameters
        ----------
        label_schema : []
            List of label objects
        label_names : []
            List of label names to be used for annotation, by default all labels
        """
        if label_names:
            valid_label_names = {label["name"] for label in label_schema}
            label_names = [
                label_name
                for label_name in label_names
                if label_name in valid_label_names
            ]
        if not label_names or len(label_names) == 0:
            label_names = [label["name"] for label in label_schema]
        self.label_schema = label_schema
        self.label_names = label_names
        self.label_dic = {
            label["name"]: [o["text"] for o in label["options"]]
            for label in label_schema
            if label["name"] in label_names
        }

    def set_instruction(self, **kwargs):
        """
        Updates template's task instruction and/or formatting instruction.
        """
        self.task_inst = kwargs.get("task_inst", self.task_inst)
        self.is_json_template = kwargs.get("is_json_template", self.is_json_template)
        self.format_inst = kwargs.get("format_inst", self.format_inst)

    def build_template(self, task_inst, format_inst, f=lambda x: x):
        """
        A helper function to build template.
        Returns a stringified prompt template with input slot.

        Parameters
        ----------
        task_inst : str
            Task instruction template. Must include '{name}' and '{options}'.
        format_inst : str
            Formatting instruction template. Must include '{format_sample}'.
        f : function, optional
            Use color() to decorate string for print, by default lambda x:x

        Returns
        -------
        template : str
            Stringified prompt template with input slot
        """
        # task_inst -> instruction
        instruction = " ".join(
            [
                task_inst.format(
                    name=f(l), options=f(comma_join_list(self.label_dic[l]))
                )
                for l in self.label_names
            ]
        )

        # format_inst -> formatting
        if self.is_json_template == False:  # format 1 // <label name>: <option>
            format_slot = "{name}: {option}"
            format_sample = "\n".join(
                [
                    format_slot.format(name=l.capitalize(), option="<" + l + ">")
                    for l in self.label_names
                ]
            )
        else:  # format 2 // json
            format_slot = '"{name}": "{option}"'
            format_sample = (
                "{"
                + ", ".join(
                    [
                        format_slot.format(name=l.capitalize(), option="<" + l + ">")
                        for l in self.label_names
                    ]
                )
                + "}"
            )
        formatting = format_inst.format(format_sample=f(format_sample))

        input_slot = "Text: '''\n$input\n'''"
        # response_start_text = '{}: '.format(label_names[0].capitalize())
        template = (
            f"{instruction} {formatting}\n\n{input_slot}\n"  # + response_start_text
        )
        return template

    def set_template(self, **kwargs):
        """
        Updates template by updating task instruction and/or formatting instruction.
        """
        self.set_instruction(**kwargs)
        self.template = self.build_template(
            task_inst=self.task_inst, format_inst=self.format_inst, f=lambda x: x
        )
        # print("Prompt template saved")

    def get_template(self):
        """
        Returns the stringified prompt template with input slot.

        Returns
        -------
        string
            Stringified prompt template with input slot
        """
        if not self.template:
            self.set_template()
        return self.template

    def get_prompt(self, input_str: str, **kwargs):
        """
        Returns the prompt for a given input.

        Parameters
        ----------
        input_str : str
            input string to fill input slot

        Returns
        -------
        prompt : str
            a prompt template built with given input string
        """
        template = kwargs.get("template", self.template)
        prompt = Template(template).safe_substitute(input=input_str)
        return prompt

    def preview(self, records=[]):
        """
        Opens up a widget to modify prompt template and preview final prompt.

        Parameters
        ----------
        records : list, optional
            List of input objects to be used for prompt preview
        """
        if not records:
            records = [
                "[sample text goes here]",
                "use prompt_template.preview(records=['input text', 'another text']) to preview prompts",
            ]

        task_inst = Textarea(
            value=self.task_inst,
            placeholder="Type task instruction. It should include {name} and {options}.",
            description="Task Inst:",
            disabled=False,
            layout=Layout(height="auto", width="auto"),
        )

        format_inst = Textarea(
            value=self.format_inst,
            placeholder="Type formatting instruction. It should include {format_sample}.",
            description="Formatting:",
            disabled=True,
            layout=Layout(height="auto", width="auto"),
        )

        input_list = Dropdown(
            options=records,
            description="Input:",
            disabled=False,
            layout=Layout(width="auto"),
        )

        btn_refresh = Button(
            description="Preview Prompt",
            disabled=False,
            tooltip="Click me",
        )

        btn_save = Button(
            description="Save Prompt",
            disabled=False,
            tooltip="Click me",
            button_style="primary",
        )

        output_desc = Label(value="Generated prompt:")
        output = Output(layout={"border": "1px dotted black"})
        output.append_stdout(
            self.get_prompt(
                input_str=input_list.value,
                template=self.build_template(
                    task_inst=task_inst.value, format_inst=format_inst.value, f=color
                ),
            )
        )

        @output.capture(clear_output=True)
        def handle_change(btn):
            prompt = self.get_prompt(
                input_str=input_list.value,
                template=self.build_template(
                    task_inst=task_inst.value, format_inst=format_inst.value, f=color
                ),
            )
            print(prompt)

        def set_prompt(btn):
            self.set_template(task_inst=task_inst.value, format_inst=format_inst.value)

        # task_inst.observe(handle_change, names=['value'])
        # input_list.observe(handle_change, names=['value'])
        btn_refresh.on_click(handle_change)
        btn_save.on_click(set_prompt)

        display(
            VBox(
                [
                    task_inst,
                    format_inst,
                    input_list,
                    HBox([btn_refresh, btn_save]),
                    output_desc,
                    output,
                ]
            )
        )
