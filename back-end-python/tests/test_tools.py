import pytest
from tools.basic_tools import safe_calculator, get_current_time, text_stats, unit_convert



class TestSafeCalculator:
    """安全计算器测试"""
    def test_basic_addition(self):
        """测试加法"""
        result=safe_calculator.invoke({"expression":"2+3"})
        assert result["ok"] is True
        assert result["data"]["value"]==5

    def test_complex_expression(self):
        """测试复杂表达式"""
        result=safe_calculator.invoke({"expression":"(1+2)*3**2"})
        assert result["ok"] is True
        assert result["data"]["value"]==27


class TestGetCurrentTime:
    """获取当前时间工具测试"""
    def test_default_format(self):
        """测试默认格式"""
        result=get_current_time.invoke({})
        assert isinstance(result,str)
        assert len(result)==19  # "YYYY-MM-DD HH:MM:SS"长度为19

    def test_custom_format(self):
        """测试自定义格式"""
        result=get_current_time.invoke({"format_str":"%Y/%m/%d"})
        assert isinstance(result,str)
        assert len(result)==10  # "YYYY/MM/DD"长度为10


class TestTextStats:
    """文本统计工具测试"""
    def test_basic_stats(self):
        """测试基本统计"""
        result = text_stats.invoke({"text": "Hello world! This is a test."})
        assert result["ok"] is True
        assert result["data"]["chinese_chars"] == 0
        assert result["data"]["english_words"] == 6
        assert result["data"]["total_chars"] == 28
        assert result["data"]["sentences_estimate"] == 2



class TestUnitConvert:
    def test_celsius_to_fahrenheit(self):
        """测试摄氏度转华氏度"""
        result = unit_convert.invoke({"value": 0, "from_unit": "C", "to_unit": "F"})
        assert result["ok"] is True
        assert result["data"]["value"] == 32.0

    def test_km_to_miles(self):
        """测试公里转英里"""
        result = unit_convert.invoke({"value": 1, "from_unit": "km", "to_unit": "miles"})
        assert result["ok"] is True
        assert abs(result["data"]["value"] - 0.621371) < 0.001

    def test_invalid_conversion(self):
        """测试无效转换"""
        result = unit_convert.invoke({"value": 100, "from_unit": "kg", "to_unit": "lb"})
        assert result["ok"] is False














