from model.recommendation.recommendation_engine import recommend


# User search example
query = "karnali"


results = recommend(
    query,
    top_n=5
)


print("========================")
print("SEARCH:")
print(query)

print("========================")
print("RECOMMENDED PLACES")


for place in results:

    print("------------------------")

    print(
        "Name:",
        place["name"]
    )

    print(
        "City:",
        place["city"]
    )

    print(
        "Type:",
        place["type"]
    )

    print(
        "Category:",
        place["category"]
    )

    print(
        "Latitude:",
        place["latitude"]
    )

    print(
        "Longitude:",
        place["longitude"]
    )

    print(
        "Similarity:",
        place["similarity_score"]
    )

    # python training/train_recommendation_model.py
    # python test_recommendation.py