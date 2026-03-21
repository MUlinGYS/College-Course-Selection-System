from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination, should_paginate
from core.permissions import IsAdmin
from core.swagger import PAGINATION_PARAMETERS, TERM_ID_PARAMETER, paginated_response
from .models import Round, Term
from .serializers import RoundSerializer, TermSerializer


class AdminWriteGuardMixin:
    def ensure_admin(self, request):
        if IsAdmin().has_permission(request, self):
            return None

        return Response({"message": "仅管理员可执行该操作"}, status=status.HTTP_403_FORBIDDEN)


class TermListCreateView(AdminWriteGuardMixin, APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TermSerializer

    @extend_schema(
        operation_id="terms_list",
        summary="获取学期列表",
        description="查询学期列表。传入 `paginate=1` 时，返回真实分页结构。",
        parameters=PAGINATION_PARAMETERS,
        responses=paginated_response("PaginatedTermListResponse", TermSerializer),
    )
    def get(self, request):
        queryset = Term.objects.all().order_by("id")

        if should_paginate(request):
            paginator = StandardPagination()
            page = paginator.paginate_queryset(queryset, request, view=self)
            return paginator.get_paginated_response(TermSerializer(page, many=True).data)

        serializer = TermSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(summary="创建学期", description="管理员创建新的学期。", request=TermSerializer, responses=TermSerializer)
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
    serializer_class = TermSerializer

    def get_object(self, term_id):
        return get_object_or_404(Term, pk=term_id)

    @extend_schema(operation_id="terms_detail", summary="获取学期详情", description="根据学期 ID 获取单个学期详情。", responses=TermSerializer)
    def get(self, request, term_id):
        term = self.get_object(term_id)
        return Response(TermSerializer(term).data)

    @extend_schema(summary="更新学期", description="管理员更新指定学期信息。", request=TermSerializer, responses=TermSerializer)
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
    serializer_class = RoundSerializer

    @extend_schema(
        operation_id="rounds_list",
        summary="获取轮次列表",
        description="查询选课轮次。支持按学期筛选；传入 `paginate=1` 时，返回真实分页结构。",
        parameters=PAGINATION_PARAMETERS + [TERM_ID_PARAMETER],
        responses=paginated_response("PaginatedRoundListResponse", RoundSerializer),
    )
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

    @extend_schema(summary="创建轮次", description="管理员创建选课轮次，并归属到指定学期。", request=RoundSerializer, responses=RoundSerializer)
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
    serializer_class = RoundSerializer

    def get_object(self, round_id):
        return get_object_or_404(Round.objects.select_related("term"), pk=round_id)

    @extend_schema(operation_id="rounds_detail", summary="获取轮次详情", description="根据轮次 ID 获取单个轮次详情。", responses=RoundSerializer)
    def get(self, request, round_id):
        round_instance = self.get_object(round_id)
        return Response(RoundSerializer(round_instance).data)

    @extend_schema(summary="更新轮次", description="管理员更新指定轮次的时间、范围和限制条件。", request=RoundSerializer, responses=RoundSerializer)
    def put(self, request, round_id):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        round_instance = self.get_object(round_id)
        serializer = RoundSerializer(round_instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
