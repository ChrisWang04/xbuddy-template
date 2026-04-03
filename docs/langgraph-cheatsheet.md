# LangGraph Cheatsheet

Quick reference for the LangGraph patterns used in this project.

## StateGraph

```python
from langgraph.graph import StateGraph, MessagesState
from langgraph.constants import START, END

class MyState(MessagesState):
    current_section: str = "intro"
    finished: bool = False

graph = StateGraph(MyState)
```

## Adding Nodes

A node is an async function that takes state and config, returns updated state.

```python
async def my_node(state: MyState, config: RunnableConfig) -> MyState:
    # Read from state
    section = state["current_section"]
    # Return updates (only changed fields)
    return {"current_section": "next_section"}

graph.add_node("my_node", my_node)
```

## Edges

```python
# Fixed edge: A always goes to B
graph.add_edge("node_a", "node_b")

# Conditional edge: route based on state
def my_router(state: MyState) -> str:
    if state["finished"]:
        return "end_node"
    return "continue_node"

graph.add_conditional_edges(
    "node_a",
    my_router,
    {"end_node": "end_node", "continue_node": "continue_node"},
)
```

## Compiling

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app = graph.compile(checkpointer=memory)
```

## Invoking

```python
# Sync
result = app.invoke(
    {"messages": [HumanMessage(content="hello")]},
    config={"configurable": {"thread_id": "abc123", "user_id": 1}},
)

# Streaming
async for event in app.astream(input, config):
    # event contains node outputs
    pass
```

## MessagesState

`MessagesState` automatically manages a `messages: list[BaseMessage]` field.
When you return `{"messages": [new_message]}`, it appends (doesn't replace).

## Key concepts

- **State**: shared dict that flows through all nodes
- **Nodes**: functions that read state, do work, return updates
- **Edges**: connections between nodes (fixed or conditional)
- **Checkpointer**: persists state between invocations (same thread_id = resumed conversation)
- **Config**: runtime config passed to every node (user_id, thread_id, etc.)

## Further reading

- [LangGraph docs](https://langchain-ai.github.io/langgraph/)
- [StateGraph API](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.StateGraph)
