from rest_framework.response import Response
from rest_framework.views import APIView

from tourist.models import Destination, User
from tourist.permissions import IsRoleOrAbove

from .engine import generate_destination_content


class GenerateDestinationContentView(APIView):
    """
    POST /api/v1/destinations/<slug>/generate-content/
    Admin/Content-Moderator+ only. Returns generated content WITHOUT
    saving by default (so a moderator can review) -- pass {"save": true}
    to write it directly onto the Destination.
    """
    permission_classes = [IsRoleOrAbove(User.Role.CONTENT_MODERATOR)]

    def post(self, request, slug):
        destination = Destination.objects.filter(slug=slug).first()
        if not destination:
            return Response({"detail": "Destination not found."}, status=404)

        generated = generate_destination_content(
            destination.name, destination.city, destination.country or "Nepal",
            existing_description=destination.description,
        )
        if not generated:
            return Response(
                {"detail": "Content generation failed -- no AI provider configured or all providers unavailable."},
                status=503,
            )

        if request.data.get("save"):
            destination.description = generated.get("description", destination.description)
            destination.short_description = generated.get("short_description", destination.short_description)
            destination.best_time_to_visit = generated.get("best_time_to_visit", destination.best_time_to_visit)
            destination.content_ai_generated = True
            destination.save(update_fields=["description", "short_description", "best_time_to_visit", "content_ai_generated"])
            return Response({"saved": True, **generated})

        return Response({"saved": False, **generated})