from agent.graph import build_graph

app = build_graph()

question = "What functions are defined in nodes.py?"

result = app.invoke({
"question": question,
"plan": [],
"current_task": "",
"answer": "",
})

print("\n==============================")
print("FINAL RESULT")
print("==============================")

print(result)
