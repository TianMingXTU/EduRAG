from tortoise import fields
from tortoise.models import Model


class FQAQAPair(Model):
    """
    FQA 标准问答对模型
    """

    id = fields.BigIntField(pk=True, description="主键 ID")
    question = fields.CharField(max_length=500, unique=True, description="标准问题")
    answer = fields.TextField(description="标准答案")
    subject = fields.CharField(
        max_length=50,
        default="general",
        description="学科分类: python/java/math/english/ops/bigdata/general",
    )

    # JSON 字段：在 Python 中自动转为 list/dict
    tags = fields.JSONField(null=True, description='标签数组: ["变量", "基础语法"]')
    question_tokens = fields.JSONField(null=True, description="预分词结果(JSON数组)")

    # 布尔字段对应 TINYINT(1)
    is_active = fields.BooleanField(
        default=True, description="是否启用: 1=启用, 0=禁用"
    )
    priority = fields.IntField(default=0, description="优先级，数值越大越优先")
    view_count = fields.BigIntField(default=0, description="被命中/查看次数")
    last_hit_at = fields.DatetimeField(null=True, description="最近一次命中时间")

    # 时间追踪：auto_now_add 对应 CURRENT_TIMESTAMP，auto_now 对应 ON UPDATE CURRENT_TIMESTAMP
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "fqa_qa_pairs"
        table_description = "FQA 标准问答对"
        # 联合索引定义 (配合对应字段的查找)
        indexes = [
            ("subject", "is_active"),
            ("priority",),
        ]

    def __str__(self):
        return f"<FQAQAPair {self.id}: {self.question[:20]}>"
