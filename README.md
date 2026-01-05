# Persona-Passwords-Study 🛡️🧠

A behavioral cybersecurity study using Large Language Models (LLMs) to simulate human password generation. This project explores the tension between personal identity (hobbies) and security requirements (leetspeak/complexity) through synthetic personas and behavioral profiling.

## 📖 Project Overview

Humans rarely create truly random passwords. Instead, they use "semantic anchors"—personally meaningful words or professional tools—to satisfy security requirements while maintaining memorability. This repository contains the tools and research data used to simulate these behaviors across different AI architectures.

### Research Goals:
* **Hobby Anchoring:** Quantifying how often personal interests drive "lazy" email passwords.
* **Professional Shortcuts:** Analyzing the predictability of leetspeak-modified professional tools (e.g., `Stetho$cope1`).
* **Architectural Benchmarking:** Comparing the behavioral "reasoning" capabilities of local Edge-AI (NPU) vs. Cloud-based LLMs.

## 🛠️ Evolution of Methodology

This project began as a local hardware study using **OpenVINO** and the **NPU (Neural Processing Unit)** on a mobile workstation. 

### Phase 1: Local Edge-AI (Qwen-1.5B)
Initially, we attempted to use Qwen-1.5B via `openvino_genai`. This phase revealed significant **Instruction Collapse** in small models; the model struggled to maintain complex JSON structures while simultaneously inventing unique personas, often defaulting to generic tokens (e.g., "John Smith").

### Phase 2: Cloud-Based Reasoning (Gemini 1.5 Flash)
To achieve higher behavioral fidelity, the study pivoted to the **Gemini API**. This allowed for:
* **Native JSON Output:** Reliable structured data without parsing errors.
* **Diverse Identities:** Greater cultural and professional variety in generated personas.
* **Deep Reasoning:** High-quality "logic notes" explaining the simulated user's choices.

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* Google AI Studio API Key (Free Tier)
* (Optional) OpenVINO Toolkit for local NPU experiments

### Installation
1.  Clone the repository:
    ```bash
    git clone [https://github.com/YOUR_USERNAME/Persona-Passwords-Study.git](https://github.com/YOUR_USERNAME/Persona-Passwords-Study.git)
    cd Persona-Passwords-Study
    ```
2.  Install dependencies:
    ```bash
    pip install -U google-generativeai
    ```
3.  Set up your API Key:
    * Create a `config.py` (added to `.gitignore`) and add: 
        `API_KEY = "your_key_here"`

## 📊 Data Format
The generated study data is saved in JSON format with the following schema:
```json
{
  "name": "Full Name",
  "job": "Occupation",
  "hobby": "Personal Interest",
  "logic_note": "Reasoning for password choices",
  "email_pwd": "Hobby-based password",
  "work_pwd": "Complex career-based password"
}
