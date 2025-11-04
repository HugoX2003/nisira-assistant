from rest_framework import serializers

from .models import Rating, ExperimentRun


class RatingRequestSerializer(serializers.Serializer):
    message_id = serializers.IntegerField(min_value=1)
    value = serializers.ChoiceField(choices=("like", "dislike", "clear"))
    comment = serializers.CharField(allow_blank=True, required=False, max_length=500)
    issue_tag = serializers.ChoiceField(
        choices=[choice[0] for choice in Rating.IssueTag.choices] + ["auto"],
        required=False,
        default=Rating.IssueTag.NONE,
    )


class RatingSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField(source="message.id", read_only=True)
    conversation_id = serializers.IntegerField(source="message.conversation_id", read_only=True)

    class Meta:
        model = Rating
        fields = (
            "id",
            "message_id",
            "conversation_id",
            "value",
            "comment",
            "issue_tag",
            "updated_at",
        )
        read_only_fields = fields


class ExperimentRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentRun
        fields = (
            "id",
            "name",
            "variant_name",
            "executed_by",
            "notes",
            "baseline_precision",
            "variant_precision",
            "delta_precision",
            "baseline_faithfulness",
            "variant_faithfulness",
            "delta_faithfulness",
            "baseline_latency",
            "variant_latency",
            "delta_latency",
            "guardrail_passed",
            "guardrail_reason",
            "created_at",
        )
        read_only_fields = (
            "delta_precision",
            "delta_faithfulness",
            "delta_latency",
            "guardrail_passed",
            "guardrail_reason",
            "created_at",
        )


class ExperimentRunCreateSerializer(serializers.ModelSerializer):
    guardrail_threshold_precision = serializers.FloatField(required=False, default=-0.01)
    guardrail_threshold_faithfulness = serializers.FloatField(required=False, default=-0.01)
    guardrail_threshold_latency = serializers.FloatField(required=False, default=0.3)

    class Meta:
        model = ExperimentRun
        fields = (
            "name",
            "variant_name",
            "executed_by",
            "notes",
            "baseline_precision",
            "variant_precision",
            "baseline_faithfulness",
            "variant_faithfulness",
            "baseline_latency",
            "variant_latency",
            "guardrail_threshold_precision",
            "guardrail_threshold_faithfulness",
            "guardrail_threshold_latency",
        )

    def create(self, validated_data):
        threshold_precision = validated_data.pop("guardrail_threshold_precision")
        threshold_faithfulness = validated_data.pop("guardrail_threshold_faithfulness")
        threshold_latency = validated_data.pop("guardrail_threshold_latency")

        experiment = ExperimentRun.objects.create(**validated_data)

        if experiment.delta_precision < threshold_precision:
            experiment.guardrail_passed = False
            experiment.guardrail_reason = (
                f"ΔPrecision ({experiment.delta_precision:.3f}) por debajo de {threshold_precision:.3f}"
            )
        elif experiment.delta_faithfulness < threshold_faithfulness:
            experiment.guardrail_passed = False
            experiment.guardrail_reason = (
                f"ΔFaithfulness ({experiment.delta_faithfulness:.3f}) por debajo de {threshold_faithfulness:.3f}"
            )
        elif experiment.delta_latency > threshold_latency:
            experiment.guardrail_passed = False
            experiment.guardrail_reason = (
                f"ΔLatencia ({experiment.delta_latency:.3f}s) excede {threshold_latency:.3f}s"
            )
        else:
            experiment.guardrail_passed = True
            experiment.guardrail_reason = ""

        experiment.save(update_fields=["guardrail_passed", "guardrail_reason", "updated_at"])
        return experiment
