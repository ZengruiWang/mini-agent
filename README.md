# mini-agent

A minimal LLM agent that talks to a model provider, calls tools, and maintains conversation history.

## Project structure

```
mini-agent/
├── main.py                 # Entry point
├── agent.py                # Agent loop and orchestration
├── models/
│   └── message.py          # Internal conversation types
├── providers/
│   ├── base_provider.py    # Provider interface (ABC)
│   └── ollama_provider.py  # Ollama SDK adapter
└── tools/
    ├── base_tool.py        # Tool base class
    └── calculator.py       # Calculator tool
```

## Layer overview

| Layer | Files | Role |
|---|---|---|
| Entry | `main.py` | Wire up agent and run a task |
| Agent | `agent.py` | Loop, message history, tool execution |
| Models | `models/message.py` | Internal conversation types |
| Tools | `tools/` | Tool definitions and logic |
| Providers | `providers/` | Translate to/from provider APIs |

**Key idea:** `Message` is the internal conversation format. Each provider translates at the boundary. The agent owns the loop and never calls Ollama directly.

## Class diagram

```mermaid
classDiagram
    direction TB

    class Role {
        <<enumeration>>
        SYSTEM
        USER
        ASSISTANT
        TOOL
    }

    class Message {
        +Role role
        +str content
        +str thinking
        +list~ToolCall~ tool_calls
    }

    class ToolCall {
        +ToolCallFunction function
        +str id
    }

    class ToolCallFunction {
        +str name
        +dict arguments
    }

    class StreamChunk {
        +str content
        +str thinking
        +list~ToolCall~ tool_calls
        +bool done
    }

    class Tool {
        +str name
        +str description
        +dict inputs
        +str output_type
    }

    class Calculator {
        +calculate(expression) float
    }

    class BaseProvider {
        <<abstract>>
        +chat(model, messages, tools) Message
        +stream_chat(model, messages, tools) Iterator~StreamChunk~
    }

    class OllamaProvider {
        -_to_ollama_message(msg) OllamaMessage
        -_from_ollama_message(msg) Message
        -_to_ollama_tool(tool) OllamaTool
        -_from_ollama_tool_calls(calls) list~ToolCall~
    }

    class Agent {
        -BaseProvider provider
        -str model
        -list~Tool~ tools
        -list~Message~ messages
        -bool stream
        -int max_turns
        +run(task) Message
        -_loop_until_done() Message
        -_call_model() Message
        -_execute_tool(tool_call) Any
        -_collect_stream(chunks) Message
    }

    class OllamaMessage {
        <<external: ollama SDK>>
    }

    class OllamaTool {
        <<external: ollama SDK>>
    }

    Message --> Role
    Message --> ToolCall
    ToolCall --> ToolCallFunction

    Calculator --|> Tool
    OllamaProvider --|> BaseProvider

    Agent --> BaseProvider : uses
    Agent --> Message : owns messages[]
    Agent --> Tool : owns tools[]
    Agent ..> Calculator : executes

    OllamaProvider --> Message : maps to/from
    OllamaProvider --> StreamChunk : yields
    OllamaProvider --> Tool : converts
    OllamaProvider --> OllamaMessage : API wire format
    OllamaProvider --> OllamaTool : API wire format
```

## Component relationships

```mermaid
flowchart TB
    subgraph Entry["Entry"]
        main["main.py"]
    end

    subgraph AgentLayer["Agent Layer"]
        Agent["Agent\n(orchestration + loop)"]
    end

    subgraph Domain["Domain Models"]
        Message["Message / Role / ToolCall"]
        StreamChunk["StreamChunk"]
    end

    subgraph ToolsLayer["Tools"]
        Tool["Tool (base)"]
        Calculator["Calculator"]
    end

    subgraph ProviderLayer["Providers"]
        BaseProvider["BaseProvider (ABC)"]
        OllamaProvider["OllamaProvider"]
    end

    subgraph External["External"]
        OllamaAPI["Ollama API / SDK"]
    end

    main --> Agent
    Agent --> Message
    Agent --> Tool
    Agent --> BaseProvider
    Calculator --> Tool
    OllamaProvider --> BaseProvider
    OllamaProvider --> Message
    OllamaProvider --> StreamChunk
    OllamaProvider --> OllamaAPI
    Agent ..>|execute| Calculator
```

## Runtime flow (one user turn with tools)

```mermaid
sequenceDiagram
    participant User
    participant Main
    participant Agent
    participant Provider as OllamaProvider
    participant Ollama as Ollama API
    participant Calc as Calculator

    User->>Main: task
    Main->>Agent: run(task)

    Agent->>Agent: append Message(USER)
    loop until no tool_calls or max_turns
        Agent->>Provider: chat(messages, tools)
        Provider->>Provider: Message → OllamaMessage
        Provider->>Provider: Tool → OllamaTool
        Provider->>Ollama: POST /api/chat
        Ollama-->>Provider: response
        Provider->>Provider: OllamaMessage → Message
        Provider-->>Agent: Message (maybe tool_calls)

        alt has tool_calls
            Agent->>Calc: calculate(expression)
            Calc-->>Agent: result
            Agent->>Agent: append Message(TOOL)
        else no tool_calls
            Agent-->>Main: final Message
        end
    end

    Main->>User: print(reply.content)
```

## Agent loop

The agent stops when the model returns a message **without** `tool_calls`, or when `max_turns` is reached.

```
User message
     ↓
Call model ──→ tool_calls? ──Yes──→ Execute tools ──┐
                No                                  │
                 ↓                                  │
           Return final answer                      │
                 ↑                                  │
                 └──────────────────────────────────┘
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Requires [Ollama](https://ollama.com/) running locally with a model pulled, e.g.:

```bash
ollama pull qwen3:8b
```

## Run

```bash
python main.py
```

## Example

```python
from agent import Agent
from providers.ollama_provider import OllamaProvider
from tools.calculator import Calculator

agent = Agent(
    provider=OllamaProvider(),
    model="qwen3:8b",
    tools=[Calculator()],
    system_prompt="You are a helpful assistant. Use tools when needed.",
)

reply = agent.run("what is 1 + 1")
print(reply.content)
```
