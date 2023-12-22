import sys
sys.path.append('../03_RAG')
from lamini import MistralRunner
from directory_loader import DefaultChunker, DirectoryLoader

import os
import csv
import json

from tqdm import tqdm


# Load the data
loader = DirectoryLoader(
    "../03_RAG/data", # path to data directory
    batch_size=512,
    chunker=DefaultChunker(chunk_size=512, step_size=512),
)

chunks = []
for chunk in tqdm(loader):
    chunks.extend(chunk)

print(chunks)
print(len(chunks))
# Generate questions for each chunk
runner = MistralRunner()

questions_type = {'question_1': 'str',
                  'question_2': 'str',
                  'question_3': 'str'}

print("---------------------\nGenerating Questions\n---------------------")
chunks = chunks[4:5]
questions = []

for chunk in chunks:
    print(chunk)
    prompt = (
        "'"
        + chunk
        + "'\nThe preceding single-quoted text is an excerpt describing various investments made by BigMoney Ventures. Generate three diverse questions about the investments.  Only generate questions that can be answered using information from the preceding single-quoted text.  Do not ask questions that require additional information outside of the preceding single-quoted text."
    )
    system_prompt = "You are an expert investment analyst working at BigMoney Ventures."

    result = runner(prompt, output_type=questions_type, system_prompt=system_prompt)
    print("1.", result['question_1'])
    print("2.", result['question_2'])
    print("3.", result['question_3'])
    questions.append([chunk, result['question_1']])
    questions.append([chunk, result['question_2']])
    questions.append([chunk, result['question_3']])    
    
print("---------------------\nGenerating Answers\n---------------------")
final_data_array = []
# Generate Answers for each Answer
for index, question in enumerate(questions):
    # Run the model
    prompt = (
        "'"
        + question[0]  # chunk
        + "'\nThe preceding single-quoted text is an excerpt describing various investment made by BigMoney Ventures.  Answer the following question using information from the single-quoted text.  If you cannot answer the question using only the single-quoted text, respond only with the statement: \"I don't know.\"\n\n"
        + question[1]  # question about the chunk
    )
    system_prompt = "You are an expert in the field of investments."
    answer = runner(prompt, system_prompt=system_prompt)
    print(f"---------------------Answer for question {index}---------------------")
    print(answer)
    print(f"---------------------------------------------------------------------")
    final_data_array.append([question[0], question[1], answer])

# Save the questions, answers, and data in a csv file (logging)
with open("qa_data/generated_data.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["Data", "Questions", "Answers"])
    for data in final_data_array:
        writer.writerow(data)

# And save to a json file for logging
with open("qa_data/generated_data.json", "w") as f:
    json.dump(final_data_array, f, indent=4)

# And finally, save the format that will actually be submitted to the model for finetuning
training_data = [
    [
        {"data": data[0], "question": data[1]},
        {"answer": data[2]},
    ]
    for data in final_data_array
]

with open("qa_data/generated_data_finetuning.json", "w") as f:
    json.dump(training_data, f, indent=4)
