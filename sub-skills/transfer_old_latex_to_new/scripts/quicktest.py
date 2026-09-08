#!/usr/bin/env python
"""
简单测试运行器（不依赖 pytest）
"""

import sys
import asyncio
from pathlib import Path

sys.dont_write_bytecode = True

# 添加 scripts/ 目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.word_count_adapter import WordCountAdapter
from core.reference_guardian import ReferenceGuardian
from core.content_optimizer import ContentOptimizer
from core.llm_bridge import AIIntegration


def test_word_count_adapter():
    """测试字数适配器"""
    print("测试 WordCountAdapter...")

    adapter = WordCountAdapter({}, ".")

    # 测试字数统计
    content = "这是测试内容。" * 100
    count = adapter._count_chinese_words(content)
    assert count > 0, "字数统计失败"

    # 测试字数报告
    report = adapter.generate_word_count_report(content, "立项依据", "2025_to_2026")
    assert "current_count" in report
    assert "old_requirement" in report
    assert "new_requirement" in report

    print("  ✅ WordCountAdapter 测试通过")
    return True


def test_reference_guardian():
    """测试引用守护者"""
    print("测试 ReferenceGuardian...")

    guardian = ReferenceGuardian({"reference_protection": {"enabled": True}})

    # 测试引用保护
    content = r"""测试\ref{fig1}和\cite{author2024}。"""
    protected, ref_map = guardian.protect_references(content)

    assert len(ref_map) == 2, "引用提取失败"
    assert r"\ref{fig1}" not in protected, "引用未被替换"
    assert "__REF_" in protected, "占位符未生成"

    # 测试引用恢复
    restored = guardian.restore_references(protected, ref_map)
    assert restored == content, "引用恢复失败"

    # 测试引用验证
    refs = guardian._extract_all_references(content)
    assert "fig1" in refs
    assert "author2024" in refs

    print("  ✅ ReferenceGuardian 测试通过")
    return True


def test_content_optimizer():
    """测试内容优化器"""
    print("测试 ContentOptimizer...")

    optimizer = ContentOptimizer({"reference_protection": {"enabled": True}}, ".")

    # 测试优化报告
    content = "这是测试内容。" * 20
    report = optimizer.generate_optimization_report(content, "测试章节")

    assert "section" in report
    assert "total_issues" in report
    assert report["section"] == "测试章节"

    # 测试启发式分析
    result = optimizer._heuristic_analysis(content, {"remove_redundancy": True})
    assert "optimization_points" in result
    assert "improvement_potential" in result

    print("  ✅ ContentOptimizer 测试通过")
    return True


async def test_async_integration():
    """测试异步集成"""
    print("测试异步集成...")

    optimizer = ContentOptimizer({"reference_protection": {"enabled": True}}, ".")
    ai = AIIntegration(enable_ai=False)

    # 测试异步优化（无 AI 时应优雅降级，不抛异常）
    content = "测试内容"
    result = await optimizer.optimize_content(content, "测试", {}, ai_integration=ai)
    assert "original_content" in result
    assert result["optimized_content"]

    print("  ✅ 异步集成测试通过")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("🧪 运行单元测试")
    print("=" * 60 + "\n")

    tests = [
        ("WordCountAdapter", test_word_count_adapter),
        ("ReferenceGuardian", test_reference_guardian),
        ("ContentOptimizer", test_content_optimizer),
        ("Async Integration", test_async_integration),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                asyncio.run(test_func())
            else:
                test_func()
            passed += 1
        except Exception as e:
            print(f"  ❌ {name} 测试失败: {e}")
            failed += 1
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
