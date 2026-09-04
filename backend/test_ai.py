from ai.services import ask_ai, reset_chat


print("PATIENT 1")

print("You: I have a headache")
print("AI:", ask_ai("I have a headache"))

print("You: Since yesterday")
print("AI:", ask_ai("Since yesterday"))


print("\n--- NEW PATIENT ---\n")

reset_chat()


print("PATIENT 2")

print("You: I have chest pain")
print("AI:", ask_ai("I have chest pain"))