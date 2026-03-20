from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination, should_paginate
from core.permissions import IsAdmin
from .models import Round, Term
from .serializers import RoundSerializer, TermSerializer


class AdminWriteGuardMixin:
    def ensure_admin(self, request):
        if IsAdmin().has_permission(request, self):
            return None

        return Response({"message": "仅管理员可执行该操作"}, status=status.HTTP_403_FORBIDDEN)


class TermListCreateView(AdminWriteGuardMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Term.objects.all().order_by("id")

        if should_paginate(request):
            paginator = StandardPagination()
            page = paginator.paginate_queryset(queryset, request, view=self)
            return paginator.get_paginated_response(TermSerializer(page, many=True).data)

        serializer = TermSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        serializer = TermSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TermDetailView(AdminWriteGuardMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, term_id):
        return get_object_or_404(Term, pk=term_id)

    def get(self, request, term_id):
        term = self.get_object(term_id)
        return Response(TermSerializer(term).data)

    def put(self, request, term_id):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        term = self.get_object(term_id)
        serializer = TermSerializer(term, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class RoundListCreateView(AdminWriteGuardMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Round.objects.select_related("term").all().order_by("id")
        term_id = request.query_params.get("term_id")

        if term_id:
            queryset = queryset.filter(term_id=term_id)

        if should_paginate(request):
            paginator = StandardPagination()
            page = paginator.paginate_queryset(queryset, request, view=self)
            return paginator.get_paginated_response(RoundSerializer(page, many=True).data)

        serializer = RoundSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        serializer = RoundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RoundDetailView(AdminWriteGuardMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, round_id):
        return get_object_or_404(Round.objects.select_related("term"), pk=round_id)

    def get(self, request, round_id):
        round_instance = self.get_object(round_id)
        return Response(RoundSerializer(round_instance).data)

    def put(self, request, round_id):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        round_instance = self.get_object(round_id)
        serializer = RoundSerializer(round_instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
