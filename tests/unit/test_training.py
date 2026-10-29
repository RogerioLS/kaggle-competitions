"""Unit tests for Gemma 4 LoRA post-training, trajectory collection, and evaluation."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
import yaml

from competitions.gemma_developer_agent.agent.runner import (
    AgentSessionResult,
    ToolCall,
    TurnRecord,
)
from competitions.gemma_developer_agent.agent.schema import AgentConfig
from competitions.gemma_developer_agent.evaluation.dataset_loader import (
    SWEInstance,
)
from competitions.gemma_developer_agent.evaluation.harness import (
    LocalSWEHarness,
)
from competitions.gemma_developer_agent.submission.packager import (
    package_submission,
)
from competitions.gemma_developer_agent.submission.validator import (
    validate_submission,
)
from competitions.gemma_developer_agent.training.evaluator import (
    ComparativeEvaluator,
    InstanceComparison,
)
from competitions.gemma_developer_agent.training.lora_trainer import (
    LoRATrainer,
    TrainingConfig,
)
from competitions.gemma_developer_agent.training.trajectory_collector import (
    ChatTurn,
    Trajectory,
    TrajectoryCollector,
)


@pytest.fixture
def sample_swe_instance() -> SWEInstance:
    """Fixture providing a mock SWEInstance."""
    return SWEInstance(
        instance_id="repo__task-101",
        repo="psf/requests",
        base_commit="commit_101",
        problem_statement="Fix status code check.",
        hints_text="Inspect response parsing.",
        patch="diff --git a/test.py b/test.py\n",
        test_patch="diff --git a/t_test.py b/t_test.py\n",
    )


@pytest.fixture
def sample_agent_session() -> AgentSessionResult:
    """Fixture providing a resolved AgentSessionResult."""
    history = [
        TurnRecord(
            turn_index=1,
            sub_agent="explorer",
            tool_call=ToolCall(tool_name="read_file", arguments={"filepath": "main.py"}),
            observation="content of main.py",
        ),
        TurnRecord(
            turn_index=2,
            sub_agent="drafter",
            tool_call=ToolCall(
                tool_name="edit_file",
                arguments={"filepath": "main.py", "old_string": "a", "new_string": "b"},
            ),
            observation="edited",
        ),
        TurnRecord(
            turn_index=3,
            sub_agent="validator",
            tool_call=ToolCall(tool_name="submit_patch", arguments={}),
            observation="patch generated",
        ),
    ]
    return AgentSessionResult(
        instance_id="repo__task-101",
        patch="diff --git a/main.py b/main.py\n+fixed\n",
        turns_used=3,
        duration_seconds=1.5,
        success=True,
        history=history,
    )


class TestTrajectoryCollector:
    """Verifies trajectory extraction, filtering, and Gemma chat formatting."""

    def test_chat_turn_gemma_formatting(self) -> None:
        """Verifies special turn tokens adhere to Gemma 4 chat standard."""
        user_turn = ChatTurn(role="user", content="Hello agent")
        model_turn = ChatTurn(role="model", content="I am thinking...")

        expected_user = "<start_of_turn>user\nHello agent<end_of_turn>\n"
        expected_model = "<start_of_turn>model\nI am thinking...<end_of_turn>\n"
        assert user_turn.to_gemma_format() == expected_user
        assert model_turn.to_gemma_format() == expected_model

    def test_trajectory_serialization_roundtrip(self) -> None:
        """Verifies to_dict and from_dict preserve trajectory structure."""
        turns = [
            ChatTurn(role="user", content="Task"),
            ChatTurn(role="model", content="Action"),
        ]
        traj = Trajectory(
            instance_id="inst-1",
            repo="org/repo",
            turns=turns,
            resolved=True,
            patch="diff ...",
            metadata={"score": 1.0},
        )

        serialized = traj.to_dict()
        assert serialized["instance_id"] == "inst-1"
        assert "<start_of_turn>user" in serialized["text"]

        reconstructed = Trajectory.from_dict(serialized)
        assert reconstructed.instance_id == traj.instance_id
        assert len(reconstructed.turns) == 2
        assert reconstructed.resolved is True

    def test_collect_from_successful_session(
        self, sample_swe_instance: SWEInstance, sample_agent_session: AgentSessionResult
    ) -> None:
        """Verifies full session history conversion into multi-turn dialogue."""
        collector = TrajectoryCollector()
        traj = collector.collect_from_session(
            session=sample_agent_session, instance=sample_swe_instance, resolved=True
        )

        assert traj is not None
        assert traj.instance_id == sample_swe_instance.instance_id
        assert traj.resolved is True
        assert len(traj.turns) == 8
        assert traj.turns[0].role == "user"
        assert traj.turns[1].role == "model"
        assert "[EXPLORER]" in traj.turns[1].content
        assert traj.turns[2].role == "user"
        assert "Observation from read_file" in traj.turns[2].content

    def test_collect_skips_unresolved_session(
        self, sample_swe_instance: SWEInstance, sample_agent_session: AgentSessionResult
    ) -> None:
        """Verifies failed sessions are ignored when filtering for resolved trajectories."""
        sample_agent_session.success = False
        collector = TrajectoryCollector()
        traj = collector.collect_from_session(
            session=sample_agent_session, instance=sample_swe_instance, resolved=True
        )
        assert traj is None

    def test_save_and_load_jsonl(self, tmp_path: Path) -> None:
        """Verifies JSONL persistence of trajectories."""
        trajs = TrajectoryCollector.create_synthetic_trajectories(count=3)
        out_file = tmp_path / "trajectories.jsonl"
        TrajectoryCollector.save_to_jsonl(trajs, out_file)

        loaded = TrajectoryCollector.load_from_jsonl(out_file)
        assert len(loaded) == 3
        assert loaded[0].instance_id == "synth_task_001"
        assert loaded[0].resolved is True

    def test_collect_from_tasks_jsonl(self, tmp_path: Path) -> None:
        """Verifies ground-truth trajectory extraction from tasks.jsonl."""
        task_data = {
            "instance_id": "test_001",
            "repo": "fastapi/fastapi",
            "base_commit": "abc1234",
            "problem_statement": "Fix query validation",
            "patch": (
                "--- a/fastapi/utils.py\n"
                "+++ b/fastapi/utils.py\n"
                "@@ -10,3 +10,4 @@ def validate(val):\n"
                "     if not val:\n"
                "+        return None\n"
                "     return val\n"
            ),
        }
        tasks_file = tmp_path / "mock_tasks.jsonl"
        tasks_file.write_text(json.dumps(task_data) + "\n", encoding="utf-8")

        trajs = TrajectoryCollector.collect_from_tasks_jsonl(tasks_file)
        assert len(trajs) == 1
        assert trajs[0].instance_id == "test_001"
        assert trajs[0].repo == "fastapi/fastapi"
        assert trajs[0].resolved is True
        assert len(trajs[0].turns) == 7
        assert "read_file" in trajs[0].turns[1].content
        assert "edit_file" in trajs[0].turns[3].content
        assert "submit_patch" in trajs[0].turns[5].content


class TestLoRATraining:
    """Verifies LoRA configuration, fine-tuning execution, and PEFT artifact export."""

    def test_training_config_from_yaml(self, tmp_path: Path) -> None:
        """Verifies parsing of LoRA configuration from YAML file."""
        cfg_file = tmp_path / "custom_config.yaml"
        cfg_content = {
            "model_name_or_path": "google/gemma-4-31b-it",
            "adapter_name": "test-adapter",
            "lora": {"r": 32, "lora_alpha": 64, "lora_dropout": 0.1},
            "training": {"learning_rate": 1e-4, "num_train_epochs": 2},
            "output": {"output_dir": "test/out"},
        }
        cfg_file.write_text(yaml.dump(cfg_content), encoding="utf-8")

        config = TrainingConfig.from_yaml(cfg_file)
        assert config.adapter_name == "test-adapter"
        assert config.lora.r == 32
        assert config.lora.lora_alpha == 64
        assert config.training.num_train_epochs == 2

    def test_lora_trainer_generates_adapter_artifacts(self, tmp_path: Path) -> None:
        """Verifies adapter_config.json, safetensors, and metrics are exported."""
        trajs = TrajectoryCollector.create_synthetic_trajectories(count=2)
        dataset_path = tmp_path / "data.jsonl"
        TrajectoryCollector.save_to_jsonl(trajs, dataset_path)

        out_dir = tmp_path / "adapter_output"
        trainer = LoRATrainer()
        saved_dir, metrics = trainer.train(dataset_path=dataset_path, output_dir=out_dir)

        assert saved_dir == out_dir
        assert (out_dir / "adapter_config.json").is_file()
        assert (out_dir / "adapter_model.safetensors").is_file()
        assert (out_dir / "README.md").is_file()
        assert (out_dir / "training_metrics.json").is_file()

        # Check adapter config content
        adapter_cfg = json.loads((out_dir / "adapter_config.json").read_text(encoding="utf-8"))
        assert adapter_cfg["peft_type"] == "LORA"
        assert adapter_cfg["r"] == 16
        assert "q_proj" in adapter_cfg["target_modules"]

        assert metrics.final_loss < metrics.initial_loss
        assert metrics.total_trajectories == 2

    def test_empty_dataset_raises_error(self, tmp_path: Path) -> None:
        """Verifies trainer raises ValueError on empty dataset."""
        empty_file = tmp_path / "empty.jsonl"
        empty_file.write_text("", encoding="utf-8")

        trainer = LoRATrainer()
        with pytest.raises(ValueError, match="No trajectories loaded"):
            trainer.train(dataset_path=empty_file, output_dir=tmp_path / "out")


class TestComparativeEvaluator:
    """Verifies Pass@1 benchmarking and delta calculation between base and adapted agents."""

    def test_comparative_evaluator_metrics_computation(self, tmp_path: Path) -> None:
        """Verifies comparison math across dual evaluation runs."""
        harness = LocalSWEHarness(base_dir=tmp_path / "harness")
        agent_yaml = Path("competitions/gemma_developer_agent/agent/agent.yaml").resolve()
        cfg = AgentConfig.from_yaml(agent_yaml)
        from competitions.gemma_developer_agent.agent.runner import (
            DeclarativeAgentRunner,
        )

        base_runner = DeclarativeAgentRunner(config=cfg)

        inst1 = SWEInstance(
            instance_id="c_inst_1",
            repo="r1",
            base_commit="c1",
            problem_statement="p1",
            patch="",
            test_patch="",
        )
        inst2 = SWEInstance(
            instance_id="c_inst_2",
            repo="r2",
            base_commit="c2",
            problem_statement="p2",
            patch="",
            test_patch="",
        )

        evaluator = ComparativeEvaluator(harness=harness)
        result = evaluator.evaluate_comparison(instances=[inst1, inst2], base_agent=base_runner)

        assert result.total_instances == 2
        assert result.adapted_pass_at_1 >= result.base_pass_at_1
        assert result.pass_at_1_delta >= 0.0
        assert len(result.instances) == 2
        assert result.turn_reduction_percent >= 0.0

    def test_markdown_report_formatting(self) -> None:
        """Verifies markdown report includes comparison table and delta."""
        from competitions.gemma_developer_agent.training.evaluator import (
            ComparisonResult,
        )

        res = ComparisonResult(
            total_instances=2,
            base_resolved_count=0,
            adapted_resolved_count=2,
            base_pass_at_1=0.0,
            adapted_pass_at_1=1.0,
            pass_at_1_delta=1.0,
            base_avg_turns=5.0,
            adapted_avg_turns=2.0,
            turn_reduction_percent=60.0,
            instances=[
                InstanceComparison("i1", "r1", False, True, 5, 2),
                InstanceComparison("i2", "r2", False, True, 5, 2),
            ],
        )

        report = res.to_markdown_report()
        assert "Pass@1 Resolution Delta" in report
        assert "+100.0%" in report
        assert "**-60.0%** fewer turns" in report


class TestSubmissionPackagingWithAdapters:
    """Verifies packaging and validation of LoRA adapters inside submission.zip."""

    def test_package_and_validate_with_adapters(self, tmp_path: Path) -> None:
        """Ensures submission.zip packages and validates adapter_config.json and weights."""
        # 1. Train a mock adapter
        trajs = TrajectoryCollector.create_synthetic_trajectories(count=2)
        dataset_path = tmp_path / "data.jsonl"
        TrajectoryCollector.save_to_jsonl(trajs, dataset_path)

        adapter_dir = tmp_path / "test_adapters" / "gemma4-swe-w4a16"
        trainer = LoRATrainer()
        trainer.train(dataset_path=dataset_path, output_dir=adapter_dir)

        # 2. Package with custom adapters directory
        zip_target = tmp_path / "submission_with_adapters.zip"
        target_path, manifest = package_submission(
            output_path=zip_target, adapters_dir=adapter_dir.parent
        )

        assert target_path.is_file()
        with zipfile.ZipFile(target_path, "r") as zf:
            namelist = zf.namelist()

        assert "agent.yaml" in namelist
        assert "adapters/gemma4-swe-w4a16/adapter_config.json" in namelist
        assert "adapters/gemma4-swe-w4a16/adapter_model.safetensors" in namelist

        # 3. Validate archive
        val_result = validate_submission(target_path)
        assert val_result.passed is True
        assert val_result.checks["schema_and_references"] is True

    def test_validator_rejects_adapter_missing_weights(self, tmp_path: Path) -> None:
        """Validator rejects archive containing adapter_config.json without weights."""
        bad_zip = tmp_path / "bad_adapter.zip"
        with zipfile.ZipFile(bad_zip, "w") as zf:
            zf.writestr(
                "agent.yaml",
                yaml.dump(
                    {
                        "name": "a",
                        "version": "1",
                        "model": "gemma",
                        "budget": {"max_turns": 5, "timeout_seconds": 60},
                        "system_prompt": "prompts/sys.md",
                        "sub_agents": {"sub1": "sub_agents/sub1.yaml"},
                        "workflow": {"sequence": ["sub1"]},
                    }
                ),
            )
            zf.writestr("prompts/sys.md", "# Sys\n")
            zf.writestr(
                "sub_agents/sub1.yaml",
                yaml.dump({"name": "sub1", "prompt": "prompts/sys.md"}),
            )
            zf.writestr(
                "adapters/lora1/adapter_config.json",
                json.dumps({"peft_type": "LORA"}),
            )

        val_result = validate_submission(bad_zip)
        assert val_result.passed is False
        assert any("missing weights" in err for err in val_result.errors)
