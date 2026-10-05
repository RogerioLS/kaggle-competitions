---
id: TASK-06
title: "Gemma 4 Post-Training & LoRA Adapter Pipeline"
area: competition/gemma-developer-agent
type: feature
milestone: 4
---

## 🎯 Task Objective
Set up post-training / fine-tuning pipeline for Gemma 4 31B using LoRA / QLoRA on high-quality SWE-bench issue-patch trajectories to boost reasoning, tool selection, and patch generation accuracy.

## 📋 Definition of Done
- [ ] Create trajectory collection pipeline from successful harness runs
- [ ] Setup SFT / LoRA fine-tuning scripts under `competitions/gemma-developer-agent/training/`
- [ ] Package and validate LoRA adapter weights inside `submission.zip`
- [ ] Measure Pass@1 improvement comparing base model vs post-trained model
