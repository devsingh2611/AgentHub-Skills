#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版一键优化脚本

实现全自动的"优化-对比-调整"迭代循环，
包括预处理、基准生成、迭代优化、收敛检测等完整流程。

使用方法:
    # 基本用法
    python scripts/enhanced_optimize.py --project NSFC_Young

    # 指定最大迭代次数
    python scripts/enhanced_optimize.py --project NSFC_Young --max-iterations 5

    # 生成 HTML 报告
    python scripts/enhanced_optimize.py --project NSFC_Young --report

    # 跳过预处理（已有基准）
    python scripts/enhanced_optimize.py --project NSFC_Young --skip-baseline
"""

import argparse
import json
import subprocess
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from scripts.core.workspace_manager import WorkspaceManager
except ImportError:
    print("警告: 无法导入 WorkspaceManager")
    WorkspaceManager = None

try:
    from scripts.core.iterative_optimizer import AIOptimizer
except ImportError:
    print("警告: 无法导入 AIOptimizer")
    AIOptimizer = None

try:
    from scripts.heuristic_adjuster import IntelligentAdjuster
except ImportError:
    print("警告: 无法导入 IntelligentAdjuster")
    IntelligentAdjuster = None


class EnhancedOptimizer:
    """增强版 LaTeX 模板优化器"""

    def __init__(self, project_name: str, config: Optional[Dict] = None):
        """
        初始化优化器

        Args:
            project_name: 项目名称
            config: 配置参数
        """
        self.skill_root = Path(__file__).parent.parent
        self.repo_root = self.skill_root.parent.parent
        self.project_path = self._resolve_project_path(project_name)
        self.project_name = self.project_path.name
        self.scripts_dir = self.skill_root / "scripts"

        # 工作空间管理器
        if WorkspaceManager:
            self.ws_manager = WorkspaceManager(self.skill_root)
            self.workspace = self.ws_manager.get_project_workspace(self.project_path)
        else:
            self.ws_manager = None
            self.workspace = self.project_path / ".make_latex_model"
            self.workspace.mkdir(parents=True, exist_ok=True)

        # 智能调整器
        self.intelligent_adjuster = None
        if IntelligentAdjuster:
            self.intelligent_adjuster = IntelligentAdjuster(self.project_name)

        # AI 优化器（按需启用）
        self.ai_optimizer = None
        if AIOptimizer and config and config.get("use_ai_optimizer"):
            self.ai_optimizer = AIOptimizer(
                skill_root=self.skill_root,
                project_name=self.project_name,
                mode=config.get("ai_mode", "heuristic"),
                evaluate_after_apply=not bool(config.get("ai_no_eval", False)),
            )

        # 默认配置
        self.config = {
            "max_iterations": 30,
            "convergence_threshold": 0.01,
            "no_improvement_limit": 5,
            "compile_timeout": 120,
            "pixel_dpi": 150,
            "pixel_tolerance": 2,
        }

        if config:
            self.config.update(config)

        # 加载配置文件
        self._load_config()

        # 状态跟踪
        self.iteration_history = []
        self.best_config = None
        self.best_ratio = float('inf')

    def _resolve_project_path(self, project_arg: str) -> Path:
        """
        解析 --project 参数：
        - 支持传入项目名（如 NSFC_Young）
        - 也支持传入相对路径（如 projects/NSFC_Young）
        但必须最终落在仓库的 projects/ 目录下（防止路径遍历）。
        """
        projects_root = (self.repo_root / "projects").resolve()
        raw = str(project_arg).strip()

        # 允许用户传入 projects/<name>，或仅 <name>
        p = Path(raw)
        if p.is_absolute() or any(sep in raw for sep in ("/", "\\")):
            candidate = p if p.is_absolute() else (self.repo_root / p)
        else:
            candidate = self.repo_root / "projects" / raw

        candidate = candidate.resolve()
        try:
            candidate.relative_to(projects_root)
        except Exception:
            raise ValueError(f"--project 必须位于 {projects_root} 下: {project_arg}")

        return candidate

    def _load_config(self):
        """从配置文件加载设置"""
        config_path = self.skill_root / "config.yaml"

        if config_path.exists():
            try:
                import yaml
                with open(config_path, "r", encoding="utf-8") as f:
                    full_config = yaml.safe_load(f)
                    if "iteration" in full_config:
                        self.config.update(full_config["iteration"])
            except Exception:
                pass

    def _get_baseline_pdf(self) -> Optional[Path]:
        """
        选择基准 PDF（兼容旧版 word.pdf；推荐 baseline.pdf / projects/<project>/template/baseline.pdf）。
        """
        candidates = [
            self.workspace / "baselines" / "baseline.pdf",
            self.workspace / "baselines" / "word.pdf",  # legacy
            self.project_path / "template" / "baseline.pdf",
        ]

        for p in candidates:
            if p.exists():
                return p

        # 兜底：template/ 下只有一个 pdf 时使用它
        template_dir = self.project_path / "template"
        if template_dir.exists():
            pdfs = sorted(template_dir.glob("*.pdf"))
            if len(pdfs) == 1:
                return pdfs[0]
        return None

    def _ensure_workspace_baseline(self, baseline_pdf: Path) -> Path:
        """
        将基准复制到工作空间 baselines/ 下，保证后续产物落盘稳定。
        """
        ws_dir = self.workspace / "baselines"
        ws_dir.mkdir(parents=True, exist_ok=True)

        # legacy: 如果本来就是 workspace 下的文件，直接返回
        try:
            baseline_pdf.relative_to(ws_dir)
            return baseline_pdf
        except Exception:
            pass

        dst = ws_dir / "baseline.pdf"
        if not dst.exists():
            shutil.copy2(str(baseline_pdf), str(dst))
        return dst

    def log(self, message: str, level: str = "info"):
        """日志输出"""
        icons = {
            "info": "📌",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "step": "🔹",
        }
        icon = icons.get(level, "")
        print(f"{icon} {message}")

    def run_script(self, script_name: str, args: List[str] = None,
                   capture_output: bool = True) -> subprocess.CompletedProcess:
        """
        运行脚本

        Args:
            script_name: 脚本名称
            args: 命令行参数
            capture_output: 是否捕获输出

        Returns:
            运行结果
        """
        script_path = self.scripts_dir / script_name

        if not script_path.exists():
            raise FileNotFoundError(f"脚本不存在: {script_path}")

        cmd = ["python3", str(script_path)]
        if args:
            cmd.extend(args)

        return subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            timeout=self.config.get("compile_timeout", 120)
        )

    def step_precheck(self) -> Dict[str, Any]:
        """
        步骤 0: 预检查

        Returns:
            检查结果
        """
        self.log("步骤 0: 预检查", "step")

        result = {
            "project_exists": self.project_path.exists(),
            "main_tex_exists": (self.project_path / "main.tex").exists(),
            "config_tex_exists": (self.project_path / "extraTex" / "@config.tex").exists(),
            "template_dir_exists": (self.project_path / "template").exists(),
            "has_baseline": False,
        }

        baseline_pdf = self._get_baseline_pdf()
        result["has_baseline"] = bool(baseline_pdf and baseline_pdf.exists())

        # 输出结果
        for key, value in result.items():
            status = "✓" if value else "✗"
            self.log(f"  {status} {key}", "info")

        return result

    def step_prepare_main(self) -> bool:
        """
        步骤 1: 预处理 main.tex

        Returns:
            是否成功
        """
        self.log("步骤 1: 预处理 main.tex", "step")

        main_tex = self.project_path / "main.tex"
        backup_dir = self.workspace / "backup"

        try:
            result = self.run_script("prepare_main.py", [
                str(main_tex),
                "--backup-dir", str(backup_dir)
            ])

            if result.returncode == 0:
                self.log("main.tex 预处理完成", "success")
                return True
            else:
                self.log(f"预处理失败: {result.stderr}", "error")
                return False

        except Exception as e:
            self.log(f"预处理异常: {e}", "error")
            return False

    def step_generate_baseline(self) -> bool:
        """
        步骤 2: 生成 Word PDF 基准

        Returns:
            是否成功
        """
        self.log("步骤 2: 生成/准备 PDF 基准", "step")

        # 如果用户已经提供了 PDF 基准（workspace 或 template），直接使用
        baseline_pdf = self._get_baseline_pdf()
        if baseline_pdf and baseline_pdf.exists():
            self._ensure_workspace_baseline(baseline_pdf)
            self.log(f"发现已有基准: {baseline_pdf}", "success")
            return True

        try:
            result = self.run_script("generate_baseline.py", [
                "--project", self.project_name
            ])

            if result.returncode == 0:
                legacy = self.workspace / "baselines" / "word.pdf"
                if legacy.exists():
                    # 为新逻辑补一个稳定的 baseline.pdf
                    self._ensure_workspace_baseline(legacy)
                    self.log(f"基准已生成: {legacy}", "success")
                    return True

            self.log("基准生成失败", "error")
            return False

        except Exception as e:
            self.log(f"基准生成异常: {e}", "error")
            return False

    def step_analyze_baseline(self) -> Optional[Dict]:
        """
        步骤 3: 分析基准 PDF

        Returns:
            分析结果
        """
        self.log("步骤 3: 分析基准 PDF", "step")

        baseline_pdf = self._get_baseline_pdf()
        if not baseline_pdf:
            self.log("基准 PDF 不存在（请提供 template/baseline.pdf 或生成基准）", "error")
            return None
        baseline_pdf = self._ensure_workspace_baseline(baseline_pdf)

        try:
            # 运行分析脚本，使用 --project 参数直接保存到工作空间
            result = self.run_script(
                "analyze_pdf.py",
                [str(baseline_pdf), "--project", self.project_name]
            )

            # 直接从工作空间读取分析结果
            analysis_file = self.workspace / "baselines" / f"{baseline_pdf.stem}_analysis.json"
            if analysis_file.exists():
                self.log(f"分析结果已保存: {analysis_file}", "success")
                with open(analysis_file, "r", encoding="utf-8") as f:
                    return json.load(f)

            # 兼容旧版本：如果工作空间没有，尝试从当前目录查找
            old_analysis = Path(f"{baseline_pdf.stem}_analysis.json")
            if old_analysis.exists():
                self.log("发现旧版分析文件，正在迁移...", "warning")
                shutil.move(str(old_analysis), str(analysis_file))
                with open(analysis_file, "r", encoding="utf-8") as f:
                    return json.load(f)

            return None

        except Exception as e:
            self.log(f"分析异常: {e}", "error")
            return None

    def step_compile_latex(self) -> bool:
        """
        编译 LaTeX 项目

        Returns:
            是否成功
        """
        self.log("编译 LaTeX 项目...", "info")

        main_tex = self.project_path / "main.tex"

        # 编译序列: xelatex -> bibtex -> xelatex -> xelatex
        compile_steps = [
            ["xelatex", "-interaction=nonstopmode", "main.tex"],
            ["bibtex", "main"],
            ["xelatex", "-interaction=nonstopmode", "main.tex"],
            ["xelatex", "-interaction=nonstopmode", "main.tex"],
        ]

        try:
            for cmd in compile_steps:
                result = subprocess.run(
                    cmd,
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode != 0 and cmd[0] == "xelatex":
                    self.log(f"编译失败: {cmd[0]}", "error")
                    return False

            # 检查输出文件
            output_pdf = self.project_path / "main.pdf"
            if output_pdf.exists():
                self.log("编译成功", "success")
                return True

            return False

        except subprocess.TimeoutExpired:
            self.log("编译超时", "error")
            return False
        except Exception as e:
            self.log(f"编译异常: {e}", "error")
            return False

    def step_compare_pixels(self) -> Optional[float]:
        """
        像素对比

        Returns:
            差异比例（0-1）
        """
        self.log("执行像素对比...", "info")

        baseline_pdf = self._get_baseline_pdf()
        output_pdf = self.project_path / "main.pdf"

        if not baseline_pdf or not output_pdf.exists():
            return None
        baseline_pdf = self._ensure_workspace_baseline(baseline_pdf)

        try:
            return self.step_compare_pixels_with_artifacts(iteration=len(self.iteration_history) + 1, tag="")

        except Exception as e:
            self.log(f"像素对比异常: {e}", "error")
            return None

    def step_compare_pixels_with_artifacts(self, iteration: int, tag: str = "") -> Optional[float]:
        """
        带产物落盘的像素对比（JSON + diff_features）

        Args:
            iteration: 迭代编号（从 1 开始）
            tag: 文件后缀（如 'post'）

        Returns:
            差异比例（0-1）
        """
        baseline_pdf = self._get_baseline_pdf()
        output_pdf = self.project_path / "main.pdf"

        if not baseline_pdf or not output_pdf.exists():
            return None
        baseline_pdf = self._ensure_workspace_baseline(baseline_pdf)

        suffix = f"_{tag}" if tag else ""
        iter_dir = self.workspace / "iterations" / f"iteration_{iteration:03d}"
        iter_dir.mkdir(parents=True, exist_ok=True)

        json_out = iter_dir / f"pixel_compare{suffix}.json"
        features_out = iter_dir / f"diff_features{suffix}.json"

        pc = self.config.get("pixel_comparison", {}) if isinstance(self.config.get("pixel_comparison", {}), dict) else {}
        dpi = pc.get("dpi", self.config.get("pixel_dpi", 150))
        tol = pc.get("tolerance", self.config.get("pixel_tolerance", 2))
        mode = pc.get("mode", pc.get("comparison_mode", "page"))
        min_sim = pc.get("min_similarity", 0.85)

        cmd = [
            str(baseline_pdf),
            str(output_pdf),
            "--dpi", str(dpi),
            "--tolerance", str(tol),
            "--mode", str(mode),
            "--min-similarity", str(min_sim),
            "--json-out", str(json_out),
            "--features-out", str(features_out),
        ]

        result = self.run_script("compare_pdf_pixels.py", cmd)

        if result.returncode != 0:
            self.log(f"像素对比失败: {result.stderr}", "warning")
            return None

        try:
            data = json.loads(json_out.read_text(encoding="utf-8"))
            return float(data.get("avg_diff_ratio", None))
        except Exception:
            return None

    def step_check_convergence(self, current_ratio: float) -> tuple:
        """
        检查是否收敛

        Args:
            current_ratio: 当前差异比例

        Returns:
            (是否停止, 原因)
        """
        threshold = self.config.get("convergence_threshold", 0.03)
        max_iter = self.config.get("max_iterations", 10)
        no_imp_limit = self.config.get("no_improvement_limit", 3)

        current_iteration = len(self.iteration_history)

        # 检查收敛阈值
        if current_ratio < threshold:
            return True, f"达到收敛阈值 (差异 {current_ratio:.2%} < {threshold:.2%})"

        # 检查最大迭代次数
        if current_iteration >= max_iter:
            return True, f"达到最大迭代次数 ({max_iter})"

        # 检查连续无改善
        if len(self.iteration_history) >= no_imp_limit:
            recent = [h["changed_ratio"] for h in self.iteration_history[-no_imp_limit:]]
            if all(r >= self.best_ratio - 0.001 for r in recent):
                return True, f"连续 {no_imp_limit} 轮无改善"

        return False, "继续迭代"

    def step_save_iteration(self, iteration: int, metrics: Dict):
        """
        保存迭代结果

        Args:
            iteration: 迭代编号
            metrics: 指标数据
        """
        if self.ws_manager:
            self.ws_manager.save_iteration_result(
                self.project_name,
                iteration,
                pdf_path=self.project_path / "main.pdf",
                config_path=self.project_path / "extraTex" / "@config.tex",
                metrics=metrics
            )

        self.iteration_history.append(metrics)

        # 更新最佳配置
        if metrics.get("changed_ratio", float('inf')) < self.best_ratio:
            self.best_ratio = metrics["changed_ratio"]
            # 保存最佳配置内容
            config_path = self.project_path / "extraTex" / "@config.tex"
            if config_path.exists():
                self.best_config = config_path.read_text(encoding="utf-8")

    def step_restore_main(self) -> bool:
        """
        步骤 6: 恢复 main.tex

        Returns:
            是否成功
        """
        self.log("步骤 6: 恢复 main.tex", "step")

        main_tex = self.project_path / "main.tex"

        try:
            result = self.run_script("prepare_main.py", [
                str(main_tex),
                "--restore"
            ])

            if result.returncode == 0:
                self.log("main.tex 已恢复", "success")
                return True

            return False

        except Exception as e:
            self.log(f"恢复异常: {e}", "error")
            return False

    def generate_report(self) -> Dict[str, Any]:
        """
        生成优化报告

        Returns:
            报告数据
        """
        report = {
            "project_name": self.project_name,
            "generated_at": datetime.now().isoformat(),
            "config": self.config,
            "total_iterations": len(self.iteration_history),
            "iterations": self.iteration_history,
            "summary": {},
            "recommendation": ""
        }

        if self.iteration_history:
            ratios = [h.get("changed_ratio", 1.0) for h in self.iteration_history]
            report["summary"] = {
                "initial_ratio": ratios[0],
                "final_ratio": ratios[-1],
                "best_ratio": min(ratios),
                "improvement": ratios[0] - min(ratios),
            }

        return report

    def save_html_report(self, output_path: Path):
        """
        保存 HTML 报告

        Args:
            output_path: 输出路径
        """
        report = self.generate_report()

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>优化报告 - {report['project_name']}</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; }}
        .card {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric {{ display: inline-block; margin: 10px 20px; text-align: center; }}
        .metric .value {{ font-size: 28px; font-weight: bold; color: #667eea; }}
        .iteration {{ border-left: 3px solid #667eea; padding-left: 15px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 LaTeX 模板优化报告</h1>
        <p>项目: {report['project_name']}</p>
        <p>生成时间: {report['generated_at']}</p>
    </div>

    <div class="card">
        <h2>📈 优化摘要</h2>
        <div class="metric">
            <div class="value">{report['total_iterations']}</div>
            <div>迭代次数</div>
        </div>
"""

        if report["summary"]:
            s = report["summary"]
            html += f"""
        <div class="metric">
            <div class="value">{s.get('initial_ratio', 0):.2%}</div>
            <div>初始差异</div>
        </div>
        <div class="metric">
            <div class="value">{s.get('best_ratio', 0):.2%}</div>
            <div>最佳差异</div>
        </div>
        <div class="metric">
            <div class="value">{s.get('improvement', 0):.2%}</div>
            <div>改善幅度</div>
        </div>
"""

        html += """
    </div>

    <div class="card">
        <h2>🔄 迭代历史</h2>
"""

        for it in report["iterations"]:
            html += f"""
        <div class="iteration">
            <strong>第 {it.get('iteration', 0)} 轮</strong>: 差异 {it.get('changed_ratio', 0):.2%}
            <small>({it.get('timestamp', '')})</small>
        </div>
"""

        html += """
    </div>
</body>
</html>
"""

        output_path.write_text(html, encoding="utf-8")
        self.log(f"报告已保存: {output_path}", "success")

    def run(self, skip_baseline: bool = False, skip_prepare: bool = False) -> bool:
        """
        执行完整优化流程

        Args:
            skip_baseline: 跳过基准生成
            skip_prepare: 跳过预处理

        Returns:
            是否成功
        """
        print(f"\n{'='*60}")
        print(f"  增强版 LaTeX 模板优化")
        print(f"{'='*60}")
        print(f"  项目: {self.project_name}")
        print(f"  最大迭代: {self.config.get('max_iterations', 10)}")
        print(f"  收敛阈值: {self.config.get('convergence_threshold', 0.03):.2%}")
        print(f"{'='*60}\n")

        # 步骤 0: 预检查
        precheck = self.step_precheck()
        if not precheck["project_exists"] or not precheck["main_tex_exists"]:
            self.log("预检查失败，项目结构不完整", "error")
            return False

        # 步骤 1: 预处理
        if not skip_prepare:
            if not self.step_prepare_main():
                self.log("预处理失败", "warning")

        # 步骤 2: 生成基准
        if not skip_baseline and not precheck["has_baseline"]:
            if not self.step_generate_baseline():
                self.log("无法生成基准，请手动准备 word.pdf", "warning")

        # 步骤 3: 分析基准
        baseline_analysis = self.step_analyze_baseline()

        # 步骤 4-5: 迭代优化循环
        print(f"\n{'='*60}")
        print(f"  开始迭代优化")
        print(f"{'='*60}\n")

        iteration = 0

        while True:
            iteration += 1
            self.log(f"迭代 {iteration}", "step")

            # 编译
            if not self.step_compile_latex():
                metrics = {
                    "iteration": iteration,
                    "compilation_failed": True,
                    "timestamp": datetime.now().isoformat()
                }
                self.step_save_iteration(iteration, metrics)
                self.log("编译失败，停止迭代", "error")
                break

            # 像素对比
            ratio = self.step_compare_pixels_with_artifacts(iteration=iteration, tag="")

            if ratio is None:
                self.log("像素对比失败", "warning")
                ratio = 1.0

            self.log(f"  差异比例: {ratio:.2%}", "info")

            # 保存迭代结果
            metrics = {
                "iteration": iteration,
                "changed_ratio": ratio,
                "timestamp": datetime.now().isoformat()
            }
            self.step_save_iteration(iteration, metrics)

            # 检查收敛
            should_stop, reason = self.step_check_convergence(ratio)

            if should_stop:
                self.log(f"停止迭代: {reason}", "success")
                break

            # 自动调整参数（如果启用了智能调整器）
            if self.ai_optimizer:
                config_path = self.project_path / "extraTex" / "@config.tex"
                if config_path.exists():
                    self.log("  正在使用 AI 优化器调整参数...", "info")

                    def _compile():
                        return self.step_compile_latex()

                    def _compare():
                        return self.step_compare_pixels_with_artifacts(iteration=iteration, tag="post")

                    result = self.ai_optimizer.optimize_iteration(
                        iteration=iteration,
                        current_ratio=ratio,
                        config_path=config_path,
                        compile_func=_compile,
                        compare_func=_compare,
                    )

                    self.log(f"  AI 优化器: {result.status}（{result.reason}）", "info")
                else:
                    self.log("  配置文件不存在，跳过 AI 优化器", "warning")

            elif self.intelligent_adjuster:
                config_path = self.project_path / "extraTex" / "@config.tex"
                if config_path.exists():
                    self.log("  正在自动调整参数...", "info")
                    adjusted = self.intelligent_adjuster.auto_adjust_from_pixel_diff(
                        diff_ratio=ratio,
                        config_path=config_path,
                        iteration=iteration
                    )
                    if not adjusted:
                        self.log("  未应用调整（差异已足够小或无法生成建议）", "info")
                else:
                    self.log("  配置文件不存在，跳过自动调整", "warning")
            else:
                self.log("  智能调整器未启用，需要手动调整参数", "warning")

            self.log(f"  {reason}", "info")

        # 步骤 6: 恢复 main.tex
        if not skip_prepare:
            self.step_restore_main()

        # 最终编译
        self.log("最终编译验证...", "step")
        self.step_compile_latex()

        print(f"\n{'='*60}")
        print(f"  优化完成")
        print(f"{'='*60}")
        print(f"  总迭代: {len(self.iteration_history)}")
        print(f"  最佳差异: {self.best_ratio:.2%}")
        print(f"{'='*60}\n")

        return True


