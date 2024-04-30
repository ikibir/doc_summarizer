import os
import json
from glob import glob
from pypdf import PdfReader
from openai import OpenAI

cheatsheet = {
    "Business Strategy": [
        "Key words/context",
        "Board top priorities or areas of focus",
        "Management team top priorities or areas of focus",
        "This may be over the short, medium or long term",
        "References to geographical, product and customer segments",
        "References to transformation objectives",
        "References to the growth of their people and teams",
        "References to the financial health/performance of the business",
        "References to sustainability and equality within the workplace",
        "References to innovation",
        "M&A (mergers & acquisitions)",
        "Looking ahead"
    ],
    "Business Growth and Performance (financials)": [
        "Revenue and profit (EBIT) growth or decline and trends over previous fiscal or quarterly periods",
        "Gross and operating profit margin with the trends over previous fiscal and quarterly periods",
        "Market share position and expansion",
        "Capital allocation position",
        "Balance sheet strength (position of assets and liabilities) and equally the trends over previous fiscal or quarterly periods",
        "Cost savings",
        "Free cash flow and the trends over previous fiscal or quarterly periods",
        "Dividend performance",
        "Value for shareholders"
    ],
    "Known business risks": [
        "Competitor pressure",
        "Supply chain risk",
        "Reorganisation or business change programmes",
        "Inflation and cost pressure",
        "Litigation / solvency risk etc",
        "Legal or court activity",
        "Ethics / code of conduct / whistleblowing",
        "Bribery or corruption"
    ]
}


from langchain.text_splitter import CharacterTextSplitter
text_splitter = CharacterTextSplitter(
    separator = "\n",
    chunk_size = 30000
)

PAGE_LIMIT = 50
def load_pdf(filepath):
    global PAGE_LIMIT
    reader = PdfReader(filepath)
    full_text = "" 
    
    print("reading pdf..")
    #TODO: remove break
    for index, page in enumerate(reader.pages):
        text = page.extract_text() 
        full_text += text
        if index >= PAGE_LIMIT: break

    return full_text

def load_doc(filepath):
    pass

def load_html(filepath):
    pass

def load_all_documents(folder):
    # TODO: remove break
    files = glob(f"{folder}/*")
    full_text = ""
    for file in files:
        print("file: ", file)
        full_text += "\n\n DOCUMENT STARTS HERE \n\n"
        if file.endswith(".pdf"):
            text = load_pdf(file)
        elif file.endswith(".doc"):
            text = load_doc(file)
        elif file.endswith(".html"):
            text = load_html(file)
        full_text += text
        full_text += "\n\n DOCUMENT ENDS HERE \n\n"
        break

    return full_text

def format_chunk(text, index, size):
    return f"""=== INSTRUCTIONS ===
Your task is ONLY to confirm receipt of this chunk, chunk {index}/{size}, and not generate any text.
=== SCRIPT CHUNK {index}/{size} ===
{text}
=== END OF CHUNK ==="""

def chunker(full_text):
    global text_splitter
    print(type(full_text))
    docs = text_splitter.create_documents([full_text])
    chunk_counter = len(docs)

    print(chunk_counter, " number of chunks created from documents")
    data = []
    for index, doc in enumerate(docs):
        text = doc.page_content
        formatted_chunk = format_chunk(text, index+1, chunk_counter)
        with open(f"temp/{index}.txt","w",encoding="utf-8") as f:
            f.write(formatted_chunk)
        data.append({"role": "user", "content": formatted_chunk})
    
    return data


    #print(docs[-1].page_content)

def feed_doc_to_gpt(client, data):
    chunk_counter = len(data)
    for index, chunk in enumerate(data):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages = [chunk, {"role":"system", "content":f"Got it, confirming receipt of script chunk {index+1}/{chunk_counter}."}]
        )

def ask_gpt(client, header, data):
    global cheatsheet
    keys = cheatsheet[header]
    grouped_keys = [keys[i:i+3] for i in range(0,len(keys),3)]

    responses = []
    # Get the informations from GPT
    for keywords in grouped_keys:
        keywords_fixed = ", ".join(["\""+key+"\"" for key in keywords])
    
        content = f"""Summarize the {header} of the company based on given documents with given keywords.
    keywords = {keywords_fixed}
    Do not create too long text. If you don't have enough information tell me "NO INFORMATION".
    """
        #messages = [{"role": "user", "content": content}]    
        messages = [{"role":"user", "content":"ceo is the elon musk?"}, {"role": "user", "content": "who is the ceo?"}]    
    
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=messages
        )
        responses.append({
            "header": header,
            "keywords": keywords,
            "input": content,
            "output": response.choices[0].message.content
            })
        break

    return responses

if __name__ == "__main__":
    # Pre-define paths&variables
    base_path = "Examples"
    full_text = load_all_documents(base_path)
    data = chunker(full_text)

    # LOGIN OPENAI
    client = OpenAI(api_key="key-here")
    feed_doc_to_gpt(client, data)
    responses = ask_gpt(client, "Business Strategy", data)
    
    print("response: ", responses)
    """with open("Business Strategy output.json", "w") as f:
        json.dump(responses, f, indent=4)

    responses = ask_gpt(client, "Business Growth and Performance (financials)", data)
    
    print("response count: ", len(responses))
    with open("Business Growth and Performance (financials) output.json", "w") as f:
        json.dump(responses, f, indent=4)
    """
    for response in responses:
        print("input: ", response["input"])
        print("output: ", response["output"])
        print("-------------------------------")  

