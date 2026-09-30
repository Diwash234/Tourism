"""
GraphQL schema support for the Tourism platform.
"""
try:
    import graphene
    from graphene_django import DjangoObjectType
    GRAPHQL_AVAILABLE = True
except ImportError:
    GRAPHQL_AVAILABLE = False


if GRAPHQL_AVAILABLE:
    class DestinationType(DjangoObjectType):
        class Meta:
            from .models import Destination
            model = Destination
            fields = ("id", "name", "slug", "description", "district", "province")

    class Query(graphene.ObjectType):
        all_destinations = graphene.List(DestinationType)
        destination = graphene.Field(DestinationType, slug=graphene.String())

        def resolve_all_destinations(self, info):
            from .models import Destination
            return Destination.objects.filter(is_published=True)

        def resolve_destination(self, info, slug):
            from .models import Destination
            try:
                return Destination.objects.get(slug=slug, is_published=True)
            except Exception:
                return None

    schema = graphene.Schema(query=Query)
else:
    schema = None
