
from tools.schemas import AgentReflection
from src.utils.validators import partial_parse


class TestValidators:
    def test_raw_output(self):
        raw_output = {
            "score": "4",  # 字符串会被自动转换为整数
            "issues": ["回答不完整"],
            "needs_revision": "true",  # 会自动转为bool
            "invalid_field": "ignored",  # 无效字段会被忽略
        }

        result = partial_parse(raw_output, AgentReflection)
        print(result)
        assert result is not None
        assert result.score == 4
        assert result.issues == ["回答不完整"]
        assert result.needs_revision is True






