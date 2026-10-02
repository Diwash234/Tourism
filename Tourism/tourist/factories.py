"""
Test factories for generating test data.
"""
import factory
from factory.django import DjangoModelFactory

from .models import User, Destination, Category, Review


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = "tourist"
    is_verified = True
    is_active = True


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.Sequence(lambda n: f"category-{n}")
    is_active = True


class DestinationFactory(DjangoModelFactory):
    class Meta:
        model = Destination

    name = factory.Sequence(lambda n: f"Destination {n}")
    slug = factory.Sequence(lambda n: f"destination-{n}")
    description = factory.Faker("text")
    district = factory.Faker("city")
    province = factory.Faker("state")
    latitude = factory.Faker("latitude")
    longitude = factory.Faker("longitude")
    is_published = True
    is_featured = False
    category = factory.SubFactory(CategoryFactory)


class ReviewFactory(DjangoModelFactory):
    class Meta:
        model = Review

    user = factory.SubFactory(UserFactory)
    destination = factory.SubFactory(DestinationFactory)
    rating = factory.Faker("random_int", min=1, max=5)
    comment = factory.Faker("text")
    is_approved = True
