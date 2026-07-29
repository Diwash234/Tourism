import os
from dotenv import load_dotenv

load_dotenv()



def ask_ai(
    message,
    context=""
):


    provider = os.getenv(
        "AI_PROVIDER",
        "groq"
    )



    if provider == "groq":

        return groq_response(
            message,
            context
        )


    elif provider == "gemini":

        return gemini_response(
            message,
            context
        )


    return None






def groq_response(
    message,
    context
):

    from groq import Groq


    client = Groq(
        api_key=os.getenv(
            "GROQ_API_KEY"
        )
    )


    prompt = f"""

You are Nepal Tourism Assistant.

Answer the user question.

Use this information if available:

{context}


User:
{message}

"""


    response = client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=[
            {
                "role":"system",
                "content":
                "You help tourists travelling in Nepal."
            },
            {
                "role":"user",
                "content":prompt
            }
        ],

        temperature=0.5
    )


    return response.choices[0].message.content







def gemini_response(
    message,
    context
):


    import google.generativeai as genai


    genai.configure(
        api_key=os.getenv(
            "GEMINI_API_KEY"
        )
    )


    model = genai.GenerativeModel(
        "gemini-2.0-flash"
    )


    prompt=f"""

You are Nepal Tourism Assistant.


Context:

{context}


Question:

{message}

"""


    response=model.generate_content(
        prompt
    )


    return response.text