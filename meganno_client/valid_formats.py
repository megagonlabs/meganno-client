model_config_options = {
    "completions": {
        "valid_format": {
            "type": "object",
            "required": ["model"],  # 'model' property is required
            "properties": {
                "model": {
                    "type": "string",
                    "enum": [
                        "text-davinci-003",
                        "text-davinci-002",
                        "text-davinci-001",
                        "text-curie-001",
                        "text-babbage-001",
                        "text-ada-001",
                        "davinci",
                        "curie",
                        "babbage",
                        "ada",
                    ],
                },
                "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                "suffix": {"type": "string"},
                "max_tokens": {"type": "integer"},
                "top_p": {"type": "number"},
                "n": {"type": "integer", "enum": [1]},
                "stream": {"type": "boolean"},
                "logprobs": {"type": "integer", "maximum": 5},
                "echo": {"type": "boolean"},
                "stop": {"type": ["array", "string"]},
                "presence_penalty": {"type": "number", "minimum": -2.0, "maximum": 2.0},
                "frequency_penalty": {
                    "type": "number",
                    "minimum": -2.0,
                    "maximum": 2.0,
                },
                "best_of": {"type": "integer"},
                "logit_bias": {"type": "object"},
                "user": {"type": "string"},
            },
        }
    },
    "chat": {
        "valid_format": {
            "type": "object",
            "required": ["model"],
            "properties": {
                "messages": {
                    "type": "array",
                },
                "model": {
                    "type": "string",
                    "enum": [
                        "gpt-4 ",
                        "gpt-4-1106-preview",
                        "gpt-4-vision-preview",
                        "gpt-4-32k",
                        "gpt-3.5-turbo",
                        "gpt-3.5-turbo-16k",
                        "gpt-3.5-turbo-0125"
                    ],
                },
                "frequency_penalty": {
                    "type": "number",
                    "default": 0,
                    "minimum": -2.0,
                    "maximum": 2.0,
                },
                "logit_bias": {"type": "object"},
                "max_tokens": {
                    "type": "integer",
                },
                "n": {"type": "integer", "default": 1, "enum": [1]},
                "presence_penalty": {
                    "type": "number",
                    "default": 0,
                    "minimum": -2.0,
                    "maximum": 2.0,
                },
                "response_format": {"type": "object"},
                "seed": {
                    "type": "integer",
                },
                "stop": {"type": ["array", "string"]},
                "stream": {"type": "boolean"},
                "temperature": {
                    "type": "number",
                    "default": 1,
                    "minimum": 0,
                    "maximum": 2,
                },
                "top_p": {
                    "type": "number",
                    "default": 1,
                },
                "tools": {
                    "type": "array",
                },
                "tool_choice": {"type": ["object", "string"]},
                "user": {"type": "string"},
            },
        }
    },
}
