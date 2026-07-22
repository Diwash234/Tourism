from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from .models import Destination, Alert


User = get_user_model()



class AdminStatsView(APIView):

    permission_classes = [IsAdminUser]


    def get(self, request):

        return Response({

            "users": User.objects.count(),

            "destinations":
                Destination.objects.count(),

            "alerts":
                Alert.objects.count()

        })



class AdminUsersView(APIView):

    permission_classes = [IsAdminUser]


    def get(self, request):

        users = User.objects.all()

        data=[]

        for user in users:

            data.append({

                "id":user.id,

                "username":user.username,

                "email":user.email,

                "is_active":user.is_active,

                "is_staff":user.is_staff

            })


        return Response(data)



class UpdateUserStatusView(APIView):

    permission_classes=[IsAdminUser]


    def put(self,request,id):

        user=User.objects.get(id=id)


        user.is_active=request.data.get(
            "is_active",
            user.is_active
        )

        user.save()


        return Response({

            "message":
            "User status updated"

        })



class AdminDestinationsView(APIView):

    permission_classes=[IsAdminUser]


    def get(self,request):

        destinations=Destination.objects.all()


        return Response([

            {
            "id":d.id,
            "name":d.name,
            "city":d.city,
            "status":d.status
            }

            for d in destinations

        ])



    def post(self,request):

        destination=Destination.objects.create(
            **request.data
        )


        return Response({

            "id":destination.id,

            "message":
            "Destination created"

        })



class AdminDestinationDetailView(APIView):

    permission_classes=[IsAdminUser]


    def put(self,request,id):

        destination=Destination.objects.get(id=id)


        for key,value in request.data.items():

            setattr(
                destination,
                key,
                value
            )


        destination.save()


        return Response({

            "message":
            "Destination updated"

        })


    def delete(self,request,id):

        Destination.objects.filter(
            id=id
        ).delete()


        return Response({

            "message":
            "Deleted"

        })



class AdminAlertsView(APIView):

    permission_classes=[IsAdminUser]


    def get(self,request):

        alerts=Alert.objects.all()


        return Response([

            {
            "id":a.id,
            "title":a.title,
            "severity":a.severity
            }

            for a in alerts

        ])


    def post(self,request):

        alert=Alert.objects.create(
            **request.data
        )


        return Response({

            "message":
            "Alert created"

        })
