import os
import requests
from time import sleep
from typing import Dict
import json


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_API_PATH = f"{OLLAMA_URL}/api/generate"

def call_ollama(prompt: str, retries: int = 2) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    
    attempt = 0
    print(f"Calling Ollama model {OLLAMA_MODEL} (attempt {attempt + 1})")
    print(f"Request payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(OLLAMA_API_PATH, json=payload)
    response.raise_for_status()
    
    # Print raw response for debugging
    #print(f"Raw response: {response.json()}")
    
    data = response.json()
    # print(f"Raw response: {data}")
    #print(f"Parsed JSON: {data['response']}")
    # print(f"Response type: {type(data['response'])}")
    
    if isinstance(data, Dict):
        text = data.get("response", "")
        return text
    
    return data
text = "Machine learning is augmenting human capabilities and making things possible—things that just a few years back were considered impossible. Take, for example, the protein folding problem. For about 50 years, the biology field assumed that solving this problem was beyond human capabilities. But with the might of AI and ML, folks at DeepMind were finally able to come up with a solution to this problem. ML-based applications are ubiquitous these days and they continue to evolve day by day. Before long we might also manage to build a fully autonomous driving vehicle. But then the question arises: how exactly do you make a machine learn? Let’s look at the two most well-known machine learning methods—supervised and unsupervised learning. We’ll deep dive into how they both work, and we’ll look at up-and-coming learning methods, too. Machines can learn We are very familiar with the paradigm of coding programs. Coding is akin to explicitly telling the machine what to do. The programmed machine cannot make a decision on its own. And it most certainly cannot handle a situation that it hasn’t been programmed for. This is like giving machines a fish when, really, we want to teach machines how to fish. In the field of AI and ML the way machines are made to learn generally fall under two categories: Supervised learning Unsupervised learning In a nutshell, the difference between these two methods is that in supervised learning we also provide the correct results in terms of labeled data. Labeled data in machine learning parlance means that we know the correct output values of the data beforehand. In unsupervised machine learning, the data is not labeled. So, in unsupervised learning the machines are left to fend for themselves, you may ask? Not quite. (Understand the role of data annotation in ML.) How supervised machine learning works The notion of ‘supervision’ in supervised machine learning comes from the labeled data. With the help of labels, the predictions a machine learning model makes can be compared against the known correct values. This helps with gauging the accuracy of the model and calculation of loss. This in turn can be used as a feedback to the model to further improve its predictions. (This labeled data seems like the answer to all our problems, right? What could ever go wrong!) But, as they say: with great power comes great responsibilities. We need to be careful with the extent we used the labels in during the supervised learning or in machine learning jargon how much we train our model. The pitfall of too much training is overfitting. This is what happens when the ML model learns the training data so well that, when new data comes in, the model often fails to perform correctly. (Unsupervised learning algorithm can also face overfitting, but it is more prevalent in supervised learning algorithms. Eagerness to train one more epoch, for the sake of better accuracy, often leads into overfitting.) Broadly, supervised machine learning finds its application in 2 types of tasks: Classification Regression"
MCQ_prompt = (
    "You are an educational question generator. From the provided text, create:\n"
    f"- {2} multiple-choice questions (4 options each), with one correct option and a short rationale.\n"
    "Return the result as a JSON object: {\"Question\": [{\"question\":...,\"options\":[...],\"answer_index\":0,\"rationale\":...}, ...]}\n\n"
    "Text:\n"
    f"{text}\n\n"
    "Keep questions at difficulty level roughly matching the requested following difficulty level (1-5).\n"
    "Difficulty level 1: Basic concepts, definitions, and explanations.\n"
    "Difficulty level 2: Intermediate concepts, applications, and examples.\n"
    "Difficulty level 3: Advanced concepts, theorems, and proofs.\n"
    "Difficulty level 4: Highly specialized concepts, theories, and applications.\n"
    "Difficulty level 5: Expert-level concepts, research-level topics, and complex problems.\n"
    f"Difficulty level: {2}\n"
)
TF_prompt = (
    "You are an educational question generator. From the provided text, create:\n"
    f"- {2} True/False questions with the correct boolean and a short rationale.\n"
    "Return the result as a JSON object: {\"Question\": [{\"question\":...,\"answer\":true,\"rationale\":...}, ...]}\n\n"
    "Text:\n"
    f"{text}\n\n"
    "Keep questions at difficulty level roughly matching the requested following difficulty level (1-5).\n"
    "Difficulty level 1: Basic concepts, definitions, and explanations.\n"
    "Difficulty level 2: Intermediate concepts, applications, and examples.\n"
    "Difficulty level 3: Advanced concepts, theorems, and proofs.\n"
    "Difficulty level 4: Highly specialized concepts, theories, and applications.\n"
    "Difficulty level 5: Expert-level concepts, research-level topics, and complex problems.\n"
    f"Difficulty level: {2}\n"
)

    
# raw = call_ollama(TF_prompt)
# parsed = json.loads(raw)

# print("THE FINAL ", parsed)

from app.services.embeddings import add_documents, search

docs = [{"id": "doc1", "text": "Test about AI agents.", "source": "manual"}]
add_documents(docs)

results = search("What is AI?")
print(results)