def main():
    parser = argparse.ArgumentParser(
        description="增强版一键优化脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--project", "-p", type=str, required=True,
                       help="项目名称或 projects/ 下相对路径（如 NSFC_Young 或 projects/NSFC_Young）")
    parser.add_argument("--max-iterations", type=int, default=10,
                       help="最大迭代次数（默认 10）")
    parser.add_argument("--report", "-r", action="store_true",
                       help="生成 HTML 报告")
    parser.add_argument("--skip-baseline", action="store_true",
                       help="跳过基准生成")
    parser.add_argument("--skip-prepare", action="store_true",
                       help="跳过预处理")
    parser.add_argument("--ai", action="store_true",
                       help="启用 AI 优化器（Analyzer→Reasoner→Executor→Memory）")
    parser.add_argument("--ai-mode", choices=["heuristic", "manual_file"], default="heuristic",
                       help="AI 优化器决策模式（默认 heuristic，可离线）")
    parser.add_argument("--ai-no-eval", action="store_true",
                       help="AI 优化器只应用调整，不做即时编译/像素对比回滚（不推荐）")

    args = parser.parse_args()

    # 配置
    config = {
        "max_iterations": args.max_iterations,
        "use_ai_optimizer": bool(args.ai),
        "ai_mode": args.ai_mode,
        "ai_no_eval": bool(args.ai_no_eval),
    }

    # 创建优化器
    optimizer = EnhancedOptimizer(args.project, config)

    # 执行优化
    success = optimizer.run(
        skip_baseline=args.skip_baseline,
        skip_prepare=args.skip_prepare
    )

    # 生成报告
    if args.report:
        report_path = optimizer.workspace / "reports" / "optimization_report.html"
        optimizer.save_html_report(report_path)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
