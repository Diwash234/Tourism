from openai import OpenAI


client=OpenAI()


def translate(
    text,
    language
):

    response=client.chat.completions.create(

        model="gpt-4.1-mini",

        messages=[

            {
            "role":"system",
            "content":
            f"Translate into {language}"
            },

            {
            "role":"user",
            "content":text
            }

        ]

    )


    return response.choices[0].message.content