from rest_framework import serializers

from .models import Round, Term


class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = ["id", "name", "start_date", "end_date", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("结束日期不能早于开始日期")

        return attrs


class RoundSerializer(serializers.ModelSerializer):
    term_name = serializers.CharField(source="term.name", read_only=True)

    class Meta:
        model = Round
        fields = [
            "id",
            "term",
            "term_name",
            "name",
            "start_at",
            "end_at",
            "target_scope",
            "max_courses",
            "allow_drop",
            "enabled",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "term_name"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        start_at = attrs.get("start_at", getattr(self.instance, "start_at", None))
        end_at = attrs.get("end_at", getattr(self.instance, "end_at", None))

        if start_at and end_at and start_at >= end_at:
            raise serializers.ValidationError("结束时间必须晚于开始时间")

        return attrs
