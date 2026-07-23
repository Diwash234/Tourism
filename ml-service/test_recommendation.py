from model.recommendation.recommendation_engine import recommend


result = recommend(
    "mountain adventure trekking"
)


print("RESULT:")
print(result)


for place in result:
    print(place)
