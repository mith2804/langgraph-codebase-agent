from agent.graph import build_graph


app = build_graph()

question = "What libraries are imported in app.py?"

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