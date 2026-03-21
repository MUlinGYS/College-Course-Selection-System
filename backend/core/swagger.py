from drf_spectacular.openapi import AutoSchema
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, inline_serializer
from rest_framework import serializers


class ProjectAutoSchema(AutoSchema):
    def get_operation_id(self):
        operation_id = super().get_operation_id()
        if not operation_id.endswith("_retrieve"):
            return operation_id

        if "{" in self.path:
            return operation_id.replace("_retrieve", "_detail")

        return operation_id.replace("_retrieve", "_list")


def paginated_response(name, item_serializer):
    serializer_field = item_serializer(many=True) if isinstance(item_serializer, type) else item_serializer
    return inline_serializer(
        name=name,
        fields={
            "count": serializers.IntegerField(),
            "page": serializers.IntegerField(),
            "page_size": serializers.IntegerField(),
            "total_pages": serializers.IntegerField(),
            "next": serializers.URLField(allow_null=True, required=False),
            "previous": serializers.URLField(allow_null=True, required=False),
            "results": serializer_field,
        },
    )


PAGINATION_PARAMETERS = [
    OpenApiParameter(
        name="paginate",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        description="传入 `1` 时启用分页返回结构。",
    ),
    OpenApiParameter(
        name="page",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="页码，从 1 开始。仅在 `paginate=1` 时生效。",
    ),
    OpenApiParameter(
        name="page_size",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="每页条数，默认 10，最大 100。仅在 `paginate=1` 时生效。",
    ),
]


KEYWORD_PARAMETER = OpenApiParameter(
    name="q",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="关键字模糊搜索。",
)


TERM_ID_PARAMETER = OpenApiParameter(
    name="term_id",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description="按学期 ID 筛选。",
)


ROUND_ID_PARAMETER = OpenApiParameter(
    name="round_id",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description="按轮次 ID 筛选。",
)


SECTION_ID_PARAMETER = OpenApiParameter(
    name="section_id",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description="按开课班级 ID 筛选。",
)


COURSE_ID_PARAMETER = OpenApiParameter(
    name="course_id",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description="按课程 ID 筛选。",
)


TEACHER_ID_PARAMETER = OpenApiParameter(
    name="teacher_id",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description="按教师用户 ID 筛选。",
)


STUDENT_ID_PARAMETER = OpenApiParameter(
    name="student_id",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description="按学生用户 ID 筛选。",
)


ROLE_PARAMETER = OpenApiParameter(
    name="role",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="按角色筛选，可选值：`student`、`teacher`、`admin`。",
)


STATUS_PARAMETER = OpenApiParameter(
    name="status",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="按状态筛选，具体可选值以该接口业务状态为准。",
)
